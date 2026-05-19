"""Dialog quản lý tiêu chí bảng tổng hợp (thêm, xóa, sửa, sắp xếp).

Features:
- Danh sách tiêu chí hiện tại
- Nút: Thêm, Sửa, Xóa, Lên, Xuống
- Kéo thả sắp xếp (hoặc dùng nút Lên/Xuống)
- Xác nhận: Lưu, Hủy
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.utils.logger import get_logger

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

logger = get_logger()


class BoardCriteriaManagerDialog(QDialog):
    """Dialog quản lý tiêu chí (column) của bảng tổng hợp."""

    def __init__(self, criteria: list[str], parent: QWidget | None = None) -> None:
        """Khởi tạo dialog.

        Args:
            criteria: Danh sách tiêu chí hiện tại
            parent: Widget cha
        """
        super().__init__(parent)
        self.setWindowTitle("Tùy chỉnh tiêu chí bảng tổng hợp")
        self.setGeometry(100, 100, 500, 400)

        self._original_criteria = criteria
        self._criteria = list(criteria)

        self._init_ui()

    def _init_ui(self) -> None:
        """Khởi tạo giao diện."""
        layout = QVBoxLayout(self)

        # Danh sách tiêu chí
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._refresh_list()

        layout.addWidget(self._list_widget)

        # Nút điều khiển
        button_layout = QHBoxLayout()

        btn_add = QPushButton("Thêm")
        btn_add.clicked.connect(self._on_add)

        btn_edit = QPushButton("Sửa")
        btn_edit.clicked.connect(self._on_edit)

        btn_delete = QPushButton("Xóa")
        btn_delete.clicked.connect(self._on_delete)

        btn_up = QPushButton("↑ Lên")
        btn_up.clicked.connect(self._on_move_up)

        btn_down = QPushButton("↓ Xuống")
        btn_down.clicked.connect(self._on_move_down)

        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_up)
        button_layout.addWidget(btn_down)

        layout.addLayout(button_layout)

        # Nút Lưu/Hủy
        bottom_layout = QHBoxLayout()

        btn_save = QPushButton("Lưu")
        btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)

        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)
        bottom_layout.addWidget(btn_cancel)

        layout.addLayout(bottom_layout)

    def _refresh_list(self) -> None:
        """Làm mới danh sách tiêu chí."""
        self._list_widget.clear()
        for criterion in self._criteria:
            item = QListWidgetItem(criterion)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self._list_widget.addItem(item)

    def _on_add(self) -> None:
        """Thêm tiêu chí mới."""
        text, ok = QInputDialog.getText(
            self,
            "Thêm tiêu chí",
            "Nhập tên tiêu chí:",
        )

        if ok and text:
            text = text.strip()
            if text in self._criteria:
                QMessageBox.warning(self, "Lỗi", "Tiêu chí này đã tồn tại!")
                return
            self._criteria.append(text)
            self._refresh_list()

    def _on_edit(self) -> None:
        """Sửa tiêu chí được chọn."""
        row = self._list_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn tiêu chí để sửa!")
            return

        old_text = self._criteria[row]
        text, ok = QInputDialog.getText(
            self,
            "Sửa tiêu chí",
            "Nhập tên tiêu chí mới:",
            text=old_text,
        )

        if ok and text:
            text = text.strip()
            if text != old_text and text in self._criteria:
                QMessageBox.warning(self, "Lỗi", "Tiêu chí này đã tồn tại!")
                return
            self._criteria[row] = text
            self._refresh_list()

    def _on_delete(self) -> None:
        """Xóa tiêu chí được chọn."""
        row = self._list_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn tiêu chí để xóa!")
            return

        ret = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Xóa tiêu chí '{self._criteria[row]}'?\nCác ô dữ liệu của tiêu chí này sẽ bị xóa.",
        )

        if ret == QMessageBox.StandardButton.Yes:
            del self._criteria[row]
            self._refresh_list()

    def _on_move_up(self) -> None:
        """Di chuyển tiêu chí lên."""
        row = self._list_widget.currentRow()
        if row <= 0:
            QMessageBox.warning(self, "Lỗi", "Không thể di chuyển lên!")
            return

        self._criteria[row], self._criteria[row - 1] = self._criteria[row - 1], self._criteria[row]
        self._refresh_list()
        self._list_widget.setCurrentRow(row - 1)

    def _on_move_down(self) -> None:
        """Di chuyển tiêu chí xuống."""
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._criteria) - 1:
            QMessageBox.warning(self, "Lỗi", "Không thể di chuyển xuống!")
            return

        self._criteria[row], self._criteria[row + 1] = self._criteria[row + 1], self._criteria[row]
        self._refresh_list()
        self._list_widget.setCurrentRow(row + 1)

    def get_criteria(self) -> list[str]:
        """Trả về danh sách tiêu chí được chỉnh sửa."""
        return self._criteria
