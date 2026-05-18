"""Container Quản lý ghi chú mới với các sub-tab theo workflow."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QTabBar, QTabWidget, QVBoxLayout, QWidget

from ui.views.workspace_view import WorkspaceView
from ui.widgets.note_list_editor_tab import NoteListEditorTab


class NoteScopeTabBar(QTabBar):
    """Tab bar tô màu cố định theo scope note để dễ nhận diện."""

    _TAB_COLORS = (
        QColor("#C62828"),  # GC Nguồn
        QColor("#2E7D32"),  # GC Khái niệm
        QColor("#1565C0"),  # GC Tổng hợp
        QColor("#7E57C2"),  # GC Board
    )

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for idx in range(self.count()):
            rect = self.tabRect(idx).adjusted(1, 1, -1, -1)
            base_color = self._TAB_COLORS[idx] if idx < len(self._TAB_COLORS) else QColor("#5A6076")
            fill_color = base_color if idx == self.currentIndex() else base_color.darker(120)

            painter.setPen(QPen(base_color.darker(130), 1))
            painter.setBrush(fill_color)
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.tabText(idx))


class NoteManagementShellView(QWidget):
    """Quản lý ghi chú với các sub-tab GC/GH theo loại note."""

    note_open_requested = Signal(int)
    note_deleted = Signal()
    note_created = Signal(int)
    library_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setTabBar(NoteScopeTabBar())
        self._tabs.setObjectName("note_scope_tabs")
        self._tabs.setStyleSheet(
            "QTabWidget#note_scope_tabs::pane { border: 0; }"
            "QTabWidget#note_scope_tabs QTabBar::tab {"
            " min-height: 36px;"
            " min-width: 130px;"
            " margin-right: 2px;"
            "}"
        )

        self._source_workspace = WorkspaceView()
        self._concept_tab = NoteListEditorTab("concept_note")
        self._synthesis_tab = NoteListEditorTab("synthesis_note")
        self._board_tab = NoteListEditorTab("board_note")

        self._tabs.addTab(self._source_workspace, "GC Nguồn")
        self._tabs.addTab(self._concept_tab, "GC Khái niệm")
        self._tabs.addTab(self._synthesis_tab, "GC Tổng hợp")
        self._tabs.addTab(self._board_tab, "GC Board")

        self._source_workspace.library_requested.connect(self.library_requested.emit)
        self._concept_tab.note_deleted.connect(self.note_deleted)
        self._synthesis_tab.note_deleted.connect(self.note_deleted)
        self._board_tab.note_deleted.connect(self.note_deleted)

        layout.addWidget(self._tabs, stretch=1)

    def open_source(self, source_id: int) -> None:
        """Mở source trong tab GC Nguồn."""
        self._tabs.setCurrentIndex(0)
        self._source_workspace.open_source(source_id)

    def refresh(self) -> None:
        """Làm mới các tab note."""
        self._source_workspace.refresh()
        self._concept_tab.refresh()
        self._synthesis_tab.refresh()
        self._board_tab.refresh()

    def set_project_context(self, project_id: int | None) -> None:
        """Đồng bộ project mode cho các tab liên quan."""
        self._source_workspace.set_project_context(project_id)
        self._concept_tab.set_project_context(project_id)
        self._synthesis_tab.set_project_context(project_id)
        self._board_tab.set_project_context(project_id)
