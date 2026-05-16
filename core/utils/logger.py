"""Cấu hình logging cho ứng dụng PKM sử dụng loguru."""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path, level: str = "DEBUG") -> None:
    """
    Khởi tạo logger.

    - Console: WARNING trở lên (không rác stdout)
    - File: DEBUG trở lên, rotation theo ngày, giữ 30 ngày
    """
    logger.remove()  # Xóa handler mặc định

    # Console handler
    logger.add(
        sys.stderr,
        level="WARNING",
        format="<level>{level: <8}</level> | {message}",
        colorize=True,
    )

    # File handler
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_dir / "pkm_{time:YYYY-MM-DD}.log"),
        level=level,
        rotation="00:00",
        retention="30 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    )


def get_logger():
    """Trả về logger instance."""
    return logger
