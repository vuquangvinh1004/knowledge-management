"""Cấu hình kết nối database SQLite.

Chỉ cung cấp thông tin cấu hình.
Engine và session được tạo tại core/storage/connection.py.
"""
from pathlib import Path

from config.paths import DATABASE_FILE


def get_database_url(path: Path = DATABASE_FILE) -> str:
    """Trả về SQLAlchemy database URL cho SQLite."""
    # check_same_thread=False cần thiết cho multi-thread access
    return f"sqlite:///{path}?check_same_thread=False"
