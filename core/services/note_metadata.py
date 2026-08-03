"""Metadata helpers cho Note."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from core.storage.models import Note
from core.storage.session import get_session
from core.utils.exceptions import NoteNotFoundError, PKMError


def get_meta(note_id: int) -> dict:
    """Lấy metadata JSON của note dưới dạng dict."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None or note.is_deleted:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        raw = note.meta_json or "{}"
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def update_meta(note_id: int, meta: dict) -> None:
    """Cập nhật meta_json của note với validation theo note_type."""
    if not isinstance(meta, dict):
        raise PKMError("meta phải là dict JSON hợp lệ.")

    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None or note.is_deleted:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")

        validated = validate_meta_for_note_type(str(note.note_type), meta)
        note.meta_json = json.dumps(validated, ensure_ascii=False)
        note.updated_at = datetime.now(timezone.utc)


def validate_meta_for_note_type(note_type: str, meta: dict) -> dict:
    """Validate meta theo từng note_type và trả về dict đã chuẩn hóa."""
    clean = {str(k): v for k, v in meta.items()}

    if note_type == "source_note":
        allowed = {"author", "year", "source_type", "publication", "topic"}
        out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
        if "year" in out:
            year_str = str(out["year"]).strip()
            if not (year_str.isdigit() and len(year_str) == 4):
                raise PKMError("Meta `year` của source_note phải là 4 chữ số.")
            out["year"] = year_str
        if "author" in out:
            out["author"] = str(out["author"]).strip()
        return out

    if note_type == "concept_note":
        allowed = {"domain", "keywords"}
        out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
        if "keywords" in out and isinstance(out["keywords"], str):
            out["keywords"] = [s.strip() for s in out["keywords"].split(",") if s.strip()]
        return out

    if note_type == "board_note":
        allowed = {"board_type", "scope", "source_count"}
        out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
        if "source_count" in out:
            try:
                out["source_count"] = int(out["source_count"])
            except Exception as exc:
                raise PKMError("Meta `source_count` của board_note phải là số nguyên.") from exc
        return out

    return {k: v for k, v in clean.items() if v not in (None, "")}
