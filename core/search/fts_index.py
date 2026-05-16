"""Quản lý FTS5 virtual table để tìm kiếm toàn văn trên notes và extracts.

Sử dụng sqlite3 trực tiếp vì SQLAlchemy không hỗ trợ FTS5 first-class.
Bảng được tạo IF NOT EXISTS khi khởi động — không cần Alembic migration.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from core.utils.logger import get_logger

logger = get_logger()

_FTS_TABLE = "fts_content"


def ensure_fts_table(db_path: str) -> None:
    """Tạo FTS5 virtual table nếu chưa tồn tại."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {_FTS_TABLE}
            USING fts5(
                entity_type,
                entity_id UNINDEXED,
                source_id UNINDEXED,
                title,
                content,
                tokenize='unicode61'
            )
            """
        )
        conn.commit()
    logger.debug("FTS5 table sẵn sàng.")


def index_note(
    db_path: str,
    note_id: int,
    title: str,
    content: str,
    source_id: int | None = None,
) -> None:
    """Lập chỉ mục hoặc cập nhật chỉ mục cho một note."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM {_FTS_TABLE} WHERE entity_type='note' AND entity_id=?",
            (note_id,),
        )
        conn.execute(
            f"INSERT INTO {_FTS_TABLE}(entity_type, entity_id, source_id, title, content) VALUES (?,?,?,?,?)",
            ("note", note_id, source_id or 0, title, content),
        )
        conn.commit()


def index_extract(
    db_path: str,
    extract_id: int,
    content: str,
    source_id: int,
    title: str = "",
) -> None:
    """Lập chỉ mục hoặc cập nhật chỉ mục cho một extract."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM {_FTS_TABLE} WHERE entity_type='extract' AND entity_id=?",
            (extract_id,),
        )
        conn.execute(
            f"INSERT INTO {_FTS_TABLE}(entity_type, entity_id, source_id, title, content) VALUES (?,?,?,?,?)",
            ("extract", extract_id, source_id, title, content),
        )
        conn.commit()


def remove_from_index(db_path: str, entity_type: str, entity_id: int) -> None:
    """Xóa entity khỏi FTS index."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            f"DELETE FROM {_FTS_TABLE} WHERE entity_type=? AND entity_id=?",
            (entity_type, entity_id),
        )
        conn.commit()


def search(
    db_path: str,
    query: str,
    entity_type: str | None = None,
    source_id: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Tìm kiếm FTS5.

    Returns:
        List[dict] với keys: entity_type, entity_id, source_id, title, snippet.
    """
    if not query.strip():
        return []

    conditions = ["fts_content MATCH ?"]
    params: list[Any] = [query]

    if entity_type:
        conditions.append("entity_type = ?")
        params.append(entity_type)
    if source_id is not None:
        conditions.append("source_id = ?")
        params.append(source_id)

    where = " AND ".join(conditions)
    sql = (
        f"SELECT entity_type, entity_id, source_id, title, "
        f"snippet({_FTS_TABLE}, 4, '**', '**', '...', 10) AS snippet "
        f"FROM {_FTS_TABLE} WHERE {where} "
        f"ORDER BY rank LIMIT ?"
    )
    params.append(limit)

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.OperationalError as exc:
        logger.warning(f"FTS search lỗi: {exc}")
        return []


def rebuild_index(db_path: str, notes_dir: Path) -> int:
    """
    Xây lại toàn bộ FTS index từ DB + file.

    Returns:
        Số entity đã index.
    """
    import json
    from core.storage.connection import get_engine
    from core.storage.models import Note, Extract
    from sqlalchemy.orm import Session

    engine = get_engine()
    count = 0

    with sqlite3.connect(db_path) as conn:
        conn.execute(f"DELETE FROM {_FTS_TABLE}")
        conn.commit()

    with Session(engine) as session:
        notes = session.query(Note).filter(Note.is_deleted == 0).all()
        for note in notes:
            try:
                note_file = Path(note.file_path)
                content = note_file.read_text(encoding="utf-8") if note_file.exists() else ""
            except OSError:
                content = ""
            index_note(db_path, note.id, note.title, content, note.source_id)
            count += 1

        extracts = session.query(Extract).all()
        for ext in extracts:
            index_extract(db_path, ext.id, ext.content_md, ext.source_id)
            count += 1

    logger.info(f"Rebuilt FTS index: {count} items.")
    return count
