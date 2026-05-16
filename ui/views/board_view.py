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
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from ui.widgets.board_selector_panel import BoardSelectorPanel
from ui.widgets.empty_state import EmptyStateWidget
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
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QLabel("Bảng nghiên cứu")
        header.setObjectName("view_header")
        layout.addWidget(header)

        self._board_selector = BoardSelectorPanel(self)
        self._board_selector.board_selected.connect(self._on_board_selected)
        layout.addWidget(self._board_selector)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        self._btn_add_row = QPushButton("+ Hàng")
        self._btn_add_row.setToolTip("Thêm hàng mới")
        self._btn_add_row.clicked.connect(self._add_row)
        toolbar.addWidget(self._btn_add_row)

        self._btn_add_col = QPushButton("+ Cột")
        self._btn_add_col.setToolTip("Thêm cột mới")
        self._btn_add_col.clicked.connect(self._add_col)
        toolbar.addWidget(self._btn_add_col)

        self._btn_init = QToolButton()
        self._btn_init.setText("Khởi tạo")
        self._btn_init.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        init_menu = QMenu(self._btn_init)
        self._act_init_meta = init_menu.addAction("(i) Đầy đủ (34 cột)")
        self._act_init_lit = init_menu.addAction("(ii) Chỉ tổng hợp tài liệu (20 cột)")
        self._act_init_note = init_menu.addAction("(iii) Tạo Board note")
        self._act_init_meta.triggered.connect(self._init_template_meta_analysis)
        self._act_init_lit.triggered.connect(self._init_template_literature)
        self._act_init_note.triggered.connect(self._init_template_board_note_only)
        self._btn_init.setMenu(init_menu)
        toolbar.addWidget(self._btn_init)

        toolbar.addSeparator()

        self._btn_open_board_note = QPushButton("Mở Board note")
        self._btn_open_board_note.setToolTip("Mở note tổng hợp gắn với board hiện tại")
        self._btn_open_board_note.clicked.connect(self._open_linked_board_note)
        self._btn_open_board_note.setVisible(False)
        toolbar.addWidget(self._btn_open_board_note)

        toolbar.addSeparator()

        self._btn_export_md = QPushButton("Xuất Markdown")
        self._btn_export_md.clicked.connect(self._export_markdown)
        toolbar.addWidget(self._btn_export_md)

        self._btn_export_csv = QPushButton("Xuất CSV")
        self._btn_export_csv.clicked.connect(self._export_csv)
        toolbar.addWidget(self._btn_export_csv)

        toolbar.addSeparator()
        self._btn_graph_view = QPushButton("Đồ thị liên kết")
        self._btn_graph_view.setToolTip("Mở đồ thị liên kết ghi chú")
        self._btn_graph_view.clicked.connect(self._open_graph_view)
        toolbar.addWidget(self._btn_graph_view)

        layout.addWidget(toolbar)

        # Empty state
        self._empty_state = EmptyStateWidget(
            "Chưa có board nào.\nThêm hàng và cột để bắt đầu tổng hợp nghiên cứu.",
            action_label="Thêm hàng đầu tiên",
        )
        if self._empty_state.action_button:
            self._empty_state.action_button.clicked.connect(self._add_row)
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
        boards = svc.list_boards()
        if not boards:
            default_board = svc.get_default_board()
            boards = [default_board]

        if self._active_board_id is None or all(b.id != self._active_board_id for b in boards):
            self._active_board_id = boards[0].id

        self._board_selector.refresh(boards, active_board_id=self._active_board_id)
        self._rows = svc.list_rows(board_id=self._active_board_id)
        self._cols = svc.list_columns(board_id=self._active_board_id)
        self._rebuild_table()
        self._update_visibility()
        self._refresh_board_note_button()

    def _on_board_selected(self, board_id: int) -> None:
        self._active_board_id = board_id
        self.refresh()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()

    def _rebuild_table(self) -> None:
        """Dựng lại QTableWidget từ rows/cols/cells."""
        svc = self._get_service()
        self._table.setRowCount(len(self._rows))
        self._table.setColumnCount(len(self._cols))

        # Headers
        self._table.setHorizontalHeaderLabels([c.label for c in self._cols])
        self._table.setVerticalHeaderLabels([r.label for r in self._rows])

        # Fill cells
        cells_map: dict[tuple[int, int], str] = {}
        for cell in svc.get_all_cells(board_id=self._active_board_id):
            cells_map[(cell.row_id, cell.col_id)] = cell.content_md or ""

        for ri, row in enumerate(self._rows):
            for ci, col in enumerate(self._cols):
                content = cells_map.get((row.id, col.id), "")
                item = QTableWidgetItem(content[:80] + ("…" if len(content) > 80 else ""))
                item.setToolTip(content)
                self._table.setItem(ri, ci, item)

        header = self._table.horizontalHeader()
        if len(self._cols) >= 20:
            # Board lớn ưu tiên điều khiển thủ công và scroll ngang ổn định.
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setDefaultSectionSize(180)
        else:
            self._table.resizeColumnsToContents()

    def _update_visibility(self) -> None:
        has_data = bool(self._rows) or bool(self._cols)
        self._empty_state.setVisible(not has_data)
        self._table.setVisible(has_data)
        self._btn_export_md.setEnabled(has_data)
        self._btn_export_csv.setEnabled(has_data)

    def _refresh_board_note_button(self) -> None:
        if self._active_board_id is None:
            self._btn_open_board_note.setVisible(False)
            self._btn_open_board_note.setEnabled(False)
            return
        try:
            board = self._get_service().get_board(self._active_board_id)
            has_linked = board.linked_note_id is not None
        except Exception:
            has_linked = False
        self._btn_open_board_note.setVisible(has_linked)
        self._btn_open_board_note.setEnabled(has_linked)

    def _init_template_meta_analysis(self) -> None:
        self._init_board_from_template("meta_analysis", "Meta-analysis Board")

    def _init_template_literature(self) -> None:
        self._init_board_from_template("literature", "Literature Review Board")

    def _init_board_from_template(self, template_name: str, default_title: str) -> None:
        title, ok = QInputDialog.getText(self, "Khởi tạo board", "Tên board:", text=default_title)
        if not ok or not title.strip():
            return

        create_note = QMessageBox.question(
            self,
            "Tạo Board note",
            "Bạn có muốn tạo kèm board_note cho board này không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

        try:
            from config.paths import NOTES_DIR

            board, linked_note_id = self._get_service().create_from_template(
                template_name,
                title.strip(),
                notes_dir=NOTES_DIR,
                create_linked_board_note=create_note,
            )
            if board is not None:
                self._active_board_id = board.id
                self.refresh()
            if linked_note_id:
                QMessageBox.information(self, "Hoàn tất", "Đã tạo board và board_note liên kết.")
            else:
                QMessageBox.information(self, "Hoàn tất", "Đã khởi tạo board từ template.")
        except Exception as exc:
            QMessageBox.warning(self, "Lỗi khởi tạo", str(exc))

    def _init_template_board_note_only(self) -> None:
        title, ok = QInputDialog.getText(
            self,
            "Tạo Board note",
            "Tiêu đề board_note:",
            text="board tổng hợp mới",
        )
        if not ok or not title.strip():
            return
        try:
            from config.paths import NOTES_DIR

            _, note_id = self._get_service().create_from_template(
                "board_note",
                title.strip(),
                notes_dir=NOTES_DIR,
            )
            if note_id is not None:
                self.note_open_requested.emit(note_id)
        except Exception as exc:
            QMessageBox.warning(self, "Lỗi tạo note", str(exc))

    def _open_linked_board_note(self) -> None:
        if self._active_board_id is None:
            return
        try:
            board = self._get_service().get_board(self._active_board_id)
        except Exception:
            return
        if board.linked_note_id is not None:
            self.note_open_requested.emit(board.linked_note_id)

    # ------------------------------------------------------------------
    # Add row / col
    # ------------------------------------------------------------------

    def _add_row(self) -> None:
        label, ok = QInputDialog.getText(self, "Thêm hàng", "Tên hàng:")
        if ok and label.strip():
            self._get_service().create_row(label.strip(), board_id=self._active_board_id)
            self.refresh()

    def _add_col(self) -> None:
        label, ok = QInputDialog.getText(self, "Thêm cột", "Tên cột:")
        if ok and label.strip():
            self._get_service().create_column(label.strip(), board_id=self._active_board_id)
            self.refresh()

    # ------------------------------------------------------------------
    # Cell edit
    # ------------------------------------------------------------------

    def _on_cell_double_clicked(self, row_idx: int, col_idx: int) -> None:
        if row_idx >= len(self._rows) or col_idx >= len(self._cols):
            return
        row = self._rows[row_idx]
        col = self._cols[col_idx]

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
        action_rename_row = menu.addAction("Đổi tên hàng")
        action_rename_col = menu.addAction("Đổi tên cột")
        menu.addSeparator()
        action_del_row = menu.addAction("Xóa hàng")
        action_del_col = menu.addAction("Xóa cột")

        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if not action:
            return

        idx = self._table.currentIndex()
        ri, ci = idx.row(), idx.column()

        if action == action_rename_row and ri < len(self._rows):
            row = self._rows[ri]
            new_label, ok = QInputDialog.getText(
                self, "Đổi tên hàng", "Tên mới:", text=row.label
            )
            if ok and new_label.strip():
                self._get_service().rename_row(
                    row.id,
                    new_label.strip(),
                    board_id=self._active_board_id,
                )
                self.refresh()

        elif action == action_rename_col and ci < len(self._cols):
            col = self._cols[ci]
            new_label, ok = QInputDialog.getText(
                self, "Đổi tên cột", "Tên mới:", text=col.label
            )
            if ok and new_label.strip():
                self._get_service().rename_column(
                    col.id,
                    new_label.strip(),
                    board_id=self._active_board_id,
                )
                self.refresh()

        elif action == action_del_row and ri < len(self._rows):
            row = self._rows[ri]
            reply = QMessageBox.question(
                self,
                "Xóa hàng",
                f"Xóa hàng '{row.label}' và toàn bộ nội dung?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._get_service().delete_row(row.id, board_id=self._active_board_id)
                self.refresh()

        elif action == action_del_col and ci < len(self._cols):
            col = self._cols[ci]
            reply = QMessageBox.question(
                self,
                "Xóa cột",
                f"Xóa cột '{col.label}' và toàn bộ nội dung?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._get_service().delete_column(col.id, board_id=self._active_board_id)
                self.refresh()

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

