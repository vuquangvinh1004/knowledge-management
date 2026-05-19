"""Public ID helpers.

Sinh public_id theo UUIDv7 cho các entity nghiệp vụ,
giữ tính duy nhất toàn cục và gần-sắp-xếp theo thời gian.
"""
from __future__ import annotations

import uuid


def generate_public_id() -> str:
    """Tạo public_id dạng chuỗi UUID.

    Ưu tiên UUIDv7 trên Python mới; fallback UUID4 để giữ tương thích.
    """
    uuid7_factory = getattr(uuid, "uuid7", None)
    if callable(uuid7_factory):
        return str(uuid7_factory())
    return str(uuid.uuid4())
