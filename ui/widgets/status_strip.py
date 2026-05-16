"""Thanh trạng thái dưới cùng của cửa sổ chính."""
from __future__ import annotations

from PySide6.QtWidgets import QStatusBar, QLabel


class StatusStrip(QStatusBar):
    """Thanh trạng thái hiển thị thông báo và thông tin ngữ cảnh."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("main_status_bar")
        self._permanent_label = QLabel("Sẵn sàng")
        self._permanent_label.setObjectName("status_permanent_label")
        self.addPermanentWidget(self._permanent_label)
        self.showMessage("Chào mừng đến với Quản lý Kiến thức Nghiên cứu")

    def set_status(self, message: str, timeout_ms: int = 0) -> None:
        """Hiển thị thông báo tạm thời."""
        self.showMessage(message, timeout_ms)

    def set_permanent_info(self, text: str) -> None:
        """Cập nhật thông tin cố định bên phải."""
        self._permanent_label.setText(text)
