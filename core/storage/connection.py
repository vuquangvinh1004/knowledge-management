"""Database engine và khởi tạo schema.

Engine được tạo một lần duy nhất thông qua `init_engine()` rồi có thể truy cập
toàn cục qua `get_engine()`. Không tạo engine nhiều lần cho cùng một DB.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from core.utils.logger import get_logger

logger = get_logger()

_engine: Engine | None = None


def _enforce_foreign_keys(dbapi_conn, connection_record) -> None:  # noqa: ANN001
    """Bật PRAGMA foreign_keys cho mọi connection mới."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_engine(db_path: Path) -> Engine:
    """
    Tạo và cấu hình SQLAlchemy engine cho SQLite.

    Gọi một lần duy nhất khi khởi động app. Lưu engine vào _engine global.

    Args:
        db_path: Đường dẫn đến file .db của SQLite.

    Returns:
        SQLAlchemy Engine đã cấu hình.
    """
    global _engine
    if _engine is not None:
        logger.warning("init_engine() được gọi nhiều lần — trả về engine hiện có.")
        return _engine

    url = f"sqlite:///{db_path}?check_same_thread=False"
    engine = create_engine(
        url,
        echo=False,
        connect_args={"timeout": 15},
    )
    # Bật foreign key enforcement cho mọi kết nối SQLite
    event.listen(engine, "connect", _enforce_foreign_keys)

    _engine = engine
    logger.info(f"Database engine khởi tạo: {db_path}")
    return engine


def get_engine() -> Engine:
    """
    Lấy engine hiện tại.

    Raises:
        RuntimeError: Nếu init_engine() chưa được gọi.
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine chưa khởi tạo. Gọi init_engine() trước."
        )
    return _engine


def reset_engine() -> None:
    """Dispose engine và reset về None (dùng trong tests)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
