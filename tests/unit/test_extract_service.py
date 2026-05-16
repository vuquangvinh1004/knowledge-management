"""Unit tests cho ExtractService."""
from __future__ import annotations

import pytest

from core.services.extract_service import ExtractService
from core.services.source_service import SourceService
from core.utils.exceptions import ExtractAnchorMissingError, ExtractOrphanError, PKMError
from core.utils.helpers import build_source_anchor


@pytest.fixture
def service():
    return ExtractService()


@pytest.fixture
def source(db_session, sample_pdf_path):
    return SourceService().import_source(sample_pdf_path, title="Test Source")


class TestCommitExtract:
    def test_commit_text_extract(self, service, db_session, source):
        anchor = build_source_anchor(source.id, 1)
        extract = service.commit_extract(
            source_id=source.id,
            page_no=1,
            extract_type="text",
            source_anchor=anchor,
            content_md="> Trích dẫn từ trang 1",
        )
        assert extract.id is not None
        assert extract.extract_type == "text"
        assert extract.page_no == 1

    def test_commit_table_extract(self, service, db_session, source):
        anchor = build_source_anchor(source.id, 3, rect=(10, 20, 200, 150))
        extract = service.commit_extract(
            source_id=source.id,
            page_no=3,
            extract_type="table",
            source_anchor=anchor,
            content_md="| A | B |\n|---|---|\n| 1 | 2 |",
        )
        assert extract.extract_type == "table"

    def test_missing_source_id_raises(self, service, db_session):
        with pytest.raises(ExtractOrphanError):
            service.commit_extract(
                source_id=None,
                page_no=1,
                extract_type="text",
                source_anchor="source://1?page=1",
                content_md="test",
            )

    def test_invalid_extract_type_raises(self, service, db_session, source):
        anchor = build_source_anchor(source.id, 1)
        with pytest.raises(PKMError, match="extract_type"):
            service.commit_extract(
                source_id=source.id,
                page_no=1,
                extract_type="unknown",
                source_anchor=anchor,
                content_md="test",
            )

    def test_empty_content_raises(self, service, db_session, source):
        anchor = build_source_anchor(source.id, 1)
        with pytest.raises(PKMError, match="content_md"):
            service.commit_extract(
                source_id=source.id,
                page_no=1,
                extract_type="text",
                source_anchor=anchor,
                content_md="   ",
            )

    def test_invalid_anchor_raises(self, service, db_session, source):
        with pytest.raises(ExtractAnchorMissingError):
            service.commit_extract(
                source_id=source.id,
                page_no=1,
                extract_type="text",
                source_anchor="not-a-valid-anchor",
                content_md="test",
            )

    def test_anchor_source_mismatch_raises(self, service, db_session, source):
        anchor = build_source_anchor(9999, 1)  # sai source_id
        with pytest.raises(ExtractAnchorMissingError, match="không khớp"):
            service.commit_extract(
                source_id=source.id,
                page_no=1,
                extract_type="text",
                source_anchor=anchor,
                content_md="test",
            )


class TestListExtracts:
    def test_list_by_source(self, service, db_session, source):
        anchor = build_source_anchor(source.id, 1)
        service.commit_extract(source.id, 1, "text", anchor, "Content 1")
        service.commit_extract(source.id, 2, "text", build_source_anchor(source.id, 2), "Content 2")
        extracts = service.list_by_source(source.id)
        assert len(extracts) == 2

    def test_list_empty_source(self, service, db_session, source):
        assert service.list_by_source(source.id) == []
