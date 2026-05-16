"""Single-instance lock ngăn ứng dụng mở nhiều instance ghi cùng database.

Dùng lock file tại data/temp/research_pkm.lock.
Ghi PID vào file khi acquire; xóa file khi release.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from core.utils.exceptions import AppLockError
from core.utils.logger import get_logger

logger = get_logger()


class AppLock:
    """
    Quản lý single-instance lock dùng lock file.

    Khi acquire thành công, ghi PID vào file lock.
    Khi release, xóa file lock.
    """

    def __init__(self, lock_file: Path) -> None:
        self._lock_file = lock_file
        self._acquired = False

    def acquire(self) -> None:
        """
        Cố gắng lấy lock.
        Nếu lock file tồn tại và process tương ứng còn chạy → raise AppLockError.
        """
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)

        if self._lock_file.exists():
            existing_pid = self._read_pid()
            if existing_pid is not None and _is_process_running(existing_pid):
                logger.warning(
                    f"Ứng dụng đã chạy tại PID {existing_pid}. Không thể mở instance mới."
                )
                raise AppLockError(
                    f"Ứng dụng đang chạy (PID {existing_pid}). "
                    "Vui lòng đóng instance hiện tại trước khi mở lại."
                )
            else:
                # Stale lock file — process cũ đã chết
                logger.info(f"Phát hiện stale lock file (PID {existing_pid}), bỏ qua.")
                self._lock_file.unlink(missing_ok=True)

        self._write_pid(os.getpid())
        self._acquired = True
        logger.debug(f"App lock acquired (PID {os.getpid()}): {self._lock_file}")

    def release(self) -> None:
        """Giải phóng lock và xóa lock file."""
        if self._acquired and self._lock_file.exists():
            self._lock_file.unlink(missing_ok=True)
            self._acquired = False
            logger.debug("App lock released.")

    def _read_pid(self) -> int | None:
        try:
            return int(self._lock_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            return None

    def _write_pid(self, pid: int) -> None:
        self._lock_file.write_text(str(pid), encoding="utf-8")

    def __enter__(self) -> "AppLock":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()


def _is_process_running(pid: int) -> bool:
    """Kiểm tra PID còn hoạt động không (cross-platform)."""
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if handle == 0:
            return False
        exit_code = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        STILL_ACTIVE = 259
        return exit_code.value == STILL_ACTIVE
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
