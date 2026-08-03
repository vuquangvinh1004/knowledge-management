"""Không gian làm việc nháp: PDF tham khảo nhiều tab + editor markdown file-based."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QMenu,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.services.markdown_snippet_service import MarkdownSnippetService
from core.services.source_service import SourceService
from core.services.workspace_orchestrator import WorkspaceOrchestrator
from ui.widgets.markdown_editor import MarkdownEditorWidget
from ui.widgets.pdf_viewer import (
    PDFViewerWidget,
    SELECTION_IMAGE,
    SELECTION_NONE,
    SELECTION_TABLE,
    SELECTION_TEXT,
)


class DraftWorkspaceView(QWidget):
    """Workspace gồm 2 khung độc lập: PDF tham khảo (trái) và editor nháp (phải)."""

    source_opened = Signal(int)
    import_requested = Signal()
    text_extract_requested = Signal(int, int, tuple)
    table_extract_requested = Signal(int, int, tuple)
    image_extract_requested = Signal(int, int, tuple)
    source_page_changed_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        from config.paths import ASSETS_DIR, NOTES_DIR

        self._orchestrator = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR)
        self._snippet_service = MarkdownSnippetService()
        self._project_id: int | None = None
        self._source_ids: list[int] = []
        self._source_codes: list[str | None] = []
        self._pdf_viewers: list[PDFViewerWidget] = []
        self._scratch_file_path: Path | None = None
        self._read_focus_mode = False
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(12, 8, 12, 8)
        header_lay.setSpacing(8)

        self._btn_new_md = QPushButton("Tệp mới")
        self._btn_new_md.setToolTip("Tạo tệp soạn thảo Markdown mới")
        self._btn_new_md.clicked.connect(self._new_scratch_file)

        self._btn_open_md = QPushButton("Mở tệp Markdown")
        self._btn_open_md.setToolTip("Mở tệp Markdown (.md)")
        self._btn_open_md.clicked.connect(self._open_scratch_file)

        self._btn_save_md = QPushButton("Lưu")
        self._btn_save_md.setToolTip("Lưu tệp Markdown hiện tại (Ctrl+S)")
        self._btn_save_md.setObjectName("primary_button")
        self._btn_save_md.clicked.connect(self.request_save_scratch_file)

        self._btn_save_as_md = QPushButton("Lưu thành...")
        self._btn_save_as_md.setToolTip("Lưu thành tệp Markdown khác (Ctrl+Shift+S)")
        self._btn_save_as_md.clicked.connect(lambda: self.request_save_scratch_file(force_pick_path=True))

        self._btn_extract_text = QPushButton("Trích văn bản")
        self._btn_extract_text.setToolTip("Kéo chọn vùng văn bản trên PDF đang mở")
        self._btn_extract_text.setCheckable(True)
        self._btn_extract_text.setProperty("workspaceRole", "extract-action")
        self._btn_extract_text.clicked.connect(lambda: self._activate_extraction_mode(SELECTION_TEXT))
        header_lay.addWidget(self._btn_extract_text)

        self._btn_extract_table = QPushButton("Trích bảng")
        self._btn_extract_table.setToolTip("Kéo chọn vùng bảng trên PDF đang mở")
        self._btn_extract_table.setCheckable(True)
        self._btn_extract_table.setProperty("workspaceRole", "extract-action")
        self._btn_extract_table.clicked.connect(lambda: self._activate_extraction_mode(SELECTION_TABLE))
        header_lay.addWidget(self._btn_extract_table)

        self._btn_capture_image = QPushButton("Chụp ảnh")
        self._btn_capture_image.setToolTip("Kéo chọn vùng ảnh trên PDF đang mở")
        self._btn_capture_image.setCheckable(True)
        self._btn_capture_image.setProperty("workspaceRole", "extract-action")
        self._btn_capture_image.clicked.connect(lambda: self._activate_extraction_mode(SELECTION_IMAGE))
        header_lay.addWidget(self._btn_capture_image)

        self._btn_read_focus = QPushButton("Tập trung đọc")
        self._btn_read_focus.setToolTip("Ẩn/hiện thanh điều hướng PDF để tăng không gian đọc")
        self._btn_read_focus.setProperty("workspaceRole", "extract-action")
        self._btn_read_focus.clicked.connect(self._toggle_read_focus_mode)
        header_lay.addWidget(self._btn_read_focus)

        self._lbl_scratch_status = QLabel("")
        self._lbl_scratch_status.setObjectName("editor_save_status")
        header_lay.addStretch()
        header_lay.addWidget(self._lbl_scratch_status)
        header_lay.addWidget(self._btn_new_md)
        header_lay.addWidget(self._btn_open_md)
        header_lay.addWidget(self._btn_save_md)
        header_lay.addWidget(self._btn_save_as_md)

        self._btn_toggle_left = QPushButton("Tài liệu")
        self._btn_toggle_left.setToolTip("Ẩn/hiện panel tài liệu tham khảo")
        self._btn_toggle_left.clicked.connect(self._toggle_reference_panel)
        header_lay.addWidget(self._btn_toggle_left)

        self._btn_close_all_refs = QPushButton("Đóng tất cả")
        self._btn_close_all_refs.setToolTip("Đóng tất cả tài liệu tham khảo đang mở")
        self._btn_close_all_refs.clicked.connect(self._close_all_reference_tabs)
        header_lay.addWidget(self._btn_close_all_refs)

        self._btn_toggle_right = QPushButton("Soạn thảo")
        self._btn_toggle_right.setToolTip("Ẩn/hiện panel soạn thảo")
        self._btn_toggle_right.clicked.connect(self._toggle_editor_panel)
        header_lay.addWidget(self._btn_toggle_right)

        self._btn_insert_snippet = QPushButton("Chèn...")
        self._btn_insert_snippet.setToolTip("Chèn nhanh mẫu Markdown vào vùng soạn thảo")
        self._btn_insert_snippet.setProperty("workspaceRole", "insert-action")
        self._btn_insert_snippet.clicked.connect(self._open_insert_menu)
        header_lay.addWidget(self._btn_insert_snippet)

        layout.addWidget(header)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)

        self._left_panel = QWidget()
        left_lay = QVBoxLayout(self._left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)
        self._pdf_tabs = QTabWidget()
        self._pdf_tabs.setObjectName("workspace_ref_tabs")
        self._pdf_tabs.setTabsClosable(True)
        self._pdf_tabs.setMovable(True)
        self._pdf_tabs.currentChanged.connect(self._on_reference_tab_changed)
        self._pdf_tabs.tabCloseRequested.connect(self._close_reference_tab)
        left_lay.addWidget(self._pdf_tabs)

        self._right_panel = QWidget()
        right_lay = QVBoxLayout(self._right_panel)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        self._draft_editor = MarkdownEditorWidget()
        self._draft_editor.enable_scratch_mode(self._editor_title())
        self._draft_editor.set_markdown_content("")
        self._draft_editor.content_changed.connect(self._on_editor_content_changed)
        right_lay.addWidget(self._draft_editor)

        self._splitter.addWidget(self._left_panel)
        self._splitter.addWidget(self._right_panel)
        self._splitter.setSizes([640, 760])
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)
        layout.addWidget(self._splitter, stretch=1)

        self._update_panel_toggle_labels()
        self._update_scratch_status_label()

    def _setup_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        save_shortcut.activated.connect(self.request_save_scratch_file)

        save_as_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        save_as_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        save_as_shortcut.activated.connect(lambda: self.request_save_scratch_file(force_pick_path=True))

    def set_project_context(self, project_id: int | None) -> None:
        """Giữ context project để thống nhất hành vi với MainWindow."""
        self._project_id = project_id

    def open_reference_source(self, source_id: int) -> None:
        """Mở source PDF vào panel tham khảo bên trái (nhiều tab)."""
        if source_id in self._source_ids:
            self._pdf_tabs.setCurrentIndex(self._source_ids.index(source_id))
            self._left_panel.setVisible(True)
            self._normalize_splitter_sizes()
            self._update_panel_toggle_labels()
            return

        try:
            source = SourceService().get_by_id(source_id)
            file_path = Path(str(source.file_path))
            if not file_path.exists():
                raise FileNotFoundError(f"Không tìm thấy file PDF: {file_path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể mở tài liệu tham khảo:\n{exc}")
            return

        viewer = PDFViewerWidget()
        start_page_raw = getattr(source, "last_opened_page", 1)
        start_page = int(start_page_raw) if isinstance(start_page_raw, int) else 1
        viewer.open_document(file_path, start_page)
        viewer.set_compact_navigation(True)
        viewer.set_navigation_visible(not self._read_focus_mode)
        viewer.text_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_text_selected(sid, pg, rect)
        )
        viewer.table_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_table_selected(sid, pg, rect)
        )
        viewer.image_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_image_selected(sid, pg, rect)
        )
        viewer.page_changed.connect(lambda pg, sid=source_id: self._on_source_page_changed(sid, pg))

        self._source_ids.append(source_id)
        self._source_codes.append(getattr(source, "source_code", None))
        self._pdf_viewers.append(viewer)
        tab_title = (str(source.title or file_path.name) or "Tài liệu").strip()[:30]
        tab_idx = self._pdf_tabs.addTab(viewer, tab_title)
        self._pdf_tabs.setTabToolTip(tab_idx, str(file_path))
        self._pdf_tabs.setCurrentIndex(tab_idx)

        self._left_panel.setVisible(True)
        self._normalize_splitter_sizes()
        self._update_panel_toggle_labels()
        self.source_opened.emit(source_id)

    def request_save_scratch_file(self, force_pick_path: bool = False) -> bool:
        """Lưu file markdown nháp, trả về True nếu lưu thành công hoặc không có thay đổi."""
        if not self._draft_editor.has_unsaved_changes() and not force_pick_path and self._scratch_file_path:
            self._update_scratch_status_label()
            return True

        file_path = self._scratch_file_path
        if force_pick_path or file_path is None:
            selected, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu tệp Markdown",
                str((self._scratch_file_path or Path.cwd() / "workspace-nhap.md")),
                "Markdown (*.md)",
            )
            if not selected:
                return False
            file_path = Path(selected)

        try:
            file_path.write_text(self._draft_editor.get_content(), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu tệp Markdown:\n{exc}")
            return False

        self._scratch_file_path = file_path
        self._draft_editor.mark_saved()
        self._draft_editor.set_editor_title(self._editor_title())
        self._update_scratch_status_label()
        return True

    def confirm_close_with_unsaved_changes(self) -> bool:
        """Xác nhận lưu file markdown trước khi đóng ứng dụng."""
        if not self._draft_editor.has_unsaved_changes():
            return True

        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setWindowTitle("Lưu tệp Markdown")
        dlg.setText("Nội dung soạn thảo trong Không gian làm việc chưa được lưu.")
        dlg.setInformativeText("Bạn muốn lưu tệp .md trước khi đóng ứng dụng không?")

        btn_save = dlg.addButton("Lưu", QMessageBox.ButtonRole.AcceptRole)
        btn_discard = dlg.addButton("Không lưu", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = dlg.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(btn_save)
        dlg.exec()

        clicked = dlg.clickedButton()
        if clicked is btn_save:
            return self.request_save_scratch_file()
        if clicked is btn_discard:
            return True
        if clicked is btn_cancel:
            return False
        return False

    def apply_editor_preferences(self, font_family: str, font_ligatures: bool, font_size: int) -> None:
        """Áp dụng font editor cho khung soạn thảo workspace."""
        self._draft_editor.apply_editor_preferences(font_family, font_ligatures, font_size)

    def refresh_wikilink_catalog(self) -> None:
        """Làm mới dữ liệu wikilink tương tự các note editor khác."""
        self._draft_editor.refresh_wikilink_catalog()

    def current_pdf_viewer(self) -> PDFViewerWidget | None:
        """Trả về viewer PDF đang được chọn, nếu có."""
        idx = self._current_reference_index()
        if 0 <= idx < len(self._pdf_viewers):
            return self._pdf_viewers[idx]
        return None

    def pdf_viewer_for_source(self, source_id: int) -> PDFViewerWidget | None:
        """Lấy viewer PDF theo source_id."""
        if source_id not in self._source_ids:
            return None
        idx = self._source_ids.index(source_id)
        if 0 <= idx < len(self._pdf_viewers):
            return self._pdf_viewers[idx]
        return None

    def source_code_for_source(self, source_id: int) -> str | None:
        """Lấy source code theo source_id."""
        if source_id not in self._source_ids:
            return None
        idx = self._source_ids.index(source_id)
        return self._source_codes[idx] if idx < len(self._source_codes) else None

    def _open_scratch_file(self) -> None:
        if not self._confirm_replace_unsaved_content():
            return

        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Mở tệp Markdown",
            str(Path.cwd()),
            "Markdown (*.md)",
        )
        if not selected:
            return

        file_path = Path(selected)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể mở tệp Markdown:\n{exc}")
            return

        self._scratch_file_path = file_path
        self._draft_editor.enable_scratch_mode(self._editor_title())
        self._draft_editor.set_markdown_content(content)
        self._update_scratch_status_label()

    def _new_scratch_file(self) -> None:
        if not self._confirm_replace_unsaved_content():
            return
        self._scratch_file_path = None
        self._draft_editor.enable_scratch_mode(self._editor_title())
        self._draft_editor.set_markdown_content("")
        self._update_scratch_status_label()

    def _confirm_replace_unsaved_content(self) -> bool:
        """Xác nhận trước khi thay nội dung editor hiện tại."""
        if not self._draft_editor.has_unsaved_changes():
            return True

        reply = QMessageBox.question(
            self,
            "Nội dung chưa lưu",
            "Nội dung hiện tại chưa lưu. Bạn có muốn lưu trước khi tiếp tục không?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            return self.request_save_scratch_file()
        if reply == QMessageBox.StandardButton.No:
            return True
        return False

    def _close_reference_tab(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._source_ids):
            return
        widget = self._pdf_tabs.widget(idx)
        self._pdf_tabs.removeTab(idx)
        self._source_ids.pop(idx)
        self._source_codes.pop(idx)
        self._pdf_viewers.pop(idx)
        if widget is not None:
            widget.deleteLater()
        self._reset_extraction_mode()
        self._update_panel_toggle_labels()

    def _close_all_reference_tabs(self) -> None:
        while self._pdf_tabs.count() > 0:
            self._close_reference_tab(0)

    def _toggle_read_focus_mode(self) -> None:
        self._read_focus_mode = not self._read_focus_mode
        for viewer in self._pdf_viewers:
            viewer.set_navigation_visible(not self._read_focus_mode)
        self._update_panel_toggle_labels()

    def _current_reference_index(self) -> int:
        return self._pdf_tabs.currentIndex()

    def _current_pdf_viewer(self) -> PDFViewerWidget | None:
        idx = self._current_reference_index()
        if 0 <= idx < len(self._pdf_viewers):
            return self._pdf_viewers[idx]
        return None

    def _activate_extraction_mode(self, mode: int) -> None:
        viewer = self._current_pdf_viewer()
        if viewer is None:
            self._reset_extraction_mode()
            return

        button_map = {
            SELECTION_TEXT: self._btn_extract_text,
            SELECTION_TABLE: self._btn_extract_table,
            SELECTION_IMAGE: self._btn_capture_image,
        }
        current_btn = button_map.get(mode)
        is_activating = current_btn is not None and current_btn.isChecked()

        self._btn_extract_text.setChecked(False)
        self._btn_extract_table.setChecked(False)
        self._btn_capture_image.setChecked(False)

        if is_activating and current_btn is not None:
            current_btn.setChecked(True)
            viewer.set_selection_mode(mode)
        else:
            viewer.set_selection_mode(SELECTION_NONE)

    def _reset_extraction_mode(self) -> None:
        self._btn_extract_text.setChecked(False)
        self._btn_extract_table.setChecked(False)
        self._btn_capture_image.setChecked(False)
        viewer = self._current_pdf_viewer()
        if viewer is not None:
            viewer.set_selection_mode(SELECTION_NONE)

    def _on_reference_tab_changed(self, _idx: int) -> None:
        self._reset_extraction_mode()

    def _on_text_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        if source_id not in self._source_ids:
            return
        self.text_extract_requested.emit(source_id, page_no, pdf_rect)
        self._reset_extraction_mode()

    def _on_table_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        if source_id not in self._source_ids:
            return
        self.table_extract_requested.emit(source_id, page_no, pdf_rect)
        self._reset_extraction_mode()

    def _on_image_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        if source_id not in self._source_ids:
            return
        self.image_extract_requested.emit(source_id, page_no, pdf_rect)
        self._reset_extraction_mode()

    def _on_source_page_changed(self, source_id: int, page_no: int) -> None:
        self.source_page_changed_requested.emit(source_id, page_no)

    def _toggle_reference_panel(self) -> None:
        if self._left_panel.isVisible() and not self._right_panel.isVisible():
            return
        self._left_panel.setVisible(not self._left_panel.isVisible())
        self._normalize_splitter_sizes()
        self._update_panel_toggle_labels()

    def _toggle_editor_panel(self) -> None:
        if self._right_panel.isVisible() and not self._left_panel.isVisible():
            return
        self._right_panel.setVisible(not self._right_panel.isVisible())
        self._normalize_splitter_sizes()
        self._update_panel_toggle_labels()

    def _normalize_splitter_sizes(self) -> None:
        left_visible = self._left_panel.isVisible()
        right_visible = self._right_panel.isVisible()
        if left_visible and right_visible:
            self._splitter.setSizes([640, 760])
        elif left_visible:
            self._splitter.setSizes([1, 0])
        elif right_visible:
            self._splitter.setSizes([0, 1])

    def _update_panel_toggle_labels(self) -> None:
        has_refs = self._pdf_tabs.count() > 0

        self._btn_toggle_left.setEnabled(has_refs)
        if not has_refs:
            self._btn_toggle_left.setToolTip("Chưa mở tài liệu tham khảo")
        elif self._left_panel.isVisible():
            self._btn_toggle_left.setToolTip("Ẩn tài liệu tham khảo")
        else:
            self._btn_toggle_left.setToolTip("Hiện tài liệu tham khảo")

        self._btn_toggle_right.setToolTip(
            "Ẩn khung soạn thảo" if self._right_panel.isVisible() else "Hiện khung soạn thảo"
        )
        self._btn_close_all_refs.setEnabled(has_refs)
        self._btn_extract_text.setEnabled(has_refs)
        self._btn_extract_table.setEnabled(has_refs)
        self._btn_capture_image.setEnabled(has_refs)

        self._btn_read_focus.setEnabled(has_refs)
        if not has_refs:
            self._btn_read_focus.setToolTip("Chưa mở tài liệu tham khảo")
        elif self._read_focus_mode:
            self._btn_read_focus.setToolTip("Thoát chế độ tập trung đọc")
        else:
            self._btn_read_focus.setToolTip("Bật chế độ tập trung đọc")

    def _on_editor_content_changed(self) -> None:
        self._update_scratch_status_label()

    def _update_scratch_status_label(self) -> None:
        has_unsaved = self._draft_editor.has_unsaved_changes()
        current_content = self._draft_editor.get_content().strip()

        # Tránh hiển thị trạng thái mặc định khi chưa có nội dung và chưa có file đích.
        if self._scratch_file_path is None and not has_unsaved and not current_content:
            self._lbl_scratch_status.setVisible(False)
            self._lbl_scratch_status.setText("")
            self._lbl_scratch_status.setToolTip("")
            self._draft_editor.set_save_status_text("")
            return

        self._lbl_scratch_status.setVisible(True)

        if self._scratch_file_path is None:
            self._lbl_scratch_status.setText("Tệp nháp chưa lưu*")
            self._lbl_scratch_status.setToolTip("Tệp markdown chưa được chọn đường dẫn lưu.")
            self._draft_editor.set_save_status_text("Chưa lưu*")
            return

        file_name = self._scratch_file_path.name
        if has_unsaved:
            text = f"{file_name} • Chưa lưu*"
            editor_status = "Chưa lưu*"
        else:
            text = file_name
            editor_status = "Đã lưu"

        self._lbl_scratch_status.setText(text)
        self._lbl_scratch_status.setToolTip(str(self._scratch_file_path))
        self._draft_editor.set_save_status_text(editor_status)

    def _editor_title(self) -> str:
        if self._scratch_file_path is None:
            return "Soạn thảo tạm thời (chưa lưu)"
        return f"Soạn thảo: {self._scratch_file_path.name}"

    def _build_insert_menu(self) -> QMenu:
        menu = QMenu(self)
        for snippet in self._snippet_service.list_visible():
            action = menu.addAction(snippet.name)
            action.triggered.connect(
                lambda _checked=False, snippet_id=snippet.snippet_id: self._insert_snippet(snippet_id)
            )
        menu.addSeparator()
        customize_action = menu.addAction("Tùy chỉnh...")
        customize_action.triggered.connect(self._open_snippet_customize_dialog)
        return menu

    def _open_insert_menu(self) -> None:
        menu = self._build_insert_menu()
        menu.exec(self._btn_insert_snippet.mapToGlobal(self._btn_insert_snippet.rect().bottomLeft()))

    def _insert_snippet(self, snippet_id: str) -> None:
        snippet = self._snippet_service.get_by_id(snippet_id)
        if snippet is None:
            return
        if not self._right_panel.isVisible():
            self._right_panel.setVisible(True)
            self._normalize_splitter_sizes()
            self._update_panel_toggle_labels()
        self._draft_editor.insert_snippet(snippet.template)

    def _open_snippet_customize_dialog(self) -> None:
        from ui.widgets.dialogs.markdown_snippet_dialog import MarkdownSnippetCustomizeDialog

        dlg = MarkdownSnippetCustomizeDialog(self._snippet_service, self)
        dlg.exec()
