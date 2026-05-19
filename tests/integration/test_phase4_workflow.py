"""Integration tests cho Phase 4: Search, Board, Export workflow."""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def source_service(db_session):
    from core.services.source_service import SourceService
    return SourceService()


@pytest.fixture
def note_service(db_session, notes_dir):
    from core.services.note_service import NoteService
    return NoteService(notes_dir)


@pytest.fixture
def board_service(db_session):
    from core.services.board_service import BoardService
    return BoardService()


@pytest.fixture
def export_service(tmp_path, db_session):
    from core.services.export_service import ExportService
    return ExportService(tmp_path / "exports")


@pytest.fixture
def search_service(db_session, notes_dir):
    from core.services.search_service import SearchService
    from config.paths import DATABASE_FILE
    return SearchService(str(DATABASE_FILE), notes_dir)


# ---------------------------------------------------------------------------
# Search integration
# ---------------------------------------------------------------------------

class TestSearchWorkflow:
    def test_index_after_create_and_search(
        self, source_service, note_service, search_service, sample_pdf_path
    ):
        src = source_service.import_source(sample_pdf_path, title="FTS PDF")
        note = note_service.create_note("FTS Note", "source_note", src.id)
        note_service.save_content(note.id, "Kiến trúc phần mềm vi dịch vụ")

        search_service.index_note_by_id(note.id)
        results = search_service.search("vi dịch vụ")
        assert any(r.entity_id == note.id for r in results)

    def test_rebuild_indexes_all(
        self, source_service, note_service, search_service, sample_pdf_path
    ):
        src = source_service.import_source(sample_pdf_path, title="Rebuild FTS PDF")
        note_service.create_note("Rebuild Note", "source_note", src.id)
        count = search_service.rebuild_all()
        assert count >= 1

    def test_search_no_match_returns_empty(self, search_service):
        results = search_service.search("xyzzyabcdef123")
        assert results == []


# ---------------------------------------------------------------------------
# Board integration
# ---------------------------------------------------------------------------

class TestBoardWorkflow:
    def test_create_board_and_fill_cell(
        self, board_service, source_service, note_service, sample_pdf_path
    ):
        src = source_service.import_source(sample_pdf_path, title="Board PDF")
        note = note_service.create_note("Board Note", "source_note", src.id)

        row = board_service.create_row(src.title)
        col = board_service.create_column("Tóm tắt")
        cell = board_service.update_cell(
            row.id, col.id,
            content_md="Tóm tắt tài liệu nguồn.",
            linked_note_id=note.id,
        )
        assert cell.linked_note_id == note.id
        assert cell.content_md == "Tóm tắt tài liệu nguồn."

    def test_board_export_markdown(self, board_service):
        board_service.create_row("Tài liệu A")
        board_service.create_column("Góc nhìn lý thuyết")
        md = board_service.export_markdown()
        assert "Tài liệu A" in md
        assert "Góc nhìn lý thuyết" in md

    def test_board_export_csv(self, board_service):
        board_service.create_row("Row CSV")
        board_service.create_column("Col CSV")
        csv_str = board_service.export_csv()
        assert "Row CSV" in csv_str
        assert "Col CSV" in csv_str


# ---------------------------------------------------------------------------
# Export integration
# ---------------------------------------------------------------------------

class TestExportWorkflow:
    def test_export_source_bundle(
        self, source_service, note_service, export_service, notes_dir, sample_pdf_path
    ):
        src = source_service.import_source(
            sample_pdf_path, title="Export Test PDF", authors="Author A", year="2024"
        )
        note = note_service.create_note("Export Test Note", "source_note", src.id)
        note_service.save_content(note.id, "## Ghi chú\nNội dung nghiên cứu.")

        output = export_service.export_source_bundle(src.id, notes_dir)
        assert output.exists()
        text = output.read_text(encoding="utf-8")
        assert "Export Test PDF" in text
        assert "Nội dung nghiên cứu" in text
        assert "**Public ID:**" in text
        assert src.public_id in text

    def test_export_source_bundle_not_found_raises(self, export_service, notes_dir):
        from core.utils.exceptions import PKMError
        with pytest.raises(PKMError):
            export_service.export_source_bundle(99999, notes_dir)

    def test_export_board_markdown_file(self, export_service):
        from core.services.board_service import BoardService
        svc = BoardService()
        svc.create_row("Row 1")
        svc.create_column("Col 1")
        path = export_service.export_board_markdown()
        assert path.exists()
        assert path.suffix == ".md"

    def test_export_board_csv_file(self, export_service):
        from core.services.board_service import BoardService
        svc = BoardService()
        svc.create_row("Row CSV")
        svc.create_column("Col CSV")
        path = export_service.export_board_csv()
        assert path.exists()
        assert path.suffix == ".csv"
