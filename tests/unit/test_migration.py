"""Unit tests cho MigrationService và Alembic setup."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.services.migration_service import get_schema_version, run_migrations
from core.utils.exceptions import MigrationError


def _make_test_engine(db_file: Path):
    """Tạo SQLAlchemy engine cho temp DB file với FK enabled."""
    import core.storage.connection as conn_module
    from core.storage import session as session_module
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    conn_module.reset_engine()
    engine = create_engine(f"sqlite:///{db_file}?check_same_thread=False")

    @event.listens_for(engine, "connect")
    def set_fk(dbapi_conn, _):
        dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")

    conn_module._engine = engine
    session_module._SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine


def _cleanup(engine):
    """Dispose engine và reset globals."""
    import core.storage.connection as conn_module
    from core.storage import session as session_module

    engine.dispose()
    conn_module._engine = None
    session_module._SessionFactory = None


class TestMigrationService:
    def test_run_migrations_creates_schema(self, tmp_path: Path, monkeypatch):
        """Chạy migration lên DB mới — tất cả bảng phải được tạo."""
        import config.paths as paths_module
        from sqlalchemy import inspect

        db_file = tmp_path / "test_migrate.db"
        monkeypatch.setattr(paths_module, "DATABASE_FILE", db_file)
        engine = _make_test_engine(db_file)

        try:
            run_migrations()
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = [
                "sources", "notes", "extracts", "assets",
                "tags", "note_tags", "links",
                "boards", "board_rows", "board_columns", "board_cells",
                "app_settings",
            ]
            for table in required_tables:
                assert table in tables, f"Bảng {table!r} chưa được tạo sau migration."

            row_cols = {c["name"] for c in inspector.get_columns("board_rows")}
            col_cols = {c["name"] for c in inspector.get_columns("board_columns")}
            note_cols = {c["name"] for c in inspector.get_columns("notes")}
            assert "board_id" in row_cols
            assert "board_id" in col_cols
            assert "is_visible" in col_cols
            assert "meta_json" in note_cols
        finally:
            _cleanup(engine)

    def test_run_migrations_seeds_schema_version(self, tmp_path: Path, monkeypatch):
        """Migration phải seed schema_version = 1 vào app_settings."""
        import config.paths as paths_module

        db_file = tmp_path / "test_version.db"
        monkeypatch.setattr(paths_module, "DATABASE_FILE", db_file)
        engine = _make_test_engine(db_file)

        try:
            run_migrations()
            version = get_schema_version()
            assert version == 1
        finally:
            _cleanup(engine)

    def test_run_migrations_idempotent(self, tmp_path: Path, monkeypatch):
        """Chạy migration hai lần liên tiếp không được raise lỗi."""
        import config.paths as paths_module

        db_file = tmp_path / "test_idempotent.db"
        monkeypatch.setattr(paths_module, "DATABASE_FILE", db_file)
        engine = _make_test_engine(db_file)

        try:
            run_migrations()
            run_migrations()  # Lần 2 — không raise
        finally:
            _cleanup(engine)

    def test_missing_alembic_ini_raises(self, monkeypatch):
        """Thiếu alembic.ini phải raise MigrationError."""
        from core.services import migration_service
        monkeypatch.setattr(migration_service, "_ALEMBIC_INI", Path("/nonexistent/alembic.ini"))
        with pytest.raises(MigrationError, match="alembic.ini"):
            migration_service.run_migrations()

    def test_upgrade_from_0003_preserves_legacy_board_data(self, tmp_path: Path, monkeypatch):
        """DB cũ ở revision 0003 phải nâng cấp sạch lên head, không mất row/column board cũ."""
        import config.paths as paths_module
        from alembic import command
        from core.services import migration_service
        from sqlalchemy import text

        db_file = tmp_path / "test_upgrade_0003.db"
        monkeypatch.setattr(paths_module, "DATABASE_FILE", db_file)
        engine = _make_test_engine(db_file)

        try:
            cfg = migration_service._get_alembic_config()  # noqa: SLF001
            command.upgrade(cfg, "0003_add_link_weight")

            with engine.begin() as conn:
                conn.execute(text("INSERT INTO board_rows (label, sort_order) VALUES ('Legacy Row', 0)"))
                conn.execute(text("INSERT INTO board_columns (label, sort_order) VALUES ('Legacy Col', 0)"))

            command.upgrade(cfg, "head")

            with engine.begin() as conn:
                boards_count = conn.execute(text("SELECT COUNT(*) FROM boards")).scalar()
                row_check = conn.execute(
                    text("SELECT label, board_id FROM board_rows WHERE label='Legacy Row'")
                ).fetchone()
                col_check = conn.execute(
                    text("SELECT label, board_id FROM board_columns WHERE label='Legacy Col'")
                ).fetchone()

            assert boards_count >= 1
            assert row_check is not None and row_check[1] is not None
            assert col_check is not None and col_check[1] is not None
        finally:
            _cleanup(engine)

    def test_upgrade_from_0005_auto_renames_legacy_source_note_titles(self, tmp_path: Path, monkeypatch):
        """DB ở revision 0005 phải tự đổi title source_note cũ theo metadata khi nâng cấp lên head."""
        import config.paths as paths_module
        from alembic import command
        from core.services import migration_service
        from sqlalchemy import text

        db_file = tmp_path / "test_upgrade_0005.db"
        monkeypatch.setattr(paths_module, "DATABASE_FILE", db_file)
        engine = _make_test_engine(db_file)

        try:
            cfg = migration_service._get_alembic_config()  # noqa: SLF001
            command.upgrade(cfg, "0005_add_note_meta_json")

            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO sources (file_path, file_hash, title, authors, year, created_at, updated_at)
                        VALUES (:file_path, :file_hash, :title, :authors, :year, :created_at, :updated_at)
                        """
                    ),
                    {
                        "file_path": "D:/tmp/demo.pdf",
                        "file_hash": "abc123",
                        "title": "Demo",
                        "authors": "Lex Lurthor; Antomov Luska",
                        "year": "2023",
                        "created_at": "2026-04-24 00:00:00",
                        "updated_at": "2026-04-24 00:00:00",
                    },
                )
                source_id = conn.execute(text("SELECT id FROM sources LIMIT 1")).scalar()
                conn.execute(
                    text(
                        """
                        INSERT INTO notes (
                            source_id, title, slug, note_type, file_path, is_deleted, created_at, updated_at, meta_json
                        ) VALUES (
                            :source_id, :title, :slug, 'source_note', :file_path, 0, :created_at, :updated_at, :meta_json
                        )
                        """
                    ),
                    {
                        "source_id": int(source_id),
                        "title": "BiCer (2023)_C2",
                        "slug": "bicer-2023-c2",
                        "file_path": "D:/tmp/bicer-2023-c2.md",
                        "created_at": "2026-04-24 00:00:00",
                        "updated_at": "2026-04-24 00:00:00",
                        "meta_json": '{"author": "Lex Lurthor; Antomov Luska", "year": "2023"}',
                    },
                )

            command.upgrade(cfg, "head")

            with engine.begin() as conn:
                title = conn.execute(text("SELECT title FROM notes WHERE note_type='source_note'")).scalar()

            assert title == "source - Lurthor & Luska (2023)"
        finally:
            _cleanup(engine)

