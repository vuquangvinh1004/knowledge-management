"""Unit tests cho WorkspaceOrchestrator — phần Project Mode (Sprint 7B)."""
from __future__ import annotations

import pytest

from core.utils.exceptions import PKMError


@pytest.fixture
def orchestrator(db_session, tmp_path):
    from core.services.workspace_orchestrator import WorkspaceOrchestrator
    notes_dir = tmp_path / "notes"
    assets_dir = tmp_path / "assets"
    notes_dir.mkdir()
    assets_dir.mkdir()
    return WorkspaceOrchestrator(notes_dir=notes_dir, assets_dir=assets_dir)


@pytest.fixture
def project_service(db_session):
    from core.services.project_service import ProjectService
    return ProjectService()


# ---------------------------------------------------------------------------
# active_project_id / is_project_mode
# ---------------------------------------------------------------------------

class TestProjectModeState:
    def test_no_active_project_returns_none(self, orchestrator):
        assert orchestrator.active_project_id is None

    def test_is_project_mode_false_when_no_active_project(self, orchestrator):
        assert orchestrator.is_project_mode() is False

    def test_is_project_mode_true_when_project_active(self, orchestrator, project_service):
        p = project_service.create_project("Active Project")
        project_service.activate_project(p.id)
        assert orchestrator.is_project_mode() is True
        assert orchestrator.active_project_id == p.id

    def test_deactivate_returns_to_global_mode(self, orchestrator, project_service):
        p = project_service.create_project("Temp Project")
        project_service.activate_project(p.id)
        project_service.deactivate_project()
        assert orchestrator.is_project_mode() is False


# ---------------------------------------------------------------------------
# get_active_project_note_ids
# ---------------------------------------------------------------------------

class TestActiveProjectNoteIds:
    def test_no_active_project_returns_empty_set(self, orchestrator):
        ids = orchestrator.get_active_project_note_ids()
        assert ids == set()

    def test_returns_own_and_ref_note_ids(self, orchestrator, project_service, tmp_path):
        from core.services.note_service import NoteService
        note_svc = NoteService(tmp_path / "notes")

        p = project_service.create_project("Note IDs Project")
        own = note_svc.create_note("Own Note", "concept_note", project_id=p.id)
        ref = note_svc.create_note("Ref Note", "concept_note")
        project_service.add_note_ref(p.id, ref.id)
        project_service.activate_project(p.id)

        ids = orchestrator.get_active_project_note_ids()
        assert own.id in ids
        assert ref.id in ids


# ---------------------------------------------------------------------------
# create_note_in_scope
# ---------------------------------------------------------------------------

class TestCreateNoteInScope:
    def test_save_global_when_no_project_active(self, orchestrator):
        note = orchestrator.create_note_in_scope(
            title="Global Scope Note",
            note_type="concept_note",
            save_to_project=False,
        )
        assert note.project_id is None

    def test_save_global_even_when_project_active(self, orchestrator, project_service):
        p = project_service.create_project("Background Project")
        project_service.activate_project(p.id)

        note = orchestrator.create_note_in_scope(
            title="Still Global Note",
            note_type="concept_note",
            save_to_project=False,
        )
        assert note.project_id is None

    def test_save_to_project_when_project_active(self, orchestrator, project_service):
        p = project_service.create_project("Target Project")
        project_service.activate_project(p.id)

        note = orchestrator.create_note_in_scope(
            title="Project Note Scope",
            note_type="concept_note",
            save_to_project=True,
        )
        assert note.project_id == p.id

    def test_save_to_project_without_active_project_raises(self, orchestrator):
        with pytest.raises(PKMError, match="active"):
            orchestrator.create_note_in_scope(
                title="No Project Note",
                note_type="concept_note",
                save_to_project=True,
            )

    def test_created_note_file_exists_on_disk(self, orchestrator, project_service, tmp_path):
        from pathlib import Path
        p = project_service.create_project("Disk Project")
        project_service.activate_project(p.id)

        note = orchestrator.create_note_in_scope(
            title="Disk Check Note",
            note_type="concept_note",
            save_to_project=True,
        )
        assert Path(note.file_path).exists()


class TestSourceNoteResilience:
    def test_load_source_with_note_auto_creates_when_missing(self, orchestrator, sample_pdf_path):
        from core.services.source_service import SourceService

        src = SourceService().import_source(file_path=sample_pdf_path, title="PDF A")

        _source, note, notice = orchestrator.load_source_with_note(src.id)
        assert note.source_id == src.id
        assert notice is None

    def test_load_source_with_note_recovers_missing_note_file(self, orchestrator, sample_pdf_path, tmp_path):
        from pathlib import Path
        from core.services.source_service import SourceService
        from core.services.note_service import NoteService
        from core.storage.models import Note
        from core.storage.session import get_session

        src = SourceService().import_source(file_path=sample_pdf_path, title="PDF B")
        note_svc = NoteService(tmp_path / "notes")
        old_note = note_svc.create_note(
            title="source - Legacy",
            note_type="source_note",
            source_id=src.id,
        )

        old_path = Path(old_note.file_path)
        assert old_path.exists()
        old_path.unlink()

        _source, new_note, notice = orchestrator.load_source_with_note(src.id)
        assert new_note.id != old_note.id
        assert Path(new_note.file_path).exists()
        assert notice is not None
        assert "tự tạo lại" in notice

        with get_session() as session:
            db_old = session.get(Note, old_note.id)
            assert db_old is not None
            assert db_old.is_deleted == 1
