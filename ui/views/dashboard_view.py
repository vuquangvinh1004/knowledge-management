"""Màn hình Trang chính - tóm tắt và truy cập nhanh.

Business logic không được viết ở đây. Chỉ gọi service và phát tín hiệu.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.empty_state import EmptyStateWidget


class DashboardView(QWidget):
    """
    Trang chính hiển thị:
    - Số lượng nguồn, ghi chú, trích xuất
    - 5 tài liệu gần nhất
    - Nút nhập PDF nhanh

    Signals:
        open_source_requested(int): Khi người dùng double-click một source.
        import_requested: Khi nhấn nút nhập.
    """

    open_source_requested = Signal(int)
    import_requested = Signal()
    note_catalog_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active_note_filters: dict[int, set[str]] = {}
        self._sort_column = 1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Trang chính")
        header.setObjectName("view_header")
        layout.addWidget(header)

        # Thanh thống kê
        self._stats_bar = self._build_stats_bar()
        layout.addWidget(self._stats_bar)

        # Danh sách gần nhất
        layout.addWidget(QLabel("Tài liệu gần đây:"))

        self._recent_list = QListWidget()
        self._recent_list.setObjectName("recent_sources_list")
        self._recent_list.setMaximumHeight(200)
        self._recent_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._recent_list)

        self._empty_recent = EmptyStateWidget(
            "Chưa có tài liệu nào.\nHãy nhập PDF để bắt đầu.",
            action_label="Nhập tài liệu PDF",
        )
        if self._empty_recent.action_button:
            self._empty_recent.action_button.clicked.connect(self.import_requested)
        layout.addWidget(self._empty_recent)

        layout.addWidget(QLabel("Danh sách ghi chú:"))

        self._notes_table = QTableWidget(0, 5)
        self._notes_table.setObjectName("dashboard_notes_table")
        self._notes_table.setHorizontalHeaderLabels(
            ["STT", "Tên ghi chú", "Loại ghi chú", "Chế độ", "Trạng thái"]
        )
        self._base_note_headers = ["STT", "Tên ghi chú", "Loại ghi chú", "Chế độ", "Trạng thái"]
        self._notes_table.setSortingEnabled(False)
        self._notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._notes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._notes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._notes_table.setAlternatingRowColors(True)
        self._notes_table.verticalHeader().setVisible(False)
        self._notes_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._notes_table.customContextMenuRequested.connect(self._on_notes_table_context_menu)

        header = self._notes_table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.sectionClicked.connect(self._on_notes_header_clicked)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_notes_header_context_menu)
        self._notes_table.setToolTip(
            "Click header để sắp xếp (trừ cột STT). Chuột phải trên header để lọc theo danh sách giá trị."
        )
        layout.addWidget(self._notes_table)

        layout.addStretch()

    def _build_stats_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("stats_bar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(24)

        self._lbl_sources = QLabel("—")
        self._lbl_sources.setObjectName("stat_label")
        self._lbl_notes = QLabel("—")
        self._lbl_notes.setObjectName("stat_label")
        self._lbl_extracts = QLabel("—")
        self._lbl_extracts.setObjectName("stat_label")
        self._lbl_source_notes = QLabel("—")
        self._lbl_source_notes.setObjectName("stat_label")
        self._lbl_concept_notes = QLabel("—")
        self._lbl_concept_notes.setObjectName("stat_label")
        self._lbl_synthesis_notes = QLabel("—")
        self._lbl_synthesis_notes.setObjectName("stat_label")
        self._lbl_board_notes = QLabel("—")
        self._lbl_board_notes.setObjectName("stat_label")
        self._lbl_orphan_notes = QLabel("—")
        self._lbl_orphan_notes.setObjectName("stat_label")

        for lbl, name in [
            (self._lbl_sources, "Nguồn"),
            (self._lbl_notes, "Ghi chú"),
            (self._lbl_extracts, "Trích xuất"),
            (self._lbl_source_notes, "source note"),
            (self._lbl_concept_notes, "concept note"),
            (self._lbl_synthesis_notes, "synthesis note"),
            (self._lbl_board_notes, "board note"),
            (self._lbl_orphan_notes, "Khác"),
        ]:
            col = QWidget()
            col_lay = QVBoxLayout(col)
            col_lay.setContentsMargins(0, 0, 0, 0)
            col_lay.setSpacing(2)
            name_lbl = QLabel(name)
            name_lbl.setObjectName("stat_name")
            col_lay.addWidget(name_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            col_lay.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(col)

        lay.addStretch()
        return bar

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tải lại dữ liệu từ DB."""
        self._load_stats()
        self._load_recent()
        self._load_notes()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_stats(self) -> None:
        try:
            from core.storage.session import get_session
            from core.storage.models import Source, Note, Extract
            from config.paths import DATABASE_FILE, NOTES_DIR
            from core.services.search_service import SearchService
            with get_session() as session:
                n_sources = session.query(Source).filter(Source.is_deleted == 0).count()
                n_notes = session.query(Note).filter(Note.is_deleted == 0).count()
                n_extracts = session.query(Extract).count()

            search_svc = SearchService(str(DATABASE_FILE), NOTES_DIR)
            by_type = search_svc.count_notes_by_type()
            orphan_count = len(search_svc.list_orphan_note_ids())

            self._lbl_sources.setText(str(n_sources))
            self._lbl_notes.setText(str(n_notes))
            self._lbl_extracts.setText(str(n_extracts))
            self._lbl_source_notes.setText(str(by_type.get("source_note", 0)))
            self._lbl_concept_notes.setText(str(by_type.get("concept_note", 0)))
            self._lbl_synthesis_notes.setText(str(by_type.get("synthesis_note", 0)))
            self._lbl_board_notes.setText(str(by_type.get("board_note", 0)))
            self._lbl_orphan_notes.setText(str(orphan_count))
        except Exception:  # noqa: BLE001
            pass

    def _load_recent(self) -> None:
        self._recent_list.clear()
        try:
            from core.services.source_service import SourceService
            sources = SourceService().list_all()[:5]
        except Exception:  # noqa: BLE001
            sources = []

        has_items = bool(sources)
        self._recent_list.setVisible(has_items)
        self._empty_recent.setVisible(not has_items)

        for src in sources:
            item = QListWidgetItem(src.title or src.file_path)
            item.setData(Qt.ItemDataRole.UserRole, src.id)
            self._recent_list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        source_id = item.data(Qt.ItemDataRole.UserRole)
        if source_id is not None:
            self.open_source_requested.emit(source_id)

    def _load_notes(self) -> None:
        """Nạp bảng danh sách ghi chú cho Trang chính."""
        self._notes_table.setRowCount(0)

        try:
            from config.paths import NOTES_DIR
            from core.services.note_service import NoteService

            notes = NoteService(NOTES_DIR).list_notes_for_management(include_deleted=True)
        except Exception:  # noqa: BLE001
            notes = []

        for row_idx, row in enumerate(notes):
            self._notes_table.insertRow(row_idx)

            note_id = int(row.get("note_id") or 0)
            note_public_id = str(row.get("note_public_id") or "")
            note_type = str(row.get("note_type") or "note")
            title = self._display_title(
                note_type=note_type,
                title=str(row.get("title") or "(không tiêu đề)"),
            )
            note_type = str(row.get("note_type") or "note")
            scope = str(row.get("scope_label") or "Toàn cục")
            delete_state = int(row.get("is_deleted") or 0)

            stt_item = QTableWidgetItem(str(row_idx + 1))
            stt_item.setData(Qt.ItemDataRole.UserRole, note_id)
            stt_item.setData(Qt.ItemDataRole.UserRole + 1, note_public_id)
            stt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            title_item = QTableWidgetItem(title)
            type_item = QTableWidgetItem(note_type)
            scope_item = QTableWidgetItem(scope)

            status_text, status_color = self._status_style(delete_state)
            status_item = QTableWidgetItem(status_text)
            status_item.setData(Qt.ItemDataRole.UserRole, delete_state)
            status_item.setForeground(status_color)

            if note_public_id:
                tooltip = f"Public ID: {note_public_id}\nID nội bộ: {note_id}"
                stt_item.setToolTip(tooltip)
                title_item.setToolTip(tooltip)

            self._notes_table.setItem(row_idx, 0, stt_item)
            self._notes_table.setItem(row_idx, 1, title_item)
            self._notes_table.setItem(row_idx, 2, type_item)
            self._notes_table.setItem(row_idx, 3, scope_item)
            self._notes_table.setItem(row_idx, 4, status_item)

        self._apply_sort()
        self._apply_note_filters()
        self._refresh_note_header_filter_badges()

    @staticmethod
    def _display_title(note_type: str, title: str) -> str:
        """Chuẩn hóa title hiển thị để tránh prefix dư thừa ở source note cũ."""
        t = title.strip()
        if note_type == "source_note" and t.lower().startswith("source - "):
            return t[len("source - "):].strip()
        return t

    @staticmethod
    def _status_style(delete_state: int) -> tuple[str, Qt.GlobalColor]:
        if delete_state == 0:
            return "● Đang sử dụng", Qt.GlobalColor.darkGreen
        if delete_state == 1:
            return "● Xóa tạm", Qt.GlobalColor.gray
        return "● Đã xóa", Qt.GlobalColor.red

    def _on_notes_header_clicked(self, col: int) -> None:
        """Sort theo header, trừ cột STT (index 0)."""
        if col == 0:
            return

        if self._sort_column == col:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = col
            self._sort_order = Qt.SortOrder.AscendingOrder

        self._apply_sort()
        self._apply_note_filters()

    def _apply_sort(self) -> None:
        """Áp dụng sort hiện tại lên bảng ghi chú (không sort theo STT)."""
        self._notes_table.sortItems(self._sort_column, self._sort_order)

    def _on_notes_header_context_menu(self, pos) -> None:
        """Context menu filter theo danh sách giá trị unique của cột."""
        header = self._notes_table.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return

        # STT chỉ để hiển thị thứ tự, không hỗ trợ filter theo yêu cầu.
        if col == 0:
            return

        values = self._unique_values_for_column(col)
        if not values:
            return

        col_name = self._notes_table.horizontalHeaderItem(col).text()
        menu = QMenu(self)
        label_action = menu.addAction(f"Lọc cột: {col_name}")
        label_action.setEnabled(False)
        menu.addSeparator()
        action_select_all = menu.addAction("Chọn tất cả")
        action_clear_selection = menu.addAction("Bỏ chọn tất cả")
        action_clear_col = menu.addAction("Xóa lọc cột này")
        action_clear_all = menu.addAction("Xóa tất cả bộ lọc")
        menu.addSeparator()

        current_selected = set(self._active_note_filters.get(col, set(values)))
        value_actions: dict = {}
        for value in values:
            action = menu.addAction(value)
            action.setCheckable(True)
            action.setChecked(value in current_selected)
            value_actions[action] = value

        if col not in self._active_note_filters:
            action_clear_col.setEnabled(False)
        if not self._active_note_filters:
            action_clear_all.setEnabled(False)

        chosen = menu.exec(header.mapToGlobal(pos))
        if chosen == action_select_all:
            self._active_note_filters.pop(col, None)
            self._apply_note_filters()
            self._refresh_note_header_filter_badges()
        elif chosen == action_clear_selection:
            self._active_note_filters[col] = set()
            self._apply_note_filters()
            self._refresh_note_header_filter_badges()
        elif chosen in value_actions:
            value = value_actions[chosen]
            selected = set(self._active_note_filters.get(col, set(values)))
            if value in selected:
                selected.remove(value)
            else:
                selected.add(value)

            if selected == set(values):
                self._active_note_filters.pop(col, None)
            else:
                self._active_note_filters[col] = selected
            self._apply_note_filters()
            self._refresh_note_header_filter_badges()
        elif chosen == action_clear_col:
            self._active_note_filters.pop(col, None)
            self._apply_note_filters()
            self._refresh_note_header_filter_badges()
        elif chosen == action_clear_all:
            self._active_note_filters.clear()
            self._apply_note_filters()
            self._refresh_note_header_filter_badges()

    def _unique_values_for_column(self, col: int) -> list[str]:
        values: set[str] = set()
        for row in range(self._notes_table.rowCount()):
            item = self._notes_table.item(row, col)
            if item is None:
                continue
            values.add(item.text())
        return sorted(values, key=lambda v: v.lower())

    def _on_notes_table_context_menu(self, pos) -> None:
        """Context menu theo trạng thái note: khôi phục/xóa cứng/xóa hoàn toàn."""
        item = self._notes_table.itemAt(pos)
        if item is None:
            return

        row = item.row()
        note_id_item = self._notes_table.item(row, 0)
        status_item = self._notes_table.item(row, 4)
        if note_id_item is None or status_item is None:
            return

        note_id_raw = note_id_item.data(Qt.ItemDataRole.UserRole)
        if note_id_raw is None:
            return
        note_id = int(note_id_raw)
        delete_state = int(status_item.data(Qt.ItemDataRole.UserRole) or 0)

        menu = QMenu(self)
        action_restore = None
        action_mark_hard = None
        action_purge = None

        if delete_state == 1:
            action_restore = menu.addAction("Khôi phục")
            action_mark_hard = menu.addAction("Xóa cứng")
        elif delete_state == 2:
            action_purge = menu.addAction("Xóa hoàn toàn")
        else:
            return

        chosen = menu.exec(self._notes_table.viewport().mapToGlobal(pos))
        if chosen == action_restore:
            self._restore_note(note_id)
        elif chosen == action_mark_hard:
            self._mark_note_hard_deleted(note_id)
        elif chosen == action_purge:
            self._purge_note(note_id)

    def _restore_note(self, note_id: int) -> None:
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        try:
            NoteService(NOTES_DIR).restore(note_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể khôi phục ghi chú:\n{exc}")
            return

        self.refresh()
        self.note_catalog_changed.emit()

    def _mark_note_hard_deleted(self, note_id: int) -> None:
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        svc = NoteService(NOTES_DIR)
        try:
            impact = svc.get_note_delete_impact(note_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
            return

        reply = QMessageBox.warning(
            self,
            "Xác nhận xóa cứng",
            (
                f"Ghi chú: {impact.get('title') or '(không tiêu đề)'}\n"
                f"Incoming links: {impact.get('incoming_links')}\n"
                f"Outgoing links: {impact.get('outgoing_links')}\n"
                f"Extract refs: {impact.get('extract_refs')}\n"
                f"Asset refs: {impact.get('asset_refs')}\n\n"
                "Thao tác này sẽ chuyển ghi chú sang trạng thái Đã xóa (màu đỏ)."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            svc.mark_hard_deleted(note_id, delete_file=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa cứng ghi chú:\n{exc}")
            return

        self.refresh()
        self.note_catalog_changed.emit()

    def _purge_note(self, note_id: int) -> None:
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        reply = QMessageBox.warning(
            self,
            "Xóa hoàn toàn",
            "Ghi chú sẽ bị xóa vĩnh viễn khỏi database và không thể hoàn tác. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            NoteService(NOTES_DIR).hard_delete(note_id, delete_file=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể xóa hoàn toàn ghi chú:\n{exc}")
            return

        self.refresh()
        self.note_catalog_changed.emit()

    def _apply_note_filters(self) -> None:
        """Áp dụng tất cả bộ lọc đang active lên bảng ghi chú."""
        for row in range(self._notes_table.rowCount()):
            visible = True
            for col, selected_values in self._active_note_filters.items():
                item = self._notes_table.item(row, col)
                value = item.text() if item else ""
                if value not in selected_values:
                    visible = False
                    break
            self._notes_table.setRowHidden(row, not visible)

    def _refresh_note_header_filter_badges(self) -> None:
        """Hiển thị badge [F] trên các cột đang có filter active."""
        for col, base_label in enumerate(self._base_note_headers):
            item = self._notes_table.horizontalHeaderItem(col)
            if item is None:
                continue
            if col in self._active_note_filters:
                item.setText(f"{base_label} [F]")
            else:
                item.setText(base_label)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

