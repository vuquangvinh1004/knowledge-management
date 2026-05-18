"""Màn hình Thư viện nguồn — danh sách, lọc và quản lý tài liệu PDF.

Business logic KHÔNG được viết ở đây. Chỉ gọi service và phát tín hiệu.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.empty_state import EmptyStateWidget
from ui.widgets.source_detail_panel import SourceDetailPanel


class LibraryView(QWidget):
    """
    Thư viện danh sách tài liệu PDF với:
    - Ô tìm kiếm nhanh theo tiêu đề / tác giả
    - Nhập PDF mới (auto-trích metadata)
    - Single-click → hiển thị chi tiết bên phải
    - Double-click → mở trong workspace
    - Context menu: mở, chỉnh sửa, xóa mềm

    Signals:
        open_source_requested(int): Khi người dùng muốn mở source.
        open_reference_requested(int): Khi người dùng muốn mở PDF tham khảo trong Workspace.
        import_requested: Khi nhấn nút Nhập nguồn.
    """

    open_source_requested = Signal(int)
    open_reference_requested = Signal(int)
    import_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._sources: list = []
        self._project_id: int | None = None
        self._project_source_ids: set[int] | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        # Header + nút nhập (ngoài splitter)
        header_row = QWidget()
        header_lay = QHBoxLayout(header_row)
        header_lay.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Thư viện nguồn")
        header.setObjectName("view_header")
        header_lay.addWidget(header)
        header_lay.addStretch()

        self._btn_import = QPushButton("➕  Nhập nguồn PDF")
        self._btn_import.setObjectName("primary_button")
        self._btn_import.clicked.connect(self.import_requested)
        header_lay.addWidget(self._btn_import)
        layout.addWidget(header_row)

        # Tìm kiếm (ngoài splitter — áp dụng cho list bên trái)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍  Tìm theo tiêu đề hoặc tác giả...")
        self._search_edit.textChanged.connect(self._filter_list)
        layout.addWidget(self._search_edit)

        # --- Splitter: list (trái) | detail panel (phải) ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # --- Trái: danh sách + empty state ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._list_widget = QListWidget()
        self._list_widget.setObjectName("sources_list")
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list_widget.currentItemChanged.connect(self._on_selection_changed)
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        left_layout.addWidget(self._list_widget)

        self._empty_state = EmptyStateWidget(
            "Thư viện chưa có tài liệu nào.\nNhấn 'Nhập nguồn PDF' để bắt đầu.",
            action_label="Nhập nguồn PDF",
        )
        if self._empty_state.action_button:
            self._empty_state.action_button.clicked.connect(self.import_requested)
        left_layout.addWidget(self._empty_state)

        splitter.addWidget(left_widget)

        # --- Phải: source detail panel ---
        self._detail_panel = SourceDetailPanel()
        self._detail_panel.open_requested.connect(self.open_source_requested)
        self._detail_panel.open_reference_requested.connect(self.open_reference_requested)
        self._detail_panel.refresh_requested.connect(self._on_detail_refresh)
        splitter.addWidget(self._detail_panel)

        splitter.setSizes([480, 300])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, stretch=1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tải lại danh sách từ DB."""
        try:
            from core.services.source_service import SourceService
            self._sources = SourceService().list_all()

            if self._project_id is not None:
                self._project_source_ids = self._resolve_project_source_ids(self._project_id)
                self._sources = [s for s in self._sources if s.id in self._project_source_ids]
            else:
                self._project_source_ids = None
        except Exception:  # noqa: BLE001
            self._sources = []
        self._populate_list(self._sources)

    def set_project_context(self, project_id: int | None) -> None:
        """Bật/tắt Project mode cho Library view.

        Khi project_id != None: chỉ hiển thị sources liên quan đến notes của project.
        """
        self._project_id = project_id
        self.refresh()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _populate_list(self, sources: list) -> None:
        self._list_widget.clear()
        has = bool(sources)
        self._list_widget.setVisible(has)
        self._empty_state.setVisible(not has)

        for src in sources:
            parts = []
            if src.authors:
                parts.append(src.authors)
            if src.year:
                parts.append(src.year)
            suffix = " — " + ", ".join(parts) if parts else ""
            item = QListWidgetItem(
                f"[{src.source_code or src.id}] {src.title or '(Không có tiêu đề)'}{suffix}"
            )
            item.setData(Qt.ItemDataRole.UserRole, src.id)
            item.setToolTip(f"Source: {src.source_code or src.id}\n{src.file_path}")
            self._list_widget.addItem(item)

    def _filter_list(self, query: str) -> None:
        q = query.lower().strip()
        if not q:
            self._populate_list(self._sources)
            return
        filtered = [
            s for s in self._sources
            if q in (s.title or "").lower() or q in (s.authors or "").lower()
        ]
        self._populate_list(filtered)

    @staticmethod
    def _resolve_project_source_ids(project_id: int) -> set[int]:
        """Lấy source IDs liên quan tới notes của project (own + refs)."""
        from core.services.project_service import ProjectService
        from core.storage.models import Note
        from core.storage.session import get_session

        note_ids = ProjectService().get_project_note_ids(project_id)
        if not note_ids:
            return set()

        with get_session() as session:
            rows = (
                session.query(Note.source_id)
                .filter(
                    Note.id.in_(note_ids),
                    Note.source_id.is_not(None),
                    Note.is_deleted == 0,
                )
                .all()
            )
        return {int(row[0]) for row in rows if row and row[0] is not None}

    def _on_selection_changed(self, current: QListWidgetItem, _previous) -> None:
        """Cập nhật detail panel khi chọn item."""
        if current is None:
            self._detail_panel.clear()
            return
        source_id = current.data(Qt.ItemDataRole.UserRole)
        if source_id is not None:
            self._detail_panel.load_source(source_id)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        source_id = item.data(Qt.ItemDataRole.UserRole)
        if source_id is not None:
            self.open_source_requested.emit(source_id)

    def _on_detail_refresh(self) -> None:
        """Reload list sau khi metadata được cập nhật."""
        self.refresh()

    def _show_context_menu(self, pos) -> None:
        item = self._list_widget.itemAt(pos)
        if not item:
            return
        source_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        act_open = menu.addAction("📖  Ghi chú nguồn")
        act_open_reference = menu.addAction("📄  Mở tài liệu")
        act_edit = menu.addAction("✏  Chỉnh sửa thông tin")
        act_delete = menu.addAction("❌  Xóa khỏi thư viện")
        menu.addSeparator()
        

        chosen = menu.exec(self._list_widget.mapToGlobal(pos))
        if chosen == act_open:
            self.open_source_requested.emit(source_id)
        elif chosen == act_open_reference:
            self.open_reference_requested.emit(source_id)
        elif chosen == act_edit:
            self._detail_panel.load_source(source_id)
            self._detail_panel._on_edit()
        elif chosen == act_delete:
            self._delete_source(source_id, item.text())

    def _delete_source(self, source_id: int, title: str) -> None:
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Xóa tài liệu '{title}' khỏi thư viện?\n(Chỉ xóa mềm, file PDF không bị xóa.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.services.source_service import SourceService
                SourceService().soft_delete(source_id)
                self._detail_panel.clear()
                self.refresh()
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Lỗi", str(exc))

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

