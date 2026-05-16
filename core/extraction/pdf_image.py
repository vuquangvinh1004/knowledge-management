"""Chụp ảnh vùng PDF sử dụng PyMuPDF."""
from __future__ import annotations

from typing import Any


def capture_region(
    doc: Any,
    page_no: int,
    rect: tuple[float, float, float, float],
    zoom: float = 2.0,
) -> bytes:
    """
    Render một vùng rect trên trang thành PNG bytes chất lượng cao.

    Args:
        doc: fitz.Document đang mở.
        page_no: Số trang 1-based.
        rect: (x0, y0, x1, y1) theo tọa độ PDF.
        zoom: Hệ số zoom cho ảnh xuất (2.0 = 144 DPI).

    Returns:
        PNG bytes của vùng đã chụp.
    """
    import fitz

    page = doc[page_no - 1]
    clip = fitz.Rect(*rect)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    return pix.tobytes("png")
