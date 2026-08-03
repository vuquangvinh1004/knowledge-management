"""CRUD và file I/O cho Note."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from core.services.note_templates import build_note_template, get_note_title_warnings
from core.services.source_service import SourceService
from core.storage.models import Note
from core.storage.session import get_session
from core.utils.constants import NOTE_TYPES
from core.utils.exceptions import NoteNotFoundError, PKMError
from core.utils.helpers import slugify
from core.utils.logger import get_logger

logger = get_logger()


def get_by_id(note_id: int) -> Note:
    """Lấy note theo id."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None or note.is_deleted:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        session.expunge(note)
        return note


def get_by_slug(slug: str) -> Note:
    """Lấy note theo slug."""
    with get_session() as session:
        note = (
            session.query(Note)
            .filter(Note.slug == slug, Note.is_deleted == 0)
            .first()
        )
        if note is None:
            raise NoteNotFoundError(f"Không tìm thấy note slug={slug!r}.")
        session.expunge(note)
        return note


def get_source_note(source_id: int) -> Note | None:
    """Lấy source_note liên kết với source (1:1)."""
    with get_session() as session:
        note = (
            session.query(Note)
            .filter(
                Note.source_id == source_id,
                Note.note_type == "source_note",
                Note.is_deleted == 0,
            )
            .first()
        )
        if note:
            session.expunge(note)
        return note


def list_all(note_type: str | None = None, include_deleted: bool = False) -> list[Note]:
    """Lấy danh sách notes, tùy chọn lọc theo note_type."""
    with get_session() as session:
        query = session.query(Note)
        if not include_deleted:
            query = query.filter(Note.is_deleted == 0)
        if note_type:
            query = query.filter(Note.note_type == note_type)
        notes = query.order_by(Note.updated_at.desc()).all()
        for n in notes:
            session.expunge(n)
        return notes


def build_template(note_type: str, title: str) -> str:
    """Public wrapper cho template markdown theo note_type."""
    return build_note_template(note_type, title)


def title_warnings(note_type: str, title: str) -> list[str]:
    """Public wrapper cho soft-warning chất lượng title."""
    return get_note_title_warnings(note_type, title)


def create_note(
    notes_dir: Path | str,
    title: str,
    note_type: str,
    source_id: int | None = None,
    initial_content: str = "",
    project_id: int | None = None,
) -> Note:
    """Tạo note mới và lưu file markdown tương ứng."""
    notes_dir = Path(notes_dir)

    if note_type not in NOTE_TYPES:
        raise PKMError(f"note_type không hợp lệ: {note_type!r}. Phải là một trong {NOTE_TYPES}.")

    if note_type == "source_note" and source_id is None:
        raise PKMError("`source_note` bắt buộc phải có source_id.")

    if note_type == "source_note" and source_id is not None:
        existing = get_source_note(source_id)
        if existing:
            raise PKMError(
                f"Source id={source_id} đã có source_note id={existing.id}. "
                "Mỗi source chỉ được có một source_note."
            )

        SourceService().ensure_source_code(source_id)

    slug = _unique_slug(notes_dir, title)
    note_file = notes_dir / f"{slug}.md"
    resolved_content = initial_content or build_note_template(note_type, title)

    notes_dir.mkdir(parents=True, exist_ok=True)
    note_file.write_text(resolved_content, encoding="utf-8")

    now = datetime.now(timezone.utc)
    note = Note(
        source_id=source_id,
        title=title,
        slug=slug,
        note_type=note_type,
        file_path=str(note_file),
        project_id=project_id,
        created_at=now,
        updated_at=now,
    )
    try:
        with get_session() as session:
            session.add(note)
            session.flush()
            session.expunge(note)
    except IntegrityError as exc:
        note_file.unlink(missing_ok=True)
        raise PKMError(f"Không thể tạo note (slug trùng): {exc}") from exc

    scope_label = f"project_id={project_id}" if project_id is not None else "global"
    logger.info(f"Tạo note id={note.id} slug={slug!r} type={note_type!r} scope={scope_label}")
    return note


def list_by_project(project_id: int) -> list[Note]:
    """Trả danh sách project-only notes có project_id = project_id."""
    with get_session() as session:
        notes = (
            session.query(Note)
            .filter(Note.project_id == project_id, Note.is_deleted == 0)
            .order_by(Note.updated_at.desc())
            .all()
        )
        for n in notes:
            session.expunge(n)
        return notes


def list_global(note_type: str | None = None) -> list[Note]:
    """Trả danh sách Global notes (project_id IS NULL)."""
    with get_session() as session:
        query = session.query(Note).filter(Note.project_id.is_(None), Note.is_deleted == 0)
        if note_type:
            query = query.filter(Note.note_type == note_type)
        notes = query.order_by(Note.updated_at.desc()).all()
        for n in notes:
            session.expunge(n)
        return notes


def read_content(note_id: int) -> str:
    """Đọc nội dung markdown của note từ file trên disk."""
    note = get_by_id(note_id)
    return Path(note.file_path).read_text(encoding="utf-8")


def save_content(note_id: int, content: str) -> None:
    """Ghi nội dung markdown vào file và cập nhật updated_at trong DB."""
    note = get_by_id(note_id)
    Path(note.file_path).write_text(content, encoding="utf-8")
    with get_session() as session:
        db_note = session.get(Note, note_id)
        if db_note:
            db_note.updated_at = datetime.now(timezone.utc)
    logger.debug(f"Lưu nội dung note id={note_id}")


def update_title(note_id: int, new_title: str) -> Note:
    """Cập nhật tiêu đề note (slug KHÔNG thay đổi để giữ liên kết ổn định)."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None or note.is_deleted:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        note.title = new_title
        note.updated_at = datetime.now(timezone.utc)
        session.flush()
        session.expunge(note)
    logger.info(f"Cập nhật title note id={note_id} → {new_title!r}")
    return note


def update_summary(note_id: int, summary: str) -> None:
    """Cập nhật summary của note."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None or note.is_deleted:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        note.summary = summary
        note.updated_at = datetime.now(timezone.utc)


def _unique_slug(notes_dir: Path, title: str) -> str:
    """Sinh slug unique từ title, thêm suffix -2, -3... nếu cần."""
    base = slugify(title) or "note"
    slug = base
    counter = 2
    while True:
        with get_session() as session:
            existing = session.query(Note).filter(Note.slug == slug).first()
        if existing is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1
