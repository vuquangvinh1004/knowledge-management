"""Add source_note link for board rows (1 row = 1 source_note support).

Revision ID: 0009_add_board_row_source_note_link
Revises: 0008_add_query_indexes
Create Date: 2026-05-19
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_add_board_row_source_note_link"
down_revision: Union[str, None] = "0008_add_query_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("board_rows") as batch_op:
        batch_op.add_column(sa.Column("source_note_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_board_rows_source_note_id",
            "notes",
            ["source_note_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_index("ix_board_rows_source_note_id", "board_rows", ["source_note_id"], unique=False)
    with op.batch_alter_table("board_rows") as batch_op:
        batch_op.create_unique_constraint(
            "uq_board_rows_board_source_note",
            ["board_id", "source_note_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("board_rows") as batch_op:
        try:
            batch_op.drop_constraint("uq_board_rows_board_source_note", type_="unique")
        except Exception:
            pass

    try:
        op.drop_index("ix_board_rows_source_note_id", table_name="board_rows")
    except Exception:
        pass

    with op.batch_alter_table("board_rows") as batch_op:
        try:
            batch_op.drop_constraint("fk_board_rows_source_note_id", type_="foreignkey")
        except Exception:
            pass
        batch_op.drop_column("source_note_id")
