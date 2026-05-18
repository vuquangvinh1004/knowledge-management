"""SQLAlchemy ORM models cho schema v1.

Tất cả thay đổi schema phải đi qua Alembic migration.
Không sửa trực tiếp bảng production.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, relationship

# NOTE: Import order matters for FK resolution
# Project must be defined before Note because Note references projects.id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# projects
# ---------------------------------------------------------------------------

class Project(Base):
    """Dự án nghiên cứu. Chứa các note riêng và tham chiếu đến Global notes."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String(16), nullable=False, default="active")  # active | closed | archived
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
    closed_at = Column(DateTime, nullable=True)
    meta_json = Column(Text)

    own_notes = relationship("Note", back_populates="project", lazy="select")
    note_refs = relationship("ProjectNoteRef", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} status={self.status!r}>"


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------

class Source(Base):
    """Tài liệu nguồn PDF."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_code = Column(String(4), unique=True, nullable=True)  # AA00-ZZ99
    file_path = Column(Text, nullable=False, unique=True)
    file_hash = Column(String(64), nullable=False)
    title = Column(Text)
    authors = Column(Text)
    year = Column(String(10))
    doi = Column(Text)
    metadata_json = Column(Text)
    last_opened_page = Column(Integer, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    notes = relationship("Note", back_populates="source", lazy="select")
    extracts = relationship("Extract", back_populates="source", lazy="select")
    assets = relationship("Asset", back_populates="source", lazy="select")

    def __repr__(self) -> str:
        return f"<Source id={self.id} title={self.title!r}>"


# ---------------------------------------------------------------------------
# notes
# ---------------------------------------------------------------------------

class Note(Base):
    """Ghi chú Markdown của người dùng."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    note_type = Column(String(32), nullable=False)  # source_note | concept_note | synthesis_note | board_note
    file_path = Column(Text, nullable=False, unique=True)
    summary = Column(Text)
    meta_json = Column(Text)
    is_deleted = Column(Integer, nullable=False, default=0)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)  # NULL = Global
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    source = relationship("Source", back_populates="notes")
    extracts = relationship("Extract", back_populates="note", lazy="select")
    assets = relationship("Asset", back_populates="note", lazy="select")
    note_tags = relationship("NoteTag", back_populates="note", cascade="all, delete-orphan")
    outgoing_links = relationship(
        "Link", foreign_keys="Link.from_note_id", back_populates="from_note", lazy="select"
    )
    incoming_links = relationship(
        "Link", foreign_keys="Link.to_note_id", back_populates="to_note", lazy="select"
    )
    board_cells = relationship("BoardCell", back_populates="linked_note", lazy="select")
    board_rows = relationship("BoardRow", back_populates="source_note", lazy="select")
    linked_boards = relationship("Board", back_populates="linked_note", lazy="select")
    project = relationship("Project", back_populates="own_notes", lazy="select")
    project_refs = relationship("ProjectNoteRef", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Note id={self.id} slug={self.slug!r} type={self.note_type!r}>"


# ---------------------------------------------------------------------------
# extracts
# ---------------------------------------------------------------------------

class Extract(Base):
    """Đoạn nội dung trích xuất từ source PDF có truy vết nguồn."""

    __tablename__ = "extracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    page_no = Column(Integer, nullable=False)
    extract_type = Column(String(16), nullable=False)  # text | table | image
    source_anchor = Column(Text, nullable=False)
    content_md = Column(Text, nullable=False)
    extra_json = Column(Text)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    source = relationship("Source", back_populates="extracts")
    note = relationship("Note", back_populates="extracts")

    def __repr__(self) -> str:
        return f"<Extract id={self.id} type={self.extract_type!r} page={self.page_no}>"


# ---------------------------------------------------------------------------
# assets
# ---------------------------------------------------------------------------

class Asset(Base):
    """File hình ảnh hoặc snapshot được lưu cục bộ."""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    asset_type = Column(String(16), nullable=False)  # image | snapshot
    file_path = Column(Text, nullable=False, unique=True)
    caption = Column(Text)
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    source = relationship("Source", back_populates="assets")
    note = relationship("Note", back_populates="assets")

    def __repr__(self) -> str:
        return f"<Asset id={self.id} type={self.asset_type!r}>"


# ---------------------------------------------------------------------------
# tags
# ---------------------------------------------------------------------------

class Tag(Base):
    """Nhãn phân loại note."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    color = Column(String(7))  # hex color e.g. #FF5733
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    note_tags = relationship("NoteTag", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"


class NoteTag(Base):
    """Bảng nối nhiều-nhiều giữa Note và Tag."""

    __tablename__ = "note_tags"
    __table_args__ = (UniqueConstraint("note_id", "tag_id", name="uq_note_tag"),)

    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    note = relationship("Note", back_populates="note_tags")
    tag = relationship("Tag", back_populates="note_tags")


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------

class Link(Base):
    """Liên kết hai chiều giữa các note (wikilink hoặc thủ công)."""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    to_note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    link_type = Column(String(16), nullable=False)  # wikilink | manual | inferred
    weight = Column(Integer, nullable=False, default=1)  # số lần wikilink xuất hiện trong note
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    from_note = relationship("Note", foreign_keys=[from_note_id], back_populates="outgoing_links")
    to_note = relationship("Note", foreign_keys=[to_note_id], back_populates="incoming_links")

    def __repr__(self) -> str:
        return f"<Link {self.from_note_id}→{self.to_note_id} type={self.link_type!r}>"


# ---------------------------------------------------------------------------
# board
# ---------------------------------------------------------------------------

class Board(Base):
    """Entity board độc lập để hỗ trợ multi-board."""

    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    board_type = Column(String(32), nullable=False, default="general")
    linked_note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    scope = Column(Text)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    rows = relationship("BoardRow", back_populates="board", cascade="all, delete-orphan")
    columns = relationship("BoardColumn", back_populates="board", cascade="all, delete-orphan")
    linked_note = relationship("Note", back_populates="linked_boards")

    def __repr__(self) -> str:
        return f"<Board id={self.id} title={self.title!r} type={self.board_type!r}>"

class BoardRow(Base):
    """Hàng của Research Board (thường là source hoặc chủ đề)."""

    __tablename__ = "board_rows"
    __table_args__ = (UniqueConstraint("board_id", "source_note_id", name="uq_board_rows_board_source_note"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    source_note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    label = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    board = relationship("Board", back_populates="rows")
    source_note = relationship("Note", back_populates="board_rows", foreign_keys=[source_note_id])
    cells = relationship("BoardCell", back_populates="row", cascade="all, delete-orphan")


class BoardColumn(Base):
    """Cột của Research Board (thường là góc nhìn hoặc chủ đề)."""

    __tablename__ = "board_columns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    label = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    board = relationship("Board", back_populates="columns")
    cells = relationship("BoardCell", back_populates="col", cascade="all, delete-orphan")


class BoardCell(Base):
    """Ô giao nhau giữa hàng và cột của Research Board."""

    __tablename__ = "board_cells"

    id = Column(Integer, primary_key=True, autoincrement=True)
    row_id = Column(Integer, ForeignKey("board_rows.id", ondelete="CASCADE"), nullable=False)
    col_id = Column(Integer, ForeignKey("board_columns.id", ondelete="CASCADE"), nullable=False)
    linked_note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    content_md = Column(Text)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    row = relationship("BoardRow", back_populates="cells")
    col = relationship("BoardColumn", back_populates="cells")
    linked_note = relationship("Note", back_populates="board_cells")


# ---------------------------------------------------------------------------
# app_settings
# ---------------------------------------------------------------------------

class AppSettingRow(Base):
    """Cài đặt ứng dụng lưu trong DB (key-value)."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(Text, nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<AppSettingRow {self.setting_key!r}={self.setting_value!r}>"


# ---------------------------------------------------------------------------
# project_note_refs
# ---------------------------------------------------------------------------

class ProjectNoteRef(Base):
    """Global note được kéo vào project để tham khảo (membership_type = reference)."""

    __tablename__ = "project_note_refs"
    __table_args__ = (UniqueConstraint("project_id", "note_id", name="uq_project_note_ref"),)

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime, nullable=False, default=_utcnow)

    project = relationship("Project", back_populates="note_refs")
    note = relationship("Note", back_populates="project_refs")

    def __repr__(self) -> str:
        return f"<ProjectNoteRef project={self.project_id} note={self.note_id}>"
