"""Trích xuất văn bản và render PDF sử dụng PyMuPDF (fitz)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def open_document(file_path: Path) -> Any:
    """
    Mở tài liệu PDF.

    Returns:
        fitz.Document — caller chịu trách nhiệm gọi .close().

    Raises:
        ImportError: Nếu PyMuPDF chưa được cài đặt.
        RuntimeError: Nếu file không thể mở.
    """
    import fitz  # PyMuPDF
    return fitz.open(str(file_path))


def page_count(doc: Any) -> int:
    """Trả về số trang của tài liệu."""
    return len(doc)


def get_page_dimensions(doc: Any, page_no: int) -> tuple[float, float]:
    """
    Kích thước trang theo tọa độ PDF.

    Args:
        page_no: Số trang 1-based.

    Returns:
        (width, height) tính bằng điểm PDF.
    """
    page = doc[page_no - 1]
    return page.rect.width, page.rect.height


def render_page_to_bytes(doc: Any, page_no: int, zoom: float = 1.5) -> bytes:
    """
    Render trang PDF thành PNG bytes.

    Args:
        page_no: Số trang 1-based.
        zoom: Hệ số zoom (1.0 = 72 DPI, 1.5 = 108 DPI, 2.0 = 144 DPI).

    Returns:
        PNG bytes.
    """
    import fitz
    page = doc[page_no - 1]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def extract_page_text(doc: Any, page_no: int) -> str:
    """Trích toàn bộ văn bản từ một trang."""
    return doc[page_no - 1].get_text("text")


def extract_region_text(
    doc: Any,
    page_no: int,
    rect: tuple[float, float, float, float],
) -> str:
    """
    Trích văn bản từ vùng rect trên trang.

    Args:
        page_no: Số trang 1-based.
        rect: (x0, y0, x1, y1) theo tọa độ PDF (điểm).

    Returns:
        Văn bản trích xuất, đã strip.
    """
    import fitz
    page = doc[page_no - 1]
    clip = fitz.Rect(*rect)
    return page.get_text("text", clip=clip).strip()
