"""Tab quản lý note theo loại với một khung ghi chú và document tabs."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabBar,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QMenu,
)

from config.paths import ASSETS_DIR, NOTES_DIR
from core.services.note_service import NoteService
from core.services.workspace_orchestrator import WorkspaceOrchestrator
from ui.widgets.markdown_editor import MarkdownEditorWidget


class NoteListEditorTab(QWidget):
    """Màn hình quản lý một nhóm note theo `note_type` với editor đơn."""

    note_open_requested = Signal(int)
    note_deleted = Signal()
    note_created = Signal(int)
    note_renamed = Signal(int)

    def __init__(self, note_type: str, parent=None) -> None:
        super().__init__(parent)
        self._note_type = note_type
        self._project_id: int | None = None
        self._rows: list = []
        self._filtered_rows: list = []
        self._tab_note_ids: list[int | None] = []
        self._suppress_tab_changed = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Tìm theo tiêu đề hoặc phạm vi...")
        self._search_edit.textChanged.connect(lambda _text: self._apply_filter())
        top_row.addWidget(self._search_edit, stretch=1)

        self._combo_scope = QComboBox()
        self._combo_scope.addItem("Tất cả phạm vi", "all")
        self._combo_scope.addItem("Toàn cục", "global")
        self._combo_scope.addItem("Project", "project")
        self._combo_scope.currentIndexChanged.connect(lambda _idx: self._apply_filter())
        top_row.addWidget(self._combo_scope)

        self._chk_include_deleted = QCheckBox("Bao gồm đã xóa")
        self._chk_include_deleted.toggled.connect(self._refresh_from_db)
        top_row.addWidget(self._chk_include_deleted)

        self._btn_delete = QPushButton("Xóa ghi chú")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._delete_selected_note)
        top_row.addWidget(self._btn_delete)

        self._btn_hard_delete = QPushButton("Xóa vĩnh viễn")
        self._btn_hard_delete.setEnabled(False)
        self._btn_hard_delete.clicked.connect(self._hard_delete_selected_note)
        top_row.addWidget(self._btn_hard_delete)

        layout.addLayout(top_row)

        self._doc_tabs = QTabBar()
        self._doc_tabs.setDocumentMode(True)
        self._doc_tabs.setDrawBase(False)
        self._doc_tabs.setExpanding(False)
        self._doc_tabs.setMovable(False)
        self._doc_tabs.setUsesScrollButtons(True)
        self._doc_tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._doc_tabs.currentChanged.connect(self._on_tab_changed)
        self._doc_tabs.tabBarClicked.connect(self._on_tab_clicked)
        self._doc_tabs.customContextMenuRequested.connect(self._on_doc_tabs_context_menu)
        self._setup_doc_tabs_style()
        layout.addWidget(self._doc_tabs)

        self._editor = MarkdownEditorWidget()
        self._editor.set_note_actions_visible(False)
        self._editor._empty_label.setText("Chưa có ghi chú nào trong tab hiện tại.")
        layout.addWidget(self._editor, stretch=1)

    def set_project_context(self, project_id: int | None) -> None:
        """Áp dụng project scope hiện tại cho ghi chú tạo mới."""
        self._project_id = project_id
        self.refresh()

    def refresh(self) -> None:
        """Tải lại danh sách note theo loại."""
        self._refresh_from_db()

    def _refresh_from_db(self) -> None:
        include_deleted = bool(self._chk_include_deleted.isChecked())
        self._rows = NoteService(NOTES_DIR).list_all(
            note_type=self._note_type,
            include_deleted=include_deleted,
        )
        self._apply_filter()

    def _apply_filter(self) -> None:
        q = (self._search_edit.text() or "").strip().lower()
        selected_scope = str(self._combo_scope.currentData() or "all")

        self._filtered_rows = []
        for note in self._rows:
            scope_label = "project" if note.project_id is not None else "global"
            if selected_scope != "all" and selected_scope != scope_label:
                continue
            title = (note.title or "").lower()
            if q and q not in title and q not in scope_label:
                continue
            self._filtered_rows.append(note)

        self._reload_tabs()

    def _setup_doc_tabs_style(self) -> None:
        """Cấu hình style cho tab tài liệu theo loại note."""
        if self._note_type == "concept_note":
            selected_color = "#2A712D"  # giảm sáng ~10% so với #2E7D32
            unselected_color = "#256328"  # giảm sáng thêm cho tab chưa chọn
        else:
            selected_color = "#1259AA"  # giảm sáng ~10% so với #1565C0
            unselected_color = "#104F97"  # giảm sáng thêm cho tab chưa chọn
        
        style = (
            f"QTabBar::tab {{"
            f"  background-color: {unselected_color};"
            f"  color: #FFFFFF;"
            f"  padding: 2px 12px;"
            f"  min-height: 22px;"
            f"  max-height: 22px;"
            f"  margin-right: 2px;"
            f"  border: 1px solid {selected_color};"
            f"  border-radius: 4px;"
            f"}}"
            f"QTabBar::tab:selected {{"
            f"  background-color: {selected_color};"
            f"}}"
        )
        self._doc_tabs.setStyleSheet(style)

    def _reload_tabs(self, preferred_note_id: int | None = None) -> None:
        current_note_id = preferred_note_id
        if current_note_id is None:
            current_note_id = self._current_tab_note_id()

        self._suppress_tab_changed = True
        while self._doc_tabs.count() > 0:
            self._doc_tabs.removeTab(0)
        self._tab_note_ids.clear()

        for note in self._filtered_rows:
            title = (note.title or "(không tiêu đề)").strip()
            is_deleted = bool(getattr(note, "is_deleted", 0))
            visible_title = f"[Đã xóa] {title}" if is_deleted else title
            tab_text = visible_title if len(visible_title) <= 28 else f"{visible_title[:27]}..."
            idx = self._doc_tabs.addTab(tab_text)
            state_text = "ĐÃ XÓA MỀM" if is_deleted else "ĐANG SỬ DỤNG"
            self._doc_tabs.setTabToolTip(idx, f"ID {note.id} | {title} | {state_text}")
            if is_deleted:
                # Tông vàng sáng giúp tương phản tốt trên nền tab xanh lá/xanh dương.
                self._doc_tabs.setTabTextColor(idx, QColor("#FFF59D"))
            self._tab_note_ids.append(int(note.id))

        create_idx = self._doc_tabs.addTab("Tạo ghi chú mới")
        self._doc_tabs.setTabToolTip(create_idx, "Tạo ghi chú mới")
        self._tab_note_ids.append(None)
        self._suppress_tab_changed = False

        has_note_tabs = bool(self._filtered_rows)
        self._btn_delete.setEnabled(has_note_tabs)
        self._btn_hard_delete.setEnabled(has_note_tabs)

        if not has_note_tabs:
            self._editor.unload_note()
            self._set_current_tab(0)
            return

        target_idx = 0
        if current_note_id is not None and current_note_id in self._tab_note_ids:
            target_idx = self._tab_note_ids.index(current_note_id)
        self._set_current_tab(target_idx)
        self._load_note_for_index(target_idx)

    def _set_current_tab(self, idx: int) -> None:
        self._suppress_tab_changed = True
        self._doc_tabs.setCurrentIndex(idx)
        self._suppress_tab_changed = False

    def _current_tab_note_id(self) -> int | None:
        idx = self._doc_tabs.currentIndex()
        if idx < 0 or idx >= len(self._tab_note_ids):
            return None
        return self._tab_note_ids[idx]

    def _on_tab_changed(self, idx: int) -> None:
        if self._suppress_tab_changed:
            return
        if idx < 0 or idx >= len(self._tab_note_ids):
            return

        note_id = self._tab_note_ids[idx]
        if note_id is None:
            created_note_id = self._quick_create_note()
            if created_note_id is None:
                if self._filtered_rows:
                    self._set_current_tab(0)
                    self._load_note_for_index(0)
                else:
                    self._editor.unload_note()
            return

        self._load_note_for_index(idx)

    def _on_tab_clicked(self, idx: int) -> None:
        """Xử lý click lặp lại trên tab Tạo ghi chú mới khi tab này đang được chọn."""
        if self._suppress_tab_changed:
            return
        if idx < 0 or idx >= len(self._tab_note_ids):
            return
        if idx != self._doc_tabs.currentIndex():
            return

        note_id = self._tab_note_ids[idx]
        if note_id is not None:
            return

        created_note_id = self._quick_create_note()
        if created_note_id is None:
            if self._filtered_rows:
                self._set_current_tab(0)
                self._load_note_for_index(0)
            else:
                self._editor.unload_note()

    def _on_doc_tabs_context_menu(self, pos) -> None:
        """Mở context menu cho tab note: hỗ trợ Sửa tên như worksheet trong Excel."""
        idx = self._doc_tabs.tabAt(pos)
        if idx < 0 or idx >= len(self._tab_note_ids):
            return

        note_id = self._tab_note_ids[idx]
        if note_id is None:
            return

        # Đồng bộ tab được tác động trước khi mở menu, để hành vi giống tab worksheet.
        if idx != self._doc_tabs.currentIndex():
            self._set_current_tab(idx)
            self._load_note_for_index(idx)

        menu = QMenu(self)
        action_rename = menu.addAction("Sửa tên")
        chosen = menu.exec(self._doc_tabs.mapToGlobal(pos))
        if chosen == action_rename:
            self._rename_tab_note_by_index(idx)

    def _rename_tab_note_by_index(self, idx: int) -> None:
        """Đổi tên note từ tab context menu và đồng bộ ngay toàn ứng dụng."""
        if idx < 0 or idx >= len(self._tab_note_ids):
            return

        note_id = self._tab_note_ids[idx]
        if note_id is None:
            return

        note_row = next((n for n in self._filtered_rows if int(n.id) == int(note_id)), None)
        current_title = str(getattr(note_row, "title", "") or "")

        new_title, ok = QInputDialog.getText(
            self,
            "Sửa tên ghi chú",
            "Nhập tên mới:",
            text=current_title,
        )
        if not ok:
            return

        normalized = new_title.strip()
        if not normalized:
            QMessageBox.warning(self, "Sửa tên", "Tên ghi chú không được để trống.")
            return
        if normalized == current_title:
            return

        try:
            NoteService(NOTES_DIR).update_title(int(note_id), normalized)
            self.refresh()
            if int(note_id) in self._tab_note_ids:
                new_idx = self._tab_note_ids.index(int(note_id))
                self._set_current_tab(new_idx)
                self._load_note_for_index(new_idx)
            self.note_renamed.emit(int(note_id))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể sửa tên ghi chú:\n{exc}")

    def _quick_create_note(self) -> int | None:
        """Tạo ghi chú mới trực tiếp, template hiển thị ở editor thay vì popup template."""
        if self._note_type == "concept_note":
            default_title = "Khái niệm mới"
            prompt = "Nhập tiêu đề ghi chú khái niệm:"
        elif self._note_type == "synthesis_note":
            default_title = "Câu hỏi tổng hợp mới"
            prompt = "Nhập tiêu đề ghi chú tổng hợp:"
        else:
            default_title = "Ghi chú mới"
            prompt = "Nhập tiêu đề ghi chú:"

        title_text, ok = QInputDialog.getText(self, "Tạo ghi chú mới", prompt, text=default_title)
        if not ok:
            return None
        title = title_text.strip() or default_title

        save_to_project = self._project_id is not None
        try:
            note = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR).create_note_in_scope(
                title=title,
                note_type=self._note_type,
                initial_content="",
                save_to_project=save_to_project,
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo ghi chú mới:\n{exc}")
            return None

        self.refresh()
        new_note_id = int(note.id)
        if new_note_id in self._tab_note_ids:
            idx = self._tab_note_ids.index(new_note_id)
            self._set_current_tab(idx)
            self._load_note_for_index(idx)
        self.note_created.emit(new_note_id)
        return new_note_id

    def _load_note_for_index(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._tab_note_ids):
            self._editor.unload_note()
            self._btn_delete.setEnabled(False)
            self._btn_hard_delete.setEnabled(False)
            return

        note_id = self._tab_note_ids[idx]
        if note_id is None:
            self._editor.unload_note()
            self._btn_delete.setEnabled(False)
            self._btn_hard_delete.setEnabled(False)
            return

        note_row = next((n for n in self._filtered_rows if int(n.id) == int(note_id)), None)
        is_deleted = bool(getattr(note_row, "is_deleted", 0)) if note_row is not None else False

        self._btn_delete.setEnabled(not is_deleted)
        self._btn_hard_delete.setEnabled(True)

        if is_deleted:
            title = str(getattr(note_row, "title", "Ghi chú") or "Ghi chú")
            self._editor.enable_scratch_mode(f"{title} (đã xóa mềm)")
            self._editor.set_markdown_content(
                "Ghi chú này đã bị xóa mềm.\n"
                "Bạn có thể dùng nút 'Xóa cứng' để xóa hoàn toàn khỏi hệ thống."
            )
            return

        try:
            self._editor.load_note(int(note_id), NOTES_DIR)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể mở ghi chú:\n{exc}")

    def _delete_selected_note(self) -> None:
        note_id = self._current_tab_note_id()
        if note_id is None:
            return

        svc = NoteService(NOTES_DIR)
        try:
            impact = svc.get_note_delete_impact(int(note_id))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
            return

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
                f"Project refs: {impact.get('project_refs')}\n\n"
                "Xác nhận xóa mềm ghi chú này?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            svc.cleanup_unused_notes({int(note_id)})
            self.refresh()
            self.note_deleted.emit()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa ghi chú:\n{exc}")

    def _hard_delete_selected_note(self) -> None:
        note_id = self._current_tab_note_id()
        if note_id is None:
            return

        svc = NoteService(NOTES_DIR)
        try:
            impact = svc.get_note_delete_impact(int(note_id))
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
                "Bạn chắc chắn muốn xóa vĩnh viễn ghi chú này ngay bây giờ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if second_confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            svc.hard_delete(int(note_id), delete_file=True)
            self.refresh()
            self.note_deleted.emit()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa vĩnh viễn ghi chú:\n{exc}")
