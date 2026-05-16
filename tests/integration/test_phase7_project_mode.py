"""Integration tests cho Phase 7: Project mode workflow (Sprint 7D)."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def note_service(db_session, notes_dir):
    from core.services.note_service import NoteService
    return NoteService(notes_dir)


@pytest.fixture
def project_service(db_session):
    from core.services.project_service import ProjectService
    return ProjectService()


@pytest.fixture
def export_service(db_session, tmp_path):
    from core.services.export_service import ExportService
    return ExportService(tmp_path / "exports")


class TestProjectModeIntegration:
    def test_close_project_updates_status_and_deactivates(self, project_service):
        p = project_service.create_project("Project Close Integration")
        project_service.activate_project(p.id)

        project_service.close_project(p.id)

        updated = project_service.get_project(p.id)
        assert updated.status == "closed"
        assert updated.closed_at is not None
        assert project_service.get_active_project_id() is None

    def test_export_project_bundle_via_export_service(self, project_service, note_service, export_service):
        p = project_service.create_project("Project Export Service")

        own_note = note_service.create_note(
            title="Own Note Export",
            note_type="concept_note",
            project_id=p.id,
            initial_content="# Own Note Export\n\nNội dung own",
        )
        ref_note = note_service.create_note(
            title="Global Ref Export",
            note_type="concept_note",
            initial_content="# Global Ref Export\n\nNội dung ref",
        )
        project_service.add_note_ref(p.id, ref_note.id)

        bundle_dir = export_service.export_project_bundle(p.id)

        assert bundle_dir.exists()
        assert (bundle_dir / "README.md").exists()
        assert (bundle_dir / "own" / Path(own_note.file_path).name).exists()
        assert (bundle_dir / "refs" / Path(ref_note.file_path).name).exists()

        readme = (bundle_dir / "README.md").read_text(encoding="utf-8")
        assert "Project Export Service" in readme
        assert "Own Note Export" in readme
        assert "Global Ref Export" in readme

    def test_export_project_bundle_via_project_service_delegate(self, project_service, note_service, tmp_path):
        p = project_service.create_project("Project Delegate Export")
        note_service.create_note(
            title="Own Delegate",
            note_type="concept_note",
            project_id=p.id,
            initial_content="# Own Delegate",
        )

        output_root = tmp_path / "project_bundle_output"
        output_root.mkdir(parents=True, exist_ok=True)

        bundle_dir = project_service.export_project_bundle(p.id, output_root)

        assert bundle_dir.exists()
        assert bundle_dir.parent == output_root
        assert (bundle_dir / "README.md").exists()

    def test_export_nonexistent_project_raises(self, export_service):
        from core.utils.exceptions import PKMError

        with pytest.raises(PKMError):
            export_service.export_project_bundle(999999)

    def test_soft_delete_project_keeps_bundle_of_previous_export(self, project_service, note_service, tmp_path):
        p = project_service.create_project("Project Archive")
        note_service.create_note(
            title="Archive Note",
            note_type="concept_note",
            project_id=p.id,
            initial_content="# Archive Note",
        )

        bundle_before = project_service.export_project_bundle(p.id, tmp_path)
        assert bundle_before.exists()

        project_service.soft_delete_project(p.id)

        # Bundle đã xuất trước đó vẫn tồn tại như snapshot standalone
        assert bundle_before.exists()