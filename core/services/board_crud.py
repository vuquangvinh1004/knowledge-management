"""CRUD cho Board."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Board, BoardCell, BoardColumn, BoardRow, Note
from core.storage.session import get_session
from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA
from core.utils.exceptions import PKMError

META_ANALYSIS_COLUMNS = list(BOARD_META_ANALYSIS_CRITERIA)
LITERATURE_COLUMNS = [
    "Mã nghiên cứu",
    "Tác giả",
    "Năm",
    "Tiêu đề",
    "Quốc gia/Bối cảnh",
    "Loại nguồn",
    "Mục tiêu nghiên cứu",
    "Câu hỏi nghiên cứu",
    "Lý thuyết/khung phân tích",
    "Chủ đề chính",
    "Biến độc lập",
    "Biến phụ thuộc",
    "Phương pháp nghiên cứu",
    "Kết quả chính",
    "Hạn chế",
    "Ghi chú mã hóa",
]
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


def _resolve_board_id(board_id: int | None) -> int:
    if board_id is not None:
        return board_id
    return get_default_board().id


def _assert_row_in_board(row_id: int, board_id: int, session) -> None:
    row = session.get(BoardRow, row_id)
    if row is None or row.board_id != board_id:
        raise PKMError(f"Row id={row_id} không thuộc board id={board_id}.")


def _assert_col_in_board(col_id: int, board_id: int, session) -> None:
    col = session.get(BoardColumn, col_id)
    if col is None or col.board_id != board_id:
        raise PKMError(f"Column id={col_id} không thuộc board id={board_id}.")


def create_board(title: str, board_type: str = "general", linked_note_id: int | None = None, scope: str | None = None) -> Board:
    title = title.strip()
    if not title:
        raise PKMError("Tên board không được để trống.")

    now = datetime.now(timezone.utc)
    with get_session() as session:
        board = Board(
            title=title,
            board_type=board_type.strip() or "general",
            linked_note_id=linked_note_id,
            scope=scope,
            created_at=now,
            updated_at=now,
        )
        session.add(board)
        session.flush()
        session.expunge(board)
    return board


def list_boards() -> list[Board]:
    with get_session() as session:
        boards = session.query(Board).order_by(Board.updated_at.desc(), Board.id.desc()).all()
        for b in boards:
            session.expunge(b)
        return boards


def get_board(board_id: int) -> Board:
    with get_session() as session:
        board = session.get(Board, board_id)
        if board is None:
            raise PKMError(f"Không tìm thấy board id={board_id}.")
        session.expunge(board)
        return board


def get_default_board() -> Board:
    with get_session() as session:
        board = (
            session.query(Board)
            .filter(Board.scope == "default")
            .order_by(Board.id.asc())
            .first()
        )
        if board is None:
            now = datetime.now(timezone.utc)
            board = Board(
                title="Research Board mặc định",
                board_type="general",
                scope="default",
                created_at=now,
                updated_at=now,
            )
            session.add(board)
            session.flush()
        session.expunge(board)
        return board


def rename_board(board_id: int, title: str) -> None:
    title = title.strip()
    if not title:
        raise PKMError("Tên board không được để trống.")
    with get_session() as session:
        board = session.get(Board, board_id)
        if board is None:
            raise PKMError(f"Không tìm thấy board id={board_id}.")
        board.title = title
        board.updated_at = datetime.now(timezone.utc)


def delete_board(board_id: int) -> None:
    with get_session() as session:
        board = session.get(Board, board_id)
        if board is None:
            raise PKMError(f"Không tìm thấy board id={board_id}.")
        session.delete(board)


def set_linked_note(board_id: int, note_id: int | None) -> None:
    with get_session() as session:
        board = session.get(Board, board_id)
        if board is None:
            raise PKMError(f"Không tìm thấy board id={board_id}.")
        board.linked_note_id = note_id
        board.updated_at = datetime.now(timezone.utc)


def create_from_template(
    template_name: str,
    title: str,
    *,
    notes_dir: Path | None = None,
    create_linked_board_note: bool = False,
) -> tuple[Board | None, int | None]:
    template = template_name.strip().lower()
    title = title.strip()
    if not title:
        raise PKMError("Tên board/note không được để trống.")

    if template in {"meta_analysis", "literature"}:
        board_type = template
        columns = META_ANALYSIS_COLUMNS if template == "meta_analysis" else LITERATURE_COLUMNS
        board = create_board(title=title, board_type=board_type)
        for col in columns:
            create_column(col, board_id=board.id)

        linked_note_id: int | None = None
        if create_linked_board_note:
            if notes_dir is None:
                raise PKMError("Thiếu notes_dir để tạo board_note đi kèm.")
            linked_note_id = _create_board_note(title=title, notes_dir=notes_dir)
            set_linked_note(board.id, linked_note_id)

        return get_board(board.id), linked_note_id

    if template == "board_note":
        if notes_dir is None:
            raise PKMError("Thiếu notes_dir để tạo board_note.")
        note_id = _create_board_note(title=title, notes_dir=notes_dir)
        return None, note_id

    raise PKMError(f"Template không hợp lệ: {template_name!r}.")


def _create_board_note(title: str, notes_dir: Path) -> int:
    from core.services.note_crud import create_note, build_template

    note_title = title if title.lower().startswith("board ") else f"board {title}"
    note = create_note(
        notes_dir,
        title=note_title,
        note_type="board_note",
        initial_content=build_template("board_note", note_title),
    )
    return note.id


def _resolve_board_id(board_id: int | None) -> int:
    if board_id is not None:
        return board_id
    return get_default_board().id


def ensure_full_meta_columns(board_id: int | None = None) -> list[BoardColumn]:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        existing = (
            session.query(BoardColumn)
            .filter(BoardColumn.board_id == resolved_board_id)
            .order_by(BoardColumn.sort_order, BoardColumn.id)
            .all()
        )
        for col in existing:
            if str(col.label) in REMOVED_META_ANALYSIS_COLUMNS:
                session.delete(col)

        session.flush()
        existing = (
            session.query(BoardColumn)
            .filter(BoardColumn.board_id == resolved_board_id)
            .order_by(BoardColumn.sort_order, BoardColumn.id)
            .all()
        )
        by_label: dict[str, BoardColumn] = {str(col.label): col for col in existing}

        next_order = max((c.sort_order for c in existing), default=-1) + 1
        for label in META_ANALYSIS_COLUMNS:
            if by_label.get(label) is None:
                session.add(BoardColumn(
                    board_id=resolved_board_id,
                    label=label,
                    sort_order=next_order,
                    is_visible=True,
                ))
                next_order += 1

        board = session.get(Board, resolved_board_id)
        if board:
            board.board_type = "meta_analysis"
            board.updated_at = datetime.now(timezone.utc)

        session.flush()
        cols = (
            session.query(BoardColumn)
            .filter(
                BoardColumn.board_id == resolved_board_id,
                BoardColumn.label.in_(META_ANALYSIS_COLUMNS),
            )
            .order_by(BoardColumn.sort_order, BoardColumn.id)
            .all()
        )
        for c in cols:
            session.expunge(c)
        return cols


def list_source_note_rows(board_id: int | None = None) -> list[BoardRow]:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        rows = (
            session.query(BoardRow)
            .filter(
                BoardRow.board_id == resolved_board_id,
                BoardRow.source_note_id.is_not(None),
            )
            .order_by(BoardRow.sort_order, BoardRow.id)
            .all()
        )
        for r in rows:
            session.expunge(r)
        return rows


def create_row(label: str, board_id: int | None = None, source_note_id: int | None = None) -> BoardRow:
    label = label.strip()
    if not label:
        raise PKMError("Nhãn hàng không được để trống.")
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        if source_note_id is not None:
            source_note = session.get(Note, int(source_note_id))
            if source_note is None or source_note.is_deleted or source_note.note_type != "source_note":
                raise PKMError("source_note_id không hợp lệ cho board row.")

        max_order = (
            session.query(BoardRow)
            .filter(BoardRow.board_id == resolved_board_id)
            .count()
        )
        row = BoardRow(
            board_id=resolved_board_id,
            source_note_id=source_note_id,
            label=label,
            sort_order=max_order,
        )
        session.add(row)
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)
        session.flush()
        session.expunge(row)
    return row


def list_rows(board_id: int | None = None) -> list[BoardRow]:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        rows = (
            session.query(BoardRow)
            .filter(BoardRow.board_id == resolved_board_id)
            .order_by(BoardRow.sort_order, BoardRow.id)
            .all()
        )
        for r in rows:
            session.expunge(r)
        return rows


def rename_row(row_id: int, label: str, board_id: int | None = None) -> None:
    label = label.strip()
    if not label:
        raise PKMError("Nhãn hàng không được để trống.")
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        _assert_row_in_board(row_id, resolved_board_id, session)
        row = session.get(BoardRow, row_id)
        row.label = label
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)


def delete_row(row_id: int, board_id: int | None = None) -> None:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        _assert_row_in_board(row_id, resolved_board_id, session)
        row = session.get(BoardRow, row_id)
        session.delete(row)
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)


def create_column(label: str, board_id: int | None = None) -> BoardColumn:
    label = label.strip()
    if not label:
        raise PKMError("Nhãn cột không được để trống.")
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        max_order = (
            session.query(BoardColumn)
            .filter(BoardColumn.board_id == resolved_board_id)
            .count()
        )
        col = BoardColumn(
            board_id=resolved_board_id,
            label=label,
            sort_order=max_order,
            is_visible=True,
        )
        session.add(col)
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)
        session.flush()
        session.expunge(col)
    return col


def list_columns(board_id: int | None = None, *, visible_only: bool = False) -> list[BoardColumn]:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        query = (
            session.query(BoardColumn)
            .filter(BoardColumn.board_id == resolved_board_id)
        )
        if visible_only:
            query = query.filter(BoardColumn.is_visible.is_(True))

        cols = query.order_by(BoardColumn.sort_order, BoardColumn.id).all()
        for c in cols:
            session.expunge(c)
        return cols


def rename_column(col_id: int, label: str, board_id: int | None = None) -> None:
    label = label.strip()
    if not label:
        raise PKMError("Nhãn cột không được để trống.")
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        _assert_col_in_board(col_id, resolved_board_id, session)
        col = session.get(BoardColumn, col_id)
        col.label = label
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)


def delete_column(col_id: int, board_id: int | None = None) -> None:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        _assert_col_in_board(col_id, resolved_board_id, session)
        col = session.get(BoardColumn, col_id)
        session.delete(col)
        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)


def get_cell(row_id: int, col_id: int, board_id: int | None = None) -> BoardCell | None:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        row = session.get(BoardRow, row_id)
        col = session.get(BoardColumn, col_id)
        if row is None or col is None:
            return None
        if row.board_id != resolved_board_id or col.board_id != resolved_board_id:
            return None
        cell = (
            session.query(BoardCell)
            .filter(BoardCell.row_id == row_id, BoardCell.col_id == col_id)
            .first()
        )
        if cell:
            session.expunge(cell)
        return cell


def update_cell(
    row_id: int,
    col_id: int,
    content_md: str = "",
    linked_note_id: int | None = None,
    board_id: int | None = None,
) -> BoardCell:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        _assert_row_in_board(row_id, resolved_board_id, session)
        _assert_col_in_board(col_id, resolved_board_id, session)
        cell = (
            session.query(BoardCell)
            .filter(BoardCell.row_id == row_id, BoardCell.col_id == col_id)
            .first()
        )
        if cell is None:
            cell = BoardCell(
                row_id=row_id,
                col_id=col_id,
                content_md=content_md,
                linked_note_id=linked_note_id,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(cell)
        else:
            cell.content_md = content_md
            cell.linked_note_id = linked_note_id
            cell.updated_at = datetime.now(timezone.utc)

        board = session.get(Board, resolved_board_id)
        if board:
            board.updated_at = datetime.now(timezone.utc)
        session.flush()
        session.expunge(cell)
        return cell


def get_all_cells(board_id: int | None = None) -> list[BoardCell]:
    resolved_board_id = _resolve_board_id(board_id)
    with get_session() as session:
        cells = (
            session.query(BoardCell)
            .join(BoardRow, BoardRow.id == BoardCell.row_id)
            .join(BoardColumn, BoardColumn.id == BoardCell.col_id)
            .filter(
                BoardRow.board_id == resolved_board_id,
                BoardColumn.board_id == resolved_board_id,
            )
            .all()
        )
        for c in cells:
            session.expunge(c)
        return cells
