"""Thanh điều hướng chính (sidebar) với 5 mục cố định.

Không chứa business logic — chỉ phát signal điều hướng.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt, QSize, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QStyle,
)

from core.utils.constants import SIDEBAR_DEFAULT_WIDTH, SIDEBAR_COLLAPSED_WIDTH
from core.services.project_service import ProjectService


class NavButton(QPushButton):
    """Nút điều hướng trong sidebar."""

    def __init__(self, label: str, icon, parent=None) -> None:
        super().__init__(label, parent)
        self.setObjectName("sidebar_nav_button")
        self.setCheckable(True)
        self.setFlat(True)
        self.setFixedHeight(44)
        self.setIcon(icon)
        self.setIconSize(QSize(18, 18))
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
    collapsed_changed = Signal(bool)

    _NAV_ITEMS = [
        "Trang chính",
        "Thư viện nguồn",
        "Không gian làm việc",
        "Quản lý ghi chú",
        "Bảng nghiên cứu",
        "Thiết lập",
    ]
    _NAV_ICONS = [
        QStyle.StandardPixmap.SP_DesktopIcon,
        QStyle.StandardPixmap.SP_DirIcon,
        QStyle.StandardPixmap.SP_FileDialogDetailedView,
        QStyle.StandardPixmap.SP_FileIcon,
        QStyle.StandardPixmap.SP_DirOpenIcon,
        QStyle.StandardPixmap.SP_FileDialogContentsView,
    ]
    _NAV_ICON_FILES = [
        "nav_dashboard.svg",
        "nav_library.svg",
        "nav_workspace.svg",
        "nav_notes.svg",
        "nav_board.svg",
        "nav_settings.svg",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar_widget")
        self.setProperty("collapsed", False)
        self._project_root = Path(__file__).resolve().parents[2]
        self._sidebar_width = SIDEBAR_DEFAULT_WIDTH
        self._active_index = 0
        self._is_collapsed = False
        self._buttons: list[NavButton] = []
        self._width_animation = QPropertyAnimation(self, b"sidebarWidth", self)
        self._width_animation.setDuration(140)
        self._width_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._set_sidebar_width(SIDEBAR_DEFAULT_WIDTH)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Navigation buttons
        for i, label in enumerate(self._NAV_ITEMS):
            icon = self._load_nav_icon(i)
            btn = NavButton(label, icon)
            btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_clicked(idx))
            btn.setToolTip(label)
            self._buttons.append(btn)
            layout.addWidget(btn)

        self._project_header = QLabel("Dự án")
        self._project_header.setObjectName("sidebar_section_header")
        self._project_header.setContentsMargins(10, 12, 10, 4)
        layout.addWidget(self._project_header)

        self._project_list = QListWidget()
        self._project_list.setObjectName("sidebar_project_list")
        self._project_list.setMaximumHeight(160)
        self._project_list.itemDoubleClicked.connect(self._on_project_item_double_clicked)
        layout.addWidget(self._project_list)

        self._project_actions = QWidget()
        pa_lay = QHBoxLayout(self._project_actions)
        pa_lay.setContentsMargins(8, 4, 8, 4)
        pa_lay.setSpacing(6)

        self._btn_global_mode = QPushButton("Toàn cục")
        self._btn_global_mode.setObjectName("sidebar_project_global_btn")
        self._btn_global_mode.setFixedHeight(28)
        self._btn_global_mode.clicked.connect(lambda: self.project_activate_requested.emit(None))
        pa_lay.addWidget(self._btn_global_mode)

        self._btn_manage_projects = QPushButton("Quản lý")
        self._btn_manage_projects.setObjectName("sidebar_project_manage_btn")
        self._btn_manage_projects.setFixedHeight(28)
        self._btn_manage_projects.clicked.connect(self.project_manager_requested)
        pa_lay.addWidget(self._btn_manage_projects)

        layout.addWidget(self._project_actions)

        layout.addStretch()

        self.refresh_projects()

    def _on_nav_clicked(self, index: int) -> None:
        if self._is_collapsed:
            self.set_active(index)
            self.navigation_requested.emit(index)
            self.set_collapsed(False)
            return

        if index == self._active_index:
            self.set_collapsed(True)
            return

        self.set_active(index)
        self.navigation_requested.emit(index)

    def _load_nav_icon(self, index: int) -> QIcon:
        """Ưu tiên icon custom trong assets; fallback về icon chuẩn Qt."""
        icon_path = self._project_root / "assets" / "icons" / self._NAV_ICON_FILES[index]
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon

        app_style = QApplication.style()
        return app_style.standardIcon(self._NAV_ICONS[index])

    def set_active(self, index: int) -> None:
        """Đánh dấu mục đang active."""
        self._active_index = index
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)

    def _get_sidebar_width(self) -> int:
        return self._sidebar_width

    def _set_sidebar_width(self, width: int) -> None:
        width = int(max(SIDEBAR_COLLAPSED_WIDTH, min(SIDEBAR_DEFAULT_WIDTH, width)))
        self._sidebar_width = width
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

    sidebarWidth = Property(int, _get_sidebar_width, _set_sidebar_width)

    def _animate_to_width(self, target_width: int) -> None:
        self._width_animation.stop()
        self._width_animation.setStartValue(self._sidebar_width)
        self._width_animation.setEndValue(target_width)
        self._width_animation.start()

    def is_collapsed(self) -> bool:
        return self._is_collapsed

    def set_collapsed(self, collapsed: bool, emit_signal: bool = True, animate: bool = True) -> None:
        """Chuyển trạng thái sidebar giữa icon-only và đầy đủ."""
        collapsed = bool(collapsed)
        if self._is_collapsed == collapsed:
            return

        self._is_collapsed = collapsed
        self.setProperty("collapsed", collapsed)

        for i, btn in enumerate(self._buttons):
            btn.setText("" if collapsed else self._NAV_ITEMS[i])

        show_project_panel = not collapsed
        self._project_header.setVisible(show_project_panel)
        self._project_list.setVisible(show_project_panel)
        self._project_actions.setVisible(show_project_panel)

        target_width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_DEFAULT_WIDTH
        if animate:
            self._animate_to_width(target_width)
        else:
            self._set_sidebar_width(target_width)

        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
            self.update()

        if emit_signal:
            self.collapsed_changed.emit(collapsed)

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
            item = QListWidgetItem("(Chưa có dự án)")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._project_list.addItem(item)

    def _on_project_item_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        self.project_activate_requested.emit(int(data))
