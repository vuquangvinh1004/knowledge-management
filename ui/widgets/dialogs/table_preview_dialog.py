"""Dialog xem trước bảng Markdown trước khi commit vào ghi chú.

Business rule: bảng trích xuất từ PDF bắt buộc phải qua bước preview/confirm.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)


class TablePreviewDialog(QDialog):
    """
    Hiển thị bảng Markdown được trích xuất để người dùng xem lại và chỉnh sửa
    trước khi chèn vào ghi chú.
    """

    def __init__(self, table_md: str, anchor: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Xem trước bảng trích xuất")
        self.setMinimumSize(560, 400)
        self._build_ui(table_md, anchor)

    def _build_ui(self, table_md: str, anchor: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(
            QLabel(
                "Kiểm tra bảng dưới đây trước khi chèn vào ghi chú."
                " Bạn có thể chỉnh sửa trực tiếp."
            )
        )

        self._editor = QPlainTextEdit()
        self._editor.setPlainText(table_md)
        self._editor.setMinimumHeight(200)
        layout.addWidget(self._editor)

        layout.addWidget(QLabel(f"Nguồn: {anchor}"))

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("Chèn vào ghi chú")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    @property
    def table_markdown(self) -> str:
        """Nội dung Markdown có thể đã được chỉnh sửa."""
        return self._editor.toPlainText()
