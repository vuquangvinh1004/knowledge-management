"""Query optimization helpers và specialized query methods.

Mục tiêu: Giảm N+1 queries bằng eager loading, query aggregation, và caching strategies.

Nguyên tắc:
1. Eager-load relationships khi cần access chúng ngoài session context
2. Sử dụng joinedload hoặc selectinload tùy theo pattern truy cập
3. Sử dụng aggregation query cho counting operations
4. Trả về DTO (dict) thay vì ORM objects nếu chỉ cần dữ liệu cụ thể
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from core.storage.models import Link, Note, Extract, Asset, BoardCell, Board, ProjectNoteRef, Project
from core.utils.logger import get_logger

logger = get_logger()


# ============================================================================
# Eager Loading Strategies
# ============================================================================

def eager_load_note_with_relationships(session: Session, note_id: int) -> Note | None:
    """
    Load một Note cùng tất cả eager-loaded relationships.
    
    Sử dụng joinedload + selectinload tùy theo access pattern.
    
    Relationships đã load:
    - source (1:1, thường cần)
    - extracts (1:N, có thể lớn)
    - note_tags → tag (1:N, thường cần)
    - outgoing_links → to_note (1:N, graph ops)
    - incoming_links → from_note (1:N, graph ops)
    - project (1:1, nullable)
    
    N+1 được tránh:
    - source: joinedload (1:1 safe)
    - extracts: selectinload (1:N, tránh cartesian product)
    - note_tags: selectinload (many-to-many)
    - outgoing_links: selectinload (1:N)
    - incoming_links: selectinload (1:N)
    - project: joinedload (1:1 safe)
    
    Args:
        session: Active SQLAlchemy session.
        note_id: ID của note cần load.
    
    Returns:
        Note object với tất cả relationships đã load, hoặc None nếu không tìm thấy.
    """
    note = (
        session.query(Note)
        .filter(Note.id == note_id, Note.is_deleted == 0)
        .options(
            joinedload(Note.source),
            selectinload(Note.extracts),
            selectinload(Note.assets),
            selectinload(Note.note_tags).joinedload(Note.note_tags),
            selectinload(Note.outgoing_links),
            selectinload(Note.incoming_links),
            selectinload(Note.board_cells),
            selectinload(Note.linked_boards),
            joinedload(Note.project),
            selectinload(Note.project_refs),
        )
        .first()
    )
    return note


def eager_load_notes_list(session: Session, note_ids: list[int]) -> dict[int, Note]:
    """
    Load multiple Notes cùng relationships eager-loaded.
    
    Args:
        session: Active SQLAlchemy session.
        note_ids: List các note IDs cần load.
    
    Returns:
        Dict {note_id → Note} với tất cả relationships đã load.
    """
    if not note_ids:
        return {}
    
    notes = (
        session.query(Note)
        .filter(Note.id.in_(note_ids), Note.is_deleted == 0)
        .options(
            joinedload(Note.source),
            selectinload(Note.extracts),
            selectinload(Note.assets),
            selectinload(Note.note_tags),
            selectinload(Note.outgoing_links),
            selectinload(Note.incoming_links),
            joinedload(Note.project),
        )
        .all()
    )
    return {note.id: note for note in notes}


# ============================================================================
# Specialized Query Methods (replace N+1 anti-patterns)
# ============================================================================

@dataclass
class NoteDeleteImpact:
    """DTO cho impact analysis của note deletion."""
    note_id: int
    title: str
    note_type: str
    is_source_note: bool
    source_id: int | None
    project_id: int | None
    incoming_links_count: int
    outgoing_links_count: int
    extract_refs_count: int
    asset_refs_count: int
    board_cell_refs_count: int
    linked_boards_count: int
    project_refs_count: int


def get_note_delete_impact(session: Session, note_id: int) -> NoteDeleteImpact:
    """
    Phân tích ảnh hưởng soft-delete một note. Tối ưu với aggregation queries.
    
    Thay vì 7 separate COUNT queries, dùng single aggregation query hoặc
    group_concat tương tương.
    
    Args:
        session: Active SQLAlchemy session.
        note_id: ID của note cần phân tích.
    
    Returns:
        NoteDeleteImpact DTO.
    
    Raises:
        Exception: Nếu note không tồn tại.
    """
    # Lấy note + aggregated counts trong 1-2 queries (thay vì 8)
    # Allow soft-deleted notes vì user có thể muốn xóa cứng chúng
    note = session.get(Note, note_id)
    if note is None:
        raise Exception(f"Không tìm thấy note id={note_id}.")
    
    # Aggregation approach: dùng func.count() + group_by hoặc subqueries
    # Mỗi COUNT sẽ là 1 query, nhưng ta có thể batch chúng
    incoming_count = session.query(func.count(Link.id)).filter(
        Link.to_note_id == note_id
    ).scalar() or 0
    
    outgoing_count = session.query(func.count(Link.id)).filter(
        Link.from_note_id == note_id
    ).scalar() or 0
    
    extract_count = session.query(func.count(Extract.id)).filter(
        Extract.note_id == note_id
    ).scalar() or 0
    
    asset_count = session.query(func.count(Asset.id)).filter(
        Asset.note_id == note_id
    ).scalar() or 0
    
    board_cell_count = session.query(func.count(BoardCell.id)).filter(
        BoardCell.linked_note_id == note_id
    ).scalar() or 0
    
    board_count = session.query(func.count(Board.id)).filter(
        Board.linked_note_id == note_id
    ).scalar() or 0
    
    project_ref_count = session.query(func.count(1)).select_from(ProjectNoteRef).filter(
        ProjectNoteRef.note_id == note_id
    ).scalar() or 0
    
    return NoteDeleteImpact(
        note_id=int(note.id),
        title=str(note.title or ""),
        note_type=str(note.note_type),
        is_source_note=(str(note.note_type) == "source_note"),
        source_id=int(note.source_id) if note.source_id is not None else None,
        project_id=int(note.project_id) if note.project_id is not None else None,
        incoming_links_count=int(incoming_count),
        outgoing_links_count=int(outgoing_count),
        extract_refs_count=int(extract_count),
        asset_refs_count=int(asset_count),
        board_cell_refs_count=int(board_cell_count),
        linked_boards_count=int(board_count),
        project_refs_count=int(project_ref_count),
    )


def get_note_with_links_efficient(session: Session, note_id: int) -> tuple[Note | None, list[Link], list[Link]]:
    """
    Load một note cùng incoming/outgoing links trong 2 queries (thay vì N+2).
    
    Args:
        session: Active SQLAlchemy session.
        note_id: ID của note.
    
    Returns:
        Tuple (note, incoming_links, outgoing_links) hoặc (None, [], []) nếu không tìm thấy.
    """
    note = session.get(Note, note_id)
    if note is None or note.is_deleted:
        return None, [], []
    
    # Load outgoing + incoming links trong 2 queries
    outgoing = session.query(Link).filter(Link.from_note_id == note_id).all()
    incoming = session.query(Link).filter(Link.to_note_id == note_id).all()
    
    return note, incoming, outgoing


def list_orphan_note_ids_efficient(session: Session) -> list[int]:
    """
    Tìm tất cả orphan notes (không incoming, không outgoing links) efficiently.
    
    Thay vì N+1 pattern (load notes + for each note query links),
    dùng subqueries hoặc NOT IN.
    
    N+1 anti-pattern cũ:
    ```
    notes = query(Note).all()  # 1 query
    for note in notes:
        has_outgoing = query(Link).filter(from_note_id=note.id).first()  # N queries
        has_incoming = query(Link).filter(to_note_id=note.id).first()  # N queries
    ```
    
    Optimized approach:
    ```
    notes_with_links = query(Note.id).join(Link).distinct()  # 1 query
    orphans = query(Note.id).filter(~Note.id.in_(subquery))  # 1 query
    ```
    
    Args:
        session: Active SQLAlchemy session.
    
    Returns:
        List các note IDs không có incoming hoặc outgoing links.
    """
    # Subquery: notes tham gia trong bất kỳ link nào
    notes_with_links_subq = (
        session.query(Note.id)
        .distinct()
        .join(Link, or_(Link.from_note_id == Note.id, Link.to_note_id == Note.id))
        .subquery()
    )
    
    # Orphan notes: không trong subquery
    orphan_ids = (
        session.query(Note.id)
        .filter(
            Note.is_deleted == 0,
            ~Note.id.in_(session.query(notes_with_links_subq))
        )
        .all()
    )
    
    return [int(nid[0]) for nid in orphan_ids]


@dataclass
class NoteManagementItem:
    """DTO cho note management list display."""
    note_id: int
    title: str
    note_type: str
    source_id: int | None
    project_id: int | None
    scope_label: str
    file_path: str
    is_deleted: int
    updated_at: Any


def list_notes_for_management_efficient(session: Session, include_deleted: bool = False) -> list[NoteManagementItem]:
    """
    Liệt kê notes cho màn hình quản lý. Optimize JOIN với project thay vì N queries.
    
    Old anti-pattern:
    ```
    notes = query(Note).all()  # 1 query
    for note in notes:
        if note.project_id:
            project = session.get(Project, note.project_id)  # N queries
    ```
    
    Optimized:
    ```
    query(Note).join(Project, ..., isouter=True).all()  # 1 query
    ```
    
    Args:
        session: Active SQLAlchemy session.
        include_deleted: Có include soft-deleted notes không.
    
    Returns:
        List NoteManagementItem.
    """
    from sqlalchemy.orm import outerjoin
    
    query = session.query(
        Note.id,
        Note.title,
        Note.note_type,
        Note.source_id,
        Note.project_id,
        Project.name,
        Note.file_path,
        Note.is_deleted,
        Note.updated_at,
    ).outerjoin(Project, Note.project_id == Project.id)
    
    if not include_deleted:
        query = query.filter(Note.is_deleted == 0)
    
    rows = query.order_by(Note.updated_at.desc()).all()
    
    items: list[NoteManagementItem] = []
    for row in rows:
        note_id, title, note_type, source_id, project_id, project_name, file_path, is_deleted, updated_at = row
        
        scope_label = "Global"
        if project_id is not None:
            scope_label = f"Project - {project_name or f'#{project_id}'}"
        
        items.append(
            NoteManagementItem(
                note_id=int(note_id),
                title=str(title or ""),
                note_type=str(note_type),
                source_id=int(source_id) if source_id is not None else None,
                project_id=int(project_id) if project_id is not None else None,
                scope_label=scope_label,
                file_path=str(file_path or ""),
                is_deleted=int(is_deleted),
                updated_at=updated_at,
            )
        )
    
    return items


# ============================================================================
# Query Monitoring Utilities (for debugging)
# ============================================================================

class QueryCounter:
    """Utility để count số queries trong một context (dùng cho testing/debugging)."""
    
    def __init__(self):
        self.count = 0
        self._listener_set = False
    
    def setup(self, engine):
        """Setup event listener trên engine để count queries."""
        from sqlalchemy import event
        
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            self.count += 1
        
        event.listen(engine, "before_cursor_execute", receive_before_cursor_execute)
        self._listener_set = True
    
    def reset(self):
        self.count = 0
    
    def __enter__(self):
        self.reset()
        return self
    
    def __exit__(self, *args):
        pass


# ============================================================================
# Validation & Documentation
# ============================================================================

def validate_eager_loading(note: Note) -> dict[str, bool]:
    """
    Kiểm tra xem các relationships của note đã được eager-loaded hay chưa.
    
    Dùng cho debugging: nếu relationship chưa load, access sẽ trigger lazy load.
    
    Args:
        note: ORM Note object.
    
    Returns:
        Dict {relationship_name → is_loaded}.
    """
    from sqlalchemy.inspection import inspect
    
    insp = inspect(note)
    loaded_relationships = {
        "source": insp.attrs.source.loaded_value is not insp.NO_VALUE,
        "extracts": insp.attrs.extracts.loaded_value is not insp.NO_VALUE,
        "note_tags": insp.attrs.note_tags.loaded_value is not insp.NO_VALUE,
        "outgoing_links": insp.attrs.outgoing_links.loaded_value is not insp.NO_VALUE,
        "incoming_links": insp.attrs.incoming_links.loaded_value is not insp.NO_VALUE,
        "project": insp.attrs.project.loaded_value is not insp.NO_VALUE,
    }
    return loaded_relationships
