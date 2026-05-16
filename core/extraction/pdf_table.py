"""Trích xuất bảng từ PDF sử dụng pdfplumber."""
from __future__ import annotations

from pathlib import Path


def extract_table_from_region(
    file_path: Path,
    page_no: int,
    bbox: tuple[float, float, float, float],
) -> list[list[str | None]] | None:
    """
    Trích bảng từ vùng bbox trên trang PDF.

    Args:
        file_path: Đường dẫn file PDF.
        page_no: Số trang 1-based.
        bbox: (x0, y0, x1, y1) theo tọa độ PDF.

    Returns:
        List of rows (list of cells), hoặc None nếu không tìm thấy bảng.
    """
    import pdfplumber

    with pdfplumber.open(str(file_path)) as pdf:
        page = pdf.pages[page_no - 1]
        # pdfplumber crop nhận (x0, top, x1, bottom)
        cropped = page.crop(bbox)
        tables = cropped.extract_tables()
        if tables:
            return tables[0]
        # Fallback: tạo bảng giả từ text
        text = cropped.extract_text() or ""
        if text.strip():
            rows = [
                [cell.strip() for cell in re.split(r"\s{2,}", line) if cell.strip()]
                for line in text.splitlines()
                if line.strip()
            ]
            return rows if rows else None
        return None


def tables_on_page(
    file_path: Path,
    page_no: int,
) -> list[dict]:
    """
    Tự động phát hiện các bảng trên trang.

    Returns:
        List of dicts với keys: bbox (x0,y0,x1,y1), rows.
    """
    import pdfplumber

    result: list[dict] = []
    with pdfplumber.open(str(file_path)) as pdf:
        page = pdf.pages[page_no - 1]
        for table in page.find_tables():
            try:
                rows = table.extract()
                result.append({"bbox": table.bbox, "rows": rows})
            except Exception:  # noqa: BLE001
                pass
    return result


import re  # noqa: E402 (imported here to avoid top-level dependency error)
