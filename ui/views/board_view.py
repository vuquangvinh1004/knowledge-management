"""Màn hình bảng tổng hợp nghiên cứu liên tài liệu.

Board là bảng rows × cols. Người dùng click vào cell để chỉnh sửa nội dung.
Business logic KHÔNG nằm ở đây — gọi qua BoardService.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


class BoardView(QWidget):
    """Bảng tổng hợp nghiên cứu liên tài liệu."""

    note_open_requested = Signal(int)
    source_open_requested = Signal(int)
    sync_requested = Signal()
    export_markdown_requested = Signal()
    export_csv_requested = Signal()
    customize_requested = Signal()
    graph_view_requested = Signal()
    cell_edit_requested = Signal(int, int)

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

        self._btn_add_row = QPushButton("Đồng bộ source note")
        self._btn_add_row.setToolTip("Đồng bộ 1 hàng = 1 source note cho bảng hiện tại")
        self._btn_add_row.clicked.connect(self._request_sync)
        toolbar.addWidget(self._btn_add_row)

        toolbar.addSeparator()

        self._btn_export_md = QPushButton("Xuất Markdown")
        self._btn_export_md.clicked.connect(self._request_export_markdown)
        toolbar.addWidget(self._btn_export_md)

        self._btn_export_csv = QPushButton("Xuất CSV")
        self._btn_export_csv.clicked.connect(self._request_export_csv)
        toolbar.addWidget(self._btn_export_csv)

        toolbar.addSeparator()

        self._btn_customize = QPushButton("Tùy chỉnh")
        self._btn_customize.setObjectName("btnCustomize")
        self._btn_customize.setToolTip("Quản lý tiêu chí: thêm, xóa, sửa, sắp xếp")
        self._btn_customize.clicked.connect(self._request_customize)
        toolbar.addWidget(self._btn_customize)

        self._btn_graph_view = QPushButton("Đồ thị liên kết")
        self._btn_graph_view.setObjectName("btnGraphView")
        self._btn_graph_view.setToolTip("Mở đồ thị liên kết ghi chú")
        self._btn_graph_view.clicked.connect(self._request_graph_view)
        toolbar.addWidget(self._btn_graph_view)

        layout.addWidget(toolbar)

        # Empty state
        self._empty_state = QWidget()
        empty_layout = QHBoxLayout(self._empty_state)
        empty_layout.setContentsMargins(8, 8, 8, 8)
        empty_layout.setSpacing(12)

        self._empty_state_label = QLabel(
            "Chưa có source note để tổng hợp. Hãy thêm nguồn PDF và tạo source note trước."
        )
        self._empty_state_label.setWordWrap(False)
        self._empty_state_label.setObjectName("empty_state_message")
        self._empty_state_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        self._empty_state_button = QPushButton("Đồng bộ source note")
        self._empty_state_button.clicked.connect(self._request_sync)

        empty_layout.addWidget(self._empty_state_label)
        empty_layout.addStretch()
        empty_layout.addWidget(self._empty_state_button)
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

    @property
    def active_board_id(self) -> int | None:
        return self._active_board_id

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

        svc.ensure_full_meta_columns(board_id=self._active_board_id)
        self._cols = svc.list_columns(board_id=self._active_board_id, visible_only=True)
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
        # - source note rows -> cột ngang
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
        """Áp dụng project scope để đồng bộ source note theo ngữ cảnh hiện tại."""
        self._project_id = project_id
        self.refresh()

    # ------------------------------------------------------------------
    # Add row / col
    # ------------------------------------------------------------------

    def _sync_source_rows(self) -> None:
        self._request_sync()

    # ------------------------------------------------------------------
    # Cell edit
    # ------------------------------------------------------------------

    def _on_cell_double_clicked(self, row_idx: int, col_idx: int) -> None:
        if row_idx >= len(self._cols) or col_idx >= len(self._rows):
            return
        col = self._cols[row_idx]
        row = self._rows[col_idx]
        self.cell_edit_requested.emit(int(row.id), int(col.id))

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        action_sync_rows = menu.addAction("Đồng bộ lại từ source note")

        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == action_sync_rows:
            self._request_sync()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_markdown(self) -> None:
        self._request_export_markdown()

    def _export_csv(self) -> None:
        self._request_export_csv()

    # ------------------------------------------------------------------
    # Graph view
    # ------------------------------------------------------------------

    def _open_graph_view(self) -> None:
        self._request_graph_view()

    # ------------------------------------------------------------------
    # Customize criteria
    # ------------------------------------------------------------------

    def _open_criteria_manager(self) -> None:
        self._request_customize()

    def _request_sync(self) -> None:
        self.sync_requested.emit()

    def _request_export_markdown(self) -> None:
        self.export_markdown_requested.emit()

    def _request_export_csv(self) -> None:
        self.export_csv_requested.emit()

    def _request_customize(self) -> None:
        self.customize_requested.emit()

    def _request_graph_view(self) -> None:
        self.graph_view_requested.emit()


