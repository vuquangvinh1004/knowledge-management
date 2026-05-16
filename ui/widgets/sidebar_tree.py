"""Thanh điều hướng chính (sidebar) với 5 mục cố định.

Không chứa business logic — chỉ phát signal điều hướng.
"""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
)

from core.utils.constants import SIDEBAR_DEFAULT_WIDTH
from core.services.project_service import ProjectService


class NavButton(QPushButton):
    """Nút điều hướng trong sidebar."""

    def __init__(self, label: str, parent=None) -> None:
        super().__init__(label, parent)
        self.setObjectName("sidebar_nav_button")
        self.setCheckable(True)
        self.setFlat(True)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SidebarWidget(QWidget):
    """
    Sidebar điều hướng.
    Phát signal navigation_requested(index) khi người dùng bấm mục.
    """

    navigation_requested = Signal(int)
    project_activate_requested = Signal(object)  # int project_id | None
    project_manager_requested = Signal()

    _NAV_ITEMS = [
        "Trang chính",
        "Thư viện nguồn",
        "Không gian làm việc",
        "Quản lý ghi chú",
        "Bảng nghiên cứu",
        "Thiết lập",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar_widget")
        self.setFixedWidth(SIDEBAR_DEFAULT_WIDTH)
        self._buttons: list[NavButton] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation buttons
        for i, label in enumerate(self._NAV_ITEMS):
            btn = NavButton(label)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_clicked(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)

        self._project_header = QLabel("Project")
        self._project_header.setObjectName("sidebar_section_header")
        self._project_header.setContentsMargins(10, 12, 10, 4)
        layout.addWidget(self._project_header)

        self._project_list = QListWidget()
        self._project_list.setObjectName("sidebar_project_list")
        self._project_list.setMaximumHeight(160)
        self._project_list.itemDoubleClicked.connect(self._on_project_item_double_clicked)
        layout.addWidget(self._project_list)

        project_actions = QWidget()
        pa_lay = QHBoxLayout(project_actions)
        pa_lay.setContentsMargins(8, 4, 8, 4)
        pa_lay.setSpacing(6)

        self._btn_global_mode = QPushButton("Global")
        self._btn_global_mode.setObjectName("sidebar_project_global_btn")
        self._btn_global_mode.setFixedHeight(28)
        self._btn_global_mode.clicked.connect(lambda: self.project_activate_requested.emit(None))
        pa_lay.addWidget(self._btn_global_mode)

        self._btn_manage_projects = QPushButton("Quản lý")
        self._btn_manage_projects.setObjectName("sidebar_project_manage_btn")
        self._btn_manage_projects.setFixedHeight(28)
        self._btn_manage_projects.clicked.connect(self.project_manager_requested)
        pa_lay.addWidget(self._btn_manage_projects)

        layout.addWidget(project_actions)

        layout.addStretch()

        self.refresh_projects()

    def _on_nav_clicked(self, index: int) -> None:
        self.set_active(index)
        self.navigation_requested.emit(index)

    def set_active(self, index: int) -> None:
        """Dánh dấu mục đang active."""
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)

    def refresh_projects(self) -> None:
        """Tải danh sách dự án để hiển thị trong sidebar."""
        self._project_list.clear()
        active_project_id = ProjectService().get_active_project_id()
        try:
            projects = ProjectService().list_projects(include_closed=True)
        except Exception:
            projects = []

        for p in projects:
            status = "(đã kết thúc)" if p.status == "closed" else ""
            marker = "●" if p.id == active_project_id else "○"
            item = QListWidgetItem(f"{marker} {p.name} {status}".strip())
            item.setData(Qt.ItemDataRole.UserRole, int(p.id))
            self._project_list.addItem(item)

        if not projects:
            item = QListWidgetItem("(Chưa có project)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._project_list.addItem(item)

    def _on_project_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        self.project_activate_requested.emit(int(data))
