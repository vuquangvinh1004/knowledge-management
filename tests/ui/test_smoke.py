"""UI Smoke tests — kiểm tra khởi tạo widgets mà không crash.

Không test logic nghiệp vụ — chỉ đảm bảo widget khởi tạo được,
hiển thị được và không raise exception.

Dùng pytest-qt qtbot fixture.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_db(db_session):
    """Đảm bảo db_session đã được khởi tạo (fixture side effect)."""
    pass  # fixture db_session đã wire SessionFactory


# ---------------------------------------------------------------------------
# MainWindow smoke test
# ---------------------------------------------------------------------------

class TestMainWindowSmoke:
    def test_main_window_creates(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        assert win is not None
        assert win.windowTitle() != ""

    def test_main_window_shows(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        win.show()
        assert win.isVisible()

    def test_navigate_to_all_views(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        for idx in range(6):
            win._navigate_to(idx)
            assert win._stack.currentIndex() == idx

    def test_warning_banner_hidden_by_default(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        assert win._warning_banner.isHidden()

    def test_warning_banner_shows_on_soft_deps(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        win.show_soft_dep_warnings(["fitz", "pdfplumber"])
        assert not win._warning_banner.isHidden()

    def test_warning_banner_hides_for_empty_list(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        win.show_soft_dep_warnings([])
        assert win._warning_banner.isHidden()

    def test_main_window_mode_indicator_is_in_settings_view(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        assert hasattr(win._settings_view, "_lbl_mode_info")
        assert "Mode:" in win._settings_view._lbl_mode_info.text()

    def test_main_window_has_no_toolbar_project_button(self, qtbot, db_session):
        from ui.main_window import MainWindow
        win = MainWindow()
        qtbot.addWidget(win)
        assert not hasattr(win, "_btn_manage_projects")


# ---------------------------------------------------------------------------
# DashboardView smoke test
# ---------------------------------------------------------------------------

class TestDashboardViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.views.dashboard_view import DashboardView
        view = DashboardView()
        qtbot.addWidget(view)
        assert view is not None

    def test_refresh_without_crash(self, qtbot, db_session):
        from ui.views.dashboard_view import DashboardView
        view = DashboardView()
        qtbot.addWidget(view)
        view.refresh()  # không có data → empty state


# ---------------------------------------------------------------------------
# LibraryView smoke test
# ---------------------------------------------------------------------------

class TestLibraryViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.views.library_view import LibraryView
        view = LibraryView()
        qtbot.addWidget(view)
        assert view is not None

    def test_refresh_empty_library(self, qtbot, db_session):
        from ui.views.library_view import LibraryView
        view = LibraryView()
        qtbot.addWidget(view)
        view.refresh()
        assert view._list_widget.count() == 0


# ---------------------------------------------------------------------------
# WorkspaceView smoke test
# ---------------------------------------------------------------------------

class TestWorkspaceViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.views.workspace_view import WorkspaceView
        view = WorkspaceView()
        qtbot.addWidget(view)
        assert view is not None

    def test_initial_state_is_empty(self, qtbot, db_session):
        from ui.views.workspace_view import WorkspaceView
        view = WorkspaceView()
        qtbot.addWidget(view)
        # index 0 = empty state
        assert view._stack.currentIndex() == 0


class TestDualPaneHostRecoverySmoke:
    def test_shows_recovery_notice_when_note_is_auto_recovered(self, qtbot, monkeypatch, tmp_path):
        from PySide6.QtWidgets import QMessageBox
        from ui.widgets.dual_pane_host import DualPaneHost, PDFViewerWidget

        captured: dict[str, str] = {}

        def _fake_info(_parent, title: str, text: str):
            captured["title"] = title
            captured["text"] = text
            return QMessageBox.StandardButton.Ok

        monkeypatch.setattr(QMessageBox, "information", _fake_info)
        monkeypatch.setattr(PDFViewerWidget, "open_document", lambda _self, _path, _page: None)

        host = DualPaneHost()
        qtbot.addWidget(host)

        source = SimpleNamespace(
            file_path=str(tmp_path / "fake.pdf"),
            last_opened_page=1,
            title="Fake Source",
            source_code="AA01",
        )
        note = SimpleNamespace(id=101)
        monkeypatch.setattr(
            host._orchestrator,
            "load_source_with_note",
            lambda _source_id: (source, note, "Ứng dụng đã tự tạo lại ghi chú nguồn."),
        )

        host.open_source(1)
        assert captured.get("title") == "Đã tự phục hồi ghi chú"
        assert "tự tạo lại" in (captured.get("text") or "")


# ---------------------------------------------------------------------------
# PDFViewerWidget smoke test
# ---------------------------------------------------------------------------

class TestPDFViewerSmoke:
    def test_creates_without_crash(self, qtbot):
        from ui.widgets.pdf_viewer import PDFViewerWidget
        w = PDFViewerWidget()
        qtbot.addWidget(w)
        assert w is not None

    def test_keyboard_shortcuts_exist(self, qtbot):
        from ui.widgets.pdf_viewer import PDFViewerWidget
        w = PDFViewerWidget()
        qtbot.addWidget(w)
        assert w._shortcut_prev is not None
        assert w._shortcut_next is not None


class TestMarkdownEditorSmoke:
    def test_new_note_button_exists(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        assert hasattr(w, "_btn_new_note")

    def test_new_note_button_enabled_after_load(self, qtbot, db_session, notes_dir):
        from core.services.note_service import NoteService
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        note = NoteService(notes_dir).create_note("SCCT", "concept_note")
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w.load_note(note.id, notes_dir)
        assert w._btn_new_note.isEnabled()

    def test_wikilink_popup_label_not_inserted_into_editor_content(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._editor.setPlainText("[[")
        cursor = w._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        w._editor.setTextCursor(cursor)
        w._wikilink_display_to_title = {"concept - Khái niệm mới": "Khái niệm mới"}
        w._on_wikilink_activated("concept - Khái niệm mới")
        assert w._editor.toPlainText() == "[[Khái niệm mới]] "

    def test_wikilink_insertion_strips_legacy_type_prefix(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._editor.setPlainText("[[")
        cursor = w._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        w._editor.setTextCursor(cursor)
        w._on_wikilink_activated("concept - mô hình hóa")
        assert w._editor.toPlainText() == "[[mô hình hóa]] "


class TestNewNoteDialogSmoke:
    def test_new_note_dialog_creates(self, qtbot):
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        dlg = NewNoteDialog()
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Tạo note mới"
        assert dlg.note_type in {"concept_note", "synthesis_note", "board_note"}

    def test_new_note_dialog_default_markers(self, qtbot):
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        dlg = NewNoteDialog()
        qtbot.addWidget(dlg)

        dlg._combo_type.setCurrentIndex(1)  # synthesis_note
        assert dlg.title_text.startswith("~")

        dlg._combo_type.setCurrentIndex(2)  # board_note
        assert dlg.title_text.startswith("!")

    def test_new_note_dialog_wikilink_popup_label_not_inserted(self, qtbot):
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        dlg = NewNoteDialog()
        qtbot.addWidget(dlg)
        dlg._edit_content.setPlainText("[[")
        cursor = dlg._edit_content.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        dlg._edit_content.setTextCursor(cursor)
        dlg._wikilink_display_to_title = {"concept - Khái niệm mới": "Khái niệm mới"}
        dlg._on_wikilink_activated("concept - Khái niệm mới")
        assert dlg._edit_content.toPlainText() == "[[Khái niệm mới]] "

    def test_new_note_dialog_project_scope_options(self, qtbot):
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        dlg = NewNoteDialog(active_project_id=3, active_project_name="Dự án A")
        qtbot.addWidget(dlg)

        assert dlg._combo_scope.count() == 2
        assert dlg._combo_scope.currentData() == "project"


class TestProjectManagerDialogSmoke:
    def test_project_manager_dialog_creates(self, qtbot, db_session, notes_dir):
        from ui.widgets.dialogs.project_manager_dialog import ProjectManagerDialog

        dlg = ProjectManagerDialog(notes_dir=notes_dir)
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Quản lý dự án nghiên cứu"
        assert hasattr(dlg, "_project_list")
        assert hasattr(dlg, "_global_notes")
        assert hasattr(dlg, "_ref_notes")
        assert hasattr(dlg, "_btn_package")

    def test_package_button_calls_export_service(self, qtbot, db_session, notes_dir, tmp_path, monkeypatch):
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from ui.widgets.dialogs.project_manager_dialog import ProjectManagerDialog

        dlg = ProjectManagerDialog(notes_dir=notes_dir)
        qtbot.addWidget(dlg)

        # tạo project để có selection hợp lệ
        p = dlg._project_service.create_project("Project Package Smoke")
        dlg._reload_projects()
        dlg._project_list.setCurrentRow(0)

        called: dict[str, object] = {}

        def _fake_get_dir(*_args, **_kwargs):
            return str(tmp_path)

        def _fake_export(project_id: int, output_dir: Path):
            called["project_id"] = project_id
            called["output_dir"] = output_dir
            out = output_dir / f"bundle_{project_id}"
            out.mkdir(parents=True, exist_ok=True)
            return out

        def _fake_question(*_args, **_kwargs):
            return QMessageBox.StandardButton.No

        monkeypatch.setattr(QFileDialog, "getExistingDirectory", _fake_get_dir)
        monkeypatch.setattr(dlg._project_service, "export_project_bundle", _fake_export)
        monkeypatch.setattr(QMessageBox, "question", _fake_question)

        dlg._on_package_project()

        assert called.get("project_id") == p.id
        assert called.get("output_dir") == tmp_path


# ---------------------------------------------------------------------------
# BoardView smoke test
# ---------------------------------------------------------------------------

class TestBoardViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.views.board_view import BoardView
        view = BoardView()
        qtbot.addWidget(view)
        assert view is not None
        assert hasattr(view, "_btn_graph_view")
        assert hasattr(view, "_board_selector")
        assert hasattr(view, "_btn_init")
        assert hasattr(view, "_btn_open_board_note")

    def test_empty_board_shows_empty_state(self, qtbot, db_session):
        from ui.views.board_view import BoardView
        view = BoardView()
        qtbot.addWidget(view)
        view.refresh()
        assert not view._empty_state.isHidden()

    def test_board_with_rows_hides_empty_state(self, qtbot, db_session):
        from ui.views.board_view import BoardView
        from core.services.board_service import BoardService
        svc = BoardService()
        svc.create_row("Row Smoke")
        svc.create_column("Col Smoke")
        view = BoardView()
        qtbot.addWidget(view)
        view.refresh()
        assert view._empty_state.isHidden()
        assert not view._table.isHidden()

    def test_board_selector_switches_active_board(self, qtbot, db_session):
        from ui.views.board_view import BoardView
        from core.services.board_service import BoardService

        svc = BoardService()
        b1 = svc.create_board("Board Smoke A")
        b2 = svc.create_board("Board Smoke B")
        svc.create_row("A-row", board_id=b1.id)
        svc.create_column("A-col", board_id=b1.id)
        svc.create_row("B-row", board_id=b2.id)
        svc.create_column("B-col", board_id=b2.id)

        view = BoardView()
        qtbot.addWidget(view)
        view.refresh()
        view._on_board_selected(b2.id)
        assert view._active_board_id == b2.id
        assert any(r.label == "B-row" for r in view._rows)


# ---------------------------------------------------------------------------
# GraphViewWidget smoke test
# ---------------------------------------------------------------------------

class TestGraphViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.widgets.graph_view import GraphViewWidget
        w = GraphViewWidget()
        qtbot.addWidget(w)
        assert w is not None
        assert hasattr(w, "_edit_search")
        assert hasattr(w, "_combo_hops")
        assert hasattr(w, "_btn_fit")
        assert hasattr(w, "_chk_cluster_by_tag")
        assert hasattr(w, "_chk_virtualize")
        assert hasattr(w, "_btn_save_layout")

    def test_refresh_with_seed_data(self, qtbot, db_session, notes_dir):
        from core.services.link_service import LinkService
        from core.services.note_service import NoteService
        from ui.widgets.graph_view import GraphViewWidget

        note_svc = NoteService(notes_dir)
        n1 = note_svc.create_note("Node Alpha", "concept_note")
        n2 = note_svc.create_note("Node Beta", "synthesis_note")
        LinkService().create_link(n1.id, n2.id, "wikilink")

        w = GraphViewWidget()
        qtbot.addWidget(w)
        w.refresh_graph()
        assert "Nút:" in w._lbl_status.text()

    def test_search_node_selects_target(self, qtbot, db_session, notes_dir):
        from core.services.note_service import NoteService
        from ui.widgets.graph_view import GraphViewWidget

        note_svc = NoteService(notes_dir)
        target = note_svc.create_note("Sustainable Node", "concept_note")

        w = GraphViewWidget()
        qtbot.addWidget(w)
        w.refresh_graph()
        w._edit_search.setText("sustainable")
        w._on_search_node()
        assert w._selected_note_id == target.id


# ---------------------------------------------------------------------------
# SearchPanelDialog smoke test
# ---------------------------------------------------------------------------

class TestSearchPanelSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.widgets.search_panel import SearchPanelDialog
        dlg = SearchPanelDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_empty_search_shows_prompt(self, qtbot, db_session):
        from ui.widgets.search_panel import SearchPanelDialog
        dlg = SearchPanelDialog()
        qtbot.addWidget(dlg)
        dlg._input.setText("")
        dlg._do_search()
        assert "Nhập" in dlg._lbl_status.text()

    def test_no_match_shows_empty_message(self, qtbot, db_session):
        from ui.widgets.search_panel import SearchPanelDialog
        dlg = SearchPanelDialog()
        qtbot.addWidget(dlg)
        dlg._input.setText("xyzzynotexist12345")
        dlg._do_search()
        assert dlg._result_list.count() == 0


# ---------------------------------------------------------------------------
# MarkdownEditorWidget smoke test
# ---------------------------------------------------------------------------

class TestMarkdownEditorSmoke:
    def test_creates_without_crash(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        assert w is not None

    def test_initial_state_is_unloaded(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        assert w._note_id is None
        assert not w._editor.isVisible()

    def test_insert_extract_appends_text(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        # Mô phỏng note đã tải
        w._note_id = 1
        w._set_note_loaded(True)
        w.insert_extract("Nội dung test", "source://1?page=1")
        content = w.get_content()
        assert "Nội dung test" in content
        assert "source://1?page=1" in content

    def test_extract_hashtags_helper(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        tags = w._extract_hashtags("#alpha nội dung #beta-2\n# tiêu đề")
        assert "alpha" in tags
        assert "beta-2" in tags
        assert "tiêu" not in tags  # '# tiêu đề' là markdown heading

    def test_insert_hashtag_completion(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setFocus()
        w._editor.setPlainText("Ghi chú #be")
        cursor = w._editor.textCursor()
        cursor.setPosition(len(w._editor.toPlainText()))
        w._editor.setTextCursor(cursor)
        w._insert_hashtag_completion("#ben_vung")
        assert "#ben_vung " in w.get_content()

    def test_heading_marker_not_treated_as_hashtag_context(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget
        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("#")
        cursor = w._editor.textCursor()
        cursor.setPosition(1)
        w._editor.setTextCursor(cursor)
        assert w._current_hashtag_context() is None

    def test_scan_and_create_wikilink_uses_slugify(self, qtbot, db_session, notes_dir):
        from core.services.link_service import LinkService
        from core.services.note_service import NoteService
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        note_svc = NoteService(notes_dir)
        src = note_svc.create_note("Source Note", "concept_note")
        target = note_svc.create_note("Bền Vững", "concept_note")

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w.load_note(src.id, notes_dir)
        w._editor.setPlainText(f"Lien ket [[{target.title}]]")
        w._scan_and_create_wikilinks()

        outgoing = LinkService().get_outgoing_links(src.id)
        assert any(l.to_note_id == target.id and l.link_type == "wikilink" for l in outgoing)

    def test_blockquote_enter_auto_continues(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("> Dòng 1")

        cursor = w._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        w._editor.setTextCursor(cursor)

        qtbot.keyClick(w._editor, Qt.Key.Key_Return)
        assert w._editor.toPlainText().endswith("\n> ")

    def test_blockquote_enter_on_empty_quote_exits_block(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("> Dòng 1")

        cursor = w._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        w._editor.setTextCursor(cursor)

        qtbot.keyClick(w._editor, Qt.Key.Key_Return)
        qtbot.keyClick(w._editor, Qt.Key.Key_Return)
        assert "> \n" not in w._editor.toPlainText()

    def test_blockquote_full_width_overlay_is_applied(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("> Dòng quote\nNội dung thường")
        w._refresh_blockquote_overlays()

        overlays = w._editor.extraSelections()
        assert len(overlays) >= 1

    def test_inline_latex_math_gets_highlighted(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("Năng lượng: $E=mc^2$")
        w._syntax_highlighter.rehighlight()

        block = w._editor.document().firstBlock()
        formats = block.layout().formats()
        assert any(rng.format.fontFamily() == "Roboto Mono" for rng in formats)
        assert any(rng.format.foreground().color().isValid() for rng in formats)

    def test_display_latex_block_gets_highlighted(self, qtbot):
        from ui.widgets.markdown_editor import MarkdownEditorWidget

        w = MarkdownEditorWidget()
        qtbot.addWidget(w)
        w._note_id = 1
        w._set_note_loaded(True)
        w._editor.setPlainText("$$\na^2+b^2=c^2\n$$")
        w._syntax_highlighter.rehighlight()

        block = w._editor.document().firstBlock().next()
        formats = block.layout().formats()
        assert any(rng.format.fontFamily() == "Roboto Mono" for rng in formats)
        assert any(rng.format.foreground().color().isValid() for rng in formats)


# ---------------------------------------------------------------------------
# SettingsView smoke test
# ---------------------------------------------------------------------------

class TestSettingsViewSmoke:
    def test_creates_without_crash(self, qtbot):
        from ui.views.settings_view import SettingsView
        v = SettingsView()
        qtbot.addWidget(v)
        assert v is not None
        assert hasattr(v, "_btn_normalize_source_titles")
        assert hasattr(v, "_btn_refresh_wikilink_catalog")
        assert hasattr(v, "_btn_cleanup_unused_notes")
        assert hasattr(v, "_btn_audit_source_notes")
        assert hasattr(v, "_combo_editor_font")
        assert hasattr(v, "_chk_editor_ligatures")
        assert hasattr(v, "_lbl_mode_info")

    def test_mode_badge_uses_color_style(self, qtbot):
        from ui.views.settings_view import SettingsView

        v = SettingsView()
        qtbot.addWidget(v)
        v.set_mode_text("Mode: Global")
        assert "#DCFCE7" in v._lbl_mode_info.styleSheet()
        v.set_mode_text("Mode: Project - Demo")
        assert "#DBEAFE" in v._lbl_mode_info.styleSheet()


class TestNoteManagementViewSmoke:
    def test_creates_without_crash(self, qtbot, db_session):
        from ui.views.note_management_view import NoteManagementView

        v = NoteManagementView()
        qtbot.addWidget(v)
        assert v is not None
        assert hasattr(v, "_btn_create")
        assert hasattr(v, "_btn_preview")
        assert hasattr(v, "_btn_edit")
        assert hasattr(v, "_btn_delete")
        assert hasattr(v, "_btn_hard_delete")
        assert hasattr(v, "_combo_type")
        assert hasattr(v, "_combo_scope")
        assert hasattr(v, "_chk_include_deleted")
        assert hasattr(v, "_preview")

    def test_refresh_without_crash(self, qtbot, db_session):
        from ui.views.note_management_view import NoteManagementView

        v = NoteManagementView()
        qtbot.addWidget(v)
        v.refresh()


# ---------------------------------------------------------------------------
# SourceDetailPanel smoke test
# ---------------------------------------------------------------------------

class TestSourceDetailPanelSmoke:
    def test_creates_without_crash(self, qtbot):
        from ui.widgets.source_detail_panel import SourceDetailPanel
        p = SourceDetailPanel()
        qtbot.addWidget(p)
        assert p is not None

    def test_empty_state_by_default(self, qtbot):
        from ui.widgets.source_detail_panel import SourceDetailPanel
        p = SourceDetailPanel()
        qtbot.addWidget(p)
        assert p._stack.currentIndex() == 0

    def test_clear_shows_empty_state(self, qtbot, db_session):
        from ui.widgets.source_detail_panel import SourceDetailPanel
        p = SourceDetailPanel()
        qtbot.addWidget(p)
        p.clear()
        assert p._stack.currentIndex() == 0

    def test_load_nonexistent_source_shows_empty(self, qtbot, db_session):
        from ui.widgets.source_detail_panel import SourceDetailPanel
        p = SourceDetailPanel()
        qtbot.addWidget(p)
        p.load_source(99999)  # không tồn tại
        assert p._stack.currentIndex() == 0


# ---------------------------------------------------------------------------
# LibraryView with detail panel smoke test
# ---------------------------------------------------------------------------

class TestLibraryViewWithDetailPanel:
    def test_detail_panel_exists(self, qtbot, db_session):
        from ui.views.library_view import LibraryView
        v = LibraryView()
        qtbot.addWidget(v)
        assert hasattr(v, "_detail_panel")

    def test_selection_change_clears_panel_on_no_item(self, qtbot, db_session):
        from ui.views.library_view import LibraryView
        v = LibraryView()
        qtbot.addWidget(v)
        v._on_selection_changed(None, None)
        assert v._detail_panel._stack.currentIndex() == 0  # empty state


# ---------------------------------------------------------------------------
# WarningBanner smoke test
# ---------------------------------------------------------------------------

class TestWarningBannerSmoke:
    def test_creates_hidden(self, qtbot):
        from ui.widgets.warning_banner import WarningBanner
        b = WarningBanner()
        qtbot.addWidget(b)
        assert b.isHidden()

    def test_show_warnings_makes_visible(self, qtbot):
        from ui.widgets.warning_banner import WarningBanner
        b = WarningBanner()
        qtbot.addWidget(b)
        b.show_warnings(["fitz không có"])
        assert not b.isHidden()

    def test_show_warnings_empty_hides(self, qtbot):
        from ui.widgets.warning_banner import WarningBanner
        b = WarningBanner()
        qtbot.addWidget(b)
        b.show_warnings(["fitz"])
        b.show_warnings([])
        assert b.isHidden()
