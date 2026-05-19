"""Add public_id (UUIDv7) for primary domain entities.

Revision ID: 0011_add_public_id_uuidv7
Revises: 0010_add_board_column_visibility
Create Date: 2026-05-19
"""
from __future__ import annotations

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "0011_add_public_id_uuidv7"
down_revision: Union[str, None] = "0010_add_board_column_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES: tuple[str, ...] = (
    "projects",
    "sources",
    "notes",
    "extracts",
    "assets",
    "tags",
    "links",
    "boards",
    "board_rows",
    "board_columns",
    "board_cells",
)


def _new_public_id() -> str:
    uuid7_factory = getattr(uuid, "uuid7", None)
    if callable(uuid7_factory):
        return str(uuid7_factory())
    return str(uuid.uuid4())


def _backfill_public_id(conn, table_name: str) -> None:
    rows = conn.execute(
        sa.text(f"SELECT id FROM {table_name} WHERE public_id IS NULL ORDER BY id")
    ).fetchall()
    for row in rows:
        conn.execute(
            sa.text(f"UPDATE {table_name} SET public_id = :public_id WHERE id = :id"),
            {"public_id": _new_public_id(), "id": int(row[0])},
        )


def upgrade() -> None:
    for table_name in _TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("public_id", sa.String(length=36), nullable=True))

    conn = op.get_bind()
    for table_name in _TABLES:
        _backfill_public_id(conn, table_name)

    for table_name in _TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "public_id",
                existing_type=sa.String(length=36),
                nullable=False,
            )
            batch_op.create_unique_constraint(
                f"uq_{table_name}_public_id",
                ["public_id"],
            )


def downgrade() -> None:
    for table_name in reversed(_TABLES):
        with op.batch_alter_table(table_name) as batch_op:
            try:
                batch_op.drop_constraint(f"uq_{table_name}_public_id", type_="unique")
            except Exception:
                pass
            batch_op.drop_column("public_id")
