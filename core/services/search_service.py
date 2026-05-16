"""Service tìm kiếm toàn văn trên notes và extracts qua FTS5.

SearchService đóng vai trò orchestrator giữa FTS index và business logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.search.fts_index import (
    ensure_fts_table,
    index_extract,
    index_note,
    rebuild_index,
    remove_from_index,
    search,
)
from core.search.query_parser import build_fts_query
from core.storage.models import Extract, Link, Note
from core.storage.session import get_session
from core.storage.query_optimization import list_orphan_note_ids_efficient
from core.utils.logger import get_logger

logger = get_logger()


@dataclass
class SearchResult:
    """Kết quả tìm kiếm đơn vị."""

    entity_type: str       # 'note' | 'extract'
    entity_id: int
    source_id: int | None
    title: str
    snippet: str
    extra: dict[str, Any] = field(default_factory=dict)


class SearchService:
    """Full-text search trên notes và extracts."""

    def __init__(self, db_path: str, notes_dir: Path) -> None:
        self._db_path = db_path
        self._notes_dir = Path(notes_dir)
        ensure_fts_table(db_path)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        user_query: str,
        entity_type: str | None = None,
        source_id: int | None = None,
        limit: int = 50,
        project_note_ids: set[int] | None = None,
    ) -> list[SearchResult]:
        """
        Tìm kiếm toàn văn.

        Args:
            user_query: Query người dùng nhập (raw).
            entity_type: Lọc theo loại entity: 'note' | 'extract' | None (tất cả).
            source_id: Lọc theo source.
            limit: Số kết quả tối đa.
            project_note_ids: Nếu không None, chỉ trả kết quả có entity_id thuộc
                              set này (dùng cho Project mode search).

        Returns:
            Danh sách SearchResult, được sắp xếp theo rank FTS.
        """
        fts_query = build_fts_query(user_query)
        if not fts_query:
            return []

        raw = search(self._db_path, fts_query, entity_type, source_id, limit)
        results: list[SearchResult] = []
        for r in raw:
            sr = SearchResult(
                entity_type=r["entity_type"],
                entity_id=int(r["entity_id"]),
                source_id=int(r["source_id"]) if r["source_id"] else None,
                title=r["title"] or "",
                snippet=r["snippet"] or "",
            )
            # Project mode filter: chỉ giữ note results thuộc project scope
            if project_note_ids is not None and sr.entity_type == "note":
                if sr.entity_id not in project_note_ids:
                    continue
            results.append(sr)
        return results

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def index_note_by_id(self, note_id: int) -> None:
        """Lập chỉ mục lại một note theo id."""
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                remove_from_index(self._db_path, "note", note_id)
                return
            session.expunge(note)

        note_file = Path(note.file_path)
        content = note_file.read_text(encoding="utf-8") if note_file.exists() else ""
        index_note(self._db_path, note.id, note.title, content, note.source_id)

    def index_extract_by_id(self, extract_id: int) -> None:
        """Lập chỉ mục lại một extract theo id."""
        with get_session() as session:
            ext = session.get(Extract, extract_id)
            if ext is None:
                remove_from_index(self._db_path, "extract", extract_id)
                return
            session.expunge(ext)

        index_extract(self._db_path, ext.id, ext.content_md, ext.source_id)

    def rebuild_all(self) -> int:
        """Xây lại toàn bộ FTS index. Trả về số entity đã index."""
        return rebuild_index(self._db_path, self._notes_dir)

    # ------------------------------------------------------------------
    # Note quality stats
    # ------------------------------------------------------------------

    def list_orphan_note_ids(self) -> list[int]:
        """Trả về danh sách note mồ côi (không incoming, không outgoing links).
        
        Optimized: Dùng subquery thay vì N+1 pattern (1 query tìm notes + 2*N queries cho links).
        """
        with get_session() as session:
            return list_orphan_note_ids_efficient(session)

    def count_notes_by_type(self) -> dict[str, int]:
        """Đếm số note theo note_type (chỉ lấy note chưa xóa)."""
        with get_session() as session:
            rows = session.query(Note.note_type).filter(Note.is_deleted == 0).all()
        stats: dict[str, int] = {}
        for row in rows:
            note_type = str(row[0])
            stats[note_type] = stats.get(note_type, 0) + 1
        return stats
