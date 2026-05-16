"""Hàm tiện ích dùng chung toàn ứng dụng."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, parse_qs


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Tính hash của file — dùng để nhận diện và chống nhập trùng source."""
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    """
    Tạo slug URL-safe từ chuỗi văn bản.
    Ví dụ: 'Nghiên cứu khoa học 2024' → 'nghien-cuu-khoa-hoc-2024'
    """
    text = text.lower().strip()
    text = _remove_vietnamese_accents(text)
    text = re.sub(r"[^a-z0-9\s\-_]", "", text)
    text = re.sub(r"[\s\-_]+", "-", text)
    text = text.strip("-")
    return text or "untitled"


def _remove_vietnamese_accents(text: str) -> str:
    """Xóa dấu tiếng Việt để tạo slug ASCII dùng unicodedata."""
    # Xử lý đặc biệt cho đ/Đ (không normalize bằng NFD)
    text = text.replace("đ", "d").replace("Đ", "d")
    # Normalize NFD rồi bỏ combining diacritical marks (category Mn)
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def build_source_anchor(
    source_id: int,
    page_no: int,
    rect: tuple[float, float, float, float] | None = None,
) -> str:
    """
    Tạo source anchor theo định dạng chuẩn:
    source://<source_id>?page=<page_no>[&rect=<x0>,<y0>,<x1>,<y1>]
    """
    anchor = f"source://{source_id}?page={page_no}"
    if rect is not None:
        x0, y0, x1, y1 = rect
        anchor += f"&rect={x0:.2f},{y0:.2f},{x1:.2f},{y1:.2f}"
    return anchor


def parse_source_anchor(anchor: str) -> dict:
    """
    Phân tích source anchor thành dict với các key: source_id, page_no, rect.
    Trả về None cho các field không có trong anchor.
    """
    parsed = urlparse(anchor)
    if parsed.scheme != "source":
        raise ValueError(f"Anchor không hợp lệ (scheme phải là 'source'): {anchor}")
    params = parse_qs(parsed.query)
    source_id = int(parsed.netloc)
    page_no = int(params["page"][0])
    rect = None
    if "rect" in params:
        parts = params["rect"][0].split(",")
        rect = tuple(float(p) for p in parts)
    return {"source_id": source_id, "page_no": page_no, "rect": rect}
