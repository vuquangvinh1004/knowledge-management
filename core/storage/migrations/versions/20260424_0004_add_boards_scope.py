"""Thêm multi-board scope: bảng boards + board_id cho rows/columns.

Revision ID: 0004_add_boards_scope
Revises: 0003_add_link_weight
Create Date: 2026-04-24
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_boards_scope"
down_revision: Union[str, None] = "0003_add_link_weight"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(" ")


def upgrade() -> None:
    op.create_table(
        "boards",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("board_type", sa.String(32), nullable=False, server_default="general"),
        sa.Column("linked_note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="SET NULL")),
        sa.Column("scope", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    conn = op.get_bind()
    now = _utcnow_iso()
    conn.execute(
        sa.text(
            """
            INSERT INTO boards (title, board_type, linked_note_id, scope, created_at, updated_at)
            VALUES (:title, :board_type, NULL, :scope, :created_at, :updated_at)
            """
        ),
        {
            "title": "Research Board mặc định",
            "board_type": "legacy",
            "scope": "default",
            "created_at": now,
            "updated_at": now,
        },
    )
    default_board_id = conn.execute(sa.text("SELECT id FROM boards ORDER BY id LIMIT 1")).scalar()

    with op.batch_alter_table("board_rows") as batch_op:
        batch_op.add_column(sa.Column("board_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("board_columns") as batch_op:
        batch_op.add_column(sa.Column("board_id", sa.Integer(), nullable=True))

    conn.execute(
        sa.text("UPDATE board_rows SET board_id = :board_id WHERE board_id IS NULL"),
        {"board_id": default_board_id},
    )
    conn.execute(
        sa.text("UPDATE board_columns SET board_id = :board_id WHERE board_id IS NULL"),
        {"board_id": default_board_id},
    )

    with op.batch_alter_table("board_rows") as batch_op:
        batch_op.alter_column("board_id", nullable=False)
        batch_op.create_foreign_key("fk_board_rows_board_id", "boards", ["board_id"], ["id"], ondelete="CASCADE")
    with op.batch_alter_table("board_columns") as batch_op:
        batch_op.alter_column("board_id", nullable=False)
        batch_op.create_foreign_key("fk_board_columns_board_id", "boards", ["board_id"], ["id"], ondelete="CASCADE")

    op.create_index("ix_board_rows_board_id", "board_rows", ["board_id"], unique=False)
    op.create_index("ix_board_columns_board_id", "board_columns", ["board_id"], unique=False)


def downgrade() -> None:
    try:
        op.drop_index("ix_board_columns_board_id", table_name="board_columns")
    except Exception:
        pass
    try:
        op.drop_index("ix_board_rows_board_id", table_name="board_rows")
    except Exception:
        pass

    with op.batch_alter_table("board_columns") as batch_op:
        try:
            batch_op.drop_constraint("fk_board_columns_board_id", type_="foreignkey")
        except Exception:
            pass
        batch_op.drop_column("board_id")

    with op.batch_alter_table("board_rows") as batch_op:
        try:
            batch_op.drop_constraint("fk_board_rows_board_id", type_="foreignkey")
        except Exception:
            pass
        batch_op.drop_column("board_id")

    op.drop_table("boards")
