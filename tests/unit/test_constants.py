"""Unit tests cho core/utils/constants.py."""
from core.utils.constants import (
    APP_NAME,
    APP_VERSION,
    SCHEMA_VERSION,
    NOTE_TYPES,
    EXTRACT_TYPES,
    NOTE_TYPE_SOURCE,
    NOTE_TYPE_CONCEPT,
    EXTRACT_TYPE_TEXT,
    EXTRACT_TYPE_TABLE,
    EXTRACT_TYPE_IMAGE,
)


def test_app_name_is_vietnamese():
    assert "Nghiên cứu" in APP_NAME or "Kiến thức" in APP_NAME


def test_schema_version_is_positive_int():
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION >= 1


def test_note_types_complete():
    assert NOTE_TYPE_SOURCE in NOTE_TYPES
    assert NOTE_TYPE_CONCEPT in NOTE_TYPES


def test_extract_types_complete():
    assert EXTRACT_TYPE_TEXT in EXTRACT_TYPES
    assert EXTRACT_TYPE_TABLE in EXTRACT_TYPES
    assert EXTRACT_TYPE_IMAGE in EXTRACT_TYPES


def test_app_version_format():
    parts = APP_VERSION.split(".")
    assert len(parts) >= 2
