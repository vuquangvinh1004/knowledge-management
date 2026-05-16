"""Session factory và context manager cho SQLAlchemy sessions.

Sử dụng `get_session()` cho mọi truy cập DB từ service layer.
Không bao giờ tạo session trực tiếp trong UI.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session, sessionmaker

from core.storage.connection import get_engine
from core.utils.logger import get_logger

logger = get_logger()

_SessionFactory: sessionmaker | None = None


def init_session_factory() -> None:
    """
    Tạo session factory từ engine hiện tại.
    Gọi sau init_engine().
    """
    global _SessionFactory
    _SessionFactory = sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )
    logger.debug("Session factory khởi tạo.")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager trả về SQLAlchemy Session.

    Tự động commit khi khối lệnh thoát bình thường, rollback nếu có ngoại lệ.

    Usage::

        with get_session() as session:
            session.add(obj)
            # commit tự động khi thoát khối with
    """
    if _SessionFactory is None:
        raise RuntimeError(
            "Session factory chưa khởi tạo. Gọi init_session_factory() trước."
        )
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
