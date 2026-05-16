"""Schema v1 khởi tạo — toàn bộ bảng ban đầu cho Research PKM.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-22
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("file_path", sa.Text, nullable=False, unique=True),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("authors", sa.Text),
        sa.Column("year", sa.String(10)),
        sa.Column("doi", sa.Text),
        sa.Column("metadata_json", sa.Text),
        sa.Column("last_opened_page", sa.Integer, server_default="1"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- notes ---
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("slug", sa.Text, nullable=False, unique=True),
        sa.Column("note_type", sa.String(32), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False, unique=True),
        sa.Column("summary", sa.Text),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- extracts ---
    op.create_table(
        "extracts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="SET NULL")),
        sa.Column("page_no", sa.Integer, nullable=False),
        sa.Column("extract_type", sa.String(16), nullable=False),
        sa.Column("source_anchor", sa.Text, nullable=False),
        sa.Column("content_md", sa.Text, nullable=False),
        sa.Column("extra_json", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- assets ---
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="SET NULL")),
        sa.Column("asset_type", sa.String(16), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False, unique=True),
        sa.Column("caption", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # --- tags ---
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("color", sa.String(7)),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # --- note_tags ---
    op.create_table(
        "note_tags",
        sa.Column("note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("note_id", "tag_id"),
        sa.UniqueConstraint("note_id", "tag_id", name="uq_note_tag"),
    )

    # --- links ---
    op.create_table(
        "links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("from_note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # --- board_rows ---
    op.create_table(
        "board_rows",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # --- board_columns ---
    op.create_table(
        "board_columns",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # --- board_cells ---
    op.create_table(
        "board_cells",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("row_id", sa.Integer, sa.ForeignKey("board_rows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("col_id", sa.Integer, sa.ForeignKey("board_columns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="SET NULL")),
        sa.Column("content_md", sa.Text),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --- app_settings ---
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("setting_key", sa.Text, nullable=False, unique=True),
        sa.Column("setting_value", sa.Text, nullable=False),
    )

    # Seed schema_version = 1
    op.execute("INSERT INTO app_settings (setting_key, setting_value) VALUES ('schema_version', '1')")


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("board_cells")
    op.drop_table("board_columns")
    op.drop_table("board_rows")
    op.drop_table("links")
    op.drop_table("note_tags")
    op.drop_table("tags")
    op.drop_table("assets")
    op.drop_table("extracts")
    op.drop_table("notes")
    op.drop_table("sources")
