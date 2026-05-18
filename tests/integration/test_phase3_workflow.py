"""Integration tests cho Phase 3 workflow.

Kiểm tra luồng: import source → mở workspace → trích xuất → lưu asset.
Không test UI widget (đó là UI smoke tests), chỉ test service + extraction pipeline.
"""
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
def extract_service(db_session):
    from core.services.extract_service import ExtractService
    return ExtractService()


@pytest.fixture
def asset_service(db_session, tmp_path):
    from core.services.asset_service import AssetService
    return AssetService(tmp_path / "assets")


# ---------------------------------------------------------------------------
# Test: import source và tạo source note
# ---------------------------------------------------------------------------

class TestImportAndNoteWorkflow:
    def test_import_creates_source(self, source_service, sample_pdf_path):
        src = source_service.import_source(sample_pdf_path, title="Test PDF")
        assert src.id is not None
        assert src.title == "Test PDF"

    def test_import_then_create_source_note(
        self, source_service, note_service, sample_pdf_path
    ):
        src = source_service.import_source(sample_pdf_path, title="Test PDF 2")
        note = note_service.create_note(
            title=src.title,
            note_type="source_note",
            source_id=src.id,
        )
        assert note.id is not None
        assert note.note_type == "source_note"
        assert note.source_id == src.id

    def test_get_source_note_after_create(
        self, source_service, note_service, sample_pdf_path
    ):
        src = source_service.import_source(sample_pdf_path, title="Test PDF 3")
        note_service.create_note(
            title=src.title,
            note_type="source_note",
            source_id=src.id,
        )
        found = note_service.get_source_note(src.id)
        assert found is not None
        assert found.source_id == src.id


# ---------------------------------------------------------------------------
# Test: extract text với anchor hợp lệ
# ---------------------------------------------------------------------------

class TestExtractWorkflow:
    def test_commit_text_extract(
        self, source_service, note_service, extract_service, sample_pdf_path
    ):
        from core.extraction.anchors import build_source_anchor

        src = source_service.import_source(sample_pdf_path, title="Ext PDF")
        note = note_service.create_note("Ext PDF", "source_note", src.id)

        anchor = build_source_anchor(src.id, 1, (0, 0, 200, 100))
        extract = extract_service.commit_extract(
            source_id=src.id,
            page_no=1,
            extract_type="text",
            source_anchor=anchor,
            content_md="Đây là văn bản trích xuất.",
            note_id=note.id,
        )
        assert extract.id is not None
        assert extract.source_id == src.id
        assert extract.page_no == 1

    def test_list_extracts_by_source(
        self, source_service, extract_service, sample_pdf_path
    ):
        from core.extraction.anchors import build_source_anchor

        src = source_service.import_source(sample_pdf_path, title="List Ext PDF")
        for pg in [1, 2]:
            anchor = build_source_anchor(src.id, pg)
            extract_service.commit_extract(
                source_id=src.id,
                page_no=pg,
                extract_type="text",
                source_anchor=anchor,
                content_md=f"Văn bản trang {pg}",
            )
        extracts = extract_service.list_by_source(src.id)
        assert len(extracts) == 2


# ---------------------------------------------------------------------------
# Test: lưu asset
# ---------------------------------------------------------------------------

class TestAssetWorkflow:
    def test_save_image_asset(self, source_service, asset_service, sample_pdf_path):
        src = source_service.import_source(sample_pdf_path, title="Asset PDF")
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        asset = asset_service.save_image_asset(
            source_id=src.id,
            image_bytes=fake_png,
        )
        assert asset.id is not None
        assert Path(asset.file_path).exists()

    def test_list_assets_by_source(self, source_service, asset_service, sample_pdf_path):
        src = source_service.import_source(sample_pdf_path, title="Asset PDF 2")
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        asset_service.save_image_asset(source_id=src.id, image_bytes=fake_png)
        asset_service.save_image_asset(source_id=src.id, image_bytes=fake_png)
        assets = asset_service.list_by_source(src.id)
        assert len(assets) == 2


# ---------------------------------------------------------------------------
# Test: normalizers + pdf extraction pipeline (nếu PyMuPDF có sẵn)
# ---------------------------------------------------------------------------

