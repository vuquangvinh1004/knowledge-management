"""Service quản lý tags và gán tag cho note."""
from __future__ import annotations

from datetime import datetime, timezone

from core.storage.models import Note, NoteTag, Tag
from core.storage.session import get_session
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()


class TagService:
    """CRUD tags và quản lý note–tag relationship."""

    def get_or_create_tag(self, name: str, color: str | None = None) -> Tag:
        """
        Tìm tag theo tên hoặc tạo mới nếu chưa tồn tại.
        Tên tag được normalize về lowercase+strip.
        """
        name = name.strip().lower()
        if not name:
            raise PKMError("Tên tag không được để trống.")

        with get_session() as session:
            tag = session.query(Tag).filter(Tag.name == name).first()
            if tag is None:
                tag = Tag(name=name, color=color, created_at=datetime.now(timezone.utc))
                session.add(tag)
                session.flush()
                logger.info(f"Tạo tag mới: {name!r}")
            session.expunge(tag)
        return tag

    def list_tags(self) -> list[Tag]:
        """Lấy danh sách tất cả tags theo tên."""
        with get_session() as session:
            tags = session.query(Tag).order_by(Tag.name).all()
            for t in tags:
                session.expunge(t)
            return tags

    def add_tag_to_note(self, note_id: int, tag_name: str) -> None:
        """Gắn tag vào note. Nếu tag chưa tồn tại sẽ được tạo mới."""
        tag = self.get_or_create_tag(tag_name)
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise PKMError(f"Không tìm thấy note id={note_id}.")
            exists = (
                session.query(NoteTag)
                .filter(NoteTag.note_id == note_id, NoteTag.tag_id == tag.id)
                .first()
            )
            if not exists:
                session.add(NoteTag(note_id=note_id, tag_id=tag.id))
                logger.debug(f"Gắn tag {tag.name!r} vào note id={note_id}")

    def remove_tag_from_note(self, note_id: int, tag_name: str) -> None:
        """Gỡ tag khỏi note."""
        name = tag_name.strip().lower()
        with get_session() as session:
            tag = session.query(Tag).filter(Tag.name == name).first()
            if tag is None:
                return
            note_tag = (
                session.query(NoteTag)
                .filter(NoteTag.note_id == note_id, NoteTag.tag_id == tag.id)
                .first()
            )
            if note_tag:
                session.delete(note_tag)
                logger.debug(f"Gỡ tag {name!r} khỏi note id={note_id}")

    def get_tags_for_note(self, note_id: int) -> list[Tag]:
        """Lấy danh sách tags của một note."""
        with get_session() as session:
            note_tags = (
                session.query(NoteTag)
                .filter(NoteTag.note_id == note_id)
                .all()
            )
            tags = []
            for nt in note_tags:
                tag = session.get(Tag, nt.tag_id)
                if tag:
                    session.expunge(tag)
                    tags.append(tag)
            return tags

    def delete_tag(self, tag_id: int) -> None:
        """Xóa tag khỏi DB (và tất cả note_tags liên quan theo cascade)."""
        with get_session() as session:
            tag = session.get(Tag, tag_id)
            if tag:
                session.delete(tag)
                logger.info(f"Xóa tag id={tag_id}")
