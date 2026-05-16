"""Màn hình Trang chính — tóm tắt và truy cập nhanh.

Business logic ĐOUTHỰỢC viết ở đây. Chỉ gọi service và phát tín hiệu.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
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

        # Stats bar
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
            (self._lbl_source_notes, "Source note"),
            (self._lbl_concept_notes, "Concept note"),
            (self._lbl_synthesis_notes, "Synthesis note"),
            (self._lbl_board_notes, "Board note"),
            (self._lbl_orphan_notes, "Other notes"),
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

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

