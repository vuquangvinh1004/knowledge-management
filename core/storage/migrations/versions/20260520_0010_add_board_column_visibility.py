"""Add visibility flag for board columns.

Revision ID: 0010_add_board_column_visibility
Revises: 0009_add_board_row_source_note_link
Create Date: 2026-05-20
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_add_board_column_visibility"
down_revision: Union[str, None] = "0009_add_board_row_source_note_link"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("board_columns") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_visible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )

    with op.batch_alter_table("board_columns") as batch_op:
        batch_op.alter_column("is_visible", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("board_columns") as batch_op:
        batch_op.drop_column("is_visible")
