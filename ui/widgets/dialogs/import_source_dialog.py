"""Dialog nhập tài liệu PDF vào thư viện nguồn."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.source_service import SourceService
from core.utils.logger import get_logger

logger = get_logger()


class ImportSourceDialog(QDialog):
    """Dialog nhập PDF vào thư viện (chỉ lưu source thô)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nhập tài liệu PDF")
        self.setMinimumWidth(560)
        self._imported_source_id: int | None = None
        self._build_ui()

    @property
    def imported_source_id(self) -> int | None:
        """ID source đã import thành công."""
        return self._imported_source_id

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        file_row = QWidget()
        file_lay = QHBoxLayout(file_row)
        file_lay.setContentsMargins(0, 0, 0, 0)
        file_lay.setSpacing(4)

        self._edit_path = QLineEdit()
        self._edit_path.setPlaceholderText("Đường dẫn file PDF...")
        self._edit_path.setReadOnly(True)

        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(32)
        btn_browse.setToolTip("Chọn file PDF")
        btn_browse.clicked.connect(self._browse_file)

        file_lay.addWidget(self._edit_path)
        file_lay.addWidget(btn_browse)
        form.addRow("File PDF:", file_row)

        self._edit_title = QLineEdit()
        self._edit_title.setPlaceholderText("Tiêu đề tài liệu")
        form.addRow("Tiêu đề source:", self._edit_title)

        self._edit_authors = QLineEdit()
        self._edit_authors.setPlaceholderText("Tác giả (tự động điền từ PDF nếu có)")
        form.addRow("Tác giả:", self._edit_authors)

        row_year = QWidget()
        row_year_lay = QHBoxLayout(row_year)
        row_year_lay.setContentsMargins(0, 0, 0, 0)
        row_year_lay.setSpacing(4)
        self._edit_year = QLineEdit()
        self._edit_year.setPlaceholderText("Năm")
        self._edit_year.setMaximumWidth(90)
        row_year_lay.addWidget(self._edit_year)
        row_year_lay.addWidget(QLabel("Ngôn ngữ:"))
        self._edit_language = QLineEdit()
        self._edit_language.setPlaceholderText("vi / en")
        self._edit_language.setMaximumWidth(80)
        row_year_lay.addWidget(self._edit_language)
        row_year_lay.addStretch()
        form.addRow("Năm:", row_year)

        self._edit_doi = QLineEdit()
        self._edit_doi.setPlaceholderText("DOI (tùy chọn)")
        form.addRow("DOI:", self._edit_doi)

        self._lbl_hint = QLabel(
            "Import chỉ thêm tài liệu vào Thư viện nguồn. source note sẽ được tạo ở thẻ source note."
        )
        self._lbl_hint.setWordWrap(True)
        self._lbl_hint.setObjectName("import_hint_label")
        form.addRow("", self._lbl_hint)

        layout.addLayout(form)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Nhập vào thư viện")
        self._button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        self._button_box.accepted.connect(self._do_import)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file PDF",
            "",
            "PDF files (*.pdf);;Tất cả (*)",
        )
        if not path:
            return

        pdf_path = Path(path)
        self._edit_path.setText(path)
        try:
            meta = SourceService.extract_pdf_metadata(pdf_path)
        except Exception:
            meta = {}

        if not self._edit_title.text().strip():
            self._edit_title.setText(meta.get("title") or pdf_path.stem)
        if not self._edit_authors.text().strip() and meta.get("authors"):
            self._edit_authors.setText(meta["authors"])
        if not self._edit_year.text().strip() and meta.get("year"):
            self._edit_year.setText(meta["year"])

    def _do_import(self) -> None:
        path_str = self._edit_path.text().strip()
        if not path_str:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn file PDF.")
            return

        pdf_path = Path(path_str)
        svc = SourceService()
        try:
            source = svc.import_source(
                file_path=pdf_path,
                title=self._edit_title.text().strip() or None,
                authors=self._edit_authors.text().strip() or None,
                year=self._edit_year.text().strip() or None,
                doi=self._edit_doi.text().strip() or None,
            )

            lang = self._edit_language.text().strip()
            if lang:
                svc.update_metadata(source.id, language=lang)

            self._imported_source_id = source.id
            logger.info(
                "Nhập source thành công (không tạo source_note): id=%s, source_title=%r",
                source.id,
                source.title,
            )
            self.accept()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể nhập tài liệu:\n{exc}")
