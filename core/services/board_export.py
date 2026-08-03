"""Export helpers cho Board."""
from __future__ import annotations

from core.storage.models import BoardCell
from core.storage.session import get_session
from core.services.board_crud import list_columns, list_rows


def export_markdown(board_id: int | None = None) -> str:
    """Xuất board thành Markdown table."""
    rows = list_rows(board_id=board_id)
    cols = list_columns(board_id=board_id, visible_only=True)

    if not rows or not cols:
        return "_Board chưa có dữ liệu._"

    header = "| | " + " | ".join(c.label for c in cols) + " |"
    separator = "|---" + "|---" * len(cols) + "|"

    md_rows: list[str] = [header, separator]
    for row in rows:
        cells_map: dict[int, str] = {}
        with get_session() as session:
            cells = (
                session.query(BoardCell)
                .filter(BoardCell.row_id == row.id)
                .all()
            )
            for c in cells:
                cells_map[c.col_id] = (c.content_md or "").replace("\n", " ")

        cell_values = [cells_map.get(c.id, "") for c in cols]
        md_rows.append("| " + row.label + " | " + " | ".join(cell_values) + " |")

    return "\n".join(md_rows)


def export_csv(board_id: int | None = None) -> str:
    """Xuất board thành CSV."""
    import csv
    import io

    rows = list_rows(board_id=board_id)
    cols = list_columns(board_id=board_id, visible_only=True)

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([""] + [c.label for c in cols])
    for row in rows:
        cells_map: dict[int, str] = {}
        with get_session() as session:
            cells = (
                session.query(BoardCell)
                .filter(BoardCell.row_id == row.id)
                .all()
            )
            for c in cells:
                cells_map[c.col_id] = c.content_md or ""

        row_data = [row.label] + [cells_map.get(c.id, "") for c in cols]
        writer.writerow(row_data)

    return buf.getvalue()
