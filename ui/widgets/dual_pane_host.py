"""Dual-pane host: tabbed PDF viewer (trái) + Markdown editor (phải).

Chịu trách nhiệm:
- Nhiều tab PDF cùng lúc — tự động đổi note khi đổi tab
- Toolbar trích xuất (văn bản / bảng / ảnh)
- Điều phối signals giữa PDF viewer và editor
- Gọi service để commit extract, lưu asset
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.pdf_viewer import (
    PDFViewerWidget,
    SELECTION_IMAGE,
    SELECTION_TABLE,
    SELECTION_TEXT,
)
from ui.widgets.markdown_editor import MarkdownEditorWidget
from core.services.workspace_orchestrator import WorkspaceOrchestrator
from core.utils.logger import get_logger

logger = get_logger()


class DualPaneHost(QWidget):
    """
    Host widget cho dual-pane làm việc — hỗ trợ nhiều tab PDF cùng lúc.

    Signals:
        source_opened(int): Phát khi source được mở lần đầu.
        all_tabs_closed: Phát khi tất cả tab PDF bị đóng.
    """

    source_opened = Signal(int)
    all_tabs_closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from config.paths import ASSETS_DIR, NOTES_DIR

        self._orchestrator = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR)
        # Per-tab data — indexed by tab position trong self._tab_widget
        self._source_ids: list[int] = []
        self._source_codes: list[str | None] = []
        self._note_ids: list[int | None] = []
        self._pdf_viewers: list[PDFViewerWidget] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setObjectName("workspace_host")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("dual_pane_splitter")

        # Tabbed PDF viewers (bên trái)
        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("source_tabs")
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tab_widget.currentChanged.connect(self._on_current_tab_changed)
        splitter.addWidget(self._tab_widget)

        self._md_editor = MarkdownEditorWidget()
        self._md_editor.set_note_actions_visible(False)
        splitter.addWidget(self._md_editor)
        splitter.setSizes([600, 600])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)
        layout.addWidget(self._build_extraction_toolbar())

    def _build_extraction_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("extraction_toolbar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)

        lay.addStretch()

        self._btn_text = QToolButton()
        self._btn_text.setText("Trích văn bản")
        self._btn_text.setToolTip(
            "Kéo chọn vùng văn bản trên PDF để trích xuất (kéo chuột)"
        )
        self._btn_text.setCheckable(True)
        self._btn_text.clicked.connect(lambda: self._activate_mode(SELECTION_TEXT))
        lay.addWidget(self._btn_text)

        self._btn_table = QToolButton()
        self._btn_table.setText("Trích bảng")
        self._btn_table.setToolTip(
            "Kéo chọn vùng chứa bảng để trích xuất và xem trước"
        )
        self._btn_table.setCheckable(True)
        self._btn_table.clicked.connect(lambda: self._activate_mode(SELECTION_TABLE))
        lay.addWidget(self._btn_table)

        self._btn_image = QToolButton()
        self._btn_image.setText("Chụp ảnh")
        self._btn_image.setToolTip("Kéo chọn vùng để chụp ảnh lưu vào assets")
        self._btn_image.setCheckable(True)
        self._btn_image.clicked.connect(lambda: self._activate_mode(SELECTION_IMAGE))
        lay.addWidget(self._btn_image)

        self._mode_btns = [self._btn_text, self._btn_table, self._btn_image]
        return bar

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_source(self, source_id: int) -> None:
        """Mở source trong tab mới hoặc chuyển sang tab đã mở (nếu có)."""
        # Already open → switch to that tab
        if source_id in self._source_ids:
            self._tab_widget.setCurrentIndex(self._source_ids.index(source_id))
            return

        try:
            source, note, recovery_notice = self._orchestrator.load_source_with_note(source_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể mở tài liệu:\n{exc}")
            return

        if recovery_notice:
            QMessageBox.information(self, "Đã tự phục hồi ghi chú", recovery_notice)

        # Tạo PDF viewer riêng cho tab này
        pdf_viewer = PDFViewerWidget()
        start_page = source.last_opened_page or 1
        pdf_viewer.open_document(Path(source.file_path), start_page)

        # Kết nối signals — ghi rõ source_id để handler biết tab nào gửi
        pdf_viewer.text_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_text_selected(sid, pg, rect)
        )
        pdf_viewer.table_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_table_selected(sid, pg, rect)
        )
        pdf_viewer.image_region_selected.connect(
            lambda pg, rect, sid=source_id: self._on_image_selected(sid, pg, rect)
        )
        pdf_viewer.page_changed.connect(
            lambda pg, sid=source_id: self._on_page_changed_for(sid, pg)
        )

        # Đồng bộ mapping trước khi phát signal currentChanged.
        self._source_ids.append(source_id)
        self._source_codes.append(source.source_code)  # AA00-ZZ99
        self._note_ids.append(note.id)
        self._pdf_viewers.append(pdf_viewer)

        # Thêm tab (tạm chặn signal để tránh race lúc tab đầu tiên).
        tab_label = (source.title or Path(source.file_path).name)[:28]
        self._tab_widget.blockSignals(True)
        idx = self._tab_widget.addTab(pdf_viewer, tab_label)
        self._tab_widget.setTabToolTip(idx, source.title or source.file_path)
        self._tab_widget.blockSignals(False)

        self._tab_widget.setCurrentIndex(idx)
        self._on_current_tab_changed(idx)
        self.source_opened.emit(source_id)

    def close_source(self) -> None:
        """Đóng tất cả các tab."""
        while self._tab_widget.count() > 0:
            self._remove_tab(0)

    def refresh_wikilink_catalog(self) -> None:
        """Làm mới popup dữ liệu [[wikilink]] ở editor."""
        self._md_editor.refresh_wikilink_catalog()

    def apply_editor_preferences(self, font_family: str, font_ligatures: bool) -> None:
        """Áp dụng cài đặt font editor cho markdown editor hiện tại."""
        self._md_editor.apply_editor_preferences(font_family, font_ligatures)

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    @property
    def _pdf_viewer(self) -> PDFViewerWidget | None:
        """PDF viewer của tab đang active."""
        idx = self._tab_widget.currentIndex()
        if 0 <= idx < len(self._pdf_viewers):
            return self._pdf_viewers[idx]
        return None

    @property
    def _source_id(self) -> int | None:
        """source_id của tab đang active."""
        idx = self._tab_widget.currentIndex()
        if 0 <= idx < len(self._source_ids):
            return self._source_ids[idx]
        return None

    @property
    def _source_code(self) -> str | None:
        """source_code (AA00-ZZ99) của tab đang active."""
        idx = self._tab_widget.currentIndex()
        if 0 <= idx < len(self._source_codes):
            return self._source_codes[idx]
        return None

    @property
    def _note_id(self) -> int | None:
        """note_id của tab đang active."""
        idx = self._tab_widget.currentIndex()
        if 0 <= idx < len(self._note_ids):
            return self._note_ids[idx]
        return None

    def _on_tab_close_requested(self, idx: int) -> None:
        self._remove_tab(idx)

    def _remove_tab(self, idx: int) -> None:
        """Xóa tab tại vị trí idx, lưu ghi chú nếu đó là tab đang active."""
        if idx < 0 or idx >= len(self._source_ids):
            return
        if idx == self._tab_widget.currentIndex():
            self._md_editor.unload_note()
        self._tab_widget.removeTab(idx)
        self._source_ids.pop(idx)
        self._source_codes.pop(idx)
        self._note_ids.pop(idx)
        self._pdf_viewers.pop(idx)
        # Sau khi xóa: load note cho tab active mới (nếu còn)
        new_idx = self._tab_widget.currentIndex()
        if new_idx >= 0:
            self._on_current_tab_changed(new_idx)
        else:
            self.all_tabs_closed.emit()

    def _on_current_tab_changed(self, idx: int) -> None:
        """Khi đổi tab: load note tương ứng vào editor."""
        if idx < 0 or idx >= len(self._source_ids):
            return
        note_id = self._note_ids[idx]
        from config.paths import NOTES_DIR
        if note_id is not None:
            self._md_editor.load_note(note_id, NOTES_DIR)

    def _on_page_changed_for(self, source_id: int, page_no: int) -> None:
        """Lưu trang đang xem vào DB cho source cụ thể."""
        self._orchestrator.update_last_opened_page(source_id, page_no)

    # ------------------------------------------------------------------
    # Extraction mode
    # ------------------------------------------------------------------

    def _activate_mode(self, mode: int) -> None:
        """Bật một chế độ chọn vùng, tắt các chế độ khác."""
        from ui.widgets.pdf_viewer import SELECTION_NONE
        viewer = self._pdf_viewer
        if viewer is None:
            return
        current_btn = {
            SELECTION_TEXT: self._btn_text,
            SELECTION_TABLE: self._btn_table,
            SELECTION_IMAGE: self._btn_image,
        }.get(mode)
        is_activating = current_btn is not None and current_btn.isChecked()
        for btn in self._mode_btns:
            btn.setChecked(False)
        if is_activating:
            current_btn.setChecked(True)  # type: ignore[union-attr]
            viewer.set_selection_mode(mode)
        else:
            viewer.set_selection_mode(SELECTION_NONE)

    # ------------------------------------------------------------------
    # Extraction handlers
    # ------------------------------------------------------------------

    def _on_text_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Trích văn bản từ vùng đã chọn → chèn vào editor."""
        if source_id not in self._source_ids:
            return
        idx = self._source_ids.index(source_id)
        viewer = self._pdf_viewers[idx]
        note_id = self._note_ids[idx]
        if not viewer.file_path or note_id is None:
            return

        from core.extraction.pdf_text import extract_region_text
        doc = viewer._doc  # truy cập nội bộ (đồng thread)
        if doc is None:
            return

        raw = extract_region_text(doc, page_no, pdf_rect)
        if not raw.strip():
            QMessageBox.information(self, "Thông tin", "Vùng đã chọn không có văn bản.")
            return

        text, anchor = self._orchestrator.prepare_text_extract(source_id, page_no, pdf_rect, raw)
        sc = self._source_codes[idx] if idx < len(self._source_codes) else None
        extract_id = self._orchestrator.commit_extract(
            source_id=source_id,
            page_no=page_no,
            extract_type="text",
            source_anchor=anchor,
            content_md=text,
            note_id=note_id,
        )

        self._md_editor.insert_extract(
            text, anchor,
            source_code=sc,
            page_no=page_no,
            extract_id=extract_id,
            rect=pdf_rect,
        )
        for btn in self._mode_btns:
            btn.setChecked(False)

    def _on_table_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Trích bảng: hiển thị preview trước khi commit."""
        if source_id not in self._source_ids:
            return
        idx = self._source_ids.index(source_id)
        viewer = self._pdf_viewers[idx]
        note_id = self._note_ids[idx]
        if not viewer.file_path or note_id is None:
            return

        from core.extraction.pdf_table import extract_table_from_region
        from core.extraction.normalizers import table_to_markdown
        from ui.widgets.dialogs.table_preview_dialog import TablePreviewDialog

        rows = extract_table_from_region(viewer.file_path, page_no, pdf_rect)
        if not rows:
            QMessageBox.information(self, "Thông tin", "Không phát hiện bảng trong vùng đã chọn.")
            for btn in self._mode_btns:
                btn.setChecked(False)
            return

        table_md = table_to_markdown(rows)
        anchor = self._orchestrator.build_anchor(source_id, page_no, pdf_rect)
        sc = self._source_codes[idx] if idx < len(self._source_codes) else None

        dlg = TablePreviewDialog(table_md, anchor, self)
        if dlg.exec():
            extract_id = self._orchestrator.commit_extract(
                source_id=source_id,
                page_no=page_no,
                extract_type="table",
                source_anchor=anchor,
                content_md=table_md,
                note_id=note_id,
            )
            self._md_editor.insert_table(
                table_md, anchor,
                source_code=sc,
                page_no=page_no,
                extract_id=extract_id,
                rect=pdf_rect,
            )

        for btn in self._mode_btns:
            btn.setChecked(False)

    def _on_image_selected(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Chụp ảnh vùng → lưu asset → chèn tham chiếu vào editor."""
        if source_id not in self._source_ids:
            return
        idx = self._source_ids.index(source_id)
        viewer = self._pdf_viewers[idx]
        note_id = self._note_ids[idx]
        if not viewer.file_path or note_id is None:
            return

        from core.extraction.pdf_image import capture_region
        doc = viewer._doc
        if doc is None:
            return

        try:
            img_bytes = capture_region(doc, page_no, pdf_rect)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể chụp ảnh:\n{exc}")
            for btn in self._mode_btns:
                btn.setChecked(False)
            return

        try:
            asset_path = self._orchestrator.save_image_asset(source_id, note_id, img_bytes)
            self._md_editor.insert_asset_ref(asset_path, "")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"Không thể lưu asset ảnh source={source_id} note={note_id} "
                f"page={page_no}: {exc}"
            )
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu ảnh:\n{exc}")

        for btn in self._mode_btns:
            btn.setChecked(False)
