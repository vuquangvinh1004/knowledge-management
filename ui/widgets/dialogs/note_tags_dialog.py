"""Dialog quản lý tags của một note.

Người dùng có thể thêm và xóa tags. Thay đổi áp dụng ngay khi bấm OK.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.tag_service import TagService
from core.utils.logger import get_logger

logger = get_logger()


class NoteTagsDialog(QDialog):
    """Dialog quản lý tags của một note."""

    def __init__(self, note_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._note_id = note_id
        self._tag_service = TagService()
        self.setWindowTitle("Quản lý nhãn (Tags)")
        self.setMinimumWidth(360)
        self._build_ui()
        self._load_tags()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Nhãn hiện tại:"))

        self._tag_list = QListWidget()
        self._tag_list.setMaximumHeight(160)
        layout.addWidget(self._tag_list)

        # Thêm tag mới
        add_row = QHBoxLayout()
        self._input_tag = QLineEdit()
        self._input_tag.setPlaceholderText("Tên nhãn mới...")
        self._input_tag.returnPressed.connect(self._add_tag)
        add_row.addWidget(self._input_tag)

        btn_add = QPushButton("Thêm")
        btn_add.clicked.connect(self._add_tag)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        # Xóa tag
        btn_remove = QPushButton("Xóa nhãn đã chọn")
        btn_remove.clicked.connect(self._remove_selected_tag)
        layout.addWidget(btn_remove)

        # Buttons OK
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _load_tags(self) -> None:
        """Tải danh sách tags hiện tại của note."""
        self._tag_list.clear()
        try:
            tags = self._tag_service.get_tags_for_note(self._note_id)
            for tag in tags:
                item = QListWidgetItem(tag.name)
                item.setData(Qt.ItemDataRole.UserRole, tag.name)
                self._tag_list.addItem(item)
        except Exception as exc:
            logger.warning(f"Lỗi load tags: {exc}")

    def _add_tag(self) -> None:
        """Thêm tag mới từ input."""
        name = self._input_tag.text().strip().lower()
        if not name:
            return
        try:
            self._tag_service.add_tag_to_note(self._note_id, name)
            self._input_tag.clear()
            self._load_tags()
        except Exception as exc:
            logger.warning(f"Lỗi thêm tag: {exc}")

    def _remove_selected_tag(self) -> None:
        """Xóa tag đang được chọn."""
        item = self._tag_list.currentItem()
        if item is None:
            return
        tag_name = item.data(Qt.ItemDataRole.UserRole)
        if tag_name:
            try:
                self._tag_service.remove_tag_from_note(self._note_id, tag_name)
                self._load_tags()
            except Exception as exc:
                logger.warning(f"Lỗi xóa tag: {exc}")
