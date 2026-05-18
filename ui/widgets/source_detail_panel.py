"""Panel hiển thị chi tiết metadata tài liệu nguồn trong Library view.

Hiển thị khi người dùng chọn một source trong danh sách.
Cho phép xem đầy đủ thông tin kiểu Zotero và chỉnh sửa.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.utils.logger import get_logger

logger = get_logger()

# Loại tài liệu
ITEM_TYPES = [
    ("", "(Chọn loại)"),
    ("journal_article", "Bài báo khoa học"),
    ("book", "Sách"),
    ("book_chapter", "Chương sách"),
    ("conference_paper", "Báo cáo hội thảo"),
    ("thesis", "Luận văn / Luận án"),
    ("report", "Báo cáo kỹ thuật"),
    ("other", "Khác"),
]

ITEM_TYPE_LABELS = {v: k for k, v in ITEM_TYPES}
ITEM_TYPE_DISPLAY = dict(ITEM_TYPES)


# ---------------------------------------------------------------------------
# Dialog chỉnh sửa metadata đầy đủ
# ---------------------------------------------------------------------------

class _SourceEditDialog(QDialog):
    """Dialog chỉnh sửa metadata tài liệu đầy đủ."""

    def __init__(self, source, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chỉnh sửa thông tin tài liệu")
        self.setMinimumWidth(540)
        self.setMinimumHeight(600)
        self._source = source
        self._build_ui()
        self._populate(source)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(12)

        def _field(placeholder):
            w = QLineEdit()
            w.setPlaceholderText(placeholder)
            return w

        # --- Nhóm: Cơ bản ---
        grp_basic = QGroupBox("Thông tin cơ bản")
        form_basic = QFormLayout(grp_basic)
        form_basic.setSpacing(8)

        self._combo_type = QComboBox()
        for _, label in ITEM_TYPES:
            self._combo_type.addItem(label)
        form_basic.addRow("Loại tài liệu:", self._combo_type)

        self._edit_title = _field("Tiêu đề tài liệu")
        form_basic.addRow("Tiêu đề:", self._edit_title)

        self._edit_authors = _field("VD: Nguyễn Văn A; Trần Thị B")
        form_basic.addRow("Tác giả:", self._edit_authors)

        self._edit_year = _field("VD: 2023")
        self._edit_year.setMaximumWidth(100)
        form_basic.addRow("Năm:", self._edit_year)
        layout.addWidget(grp_basic)

        # --- Nhóm: Xuất bản ---
        grp_pub = QGroupBox("Xuất bản")
        form_pub = QFormLayout(grp_pub)
        form_pub.setSpacing(8)

        self._edit_journal = _field("Tên tạp chí / nhà xuất bản")
        form_pub.addRow("Tạp chí:", self._edit_journal)

        self._edit_publisher = _field("Nhà xuất bản")
        form_pub.addRow("Nhà XB:", self._edit_publisher)

        row_vol = QWidget()
        row_vol_lay = QHBoxLayout(row_vol)
        row_vol_lay.setContentsMargins(0, 0, 0, 0)
        row_vol_lay.setSpacing(6)
        self._edit_volume = _field("Tập")
        self._edit_volume.setMaximumWidth(80)
        self._edit_issue = _field("Số")
        self._edit_issue.setMaximumWidth(80)
        self._edit_pages = _field("VD: 163-180")
        self._edit_pages.setMaximumWidth(120)
        row_vol_lay.addWidget(QLabel("Tập:"))
        row_vol_lay.addWidget(self._edit_volume)
        row_vol_lay.addWidget(QLabel("Số:"))
        row_vol_lay.addWidget(self._edit_issue)
        row_vol_lay.addWidget(QLabel("Trang:"))
        row_vol_lay.addWidget(self._edit_pages)
        row_vol_lay.addStretch()
        form_pub.addRow("", row_vol)
        layout.addWidget(grp_pub)

        # --- Nhóm: Định danh ---
        grp_id = QGroupBox("Định danh")
        form_id = QFormLayout(grp_id)
        form_id.setSpacing(8)

        self._edit_doi = _field("VD: 10.1016/j.jom.2020.01.001")
        form_id.addRow("DOI:", self._edit_doi)

        self._edit_url = _field("https://...")
        form_id.addRow("URL:", self._edit_url)

        self._edit_issn = _field("VD: 0272-6963")
        form_id.addRow("ISSN:", self._edit_issn)

        self._edit_language = _field("VD: vi, en")
        self._edit_language.setMaximumWidth(120)
        form_id.addRow("Ngôn ngữ:", self._edit_language)
        layout.addWidget(grp_id)

        # --- Nhóm: Nội dung ---
        grp_content = QGroupBox("Nội dung")
        form_content = QFormLayout(grp_content)
        form_content.setSpacing(8)

        self._edit_keywords = _field("Từ khóa, phân cách bằng dấu phẩy")
        form_content.addRow("Từ khóa:", self._edit_keywords)

        self._edit_abstract = QTextEdit()
        self._edit_abstract.setPlaceholderText("Tóm tắt nội dung tài liệu...")
        self._edit_abstract.setMinimumHeight(100)
        self._edit_abstract.setMaximumHeight(160)
        form_content.addRow("Tóm tắt:", self._edit_abstract)
        layout.addWidget(grp_content)

        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

        # Buttons — ngoài scroll
        btn_container = QWidget()
        btn_lay = QHBoxLayout(btn_container)
        btn_lay.setContentsMargins(16, 8, 16, 12)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Lưu")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        btn_lay.addWidget(btns)
        outer.addWidget(btn_container)

    def _populate(self, source) -> None:
        self._edit_title.setText(source.title or "")
        self._edit_authors.setText(source.authors or "")
        self._edit_year.setText(source.year or "")
        self._edit_doi.setText(source.doi or "")
        try:
            extra = json.loads(source.metadata_json or "{}")
        except Exception:
            extra = {}
        # item_type combo
        type_val = extra.get("item_type", "")
        for i, (val, _) in enumerate(ITEM_TYPES):
            if val == type_val:
                self._combo_type.setCurrentIndex(i)
                break
        self._edit_journal.setText(extra.get("journal", ""))
        self._edit_publisher.setText(extra.get("publisher", ""))
        self._edit_volume.setText(extra.get("volume", ""))
        self._edit_issue.setText(extra.get("issue", ""))
        self._edit_pages.setText(extra.get("pages", ""))
        self._edit_url.setText(extra.get("url", ""))
        self._edit_issn.setText(extra.get("issn", ""))
        self._edit_language.setText(extra.get("language", ""))
        self._edit_keywords.setText(extra.get("keywords", ""))
        self._edit_abstract.setPlainText(extra.get("abstract", ""))

    def _save(self) -> None:
        from core.services.source_service import SourceService
        type_idx = self._combo_type.currentIndex()
        type_val = ITEM_TYPES[type_idx][0] if type_idx >= 0 else ""
        try:
            SourceService().update_metadata(
                self._source.id,
                title=self._edit_title.text().strip() or None,
                authors=self._edit_authors.text().strip() or None,
                year=self._edit_year.text().strip() or None,
                doi=self._edit_doi.text().strip() or None,
                item_type=type_val or None,
                journal=self._edit_journal.text().strip() or None,
                publisher=self._edit_publisher.text().strip() or None,
                volume=self._edit_volume.text().strip() or None,
                issue=self._edit_issue.text().strip() or None,
                pages=self._edit_pages.text().strip() or None,
                url=self._edit_url.text().strip() or None,
                issn=self._edit_issn.text().strip() or None,
                language=self._edit_language.text().strip() or None,
                keywords=self._edit_keywords.text().strip() or None,
                abstract=self._edit_abstract.toPlainText().strip() or None,
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu:\n{exc}")


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

def _row_label(text: str) -> QLabel:
    """Label cho tên trường trong form chi tiết."""
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #5A6076; font-size: 11px; font-weight: 600;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
    return lbl


def _value_label(selectable: bool = True) -> QLabel:
    """Label cho giá trị trong form chi tiết."""
    lbl = QLabel("—")
    lbl.setWordWrap(True)
    lbl.setStyleSheet("color: #1A1A2E; font-size: 12px;")
    if selectable:
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl


class SourceDetailPanel(QWidget):
    """
    Panel hiển thị chi tiết metadata nguồn tài liệu — kiểu Zotero.

    Đặt ở phía phải của LibraryView qua QSplitter.

    Signals:
        open_requested(int): Khi nhấn 'Ghi chú nguồn'.
        open_reference_requested(int): Khi nhấn 'Mở tài liệu'.
        refresh_requested: Khi metadata đã được cập nhật.
    """

    open_requested = Signal(int)
    open_reference_requested = Signal(int)
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._source_id: int | None = None
        self.setObjectName("source_detail_panel")
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._apply_panel_style()
        self._build_ui()

    def _apply_panel_style(self) -> None:
        """Khóa style sáng cho panel để không bị ảnh hưởng bởi theme hệ điều hành."""
        self.setStyleSheet(
            "QWidget#source_detail_panel {"
            " background-color: #FBFCFF;"
            " border-left: 1px solid #D0D4E8;"
            "}"
            "QWidget#source_detail_panel QScrollArea,"
            "QWidget#source_detail_panel QStackedWidget,"
            "QWidget#source_detail_panel QScrollArea > QWidget > QWidget {"
            " background-color: #FBFCFF;"
            "}"
            "QWidget#source_detail_panel QLabel {"
            " color: #1A1A2E;"
            "}"
            "QWidget#source_detail_panel QPushButton {"
            " color: #1A1A2E;"
            " background-color: #FFFFFF;"
            " border: 1px solid #D0D4E8;"
            " border-radius: 4px;"
            " padding: 6px 10px;"
            "}"
            "QWidget#source_detail_panel QPushButton:hover {"
            " background-color: #EEF0F8;"
            " border-color: #3A5CE6;"
            "}"
            "QWidget#source_detail_panel QPushButton#primary_button {"
            " background-color: #3A5CE6;"
            " color: #FFFFFF;"
            " border-color: #3A5CE6;"
            " font-weight: 600;"
            "}"
            "QWidget#source_detail_panel QPushButton#primary_button:hover {"
            " background-color: #3A5CE6;"
            " border-color: #3A5CE6;"
            "}"
            "QWidget#source_detail_panel QPushButton#primary_button:disabled {"
            " background-color: #D7DEF8;"
            " color: #2E3A59;"
            " border-color: #C6D0F4;"
            "}"
            "QWidget#source_detail_panel QWidget#btn_container {"
            " background-color: #F7F9FD;"
            " border-top: 1px solid #D0D4E8;"
            "}"
        )

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setCurrentIndex(0)

        # --- Trang 0: Empty state ---
        empty_widget = QWidget()
        empty_lay = QVBoxLayout(empty_widget)
        empty_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty = QLabel("Chọn tài liệu để\nxem thông tin chi tiết.")
        lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty.setWordWrap(True)
        lbl_empty.setStyleSheet("color: #8A94A8; font-size: 13px;")
        empty_lay.addWidget(lbl_empty)
        self._stack.addWidget(empty_widget)

        # --- Trang 1: Detail view ---
        detail_widget = QWidget()
        detail_outer = QVBoxLayout(detail_widget)
        detail_outer.setContentsMargins(0, 0, 0, 0)
        detail_outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_container = QWidget()
        content_lay = QVBoxLayout(scroll_container)
        content_lay.setContentsMargins(12, 12, 12, 12)
        content_lay.setSpacing(8)

        # Thumbnail
        self._lbl_thumb = QLabel()
        self._lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_thumb.setMinimumHeight(140)
        self._lbl_thumb.setMaximumHeight(180)
        self._lbl_thumb.setStyleSheet(
            "background-color: #F7F9FD; border: 1px solid #D0D4E8; border-radius: 4px;"
        )
        content_lay.addWidget(self._lbl_thumb)

        # Item type badge
        self._lbl_item_type = QLabel()
        self._lbl_item_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_item_type.setStyleSheet(
            "color: #1E40AF; font-size: 11px; font-weight: 600;"
            " background: #E5EEFF; border-radius: 10px; padding: 2px 10px;"
        )
        content_lay.addWidget(self._lbl_item_type)

        # Title
        self._lbl_title = QLabel()
        self._lbl_title.setWordWrap(True)
        self._lbl_title.setStyleSheet(
            "color: #1A1A2E; font-size: 13px; font-weight: 700;"
        )
        self._lbl_title.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        content_lay.addWidget(self._lbl_title)

        # --- Info section ---
        info_section = QGroupBox("Thông tin")
        info_section.setStyleSheet(
            "QGroupBox { font-size: 11px; font-weight: 600; color: #5A6076;"
            " border: 1px solid #D0D4E8; border-radius: 6px;"
            " margin-top: 8px; padding-top: 12px; }"
            " QGroupBox::title { subcontrol-origin: margin; left: 8px;"
            " padding: 0 4px; color: #5A6076; background: #FBFCFF; }"
        )
        form = QFormLayout(info_section)
        form.setSpacing(6)
        form.setContentsMargins(10, 8, 10, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def _add_row(label_text):
            key_lbl = QLabel(label_text)
            key_lbl.setStyleSheet(
                "color: #5A6076; font-size: 11px; font-weight: 600;"
            )
            key_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            val_lbl = QLabel("—")
            val_lbl.setWordWrap(True)
            val_lbl.setStyleSheet("color: #1A1A2E; font-size: 12px;")
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(key_lbl, val_lbl)
            return val_lbl

        self._lbl_authors = _add_row("Tác giả")
        self._lbl_year = _add_row("Năm")
        self._lbl_source_code = _add_row("Source ID")
        self._lbl_journal = _add_row("Tạp chí")
        self._lbl_publisher = _add_row("Nhà XB")
        self._lbl_vol_issue = _add_row("Tập/Số")
        self._lbl_pages = _add_row("Trang")
        self._lbl_doi = _add_row("DOI")
        self._lbl_url = _add_row("URL")
        self._lbl_issn = _add_row("ISSN")
        self._lbl_language = _add_row("Ngôn ngữ")
        self._lbl_keywords = _add_row("Từ khóa")
        self._lbl_pages_count = _add_row("Số trang PDF")
        content_lay.addWidget(info_section)

        # --- Abstract section ---
        abstract_section = QGroupBox("Tóm tắt")
        abstract_section.setStyleSheet(
            "QGroupBox { font-size: 11px; font-weight: 600; color: #5A6076;"
            " border: 1px solid #D0D4E8; border-radius: 6px;"
            " margin-top: 8px; padding-top: 12px; }"
            " QGroupBox::title { subcontrol-origin: margin; left: 8px;"
            " padding: 0 4px; color: #5A6076; background: #FBFCFF; }"
        )
        abs_lay = QVBoxLayout(abstract_section)
        abs_lay.setContentsMargins(10, 8, 10, 8)
        self._lbl_abstract = QLabel("(Chưa có tóm tắt)")
        self._lbl_abstract.setWordWrap(True)
        self._lbl_abstract.setStyleSheet(
            "color: #333333; font-size: 12px; line-height: 1.5;"
        )
        self._lbl_abstract.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        abs_lay.addWidget(self._lbl_abstract)
        content_lay.addWidget(abstract_section)

        # File path
        self._lbl_path = QLabel()
        self._lbl_path.setWordWrap(True)
        self._lbl_path.setStyleSheet("color: #8A94A8; font-size: 11px;")
        self._lbl_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_lay.addWidget(self._lbl_path)

        content_lay.addStretch()
        scroll.setWidget(scroll_container)
        detail_outer.addWidget(scroll, stretch=1)

        # Action buttons
        btn_container = QWidget()
        btn_container.setObjectName("btn_container")
        btn_lay = QVBoxLayout(btn_container)
        btn_lay.setContentsMargins(10, 8, 10, 8)
        btn_lay.setSpacing(6)

        self._btn_open = QPushButton("Ghi chú nguồn")
        self._btn_open.setObjectName("primary_button")
        self._btn_open.setMinimumHeight(34)
        self._btn_open.setEnabled(False)
        self._btn_open.clicked.connect(self._on_open)
        btn_lay.addWidget(self._btn_open)

        self._btn_open_reference = QPushButton("Mở tài liệu")
        self._btn_open_reference.setMinimumHeight(34)
        self._btn_open_reference.setEnabled(False)
        self._btn_open_reference.clicked.connect(self._on_open_reference)
        btn_lay.addWidget(self._btn_open_reference)

        self._btn_edit = QPushButton("Chỉnh sửa thông tin")
        self._btn_edit.clicked.connect(self._on_edit)
        btn_lay.addWidget(self._btn_edit)

        detail_outer.addWidget(btn_container)

        self._stack.addWidget(detail_widget)
        layout.addWidget(self._stack)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_source(self, source_id: int) -> None:
        """Tải và hiển thị thông tin chi tiết của source."""
        try:
            from core.services.source_service import SourceService
            source = SourceService().get_by_id(source_id)
        except Exception as exc:
            logger.warning(f"SourceDetailPanel: không tải được source {source_id}: {exc}")
            self._stack.setCurrentIndex(0)
            return
        self._source_id = source_id
        self._btn_open.setEnabled(True)
        self._btn_open_reference.setEnabled(True)
        self._populate(source)
        self._stack.setCurrentIndex(1)
        self._load_thumbnail(source.file_path)

    def clear(self) -> None:
        """Xóa và hiển thị empty state."""
        self._source_id = None
        self._btn_open.setEnabled(False)
        self._btn_open_reference.setEnabled(False)
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _populate(self, source) -> None:
        """Điền dữ liệu metadata vào các label."""
        self._lbl_title.setText(source.title or "(Không có tiêu đề)")

        try:
            extra = json.loads(source.metadata_json or "{}")
        except Exception:
            extra = {}

        # Item type badge
        item_type_val = extra.get("item_type", "")
        item_type_display = ITEM_TYPE_DISPLAY.get(item_type_val, "")
        if item_type_display:
            self._lbl_item_type.setText(item_type_display)
            self._lbl_item_type.setVisible(True)
        else:
            self._lbl_item_type.setVisible(False)

        def _set(lbl, val):
            lbl.setText(val if val else "—")

        _set(self._lbl_authors, source.authors)
        _set(self._lbl_year, source.year)
        _set(self._lbl_source_code, source.source_code)
        _set(self._lbl_journal, extra.get("journal"))
        _set(self._lbl_publisher, extra.get("publisher"))

        # Vol/Issue
        vol = extra.get("volume", "")
        iss = extra.get("issue", "")
        if vol or iss:
            vi = []
            if vol:
                vi.append(f"Tập {vol}")
            if iss:
                vi.append(f"Số {iss}")
            self._lbl_vol_issue.setText(", ".join(vi))
        else:
            self._lbl_vol_issue.setText("—")

        _set(self._lbl_pages, extra.get("pages"))
        _set(self._lbl_doi, source.doi)
        _set(self._lbl_url, extra.get("url"))
        _set(self._lbl_issn, extra.get("issn"))
        _set(self._lbl_language, extra.get("language"))
        _set(self._lbl_keywords, extra.get("keywords"))

        pages_count = extra.get("pages_count")
        self._lbl_pages_count.setText(str(pages_count) if pages_count else "—")

        abstract = extra.get("abstract", "")
        self._lbl_abstract.setText(abstract if abstract else "(Chưa có tóm tắt)")

        p = Path(source.file_path)
        self._lbl_path.setText(f"📁 {p.name}")
        self._lbl_path.setToolTip(source.file_path)

    def _load_thumbnail(self, file_path: str) -> None:
        """Render trang đầu PDF thành thumbnail."""
        self._lbl_thumb.setText("⏳")
        try:
            import fitz  # noqa: PLC0415
            doc = fitz.open(file_path)
            if doc.page_count > 0:
                page = doc[0]
                mat = fitz.Matrix(0.35, 0.35)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                panel_w = max(self.width() - 28, 200)
                scaled = pixmap.scaled(
                    panel_w, 175,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._lbl_thumb.setPixmap(scaled)
                self._lbl_thumb.setText("")
            doc.close()
            return
        except Exception as exc:
            logger.debug(f"Không thể render thumbnail: {exc}")
        self._lbl_thumb.setText("📄")
        self._lbl_thumb.setStyleSheet(
            "font-size: 36px; color: #8A94A8;"
            " background-color: #F7F9FD; border: 1px solid #D0D4E8; border-radius: 4px;"
        )

    def _on_open(self) -> None:
        if self._source_id is not None:
            self.open_requested.emit(self._source_id)

    def _on_open_reference(self) -> None:
        if self._source_id is not None:
            self.open_reference_requested.emit(self._source_id)

    def _on_edit(self) -> None:
        if self._source_id is None:
            return
        try:
            from core.services.source_service import SourceService
            source = SourceService().get_by_id(self._source_id)
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
            return
        dlg = _SourceEditDialog(source, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_source(self._source_id)
            self.refresh_requested.emit()


