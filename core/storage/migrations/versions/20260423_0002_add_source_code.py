"""Thêm cột source_code vào bảng sources.

source_code: chuỗi 4 ký tự (2 chữ cái + 2 số) dạng AA00-ZZ99,
sinh tuần tự từ AA00, dùng để hiển thị trong trích dẫn và graph.

Revision ID: 0002_add_source_code
Revises: 0001_initial
Create Date: 2026-04-23
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_source_code"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _int_to_source_code(n: int) -> str:
    """Chuyển số thứ tự thành mã 4 ký tự AA00-ZZ99."""
    digits = n % 100
    letter_idx = n // 100
    letter1 = chr(65 + letter_idx // 26)
    letter2 = chr(65 + letter_idx % 26)
    return f"{letter1}{letter2}{digits:02d}"


def upgrade() -> None:
    op.add_column("sources", sa.Column("source_code", sa.String(4), nullable=True))

    # Backfill existing records theo thứ tự id
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM sources ORDER BY id"))
    rows = result.fetchall()
    for i, row in enumerate(rows):
        code = _int_to_source_code(i)
        conn.execute(
            sa.text("UPDATE sources SET source_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    # SQLite không hỗ trợ ALTER TABLE ADD CONSTRAINT; unique index thay thế
    try:
        op.create_index("ix_sources_source_code_unique", "sources", ["source_code"], unique=True)
    except Exception:
        pass  # index đã tồn tại hoặc dialect không hỗ trợ


def downgrade() -> None:
    try:
        op.drop_index("ix_sources_source_code_unique", table_name="sources")
    except Exception:
        pass
    op.drop_column("sources", "source_code")
