"""Đổi tên source_note cũ theo format mới `source - {Tác giả} ({Năm})`.

Revision ID: 0006_rename_source_note_titles
Revises: 0005_add_note_meta_json
Create Date: 2026-04-24
"""
from __future__ import annotations

import json
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_rename_source_note_titles"
down_revision: Union[str, None] = "0005_add_note_meta_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize_year(year: str | None) -> str | None:
    if not year:
        return None
    digits = "".join(ch for ch in str(year) if ch.isdigit())
    if len(digits) >= 4:
        candidate = digits[:4]
        if 1900 <= int(candidate) <= 2100:
            return candidate
    return None


def _extract_author_surnames(authors: str | None) -> list[str]:
    if not authors:
        return []
    raw = str(authors).strip()
    if not raw:
        return []

    normalized = re.sub(r"\s+(and|&|va)\s+", ";", raw, flags=re.IGNORECASE)
    parts = [p.strip() for p in re.split(r";", normalized) if p.strip()]
    if not parts:
        return []

    surnames: list[str] = []
    for part in parts:
        if "," in part:
            surname = part.split(",", 1)[0].strip()
        else:
            tokens = part.split()
            surname = tokens[-1].strip() if tokens else ""
        if surname:
            surnames.append(surname)
    return surnames


def _build_source_note_title(authors: str | None, year: str | None, fallback_title: str) -> str:
    surnames = _extract_author_surnames(authors)
    year_part = _normalize_year(year)

    author_part: str | None = None
    if len(surnames) >= 3:
        author_part = f"{surnames[0]} et al."
    elif len(surnames) == 2:
        author_part = f"{surnames[0]} & {surnames[1]}"
    elif len(surnames) == 1:
        author_part = surnames[0]

    if author_part and year_part:
        return f"source - {author_part} ({year_part})"
    if author_part:
        return f"source - {author_part}"
    if year_part:
        return f"source - ({year_part})"
    return fallback_title.strip() or "source_note"


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT n.id, n.title, n.meta_json, s.authors, s.year
            FROM notes n
            LEFT JOIN sources s ON s.id = n.source_id
            WHERE n.note_type = 'source_note' AND n.source_id IS NOT NULL
            """
        )
    ).fetchall()

    for row in rows:
        note_id = int(row[0])
        old_title = str(row[1] or "")
        meta_raw = row[2]
        src_authors = row[3]
        src_year = row[4]

        meta_author = None
        meta_year = None
        if meta_raw:
            try:
                parsed = json.loads(str(meta_raw))
                if isinstance(parsed, dict):
                    meta_author = parsed.get("author")
                    meta_year = parsed.get("year")
            except Exception:
                pass

        effective_authors = str(meta_author).strip() if meta_author else str(src_authors or "").strip()
        effective_year = str(meta_year).strip() if meta_year else str(src_year or "").strip()
        new_title = _build_source_note_title(
            authors=effective_authors or None,
            year=effective_year or None,
            fallback_title=old_title,
        )

        if new_title != old_title:
            bind.execute(
                sa.text(
                    "UPDATE notes SET title = :title WHERE id = :note_id"
                ),
                {"title": new_title, "note_id": note_id},
            )


def downgrade() -> None:
    # Data migration này không thể rollback an toàn về title cũ.
    pass
