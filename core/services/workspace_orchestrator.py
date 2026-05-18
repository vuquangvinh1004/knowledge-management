"""Use case/orchestrator cho workflow Workspace (dual-pane + markdown editor).

Mục tiêu:
- Kéo bớt business orchestration khỏi UI widgets.
- Chuẩn hóa logging và xử lý lỗi ở luồng mở source, extract và đồng bộ note.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Optional

from core.services.asset_service import AssetService
from core.services.extract_service import ExtractService
from core.services.link_service import LinkService
from core.services.note_service import NoteService
from core.services.project_service import ProjectService
from core.services.source_service import SourceService
from core.services.tag_service import TagService
from core.extraction.anchors import build_source_anchor
from core.extraction.normalizers import normalize_text
from core.utils.exceptions import NoteNotFoundError, PKMError
from core.utils.helpers import slugify
from core.utils.logger import get_logger

logger = get_logger()


class WorkspaceOrchestrator:
    """Điều phối các workflow chính của Workspace và Markdown editor."""

    def __init__(self, notes_dir: Path, assets_dir: Path) -> None:
        self._notes_dir = Path(notes_dir)
        self._assets_dir = Path(assets_dir)

    # ------------------------------------------------------------------
    # Source / note binding
    # ------------------------------------------------------------------

    def ensure_source_note(
        self,
        source_id: int,
        *,
        preferred_title: str | None = None,
    ):
        """Đảm bảo source luôn có source_note hợp lệ trên disk.

        Returns:
            tuple(Note, notice)
            - note: source_note đang hợp lệ
            - notice: thông báo phục hồi (nếu có), ngược lại None
        """
        source = SourceService().get_by_id(source_id)
        note_svc = NoteService(self._notes_dir)
        note = note_svc.get_source_note(source_id)
        notice: str | None = None

        if note is not None:
            note_path = Path(str(note.file_path or ""))
            if note.file_path and note_path.exists():
                return note, None

            # Record source_note vẫn còn trong DB nhưng file markdown đã mất.
            logger.warning(
                "Phát hiện source_note thiếu file trên disk: "
                f"note_id={note.id}, source_id={source_id}, path={note.file_path!r}"
            )
            try:
                note_svc.soft_delete(int(note.id))
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Không thể soft-delete source_note lỗi file id={note.id}: {exc}")

            notice = (
                "Ứng dụng phát hiện ghi chú nguồn cũ bị thiếu file trên máy và đã tự tạo lại "
                "một ghi chú nguồn mới để bạn tiếp tục làm việc an toàn."
            )

        auto_title = (preferred_title or "").strip() or SourceService.build_source_note_title(
            authors=source.authors,
            year=source.year,
            fallback_filename=Path(source.file_path).stem,
        )
        note = note_svc.create_note(
            title=auto_title,
            note_type="source_note",
            source_id=source_id,
        )

        meta_payload: dict[str, str] = {}
        if source.authors:
            meta_payload["author"] = str(source.authors)
        if source.year and str(source.year).isdigit() and len(str(source.year)) == 4:
            meta_payload["year"] = str(source.year)
        if meta_payload:
            try:
                note_svc.update_meta(note.id, meta_payload)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Không thể update meta cho source_note id={note.id}: {exc}")

        logger.info(f"Đảm bảo source_note id={note.id} cho source id={source_id}")
        return note, notice

    def load_source_with_note(self, source_id: int):
        """Lấy source và source_note, tự phục hồi nếu file note bị mất.

        Returns:
            tuple(source, note, notice)
            - notice: thông báo phục hồi cho UI (nếu có)
        """
        source = SourceService().get_by_id(source_id)
        note, notice = self.ensure_source_note(source_id)
        return source, note, notice

    def update_last_opened_page(self, source_id: int, page_no: int) -> None:
        """Lưu trang hiện tại của source, có log ngữ cảnh nếu lỗi."""
        try:
            SourceService().update_last_opened_page(source_id, page_no)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"Không thể cập nhật last_opened_page cho source id={source_id} "
                f"page={page_no}: {exc}"
            )

    # ------------------------------------------------------------------
    # Extraction workflows
    # ------------------------------------------------------------------

    def prepare_text_extract(self, source_id: int, page_no: int, pdf_rect: tuple, raw_text: str) -> tuple[str, str]:
        """Chuẩn hóa text và dựng anchor cho extract text."""
        text = normalize_text(raw_text)
        anchor = build_source_anchor(source_id, page_no, pdf_rect)
        return text, anchor

    def build_anchor(self, source_id: int, page_no: int, pdf_rect: tuple) -> str:
        """Dựng source anchor từ source/page/rect."""
        return build_source_anchor(source_id, page_no, pdf_rect)

    def commit_extract(
        self,
        *,
        source_id: int,
        page_no: int,
        extract_type: str,
        source_anchor: str,
        content_md: str,
        note_id: int | None,
    ) -> int | None:
        """Commit extract và trả về extract id nếu thành công."""
        try:
            extract = ExtractService().commit_extract(
                source_id=source_id,
                page_no=page_no,
                extract_type=extract_type,
                source_anchor=source_anchor,
                content_md=content_md,
                note_id=note_id,
            )
            return int(extract.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"Không thể commit extract type={extract_type} source={source_id} "
                f"page={page_no} note={note_id}: {exc}"
            )
            return None

    def save_image_asset(self, source_id: int, note_id: int | None, image_bytes: bytes) -> str:
        """Lưu asset ảnh và trả về file path."""
        asset = AssetService(self._assets_dir).save_image_asset(
            source_id=source_id,
            image_bytes=image_bytes,
            note_id=note_id,
        )
        return str(asset.file_path)

    # ------------------------------------------------------------------
    # Markdown note workflows
    # ------------------------------------------------------------------

    def save_note_content(self, note_id: int, content: str) -> None:
        NoteService(self._notes_dir).save_content(note_id, content)

    def sync_note_relations(self, note_id: int, content: str) -> None:
        """Đồng bộ wikilink và hashtag -> tags sau khi lưu note."""
        self._scan_and_sync_wikilinks(note_id, content)
        self._sync_hashtags_to_note_tags(note_id, content)

    def backlinks_count(self, note_id: int) -> int:
        return len(LinkService().get_backlinks(note_id))

    def known_tags(self, content: str) -> set[str]:
        tags: set[str] = set()
        try:
            tags.update(t.name.strip().lower() for t in TagService().list_tags())
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể tải tag catalog: {exc}")
        tags.update(self._extract_hashtags(content))
        return {t for t in tags if t}

    def wikilink_catalog(self, current_note_id: int | None = None) -> list[tuple[str, str]]:
        """Trả về danh sách (title, note_type) dùng cho popup wikilink."""
        notes = NoteService(self._notes_dir).list_all()
        active_project_id = self.active_project_id
        if active_project_id is not None:
            allowed_ids = ProjectService().get_project_note_ids(active_project_id)
            notes = [n for n in notes if int(n.id) in allowed_ids]
        entries: list[tuple[str, str]] = []
        for note in notes:
            if current_note_id is not None and note.id == current_note_id:
                continue
            title = (note.title or "").strip()
            note_type = str(getattr(note, "note_type", "concept_note"))
            if title:
                entries.append((title, note_type))

        dedup: dict[str, tuple[str, str]] = {}
        for title, note_type in entries:
            dedup[title.lower()] = (title, note_type)
        return sorted(dedup.values(), key=lambda x: x[0].lower())

    def build_quality_warnings(
        self,
        *,
        note_id: int,
        note_type: str,
        note_title: str,
        content: str,
        current_source_id: int | None,
    ) -> list[str]:
        """Tổng hợp soft-warning chất lượng note."""
        warnings = NoteService.title_warnings(note_type, note_title)

        if "[[" not in content:
            warnings.append("Nên có ít nhất 1 wikilink để tránh note mồ côi.")

        if note_type == "source_note" and current_source_id is not None:
            try:
                source = SourceService().get_by_id(current_source_id)
                note_meta = NoteService(self._notes_dir).get_meta(note_id)
                source_authors = str(source.authors or "").strip()
                source_year = str(source.year or "").strip()
                meta_author = str(note_meta.get("author", "")).strip()
                meta_year = str(note_meta.get("year", "")).strip()

                effective_author = meta_author or source_authors
                effective_year = meta_year or source_year

                if not effective_author:
                    warnings.append("source_note thiếu metadata: author.")
                if not effective_year:
                    warnings.append("source_note thiếu metadata: year.")
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"Không thể kiểm tra metadata quality cho source_note id={note_id}: {exc}"
                )

        try:
            outgoing = LinkService().get_outgoing_links(note_id)
            if not outgoing and "[[" not in content:
                warnings.append("Chưa có outgoing link trong graph.")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể đọc outgoing links của note id={note_id}: {exc}")

        # Giữ thứ tự nhưng loại duplicate
        return list(dict.fromkeys(warnings))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scan_and_sync_wikilinks(self, note_id: int, content: str) -> None:
        pattern = re.compile(r"\[\[([^\[\]\n]+)\]\]")
        raw_matches = pattern.findall(content)

        target_counts: Counter[str] = Counter()
        for m in raw_matches:
            raw = m.strip()
            if "|" in raw:
                raw = raw.split("|")[0].strip()
            if "#" in raw:
                note_part = raw.split("#")[0].strip()
                if not note_part:
                    continue
                raw = note_part
            if raw:
                target_counts[raw] += 1

        note_svc = NoteService(self._notes_dir)
        link_svc = LinkService()
        active_target_ids: set[int] = set()

        all_notes = note_svc.list_all()
        notes_by_title = {
            str(n.title).strip().lower(): n
            for n in all_notes
            if getattr(n, "title", None)
        }

        for target_raw, count in target_counts.items():
            target_clean, target_note_type = self.normalize_wikilink_target(target_raw)
            slug = slugify(target_clean)
            target_note = notes_by_title.get(target_clean.lower())

            if target_note is None:
                try:
                    target_note = note_svc.get_by_slug(slug)
                except NoteNotFoundError:
                    target_note = None
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Không thể get_by_slug({slug}): {exc}")
                    target_note = None

            if target_note is None and target_clean:
                try:
                    target_note = note_svc.create_note(
                        title=target_clean,
                        note_type=target_note_type,
                        initial_content=f"# {target_clean}\n\n",
                    )
                    logger.debug(
                        f"Tạo {target_note_type} stub cho wikilink: {target_clean!r}"
                    )
                except PKMError as exc:
                    logger.debug(f"Không tạo được stub do ràng buộc: {exc}")
                    target_note = next(
                        (n for n in all_notes if n.title.lower() == target_clean.lower()),
                        None,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Không thể tạo stub note cho wikilink {target_clean!r}: {exc}")

            if target_note and target_note.id != note_id:
                active_target_ids.add(target_note.id)
                try:
                    link_svc.upsert_wikilink(note_id, target_note.id, weight=count)
                except PKMError as exc:
                    logger.debug(
                        f"Bỏ qua upsert wikilink {note_id}->{target_note.id}: {exc}"
                    )

        link_svc.cleanup_outgoing_wikilinks(note_id, active_target_ids)

    @staticmethod
    def _extract_hashtags(content: str) -> set[str]:
        pattern = re.compile(r"(?<!\w)#(?!\s)([\w\-]+)", re.UNICODE)
        return {m.group(1).strip().lower() for m in pattern.finditer(content)}

    def _sync_hashtags_to_note_tags(self, note_id: int, content: str) -> None:
        tag_svc = TagService()
        for tag in self._extract_hashtags(content):
            try:
                tag_svc.add_tag_to_note(note_id, tag)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Không thể add tag={tag} cho note id={note_id}: {exc}")

    @staticmethod
    def normalize_wikilink_target(raw_target: str) -> tuple[str, str]:
        """Chuẩn hóa title từ marker wikilink và suy ra note_type."""
        clean = raw_target.strip()
        lower = clean.lower()

        if lower.startswith("concept - "):
            clean = clean[len("concept - "):].strip()
            return clean, "concept_note"
        if lower.startswith("synthesis - "):
            stripped = clean[len("synthesis - "):].strip()
            normalized = stripped if stripped.startswith("~") else f"~ {stripped}".strip()
            return normalized, "synthesis_note"
        if lower.startswith("board - "):
            stripped = clean[len("board - "):].strip()
            normalized = stripped if stripped.startswith("!") else f"! {stripped}".strip()
            return normalized, "board_note"

        if clean.startswith("~"):
            stripped = clean[1:].strip()
            return (f"~ {stripped}" if stripped else "~", "synthesis_note")
        if clean.startswith("!"):
            stripped = clean[1:].strip()
            return (f"! {stripped}" if stripped else "!", "board_note")
        return clean, "concept_note"

    # ------------------------------------------------------------------
    # Project Mode helpers
    # ------------------------------------------------------------------

    @property
    def active_project_id(self) -> Optional[int]:
        """Trả về project đang active, hoặc None nếu đang ở Global mode."""
        return ProjectService().get_active_project_id()

    def is_project_mode(self) -> bool:
        """Trả True nếu đang có project active."""
        return self.active_project_id is not None

    def get_active_project_note_ids(self) -> set[int]:
        """Trả set note IDs thuộc project đang active (own + refs).

        Trả set rỗng nếu đang ở Global mode.
        """
        pid = self.active_project_id
        if pid is None:
            return set()
        return ProjectService().get_project_note_ids(pid)

    def create_note_in_scope(
        self,
        title: str,
        note_type: str,
        source_id: int | None = None,
        initial_content: str = "",
        save_to_project: bool = False,
    ):
        """Tạo note với scope tự động theo project mode.

        Args:
            title: Tiêu đề note.
            note_type: Loại note.
            source_id: Source PDF gắn vào (nếu có).
            initial_content: Nội dung khởi đầu.
            save_to_project: True → lưu vào project đang active (project-only note).
                             False → lưu Global (dù đang ở project mode hay không).

        Returns:
            Note đã tạo.

        Raises:
            PKMError: Nếu save_to_project=True nhưng không có project active.
        """
        project_id: int | None = None
        if save_to_project:
            pid = self.active_project_id
            if pid is None:
                raise PKMError("Không có project nào đang active. Không thể lưu project-only note.")
            project_id = pid

        note = NoteService(self._notes_dir).create_note(
            title=title,
            note_type=note_type,
            source_id=source_id,
            initial_content=initial_content,
            project_id=project_id,
        )
        scope = f"project id={project_id}" if project_id is not None else "global"
        logger.info(f"WorkspaceOrchestrator: tạo note id={note.id} scope={scope}")
        return note
