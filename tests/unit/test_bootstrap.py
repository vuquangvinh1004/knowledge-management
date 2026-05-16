"""Unit tests cho core/app_kernel/bootstrap.py và startup_checks.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.utils.exceptions import AppLockError, ConfigError


class TestStartupChecks:
    def test_check_python_version_passes(self):
        """Python đang dùng phải >= 3.11."""
        from core.app_kernel.startup_checks import check_python_version
        check_python_version()  # Không raise

    def test_check_python_version_fails_old_version(self, monkeypatch):
        import sys
        from core.app_kernel.startup_checks import check_python_version
        monkeypatch.setattr(sys, "version_info", (3, 10, 0))
        with pytest.raises(ConfigError, match="3.11"):
            check_python_version()

    def test_check_data_dirs_passes_when_dirs_exist(self, tmp_path: Path, monkeypatch):
        """check_data_dirs() pass khi patch trực tiếp vào module startup_checks."""
        from core.app_kernel import startup_checks
        monkeypatch.setattr(startup_checks, "SOURCES_DIR", tmp_path / "sources")
        monkeypatch.setattr(startup_checks, "NOTES_DIR", tmp_path / "notes")
        monkeypatch.setattr(startup_checks, "ASSETS_DIR", tmp_path / "assets")
        monkeypatch.setattr(startup_checks, "DATABASE_DIR", tmp_path / "database")
        for attr in ["SOURCES_DIR", "NOTES_DIR", "ASSETS_DIR", "DATABASE_DIR"]:
            getattr(startup_checks, attr).mkdir(parents=True, exist_ok=True)
        startup_checks.check_data_dirs()  # Không raise

    def test_check_data_dirs_fails_when_missing(self, tmp_path: Path, monkeypatch):
        """check_data_dirs() raise ConfigError khi thư mục thiếu."""
        from core.app_kernel import startup_checks
        monkeypatch.setattr(startup_checks, "SOURCES_DIR", tmp_path / "no_sources")
        monkeypatch.setattr(startup_checks, "NOTES_DIR", tmp_path / "no_notes")
        monkeypatch.setattr(startup_checks, "ASSETS_DIR", tmp_path / "no_assets")
        monkeypatch.setattr(startup_checks, "DATABASE_DIR", tmp_path / "no_db")
        with pytest.raises(ConfigError, match="Thiếu thư mục"):
            startup_checks.check_data_dirs()

    def test_check_dependencies_soft_dep_missing_returns_list(self, monkeypatch):
        """Soft dep thiếu phải trả về danh sách, không raise."""
        from core.app_kernel import startup_checks
        monkeypatch.setattr(startup_checks, "_HARD_DEPS", {})
        monkeypatch.setattr(startup_checks, "_SOFT_DEPS", {"_nonexistent_pkg_xyz": "Gói test"})
        _, missing_soft = startup_checks.check_dependencies()
        assert "Gói test" in missing_soft

    def test_check_dependencies_hard_dep_missing_raises(self, monkeypatch):
        """Hard dep thiếu phải raise ConfigError."""
        from core.app_kernel import startup_checks
        monkeypatch.setattr(startup_checks, "_HARD_DEPS", {"_nonexistent_pkg_xyz": "Gói bắt buộc"})
        monkeypatch.setattr(startup_checks, "_SOFT_DEPS", {})
        with pytest.raises(ConfigError, match="bắt buộc"):
            startup_checks.check_dependencies()

    def test_run_all_checks_returns_list(self, tmp_path: Path, monkeypatch):
        """run_all_checks() phải trả về list."""
        from core.app_kernel import startup_checks
        for attr in ["SOURCES_DIR", "NOTES_DIR", "ASSETS_DIR", "DATABASE_DIR"]:
            d = tmp_path / attr.lower()
            d.mkdir()
            monkeypatch.setattr(startup_checks, attr, d)
        # Không cần thật sự pass tất cả deps — chỉ check return type
        monkeypatch.setattr(startup_checks, "_HARD_DEPS", {})
        monkeypatch.setattr(startup_checks, "_SOFT_DEPS", {})
        result = startup_checks.run_all_checks()
        assert isinstance(result, list)


class TestShutdownManager:
    def test_handlers_called_in_order(self):
        from core.app_kernel.shutdown_manager import ShutdownManager
        call_order = []
        manager = ShutdownManager()
        manager.register(lambda: call_order.append(1))
        manager.register(lambda: call_order.append(2))
        manager.run()
        assert call_order == [1, 2]

    def test_failed_handler_does_not_stop_others(self):
        """Handler lỗi không được chặn các handler sau."""
        from core.app_kernel.shutdown_manager import ShutdownManager
        call_order = []

        def failing_handler():
            raise RuntimeError("handler lỗi")

        manager = ShutdownManager()
        manager.register(failing_handler)
        manager.register(lambda: call_order.append("second"))
        manager.run()  # Không raise
        assert "second" in call_order

    def test_empty_manager_runs_safely(self):
        from core.app_kernel.shutdown_manager import ShutdownManager
        ShutdownManager().run()  # Không raise khi không có handler