class TestExtractionPipeline:
    def test_text_normalize_then_anchor(self, source_service, sample_pdf_path):
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, extract_page_text
        from core.extraction.normalizers import normalize_text
        from core.extraction.anchors import build_source_anchor

        src = source_service.import_source(sample_pdf_path, title="Pipeline PDF")
        doc = open_document(sample_pdf_path)
        try:
            raw = extract_page_text(doc, 1)
            clean = normalize_text(raw)
            anchor = build_source_anchor(src.id, 1)
            assert isinstance(clean, str)
            assert anchor.startswith(f"source://{src.id}?page=1")
        finally:
            doc.close()


class TestDraftWorkspaceScratchExtraction:
    def test_text_extract_inserts_into_scratch_editor_and_persists_extract(
        self,
        qtbot,
        source_service,
        extract_service,
        sample_pdf_path,
        monkeypatch,
    ):
        from ui.views.draft_workspace_view import DraftWorkspaceView

        src = source_service.import_source(sample_pdf_path, title="Scratch Extraction PDF")

        monkeypatch.setattr(
            "core.extraction.pdf_text.extract_region_text",
            lambda _doc, _page_no, _rect: "Đây là nội dung trích trong workspace.",
        )

        view = DraftWorkspaceView()
        qtbot.addWidget(view)
        view.show()
        view.open_reference_source(src.id)

        view._on_text_selected(src.id, 1, (0, 0, 200, 100))

        content = view._draft_editor.get_content()
        assert "Đây là nội dung trích trong workspace." in content
        extracts = extract_service.list_by_source(src.id)
        assert len(extracts) == 1
        assert extracts[0].note_id is None
        assert extracts[0].extract_type == "text"

    def test_table_extract_inserts_into_scratch_editor_and_persists_extract(
        self,
        qtbot,
        source_service,
        extract_service,
        sample_pdf_path,
        monkeypatch,
    ):
        from ui.views.draft_workspace_view import DraftWorkspaceView

        src = source_service.import_source(sample_pdf_path, title="Scratch Table PDF")

        monkeypatch.setattr(
            "core.extraction.pdf_table.extract_table_from_region",
            lambda _file_path, _page_no, _rect: [
                ["Cột A", "Cột B"],
                ["Giá trị 1", "Giá trị 2"],
            ],
        )
        monkeypatch.setattr(
            "ui.widgets.dialogs.table_preview_dialog.TablePreviewDialog.exec",
            lambda self: 1,
        )

        view = DraftWorkspaceView()
        qtbot.addWidget(view)
        view.show()
        view.open_reference_source(src.id)

        view._on_table_selected(src.id, 1, (0, 0, 240, 120))

        content = view._draft_editor.get_content()
        assert "| Cột A | Cột B |" in content
        assert "| Giá trị 1 | Giá trị 2 |" in content
        extracts = extract_service.list_by_source(src.id)
        assert len(extracts) == 1
        assert extracts[0].note_id is None
        assert extracts[0].extract_type == "table"

    def test_image_capture_inserts_asset_ref_and_persists_asset(
        self,
        qtbot,
        source_service,
        sample_pdf_path,
        monkeypatch,
        tmp_path,
    ):
        from config.paths import NOTES_DIR
        from core.services.asset_service import AssetService
        from core.services.workspace_orchestrator import WorkspaceOrchestrator
        from ui.views.draft_workspace_view import DraftWorkspaceView

        src = source_service.import_source(sample_pdf_path, title="Scratch Image PDF")
        assets_dir = tmp_path / "scratch_assets"

        monkeypatch.setattr(
            "core.extraction.pdf_image.capture_region",
            lambda _doc, _page_no, _rect: b"\x89PNG\r\n\x1a\n" + b"\x00" * 64,
        )

        view = DraftWorkspaceView()
        view._orchestrator = WorkspaceOrchestrator(NOTES_DIR, assets_dir)
        qtbot.addWidget(view)
        view.show()
        view.open_reference_source(src.id)

        view._on_image_selected(src.id, 1, (0, 0, 180, 180))

        assets = AssetService(assets_dir).list_by_source(src.id)
        assert len(assets) == 1
        assert assets[0].note_id is None
        assert assets[0].asset_type == "image"
        assert Path(assets[0].file_path).exists()
        content = view._draft_editor.get_content()
        assert assets[0].file_path in content
