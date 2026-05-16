"""Unit tests cho core/app_kernel/app_lock.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.app_kernel.app_lock import AppLock
from core.utils.exceptions import AppLockError


class TestAppLock:
    def test_acquire_creates_lock_file(self, tmp_path: Path):
        lock_file = tmp_path / "test.lock"
        lock = AppLock(lock_file)
        lock.acquire()
        assert lock_file.exists()
        lock.release()

    def test_lock_file_contains_pid(self, tmp_path: Path):
        import os
        lock_file = tmp_path / "test.lock"
        lock = AppLock(lock_file)
        lock.acquire()
        pid = int(lock_file.read_text())
        assert pid == os.getpid()
        lock.release()

    def test_release_removes_lock_file(self, tmp_path: Path):
        lock_file = tmp_path / "test.lock"
        lock = AppLock(lock_file)
        lock.acquire()
        lock.release()
        assert not lock_file.exists()

    def test_context_manager(self, tmp_path: Path):
        lock_file = tmp_path / "test.lock"
        with AppLock(lock_file) as lock:
            assert lock_file.exists()
        assert not lock_file.exists()

    def test_stale_lock_file_ignored(self, tmp_path: Path):
        """Lock file với PID không tồn tại phải được bỏ qua."""
        lock_file = tmp_path / "test.lock"
        # Ghi một PID không tồn tại
        lock_file.write_text("99999999", encoding="utf-8")
        lock = AppLock(lock_file)
        # Không nên raise — stale lock phải được dọn
        lock.acquire()
        lock.release()

    def test_double_release_safe(self, tmp_path: Path):
        lock_file = tmp_path / "test.lock"
        lock = AppLock(lock_file)
        lock.acquire()
        lock.release()
        lock.release()  # Không được raise
