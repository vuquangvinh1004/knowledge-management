"""Thêm cột meta_json vào bảng notes.

Revision ID: 0005_add_note_meta_json
Revises: 0004_add_boards_scope
Create Date: 2026-04-24
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_note_meta_json"
down_revision: Union[str, None] = "0004_add_boards_scope"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("notes") as batch_op:
        batch_op.add_column(sa.Column("meta_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("notes") as batch_op:
        batch_op.drop_column("meta_json")
