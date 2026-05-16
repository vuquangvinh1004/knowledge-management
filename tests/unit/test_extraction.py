"""Unit tests cho extraction layer (normalizers, pdf_text, pdf_table, pdf_image)."""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_join_hyphen_line_break(self):
        from core.extraction.normalizers import normalize_text
        result = normalize_text("re-\nsearch")
        assert result == "research"

    def test_single_newline_becomes_space(self):
        from core.extraction.normalizers import normalize_text
        result = normalize_text("hello\nworld")
        assert result == "hello world"

    def test_double_newline_preserved_as_paragraph(self):
        from core.extraction.normalizers import normalize_text
        result = normalize_text("para1\n\npara2")
        assert "\n\n" in result

    def test_extra_spaces_collapsed(self):
        from core.extraction.normalizers import normalize_text
        result = normalize_text("foo   bar")
        assert result == "foo bar"

    def test_empty_string(self):
        from core.extraction.normalizers import normalize_text
        assert normalize_text("") == ""

    def test_strip_leading_trailing(self):
        from core.extraction.normalizers import normalize_text
        assert normalize_text("  hello  ") == "hello"


class TestTableToMarkdown:
    def test_basic_table(self):
        from core.extraction.normalizers import table_to_markdown
        rows = [["Tên", "Tuổi"], ["An", "25"], ["Bình", "30"]]
        md = table_to_markdown(rows)
        assert "| Tên | Tuổi |" in md
        assert "| --- |" in md
        assert "| An | 25 |" in md

    def test_empty_returns_empty_string(self):
        from core.extraction.normalizers import table_to_markdown
        assert table_to_markdown([]) == ""

    def test_none_cells_become_empty(self):
        from core.extraction.normalizers import table_to_markdown
        rows = [["A", None], ["1", None]]
        md = table_to_markdown(rows)
        assert "| A |  |" in md

    def test_short_rows_padded(self):
        from core.extraction.normalizers import table_to_markdown
        rows = [["Col1", "Col2", "Col3"], ["only_one"]]
        md = table_to_markdown(rows)
        # Hàng dữ liệu phải có 3 cột
        lines = md.splitlines()
        data_line = lines[-1]
        assert data_line.count("|") == 4  # 3 cells + 2 borders = 4 |

    def test_newline_in_cell_replaced(self):
        from core.extraction.normalizers import table_to_markdown
        rows = [["head"], ["cell\nwith\nnewline"]]
        md = table_to_markdown(rows)
        assert "\n" not in md.splitlines()[-1]


# ---------------------------------------------------------------------------
# PDF text extraction (cần PyMuPDF)
# ---------------------------------------------------------------------------

class TestPDFText:
    def test_page_count(self, sample_pdf_path: Path):
        """Tài liệu PDF mẫu phải có ít nhất 1 trang."""
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, page_count
        doc = open_document(sample_pdf_path)
        try:
            assert page_count(doc) >= 1
        finally:
            doc.close()

    def test_render_page_returns_bytes(self, sample_pdf_path: Path):
        """render_page_to_bytes phải trả về PNG bytes."""
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, render_page_to_bytes
        doc = open_document(sample_pdf_path)
        try:
            data = render_page_to_bytes(doc, 1, zoom=1.0)
            assert isinstance(data, bytes)
            assert data[:4] == b"\x89PNG"  # PNG header
        finally:
            doc.close()

    def test_get_page_dimensions(self, sample_pdf_path: Path):
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, get_page_dimensions
        doc = open_document(sample_pdf_path)
        try:
            w, h = get_page_dimensions(doc, 1)
            assert w > 0
            assert h > 0
        finally:
            doc.close()

    def test_extract_page_text_returns_string(self, sample_pdf_path: Path):
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, extract_page_text
        doc = open_document(sample_pdf_path)
        try:
            text = extract_page_text(doc, 1)
            assert isinstance(text, str)
            assert "Sample" in text  # conftest inserts "Sample PDF for testing"
        finally:
            doc.close()

    def test_extract_region_text(self, sample_pdf_path: Path):
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document, extract_region_text
        doc = open_document(sample_pdf_path)
        try:
            # Vùng toàn trang
            text = extract_region_text(doc, 1, (0, 0, 595, 842))
            assert isinstance(text, str)
        finally:
            doc.close()


# ---------------------------------------------------------------------------
# PDF image capture
# ---------------------------------------------------------------------------

class TestPDFImage:
    def test_capture_region_returns_png(self, sample_pdf_path: Path):
        pytest.importorskip("fitz")
        from core.extraction.pdf_text import open_document
        from core.extraction.pdf_image import capture_region
        doc = open_document(sample_pdf_path)
        try:
            data = capture_region(doc, 1, (0, 0, 200, 200), zoom=1.0)
            assert isinstance(data, bytes)
            assert data[:4] == b"\x89PNG"
        finally:
            doc.close()


# ---------------------------------------------------------------------------
# Anchors re-export
# ---------------------------------------------------------------------------

class TestAnchorsReexport:
    def test_build_and_parse_roundtrip(self):
        from core.extraction.anchors import build_source_anchor, parse_source_anchor
        anchor = build_source_anchor(42, 3, (10.0, 20.0, 100.0, 200.0))
        parsed = parse_source_anchor(anchor)
        assert parsed["source_id"] == 42
        assert parsed["page_no"] == 3
        assert parsed["rect"] == (10.0, 20.0, 100.0, 200.0)
