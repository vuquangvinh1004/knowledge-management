"""Service quản lý liên kết hai chiều giữa notes (wikilink / manual / inferred)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Link, Note
from core.storage.session import get_session
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()

LINK_TYPES = frozenset({"wikilink", "manual", "inferred"})


class LinkService:
    """Tạo, đọc và xóa links giữa notes."""

    def create_link(
        self,
        from_note_id: int,
        to_note_id: int,
        link_type: str = "manual",
    ) -> Link:
        """
        Tạo link từ một note đến note khác.

        Raises:
            PKMError: Nếu link_type không hợp lệ hoặc link đã tồn tại.
        """
        if link_type not in LINK_TYPES:
            raise PKMError(f"link_type không hợp lệ: {link_type!r}")
        if from_note_id == to_note_id:
            raise PKMError("Không thể tạo link tự trỏ đến chính nó.")

        with get_session() as session:
            existing = (
                session.query(Link)
                .filter(
                    Link.from_note_id == from_note_id,
                    Link.to_note_id == to_note_id,
                    Link.link_type == link_type,
                )
                .first()
            )
            if existing:
                session.expunge(existing)
                return existing

            link = Link(
                from_note_id=from_note_id,
                to_note_id=to_note_id,
                link_type=link_type,
                created_at=datetime.now(timezone.utc),
            )
            session.add(link)
            session.flush()
            session.expunge(link)

        logger.debug(f"Tạo link {from_note_id}→{to_note_id} type={link_type!r}")
        return link

    def get_backlinks(self, note_id: int) -> list[Link]:
        """Lấy tất cả link trỏ đến note này (backlinks)."""
        with get_session() as session:
            links = (
                session.query(Link)
                .filter(Link.to_note_id == note_id)
                .all()
            )
            for lnk in links:
                session.expunge(lnk)
            return links

    def get_outgoing_links(self, note_id: int) -> list[Link]:
        """Lấy tất cả link đi ra từ note này."""
        with get_session() as session:
            links = (
                session.query(Link)
                .filter(Link.from_note_id == note_id)
                .all()
            )
            for lnk in links:
                session.expunge(lnk)
            return links

    def delete_link(self, link_id: int) -> None:
        """Xóa link khỏi DB."""
        with get_session() as session:
            link = session.get(Link, link_id)
            if link is None:
                raise PKMError(f"Không tìm thấy link id={link_id}.")
            session.delete(link)
            logger.debug(f"Xóa link id={link_id}")

    def delete_links_for_note(self, note_id: int) -> None:
        """Xóa tất cả links (outgoing + incoming) của một note."""
        with get_session() as session:
            session.query(Link).filter(
                (Link.from_note_id == note_id) | (Link.to_note_id == note_id)
            ).delete(synchronize_session="fetch")
            logger.debug(f"Xóa tất cả links của note id={note_id}")

    def resolve_wikilink(self, slug_or_title: str) -> Note | None:
        """
        Tìm note tương ứng với [[wikilink]] theo slug hoặc title.

        Returns:
            Note nếu tìm thấy, None nếu không có.
        """
        from core.utils.helpers import slugify
        target_slug = slugify(slug_or_title)

        with get_session() as session:
            note = (
                session.query(Note)
                .filter(
                    (Note.slug == target_slug) | (Note.title == slug_or_title),
                    Note.is_deleted == 0,
                )
                .first()
            )
            if note:
                session.expunge(note)
            return note

    def resolve_wikilinks_in_note(self, note_id: int, content: str | None = None) -> tuple[list[int], int]:
        """
        Parse markdown content của note, tìm [[wikilinks]], resolve thành note targets.
        
        Cập nhật DB links để match với wikilinks hiện tại trong note.
        Xóa wikilinks cũ không còn xuất hiện, tạo links mới.
        
        Args:
            note_id: ID của note.
            content: Markdown content (nếu None, sẽ load từ file).
        
        Returns:
            Tuple (resolved_note_ids, weight) - danh sách note IDs được link đến, tổng weight.
        """
        # Load content nếu không được truyền vào
        if content is None:
            from core.services.note_service import NoteService
            note_service = NoteService(Path(__file__).parent.parent.parent / "data" / "notes")
            try:
                content = note_service.read_content(note_id)
            except Exception as e:
                logger.warning(f"Không thể load content note id={note_id}: {e}")
                return [], 0
        
        # Parse wikilinks từ content theo pattern [[...]]
        # Hỗ trợ [[slug]], [[slug|display text]], [[#anchor]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        wikilinks = re.findall(pattern, content)
        
        if not wikilinks:
            # Nếu không có wikilink nào, xóa tất cả outgoing wikilinks
            self.cleanup_outgoing_wikilinks(note_id, set())
            return [], 0
        
        # Count occurrences từng wikilink
        link_counts: dict[str, int] = {}
        for link in wikilinks:
            link_text = link.strip()
            if link_text:
                link_counts[link_text] = link_counts.get(link_text, 0) + 1
        
        # Resolve từng wikilink đến note target
        resolved_ids: list[int] = []
        with get_session() as session:
            for link_text, count in link_counts.items():
                target = self.resolve_wikilink(link_text)
                if target is None:
                    logger.debug(f"Wikilink [[{link_text}]] không thể resolve trong note id={note_id}")
                    continue
                
                # Tạo hoặc cập nhật link với weight
                link = self.upsert_wikilink(note_id, target.id, weight=count)
                resolved_ids.append(target.id)
        
        # Cleanup wikilinks cũ không còn xuất hiện
        self.cleanup_outgoing_wikilinks(note_id, set(resolved_ids))
        
        total_weight = sum(link_counts.values())
        logger.debug(
            f"Resolved {len(resolved_ids)} wikilinks trong note id={note_id} "
            f"(total weight={total_weight})"
        )
        
        return resolved_ids, total_weight

    # ------------------------------------------------------------------
    # Wikilink helpers
    # ------------------------------------------------------------------

    def upsert_wikilink(
        self,
        from_note_id: int,
        to_note_id: int,
        weight: int = 1,
    ) -> Link:
        """Tạo hoặc cập nhật wikilink với weight (số lần xuất hiện)."""
        if from_note_id == to_note_id:
            raise PKMError("Không thể tạo link tự trỏ đến chính nó.")

        with get_session() as session:
            existing = (
                session.query(Link)
                .filter(
                    Link.from_note_id == from_note_id,
                    Link.to_note_id == to_note_id,
                    Link.link_type == "wikilink",
                )
                .first()
            )
            if existing:
                existing.weight = max(1, weight)
                session.flush()
                session.expunge(existing)
                return existing

            link = Link(
                from_note_id=from_note_id,
                to_note_id=to_note_id,
                link_type="wikilink",
                weight=max(1, weight),
                created_at=datetime.now(timezone.utc),
            )
            session.add(link)
            session.flush()
            session.expunge(link)
        logger.debug(
            f"Upsert wikilink {from_note_id}→{to_note_id} weight={weight}"
        )
        return link

    def cleanup_outgoing_wikilinks(
        self,
        from_note_id: int,
        keep_target_ids: set[int],
    ) -> None:
        """Xóa các wikilink outgoing không còn xuất hiện trong nội dung note.
        
        Sau khi xóa link, cũng xóa concept stub nào không còn được trỏ đến từ đâu.
        """
        with get_session() as session:
            existing = (
                session.query(Link)
                .filter(
                    Link.from_note_id == from_note_id,
                    Link.link_type == "wikilink",
                )
                .all()
            )
            # Thu thập các target bị xóa để check xem có orphan không
            deleted_targets = set()
            for lnk in existing:
                if lnk.to_note_id not in keep_target_ids:
                    deleted_targets.add(lnk.to_note_id)
                    logger.debug(
                        f"Xóa wikilink orphan {from_note_id}→{lnk.to_note_id}"
                    )
                    session.delete(lnk)
            session.commit()
        
        # Xóa concept stubs không còn được trỏ đến từ đâu
        if deleted_targets:
            self._delete_orphan_concept_stubs(deleted_targets)

    def _delete_orphan_concept_stubs(self, note_ids: set[int]) -> None:
        """Xóa concept note stubs nếu không còn link nào trỏ đến (incoming edges)."""
        with get_session() as session:
            for note_id in note_ids:
                # Kiểm tra xem note có incoming link không
                incoming = session.query(Link).filter(
                    Link.to_note_id == note_id
                ).first()
                if incoming is not None:
                    continue  # Còn link trỏ đến, giữ lại
                
                # Kiểm tra xem note có outgoing link không
                outgoing = session.query(Link).filter(
                    Link.from_note_id == note_id
                ).first()
                if outgoing is not None:
                    continue  # Còn link từ note này, giữ lại
                
                # Xóa concept stub nếu không có link nào
                note = session.query(Note).filter(Note.id == note_id).first()
                if note and note.note_type == "concept_note":
                    logger.debug(
                        f"Xóa orphan concept stub: {note.title} (id={note_id})"
                    )
                    session.delete(note)
            session.commit()
