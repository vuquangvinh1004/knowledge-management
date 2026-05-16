"""Dialog quản lý [[wikilinks]] của một note.

Hiển thị danh sách outgoing wikilinks (các note mà note này đang trỏ tới).
Người dùng có thể xóa wikilink (xóa Link record) — không xóa note đích.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.link_service import LinkService
from core.services.note_service import NoteService
from core.utils.logger import get_logger

logger = get_logger()


class NoteWikilinksDialog(QDialog):
    """Dialog hiển thị và quản lý outgoing wikilinks của một note."""

    def __init__(
        self,
        note_id: int,
        parent: QWidget | None = None,
        *,
        notes_dir=None,
    ) -> None:
        super().__init__(parent)
        self._note_id = note_id
        self._link_service = LinkService()
        # Lấy notes_dir từ parent nếu có
        if notes_dir is not None:
            self._notes_dir = notes_dir
        else:
            try:
                self._notes_dir = parent._notes_dir  # type: ignore[union-attr]
            except AttributeError:
                self._notes_dir = None

        self.setWindowTitle("Quản lý liên kết (Wikilinks)")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_links()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Wikilinks đi ra từ ghi chú này:"))

        self._link_list = QListWidget()
        self._link_list.setMinimumHeight(180)
        layout.addWidget(self._link_list)

        # Row hiển thị chú thích
        hint = QLabel(
            "💡 Xóa wikilink sẽ xóa liên kết trong CSDL và gỡ cú pháp [[...]] trong nội dung ghi chú\n"
            "   về text thường (chữ thường, màu đen), nhưng KHÔNG xóa ghi chú đích."
        )
        hint.setWordWrap(True)
        hint.setObjectName("wikilink_hint_label")
        layout.addWidget(hint)

        # Nút xóa + thông tin
        action_row = QHBoxLayout()
        btn_remove = QPushButton("Xóa liên kết đã chọn")
        btn_remove.clicked.connect(self._remove_selected)
        action_row.addWidget(btn_remove)
        action_row.addStretch()

        btn_remove_all_orphan = QPushButton("Dọn link không còn trong nội dung")
        btn_remove_all_orphan.setToolTip(
            "Quét lại nội dung ghi chú và xóa các link record "
            "cho những [[wikilink]] không còn xuất hiện."
        )
        btn_remove_all_orphan.clicked.connect(self._rescan_and_cleanup)
        action_row.addWidget(btn_remove_all_orphan)
        layout.addLayout(action_row)

        # OK
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _load_links(self) -> None:
        """Tải danh sách outgoing wikilinks."""
        self._link_list.clear()
        try:
            links = self._link_service.get_outgoing_links(self._note_id)
            # Chỉ lấy wikilink (bỏ manual/inferred)
            wikilinks = [lnk for lnk in links if lnk.link_type == "wikilink"]

            if not wikilinks:
                item = QListWidgetItem("(Không có wikilink nào)")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self._link_list.addItem(item)
                return

            # Lấy title của note đích
            from core.storage.models import Note
            from core.storage.session import get_session
            target_ids = [lnk.to_note_id for lnk in wikilinks]
            with get_session() as s:
                note_rows = s.query(Note.id, Note.title, Note.note_type).filter(
                    Note.id.in_(target_ids)
                ).all()
                note_map = {r[0]: (r[1], r[2]) for r in note_rows}

            for lnk in sorted(wikilinks, key=lambda l: l.to_note_id):
                title, ntype = note_map.get(lnk.to_note_id, (f"Note {lnk.to_note_id}", ""))
                weight_info = f"  ×{lnk.weight}" if lnk.weight and lnk.weight > 1 else ""
                display = f"[[{title}]]  ({ntype}){weight_info}"
                list_item = QListWidgetItem(display)
                list_item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "link_id": int(lnk.id),
                        "to_note_id": int(lnk.to_note_id),
                        "title": str(title),
                    },
                )
                list_item.setToolTip(
                    f"Link ID: {lnk.id}\n"
                    f"→ Note ID: {lnk.to_note_id}: {title}\n"
                    f"Type: {ntype} | Weight: {lnk.weight}"
                )
                self._link_list.addItem(list_item)
        except Exception as exc:
            logger.warning(f"Lỗi load wikilinks: {exc}")

    def _remove_selected(self) -> None:
        """Xóa link record đang được chọn."""
        item = self._link_list.currentItem()
        if item is None:
            return
        payload = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(payload, dict):
            return
        link_id = payload.get("link_id")
        to_note_id = payload.get("to_note_id")
        if link_id is None:
            return
        try:
            self._link_service.delete_link(link_id)
            if isinstance(to_note_id, int):
                self._demote_removed_wikilinks_in_content({to_note_id})
            self._load_links()
        except Exception as exc:
            logger.warning(f"Lỗi xóa link: {exc}")

    def _rescan_and_cleanup(self) -> None:
        """Quét lại nội dung note và dọn link record không còn hợp lệ."""
        if self._notes_dir is None:
            return
        try:
            from collections import Counter
            import re
            from core.services.note_service import NoteService
            from core.utils.helpers import slugify
            from core.utils.exceptions import NoteNotFoundError

            note_svc = NoteService(self._notes_dir)
            content = note_svc.read_content(self._note_id)
            pattern = re.compile(r"\[\[([^\[\]\n]+)\]\]")
            raw_matches = pattern.findall(content)

            active_target_ids: set[int] = set()
            for m in raw_matches:
                raw = m.strip()
                if "|" in raw:
                    raw = raw.split("|")[0].strip()
                if "#" in raw:
                    note_part = raw.split("#")[0].strip()
                    if not note_part:
                        continue
                    raw = note_part
                if not raw:
                    continue
                slug = slugify(raw)
                try:
                    tn = note_svc.get_by_slug(slug)
                    active_target_ids.add(tn.id)
                except NoteNotFoundError:
                    all_notes = note_svc.list_all()
                    found = next(
                        (n for n in all_notes if n.title.lower() == raw.lower()), None
                    )
                    if found:
                        active_target_ids.add(found.id)
                except Exception:
                    pass

            self._link_service.cleanup_outgoing_wikilinks(
                self._note_id, active_target_ids
            )
            self._load_links()
        except Exception as exc:
            logger.warning(f"Lỗi rescan wikilinks: {exc}")

    def _demote_removed_wikilinks_in_content(self, target_note_ids: set[int]) -> None:
        """Chuyển [[wikilink]] đã bị xóa link record về text thường (lowercase)."""
        if self._notes_dir is None or not target_note_ids:
            return

        try:
            import re
            from core.utils.exceptions import NoteNotFoundError
            from core.utils.helpers import slugify

            note_svc = NoteService(self._notes_dir)
            content = note_svc.read_content(self._note_id)
            all_notes = note_svc.list_all()

            title_map = {
                str(n.title).strip().lower(): int(n.id)
                for n in all_notes
                if getattr(n, "title", None)
            }
            slug_map = {
                str(getattr(n, "slug", "")).strip().lower(): int(n.id)
                for n in all_notes
                if getattr(n, "slug", None)
            }

            pattern = re.compile(r"\[\[([^\[\]\n]+)\]\]")

            def _replace(match: re.Match[str]) -> str:
                raw = match.group(1).strip()
                target_raw = raw
                if "|" in target_raw:
                    target_raw = target_raw.split("|", 1)[0].strip()
                if "#" in target_raw:
                    note_part = target_raw.split("#", 1)[0].strip()
                    if note_part:
                        target_raw = note_part

                note_id = None
                target_slug = slugify(target_raw)
                if target_slug:
                    note_id = slug_map.get(target_slug.lower())
                if note_id is None:
                    note_id = title_map.get(target_raw.lower())
                if note_id is None:
                    try:
                        maybe_note = note_svc.get_by_slug(target_slug)
                        note_id = int(maybe_note.id)
                    except NoteNotFoundError:
                        note_id = None
                    except Exception:
                        note_id = None

                if note_id in target_note_ids:
                    plain = target_raw.strip().lower()
                    return plain
                return match.group(0)

            new_content = pattern.sub(_replace, content)
            if new_content != content:
                note_svc.save_content(self._note_id, new_content)
        except Exception as exc:
            logger.warning(f"Lỗi khi gỡ định dạng wikilink đã xóa: {exc}")
