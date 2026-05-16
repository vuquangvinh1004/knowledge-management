"""Fixtures dùng chung cho toàn bộ test suite."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Thư mục tạm cho từng test."""
    return tmp_path


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Tạo file PDF mẫu tối thiểu cho test."""
    sample = tmp_path / "sample.pdf"
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 100), "Sample PDF for testing")
        doc.save(str(sample))
        doc.close()
    except ImportError:
        sample.write_bytes(b"%PDF-1.4")
    return sample


@pytest.fixture
def mock_settings(tmp_path: Path):
    """AppSettings dùng thư mục tạm cho test."""
    from config.settings import AppSettings
    return AppSettings(path=tmp_path / "test_settings.json")


# ---------------------------------------------------------------------------
# Database fixtures cho Phase 2 tests
# ---------------------------------------------------------------------------

@pytest.fixture
def db_engine(tmp_path: Path):
    """
    SQLAlchemy engine dùng SQLite in-memory (per test).
    Tự động tạo schema và dọn dẹp sau mỗi test.
    """
    import core.storage.connection as conn_module
    from sqlalchemy import create_engine, event
    from core.storage.models import Base

    # Reset global engine để tránh xung đột giữa các tests
    conn_module.reset_engine()

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Bật foreign keys
    @event.listens_for(engine, "connect")
    def set_fk(dbapi_conn, _):
        dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")

    # Tạo tất cả bảng
    Base.metadata.create_all(engine)

    # Gán engine vào global để get_engine() hoạt động
    conn_module._engine = engine

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()
    conn_module._engine = None


@pytest.fixture
def db_session(db_engine):
    """
    SQLAlchemy session factory được khởi tạo với db_engine.
    Sử dụng cùng với get_session() context manager.
    """
    import core.storage.session as session_module
    from sqlalchemy.orm import sessionmaker

    session_module._SessionFactory = sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )
    yield session_module._SessionFactory

    session_module._SessionFactory = None


@pytest.fixture
def notes_dir(tmp_path: Path) -> Path:
    """Thư mục tạm cho markdown notes."""
    d = tmp_path / "notes"
    d.mkdir()
    return d


@pytest.fixture
def sources_dir(tmp_path: Path) -> Path:
    """Thư mục tạm cho source PDFs."""
    d = tmp_path / "sources"
    d.mkdir()
    return d

