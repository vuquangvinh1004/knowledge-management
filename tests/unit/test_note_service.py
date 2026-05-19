"""Unit tests cho NoteService."""
from __future__ import annotations

import pytest

from core.services.note_service import NoteService
from core.utils.exceptions import NoteNotFoundError, PKMError


@pytest.fixture
def service(notes_dir):
    return NoteService(notes_dir=notes_dir)


class TestCreateNote:
    def test_create_concept_note(self, service, db_session):
        note = service.create_note(title="Machine Learning", note_type="concept_note")
        assert note.id is not None
        assert note.slug == "machine-learning"
        assert note.note_type == "concept_note"

    def test_create_note_creates_markdown_file(self, service, db_session, notes_dir):
        note = service.create_note(title="Test Note", note_type="concept_note", initial_content="# Hello")
        assert (notes_dir / f"{note.slug}.md").exists()

    def test_invalid_note_type_raises(self, service, db_session):
        with pytest.raises(PKMError, match="note_type"):
            service.create_note(title="X", note_type="invalid_type")

    def test_duplicate_source_note_raises(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService
        src = SourceService().import_source(sample_pdf_path)
        service.create_note(title="Source Note 1", note_type="source_note", source_id=src.id)
        with pytest.raises(PKMError, match="source_note"):
            service.create_note(title="Source Note 2", note_type="source_note", source_id=src.id)

    def test_source_note_requires_source_id(self, service, db_session):
        with pytest.raises(PKMError, match="source_id"):
            service.create_note(title="source Unknown 2020", note_type="source_note")

    def test_slug_collision_gets_suffix(self, service, db_session):
        note1 = service.create_note(title="Deep Learning", note_type="concept_note")
        note2 = service.create_note(title="Deep Learning", note_type="concept_note")
        assert note1.slug == "deep-learning"
        assert note2.slug == "deep-learning-2"


class TestReadWriteContent:
    def test_read_content(self, service, db_session):
        note = service.create_note(title="Read Test", note_type="concept_note", initial_content="Hello World")
        content = service.read_content(note.id)
        assert content == "Hello World"

    def test_save_content(self, service, db_session):
        note = service.create_note(title="Save Test", note_type="concept_note")
        service.save_content(note.id, "# New Content\n\nParagraph.")
        assert service.read_content(note.id) == "# New Content\n\nParagraph."

    def test_default_template_is_applied_when_initial_content_empty(self, service, db_session):
        note = service.create_note(title="SCCT", note_type="concept_note")
        content = service.read_content(note.id)
        assert "# Concept - SCCT" in content
        assert "## Định nghĩa" in content

    def test_source_note_template_contains_metadata_callouts(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService

        src = SourceService().import_source(sample_pdf_path)
        note = service.create_note(title="source - Template Metadata", note_type="source_note", source_id=src.id)
        content = service.read_content(note.id)

        assert "## Metadata" in content
        assert "> [!TÁC GIẢ]" in content
        assert "> [!NĂM]" in content
        assert "Thông tin tiêu chí." not in content


class TestNoteTitleWarnings:
    def test_title_warning_for_generic_title(self):
        warnings = NoteService.title_warnings("concept_note", "note moi")
        assert any("chung chung" in w for w in warnings)

    def test_title_warning_for_board_prefix(self):
        warnings = NoteService.title_warnings("board_note", "Meta board")
        assert any("board_note" in w for w in warnings)

    def test_title_warning_for_synthesis_marker(self):
        warnings = NoteService.title_warnings("synthesis_note", "Tong hop chu de")
        assert any("synthesis_note" in w for w in warnings)


class TestNoteMetadata:
    def test_update_meta_source_note(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService

        src = SourceService().import_source(sample_pdf_path)
        note = service.create_note("source Test 2024", "source_note", source_id=src.id)
        service.update_meta(note.id, {"author": "Lent", "year": "1994", "source_type": "journal"})
        meta = service.get_meta(note.id)
        assert meta.get("author") == "Lent"
        assert meta.get("year") == "1994"

    def test_update_meta_invalid_source_year_raises(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService

        src = SourceService().import_source(sample_pdf_path)
        note = service.create_note("source Test", "source_note", source_id=src.id)
        with pytest.raises(PKMError, match="year"):
            service.update_meta(note.id, {"author": "A", "year": "20A4"})

    def test_update_meta_board_source_count_casts_int(self, service, db_session):
        note = service.create_note("board test", "board_note")
        service.update_meta(note.id, {"board_type": "literature", "source_count": "12"})
        meta = service.get_meta(note.id)
        assert meta.get("source_count") == 12


class TestGetNote:
    def test_get_by_id(self, service, db_session):
        note = service.create_note(title="Find Me", note_type="synthesis_note")
        fetched = service.get_by_id(note.id)
        assert fetched.title == "Find Me"

    def test_get_nonexistent_raises(self, service, db_session):
        with pytest.raises(NoteNotFoundError):
            service.get_by_id(9999)

    def test_get_by_slug(self, service, db_session):
        note = service.create_note(title="Slug Test", note_type="concept_note")
        fetched = service.get_by_slug(note.slug)
        assert fetched.id == note.id

    def test_get_source_note(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService
        src = SourceService().import_source(sample_pdf_path)
        note = service.create_note(title="Source Note", note_type="source_note", source_id=src.id)
        found = service.get_source_note(src.id)
        assert found is not None
        assert found.id == note.id


class TestDeleteNote:
    def test_soft_delete(self, service, db_session):
        note = service.create_note(title="Delete Me", note_type="concept_note")
        service.soft_delete(note.id)
        with pytest.raises(NoteNotFoundError):
            service.get_by_id(note.id)

    def test_hard_delete_removes_file(self, service, db_session, notes_dir):
        from pathlib import Path
        note = service.create_note(title="Hard Delete", note_type="concept_note")
        file_path = Path(note.file_path)
        assert file_path.exists()
        service.hard_delete(note.id, delete_file=True)
        assert not file_path.exists()

    def test_hard_delete_note_with_links_does_not_fail(self, service, db_session):
        from core.services.link_service import LinkService
        from core.storage.session import get_session
        from core.storage.models import Link

        target = service.create_note(title="Target", note_type="concept_note")
        other = service.create_note(title="Other", note_type="concept_note")
        LinkService().create_link(other.id, target.id, "wikilink")

        service.hard_delete(target.id, delete_file=True)

        with pytest.raises(NoteNotFoundError):
            service.get_by_id(target.id)

        with get_session() as session:
            remains = session.query(Link).filter(
                (Link.from_note_id == target.id) | (Link.to_note_id == target.id)
            ).count()
        assert remains == 0


class TestNoteMaintenance:
    def test_normalize_source_note_titles_is_idempotent(self, service, db_session, sample_pdf_path):
        from core.services.source_service import SourceService

        src = SourceService().import_source(
            sample_pdf_path,
            authors="Lex Lurthor; Antomov Luska",
            year="2023",
        )
        note = service.create_note("legacy file title", "source_note", source_id=src.id)

        changed = service.normalize_source_note_titles()
        assert changed == 1

        refreshed = service.get_by_id(note.id)
        assert refreshed.title == "source - Lurthor & Luska (2023)"

        changed_again = service.normalize_source_note_titles()
        assert changed_again == 0

    def test_refresh_wikilink_note_catalog_soft_deletes_missing_file(self, service, db_session):
        note = service.create_note("Temp Note", "concept_note")
        from pathlib import Path
        Path(note.file_path).unlink(missing_ok=True)

        stats = service.refresh_wikilink_note_catalog()
        assert stats["soft_deleted_missing_file"] >= 1

        with pytest.raises(NoteNotFoundError):
            service.get_by_id(note.id)

    def test_refresh_wikilink_note_catalog_removes_orphan_stub_notes(self, service, db_session):
        concept = service.create_note("Khái niệm mới", "concept_note", initial_content="# Khái niệm mới\n")
        synth = service.create_note("~ alehap", "synthesis_note", initial_content="# ~ alehap\n")
        board = service.create_note("! board tạm", "board_note", initial_content="# ! board tạm\n")

        stats = service.refresh_wikilink_note_catalog()
        assert stats["removed_orphan_stub_notes"] >= 3

        with pytest.raises(NoteNotFoundError):
            service.get_by_id(concept.id)
        with pytest.raises(NoteNotFoundError):
            service.get_by_id(synth.id)
        with pytest.raises(NoteNotFoundError):
            service.get_by_id(board.id)

    def test_get_unused_note_candidates_includes_missing_file_and_orphan(self, service, db_session):
        missing = service.create_note("Missing candidate", "concept_note")
        orphan = service.create_note("Orphan candidate", "concept_note", initial_content="# Ghi chu goc\n")

        from pathlib import Path
        Path(missing.file_path).unlink(missing_ok=True)

        candidates = service.get_unused_note_candidates()
        by_id = {int(c["note_id"]): c for c in candidates}

        assert missing.id in by_id
        assert by_id[missing.id]["reason"] == "missing-file"

        assert orphan.id in by_id
        assert by_id[orphan.id]["reason"] == "orphan-no-link"

    def test_cleanup_unused_notes_only_applies_selected_note_ids(self, service, db_session):
        keep_note = service.create_note("Keep me", "concept_note", initial_content="# Keep me\n")
        delete_note = service.create_note("Delete me", "concept_note", initial_content="# Delete me\n")

        stats = service.cleanup_unused_notes({delete_note.id})
        assert stats["soft_deleted"] == 1

        with pytest.raises(NoteNotFoundError):
            service.get_by_id(delete_note.id)

        kept = service.get_by_id(keep_note.id)
        assert kept.id == keep_note.id

    def test_audit_missing_source_note_files_returns_missing_source_notes(self, service, db_session, sample_pdf_path):
        from pathlib import Path
        from core.services.source_service import SourceService

        src = SourceService().import_source(sample_pdf_path, title="Audit Source")
        note = service.create_note("source - Audit", "source_note", source_id=src.id)
        Path(note.file_path).unlink(missing_ok=True)

        issues = service.audit_missing_source_note_files()
        by_id = {int(x["note_id"]): x for x in issues}
        assert note.id in by_id
        assert by_id[note.id]["source_id"] == src.id

    def test_get_note_delete_impact_counts_links_and_extracts(self, service, db_session, sample_pdf_path):
        from core.extraction.anchors import build_source_anchor
        from core.services.extract_service import ExtractService
        from core.services.link_service import LinkService
        from core.services.source_service import SourceService

        src = SourceService().import_source(sample_pdf_path, title="Impact Source")
        source_note = service.create_note("source - Impact", "source_note", source_id=src.id)
        concept = service.create_note("Impact Concept", "concept_note")

        LinkService().create_link(concept.id, source_note.id, "wikilink")
        ExtractService().commit_extract(
            source_id=src.id,
            page_no=1,
            extract_type="text",
            source_anchor=build_source_anchor(src.id, 1, (0, 0, 200, 100)),
            content_md="Impact extract",
            note_id=source_note.id,
        )

        impact = service.get_note_delete_impact(source_note.id)
        assert impact["is_source_note"] is True
        assert impact["incoming_links"] >= 1
        assert impact["extract_refs"] >= 1

    def test_get_note_delete_impact_supports_soft_deleted_note(self, service, db_session):
        note = service.create_note("Temp delete impact", "concept_note")
        service.soft_delete(note.id)

        impact = service.get_note_delete_impact(note.id)
        assert impact["note_id"] == note.id
        assert impact["note_type"] == "concept_note"


# ---------------------------------------------------------------------------
# Project scope (Sprint 7B)
# ---------------------------------------------------------------------------

class TestNoteProjectScope:
    def test_create_global_note_has_null_project_id(self, service, db_session):
        note = service.create_note(title="Global Note", note_type="concept_note")
        assert note.project_id is None

    def test_create_project_note_has_project_id(self, service, db_session):
        from core.services.project_service import ProjectService
        p = ProjectService().create_project("Test Project")
        note = service.create_note(title="Project Note", note_type="concept_note", project_id=p.id)
        assert note.project_id == p.id

    def test_list_by_project_returns_only_own_notes(self, service, db_session):
        from core.services.project_service import ProjectService
        p = ProjectService().create_project("Filter Project")
        own = service.create_note(title="Own Note", note_type="concept_note", project_id=p.id)
        global_note = service.create_note(title="Global Note 2", note_type="concept_note")

        result = service.list_by_project(p.id)
        ids = [n.id for n in result]
        assert own.id in ids
        assert global_note.id not in ids

    def test_list_global_excludes_project_notes(self, service, db_session):
        from core.services.project_service import ProjectService
        p = ProjectService().create_project("Exclude Project")
        own = service.create_note(title="Project Only", note_type="concept_note", project_id=p.id)
        global_note = service.create_note(title="Global Only", note_type="concept_note")

        result = service.list_global()
        ids = [n.id for n in result]
        assert global_note.id in ids
        assert own.id not in ids

    def test_list_global_with_note_type_filter(self, service, db_session):
        concept = service.create_note(title="Concept Global", note_type="concept_note")
        synth = service.create_note(title="~ Synth Global", note_type="synthesis_note")

        concepts = service.list_global(note_type="concept_note")
        ids = [n.id for n in concepts]
        assert concept.id in ids
        assert synth.id not in ids
