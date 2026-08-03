"""Lifecycle và maintenance cho Note."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Link, Note, Source
from core.storage.query_optimization import (
    get_note_delete_impact as query_get_note_delete_impact,
    list_notes_for_management_efficient,
)
from core.storage.session import get_session
from core.services.source_service import SourceService
from core.utils.exceptions import NoteNotFoundError, PKMError
from core.utils.logger import get_logger

logger = get_logger()


def list_notes_for_management(include_deleted: bool = False) -> list[dict]:
    """Liệt kê note cho màn hình quản lý ghi chú."""
    with get_session() as session:
        items = list_notes_for_management_efficient(session, include_deleted=include_deleted)
        return [
            {
                "note_id": item.note_id,
                "note_public_id": item.note_public_id,
                "title": item.title,
                "note_type": item.note_type,
                "source_id": item.source_id,
                "project_id": item.project_id,
                "scope_label": item.scope_label,
                "file_path": item.file_path,
                "is_deleted": item.is_deleted,
                "updated_at": item.updated_at,
            }
            for item in items
        ]


def get_note_delete_impact(note_id: int) -> dict:
    """Phân tích ảnh hưởng nếu soft-delete note."""
    try:
        with get_session() as session:
            impact = query_get_note_delete_impact(session, note_id)
            return {
                "note_id": impact.note_id,
                "title": impact.title,
                "note_type": impact.note_type,
                "is_source_note": impact.is_source_note,
                "source_id": impact.source_id,
                "project_id": impact.project_id,
                "incoming_links": impact.incoming_links_count,
                "outgoing_links": impact.outgoing_links_count,
                "extract_refs": impact.extract_refs_count,
                "asset_refs": impact.asset_refs_count,
                "board_cell_refs": impact.board_cell_refs_count,
                "linked_boards": impact.linked_boards_count,
                "project_refs": impact.project_refs_count,
            }
    except Exception as e:
        if "Không tìm thấy" in str(e):
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        raise


def audit_missing_source_note_files() -> list[dict]:
    """Audit read-only các source_note có record DB nhưng thiếu file markdown."""
    with get_session() as session:
        notes = (
            session.query(Note)
            .filter(
                Note.note_type == "source_note",
                Note.is_deleted == 0,
            )
            .all()
        )

        source_ids = {int(n.source_id) for n in notes if n.source_id is not None}
        source_map: dict[int, Source] = {}
        if source_ids:
            for src in session.query(Source).filter(Source.id.in_(source_ids)).all():
                if src.id is not None:
                    source_map[int(src.id)] = src

        issues: list[dict] = []
        for note in notes:
            file_path = Path(str(note.file_path or ""))
            if file_path.exists():
                continue

            src_id = int(note.source_id) if note.source_id is not None else None
            src = source_map.get(src_id) if src_id is not None else None
            issues.append(
                {
                    "note_id": int(note.id),
                    "source_id": src_id,
                    "source_code": str(getattr(src, "source_code", "") or ""),
                    "source_title": str(getattr(src, "title", "") or ""),
                    "note_title": str(note.title or ""),
                    "file_path": str(note.file_path or ""),
                }
            )

        issues.sort(key=lambda x: (x.get("source_id") or 0, x.get("note_id") or 0))
        return issues


def soft_delete(note_id: int) -> None:
    """Soft-delete note (xóa tạm, giữ file và record DB)."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        note.is_deleted = 1
        note.updated_at = datetime.now(timezone.utc)
    logger.info("Soft-delete note id=%s", note_id)


def restore(note_id: int) -> None:
    """Khôi phục note từ trạng thái xóa tạm (is_deleted = 1)."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        if int(note.is_deleted or 0) != 1:
            raise PKMError("Chỉ có thể khôi phục note ở trạng thái xóa tạm.")
        note.is_deleted = 0
        note.updated_at = datetime.now(timezone.utc)
    logger.info("Restore soft-deleted note id=%s", note_id)


def mark_hard_deleted(note_id: int, delete_file: bool = True) -> None:
    """Đánh dấu note ở trạng thái xóa cứng (is_deleted = 2)."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        file_path = Path(note.file_path)

        session.query(Link).filter(
            (Link.from_note_id == note_id) | (Link.to_note_id == note_id)
        ).delete(synchronize_session=False)

        note.is_deleted = 2
        note.updated_at = datetime.now(timezone.utc)

    if delete_file and file_path.exists():
        file_path.unlink(missing_ok=True)
    logger.info("Mark hard-deleted note id=%s", note_id)


