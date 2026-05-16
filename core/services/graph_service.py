"""Service build do thi lien ket ghi chu (Phase A)."""
from __future__ import annotations

from dataclasses import dataclass, field

from core.storage.models import Link, Note, NoteTag, Tag
from core.storage.session import get_session
from core.utils.constants import NOTE_TYPES
from core.utils.exceptions import PKMError


@dataclass
class GraphNode:
    """Node do thi dai dien cho mot note."""

    note_id: int
    title: str
    slug: str
    note_type: str
    source_id: int | None
    source_code: str | None = None  # AA00-ZZ99 để hiển thị cho source_note
    tags: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Edge co huong giua hai notes."""

    from_note_id: int
    to_note_id: int
    link_type: str
    weight: int = 1  # số lần wikilink xuất hiện


@dataclass
class GraphSnapshot:
    """Snapshot do thi voi danh sach nodes/edges."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    is_virtualized: bool = False
    virtualized_from: int = 0


class GraphService:
    """Sinh graph data tu notes + links + tags voi bo loc co ban."""

    def build_graph(
        self,
        *,
        note_type: str | None = None,
        tag: str | None = None,
        source_id: int | None = None,
        source_code: str | None = None,
        include_isolated: bool = True,
        limit_nodes: int | None = None,
    ) -> GraphSnapshot:
        """
        Tao graph snapshot tu du lieu thuc trong DB.

        Args:
            note_type: Loc theo loai note.
            tag: Loc theo ten tag (lowercase normalize).
            source_id: Loc theo source_id (legacy contract).
            source_code: Loc theo source_code (AA00-ZZ99) — tra cuu sang source_id.
            include_isolated: Neu False, bo cac node khong co edge.
            limit_nodes: Gioi han so node de virtualize graph lon.
        """
        if note_type is not None and note_type not in NOTE_TYPES:
            raise PKMError(f"note_type khong hop le: {note_type!r}")

        tag_name = tag.strip().lower() if tag else None

        # source_code có độ ưu tiên cao hơn source_id nếu cùng cung cấp.
        if source_code:
            from core.storage.models import Source as SourceModel
            with get_session() as s:
                src = (
                    s.query(SourceModel)
                    .filter(SourceModel.source_code == source_code.strip().upper())
                    .first()
                )
                if src is None:
                    return GraphSnapshot()
                source_id = src.id

        with get_session() as session:
            notes_query = session.query(Note).filter(Note.is_deleted == 0)

            if note_type is not None:
                notes_query = notes_query.filter(Note.note_type == note_type)

            if source_id is not None:
                notes_query = notes_query.filter(Note.source_id == source_id)

            if tag_name:
                tagged_ids = [
                    row[0]
                    for row in (
                        session.query(NoteTag.note_id)
                        .join(Tag, Tag.id == NoteTag.tag_id)
                        .filter(Tag.name == tag_name)
                        .all()
                    )
                ]
                if not tagged_ids:
                    return GraphSnapshot()
                notes_query = notes_query.filter(Note.id.in_(tagged_ids))

            notes = notes_query.order_by(Note.updated_at.desc()).all()
            if not notes:
                return GraphSnapshot()

            note_ids = [n.id for n in notes]

            tag_rows = (
                session.query(NoteTag.note_id, Tag.name)
                .join(Tag, Tag.id == NoteTag.tag_id)
                .filter(NoteTag.note_id.in_(note_ids))
                .all()
            )
            tag_map: dict[int, list[str]] = {}
            for note_id_val, tag_name_val in tag_rows:
                tag_map.setdefault(note_id_val, []).append(tag_name_val)

            # Lấy source_code cho source_note nodes
            source_ids = [n.source_id for n in notes if n.source_id is not None]
            source_code_map: dict[int, str | None] = {}
            if source_ids:
                from core.storage.models import Source as SourceModel
                src_rows = (
                    session.query(SourceModel.id, SourceModel.source_code)
                    .filter(SourceModel.id.in_(source_ids))
                    .all()
                )
                source_code_map = {row[0]: row[1] for row in src_rows}

            links = (
                session.query(Link)
                .filter(
                    Link.from_note_id.in_(note_ids),
                    Link.to_note_id.in_(note_ids),
                )
                .all()
            )

            if not include_isolated:
                connected_ids: set[int] = set()
                for link in links:
                    connected_ids.add(link.from_note_id)
                    connected_ids.add(link.to_note_id)
                notes = [n for n in notes if n.id in connected_ids]
                if not notes:
                    return GraphSnapshot()
                note_ids = [n.id for n in notes]
                links = [
                    l
                    for l in links
                    if l.from_note_id in note_ids and l.to_note_id in note_ids
                ]

            nodes = [
                GraphNode(
                    note_id=n.id,
                    title=n.title,
                    slug=n.slug,
                    note_type=n.note_type,
                    source_id=n.source_id,
                    source_code=source_code_map.get(n.source_id) if n.source_id else None,
                    tags=sorted(set(tag_map.get(n.id, []))),
                )
                for n in notes
            ]

            edges = [
                GraphEdge(
                    from_note_id=lnk.from_note_id,
                    to_note_id=lnk.to_note_id,
                    link_type=lnk.link_type,
                    weight=lnk.weight if lnk.weight is not None else 1,
                )
                for lnk in links
            ]

        snapshot = GraphSnapshot(nodes=nodes, edges=edges)

        if limit_nodes is not None and limit_nodes > 0 and len(snapshot.nodes) > limit_nodes:
            snapshot = self._virtualize_snapshot(snapshot, limit_nodes)

        return snapshot

    def _virtualize_snapshot(self, snapshot: GraphSnapshot, limit_nodes: int) -> GraphSnapshot:
        """Giam tai rendering bang cach giu node quan trong nhat theo degree."""
        degree_map: dict[int, int] = {n.note_id: 0 for n in snapshot.nodes}
        for edge in snapshot.edges:
            if edge.from_note_id in degree_map:
                degree_map[edge.from_note_id] += 1
            if edge.to_note_id in degree_map:
                degree_map[edge.to_note_id] += 1

        ranked_nodes = sorted(
            snapshot.nodes,
            key=lambda n: (
                degree_map.get(n.note_id, 0),
                len(n.tags),
                n.title.lower(),
            ),
            reverse=True,
        )

        kept_nodes = ranked_nodes[:limit_nodes]
        kept_ids = {n.note_id for n in kept_nodes}
        kept_edges = [
            e
            for e in snapshot.edges
            if e.from_note_id in kept_ids and e.to_note_id in kept_ids
        ]

        return GraphSnapshot(
            nodes=kept_nodes,
            edges=kept_edges,
            is_virtualized=True,
            virtualized_from=len(snapshot.nodes),
        )
