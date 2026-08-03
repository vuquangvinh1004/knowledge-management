"""Main window của ứng dụng PKM.

Bố cục: sidebar | central stacked widget, toolbar trên, status bar dưới.
Business logic KHÔNG được viết ở đây — chỉ layout và điều hướng.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)

from config.settings import get_settings
from core.utils.constants import APP_NAME, APP_VERSION
from core.utils.logger import get_logger
from ui.handlers import main_window_handlers as mwh
from ui.widgets.sidebar_tree import SidebarWidget
from ui.widgets.status_strip import StatusStrip
from ui.widgets.warning_banner import WarningBanner
from ui.views.dashboard_view import DashboardView
from ui.views.library_view import LibraryView
from ui.views.draft_workspace_view import DraftWorkspaceView
from ui.views.note_management_shell_view import NoteManagementShellView
from ui.views.board_view import BoardView
from ui.views.settings_view import SettingsView
from core.services.project_service import ProjectService

# Index tương ứng với các mục sidebar
NAV_DASHBOARD = 0
NAV_LIBRARY = 1
NAV_WORKSPACE = 2
NAV_NOTES = 3
NAV_BOARD = 4
NAV_SETTINGS = 5

logger = get_logger()


class MainWindow(QMainWindow):
    """Cửa sổ chính ứng dụng PKM."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = get_settings()
        self._project_service = ProjectService()
        self._setup_window()
        self._build_central()
        self._build_status_bar()
        self._connect_signals()
        self._apply_project_context(self._project_service.get_active_project_id())
        self._restore_geometry()
        # Mở trang chính mặc định
        self._navigate_to(NAV_DASHBOARD)

    def show_soft_dep_warnings(self, missing: list[str]) -> None:
        """Hiển thị warning banner nếu có soft dependency bị thiếu."""
        if missing:
            self._warning_banner.show_warnings(
                [f"Thiếu thư viện: {m}" for m in missing]
            )

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}")
        self.setMinimumSize(900, 600)

    def _build_central(self) -> None:
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Warning banner (ẩn theo mặc định)
        self._warning_banner = WarningBanner()
        central_layout.addWidget(self._warning_banner)

        # Sidebar + stack
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = SidebarWidget()
        self._sidebar.set_collapsed(
            bool(self._settings.get("sidebar_collapsed", True)),
            emit_signal=False,
            animate=False,
        )
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._dashboard_view = DashboardView()
        self._library_view = LibraryView()
        self._workspace_view = DraftWorkspaceView()
        self._note_management_view = NoteManagementShellView()
        self._board_view = BoardView()
        self._settings_view = SettingsView()

        self._stack.addWidget(self._dashboard_view)   # 0
        self._stack.addWidget(self._library_view)     # 1
        self._stack.addWidget(self._workspace_view)   # 2
        self._stack.addWidget(self._note_management_view)  # 3
        self._stack.addWidget(self._board_view)       # 4
        self._stack.addWidget(self._settings_view)    # 5

        layout.addWidget(self._stack)
        central_layout.addWidget(content, stretch=1)
        self.setCentralWidget(central)

    def _build_status_bar(self) -> None:
        self._status_strip = StatusStrip()
        self.setStatusBar(self._status_strip)

    def _connect_signals(self) -> None:
        self._sidebar.navigation_requested.connect(self._navigate_to)
        self._sidebar.collapsed_changed.connect(self._on_sidebar_collapsed_changed)
        self._sidebar.project_activate_requested.connect(self._on_sidebar_project_activate_requested)
        self._sidebar.project_manager_requested.connect(self._open_project_manager_dialog)

        # Dashboard
        self._dashboard_view.open_source_requested.connect(self._open_reference_in_workspace)
        self._dashboard_view.import_requested.connect(self._open_import_dialog)
        self._dashboard_view.note_catalog_changed.connect(self._on_note_catalog_changed)

        # Library
        self._library_view.open_reference_requested.connect(self._open_reference_in_workspace)
        self._library_view.create_source_note_requested.connect(self._create_source_note_from_library)
        self._library_view.import_requested.connect(self._open_import_dialog)

        # Board / Graph view relay
        self._board_view.note_open_requested.connect(self._open_note_in_workspace)
        self._board_view.source_open_requested.connect(self._open_source_in_workspace)
        self._board_view.sync_requested.connect(self._sync_board_with_source_notes)
        self._board_view.export_markdown_requested.connect(self._export_board_markdown)
        self._board_view.export_csv_requested.connect(self._export_board_csv)
        self._board_view.customize_requested.connect(self._open_board_criteria_manager)
        self._board_view.graph_view_requested.connect(self._open_board_graph_view)
        self._board_view.cell_edit_requested.connect(self._edit_board_cell)

        # Note management actions
        self._note_management_view.note_open_requested.connect(self._open_note_in_workspace)
        self._note_management_view.note_deleted.connect(self._on_note_catalog_changed)
        self._note_management_view.note_created.connect(self._open_note_in_workspace)
        self._note_management_view.note_renamed.connect(self._on_note_catalog_changed)
        self._note_management_view.library_requested.connect(lambda: self._navigate_to(NAV_LIBRARY))
        self._note_management_view.create_note_requested.connect(self._start_create_source_note_flow)

        # Workspace empty state action
        if hasattr(self._workspace_view, "_empty_state"):
            empty_state = getattr(self._workspace_view, "_empty_state", None)
            if empty_state and empty_state.action_button:
                empty_state.action_button.clicked.connect(lambda: self._navigate_to(NAV_LIBRARY))

        # Draft workspace relay
        self._workspace_view.import_requested.connect(self._open_import_dialog)
        self._workspace_view.text_extract_requested.connect(self._extract_text_from_workspace)
        self._workspace_view.table_extract_requested.connect(self._extract_table_from_workspace)
        self._workspace_view.image_extract_requested.connect(self._capture_image_from_workspace)
        self._workspace_view.source_page_changed_requested.connect(self._update_last_opened_page_from_workspace)

        # Settings maintenance actions
        self._settings_view.backup_requested.connect(self._do_backup_from_settings)
        self._settings_view.rebuild_fts_requested.connect(self._rebuild_fts_from_settings)
        self._settings_view.reset_settings_requested.connect(self._reset_settings_from_settings)
        self._settings_view.normalize_source_titles_requested.connect(self._normalize_source_titles_from_settings)
        self._settings_view.refresh_wikilink_catalog_requested.connect(self._refresh_wikilink_catalog_from_settings)
        self._settings_view.cleanup_unused_notes_requested.connect(self._cleanup_unused_notes_from_settings)
        self._settings_view.audit_missing_source_note_files_requested.connect(self._audit_missing_source_note_files_from_settings)
        self._settings_view.source_titles_normalized.connect(self._on_note_catalog_changed)
        self._settings_view.wikilink_catalog_refreshed.connect(self._on_note_catalog_changed)
        self._settings_view.editor_preferences_changed.connect(self._on_editor_preferences_changed)

    def _on_sidebar_project_activate_requested(self, project_id: object) -> None:
        """Kích hoạt project từ sidebar, hoặc về Global mode nếu project_id=None."""
        mwh.activate_project_from_sidebar(self, project_id)

    def _on_sidebar_collapsed_changed(self, collapsed: bool) -> None:
        """Lưu preference thu gọn sidebar ngay khi người dùng đổi trạng thái."""
        self._settings.set("sidebar_collapsed", bool(collapsed))
        self._settings.save()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate_to(self, index: int) -> None:
        """Chuyển màn hình theo index điều hướng."""
        self._stack.setCurrentIndex(index)
        self._sidebar.set_active(index)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _open_import_dialog(self) -> None:
        """Mở dialog nhập PDF mới."""
        mwh.open_import_dialog(self)

    def _start_create_source_note_flow(self) -> None:
        """Bắt đầu workflow tạo source_note từ GC Nguồn."""
        mwh.start_create_source_note_flow(self, NAV_LIBRARY)

    def _create_source_note_from_library(self, source_id: int) -> None:
        """Tạo source_note tường minh cho source được chọn trong Library."""
        mwh.create_source_note_from_library(self, source_id)

    def _open_source_in_workspace(self, source_id: int) -> None:
        """Mở source trong tab GC Nguồn và chuyển sang tab Quản lý ghi chú."""
        mwh.open_source_in_workspace(self, source_id, NAV_NOTES)

    def _open_reference_in_workspace(self, source_id: int) -> None:
        """Mở PDF tham khảo trong tab Không gian làm việc."""
        mwh.open_source_in_draft_workspace(self, source_id, NAV_WORKSPACE)

    def _save_current_note(self) -> None:
        """Lưu ghi chú đang mở trong workspace (nếu có)."""
        mwh.save_current_note(self)

    def _do_backup(self) -> None:
        """Tạo backup DB."""
        mwh.do_backup(self)

    def _do_backup_from_settings(self, keep_count: int) -> None:
        """Tạo backup từ tab Thiết lập."""
        mwh.do_backup_from_settings(self, keep_count)

    def _rebuild_fts_from_settings(self) -> None:
        """Rebuild FTS index từ tab Thiết lập."""
        mwh.rebuild_fts_index(self)

    def _reset_settings_from_settings(self) -> None:
        """Khôi phục cài đặt mặc định từ tab Thiết lập."""
        mwh.reset_settings(self)

    def _normalize_source_titles_from_settings(self) -> None:
        """Chuẩn hóa source-note titles từ tab Thiết lập."""
        mwh.normalize_source_note_titles(self)

    def _refresh_wikilink_catalog_from_settings(self) -> None:
        """Làm mới wikilink catalog từ tab Thiết lập."""
        mwh.refresh_wikilink_catalog(self)

    def _cleanup_unused_notes_from_settings(self) -> None:
        """Dọn note không còn dùng từ tab Thiết lập."""
        mwh.cleanup_unused_notes_with_preview(self)

    def _audit_missing_source_note_files_from_settings(self) -> None:
        """Quét source-note thiếu file markdown từ tab Thiết lập."""
        mwh.audit_missing_source_note_files(self)

    def _open_search_dialog(self) -> None:
        """Mở dialog tìm kiếm toàn văn."""
        mwh.open_search_dialog(self)

    def _open_project_manager_dialog(self) -> None:
        """Mở dialog quản lý project."""
        mwh.open_project_manager_dialog(self)

    def _on_project_context_changed(self) -> None:
        """Refresh context khi project mode thay đổi."""
        mwh.on_project_context_changed(self)

    def _apply_project_context(self, project_id: int | None) -> None:
        """Áp dụng project scope vào UI (indicator + sidebar + views)."""
        mwh.apply_project_context(self, project_id)

    def _update_mode_indicator(self, project_id: int | None) -> None:
        mwh.update_mode_indicator(self, project_id, logger)

    def _open_note_in_workspace(self, note_id: int) -> None:
        """Mở note theo id.

        - Nếu note có source_id: mở trong Workspace như cũ.
        - Nếu note không có source_id (vd board_note): mở bằng dialog editor standalone.
        """
        mwh.open_note_in_workspace(self, note_id, logger)

    def _open_standalone_note_dialog(self, note_id: int) -> None:
        """Mở note không gắn source trong dialog editor."""
        mwh.open_standalone_note_dialog(self, note_id)

    def _open_export_dialog(self) -> None:
        """Xuất source bundle cho source đang mở (nếu có)."""
        mwh.open_export_dialog(self)

    def _extract_text_from_workspace(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Trích văn bản từ vùng chọn trong Workspace."""
        mwh.extract_text_from_workspace(self, source_id, page_no, pdf_rect)

    def _extract_table_from_workspace(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Trích bảng từ vùng chọn trong Workspace."""
        mwh.extract_table_from_workspace(self, source_id, page_no, pdf_rect)

    def _capture_image_from_workspace(self, source_id: int, page_no: int, pdf_rect: tuple) -> None:
        """Chụp ảnh từ vùng chọn trong Workspace."""
        mwh.capture_image_from_workspace(self, source_id, page_no, pdf_rect)

    def _update_last_opened_page_from_workspace(self, source_id: int, page_no: int) -> None:
        """Lưu trang PDF đang mở từ Workspace."""
        mwh.update_last_opened_page_from_workspace(self, source_id, page_no)

    def _sync_board_with_source_notes(self) -> None:
        """Đồng bộ board hiện tại theo source_note."""
        mwh.sync_board_with_source_notes(self)

    def _edit_board_cell(self, row_id: int, col_id: int) -> None:
        """Sửa một ô trong board hiện tại."""
        mwh.edit_board_cell(self, row_id, col_id)

    def _export_board_markdown(self) -> None:
        """Xuất board hiện tại ra Markdown."""
        mwh.export_board_markdown(self)

    def _export_board_csv(self) -> None:
        """Xuất board hiện tại ra CSV."""
        mwh.export_board_csv(self)

    def _open_board_graph_view(self) -> None:
        """Mở đồ thị liên kết của board."""
        mwh.open_board_graph_view(self)

    def _open_board_criteria_manager(self) -> None:
        """Mở dialog tùy chỉnh tiêu chí board."""
        mwh.open_board_criteria_manager(self)

    def _on_note_catalog_changed(self) -> None:
        """Khi catalog note thay đổi từ Settings: refresh các view liên quan."""
        mwh.on_note_catalog_changed(self, logger)

    def _on_editor_preferences_changed(self, font_family: str, font_ligatures: bool, font_size: int) -> None:
        """Áp dụng ngay cài đặt font editor cho workspace hiện tại."""
        mwh.on_editor_preferences_changed(self, font_family, font_ligatures, font_size, logger)

    # ------------------------------------------------------------------
    # Geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        w = self._settings.get("window_width", 1280)
        h = self._settings.get("window_height", 800)
        self.resize(w, h)
        if self._settings.get("window_maximized", False):
            self.showMaximized()

    def closeEvent(self, event) -> None:  # noqa: N802
        """Lưu geometry khi đóng cửa sổ."""
        if hasattr(self._workspace_view, "confirm_close_with_unsaved_changes"):
            if not self._workspace_view.confirm_close_with_unsaved_changes():
                event.ignore()
                return
        if not self.isMaximized():
            self._settings.set("window_width", self.width())
            self._settings.set("window_height", self.height())
        self._settings.set("sidebar_collapsed", self._sidebar.is_collapsed())
        self._settings.set("window_maximized", self.isMaximized())
        self._settings.save()
        super().closeEvent(event)

