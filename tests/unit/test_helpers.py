"""Unit tests cho core/utils/helpers.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.utils.helpers import (
    slugify,
    compute_file_hash,
    build_source_anchor,
    parse_source_anchor,
)


class TestSlugify:
    def test_basic_ascii(self):
        assert slugify("Hello World") == "hello-world"

    def test_vietnamese_accents(self):
        result = slugify("Nghiên cứu khoa học")
        assert result == "nghien-cuu-khoa-hoc"

    def test_numbers(self):
        assert slugify("Bài 2024") == "bai-2024"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == "untitled"

    def test_only_special_chars(self):
        assert slugify("!!!") == "untitled"

    def test_trailing_dashes(self):
        result = slugify("  test  ")
        assert result == "test"


class TestComputeFileHash:
    def test_consistent_hash(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello world")
        h1 = compute_file_hash(f)
        h2 = compute_file_hash(f)
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path: Path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert compute_file_hash(f1) != compute_file_hash(f2)

    def test_hash_is_hex_string(self, tmp_path: Path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"data")
        h = compute_file_hash(f)
        assert isinstance(h, str)
        assert all(c in "0123456789abcdef" for c in h)


class TestBuildSourceAnchor:
    def test_without_rect(self):
        anchor = build_source_anchor(source_id=1, page_no=3)
        assert anchor == "source://1?page=3"

    def test_with_rect(self):
        anchor = build_source_anchor(source_id=5, page_no=10, rect=(10.0, 20.0, 200.0, 50.0))
        assert anchor == "source://5?page=10&rect=10.00,20.00,200.00,50.00"

    def test_scheme(self):
        anchor = build_source_anchor(1, 1)
        assert anchor.startswith("source://")


class TestParseSourceAnchor:
    def test_parse_without_rect(self):
        anchor = "source://1?page=3"
        result = parse_source_anchor(anchor)
        assert result["source_id"] == 1
        assert result["page_no"] == 3
        assert result["rect"] is None

    def test_parse_with_rect(self):
        anchor = "source://5?page=10&rect=10.00,20.00,200.00,50.00"
        result = parse_source_anchor(anchor)
        assert result["source_id"] == 5
        assert result["page_no"] == 10
        assert result["rect"] is not None
        assert len(result["rect"]) == 4

    def test_roundtrip(self):
        original = build_source_anchor(42, 7, rect=(1.0, 2.0, 3.0, 4.0))
        parsed = parse_source_anchor(original)
        assert parsed["source_id"] == 42
        assert parsed["page_no"] == 7

    def test_invalid_scheme_raises(self):
        with pytest.raises(ValueError, match="scheme"):
            parse_source_anchor("http://example.com?page=1")
