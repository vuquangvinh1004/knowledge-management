"""Màn hình Quản lý ghi chú.

Hiển thị toàn bộ note (Global + Project), hỗ trợ tạo mới,
đi tới màn hình chỉnh sửa và xóa với cảnh báo ảnh hưởng.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QTextEdit,
    QWidget,
)

from config.paths import ASSETS_DIR, NOTES_DIR
from core.services.note_service import NoteService
from core.services.project_service import ProjectService
from core.services.workspace_orchestrator import WorkspaceOrchestrator


class NoteManagementView(QWidget):
    """Quản lý note ở mức danh mục và lifecycle."""

    note_open_requested = Signal(int)
    note_deleted = Signal()
    note_created = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._project_id: int | None = None
        self._rows: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        header = QLabel("Quản lý ghi chú")
        header.setObjectName("view_header")
        layout.addWidget(header)

        top_row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Tìm theo tiêu đề, loại note hoặc phạm vi...")
        self._search_edit.textChanged.connect(lambda _text: self._apply_filter())
        top_row.addWidget(self._search_edit, stretch=1)

        self._combo_type = QComboBox()
        self._combo_type.addItem("Tất cả loại", "all")
        self._combo_type.addItem("source_note", "source_note")
        self._combo_type.addItem("concept_note", "concept_note")
        self._combo_type.addItem("synthesis_note", "synthesis_note")
        self._combo_type.addItem("board_note", "board_note")
        self._combo_type.currentIndexChanged.connect(lambda _idx: self._apply_filter())
        top_row.addWidget(self._combo_type)

        self._combo_scope = QComboBox()
        self._combo_scope.addItem("Tất cả phạm vi", "all")
        self._combo_scope.addItem("Global", "global")
        self._combo_scope.addItem("Project", "project")
        self._combo_scope.currentIndexChanged.connect(lambda _idx: self._apply_filter())
        top_row.addWidget(self._combo_scope)

        self._chk_include_deleted = QCheckBox("Bao gồm đã xóa")
        self._chk_include_deleted.toggled.connect(self._refresh_from_db)
        top_row.addWidget(self._chk_include_deleted)

        self._btn_create = QPushButton("Tạo note mới")
        self._btn_create.clicked.connect(self._create_note)
        top_row.addWidget(self._btn_create)

        self._btn_preview = QPushButton("Xem trước")
        self._btn_preview.setEnabled(False)
        self._btn_preview.clicked.connect(self._show_preview_dialog)
        top_row.addWidget(self._btn_preview)

        self._btn_edit = QPushButton("Chỉnh sửa note")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_selected_note)
        top_row.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("Xóa note")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_selected_note)
        top_row.addWidget(self._btn_delete)

        self._btn_hard_delete = QPushButton("Xóa cứng")
        self._btn_hard_delete.setEnabled(False)
        self._btn_hard_delete.clicked.connect(self._hard_delete_selected_note)
        top_row.addWidget(self._btn_hard_delete)

        layout.addLayout(top_row)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(lambda _item: self._edit_selected_note())
        layout.addWidget(self._list, stretch=1)

        self._lbl_detail = QLabel("Chọn một note để xem thông tin.")
        self._lbl_detail.setWordWrap(True)
        self._lbl_detail.setObjectName("empty_state_message")
        layout.addWidget(self._lbl_detail)

        self._preview = QTextEdit()
        self._preview.setObjectName("note_preview")
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Xem trước nội dung note sẽ hiển thị ở đây.")
        self._preview.setMinimumHeight(200)
        self._preview.setAcceptRichText(False)
        self._preview.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._preview.setTabStopDistance(self._preview.fontMetrics().horizontalAdvance(" ") * 4)
        self._preview.document().setDocumentMargin(14)
        self._preview.document().setDefaultStyleSheet(
            "body { color: #1A1A2E; font-family: 'Segoe UI'; font-size: 14px; margin: 0; padding: 0; }"
            "h1, h2, h3, h4, h5, h6 { color: #5B4B8A; font-weight: 700; margin-top: 1.0em; margin-bottom: 0.35em; }"
            "h1 { font-size: 1.55em; } h2 { font-size: 1.28em; } h3 { font-size: 1.12em; } h4, h5, h6 { font-size: 1.0em; }"
            "p, li { line-height: 1.7; margin: 0.35em 0; }"
            "ul, ol { margin-top: 0.35em; margin-bottom: 0.6em; padding-left: 1.4em; }"
            "blockquote { background: #F8EEDB; border-left: 3px solid #E7B96C; padding: 8px 12px; margin: 10px 0; color: #1F3B73; }"
            "blockquote p { margin: 0.2em 0; }"
            "code { font-family: 'Cascadia Code', 'Consolas', monospace; background: #F3F4F6; color: #111827; padding: 1px 5px; border-radius: 3px; }"
            "pre { font-family: 'Cascadia Code', 'Consolas', monospace; background: #F8FAFC; color: #111827; padding: 12px; border-radius: 8px; white-space: pre-wrap; word-wrap: break-word; }"
            "pre code { background: transparent; padding: 0; }"
            "table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }"
            "th, td { border: 1px solid #D0D4E8; padding: 6px 8px; vertical-align: top; }"
            "th { background: #F0F2F8; color: #1A1A2E; font-weight: 700; }"
            "a { color: #1D4ED8; text-decoration: none; }"
            "a:hover { text-decoration: underline; }"
        )
        layout.addWidget(self._preview)

    def set_project_context(self, project_id: int | None) -> None:
        """Nhận project mode hiện tại để default scope khi tạo note."""
        self._project_id = project_id

    def refresh(self) -> None:
        """Tải lại danh sách note từ DB."""
        self._refresh_from_db()

    def _refresh_from_db(self) -> None:
        include_deleted = bool(self._chk_include_deleted.isChecked())
        self._rows = NoteService(NOTES_DIR).list_notes_for_management(include_deleted=include_deleted)
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = (self._search_edit.text() or "").strip().lower()
        selected_type = str(self._combo_type.currentData() or "all")
        selected_scope = str(self._combo_scope.currentData() or "all")
        self._list.clear()

        rows = self._rows
        filtered: list[dict] = []
        for r in rows:
            note_type = str(r.get("note_type") or "")
            scope_label = str(r.get("scope_label") or "")

            if selected_type != "all" and note_type != selected_type:
                continue
            if selected_scope == "global" and not scope_label.startswith("Global"):
                continue
            if selected_scope == "project" and not scope_label.startswith("Project"):
                continue
            if q and (
                q not in (r.get("title") or "").lower()
                and q not in note_type.lower()
                and q not in scope_label.lower()
            ):
                continue
            filtered.append(r)

        for row in filtered:
            title = row.get("title") or "(không tiêu đề)"
            note_type = row.get("note_type") or "note"
            scope = row.get("scope_label") or "Global"
            note_id = row.get("note_id")
            deleted_marker = " [ĐÃ XÓA]" if int(row.get("is_deleted") or 0) == 1 else ""
            item = QListWidgetItem(f"[{note_type}] {title}  |  {scope}{deleted_marker}")
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self._list.addItem(item)

        self._btn_edit.setEnabled(self._list.currentItem() is not None)
        self._btn_delete.setEnabled(self._list.currentItem() is not None)
        self._btn_preview.setEnabled(self._list.currentItem() is not None)
        self._btn_hard_delete.setEnabled(self._list.currentItem() is not None)
        if self._list.count() == 0:
            self._lbl_detail.setText("Không có ghi chú phù hợp với bộ lọc hiện tại.")
            self._preview.clear()

    def _selected_note_id(self) -> int | None:
        item = self._list.currentItem()
        if item is None:
            return None
        raw = item.data(Qt.ItemDataRole.UserRole)
        return int(raw) if raw is not None else None

    def _on_selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        note_id = None
        if current is not None:
            raw = current.data(Qt.ItemDataRole.UserRole)
            note_id = int(raw) if raw is not None else None

        self._btn_edit.setEnabled(note_id is not None)
        self._btn_delete.setEnabled(note_id is not None)
        self._btn_preview.setEnabled(note_id is not None)
        self._btn_hard_delete.setEnabled(note_id is not None)

        if note_id is None:
            self._lbl_detail.setText("Chọn một note để xem thông tin.")
            self._preview.clear()
            return

        row = next((r for r in self._rows if int(r.get("note_id", -1)) == note_id), None)
        if row is None:
            self._lbl_detail.setText("Không đọc được thông tin note đã chọn.")
            self._preview.clear()
            return

        source_text = f"source_id={row.get('source_id')}" if row.get("source_id") is not None else "không gắn source"
        self._lbl_detail.setText(
            f"ID: {row.get('note_id')} | Loại: {row.get('note_type')} | "
            f"Phạm vi: {row.get('scope_label')} | {source_text}"
        )
        self._load_preview(note_id, int(row.get("is_deleted") or 0) == 1)

    def _load_preview(self, note_id: int, is_deleted: bool) -> None:
        if is_deleted:
            self._preview.setMarkdown("**Note đã soft-delete.** Chỉ có thể xem metadata hoặc xóa cứng.")
            return
        try:
            content = NoteService(NOTES_DIR).read_content(note_id)
        except Exception as exc:  # noqa: BLE001
            self._preview.setMarkdown(f"**Không thể tải preview nội dung note:** {exc}")
            return

        trimmed = content.strip()
        if len(trimmed) > 6000:
            trimmed = trimmed[:6000] + "\n\n...[đã rút gọn preview]"
        self._preview.setMarkdown(trimmed)

    def _show_preview_dialog(self) -> None:
        note_id = self._selected_note_id()
        if note_id is None:
            return
        QMessageBox.information(
            self,
            "Xem trước note",
            "Bạn có thể xem trước đầy đủ ở khung preview bên dưới danh sách trước khi chọn Chỉnh sửa.",
        )

    def _create_note(self) -> None:
        """Tạo note mới bằng NewNoteDialog."""
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        active_project_id = self._project_id
        active_project_name = None
        if active_project_id is not None:
            try:
                active_project_name = ProjectService().get_project(active_project_id).name
            except Exception:
                active_project_name = None

        dlg = NewNoteDialog(
            self,
            notes_dir=NOTES_DIR,
            current_note_title="",
            active_project_id=active_project_id,
            active_project_name=active_project_name,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        try:
            note = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR).create_note_in_scope(
                title=dlg.title_text,
                note_type=dlg.note_type,
                initial_content=dlg.content_text,
                save_to_project=(dlg.save_scope == "project"),
            )
            self.refresh()
            self.note_created.emit(int(note.id))
            QMessageBox.information(self, "Tạo note", f"Đã tạo note mới: {note.title}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo note mới:\n{exc}")

    def _edit_selected_note(self) -> None:
        """Chuyển sang màn hình chỉnh sửa note đã chọn."""
        note_id = self._selected_note_id()
        if note_id is None:
            QMessageBox.information(self, "Chỉnh sửa note", "Vui lòng chọn một note trước.")
            return

        row = next((r for r in self._rows if int(r.get("note_id", -1)) == note_id), None)
        if row is not None and int(row.get("is_deleted") or 0) == 1:
            QMessageBox.warning(
                self,
                "Chỉnh sửa note",
                "Note này đang ở trạng thái đã xóa mềm, không thể mở chỉnh sửa."
                "\nBạn có thể xóa cứng để dọn hẳn hoặc bỏ lọc 'Bao gồm đã xóa'.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Mở chỉnh sửa note",
            (
                "Bạn sắp mở note để chỉnh sửa nội dung.\n"
                "Lưu ý: thay đổi có thể ảnh hưởng wikilink, backlinks, tags và kết quả tìm kiếm.\n\n"
                "Tiếp tục?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.note_open_requested.emit(note_id)

    def _delete_selected_note(self) -> None:
        """Xóa mềm note với cảnh báo ảnh hưởng."""
        note_id = self._selected_note_id()
        if note_id is None:
            QMessageBox.information(self, "Xóa note", "Vui lòng chọn một note trước.")
            return

        svc = NoteService(NOTES_DIR)
        try:
            impact = svc.get_note_delete_impact(note_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
            return

        extra = ""
        if impact.get("is_source_note"):
            extra = (
                "\n\nLưu ý source_note:\n"
                "- Note này đang gắn với một source PDF.\n"
                "- Khi mở lại source, ứng dụng sẽ tự tạo source_note mới nếu cần."
            )

        reply = QMessageBox.warning(
            self,
            "Xác nhận xóa note",
            (
                f"Bạn sắp xóa note: {impact.get('title') or '(không tiêu đề)'}\n"
                f"Loại: {impact.get('note_type')}\n"
                f"Incoming links: {impact.get('incoming_links')}\n"
                f"Outgoing links: {impact.get('outgoing_links')}\n"
                f"Extract refs: {impact.get('extract_refs')}\n"
                f"Asset refs: {impact.get('asset_refs')}\n"
                f"Board cell refs: {impact.get('board_cell_refs')}\n"
                f"Linked boards: {impact.get('linked_boards')}\n"
                f"Project refs: {impact.get('project_refs')}"
                f"{extra}\n\n"
                "Xác nhận xóa mềm note này?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            stats = svc.cleanup_unused_notes({note_id})
            self.refresh()
            self.note_deleted.emit()
            QMessageBox.information(
                self,
                "Đã xóa note",
                (
                    "Đã áp dụng xóa mềm note.\n"
                    f"Stale links đã dọn: {stats.get('removed_stale_links', 0)}"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa note:\n{exc}")

    def _hard_delete_selected_note(self) -> None:
        """Xóa cứng note và file markdown (không thể hoàn tác)."""
        note_id = self._selected_note_id()
        if note_id is None:
            QMessageBox.information(self, "Xóa cứng", "Vui lòng chọn một note trước.")
            return

        svc = NoteService(NOTES_DIR)
        try:
            impact = svc.get_note_delete_impact(note_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
            return

        first_confirm = QMessageBox.warning(
            self,
            "CẢNH BÁO XÓA CỨNG",
            (
                "Bạn đang chọn XÓA CỨNG note.\n"
                "- Record note sẽ bị xóa khỏi DB.\n"
                "- File markdown sẽ bị xóa khỏi ổ đĩa.\n"
                "- Không thể hoàn tác.\n\n"
                f"Note: {impact.get('title') or '(không tiêu đề)'}\n"
                f"Incoming links: {impact.get('incoming_links')}\n"
                f"Outgoing links: {impact.get('outgoing_links')}\n"
                f"Extract refs: {impact.get('extract_refs')}\n"
                f"Asset refs: {impact.get('asset_refs')}\n"
                f"Board refs: {impact.get('board_cell_refs')} cells / {impact.get('linked_boards')} boards\n\n"
                "Tiếp tục xóa cứng?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if first_confirm != QMessageBox.StandardButton.Yes:
            return

        second_confirm = QMessageBox.question(
            self,
            "Xác nhận lần 2",
            "Bạn chắc chắn muốn xóa cứng note này ngay bây giờ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if second_confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            svc.hard_delete(note_id, delete_file=True)
            self.refresh()
            self.note_deleted.emit()
            QMessageBox.information(self, "Xóa cứng", "Đã xóa cứng note thành công.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa cứng note:\n{exc}")

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()
