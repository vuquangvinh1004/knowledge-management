"""Chuẩn hóa văn bản và bảng trích xuất từ PDF thành Markdown."""
from __future__ import annotations

import re
from collections.abc import Sequence


def normalize_text(text: str) -> str:
    """
    Làm sạch văn bản thô từ PDF:
    - Nối các từ bị ngắt dòng do dấu gạch ngang cuối dòng
    - Gộp xuống dòng đơn thành khoảng trắng
    - Gộp nhiều dòng trắng thành một
    """
    # Nối hyphen line-break: "word-\n" → "word"
    text = re.sub(r"-\n(\S)", r"\1", text)
    # Dòng đơn không phải kết đoạn → thay bằng khoảng trắng
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Chuẩn hóa khoảng trắng thừa
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Tối đa 2 dòng trắng liên tiếp
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def table_to_markdown(rows: Sequence[Sequence[str | None]]) -> str:
    """
    Chuyển đổi bảng 2D thành GFM Markdown table.

    Args:
        rows: Danh sách hàng, mỗi hàng là danh sách cell.
              Hàng đầu tiên được coi là header.

    Returns:
        Chuỗi GFM Markdown, hoặc chuỗi rỗng nếu đầu vào rỗng.
    """
    if not rows:
        return ""

    cleaned: list[list[str]] = [
        [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
        for row in rows
    ]
    if not cleaned:
        return ""

    col_count = max(len(r) for r in cleaned)

    def _pad(row: list[str]) -> list[str]:
        return row + [""] * (col_count - len(row))

    def _row_str(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    header = _pad(cleaned[0])
    separator = ["---"] * col_count
    lines = [_row_str(header), _row_str(separator)]
    for row in cleaned[1:]:
        lines.append(_row_str(_pad(row)))
    return "\n".join(lines)
