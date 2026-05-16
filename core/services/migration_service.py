"""Service quản lý migration schema database.

Chạy Alembic programmatically từ bên trong ứng dụng.
Nếu migration thất bại, raise MigrationError để app dừng an toàn.
"""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text

from core.storage.connection import get_engine
from core.utils.exceptions import MigrationError
from core.utils.logger import get_logger

logger = get_logger()

# Vị trí alembic.ini tính từ project root
_ALEMBIC_INI: Path = Path(__file__).parent.parent.parent / "alembic.ini"


def _get_alembic_config() -> Config:
    """Tạo Alembic Config từ alembic.ini."""
    if not _ALEMBIC_INI.exists():
        raise MigrationError(f"Không tìm thấy alembic.ini tại: {_ALEMBIC_INI}")
    cfg = Config(str(_ALEMBIC_INI))
    return cfg


def run_migrations() -> None:
    """
    Chạy tất cả migration chưa áp dụng lên DB hiện tại.

    Raises:
        MigrationError: Nếu migration thất bại.
    """
    try:
        logger.info("Bắt đầu chạy database migrations...")
        cfg = _get_alembic_config()
        command.upgrade(cfg, "head")
        logger.info("Database migrations hoàn tất.")
    except MigrationError:
        raise
    except Exception as exc:
        raise MigrationError(f"Migration thất bại: {exc}") from exc


def get_current_revision() -> str | None:
    """
    Lấy revision hiện tại của DB.

    Returns:
        Revision ID dạng chuỗi, hoặc None nếu DB chưa có migration.
    """
    engine = get_engine()
    with engine.connect() as conn:
        migration_context = MigrationContext.configure(conn)
        return migration_context.get_current_revision()


def get_schema_version() -> int:
    """
    Lấy schema_version từ bảng app_settings.

    Returns:
        Số nguyên schema version, mặc định 0 nếu chưa có.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT setting_value FROM app_settings WHERE setting_key = 'schema_version'")
            )
            row = result.fetchone()
            return int(row[0]) if row else 0
    except Exception as exc:
        logger.warning(f"Không thể đọc schema_version: {exc}")
        return 0


def verify_schema_version(expected: int) -> None:
    """
    Kiểm tra schema_version trong DB khớp với version app mong đợi.

    Raises:
        MigrationError: Nếu version không khớp.
    """
    current = get_schema_version()
    if current != expected:
        raise MigrationError(
            f"Schema version không khớp. App cần version {expected}, DB có version {current}. "
            "Chạy migration để cập nhật."
        )
    logger.debug(f"Schema version OK: {current}")
