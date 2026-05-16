"""Quản lý quá trình tắt ứng dụng một cách an toàn.

Đảm bảo autosave, release lock và ghi log trước khi thoát.
"""
from __future__ import annotations

from typing import Callable

from core.utils.logger import get_logger

logger = get_logger()


class ShutdownManager:
    """Quản lý danh sách handler được gọi khi ứng dụng tắt."""

    def __init__(self) -> None:
        self._handlers: list[Callable] = []

    def register(self, handler: Callable) -> None:
        """[Đăng ký một callable được gọi khi shutdown."""
        self._handlers.append(handler)

    def run(self) -> None:
        """Thực thi tất cả shutdown handlers theo thứ tự đăng ký."""
        logger.info("Bắt đầu shutdown sequence...")
        for handler in self._handlers:
            try:
                handler()
            except Exception as exc:
                logger.error(f"Lỗi trong shutdown handler {handler}: {exc}")
        logger.info("Shutdown hoàn tất.")
