"""Unit tests cho ORM models — kiểm tra schema, relationships và constraints."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.storage.models import (
    AppSettingRow,
    Asset,
    BoardCell,
    BoardColumn,
    BoardRow,
    Extract,
    Link,
    Note,
    NoteTag,
    Source,
    Tag,
)
from core.storage.session import get_session


class TestSourceModel:
    def test_create_source(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            source = Source(
                file_path="/tmp/test.pdf",
                file_hash="abc123",
                title="Test Paper",
                created_at=now,
                updated_at=now,
            )
            session.add(source)
            session.flush()
            assert source.id is not None

    def test_source_is_not_deleted_by_default(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            source = Source(file_path="/tmp/s.pdf", file_hash="hash1", created_at=now, updated_at=now)
            session.add(source)
            session.flush()
            assert source.is_deleted == 0

    def test_source_unique_file_path(self, db_session):
        from sqlalchemy.exc import IntegrityError
        now = datetime.now(timezone.utc)
        with pytest.raises(IntegrityError):
            with get_session() as session:
                session.add(Source(file_path="/dup.pdf", file_hash="h1", created_at=now, updated_at=now))
                session.add(Source(file_path="/dup.pdf", file_hash="h2", created_at=now, updated_at=now))
                session.flush()


class TestNoteModel:
    def test_create_note_without_source(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            note = Note(
                title="My Note",
                slug="my-note",
                note_type="concept_note",
                file_path="/notes/my-note.md",
                created_at=now,
                updated_at=now,
            )
            session.add(note)
            session.flush()
            assert note.id is not None
            assert note.source_id is None

    def test_note_slug_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError
        now = datetime.now(timezone.utc)
        with pytest.raises(IntegrityError):
            with get_session() as session:
                session.add(Note(title="A", slug="same-slug", note_type="concept_note", file_path="/a.md", created_at=now, updated_at=now))
                session.add(Note(title="B", slug="same-slug", note_type="concept_note", file_path="/b.md", created_at=now, updated_at=now))
                session.flush()


class TestExtractModel:
    def test_extract_requires_source(self, db_session):
        """Extract không có source_id phải raise IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        now = datetime.now(timezone.utc)
        with pytest.raises(IntegrityError):
            with get_session() as session:
                extract = Extract(
                    source_id=9999,  # không tồn tại
                    page_no=1,
                    extract_type="text",
                    source_anchor="source://9999?page=1",
                    content_md="test",
                    created_at=now,
                    updated_at=now,
                )
                session.add(extract)
                session.flush()

    def test_extract_linked_to_source(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            src = Source(file_path="/s.pdf", file_hash="hh", created_at=now, updated_at=now)
            session.add(src)
            session.flush()
            extract = Extract(
                source_id=src.id,
                page_no=2,
                extract_type="text",
                source_anchor=f"source://{src.id}?page=2",
                content_md="> Quoted text",
                created_at=now,
                updated_at=now,
            )
            session.add(extract)
            session.flush()
            assert extract.id is not None


class TestTagAndNoteTag:
    def test_create_tag(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            tag = Tag(name="machine-learning", created_at=now)
            session.add(tag)
            session.flush()
            assert tag.id is not None

    def test_add_tag_to_note(self, db_session):
        now = datetime.now(timezone.utc)
        with get_session() as session:
            note = Note(title="N", slug="n-slug", note_type="concept_note", file_path="/n.md", created_at=now, updated_at=now)
            tag = Tag(name="ai", created_at=now)
            session.add_all([note, tag])
            session.flush()
            session.add(NoteTag(note_id=note.id, tag_id=tag.id))
            session.flush()

    def test_note_tag_unique_constraint(self, db_session):
        from sqlalchemy.exc import IntegrityError
        now = datetime.now(timezone.utc)
        with pytest.raises(IntegrityError):
            with get_session() as session:
                note = Note(title="N2", slug="n2-slug", note_type="concept_note", file_path="/n2.md", created_at=now, updated_at=now)
                tag = Tag(name="dup-tag", created_at=now)
                session.add_all([note, tag])
                session.flush()
                session.add(NoteTag(note_id=note.id, tag_id=tag.id))
                session.add(NoteTag(note_id=note.id, tag_id=tag.id))
                session.flush()


class TestAppSettings:
    def test_schema_version_seed(self, db_session):
        """Sau khi tạo schema, app_settings không tự có schema_version (chỉ migration seed)."""
        # Chỉ kiểm tra model có thể insert/query
        with get_session() as session:
            session.add(AppSettingRow(setting_key="schema_version", setting_value="1"))
            session.flush()
            result = session.query(AppSettingRow).filter_by(setting_key="schema_version").first()
            assert result is not None
            assert result.setting_value == "1"