def hard_delete(note_id: int, delete_file: bool = True) -> None:
    """Xóa cứng note khỏi DB."""
    with get_session() as session:
        note = session.get(Note, note_id)
        if note is None:
            raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
        file_path = Path(note.file_path)

        session.query(Link).filter(
            (Link.from_note_id == note_id) | (Link.to_note_id == note_id)
        ).delete(synchronize_session=False)

        session.delete(note)

    if delete_file and file_path.exists():
        file_path.unlink()
    logger.info("Hard-delete note id=%s", note_id)


def normalize_source_note_titles(notes_dir: Path) -> int:
    """Chuẩn hóa title source_note dựa trên metadata hiện có."""
    updated_count = 0
    with get_session() as session:
        source_rows = session.query(Source).all()
        source_map = {int(s.id): s for s in source_rows if s.id is not None}

        notes = (
            session.query(Note)
            .filter(Note.note_type == "source_note", Note.is_deleted == 0)
            .all()
        )

        for note in notes:
            if note.source_id is None:
                continue
            source = source_map.get(int(note.source_id))
            if source is None:
                continue

            meta = {}
            if note.meta_json:
                try:
                    parsed = json.loads(note.meta_json)
                    if isinstance(parsed, dict):
                        meta = parsed
                except Exception:
                    meta = {}

            effective_authors = str(meta.get("author") or source.authors or "").strip() or None
            effective_year = str(meta.get("year") or source.year or "").strip() or None
            fallback_title = _normalize_note_title_for_catalog(
                "source_note",
                str(note.title or ""),
            )

            new_title = SourceService.build_source_note_title(
                authors=effective_authors,
                year=effective_year,
                fallback_filename=fallback_title,
            )
            if new_title != note.title:
                note.title = new_title
                note.updated_at = datetime.now(timezone.utc)
                updated_count += 1

    return updated_count


def refresh_wikilink_note_catalog(notes_dir: Path) -> dict[str, int]:
    """Làm mới catalog note cho wikilink suggestions."""
    soft_deleted_missing_file = 0
    removed_stale_links = 0
    removed_orphan_stub_notes = 0

    with get_session() as session:
        active_notes = session.query(Note).filter(Note.is_deleted == 0).all()

        link_rows = session.query(Link.from_note_id, Link.to_note_id).all()
        incoming_count: dict[int, int] = {}
        outgoing_count: dict[int, int] = {}
        for from_id, to_id in link_rows:
            f_id = int(from_id)
            t_id = int(to_id)
            outgoing_count[f_id] = outgoing_count.get(f_id, 0) + 1
            incoming_count[t_id] = incoming_count.get(t_id, 0) + 1

        for note in active_notes:
            file_path = Path(str(note.file_path or ""))
            if note.file_path and not file_path.exists():
                note.is_deleted = 1
                note.updated_at = datetime.now(timezone.utc)
                soft_deleted_missing_file += 1
                continue

            note_id = int(note.id)
            note_type = str(note.note_type)
            if note_type in {"concept_note", "synthesis_note", "board_note"}:
                has_incoming = incoming_count.get(note_id, 0) > 0
                has_outgoing = outgoing_count.get(note_id, 0) > 0
                if not has_incoming and not has_outgoing and _is_auto_stub_note(note):
                    note.is_deleted = 1
                    note.updated_at = datetime.now(timezone.utc)
                    removed_orphan_stub_notes += 1

        stale_note_ids = {
            int(n.id)
            for n in session.query(Note).filter(Note.is_deleted != 0).all()
            if n.id is not None
        }
        if stale_note_ids:
            stale_links = session.query(Link).filter(
                (Link.from_note_id.in_(stale_note_ids)) | (Link.to_note_id.in_(stale_note_ids))
            ).all()
            for lnk in stale_links:
                session.delete(lnk)
                removed_stale_links += 1

    return {
        "soft_deleted_missing_file": soft_deleted_missing_file,
        "removed_stale_links": removed_stale_links,
        "removed_orphan_stub_notes": removed_orphan_stub_notes,
    }


