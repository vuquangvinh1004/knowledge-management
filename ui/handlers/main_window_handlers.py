"""Orchestration handlers cho MainWindow.

Module này gom các luồng điều phối để giảm độ phình của main_window.py
và giữ class MainWindow tập trung vào layout/signal wiring.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QLabel, QDialog, QDialogButtonBox, QMessageBox, QPlainTextEdit, QVBoxLayout


def _format_note_impact_details(impact: dict[str, Any]) -> str:
    """Định dạng thông tin ảnh hưởng của ghi chú bằng tiếng Việt."""
    return "\n".join(
        [
            f"Tiêu đề: {impact.get('title') or '(không tiêu đề)'}",
            f"Loại: {impact.get('note_type')}",
            f"Liên kết vào: {impact.get('incoming_links')}",
            f"Liên kết ra: {impact.get('outgoing_links')}",
            f"Trích xuất: {impact.get('extract_refs')}",
            f"Tài sản: {impact.get('asset_refs')}",
            f"Ô bảng: {impact.get('board_cell_refs')}",
            f"Bảng liên quan: {impact.get('linked_boards')}",
            f"Phạm vi dự án: {impact.get('project_refs')}",
        ]
    )


def open_import_dialog(window: Any) -> None:
    """Mở dialog nhập PDF mới và chỉ cập nhật thư viện sau khi import thành công."""
    from ui.widgets.dialogs.import_source_dialog import ImportSourceDialog

    dlg = ImportSourceDialog(window)
    if dlg.exec() and dlg.imported_source_id is not None:
        window._library_view.refresh()
        window._dashboard_view.refresh()
        window._navigate_to(1)


def start_create_source_note_flow(window: Any, library_index: int) -> None:
    """Điều hướng sang Library ở chế độ chọn tài liệu để tạo source note."""
    window._navigate_to(library_index)
    window._library_view.start_source_note_creation_mode()


def create_source_note_from_library(window: Any, source_id: int) -> None:
    """Tạo source note tường minh cho source được chọn trong Library."""
    from config.paths import ASSETS_DIR, NOTES_DIR
    from core.services.note_service import NoteService
    from core.services.workspace_orchestrator import WorkspaceOrchestrator

    note_svc = NoteService(NOTES_DIR)
    existing = note_svc.get_source_note(source_id)
    if existing is not None:
        QMessageBox.information(
            window,
            "Đã tồn tại source note",
            "Tài liệu này đã có source note, không thể tạo mới trùng lặp.",
        )
        window._library_view.end_source_note_creation_mode()
        window._open_source_in_workspace(source_id)
        return

    try:
        WorkspaceOrchestrator(notes_dir=NOTES_DIR, assets_dir=ASSETS_DIR).ensure_source_note(source_id)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể tạo source note:\n{exc}")
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


def show_note_management_preview(view: Any, note_id: int) -> None:
    """Hiển thị hướng dẫn xem trước note đã chọn."""
    QMessageBox.information(
        view,
        "Xem trước ghi chú",
        "Bạn có thể xem trước đầy đủ ở khung xem trước bên dưới danh sách trước khi chọn Chỉnh sửa.",
    )


def create_note_from_management_view(view: Any) -> None:
    """Tạo ghi chú mới từ màn hình quản lý ghi chú."""
    from config.paths import ASSETS_DIR, NOTES_DIR
    from core.services.project_service import ProjectService
    from core.services.workspace_orchestrator import WorkspaceOrchestrator
    from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

    active_project_id = getattr(view, "_project_id", None)
    active_project_name = None
    if active_project_id is not None:
        try:
            active_project_name = ProjectService().get_project(active_project_id).name
        except Exception:
            active_project_name = None

    dlg = NewNoteDialog(
        view,
        notes_dir=NOTES_DIR,
        current_note_title="",
        active_project_id=active_project_id,
        active_project_name=active_project_name,
    )
    if dlg.exec() != dlg.DialogCode.Accepted:
        return

    try:
        note = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR).create_note_in_scope(
            title=dlg.title_text,
            note_type=dlg.note_type,
            initial_content=dlg.content_text,
            save_to_project=(dlg.save_scope == "project"),
        )
        view.refresh()
        view.note_created.emit(int(note.id))
        QMessageBox.information(view, "Tạo ghi chú", f"Đã tạo ghi chú mới: {note.title}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(view, "Lỗi", f"Không thể tạo ghi chú mới:\n{exc}")


def edit_note_from_management_view(view: Any) -> None:
    """Mở note đã chọn để chỉnh sửa."""
    note_id = view._selected_note_id()
    if note_id is None:
        QMessageBox.information(view, "Chỉnh sửa ghi chú", "Vui lòng chọn một ghi chú trước.")
        return

    row = next((r for r in view._rows if int(r.get("note_id", -1)) == note_id), None)
    if row is not None and int(row.get("is_deleted") or 0) == 1:
        QMessageBox.warning(
            view,
            "Chỉnh sửa ghi chú",
            "Ghi chú này đang ở trạng thái đã xóa mềm, không thể mở chỉnh sửa."
            "\nBạn có thể xóa cứng để dọn hẳn hoặc bỏ lọc 'Bao gồm đã xóa'.",
        )
        return

    reply = QMessageBox.question(
        view,
        "Mở chỉnh sửa ghi chú",
        (
            "Bạn sắp mở ghi chú để chỉnh sửa nội dung.\n"
            "Lưu ý: thay đổi có thể ảnh hưởng đến wikilink, liên kết ngược, thẻ và kết quả tìm kiếm.\n\n"
            "Tiếp tục?"
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    view.note_open_requested.emit(note_id)


def delete_note_from_management_view(view: Any) -> None:
    """Xóa mềm ghi chú đã chọn với cảnh báo ảnh hưởng."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    note_id = view._selected_note_id()
    if note_id is None:
        QMessageBox.information(view, "Xóa ghi chú", "Vui lòng chọn một ghi chú trước.")
        return

    svc = NoteService(NOTES_DIR)
    try:
        impact = svc.get_note_delete_impact(note_id)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(view, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
        return

    extra = ""
    if impact.get("is_source_note"):
        extra = (
            "\n\nLưu ý source note:\n"
            "- Ghi chú này đang gắn với một tệp PDF nguồn.\n"
            "- Khi mở lại nguồn, ứng dụng sẽ tự tạo source note mới nếu cần."
        )

    reply = QMessageBox.warning(
        view,
        "Xác nhận xóa ghi chú",
        (
            "Bạn sắp xóa ghi chú với các thông tin sau:\n"
            f"{_format_note_impact_details(impact)}"
            f"{extra}\n\n"
            "Xác nhận xóa mềm ghi chú này?"
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    try:
        stats = svc.cleanup_unused_notes({note_id})
        view.refresh()
        view.note_deleted.emit()
        QMessageBox.information(
            view,
            "Đã xóa ghi chú",
            (
                "Đã áp dụng xóa mềm ghi chú.\n"
                f"Liên kết cũ đã dọn: {stats.get('removed_stale_links', 0)}"
            ),
        )
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(view, "Lỗi", f"Không thể xóa ghi chú:\n{exc}")


def hard_delete_note_from_management_view(view: Any) -> None:
    """Xóa vĩnh viễn ghi chú đã chọn."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    note_id = view._selected_note_id()
    if note_id is None:
        QMessageBox.information(view, "Xóa cứng", "Vui lòng chọn một ghi chú trước.")
        return

    svc = NoteService(NOTES_DIR)
    try:
        impact = svc.get_note_delete_impact(note_id)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(view, "Lỗi", f"Không thể phân tích ảnh hưởng:\n{exc}")
        return

    first_confirm = QMessageBox.warning(
        view,
        "CẢNH BÁO XÓA CỨNG",
        (
            "Bạn đang chọn XÓA CỨNG ghi chú.\n"
            "- Bản ghi ghi chú sẽ bị xóa khỏi cơ sở dữ liệu.\n"
            "- Tệp Markdown sẽ bị xóa khỏi ổ đĩa.\n"
            "- Không thể hoàn tác.\n\n"
            f"{_format_note_impact_details(impact)}\n"
            f"Ô bảng: {impact.get('board_cell_refs')} ô / {impact.get('linked_boards')} bảng\n\n"
            "Tiếp tục xóa cứng?"
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if first_confirm != QMessageBox.StandardButton.Yes:
        return

    second_confirm = QMessageBox.question(
        view,
        "Xác nhận lần 2",
        "Bạn chắc chắn muốn xóa cứng ghi chú này ngay bây giờ?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if second_confirm != QMessageBox.StandardButton.Yes:
        return

    try:
        svc.hard_delete(note_id, delete_file=True)
        view.refresh()
        view.note_deleted.emit()
        QMessageBox.information(view, "Xóa cứng", "Đã xóa cứng ghi chú thành công.")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(view, "Lỗi", f"Không thể xóa cứng ghi chú:\n{exc}")


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


def sync_board_with_source_notes(window: Any) -> None:
    """Đồng bộ board hiện tại theo source note."""
    from core.services.board_service import BoardService

    view = window._board_view
    svc = BoardService()
    board_id = view.active_board_id or svc.get_default_board().id
    try:
        svc.sync_rows_with_source_notes(
            board_id=board_id,
            project_id=getattr(view, "_project_id", None),
        )
        svc.sync_cells_from_source_note_metadata(
            board_id=board_id,
            project_id=getattr(view, "_project_id", None),
        )
        view.refresh()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể đồng bộ board:\n{exc}")


def edit_board_cell(window: Any, row_id: int, col_id: int) -> None:
    """Sửa nội dung một ô board."""
    from core.services.board_service import BoardService

    view = window._board_view
    svc = BoardService()
    board_id = view.active_board_id or svc.get_default_board().id
    try:
        existing_cell = svc.get_cell(row_id, col_id, board_id=board_id)
        current_content = existing_cell.content_md if existing_cell else ""

        class _CellEditDialog(QDialog):
            def __init__(self, content: str, parent: Any = None) -> None:
                super().__init__(parent)
                self.setWindowTitle("Chỉnh sửa ô")
                self.setMinimumSize(400, 260)
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel("Nội dung Markdown:"))
                self._editor = QPlainTextEdit()
                self._editor.setPlainText(content)
                layout.addWidget(self._editor)
                buttons = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                buttons.accepted.connect(self.accept)
                buttons.rejected.connect(self.reject)
                layout.addWidget(buttons)

            @property
            def content(self) -> str:
                return self._editor.toPlainText()

        dlg = _CellEditDialog(current_content, window)
        if dlg.exec():
            svc.update_cell(
                row_id,
                col_id,
                content_md=dlg.content,
                board_id=board_id,
            )
            view.refresh()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(window, "Lỗi", f"Không thể sửa ô board:\n{exc}")


def export_board_markdown(window: Any) -> None:
    """Xuất board hiện tại ra Markdown."""
    from config.paths import EXPORTS_DIR
    from core.services.board_service import BoardService
    from core.services.export_service import ExportService

    view = window._board_view
    svc = BoardService()
    board_id = view.active_board_id or svc.get_default_board().id
    try:
        path = ExportService(EXPORTS_DIR).export_board_markdown(board_id=board_id)
        QMessageBox.information(window, "Xuất thành công", f"Đã xuất:\n{path}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(window, "Lỗi xuất", str(exc))


def export_board_csv(window: Any) -> None:
    """Xuất board hiện tại ra CSV."""
    from config.paths import EXPORTS_DIR
    from core.services.board_service import BoardService
    from core.services.export_service import ExportService

    view = window._board_view
    svc = BoardService()
    board_id = view.active_board_id or svc.get_default_board().id
    try:
        path = ExportService(EXPORTS_DIR).export_board_csv(board_id=board_id)
        QMessageBox.information(window, "Xuất thành công", f"Đã xuất:\n{path}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(window, "Lỗi xuất", str(exc))


def open_board_graph_view(window: Any) -> None:
    """Mở đồ thị liên kết của board."""
    from ui.widgets.graph_view import GraphViewWidget

    dlg = QDialog(window)
    dlg.setWindowTitle("Đồ thị liên kết")
    dlg.setMinimumSize(980, 640)

    layout = QVBoxLayout(dlg)
    graph = GraphViewWidget(dlg)
    graph.note_open_requested.connect(window._board_view.note_open_requested)
    graph.source_open_requested.connect(window._board_view.source_open_requested)
    layout.addWidget(graph)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dlg.reject)
    buttons.accepted.connect(dlg.accept)
    buttons.button(QDialogButtonBox.StandardButton.Close).setText("Đóng")
    layout.addWidget(buttons)

    dlg.exec()


def open_board_criteria_manager(window: Any) -> None:
    """Mở dialog tùy chỉnh tiêu chí board."""
    from core.services.board_service import BoardService
    from ui.widgets.dialogs.board_criteria_manager_dialog import BoardCriteriaManagerDialog
    from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA

    view = window._board_view
    svc = BoardService()
    board_id = view.active_board_id or svc.get_default_board().id

    try:
        svc.get_board(board_id)
        svc.ensure_full_meta_columns(board_id=board_id)

        system_labels = set(BOARD_META_ANALYSIS_CRITERIA)
        criteria = [
            {
                "id": col.id,
                "label": col.label,
                "visible": bool(getattr(col, "is_visible", True)),
                "locked": col.label in system_labels,
            }
            for col in svc.list_columns(board_id)
        ]

        dlg = BoardCriteriaManagerDialog(criteria, window)
        if dlg.exec():
            try:
                svc.apply_column_configuration(board_id, dlg.get_configurations())
                QMessageBox.information(window, "Thành công", "Tiêu chí đã được cập nhật.")
                view.refresh()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error updating board criteria")
                QMessageBox.warning(window, "Lỗi", f"Không thể cập nhật tiêu chí: {exc}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(window, "Lỗi", f"Không thể mở tùy chỉnh tiêu chí:\n{exc}")


def update_last_opened_page_from_workspace(window: Any, source_id: int, page_no: int) -> None:
    """Lưu trang đang mở của source từ Workspace."""
    from core.services.source_service import SourceService

    try:
        SourceService().update_last_opened_page(source_id, page_no)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Không thể cập nhật last_opened_page cho source id={} page={}: {}",
            source_id,
            page_no,
            exc,
        )


def extract_text_from_workspace(window: Any, source_id: int, page_no: int, pdf_rect: tuple) -> None:
    """Trích văn bản từ vùng chọn trong Workspace."""
    from core.extraction.pdf_text import extract_region_text

    view = window._workspace_view
    viewer = view.pdf_viewer_for_source(source_id)
    if viewer is None or not viewer.file_path:
        return

    doc = getattr(viewer, "_doc", None)
    if doc is None:
        return

    raw = extract_region_text(doc, page_no, pdf_rect)
    if not raw.strip():
        QMessageBox.information(window, "Thông tin", "Vùng đã chọn không có văn bản.")
        return

    text, anchor = view._orchestrator.prepare_text_extract(source_id, page_no, pdf_rect, raw)
    source_code = view.source_code_for_source(source_id)
    extract_id = view._orchestrator.commit_extract(
        source_id=source_id,
        page_no=page_no,
        extract_type="text",
        source_anchor=anchor,
        content_md=text,
        note_id=None,
    )
    view._draft_editor.insert_extract(
        text,
        anchor,
        source_code=source_code,
        page_no=page_no,
        extract_id=extract_id,
        rect=pdf_rect,
    )


def extract_table_from_workspace(window: Any, source_id: int, page_no: int, pdf_rect: tuple) -> None:
    """Trích bảng từ vùng chọn trong Workspace."""
    from core.extraction.normalizers import table_to_markdown
    from core.extraction.pdf_table import extract_table_from_region
    from ui.widgets.dialogs.table_preview_dialog import TablePreviewDialog

    view = window._workspace_view
    viewer = view.pdf_viewer_for_source(source_id)
    if viewer is None or not viewer.file_path:
        return

    rows = extract_table_from_region(viewer.file_path, page_no, pdf_rect)
    if not rows:
        QMessageBox.information(window, "Thông tin", "Không phát hiện bảng trong vùng đã chọn.")
        return

    table_md = table_to_markdown(rows)
    anchor = view._orchestrator.build_anchor(source_id, page_no, pdf_rect)
    source_code = view.source_code_for_source(source_id)

    dlg = TablePreviewDialog(table_md, anchor, window)
    if dlg.exec():
        extract_id = view._orchestrator.commit_extract(
            source_id=source_id,
            page_no=page_no,
            extract_type="table",
            source_anchor=anchor,
            content_md=table_md,
            note_id=None,
        )
        view._draft_editor.insert_table(
            table_md,
            anchor,
            source_code=source_code,
            page_no=page_no,
            extract_id=extract_id,
            rect=pdf_rect,
        )


def capture_image_from_workspace(window: Any, source_id: int, page_no: int, pdf_rect: tuple) -> None:
    """Chụp ảnh từ vùng chọn trong Workspace."""
    from core.extraction.pdf_image import capture_region

    view = window._workspace_view
    viewer = view.pdf_viewer_for_source(source_id)
    if viewer is None or not viewer.file_path:
        return

    doc = getattr(viewer, "_doc", None)
    if doc is None:
        return

    try:
        img_bytes = capture_region(doc, page_no, pdf_rect)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể chụp ảnh:\n{exc}")
        return

    try:
        asset_path = view._orchestrator.save_image_asset(source_id, None, img_bytes)
        view._draft_editor.insert_asset_ref(asset_path, "")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", f"Không thể lưu ảnh:\n{exc}")


def do_backup_from_settings(window: Any, keep_count: int) -> None:
    """Tạo backup từ tab Thiết lập và lưu lại số bản sao giữ lại."""
    from config.paths import BACKUPS_DIR, DATABASE_FILE
    from core.services.backup_service import BackupService
    from core.services.settings_service import SettingsService

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        entry = BackupService(DATABASE_FILE, BACKUPS_DIR).create_backup()
        SettingsService().set("backup_keep_count", keep_count)
        QMessageBox.information(window, "Sao lưu thành công", f"Đã tạo backup:\n{entry.path}")
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi sao lưu", str(exc))
    finally:
        view.set_maintenance_buttons_enabled(True)


def rebuild_fts_index(window: Any) -> None:
    """Xây dựng lại chỉ mục FTS từ tab Thiết lập."""
    from config.paths import DATABASE_FILE, NOTES_DIR
    from core.services.search_service import SearchService

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        view.set_fts_status("Đang xây dựng lại chỉ mục...")
        count = SearchService(str(DATABASE_FILE), NOTES_DIR).rebuild_all()
        view.set_fts_status(f"✓ {count} mục đã được lập chỉ mục")
    except Exception as exc:  # noqa: BLE001
        view.set_fts_status("Lỗi xây dựng lại chỉ mục!")
        logger.error(f"Rebuild FTS lỗi: {exc}")
    finally:
        view.set_maintenance_buttons_enabled(True)


def reset_settings(window: Any) -> None:
    """Khôi phục cài đặt về mặc định từ tab Thiết lập."""
    from core.services.settings_service import SettingsService

    reply = QMessageBox.question(
        window,
        "Khôi phục cài đặt",
        "Bạn có chắc muốn khôi phục tất cả cài đặt về mặc định?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    SettingsService().reset_to_defaults()
    window._settings_view.reload_settings()
    QMessageBox.information(window, "Đã khôi phục", "Cài đặt đã được khôi phục về mặc định.")


def normalize_source_note_titles(window: Any) -> None:
    """Chuẩn hóa title source note từ tab Thiết lập."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        updated = NoteService(NOTES_DIR).normalize_source_note_titles()
        QMessageBox.information(
            window,
            "Chuẩn hóa hoàn tất",
            f"Đã cập nhật {updated} source note.",
        )
        view.source_titles_normalized.emit()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", str(exc))
    finally:
        view.set_maintenance_buttons_enabled(True)


def refresh_wikilink_catalog(window: Any) -> None:
    """Làm mới catalog wikilink từ tab Thiết lập."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        stats = NoteService(NOTES_DIR).refresh_wikilink_note_catalog()
        QMessageBox.information(
            window,
            "Đã làm mới danh sách wikilink",
            (
                f"Source note thiếu file đã soft-delete: {stats.get('soft_deleted_missing_file', 0)}\n"
                f"Stub note mồ côi đã dọn: {stats.get('removed_orphan_stub_notes', 0)}\n"
                f"Link stale đã dọn: {stats.get('removed_stale_links', 0)}"
            ),
        )
        view.wikilink_catalog_refreshed.emit()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", str(exc))
    finally:
        view.set_maintenance_buttons_enabled(True)


def cleanup_unused_notes_with_preview(window: Any) -> None:
    """Xem trước và dọn ghi chú không còn dùng từ tab Thiết lập."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService
    from ui.widgets.dialogs.note_cleanup_preview_dialog import NoteCleanupPreviewDialog

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        svc = NoteService(NOTES_DIR)
        candidates = svc.get_unused_note_candidates()
        if not candidates:
            QMessageBox.information(
                window,
                "Không có ghi chú cần dọn",
                "Hiện tại không phát hiện ghi chú không còn dùng.",
            )
            return

        dlg = NoteCleanupPreviewDialog(candidates, window)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        selected_ids = dlg.selected_note_ids
        if not selected_ids:
            QMessageBox.information(
                window,
                "Chưa dọn ghi chú nào",
                "Bạn đã chọn giữ lại toàn bộ ghi chú trong danh sách xem trước.",
            )
            return

        stats = svc.cleanup_unused_notes(selected_ids)
        QMessageBox.information(
            window,
            "Đã áp dụng dọn ghi chú",
            (
                f"Đã soft-delete: {stats.get('soft_deleted', 0)} ghi chú\n"
                f"Đã dọn stale links: {stats.get('removed_stale_links', 0)}"
            ),
        )
        view.wikilink_catalog_refreshed.emit()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", str(exc))
    finally:
        view.set_maintenance_buttons_enabled(True)


def audit_missing_source_note_files(window: Any) -> None:
    """Quét read-only source note thiếu file từ tab Thiết lập."""
    from config.paths import NOTES_DIR
    from core.services.note_service import NoteService

    view = window._settings_view
    view.set_maintenance_buttons_enabled(False)
    try:
        issues = NoteService(NOTES_DIR).audit_missing_source_note_files()
        if not issues:
            QMessageBox.information(
                window,
                "Kiểm tra source note",
                "Không phát hiện source note nào bị thiếu file Markdown.",
            )
            return

        preview_lines: list[str] = []
        for item in issues[:20]:
            code = item.get("source_code") or "----"
            sid = item.get("source_id") or "?"
            nid = item.get("note_id") or "?"
            title = item.get("note_title") or "(không tiêu đề)"
            preview_lines.append(f"- [{code}|source={sid}|ghi chú={nid}] {title}")

        more = ""
        if len(issues) > 20:
            more = f"\n... và {len(issues) - 20} mục khác."

        preview_text = "\n".join(preview_lines)

        QMessageBox.warning(
            window,
            "Phát hiện source note thiếu file",
            (
                f"Tổng số phát hiện: {len(issues)}\n\n"
                "Danh sách mẫu:\n"
                f"{preview_text}"
                f"{more}\n\n"
                "Đây là thao tác chỉ xem. Không có thay đổi dữ liệu."
            ),
        )
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(window, "Lỗi", str(exc))
    finally:
        view.set_maintenance_buttons_enabled(True)


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
    """Cập nhật badge chế độ Toàn cục/Dự án trong Settings view."""
    mode_text = "Chế độ: Toàn cục"
    if project_id is None:
        window._settings_view.set_mode_text(mode_text)
        return
    try:
        p = window._project_service.get_project(project_id)
        mode_text = f"Chế độ: Dự án - {p.name}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không thể đọc thông tin project_id={} để hiển thị mode: {}", project_id, exc)
        mode_text = "Chế độ: Toàn cục"
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
    dlg.setWindowTitle("Mở ghi chú bảng")
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


def on_editor_preferences_changed(
    window: Any,
    font_family: str,
    font_ligatures: bool,
    font_size: int,
    logger: Any,
) -> None:
    """Áp dụng ngay cài đặt editor cho workspace hiện tại."""
    try:
        window._workspace_view.apply_editor_preferences(font_family, font_ligatures, font_size)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Áp dụng editor preferences thất bại (font_family={}, font_ligatures={}, font_size={}): {}",
            font_family,
            font_ligatures,
            font_size,
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
