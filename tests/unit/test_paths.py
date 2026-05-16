"""Unit tests cho config/paths.py."""
from __future__ import annotations

from pathlib import Path

import pytest


class TestPaths:
    def test_base_dir_is_path(self):
        from config.paths import BASE_DIR
        assert isinstance(BASE_DIR, Path)

    def test_data_dirs_under_base(self):
        from config.paths import DATA_DIR, SOURCES_DIR, NOTES_DIR, BASE_DIR
        assert DATA_DIR.is_relative_to(BASE_DIR)
        assert SOURCES_DIR.is_relative_to(DATA_DIR)
        assert NOTES_DIR.is_relative_to(DATA_DIR)

    def test_database_file_under_data(self):
        from config.paths import DATABASE_FILE, DATA_DIR
        assert DATABASE_FILE.is_relative_to(DATA_DIR)

    def test_lock_file_under_temp(self):
        from config.paths import LOCK_FILE, TEMP_DIR
        assert LOCK_FILE.is_relative_to(TEMP_DIR)

    def test_ensure_data_dirs_creates_directories(self, tmp_path: Path, monkeypatch):
        """ensure_data_dirs() phải tạo tất cả thư mục."""
        import config.paths as paths_module
        # Redirect tất cả DATA_DIRS sang tmp_path
        test_dirs = [tmp_path / name for name in [
            "data", "sources", "notes", "assets",
            "exports", "backups", "logs", "temp", "database"
        ]]
        monkeypatch.setattr(paths_module, "DATA_DIRS", test_dirs)
        paths_module.ensure_data_dirs()
        for d in test_dirs:
            assert d.exists(), f"{d} phải được tạo"
