"""Banner cảnh báo hiển thị khi có vấn đề khởi động hoặc tính năng không khả dụng.

Luôn hiển thị phía trên màn hình, người dùng có thể đóng.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class WarningBanner(QWidget):
    """
    Banner cảnh báo nằm trên cùng của main window.

    Hiển thị danh sách các soft dependency thiếu
    (ví dụ: PyMuPDF, pdfplumber) hoặc bất kỳ cảnh báo rờng.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("warning_banner")
        self._build_ui()
        self.hide()  # Ẩn mặc định

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setObjectName("warning_banner_label")
        layout.addWidget(self._lbl)

        layout.addStretch()

        self._btn_close = QPushButton("×")
        self._btn_close.setFixedSize(22, 22)
        self._btn_close.setToolTip("Đóng cảnh báo")
        self._btn_close.clicked.connect(self.hide)
        layout.addWidget(self._btn_close)

    def show_warnings(self, warnings: list[str]) -> None:
        """
        Hiển thị danh sách cảnh báo.

        Args:
            warnings: Danh sách chuỗi cảnh báo cần hiển thị.
        """
        if not warnings:
            self.hide()
            return
        text = " \u2022 ".join(warnings)
        self._lbl.setText(f"⚠️ {text}")
        self.show()

    def show_message(self, message: str) -> None:
        """Hiển thị một thông báo cảnh báo dưới dạng chuỗi đơn."""
        self._lbl.setText(f"⚠️ {message}")
        self.show()
