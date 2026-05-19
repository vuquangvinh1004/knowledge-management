"""Màn hình Research Board — tổng hợp nghiên cứu liên tài liệu.

Board là bảng rows × cols. Người dùng click vào cell để chỉnh sửa nội dung.
Business logic KHÔNG nằm ở đây — gọi qua BoardService.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ui.widgets.empty_state import EmptyStateWidget
from ui.widgets.dialogs.board_criteria_manager_dialog import BoardCriteriaManagerDialog
from core.utils.logger import get_logger

logger = get_logger()


class _CellEditDialog(QDialog):
    """Dialog chỉnh sửa nội dung một cell."""

    def __init__(self, current_content: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chỉnh sửa ô")
        self.setMinimumSize(400, 260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nội dung Markdown:"))
        self._editor = QPlainTextEdit()
        self._editor.setPlainText(current_content)
        layout.addWidget(self._editor)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def content(self) -> str:
        return self._editor.toPlainText()


class BoardView(QWidget):
    """Research Board — tổng hợp nghiên cứu liên tài liệu."""

    note_open_requested = Signal(int)
    source_open_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list = []   # list[BoardRow]
        self._cols: list = []   # list[BoardColumn]
        self._active_board_id: int | None = None
        self._project_id: int | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        self._btn_add_row = QPushButton("Đồng bộ nguồn")
        self._btn_add_row.setToolTip("Đồng bộ 1 hàng = 1 source_note cho board hiện tại")
        self._btn_add_row.clicked.connect(self._sync_source_rows)
        toolbar.addWidget(self._btn_add_row)

        toolbar.addSeparator()

        self._btn_export_md = QPushButton("Xuất Markdown")
        self._btn_export_md.clicked.connect(self._export_markdown)
        toolbar.addWidget(self._btn_export_md)

        self._btn_export_csv = QPushButton("Xuất CSV")
        self._btn_export_csv.clicked.connect(self._export_csv)
        toolbar.addWidget(self._btn_export_csv)

        toolbar.addSeparator()

        self._btn_customize = QPushButton("Tùy chỉnh")
        self._btn_customize.setObjectName("btnCustomize")
        self._btn_customize.setToolTip("Quản lý tiêu chí: thêm, xóa, sửa, sắp xếp")
        self._btn_customize.clicked.connect(self._open_criteria_manager)
        toolbar.addWidget(self._btn_customize)

        self._btn_graph_view = QPushButton("Đồ thị liên kết")
        self._btn_graph_view.setObjectName("btnGraphView")
        self._btn_graph_view.setToolTip("Mở đồ thị liên kết ghi chú")
        self._btn_graph_view.clicked.connect(self._open_graph_view)
        toolbar.addWidget(self._btn_graph_view)

        layout.addWidget(toolbar)

        # Empty state
        self._empty_state = EmptyStateWidget(
            "Chưa có source_note để tổng hợp.\nHãy thêm nguồn PDF và tạo source_note trước.",
            action_label="Đồng bộ source_note",
        )
        if self._empty_state.action_button:
            self._empty_state.action_button.clicked.connect(self._sync_source_rows)
        layout.addWidget(self._empty_state)

        # Table widget
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._table)

        self._update_visibility()

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------

    def _get_service(self):
        from core.services.board_service import BoardService
        return BoardService()

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tải lại dữ liệu board từ DB."""
        svc = self._get_service()
        if self._active_board_id is None:
            self._active_board_id = svc.get_default_board().id
        else:
            try:
                svc.get_board(self._active_board_id)
            except Exception:
                self._active_board_id = svc.get_default_board().id

        self._cols = svc.ensure_full_meta_columns(board_id=self._active_board_id)
        self._rows = svc.sync_rows_with_source_notes(
            board_id=self._active_board_id,
            project_id=self._project_id,
        )

        self._rebuild_table()
        self._update_visibility()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()

    def _rebuild_table(self) -> None:
        """Dựng lại QTableWidget từ rows/cols/cells."""
        svc = self._get_service()
        # Hiển thị transpose:
        # - source_note rows -> cột ngang
        # - tiêu chí (columns) -> hàng dọc bên trái
        self._table.setRowCount(len(self._cols))
        self._table.setColumnCount(len(self._rows))

        # Headers
        self._table.setHorizontalHeaderLabels([r.label for r in self._rows])
        self._table.setVerticalHeaderLabels([c.label for c in self._cols])

        # Fill cells
        cells_map: dict[tuple[int, int], str] = {}
        for cell in svc.get_all_cells(board_id=self._active_board_id):
            cells_map[(cell.row_id, cell.col_id)] = cell.content_md or ""

        for ri, col in enumerate(self._cols):
            for ci, row in enumerate(self._rows):
                content = cells_map.get((row.id, col.id), "")
                item = QTableWidgetItem(content)
                item.setToolTip(content)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(ri, ci, item)

        h_header = self._table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setDefaultSectionSize(280)

        v_header = self._table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        v_header.setMinimumSectionSize(60)
        self._table.verticalHeader().setFixedWidth(250)
        
        self._table.resizeRowsToContents()
        self._table.setWordWrap(True)

    def _update_visibility(self) -> None:
        has_data = bool(self._rows)
        self._empty_state.setVisible(not has_data)
        self._table.setVisible(True)
        self._btn_export_md.setEnabled(bool(self._rows))
        self._btn_export_csv.setEnabled(bool(self._rows))

    def set_project_context(self, project_id: int | None) -> None:
        """Áp dụng project scope để đồng bộ source_note theo ngữ cảnh hiện tại."""
        self._project_id = project_id
        self.refresh()

    # ------------------------------------------------------------------
    # Add row / col
    # ------------------------------------------------------------------

    def _sync_source_rows(self) -> None:
        svc = self._get_service()
        svc.sync_rows_with_source_notes(
            board_id=self._active_board_id,
            project_id=self._project_id,
        )
        svc.sync_cells_from_source_note_metadata(
            board_id=self._active_board_id,
            project_id=self._project_id,
        )
        self.refresh()

    # ------------------------------------------------------------------
    # Cell edit
    # ------------------------------------------------------------------

    def _on_cell_double_clicked(self, row_idx: int, col_idx: int) -> None:
        if row_idx >= len(self._cols) or col_idx >= len(self._rows):
            return
        col = self._cols[row_idx]
        row = self._rows[col_idx]

        svc = self._get_service()
        existing_cell = svc.get_cell(row.id, col.id, board_id=self._active_board_id)
        current_content = existing_cell.content_md if existing_cell else ""

        dlg = _CellEditDialog(current_content, self)
        if dlg.exec():
            svc.update_cell(
                row.id,
                col.id,
                content_md=dlg.content,
                board_id=self._active_board_id,
            )
            self.refresh()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        action_sync_rows = menu.addAction("Đồng bộ lại từ source_note")

        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == action_sync_rows:
            self._sync_source_rows()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_markdown(self) -> None:
        try:
            from config.paths import EXPORTS_DIR
            from core.services.export_service import ExportService
            svc = ExportService(EXPORTS_DIR)
            path = svc.export_board_markdown(board_id=self._active_board_id)
            QMessageBox.information(self, "Xuất thành công", f"Đã xuất:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Lỗi xuất", str(exc))

    def _export_csv(self) -> None:
        try:
            from config.paths import EXPORTS_DIR
            from core.services.export_service import ExportService
            svc = ExportService(EXPORTS_DIR)
            path = svc.export_board_csv(board_id=self._active_board_id)
            QMessageBox.information(self, "Xuất thành công", f"Đã xuất:\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "Lỗi xuất", str(exc))

    # ------------------------------------------------------------------
    # Graph view
    # ------------------------------------------------------------------

    def _open_graph_view(self) -> None:
        """Mở dialog Graph view dựa trên GraphService."""
        from ui.widgets.graph_view import GraphViewWidget

        dlg = QDialog(self)
        dlg.setWindowTitle("Đồ thị liên kết (Graph view)")
        dlg.setMinimumSize(980, 640)

        layout = QVBoxLayout(dlg)
        graph = GraphViewWidget(dlg)
        graph.note_open_requested.connect(self.note_open_requested)
        graph.source_open_requested.connect(self.source_open_requested)
        layout.addWidget(graph)

        action_row = QHBoxLayout()

        btn_fullscreen = QPushButton("Toàn màn hình")
        btn_fullscreen.setCheckable(True)

        def _toggle_fullscreen(checked: bool) -> None:
            if checked:
                dlg.showFullScreen()
                btn_fullscreen.setText("Thoát toàn màn hình")
            else:
                dlg.showNormal()
                btn_fullscreen.setText("Toàn màn hình")

        btn_fullscreen.toggled.connect(_toggle_fullscreen)
        action_row.addWidget(btn_fullscreen)
        action_row.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Đóng")

        action_row.addWidget(buttons)
        layout.addLayout(action_row)

        dlg.exec()

    # ------------------------------------------------------------------
    # Customize criteria
    # ------------------------------------------------------------------

    def _open_criteria_manager(self) -> None:
        """Mở dialog quản lý tiêu chí bảng."""
        logger.debug(f"_open_criteria_manager called, _active_board_id={self._active_board_id}")
        
        svc = self._get_service()
        if self._active_board_id is None:
            logger.warning("No active board ID set")
            QMessageBox.warning(self, "Lỗi", "Chưa có board nào được chọn!")
            return

        board = svc.get_board(self._active_board_id)
        if board is None:
            logger.warning(f"Board {self._active_board_id} not found")
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy board!")
            return

        logger.debug(f"Loading criteria for board {self._active_board_id}")
        # Lấy danh sách tiêu chí hiện tại từ board columns
        current_criteria = [col.label for col in svc.list_columns(self._active_board_id)]
        logger.debug(f"Current criteria: {current_criteria}")

        dlg = BoardCriteriaManagerDialog(current_criteria, self)
        logger.debug("Dialog created, executing...")
        
        if dlg.exec():
            new_criteria = dlg.get_criteria()
            logger.debug(f"Dialog accepted with new criteria: {new_criteria}")

            # Xác định các tiêu chí bị thêm, sửa, xóa
            # Lưu ý: Điều này là đơn giản - chỉ support add/delete column, không support rename
            # Nếu tương lai cần rename, sẽ cần track mapping cũ->mới

            deleted_criteria = set(current_criteria) - set(new_criteria)
            added_criteria = set(new_criteria) - set(current_criteria)
            reordered = new_criteria  # Danh sách mới đã được sắp xếp

            logger.debug(f"Deleted: {deleted_criteria}, Added: {added_criteria}")

            try:
                # Xóa các tiêu chí bị xóa (xóa column và cascade ô)
                for criterion in deleted_criteria:
                    col = next(
                        (c for c in svc.list_columns(self._active_board_id) if c.label == criterion),
                        None,
                    )
                    if col:
                        logger.debug(f"Deleting column {criterion} (id={col.id})")
                        svc.delete_column(col.id, self._active_board_id)

                # Thêm tiêu chí mới
                for criterion in added_criteria:
                    logger.debug(f"Creating column {criterion}")
                    svc.create_column(criterion, self._active_board_id)

                # Cập nhật thứ tự tiêu chí (nếu cần)
                # Lưu ý: Hiện tại, order được lưu implicit qua position trong list_columns
                # Nếu muốn explicit order, cần thêm column `position` vào model

                QMessageBox.information(self, "Thành công", "Tiêu chí đã được cập nhật.")
                self.refresh()
            except Exception as exc:
                logger.exception("Error updating board criteria")
                QMessageBox.warning(self, "Lỗi", f"Không thể cập nhật tiêu chí: {exc}")
        else:
            logger.debug("Dialog rejected/closed")


