"""Thêm cột weight vào bảng links.

weight: số lần wikilink xuất hiện trong note nguồn (dùng để vẽ độ dày cạnh đồ thị).

Revision ID: 0003_add_link_weight
Revises: 0002_add_source_code
Create Date: 2026-04-23
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_link_weight"
down_revision: Union[str, None] = "0002_add_source_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite hỗ trợ ADD COLUMN với DEFAULT
    op.add_column(
        "links",
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("links", "weight")
