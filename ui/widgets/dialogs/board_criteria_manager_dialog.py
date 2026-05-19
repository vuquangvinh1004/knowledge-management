"""Dialog quản lý tiêu chí bảng tổng hợp.

Quy ước:
- Checkbox được dùng để bật/tắt hiển thị tiêu chí trên bảng tổng hợp.
- Cột hệ thống meta-analysis không cho xóa cứng (chỉ cho phép bỏ chọn để ẩn).
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

    def __init__(
        self,
        criteria: list[dict[str, object]],
        parent: QWidget | None = None,
    ) -> None:
        """Khởi tạo dialog.

        Args:
            criteria: Danh sách cấu hình tiêu chí hiện tại.
            parent: Widget cha
        """
        super().__init__(parent)
        self.setWindowTitle("Tùy chỉnh tiêu chí bảng tổng hợp")
        self.setGeometry(100, 100, 500, 400)

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
            label = str(criterion.get("label", ""))
            visible = bool(criterion.get("visible", True))
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, criterion)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(
                Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
            )
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
            labels = {
                self._list_widget.item(i).text().strip().lower()
                for i in range(self._list_widget.count())
            }
            if text.lower() in labels:
                QMessageBox.warning(self, "Lỗi", "Tiêu chí này đã tồn tại!")
                return
            item = QListWidgetItem(text)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "id": None,
                    "label": text,
                    "visible": True,
                    "locked": False,
                },
            )
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(Qt.CheckState.Checked)
            self._list_widget.addItem(item)
            self._list_widget.setCurrentItem(item)

    def _on_edit(self) -> None:
        """Sửa tiêu chí được chọn."""
        row = self._list_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn tiêu chí để sửa!")
            return

        item = self._list_widget.item(row)
        old_text = item.text().strip()
        text, ok = QInputDialog.getText(
            self,
            "Sửa tiêu chí",
            "Nhập tên tiêu chí mới:",
            text=old_text,
        )

        if ok and text:
            text = text.strip()
            labels = {
                self._list_widget.item(i).text().strip().lower()
                for i in range(self._list_widget.count())
                if i != row
            }
            if text.lower() in labels:
                QMessageBox.warning(self, "Lỗi", "Tiêu chí này đã tồn tại!")
                return
            item.setText(text)

    def _on_delete(self) -> None:
        """Xóa tiêu chí được chọn."""
        row = self._list_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Chọn tiêu chí để xóa!")
            return

        item = self._list_widget.item(row)
        data = item.data(Qt.ItemDataRole.UserRole) or {}
        locked = bool(data.get("locked", False)) if isinstance(data, dict) else False
        if locked:
            QMessageBox.information(
                self,
                "Tiêu chí hệ thống",
                "Tiêu chí hệ thống không thể xóa.\n"
                "Hãy bỏ chọn checkbox nếu bạn muốn ẩn khỏi bảng tổng hợp.",
            )
            return

        ret = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Xóa tiêu chí '{item.text().strip()}'?\n"
            "Các ô dữ liệu của tiêu chí này sẽ bị xóa.",
        )

        if ret == QMessageBox.StandardButton.Yes:
            self._list_widget.takeItem(row)

    def _on_move_up(self) -> None:
        """Di chuyển tiêu chí lên."""
        row = self._list_widget.currentRow()
        if row <= 0:
            QMessageBox.warning(self, "Lỗi", "Không thể di chuyển lên!")
            return

        item = self._list_widget.takeItem(row)
        self._list_widget.insertItem(row - 1, item)
        self._list_widget.setCurrentRow(row - 1)

    def _on_move_down(self) -> None:
        """Di chuyển tiêu chí xuống."""
        row = self._list_widget.currentRow()
        if row < 0 or row >= self._list_widget.count() - 1:
            QMessageBox.warning(self, "Lỗi", "Không thể di chuyển xuống!")
            return

        item = self._list_widget.takeItem(row)
        self._list_widget.insertItem(row + 1, item)
        self._list_widget.setCurrentRow(row + 1)

    def get_configurations(self) -> list[dict[str, object]]:
        """Trả về cấu hình tiêu chí theo thứ tự hiện tại của UI."""
        configurations: list[dict[str, object]] = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            configurations.append(
                {
                    "id": data.get("id") if isinstance(data, dict) else None,
                    "label": item.text().strip(),
                    "visible": item.checkState() == Qt.CheckState.Checked,
                    "locked": bool(data.get("locked", False)) if isinstance(data, dict) else False,
                }
            )
        return configurations
