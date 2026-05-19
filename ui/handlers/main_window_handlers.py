"""Orchestration handlers cho MainWindow.

Module này gom các luồng điều phối để giảm độ phình của main_window.py
và giữ class MainWindow tập trung vào layout/signal wiring.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QMessageBox, QVBoxLayout


def open_import_dialog(window: Any) -> None:
    """Mở dialog nhập PDF mới và chỉ cập nhật thư viện sau khi import thành công."""
    from ui.widgets.dialogs.import_source_dialog import ImportSourceDialog

    dlg = ImportSourceDialog(window)
    if dlg.exec() and dlg.imported_source_id is not None:
        window._library_view.refresh()
        window._dashboard_view.refresh()
        window._navigate_to(1)


def start_create_source_note_flow(window: Any, library_index: int) -> None:
    """Điều hướng sang Library ở chế độ chọn tài liệu để tạo source_note."""
    window._navigate_to(library_index)
    window._library_view.start_source_note_creation_mode()


def create_source_note_from_library(window: Any, source_id: int) -> None:
    """Tạo source_note tường minh cho source được chọn trong Library."""
    from config.paths import ASSETS_DIR, NOTES_DIR
    from core.services.note_service import NoteService
    from core.services.workspace_orchestrator import WorkspaceOrchestrator

    note_svc = NoteService(NOTES_DIR)
    existing = note_svc.get_source_note(source_id)
    if existing is not None:
        QMessageBox.information(
            window,
            "Đã tồn tại source_note",
            "Tài liệu này đã có source_note, không thể tạo mới trùng lặp.",
        )
        window._library_view.end_source_note_creation_mode()
        window._open_source_in_workspace(source_id)
        return

    try:
        WorkspaceOrchestrator(notes_dir=NOTES_DIR, assets_dir=ASSETS_DIR).ensure_source_note(source_id)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể tạo source_note:\n{exc}")
        return

    window._library_view.end_source_note_creation_mode()
    window._library_view.refresh()
    window._dashboard_view.refresh()
    window._on_note_catalog_changed()
    window._open_source_in_workspace(source_id)


def open_source_in_workspace(window: Any, source_id: int, workspace_index: int) -> None:
    """Mở source trong tab GC Nguồn của Quản lý ghi chú."""
    window._note_management_view.open_source(source_id)
    window._navigate_to(workspace_index)


def open_source_in_draft_workspace(window: Any, source_id: int, workspace_index: int) -> None:
    """Mở source PDF vào Workspace tham khảo (không gắn note)."""
    window._workspace_view.open_reference_source(source_id)
    window._navigate_to(workspace_index)


def save_current_note(window: Any) -> None:
    """Lưu note hiện tại nếu đang có note mở."""
    workspace = getattr(window, "_workspace_view", None)
    if workspace is None:
        return

    # Workspace nháp mới: lưu file markdown tạm.
    if hasattr(workspace, "request_save_scratch_file"):
        workspace.request_save_scratch_file()
        return

    # Backward compatibility cho workspace cũ.
    dual = getattr(workspace, "_dual_pane", None)
    if dual is not None and getattr(dual, "_note_id", None) is not None:
        dual._md_editor._do_save()


def do_backup(window: Any) -> None:
    """Tạo backup DB và báo kết quả cho người dùng."""
    from config.paths import BACKUPS_DIR, DATABASE_FILE
    from core.services.backup_service import BackupService

    try:
        svc = BackupService(DATABASE_FILE, BACKUPS_DIR)
        entry = svc.create_backup()
        QMessageBox.information(window, "Sao lưu thành công", f"Đã tạo backup:\n{entry.path}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi sao lưu", str(exc))


def open_search_dialog(window: Any) -> None:
    """Mở dialog tìm kiếm và relay open actions về MainWindow."""
    from ui.widgets.search_panel import SearchPanelDialog

    dlg = SearchPanelDialog(window)
    dlg.note_open_requested.connect(window._open_note_in_workspace)
    dlg.source_open_requested.connect(window._open_source_in_workspace)
    dlg.focus_search()
    dlg.exec()


def open_project_manager_dialog(window: Any) -> None:
    """Mở dialog quản lý project và đồng bộ context sau khi đóng."""
    from config.paths import NOTES_DIR
    from ui.widgets.dialogs.project_manager_dialog import ProjectManagerDialog

    dlg = ProjectManagerDialog(window, notes_dir=NOTES_DIR)
    dlg.project_context_changed.connect(window._on_project_context_changed)
    dlg.exec()
    window._on_project_context_changed()


def on_project_context_changed(window: Any) -> None:
    """Refresh context khi project mode thay đổi."""
    active_project_id = window._project_service.get_active_project_id()
    window._apply_project_context(active_project_id)


def apply_project_context(window: Any, project_id: int | None) -> None:
    """Áp dụng project scope vào các view liên quan."""
    window._update_mode_indicator(project_id)
    window._sidebar.refresh_projects()
    window._library_view.set_project_context(project_id)
    window._workspace_view.set_project_context(project_id)
    window._note_management_view.set_project_context(project_id)
    window._board_view.set_project_context(project_id)
    window._dashboard_view.refresh()


def update_mode_indicator(window: Any, project_id: int | None, logger: Any) -> None:
    """Cập nhật badge mode Global/Project trong Settings view."""
    mode_text = "Mode: Global"
    if project_id is None:
        window._settings_view.set_mode_text(mode_text)
        return
    try:
        p = window._project_service.get_project(project_id)
        mode_text = f"Mode: Project - {p.name}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không thể đọc thông tin project_id={} để hiển thị mode: {}", project_id, exc)
        mode_text = "Mode: Global"
    window._settings_view.set_mode_text(mode_text)


def open_note_in_workspace(window: Any, note_id: int, logger: Any) -> None:
    """Mở note theo id, hỗ trợ cả note có source và note standalone."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    try:
        note = NoteService(NOTES_DIR).get_by_id(note_id)
        source_id = getattr(note, "source_id", None)
        if isinstance(source_id, int):
            window._open_source_in_workspace(source_id)
            return
        window._open_standalone_note_dialog(note_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Không thể mở note_id={} trong workspace: {}", note_id, exc)


def open_standalone_note_dialog(window: Any, note_id: int) -> None:
    """Mở note không gắn source trong dialog editor."""
    from config.paths import NOTES_DIR
    from ui.widgets.markdown_editor import MarkdownEditorWidget

    dlg = QDialog(window)
    dlg.setWindowTitle("Mở Board note")
    dlg.setMinimumSize(980, 680)

    lay = QVBoxLayout(dlg)
    editor = MarkdownEditorWidget(dlg)
    lay.addWidget(editor)
    editor.load_note(note_id, NOTES_DIR)
    dlg.finished.connect(lambda _code: editor._do_save())
    dlg.exec()


def open_export_dialog(window: Any) -> None:
    """Xuất source bundle cho source đang mở (nếu có)."""
    from config.paths import EXPORTS_DIR, NOTES_DIR
    from core.services.export_service import ExportService

    dual = getattr(window._workspace_view, "_dual_pane", None)
    source_id = getattr(dual, "_source_id", None) if dual else None

    if source_id is None:
        QMessageBox.information(
            window,
            "Xuất văn bản",
            "Vui lòng mở một tài liệu trong Workspace trước khi xuất.",
        )
        return

    try:
        svc = ExportService(EXPORTS_DIR)
        path = svc.export_source_bundle(source_id, NOTES_DIR)
        QMessageBox.information(window, "Xuất thành công", f"Đã xuất:\n{path}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi xuất", str(exc))


def on_note_catalog_changed(window: Any, logger: Any) -> None:
    """Refresh các view liên quan khi catalog note thay đổi."""
    try:
        window._workspace_view.refresh_wikilink_catalog()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Refresh wikilink catalog thất bại: {}", exc)
    try:
        window._dashboard_view.refresh()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Refresh dashboard thất bại: {}", exc)
    try:
        window._board_view.refresh()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Refresh board view thất bại: {}", exc)
    try:
        window._note_management_view.refresh()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Refresh note management view thất bại: {}", exc)


def on_editor_preferences_changed(window: Any, font_family: str, font_ligatures: bool, logger: Any) -> None:
    """Áp dụng ngay cài đặt editor cho workspace hiện tại."""
    try:
        window._workspace_view.apply_editor_preferences(font_family, font_ligatures)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Áp dụng editor preferences thất bại (font_family={}, font_ligatures={}): {}",
            font_family,
            font_ligatures,
            exc,
        )


def activate_project_from_sidebar(window: Any, project_id: object) -> None:
    """Kích hoạt project từ sidebar hoặc chuyển về global mode."""
    try:
        if project_id is None:
            window._project_service.deactivate_project()
            window._apply_project_context(None)
            return
        if not isinstance(project_id, (int, str)):
            raise ValueError("project_id không hợp lệ")
        pid = int(project_id)
        window._project_service.activate_project(pid)
        window._apply_project_context(pid)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể chuyển mode:\n{exc}")
