"""Thêm indexes để optimize query performance.

Indexes được thêm trên các FK columns thường dùng trong WHERE/JOIN:
- notes.source_id: dùng khi filter notes theo source
- extracts.note_id: dùng khi filter extracts theo note
- links.from_note_id, links.to_note_id: dùng khi query graph
- note_tags.tag_id: dùng khi filter notes theo tag
- notes.project_id: dùng khi filter notes theo project

Revision ID: 0008_add_query_indexes
Revises: 0007_add_project_mode
Create Date: 2026-05-16
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_add_query_indexes"
down_revision: Union[str, None] = "0007_add_project_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm indexes cho các FK columns hay dùng."""
    # FK để query notes theo source
    try:
        op.create_index("ix_notes_source_id", "notes", ["source_id"])
    except Exception:
        pass
    
    # FK để query extracts theo note
    try:
        op.create_index("ix_extracts_note_id", "extracts", ["note_id"])
    except Exception:
        pass
    
    # FK để query extracts theo source
    try:
        op.create_index("ix_extracts_source_id", "extracts", ["source_id"])
    except Exception:
        pass
    
    # FK để query links (graph queries)
    try:
        op.create_index("ix_links_from_note_id", "links", ["from_note_id"])
    except Exception:
        pass
    
    try:
        op.create_index("ix_links_to_note_id", "links", ["to_note_id"])
    except Exception:
        pass
    
    # FK để query note_tags theo tag (filter notes by tag)
    try:
        op.create_index("ix_note_tags_tag_id", "note_tags", ["tag_id"])
    except Exception:
        pass
    
    # FK để query notes theo project
    try:
        op.create_index("ix_notes_project_id", "notes", ["project_id"])
    except Exception:
        pass
    
    # FK để query assets theo note
    try:
        op.create_index("ix_assets_note_id", "assets", ["note_id"])
    except Exception:
        pass
    
    # FK để query board_cells theo linked_note
    try:
        op.create_index("ix_board_cells_linked_note_id", "board_cells", ["linked_note_id"])
    except Exception:
        pass
    
    # FK để query boards theo linked_note
    try:
        op.create_index("ix_boards_linked_note_id", "boards", ["linked_note_id"])
    except Exception:
        pass


def downgrade() -> None:
    """Xóa tất cả indexes mới thêm."""
    try:
        op.drop_index("ix_notes_source_id", "notes")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_extracts_note_id", "extracts")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_extracts_source_id", "extracts")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_links_from_note_id", "links")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_links_to_note_id", "links")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_note_tags_tag_id", "note_tags")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_notes_project_id", "notes")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_assets_note_id", "assets")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_board_cells_linked_note_id", "board_cells")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_boards_linked_note_id", "boards")
    except Exception:
        pass
