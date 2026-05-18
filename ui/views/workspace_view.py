"""Màn hình Không gian làm việc — dual-pane PDF + Markdown.

Wrapper của DualPaneHost, hiển thị empty state khi chưa mở tài liệu.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget, QMessageBox

from ui.widgets.dual_pane_host import DualPaneHost
from ui.widgets.empty_state import EmptyStateWidget


class WorkspaceView(QWidget):
    """
    Container cho DualPaneHost.

    Signals:
        library_requested: Khi người dùng nhấn nút điều hướng sang Thư viện nguồn.
        source_opened(int): Relay từ DualPaneHost.
    """

    library_requested = Signal()
    source_opened = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._project_id: int | None = None
        self._project_source_ids: set[int] | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()

        # Trang 0: empty state
        self._empty_state = EmptyStateWidget(
            "Chưa có tài liệu nào được mở.\nVào Thư viện nguồn để chọn hoặc nhập PDF.",
            action_label="Vào Thư viện",
        )
        if self._empty_state.action_button is not None:
            self._empty_state.action_button.clicked.connect(self.library_requested.emit)
        self._stack.addWidget(self._empty_state)  # index 0

        # Trang 1: dual pane
        self._dual_pane = DualPaneHost()
        self._dual_pane.source_opened.connect(self.source_opened)
        self._dual_pane.all_tabs_closed.connect(lambda: self._stack.setCurrentIndex(0))
        self._stack.addWidget(self._dual_pane)  # index 1

        layout.addWidget(self._stack)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_source(self, source_id: int) -> None:
        """Mở source trong dual pane."""
        if self._project_id is not None:
            allowed_ids = self._project_source_ids or set()
            if source_id not in allowed_ids:
                QMessageBox.information(
                    self,
                    "Project mode",
                    "Tài liệu này không thuộc phạm vi project đang kích hoạt.",
                )
                return
        self._dual_pane.open_source(source_id)
        self._stack.setCurrentIndex(1)

    def close_source(self) -> None:
        """Trở về empty state."""
        self._dual_pane.close_source()
        self._stack.setCurrentIndex(0)

    def refresh_wikilink_catalog(self) -> None:
        """Làm mới danh sách note dùng cho wikilink ở editor đang mở."""
        self._dual_pane.refresh_wikilink_catalog()

    def apply_editor_preferences(self, font_family: str, font_ligatures: bool) -> None:
        """Áp dụng cấu hình font editor vào dual pane hiện tại."""
        self._dual_pane.apply_editor_preferences(font_family, font_ligatures)

    def set_project_context(self, project_id: int | None) -> None:
        """Bật/tắt Project mode cho Workspace view."""
        self._project_id = project_id
        self._project_source_ids = self._resolve_project_source_ids(project_id)

    @staticmethod
    def _resolve_project_source_ids(project_id: int | None) -> set[int] | None:
        if project_id is None:
            return None

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

