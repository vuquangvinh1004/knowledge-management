"""Unit tests cho ProjectService (Phase 7 — Project Mode)."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.utils.exceptions import PKMError


@pytest.fixture
def project_service(db_session):
    from core.services.project_service import ProjectService
    return ProjectService()


@pytest.fixture
def note_service(db_session, tmp_path):
    from core.services.note_service import NoteService
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    return NoteService(notes_dir=notes_dir)


def _make_note(note_service, title: str, note_type: str = "concept_note"):
    """Helper: tạo note nhanh."""
    return note_service.create_note(title=title, note_type=note_type)


# ---------------------------------------------------------------------------
# CRUD cơ bản
# ---------------------------------------------------------------------------

class TestProjectCRUD:
    def test_create_project(self, project_service):
        p = project_service.create_project("Dự án Alpha")
        assert p.id is not None
        assert p.name == "Dự án Alpha"
        assert p.status == "active"
        assert p.is_deleted == 0

    def test_create_project_empty_name_raises(self, project_service):
        with pytest.raises(PKMError):
            project_service.create_project("")

    def test_create_project_whitespace_name_raises(self, project_service):
        with pytest.raises(PKMError):
            project_service.create_project("   ")

    def test_get_project(self, project_service):
        p = project_service.create_project("Beta")
        fetched = project_service.get_project(p.id)
        assert fetched.id == p.id
        assert fetched.name == "Beta"

    def test_get_nonexistent_project_raises(self, project_service):
        with pytest.raises(PKMError):
            project_service.get_project(99999)

    def test_list_projects_active_only(self, project_service):
        p1 = project_service.create_project("Active 1")
        p2 = project_service.create_project("Active 2")
        projects = project_service.list_projects()
        ids = [p.id for p in projects]
        assert p1.id in ids
        assert p2.id in ids

    def test_list_projects_excludes_deleted(self, project_service):
        p = project_service.create_project("Sẽ bị xóa")
        project_service.soft_delete_project(p.id)
        projects = project_service.list_projects()
        assert all(proj.id != p.id for proj in projects)

    def test_list_projects_excludes_closed_by_default(self, project_service):
        p = project_service.create_project("Sẽ đóng")
        project_service.close_project(p.id)
        projects = project_service.list_projects(include_closed=False)
        assert all(proj.id != p.id for proj in projects)

    def test_list_projects_includes_closed_when_requested(self, project_service):
        p = project_service.create_project("Đã đóng")
        project_service.close_project(p.id)
        projects = project_service.list_projects(include_closed=True)
        ids = [proj.id for proj in projects]
        assert p.id in ids

    def test_rename_project(self, project_service):
        p = project_service.create_project("Tên cũ")
        project_service.rename_project(p.id, "Tên mới")
        fetched = project_service.get_project(p.id)
        assert fetched.name == "Tên mới"

    def test_rename_project_empty_name_raises(self, project_service):
        p = project_service.create_project("Có tên")
        with pytest.raises(PKMError):
            project_service.rename_project(p.id, "")

    def test_close_project(self, project_service):
        p = project_service.create_project("Dự án hoàn thành")
        project_service.close_project(p.id)
        fetched = project_service.get_project(p.id)
        assert fetched.status == "closed"
        assert fetched.closed_at is not None

    def test_soft_delete_project(self, project_service):
        p = project_service.create_project("Xóa mềm")
        project_service.soft_delete_project(p.id)
        with pytest.raises(PKMError):
            project_service.get_project(p.id)

    def test_soft_delete_project_not_found_raises(self, project_service):
        with pytest.raises(PKMError):
            project_service.soft_delete_project(99999)


# ---------------------------------------------------------------------------
# Activate / Deactivate
# ---------------------------------------------------------------------------

class TestProjectActivation:
    def test_activate_project(self, project_service):
        p = project_service.create_project("Active Project")
        project_service.activate_project(p.id)
        assert project_service.get_active_project_id() == p.id

    def test_deactivate_project(self, project_service):
        p = project_service.create_project("Deactivate Test")
        project_service.activate_project(p.id)
        project_service.deactivate_project()
        assert project_service.get_active_project_id() is None

    def test_no_active_project_returns_none(self, project_service):
        assert project_service.get_active_project_id() is None

    def test_activate_nonexistent_project_raises(self, project_service):
        with pytest.raises(PKMError):
            project_service.activate_project(99999)

    def test_activate_switches_project(self, project_service):
        p1 = project_service.create_project("P1")
        p2 = project_service.create_project("P2")
        project_service.activate_project(p1.id)
        project_service.activate_project(p2.id)
        assert project_service.get_active_project_id() == p2.id

    def test_close_project_deactivates_if_active(self, project_service):
        p = project_service.create_project("Close + Deactivate")
        project_service.activate_project(p.id)
        project_service.close_project(p.id)
        assert project_service.get_active_project_id() is None

    def test_soft_delete_project_deactivates_if_active(self, project_service):
        p = project_service.create_project("Delete + Deactivate")
        project_service.activate_project(p.id)
        project_service.soft_delete_project(p.id)
        assert project_service.get_active_project_id() is None


# ---------------------------------------------------------------------------
# Note References
# ---------------------------------------------------------------------------

class TestProjectNoteRefs:
    def test_add_note_ref(self, project_service, note_service):
        p = project_service.create_project("Ref Project")
        note = _make_note(note_service, "Global Note")
        project_service.add_note_ref(p.id, note.id)
        refs = project_service.list_note_refs(p.id)
        assert any(r.id == note.id for r in refs)

    def test_add_note_ref_idempotent(self, project_service, note_service):
        p = project_service.create_project("Idempotent Ref")
        note = _make_note(note_service, "Note Idempotent")
        project_service.add_note_ref(p.id, note.id)
        project_service.add_note_ref(p.id, note.id)  # second call should not raise
        refs = project_service.list_note_refs(p.id)
        assert len([r for r in refs if r.id == note.id]) == 1

    def test_add_project_only_note_as_ref_raises(self, project_service, note_service, db_session):
        """Project-only note không thể được thêm vào project_note_refs."""
        p = project_service.create_project("Owner Project")
        p2 = project_service.create_project("Ref Project")
        note = _make_note(note_service, "Project-Only Note")
        # Gán note vào p (project-only)
        from sqlalchemy import update as sa_update
        from core.storage.models import Note
        from core.storage.session import get_session
        with get_session() as session:
            session.execute(sa_update(Note).where(Note.id == note.id).values(project_id=p.id))

        with pytest.raises(PKMError, match="project-only"):
            project_service.add_note_ref(p2.id, note.id)

    def test_remove_note_ref(self, project_service, note_service):
        p = project_service.create_project("Remove Ref Project")
        note = _make_note(note_service, "Remove Ref Note")
        project_service.add_note_ref(p.id, note.id)
        project_service.remove_note_ref(p.id, note.id)
        refs = project_service.list_note_refs(p.id)
        assert all(r.id != note.id for r in refs)

    def test_remove_nonexistent_ref_does_not_raise(self, project_service, note_service):
        p = project_service.create_project("No Ref Project")
        note = _make_note(note_service, "Not Ref Note")
        project_service.remove_note_ref(p.id, note.id)  # should not raise

    def test_add_ref_nonexistent_project_raises(self, project_service, note_service):
        note = _make_note(note_service, "Orphan Note")
        with pytest.raises(PKMError):
            project_service.add_note_ref(99999, note.id)

    def test_add_ref_nonexistent_note_raises(self, project_service):
        p = project_service.create_project("Valid Project")
        with pytest.raises(PKMError):
            project_service.add_note_ref(p.id, 99999)


# ---------------------------------------------------------------------------
# get_project_notes
# ---------------------------------------------------------------------------

class TestGetProjectNotes:
    def test_get_project_notes_own(self, project_service, note_service, db_session):
        p = project_service.create_project("Own Notes Project")
        note = _make_note(note_service, "Own Note")
        # Gán note vào project
        from sqlalchemy import update as sa_update
        from core.storage.models import Note
        from core.storage.session import get_session
        with get_session() as session:
            session.execute(sa_update(Note).where(Note.id == note.id).values(project_id=p.id))

        result = project_service.get_project_notes(p.id)
        assert any(n.id == note.id for n in result["own"])
        assert all(n.id != note.id for n in result["refs"])

    def test_get_project_notes_refs(self, project_service, note_service):
        p = project_service.create_project("Refs Notes Project")
        note = _make_note(note_service, "Ref Note")
        project_service.add_note_ref(p.id, note.id)

        result = project_service.get_project_notes(p.id)
        assert all(n.id != note.id for n in result["own"])
        assert any(n.id == note.id for n in result["refs"])

    def test_get_project_note_ids(self, project_service, note_service, db_session):
        p = project_service.create_project("IDs Project")
        own = _make_note(note_service, "Own")
        ref = _make_note(note_service, "Ref")

        from sqlalchemy import update as sa_update
        from core.storage.models import Note
        from core.storage.session import get_session
        with get_session() as session:
            session.execute(sa_update(Note).where(Note.id == own.id).values(project_id=p.id))

        project_service.add_note_ref(p.id, ref.id)

        ids = project_service.get_project_note_ids(p.id)
        assert own.id in ids
        assert ref.id in ids


# ---------------------------------------------------------------------------
# Export bundle
# ---------------------------------------------------------------------------

class TestExportProjectBundle:
    def test_export_creates_folder_structure(self, project_service, note_service, tmp_path, db_session):
        p = project_service.create_project("Export Test Project")
        ref_note = _make_note(note_service, "Reference Note")
        project_service.add_note_ref(p.id, ref_note.id)

        output_dir = tmp_path / "exports"
        output_dir.mkdir()

        bundle_path = project_service.export_project_bundle(p.id, output_dir)

        assert bundle_path.exists()
        assert (bundle_path / "README.md").exists()
        assert (bundle_path / "own").is_dir()
        assert (bundle_path / "refs").is_dir()

    def test_export_readme_contains_project_name(self, project_service, note_service, tmp_path):
        p = project_service.create_project("Dự án Ma trận")
        output_dir = tmp_path / "exports"
        output_dir.mkdir()
        bundle_path = project_service.export_project_bundle(p.id, output_dir)
        readme = (bundle_path / "README.md").read_text(encoding="utf-8")
        assert "Dự án Ma trận" in readme

    def test_export_ref_note_file_copied(self, project_service, note_service, tmp_path):
        p = project_service.create_project("Copy Test")
        note = _make_note(note_service, "Note To Copy")
        # Ghi nội dung vào file note
        Path(note.file_path).write_text("# Note To Copy\n\nContent here.", encoding="utf-8")
        project_service.add_note_ref(p.id, note.id)

        output_dir = tmp_path / "exports"
        output_dir.mkdir()
        bundle_path = project_service.export_project_bundle(p.id, output_dir)

        refs_dir = bundle_path / "refs"
        copied_files = list(refs_dir.glob("*.md"))
        assert len(copied_files) >= 1

    def test_export_nonexistent_project_raises(self, project_service, tmp_path):
        with pytest.raises(PKMError):
            project_service.export_project_bundle(99999, tmp_path)
