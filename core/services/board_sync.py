"""Đồng bộ dữ liệu cho Board."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from core.services.note_crud import list_all
from core.storage.models import Board, BoardCell, BoardColumn, BoardRow, Note
from core.storage.session import get_session
from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA
from core.utils.logger import get_logger

logger = get_logger()

META_ANALYSIS_COLUMNS = list(BOARD_META_ANALYSIS_CRITERIA)
REMOVED_META_ANALYSIS_COLUMNS = {
    "ID",
    "Mã nghiên cứu",
    "Hướng tác động",
    "Effect size",
    "Loại effect size",
    "SE/SD",
    "CI thấp",
    "CI cao",
    "p-value",
    "Chất lượng nghiên cứu",
    "Ghi chú mã hóa",
    "Link source_note",
    "Link concept_note",
    "Link synthesis_note",
}

_META_SECTION_RE = re.compile(r"^##\s+Metadata\s*$", re.IGNORECASE)
_MY_NOTES_SECTION_RE = re.compile(r"^##\s+Ghi\s+chú\s+của\s+tôi\s*$", re.IGNORECASE)
_META_CALLOUT_RE = re.compile(r"^>\s*\[!\s*(.*?)\s*\]\s*$")


def _resolve_board_id(board_id: int | None) -> int:
    if board_id is not None:
        return board_id

    from core.services.board_crud import get_default_board

    return get_default_board().id


def sync_rows_with_source_notes(board_id: int | None = None, *, project_id: int | None = None) -> list[BoardRow]:
    """Đồng bộ hàng board theo source_note (1 hàng = 1 source_note)."""
    from core.services.project_service import ProjectService

    resolved_board_id = _resolve_board_id(board_id)

    notes = list_all(note_type="source_note", include_deleted=False)
    if project_id is not None:
        allowed = ProjectService().get_project_note_ids(project_id)
        notes = [n for n in notes if int(n.id) in allowed]
    notes = sorted(notes, key=lambda n: str(n.title or "").lower())

    with get_session() as session:
        rows = (
            session.query(BoardRow)
            .filter(BoardRow.board_id == resolved_board_id)
            .all()
        )
        by_source_note_id = {
            int(r.source_note_id): r
            for r in rows
            if isinstance(r.source_note_id, int)
        }

        for idx, note in enumerate(notes):
            row = by_source_note_id.get(int(note.id))
            if row is None:
                row = BoardRow(
                    board_id=resolved_board_id,
                    source_note_id=int(note.id),
                    label=str(note.title or f"source_note {note.id}"),
                    sort_order=idx,
                )
                session.add(row)
            else:
                row.label = str(note.title or row.label)
                row.sort_order = idx

        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)

        session.flush()
        linked_rows = (
            session.query(BoardRow)
            .filter(
                BoardRow.board_id == resolved_board_id,
                BoardRow.source_note_id.is_not(None),
            )
            .order_by(BoardRow.sort_order, BoardRow.id)
            .all()
        )
        for r in linked_rows:
            session.expunge(r)
        return linked_rows


def sync_cells_from_source_note_metadata(board_id: int | None = None, *, project_id: int | None = None) -> int:
    """Đồng bộ metadata source_note vào cells của board."""
    resolved_board_id = _resolve_board_id(board_id)
    now = datetime.now(timezone.utc)
    project_note_ids: set[int] | None = None

    if project_id is not None:
        from core.services.project_service import ProjectService

        project_note_ids = ProjectService().get_project_note_ids(project_id)

    with get_session() as session:
        rows = (
            session.query(BoardRow)
            .filter(
                BoardRow.board_id == resolved_board_id,
                BoardRow.source_note_id.is_not(None),
            )
            .all()
        )
        if not rows:
            return 0

        note_ids = [int(r.source_note_id) for r in rows if r.source_note_id is not None]
        notes = (
            session.query(Note)
            .filter(
                Note.id.in_(note_ids),
                Note.note_type == "source_note",
                Note.is_deleted == 0,
            )
            .all()
        )

        note_by_id = {int(n.id): n for n in notes if n.id is not None}
        if project_note_ids is not None:
            note_by_id = {note_id: note for note_id, note in note_by_id.items() if note_id in project_note_ids}
        if not note_by_id:
            return 0

        columns = (
            session.query(BoardColumn)
            .filter(
                BoardColumn.board_id == resolved_board_id,
                BoardColumn.label.in_(META_ANALYSIS_COLUMNS),
            )
            .all()
        )
        col_by_key = {
            _normalize_meta_key(str(c.label)): c
            for c in columns
        }
        if not col_by_key:
            return 0

        row_ids = [int(r.id) for r in rows if r.id is not None]
        col_ids = [int(c.id) for c in columns if c.id is not None]
        existing_cells = (
            session.query(BoardCell)
            .filter(
                BoardCell.row_id.in_(row_ids),
                BoardCell.col_id.in_(col_ids),
            )
            .all()
        )
        existing_map = {(int(c.row_id), int(c.col_id)): c for c in existing_cells}

        changed = 0
        for row in rows:
            row_id = int(row.id)
            source_note_id = int(row.source_note_id or 0)
            note = note_by_id.get(source_note_id)
            if note is None:
                continue

            file_path = Path(str(note.file_path or ""))
            if not file_path.exists():
                continue

            metadata = _parse_source_note_metadata(file_path.read_text(encoding="utf-8"))
            if not metadata:
                continue

            for key, value in metadata.items():
                col = col_by_key.get(key)
                if col is None:
                    continue

                map_key = (row_id, int(col.id))
                current = existing_map.get(map_key)
                if current is None:
                    session.add(
                        BoardCell(
                            row_id=row_id,
                            col_id=int(col.id),
                            content_md=value,
                            updated_at=now,
                        )
                    )
                    changed += 1
                    continue

                if (current.content_md or "") != value:
                    current.content_md = value
                    current.updated_at = now
                    changed += 1

        if changed > 0:
            board = session.get(Board, resolved_board_id)
            if board is not None:
                board.updated_at = now
        return changed


def cleanup_deprecated_source_note_metadata(*, project_id: int | None = None) -> int:
    """Dọn các callout metadata deprecated khỏi source_note active."""
    from core.services.project_service import ProjectService

    notes = list_all(note_type="source_note", include_deleted=False)
    if project_id is not None:
        allowed = ProjectService().get_project_note_ids(project_id)
        notes = [n for n in notes if int(n.id) in allowed]

    changed_notes = 0
    for note in notes:
        file_path = Path(str(note.file_path or ""))
        if not file_path.exists():
            continue

        original = file_path.read_text(encoding="utf-8")
        cleaned, removed_blocks = _strip_deprecated_metadata_blocks(original)
        if removed_blocks <= 0 or cleaned == original:
            continue

        file_path.write_text(cleaned, encoding="utf-8")
        changed_notes += 1

    if changed_notes > 0:
        logger.info("Đã cleanup callout metadata deprecated cho %s source_note", changed_notes)
    return changed_notes


def _normalize_meta_key(text: str) -> str:
    return " ".join(str(text or "").strip().upper().split())


def _strip_deprecated_metadata_blocks(markdown: str) -> tuple[str, int]:
    """Xóa các callout metadata deprecated khỏi markdown source_note."""
    lines = markdown.splitlines()
    removed = 0
    out: list[str] = []
    idx = 0
    removed_keys = {_normalize_meta_key(k) for k in REMOVED_META_ANALYSIS_COLUMNS}

    while idx < len(lines):
        line = lines[idx]
        callout = _META_CALLOUT_RE.match(line)
        if not callout:
            out.append(line)
            idx += 1
            continue

        raw_key = _normalize_meta_key(callout.group(1))
        if raw_key not in removed_keys:
            out.append(line)
            idx += 1
            continue

        removed += 1
        idx += 1
        while idx < len(lines):
            current = lines[idx]
            if current.startswith("## "):
                break
            if _META_CALLOUT_RE.match(current):
                break
            idx += 1

        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1

    cleaned = "\n".join(out).rstrip() + "\n"
    return cleaned, removed


def _parse_source_note_metadata(markdown: str) -> dict[str, str]:
    """Parse metadata callout blocks trong source_note markdown."""
    lines = markdown.splitlines()

    def _parse_from(start_idx: int) -> dict[str, str]:
        parsed: dict[str, str] = {}
        idx = start_idx
        while idx < len(lines):
            line = lines[idx]
            if line.startswith("## "):
                break

            callout = _META_CALLOUT_RE.match(line)
            if not callout:
                idx += 1
                continue

            raw_key = _normalize_meta_key(callout.group(1))
            idx += 1

            value_lines: list[str] = []
            while idx < len(lines):
                current = lines[idx]
                if current.startswith("## "):
                    break
                if _META_CALLOUT_RE.match(current):
                    break

                stripped = current.strip()
                if current.lstrip().startswith(">"):
                    payload = current.lstrip()[1:]
                    if payload.startswith(" "):
                        payload = payload[1:]
                    value_lines.append(payload.rstrip())
                    idx += 1
                    continue

                if stripped:
                    value_lines.append(current.rstrip())
                    idx += 1
                    continue

                value_lines.append("")
                idx += 1

            value = "\n".join(value_lines).strip()
            normalized_placeholder = _normalize_meta_key(value).rstrip(".")
            if normalized_placeholder in {"THÔNG TIN TIÊU CHÍ", "THONG TIN TIEU CHI"}:
                value = ""

            if raw_key:
                parsed[raw_key] = value
        return parsed

    metadata_start: int | None = None
    notes_start: int | None = None
    for i, line in enumerate(lines):
        normalized = line.strip()
        if metadata_start is None and _META_SECTION_RE.match(normalized):
            metadata_start = i + 1
        if notes_start is None and _MY_NOTES_SECTION_RE.match(normalized):
            notes_start = i + 1

    if metadata_start is not None:
        return _parse_from(metadata_start)
    if notes_start is not None:
        return _parse_from(notes_start)
    return {}
