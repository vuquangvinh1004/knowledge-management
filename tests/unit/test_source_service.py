"""Unit tests cho SourceService."""
from __future__ import annotations

from pathlib import Path
import uuid

import pytest

from core.services.source_service import SourceService
from core.utils.exceptions import SourceDuplicateError, SourceFileNotFoundError, SourceNotFoundError


@pytest.fixture
def service():
    return SourceService()


class TestImportSource:
    def test_import_valid_pdf(self, service, db_session, sample_pdf_path):
        source = service.import_source(sample_pdf_path, title="Test Paper")
        assert source.id is not None
        assert source.public_id
        assert uuid.UUID(str(source.public_id)).version in (4, 7)
        assert source.title == "Test Paper"
        assert source.file_hash

    def test_import_nonexistent_file_raises(self, service, db_session, tmp_path):
        with pytest.raises(SourceFileNotFoundError):
            service.import_source(tmp_path / "missing.pdf")

    def test_import_duplicate_raises(self, service, db_session, sample_pdf_path):
        service.import_source(sample_pdf_path, title="First")
        with pytest.raises(SourceDuplicateError):
            service.import_source(sample_pdf_path, title="Duplicate")

    def test_import_uses_filename_as_default_title(self, service, db_session, sample_pdf_path):
        source = service.import_source(sample_pdf_path)
        assert source.title == sample_pdf_path.stem


class TestListSources:
    def test_list_empty(self, service, db_session):
        assert service.list_all() == []

    def test_list_returns_imported(self, service, db_session, sample_pdf_path):
        service.import_source(sample_pdf_path, title="Paper A")
        sources = service.list_all()
        assert len(sources) == 1
        assert sources[0].title == "Paper A"

    def test_list_excludes_deleted(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        service.soft_delete(s.id)
        assert service.list_all() == []

    def test_list_include_deleted(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        service.soft_delete(s.id)
        assert len(service.list_all(include_deleted=True)) == 1


class TestGetSource:
    def test_get_by_id(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        fetched = service.get_by_id(s.id)
        assert fetched.id == s.id

    def test_get_nonexistent_raises(self, service, db_session):
        with pytest.raises(SourceNotFoundError):
            service.get_by_id(9999)

    def test_get_deleted_raises(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        service.soft_delete(s.id)
        with pytest.raises(SourceNotFoundError):
            service.get_by_id(s.id)


class TestUpdateSource:
    def test_update_metadata(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        updated = service.update_metadata(s.id, title="New Title", year="2024")
        assert updated.title == "New Title"
        assert updated.year == "2024"

    def test_relink_path(self, service, db_session, sample_pdf_path, tmp_path):
        s = service.import_source(sample_pdf_path)
        new_path = tmp_path / "moved.pdf"
        sample_pdf_path.rename(new_path)
        updated = service.relink_path(s.id, new_path)
        assert updated.file_path == str(new_path)

    def test_relink_missing_file_raises(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        with pytest.raises(SourceFileNotFoundError):
            service.relink_path(s.id, Path("/nonexistent/path.pdf"))


class TestDeleteSource:
    def test_soft_delete(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        service.soft_delete(s.id)
        assert service.list_all() == []

    def test_hard_delete(self, service, db_session, sample_pdf_path):
        s = service.import_source(sample_pdf_path)
        service.hard_delete(s.id)
        with pytest.raises(SourceNotFoundError):
            service.get_by_id(s.id)


class TestExtractPdfMetadata:
    def test_returns_dict_with_expected_keys(self, service, sample_pdf_path):
        meta = SourceService.extract_pdf_metadata(sample_pdf_path)
        assert "title" in meta
        assert "authors" in meta
        assert "year" in meta
        assert "keywords" in meta
        assert "pages_count" in meta

    def test_pages_count_is_positive(self, service, sample_pdf_path):
        meta = SourceService.extract_pdf_metadata(sample_pdf_path)
        assert meta["pages_count"] >= 1

    def test_nonexistent_file_returns_zero_pages(self, service, tmp_path):
        meta = SourceService.extract_pdf_metadata(tmp_path / "ghost.pdf")
        assert meta["pages_count"] == 0

    def test_import_stores_pages_count_in_metadata_json(
        self, service, db_session, sample_pdf_path
    ):
        import json
        s = service.import_source(sample_pdf_path)
        if s.metadata_json:
            extra = json.loads(s.metadata_json)
            assert "pages_count" in extra
            assert extra["pages_count"] >= 1


class TestUpdateMetadataExtended:
    def test_update_abstract_and_keywords(self, service, db_session, sample_pdf_path):
        import json
        s = service.import_source(sample_pdf_path)
        updated = service.update_metadata(
            s.id,
            abstract="Đây là tóm tắt nghiên cứu.",
            keywords="supply chain, logistics",
        )
        assert updated.id == s.id
        extra = json.loads(updated.metadata_json or "{}")
        assert extra.get("abstract") == "Đây là tóm tắt nghiên cứu."
        assert extra.get("keywords") == "supply chain, logistics"

    def test_update_abstract_preserves_other_json_fields(
        self, service, db_session, sample_pdf_path
    ):
        import json
        s = service.import_source(sample_pdf_path)
        # pages_count có thể đã được lưu từ import
        service.update_metadata(s.id, abstract="New abstract")
        updated = service.get_by_id(s.id)
        extra = json.loads(updated.metadata_json or "{}")
        assert extra.get("abstract") == "New abstract"
        # pages_count không bị xóa
        if "pages_count" in json.loads(s.metadata_json or "{}"):
            assert "pages_count" in extra


class TestSourceNoteTitleNaming:
    def test_build_source_note_title_author_and_year(self):
        title = SourceService.build_source_note_title(
            authors="John Lent; Robert Brown",
            year="1994",
            fallback_filename="paper_abc",
        )
        assert title == "Lent & Brown (1994)"

    def test_build_source_note_title_fallback_filename(self):
        title = SourceService.build_source_note_title(
            authors=None,
            year=None,
            fallback_filename="sample_document",
        )
        assert title == "sample_document"

    def test_build_source_note_title_single_author(self):
        title = SourceService.build_source_note_title(
            authors="Ajzen",
            year="1991",
            fallback_filename="ignored",
        )
        assert title == "Ajzen (1991)"

    def test_build_source_note_title_three_authors_uses_et_al(self):
        title = SourceService.build_source_note_title(
            authors="Nguyen Van A; Tran Van B; Le Van C",
            year="2024",
            fallback_filename="ignored",
        )
        assert title == "A et al. (2024)"
