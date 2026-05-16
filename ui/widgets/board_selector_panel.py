"""Panel chọn board đang làm việc trong Research Board."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)


class BoardSelectorPanel(QWidget):
    """Panel hiển thị danh sách board và thao tác create/rename/delete/select."""

    board_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._boards: list = []
        self._active_board_id: int | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        row = QHBoxLayout()
        self._lbl_title = QLabel("Boards")
        self._btn_new = QPushButton("+ Board")
        self._btn_new.setToolTip("Tạo board mới")
        self._btn_new.clicked.connect(self._on_create_board)
        row.addWidget(self._lbl_title)
        row.addStretch()
        row.addWidget(self._btn_new)
        layout.addLayout(row)

        self._list = QListWidget()
        self._list.setObjectName("board_selector_list")
        self._list.currentItemChanged.connect(self._on_current_item_changed)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list)

    def refresh(self, boards: list, active_board_id: int | None = None) -> None:
        self._boards = boards
        if active_board_id is not None:
            self._active_board_id = active_board_id

        self._list.blockSignals(True)
        self._list.clear()
        selected_row = -1

        for idx, board in enumerate(boards):
            label = f"{board.title} ({board.board_type})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, board.id)
            self._list.addItem(item)
            if board.id == self._active_board_id:
                selected_row = idx

        if selected_row == -1 and self._list.count() > 0:
            selected_row = 0

        if selected_row >= 0:
            self._list.setCurrentRow(selected_row)
            item = self._list.item(selected_row)
            self._active_board_id = item.data(Qt.ItemDataRole.UserRole)

        self._list.blockSignals(False)

    def _get_service(self):
        from core.services.board_service import BoardService

        return BoardService()

    def _on_create_board(self) -> None:
        title, ok = QInputDialog.getText(self, "Tạo board", "Tên board mới:")
        if not ok or not title.strip():
            return

        svc = self._get_service()
        created = svc.create_board(title.strip())
        boards = svc.list_boards()
        self.refresh(boards, active_board_id=created.id)
        self.board_selected.emit(created.id)

    def _on_current_item_changed(self, current, _previous) -> None:
        if current is None:
            return
        board_id = current.data(Qt.ItemDataRole.UserRole)
        if board_id is None:
            return
        self._active_board_id = int(board_id)
        self.board_selected.emit(self._active_board_id)

    def _show_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return

        board_id = item.data(Qt.ItemDataRole.UserRole)
        if board_id is None:
            return

        menu = QMenu(self)
        act_rename = menu.addAction("Đổi tên board")
        act_delete = menu.addAction("Xóa board")
        chosen = menu.exec(self._list.mapToGlobal(pos))
        if chosen is None:
            return

        svc = self._get_service()

        if chosen == act_rename:
            new_title, ok = QInputDialog.getText(
                self,
                "Đổi tên board",
                "Tên mới:",
                text=item.text().split(" (", 1)[0],
            )
            if ok and new_title.strip():
                svc.rename_board(int(board_id), new_title.strip())
                self.refresh(svc.list_boards(), active_board_id=int(board_id))

        elif chosen == act_delete:
            if self._list.count() <= 1:
                QMessageBox.information(
                    self,
                    "Không thể xóa",
                    "Cần giữ ít nhất 1 board hoạt động.",
                )
                return

            reply = QMessageBox.question(
                self,
                "Xóa board",
                "Xóa board này và toàn bộ dữ liệu hàng/cột/cell của board?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            svc.delete_board(int(board_id))
            boards = svc.list_boards()
            self.refresh(boards)
            current_item = self._list.currentItem()
            if current_item is not None:
                current_id = current_item.data(Qt.ItemDataRole.UserRole)
                if current_id is not None:
                    self.board_selected.emit(int(current_id))
