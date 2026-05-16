"""Thêm Project Mode: bảng projects, project_note_refs và cột notes.project_id.

Revision ID: 0007_add_project_mode
Revises: 0006_rename_source_note_titles
Create Date: 2026-05-04

Schema changes:
- CREATE TABLE projects (id, name, description, status, is_deleted, created_at, updated_at, closed_at, meta_json)
- CREATE TABLE project_note_refs (project_id FK, note_id FK, added_at) UNIQUE(project_id, note_id)
- ALTER TABLE notes ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_project_mode"
down_revision: Union[str, None] = "0006_rename_source_note_titles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Bảng projects
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("meta_json", sa.Text),
    )
    op.create_index("ix_projects_status", "projects", ["status"], unique=False)

    # 2. Bảng project_note_refs
    op.create_table(
        "project_note_refs",
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("added_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("project_id", "note_id", name="uq_project_note_ref"),
    )
    op.create_index("ix_project_note_refs_project_id", "project_note_refs", ["project_id"], unique=False)

    # 3. Thêm cột project_id vào notes (nullable, NULL = Global note)
    with op.batch_alter_table("notes") as batch_op:
        batch_op.add_column(
            sa.Column("project_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_notes_project_id", "projects", ["project_id"], ["id"], ondelete="SET NULL"
        )
    op.create_index("ix_notes_project_id", "notes", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notes_project_id", table_name="notes")
    with op.batch_alter_table("notes") as batch_op:
        batch_op.drop_column("project_id")

    op.drop_index("ix_project_note_refs_project_id", table_name="project_note_refs")
    op.drop_table("project_note_refs")

    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_table("projects")
