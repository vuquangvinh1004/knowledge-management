"""Unit tests cho MarkdownSnippetService."""
from __future__ import annotations


class TestMarkdownSnippetService:
    def test_defaults_include_requested_workspace_menu_items(self, mock_settings):
        from core.services.markdown_snippet_service import MarkdownSnippetService
        from core.services.settings_service import SettingsService

        svc = MarkdownSnippetService(SettingsService())
        svc._settings_service._settings = mock_settings

        visible = svc.list_visible()
        assert [snippet.snippet_id for snippet in visible] == ["math", "table", "checklist", "url"]

    def test_create_custom_snippet_adds_it_to_visible_menu(self, mock_settings):
        from core.services.markdown_snippet_service import MarkdownSnippetService
        from core.services.settings_service import SettingsService

        svc = MarkdownSnippetService(SettingsService())
        svc._settings_service._settings = mock_settings

        created = svc.create_snippet(
            name="Khối trích dẫn chuẩn",
            description="Snippet trích dẫn tùy chỉnh.",
            template="> Dòng 1\n> Dòng 2\n",
        )

        visible_ids = [snippet.snippet_id for snippet in svc.list_visible()]
        assert created.snippet_id in visible_ids
        assert svc.get_by_id(created.snippet_id) is not None

    def test_update_and_delete_custom_snippet_persists_changes(self, mock_settings):
        from core.services.markdown_snippet_service import MarkdownSnippetService
        from core.services.settings_service import SettingsService

        svc = MarkdownSnippetService(SettingsService())
        svc._settings_service._settings = mock_settings

        created = svc.create_snippet(
            name="Khối tùy chỉnh",
            description="Mô tả cũ",
            template="Noi dung cu\n",
        )

        updated = svc.update_snippet(
            created.snippet_id,
            name="Khối tùy chỉnh mới",
            description="Mô tả mới",
            template="Noi dung moi\n",
        )
        assert updated.name == "Khối tùy chỉnh mới"
        assert svc.get_by_id(created.snippet_id).template == "Noi dung moi\n"

        svc.delete_snippet(created.snippet_id)
        assert svc.get_by_id(created.snippet_id) is None

    def test_delete_builtin_snippet_is_rejected(self, mock_settings):
        from core.services.markdown_snippet_service import MarkdownSnippetService
        from core.services.settings_service import SettingsService

        svc = MarkdownSnippetService(SettingsService())
        svc._settings_service._settings = mock_settings

        try:
            svc.delete_snippet("math")
        except ValueError as exc:
            assert "mặc định" in str(exc)
        else:
            raise AssertionError("Expected ValueError when deleting built-in snippet")