def get_unused_note_candidates() -> list[dict]:
    """Liệt kê candidate note không còn dùng để preview."""
    candidates: list[dict] = []

    with get_session() as session:
        active_notes = session.query(Note).filter(Note.is_deleted == 0).all()

        link_rows = session.query(Link.from_note_id, Link.to_note_id).all()
        incoming_count: dict[int, int] = {}
        outgoing_count: dict[int, int] = {}
        for from_id, to_id in link_rows:
            f_id = int(from_id)
            t_id = int(to_id)
            outgoing_count[f_id] = outgoing_count.get(f_id, 0) + 1
            incoming_count[t_id] = incoming_count.get(t_id, 0) + 1

        for note in active_notes:
            note_id = int(note.id)
            note_type = str(note.note_type)
            title = str(note.title or "")
            file_path_str = str(note.file_path or "")
            file_path = Path(file_path_str)

            if not file_path.exists():
                candidates.append(
                    {
                        "note_id": note_id,
                        "title": title,
                        "note_type": note_type,
                        "file_path": file_path_str,
                        "reason": "missing-file",
                        "is_auto_stub": False,
                        "incoming": incoming_count.get(note_id, 0),
                        "outgoing": outgoing_count.get(note_id, 0),
                    }
                )
                continue

            if note_type in {"concept_note", "synthesis_note", "board_note"}:
                in_cnt = incoming_count.get(note_id, 0)
                out_cnt = outgoing_count.get(note_id, 0)
                if in_cnt == 0 and out_cnt == 0:
                    candidates.append(
                        {
                            "note_id": note_id,
                            "title": title,
                            "note_type": note_type,
                            "file_path": file_path_str,
                            "reason": "orphan-no-link",
                            "is_auto_stub": _is_auto_stub_note(note),
                            "incoming": in_cnt,
                            "outgoing": out_cnt,
                        }
                    )

    return sorted(candidates, key=lambda x: (x["reason"], x["note_type"], x["title"].lower()))


def cleanup_unused_notes(note_ids: set[int]) -> dict[str, int]:
    """Soft-delete các note người dùng đã chọn và dọn stale links liên quan."""
    if not note_ids:
        return {"soft_deleted": 0, "removed_stale_links": 0}

    soft_deleted = 0
    removed_stale_links = 0

    with get_session() as session:
        notes = (
            session.query(Note)
            .filter(Note.id.in_(note_ids), Note.is_deleted == 0)
            .all()
        )
        deleted_ids: set[int] = set()
        for note in notes:
            note.is_deleted = 1
            note.updated_at = datetime.now(timezone.utc)
            soft_deleted += 1
            deleted_ids.add(int(note.id))

        if deleted_ids:
            stale_links = session.query(Link).filter(
                (Link.from_note_id.in_(deleted_ids)) | (Link.to_note_id.in_(deleted_ids))
            ).all()
            for lnk in stale_links:
                session.delete(lnk)
                removed_stale_links += 1

    return {"soft_deleted": soft_deleted, "removed_stale_links": removed_stale_links}


def _is_auto_stub_note(note: Note) -> bool:
    file_path = Path(str(note.file_path or ""))
    if not file_path.exists():
        return False
    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except Exception:
        return False

    title = str(note.title or "").strip()
    if not title:
        return False

    skeletons = {
        f"# {title}",
        f"# Concept - {title}",
        f"# Synthesis - {title}",
        f"# Board - {title}",
    }
    return content in skeletons


def _normalize_note_title_for_catalog(note_type: str, title: str) -> str:
    t = title.strip()
    lower = t.lower()

    if note_type == "source_note":
        if lower.startswith("source - "):
            return t[len("source - "):].strip()
        return t

    if note_type == "concept_note":
        if lower.startswith("concept - "):
            return t[len("concept - "):].strip()
        return t

    if note_type == "synthesis_note":
        stripped = t
        if lower.startswith("synthesis - "):
            stripped = t[len("synthesis - "):].strip()
        if stripped.lower().startswith("concept - synthesis - "):
            stripped = stripped[len("concept - synthesis - "):].strip()
        if stripped.lower().startswith("concept - "):
            stripped = stripped[len("concept - "):].strip()
        if stripped and not stripped.startswith("~"):
            stripped = f"~ {stripped}".strip()
        return stripped

    if note_type == "board_note":
        stripped = t
        if lower.startswith("board - "):
            stripped = t[len("board - "):].strip()
        if stripped and not stripped.startswith("!"):
            stripped = f"! {stripped}".strip()
        return stripped

    return t
