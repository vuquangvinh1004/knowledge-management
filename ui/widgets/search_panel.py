"""Panel tìm kiếm toàn văn — hiển thị kết quả notes và extracts.

Có thể mở như dialog hoặc dock widget.
Business logic KHÔNG nằm ở đây — gọi qua SearchService.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.utils.logger import get_logger

logger = get_logger()

_SEARCH_DELAY_MS = 300  # debounce


class SearchResultItem(QListWidgetItem):
    """Item trong danh sách kết quả tìm kiếm."""

    def __init__(
        self,
        entity_type: str,
        entity_id: int,
        title: str,
        snippet: str,
        source_id: int | None = None,
    ) -> None:
        super().__init__()
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.source_id = source_id

        type_label = "Ghi chú" if entity_type == "note" else "Trích xuất"
        display = f"[{type_label}] {title}"
        if snippet:
            display += f"\n  {snippet[:100]}"
        self.setText(display)
        self.setToolTip(f"{type_label} #{entity_id}\n{snippet}")


class SearchPanelDialog(QDialog):
    """
    Dialog tìm kiếm toàn văn.

    Signals:
        note_open_requested(int): Phát khi người dùng muốn mở note.
        source_open_requested(int): Phát khi người dùng muốn mở source.
    """

    note_open_requested = Signal(int)
    source_open_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm")
        self.setMinimumSize(520, 400)
        self._build_ui()
        self._setup_debounce()
        self._search_service = None

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Thanh tìm kiếm
        search_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Tìm kiếm ghi chú, trích xuất...")
        self._input.setClearButtonEnabled(True)
        self._input.textChanged.connect(self._on_input_changed)
        search_row.addWidget(self._input)

        # Filter entity type
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("Tất cả", None)
        self._filter_combo.addItem("Ghi chú", "note")
        self._filter_combo.addItem("Trích xuất", "extract")
        self._filter_combo.currentIndexChanged.connect(self._do_search)
        search_row.addWidget(self._filter_combo)
        layout.addLayout(search_row)

        # Kết quả
        self._result_list = QListWidget()
        self._result_list.setAlternatingRowColors(True)
        self._result_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._result_list)

        # Status
        status_row = QHBoxLayout()
        self._lbl_status = QLabel("Nhập từ khóa để bắt đầu tìm kiếm.")
        self._lbl_status.setObjectName("search_status")
        status_row.addWidget(self._lbl_status)
        status_row.addStretch()

        btn_open = QPushButton("Mở")
        btn_open.clicked.connect(self._on_open_clicked)
        status_row.addWidget(btn_open)
        layout.addLayout(status_row)

    def _setup_debounce(self) -> None:
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(_SEARCH_DELAY_MS)
        self._debounce_timer.timeout.connect(self._do_search)

    # ------------------------------------------------------------------
    # Lazy service init
    # ------------------------------------------------------------------

    def _get_service(self):
        if self._search_service is None:
            try:
                from config.paths import DATABASE_FILE, NOTES_DIR
                from core.services.search_service import SearchService
                self._search_service = SearchService(str(DATABASE_FILE), NOTES_DIR)
            except Exception as exc:
                logger.error(f"Không thể khởi tạo SearchService: {exc}")
        return self._search_service

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_input_changed(self) -> None:
        self._debounce_timer.start()

    def _do_search(self) -> None:
        query = self._input.text().strip()
        if not query:
            self._result_list.clear()
            self._lbl_status.setText("Nhập từ khóa để bắt đầu tìm kiếm.")
            return

        svc = self._get_service()
        if svc is None:
            self._lbl_status.setText("Dịch vụ tìm kiếm chưa sẵn sàng.")
            return

        entity_type = self._filter_combo.currentData()
        try:
            from core.services.project_service import ProjectService
            project_note_ids = None
            active_project_id = ProjectService().get_active_project_id()
            if active_project_id is not None:
                project_note_ids = ProjectService().get_project_note_ids(active_project_id)

            results = svc.search(
                query,
                entity_type=entity_type,
                limit=50,
                project_note_ids=project_note_ids,
            )
        except Exception as exc:
            logger.warning(f"Lỗi tìm kiếm: {exc}")
            self._lbl_status.setText("Lỗi khi tìm kiếm.")
            return

        self._result_list.clear()
        for r in results:
            item = SearchResultItem(
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                title=r.title,
                snippet=r.snippet,
                source_id=r.source_id,
            )
            self._result_list.addItem(item)

        count = len(results)
        self._lbl_status.setText(
            f"Tìm thấy {count} kết quả." if count else "Không tìm thấy kết quả nào."
        )

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        if isinstance(item, SearchResultItem):
            if item.entity_type == "note":
                self.note_open_requested.emit(item.entity_id)
            elif item.entity_type == "extract" and item.source_id:
                self.source_open_requested.emit(item.source_id)

    def _on_open_clicked(self) -> None:
        item = self._result_list.currentItem()
        if item:
            self._on_item_double_clicked(item)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def focus_search(self) -> None:
        """Đặt focus vào ô tìm kiếm."""
        self._input.setFocus()
        self._input.selectAll()
