"""Unit tests cho core/services/settings_service.py."""
from __future__ import annotations


class TestSettingsService:
    def test_get_returns_default_value(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        # Reset để đảm bảo defaults
        svc.reset_to_defaults()
        assert svc.get("theme") == "light"
        assert svc.get("autosave_delay_ms") == 2000

    def test_set_and_get(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.set("theme", "dark")
        assert svc.get("theme") == "dark"
        # Dọn dẹp
        svc.set("theme", "light")

    def test_get_unknown_key_returns_default_param(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        result = svc.get("nonexistent_key_xyz", "fallback_value")
        assert result == "fallback_value"

    def test_all_defaults_returns_dict_with_known_keys(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.reset_to_defaults()
        defaults = svc.all_defaults()
        assert "theme" in defaults
        assert "autosave_delay_ms" in defaults
        assert "backup_keep_count" in defaults
        assert "window_width" in defaults
        assert "fts_rebuild_on_startup" in defaults
        assert "editor.fontFamily" in defaults
        assert "editor.fontLigatures" in defaults
        assert "editor.fontSize" in defaults

    def test_reset_to_defaults_restores_theme(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.set("theme", "dark")
        svc.reset_to_defaults()
        assert svc.get("theme") == "light"

    def test_backup_keep_count_default(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.reset_to_defaults()
        assert svc.get("backup_keep_count") == 10

    def test_search_default_limit(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.reset_to_defaults()
        assert svc.get("search_default_limit") == 50

    def test_set_none_value(self):
        from core.services.settings_service import SettingsService
        svc = SettingsService()
        svc.set("last_opened_source_id", None)
        assert svc.get("last_opened_source_id") is None

    def test_editor_font_defaults(self):
        from core.services.settings_service import SettingsService

        svc = SettingsService()
        svc.reset_to_defaults()
        assert svc.get("editor.fontFamily") == "Cascadia Code, Consolas, Courier New, monospace"
        assert svc.get("editor.fontLigatures") is True
        assert svc.get("editor.fontSize") == 12
