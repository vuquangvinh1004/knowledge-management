"""Unit tests cho search layer: FTS index, query parser, SearchService."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Query parser
# ---------------------------------------------------------------------------

class TestQueryParser:
    def test_empty_returns_empty(self):
        from core.search.query_parser import build_fts_query
        assert build_fts_query("") == ""
        assert build_fts_query("   ") == ""

    def test_single_word_gets_wildcard(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query("python")
        assert result == "python*"

    def test_quoted_phrase_preserved(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query('"machine learning"')
        assert result == '"machine learning"'

    def test_exclusion_preserved(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query("-python")
        assert "-python" in result

    def test_multiple_words_all_wildcarded(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query("machine learning")
        assert "machine*" in result
        assert "learning*" in result

    def test_special_chars_removed(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query("hello; world!")
        # kỳ tự đặc biệt bị loại
        assert ";" not in result
        assert "!" not in result

    def test_already_wildcard_not_doubled(self):
        from core.search.query_parser import build_fts_query
        result = build_fts_query("python*")
        # Không thêm * nữa
        assert result.count("*") == 1


# ---------------------------------------------------------------------------
# FTS Index
# ---------------------------------------------------------------------------

@pytest.fixture
def fts_db(tmp_path):
    """SQLite DB đơn giản với FTS table được khởi tạo."""
    db_path = str(tmp_path / "test.db")
    from core.search.fts_index import ensure_fts_table
    ensure_fts_table(db_path)
    return db_path


class TestFTSIndex:
    def test_ensure_fts_table_creates_table(self, fts_db):
        with sqlite3.connect(fts_db) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
        assert "fts_content" in table_names

    def test_index_and_search_note(self, fts_db):
        from core.search.fts_index import index_note, search
        index_note(fts_db, 1, "Python cơ bản", "Hướng dẫn Python cho người mới", source_id=10)
        results = search(fts_db, "Python*")
        assert len(results) >= 1
        assert results[0]["entity_type"] == "note"
        assert results[0]["entity_id"] == 1

    def test_index_and_search_extract(self, fts_db):
        from core.search.fts_index import index_extract, search
        index_extract(fts_db, 5, "Machine learning là gì?", source_id=2)
        results = search(fts_db, "machine*", entity_type="extract")
        assert any(r["entity_id"] == 5 for r in results)

    def test_filter_by_entity_type(self, fts_db):
        from core.search.fts_index import index_note, index_extract, search
        index_note(fts_db, 1, "Khóa học data", "data science overview", source_id=1)
        index_extract(fts_db, 1, "data pipeline", source_id=1)
        note_results = search(fts_db, "data*", entity_type="note")
        extract_results = search(fts_db, "data*", entity_type="extract")
        assert all(r["entity_type"] == "note" for r in note_results)
        assert all(r["entity_type"] == "extract" for r in extract_results)

    def test_remove_from_index(self, fts_db):
        from core.search.fts_index import index_note, remove_from_index, search
        index_note(fts_db, 99, "Temporary", "temporary content to delete", source_id=None)
        remove_from_index(fts_db, "note", 99)
        results = search(fts_db, "temporary*")
        assert all(r["entity_id"] != 99 for r in results)

    def test_reindex_updates_content(self, fts_db):
        from core.search.fts_index import index_note, search
        index_note(fts_db, 10, "Old Title", "old content here", source_id=None)
        index_note(fts_db, 10, "New Title", "completely new content", source_id=None)
        old_results = search(fts_db, "old*")
        assert all(r["entity_id"] != 10 for r in old_results)
        new_results = search(fts_db, "new*")
        assert any(r["entity_id"] == 10 for r in new_results)

    def test_empty_query_returns_empty(self, fts_db):
        from core.search.fts_index import search
        results = search(fts_db, "")
        assert results == []

    def test_filter_by_source_id(self, fts_db):
        from core.search.fts_index import index_note, search
        index_note(fts_db, 1, "Source A Note", "content about pandas", source_id=1)
        index_note(fts_db, 2, "Source B Note", "content about pandas", source_id=2)
        results = search(fts_db, "pandas*", source_id=1)
        assert all(int(r["source_id"]) == 1 for r in results)


# ---------------------------------------------------------------------------
# SearchService
# ---------------------------------------------------------------------------

class TestSearchService:
    def test_search_returns_results(self, db_session, notes_dir, sample_pdf_path):
        from core.services.source_service import SourceService
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService
        from config.paths import DATABASE_FILE

        src = SourceService().import_source(sample_pdf_path, title="Search Test PDF")
        note_svc = NoteService(notes_dir)
        note = note_svc.create_note("Search Test Note", "source_note", src.id)
        note_svc.save_content(note.id, "Kỹ thuật machine learning trong Python")

        svc = SearchService(str(DATABASE_FILE), notes_dir)
        svc.index_note_by_id(note.id)

        results = svc.search("machine")
        matched = next((r for r in results if r.entity_id == note.id), None)
        assert matched is not None
        assert matched.entity_public_id == note.public_id
        assert matched.source_public_id == src.public_id

    def test_search_empty_query_returns_empty(self, db_session, notes_dir):
        from core.services.search_service import SearchService
        from config.paths import DATABASE_FILE
        svc = SearchService(str(DATABASE_FILE), notes_dir)
        assert svc.search("") == []

    def test_rebuild_all(self, db_session, notes_dir, sample_pdf_path):
        from core.services.source_service import SourceService
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService
        from config.paths import DATABASE_FILE

        SourceService().import_source(sample_pdf_path, title="Rebuild PDF")
        note_svc = NoteService(notes_dir)
        note_svc.create_note("Rebuild Note", "concept_note")

        svc = SearchService(str(DATABASE_FILE), notes_dir)
        count = svc.rebuild_all()
        assert count >= 1

    def test_list_orphan_note_ids(self, db_session, notes_dir):
        from config.paths import DATABASE_FILE
        from core.services.link_service import LinkService
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService

        note_svc = NoteService(notes_dir)
        orphan = note_svc.create_note("Orphan Node", "concept_note")
        n1 = note_svc.create_note("Linked A", "concept_note")
        n2 = note_svc.create_note("Linked B", "concept_note")
        LinkService().create_link(n1.id, n2.id, "wikilink")

        svc = SearchService(str(DATABASE_FILE), notes_dir)
        orphan_ids = svc.list_orphan_note_ids()
        assert orphan.id in orphan_ids
        assert n1.id not in orphan_ids
        assert n2.id not in orphan_ids


# ---------------------------------------------------------------------------
# SearchService project filter (Sprint 7B)
# ---------------------------------------------------------------------------

class TestSearchServiceProjectFilter:
    def test_search_with_project_note_ids_filters_results(self, db_session, notes_dir):
        from config.paths import DATABASE_FILE
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService

        note_svc = NoteService(notes_dir)
        included = note_svc.create_note("Project Alpha Note", "concept_note",
                                        initial_content="# Project Alpha Note\n\nAlpha keyword")
        excluded = note_svc.create_note("Global Beta Note", "concept_note",
                                        initial_content="# Global Beta Note\n\nAlpha keyword")

        svc = SearchService(str(DATABASE_FILE), notes_dir)
        svc.index_note_by_id(included.id)
        svc.index_note_by_id(excluded.id)

        # Không filter → trả cả 2
        all_results = svc.search("Alpha")
        all_ids = {r.entity_id for r in all_results if r.entity_type == "note"}
        assert included.id in all_ids
        assert excluded.id in all_ids

        # Filter project_note_ids → chỉ trả included
        filtered = svc.search("Alpha", project_note_ids={included.id})
        filtered_ids = {r.entity_id for r in filtered if r.entity_type == "note"}
        assert included.id in filtered_ids
        assert excluded.id not in filtered_ids

    def test_search_project_filter_empty_set_returns_no_notes(self, db_session, notes_dir):
        from config.paths import DATABASE_FILE
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService

        note_svc = NoteService(notes_dir)
        note = note_svc.create_note("Filter Empty Test", "concept_note",
                                    initial_content="# Filter Empty Test\n\nkeyword")
        svc = SearchService(str(DATABASE_FILE), notes_dir)
        svc.index_note_by_id(note.id)

        results = svc.search("keyword", project_note_ids=set())
        note_results = [r for r in results if r.entity_type == "note"]
        assert len(note_results) == 0

    def test_search_without_project_filter_behaves_as_before(self, db_session, notes_dir):
        """project_note_ids=None không thay đổi hành vi cũ."""
        from config.paths import DATABASE_FILE
        from core.services.note_service import NoteService
        from core.services.search_service import SearchService

        note_svc = NoteService(notes_dir)
        note = note_svc.create_note("No Filter Test", "concept_note",
                                    initial_content="# No Filter Test\n\nunique_token_xyz")
        svc = SearchService(str(DATABASE_FILE), notes_dir)
        svc.index_note_by_id(note.id)

        results = svc.search("unique_token_xyz", project_note_ids=None)
        ids = {r.entity_id for r in results if r.entity_type == "note"}
        assert note.id in ids
