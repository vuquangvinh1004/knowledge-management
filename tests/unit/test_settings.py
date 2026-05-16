"""Unit tests cho config/settings.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from config.settings import AppSettings


class TestAppSettings:
    def test_defaults_loaded_when_no_file(self, tmp_path: Path):
        settings = AppSettings(path=tmp_path / "settings.json")
        assert settings.get("window_width") == 1280
        assert settings.get("window_height") == 800
        assert settings.get("theme") == "light"

    def test_set_and_get(self, tmp_path: Path):
        settings = AppSettings(path=tmp_path / "settings.json")
        settings.set("theme", "dark")
        assert settings.get("theme") == "dark"

    def test_save_and_reload(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        s1 = AppSettings(path=path)
        s1.set("window_width", 1920)
        s1.save()

        s2 = AppSettings(path=path)
        assert s2.get("window_width") == 1920

    def test_missing_key_returns_default(self, tmp_path: Path):
        settings = AppSettings(path=tmp_path / "settings.json")
        assert settings.get("nonexistent_key", "fallback") == "fallback"

    def test_subscript_access(self, tmp_path: Path):
        settings = AppSettings(path=tmp_path / "settings.json")
        settings["theme"] = "dark"
        assert settings["theme"] == "dark"

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        path.write_text("not valid json", encoding="utf-8")
        settings = AppSettings(path=path)
        # Defaults vẫn phải được load
        assert settings.get("window_width") == 1280
