"""Widget hiển thị và tương tác với file PDF.

Sử dụng PyMuPDF để render trang thành pixmap.
Business logic (extract service, lưu DB) KHÔNG ở đây — chỉ render và phát tín hiệu.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QPoint, QRect, QSize, Signal
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QRubberBand,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# Inner widget: trang PDF có thể chọn vùng
# ---------------------------------------------------------------------------

class _PDFPageLabel(QLabel):
    """QLabel chứa pixmap trang PDF, hỗ trợ rubber-band selection."""

    region_selected = Signal(QRect)  # pixel coordinates trong label

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selection_active = False
        self._origin: QPoint | None = None
        self._rubber = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_selection_active(self, enabled: bool) -> None:
        self._selection_active = enabled
        cursor = Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor
        self.setCursor(cursor)
        if not enabled:
            self._rubber.hide()
            self._origin = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.setFocus()
        if self._selection_active and event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._rubber.setGeometry(QRect(self._origin, QSize()))
            self._rubber.show()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._selection_active and self._origin is not None:
            rect = QRect(self._origin, event.pos()).normalized()
            self._rubber.setGeometry(rect)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if (
            self._selection_active
            and self._origin is not None
            and event.button() == Qt.MouseButton.LeftButton
        ):
            rect = QRect(self._origin, event.pos()).normalized()
            self._rubber.hide()
            self._origin = None
            if rect.width() > 4 and rect.height() > 4:
                self.region_selected.emit(rect)


# ---------------------------------------------------------------------------
# Public widget
# ---------------------------------------------------------------------------

# Chế độ chọn vùng
SELECTION_NONE = 0
SELECTION_TEXT = 1
SELECTION_TABLE = 2
SELECTION_IMAGE = 3

_ZOOM_STEPS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
_DEFAULT_ZOOM_INDEX = 4  # 1.5


class PDFViewerWidget(QWidget):
    """
    Widget hiển thị PDF nhiều trang với hỗ trợ:
    - Chuyển trang (trước/sau/nhảy tới)
    - Zoom in/out
    - Chọn vùng để trích xuất văn bản / bảng / ảnh
    """

    # Phát khi người dùng chọn vùng theo từng mode
    text_region_selected = Signal(int, tuple)   # (page_no, pdf_rect)
    table_region_selected = Signal(int, tuple)  # (page_no, pdf_rect)
    image_region_selected = Signal(int, tuple)  # (page_no, pdf_rect)
    page_changed = Signal(int)                  # page_no (1-based)
    document_loaded = Signal(int)               # total_pages

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doc: Any | None = None
        self._file_path: Path | None = None
        self._current_page = 1
        self._total_pages = 0
        self._zoom_index = _DEFAULT_ZOOM_INDEX
        self._selection_mode = SELECTION_NONE
        self._build_ui()
        self._setup_shortcuts()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._nav_bar = self._build_nav_bar()
        layout.addWidget(self._nav_bar)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._page_label = _PDFPageLabel()
        self._page_label.region_selected.connect(self._on_rubber_band_selection)
        self._scroll.setWidget(self._page_label)

        layout.addWidget(self._scroll)

        self._empty_label = QLabel("Chưa có tài liệu nào.\nMở PDF để bắt đầu.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setObjectName("empty_state_message")
        layout.addWidget(self._empty_label)

        self._set_document_loaded(False)
        self.set_compact_navigation(False)

    def _build_nav_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("pdf_nav_bar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(4)

        self._btn_prev = QToolButton()
        self._btn_prev.setText("◀")
        self._btn_prev.setToolTip("Trang trước")
        self._btn_prev.clicked.connect(self._prev_page)

        self._spin_page = QSpinBox()
        self._spin_page.setMinimum(1)
        self._spin_page.setMaximum(9999)
        self._spin_page.setFixedWidth(60)
        self._spin_page.setToolTip("Số trang hiện tại")
        self._spin_page.valueChanged.connect(self._on_spin_changed)

        self._lbl_total = QLabel("/ 0")
        self._lbl_total.setFixedWidth(48)

        self._btn_next = QToolButton()
        self._btn_next.setText("▶")
        self._btn_next.setToolTip("Trang kế")
        self._btn_next.clicked.connect(self._next_page)

        lay.addWidget(self._btn_prev)
        lay.addWidget(self._spin_page)
        lay.addWidget(self._lbl_total)
        lay.addWidget(self._btn_next)
        lay.addSpacing(12)

        self._btn_zoom_out = QToolButton()
        self._btn_zoom_out.setText("−")
        self._btn_zoom_out.setToolTip("Thu nhỏ")
        self._btn_zoom_out.clicked.connect(self._zoom_out)

        self._lbl_zoom = QLabel("150%")
        self._lbl_zoom.setFixedWidth(44)
        self._lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_zoom_in = QToolButton()
        self._btn_zoom_in.setText("+")
        self._btn_zoom_in.setToolTip("Phóng to")
        self._btn_zoom_in.clicked.connect(self._zoom_in)

        lay.addWidget(self._btn_zoom_out)
        lay.addWidget(self._lbl_zoom)
        lay.addWidget(self._btn_zoom_in)
        lay.addStretch()

        return bar

    def _setup_shortcuts(self) -> None:
        """Thiết lập điều hướng trang bằng phím mũi tên trái/phải."""
        self._shortcut_prev = QShortcut(QKeySequence("Left"), self)
        self._shortcut_prev.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._shortcut_prev.activated.connect(self._prev_page)

        self._shortcut_next = QShortcut(QKeySequence("Right"), self)
        self._shortcut_next.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._shortcut_next.activated.connect(self._next_page)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_document(self, file_path: Path, start_page: int = 1) -> None:
        """Mở file PDF và render trang đầu tiên."""
        from core.extraction.pdf_text import open_document, page_count
        self._close_current()
        self._file_path = Path(file_path)
        try:
            self._doc = open_document(self._file_path)
            self._total_pages = page_count(self._doc)
        except Exception as exc:  # noqa: BLE001
            self._empty_label.setText(f"Không thể mở PDF:\n{exc}")
            self._set_document_loaded(False)
            return
        self._total_pages = max(self._total_pages, 1)
        self._spin_page.setMaximum(self._total_pages)
        self._lbl_total.setText(f"/ {self._total_pages}")
        self._set_document_loaded(True)
        self.go_to_page(max(1, min(start_page, self._total_pages)))
        self.document_loaded.emit(self._total_pages)

    def close_document(self) -> None:
        """Đóng tài liệu hiện tại."""
        self._close_current()
        self._set_document_loaded(False)

    def go_to_page(self, page_no: int) -> None:
        """Chuyển tới trang (1-based)."""
        if not self._doc:
            return
        page_no = max(1, min(page_no, self._total_pages))
        self._current_page = page_no
        # block spin signal để tránh vòng lặp
        self._spin_page.blockSignals(True)
        self._spin_page.setValue(page_no)
        self._spin_page.blockSignals(False)
        self._render()
        self.page_changed.emit(page_no)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def file_path(self) -> Path | None:
        return self._file_path

    def set_selection_mode(self, mode: int) -> None:
        """Đặt chế độ chọn vùng: SELECTION_NONE / TEXT / TABLE / IMAGE."""
        self._selection_mode = mode
        self._page_label.set_selection_active(mode != SELECTION_NONE)

    def set_navigation_visible(self, visible: bool) -> None:
        """Hiện/ẩn thanh điều hướng PDF để tối ưu không gian đọc."""
        self._nav_bar.setVisible(visible)

    def set_compact_navigation(self, enabled: bool) -> None:
        """Giảm chiều cao và khoảng đệm của toolbar điều hướng PDF."""
        if enabled:
            self._nav_bar.setMinimumHeight(34)
            self._nav_bar.setMaximumHeight(34)
            self._btn_prev.setFixedSize(30, 24)
            self._btn_next.setFixedSize(30, 24)
            self._btn_zoom_out.setFixedSize(30, 24)
            self._btn_zoom_in.setFixedSize(30, 24)
            self._spin_page.setFixedWidth(52)
            self._lbl_total.setFixedWidth(40)
            self._lbl_zoom.setFixedWidth(42)
        else:
            self._nav_bar.setMinimumHeight(0)
            self._nav_bar.setMaximumHeight(16777215)
            self._btn_prev.setMinimumSize(0, 0)
            self._btn_prev.setMaximumSize(16777215, 16777215)
            self._btn_next.setMinimumSize(0, 0)
            self._btn_next.setMaximumSize(16777215, 16777215)
            self._btn_zoom_out.setMinimumSize(0, 0)
            self._btn_zoom_out.setMaximumSize(16777215, 16777215)
            self._btn_zoom_in.setMinimumSize(0, 0)
            self._btn_zoom_in.setMaximumSize(16777215, 16777215)
            self._spin_page.setFixedWidth(60)
            self._lbl_total.setFixedWidth(48)
            self._lbl_zoom.setFixedWidth(44)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_page(self) -> None:
        self.go_to_page(self._current_page - 1)

    def _next_page(self) -> None:
        self.go_to_page(self._current_page + 1)

    def _on_spin_changed(self, value: int) -> None:
        if value != self._current_page:
            self.go_to_page(value)

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def _zoom_in(self) -> None:
        if self._zoom_index < len(_ZOOM_STEPS) - 1:
            self._zoom_index += 1
            self._update_zoom_label()
            self._render()

    def _zoom_out(self) -> None:
        if self._zoom_index > 0:
            self._zoom_index -= 1
            self._update_zoom_label()
            self._render()

    def _update_zoom_label(self) -> None:
        pct = int(_ZOOM_STEPS[self._zoom_index] * 100)
        self._lbl_zoom.setText(f"{pct}%")

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _render(self) -> None:
        if not self._doc:
            return
        from core.extraction.pdf_text import render_page_to_bytes
        zoom = _ZOOM_STEPS[self._zoom_index]
        try:
            png_bytes = render_page_to_bytes(self._doc, self._current_page, zoom)
        except Exception:  # noqa: BLE001
            return
        pixmap = QPixmap()
        pixmap.loadFromData(png_bytes, "PNG")
        self._page_label.setPixmap(pixmap)
        self._page_label.resize(pixmap.size())

    # ------------------------------------------------------------------
    # Rubber-band callback
    # ------------------------------------------------------------------

    def _on_rubber_band_selection(self, pixel_rect: QRect) -> None:
        """Chuyển đổi tọa độ pixel → PDF và phát signal đúng loại."""
        if not self._doc or self._selection_mode == SELECTION_NONE:
            return
        zoom = _ZOOM_STEPS[self._zoom_index]
        x0 = pixel_rect.x() / zoom
        y0 = pixel_rect.y() / zoom
        x1 = (pixel_rect.x() + pixel_rect.width()) / zoom
        y1 = (pixel_rect.y() + pixel_rect.height()) / zoom
        pdf_rect = (x0, y0, x1, y1)
        if self._selection_mode == SELECTION_TEXT:
            self.text_region_selected.emit(self._current_page, pdf_rect)
        elif self._selection_mode == SELECTION_TABLE:
            self.table_region_selected.emit(self._current_page, pdf_rect)
        elif self._selection_mode == SELECTION_IMAGE:
            self.image_region_selected.emit(self._current_page, pdf_rect)
        # Reset về chế độ bình thường sau mỗi selection
        self.set_selection_mode(SELECTION_NONE)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _close_current(self) -> None:
        if self._doc is not None:
            try:
                self._doc.close()
            except Exception:  # noqa: BLE001
                pass
            self._doc = None
        self._file_path = None
        self._current_page = 1
        self._total_pages = 0

    def _set_document_loaded(self, loaded: bool) -> None:
        self._scroll.setVisible(loaded)
        self._empty_label.setVisible(not loaded)
        for w in [self._btn_prev, self._btn_next, self._spin_page,
                  self._btn_zoom_in, self._btn_zoom_out]:
            w.setEnabled(loaded)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._close_current()
        super().closeEvent(event)
