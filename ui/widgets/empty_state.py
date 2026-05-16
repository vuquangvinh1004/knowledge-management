"""Widget hiển thị trạng thái rỗng (empty state) khi chưa có dữ liệu.

Mọi view KHÔNG được để màn hình trắng — phải dùng widget này.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class EmptyStateWidget(QWidget):
    """Hiển thị thông báo và nút gợi ý hành động khi view không có dữ liệu."""

    def __init__(
        self,
        message: str,
        action_label: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._action_btn: QPushButton | None = None
        self._build_ui(message, action_label)

    def _build_ui(self, message: str, action_label: str | None) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setObjectName("empty_state_message")
        layout.addWidget(msg_label)

        if action_label:
            self._action_btn = QPushButton(action_label)
            self._action_btn.setObjectName("empty_state_action")
            self._action_btn.setFixedWidth(200)
            layout.addWidget(self._action_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    @property
    def action_button(self) -> QPushButton | None:
        """Trả về nút hành động nếu có."""
        return self._action_btn
