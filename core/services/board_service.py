"""Service quản lý Research Board theo board scope.

Sprint B refactor:
- Thêm entity `boards`
- Mọi thao tác rows/columns/cells được scope bởi `board_id`
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Board, BoardCell, BoardColumn, BoardRow
from core.storage.session import get_session
from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA
from core.utils.exceptions import PKMError
from core.services.board_crud import (
    create_board as crud_create_board,
    create_column as crud_create_column,
    create_from_template as crud_create_from_template,
    create_row as crud_create_row,
    delete_board as crud_delete_board,
    delete_column as crud_delete_column,
    delete_row as crud_delete_row,
    ensure_full_meta_columns as crud_ensure_full_meta_columns,
    get_board as crud_get_board,
    get_cell as crud_get_cell,
    get_default_board as crud_get_default_board,
    get_all_cells as crud_get_all_cells,
    list_boards as crud_list_boards,
    list_columns as crud_list_columns,
    list_rows as crud_list_rows,
    list_source_note_rows as crud_list_source_note_rows,
    rename_board as crud_rename_board,
    rename_column as crud_rename_column,
    rename_row as crud_rename_row,
    set_linked_note as crud_set_linked_note,
    update_cell as crud_update_cell,
)
from core.services.board_export import export_csv as board_export_csv, export_markdown as board_export_markdown
from core.services.board_sync import (
    cleanup_deprecated_source_note_metadata as board_sync_cleanup_deprecated_source_note_metadata,
    sync_cells_from_source_note_metadata as board_sync_cells_from_source_note_metadata,
    sync_rows_with_source_notes as board_sync_rows_with_source_notes,
)

META_ANALYSIS_COLUMNS = list(BOARD_META_ANALYSIS_CRITERIA)
REMOVED_META_ANALYSIS_COLUMNS = {
    "ID",
    "Mã nghiên cứu",
    "Hướng tác động",
    "Effect size",
    "Loại effect size",
    "SE/SD",
    "CI thấp",
    "CI cao",
    "p-value",
    "Chất lượng nghiên cứu",
    "Ghi chú mã hóa",
    "Link source_note",
    "Link concept_note",
    "Link synthesis_note",
}

LITERATURE_COLUMNS = [
    "Mã nghiên cứu",
    "Tác giả",
    "Năm",
    "Tiêu đề",
    "Quốc gia/Bối cảnh",
    "Loại nguồn",
    "Mục tiêu nghiên cứu",
    "Câu hỏi nghiên cứu",
    "Lý thuyết/khung phân tích",
    "Chủ đề chính",
    "Biến độc lập",
    "Biến phụ thuộc",
    "Phương pháp nghiên cứu",
    "Kết quả chính",
    "Hạn chế",
    "Ghi chú mã hóa",
]

_META_SECTION_RE = re.compile(r"^##\s+Metadata\s*$", re.IGNORECASE)
_MY_NOTES_SECTION_RE = re.compile(r"^##\s+Ghi\s+chú\s+của\s+tôi\s*$", re.IGNORECASE)
_META_CALLOUT_RE = re.compile(r"^>\s*\[!\s*(.*?)\s*\]\s*$")


class BoardService:
    """CRUD cho board, rows, columns và cells theo board_id."""

    # ------------------------------------------------------------------
    # Board CRUD
    # ------------------------------------------------------------------

    def create_board(
        self,
        title: str,
        board_type: str = "general",
        linked_note_id: int | None = None,
        scope: str | None = None,
    ) -> Board:
        return crud_create_board(title, board_type=board_type, linked_note_id=linked_note_id, scope=scope)

    def list_boards(self) -> list[Board]:
        return crud_list_boards()

    def get_board(self, board_id: int) -> Board:
        return crud_get_board(board_id)

    def get_default_board(self) -> Board:
        return crud_get_default_board()

    def rename_board(self, board_id: int, title: str) -> None:
        crud_rename_board(board_id, title)

    def delete_board(self, board_id: int) -> None:
        crud_delete_board(board_id)

    def set_linked_note(self, board_id: int, note_id: int | None) -> None:
        """Gắn hoặc bỏ gắn board_note cho board."""
        crud_set_linked_note(board_id, note_id)

    def create_from_template(
        self,
        template_name: str,
        title: str,
        *,
        notes_dir: Path | None = None,
        create_linked_board_note: bool = False,
    ) -> tuple[Board | None, int | None]:
        """Khởi tạo board/note theo template Sprint C.

        Returns:
            (board_or_none, linked_note_id_or_none)
        """
        return crud_create_from_template(
            template_name,
            title,
            notes_dir=notes_dir,
            create_linked_board_note=create_linked_board_note,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_board_id(self, board_id: int | None) -> int:
        if board_id is not None:
            return board_id
        return self.get_default_board().id

    def ensure_full_meta_columns(self, board_id: int | None = None) -> list[BoardColumn]:
        """Đảm bảo board có đủ bộ cột meta-analysis tiêu chuẩn.

        Quy tắc quan trọng:
        - Chỉ thêm cột còn thiếu; KHÔNG bao giờ đặt lại sort_order của cột đã tồn tại
          để thứ tự tuỳ chỉnh của người dùng được bảo toàn sau restart.
        - Cột tiêu chí deprecated bị xóa cứng.
        """
        return crud_ensure_full_meta_columns(board_id)

    def sync_rows_with_source_notes(
        self,
        board_id: int | None = None,
        *,
        project_id: int | None = None,
    ) -> list[BoardRow]:
        """Đồng bộ hàng board theo source_note (1 hàng = 1 source_note).

        Không xóa hàng legacy không gắn source_note để tránh mất dữ liệu cũ.
        """
        return board_sync_rows_with_source_notes(board_id=board_id, project_id=project_id)

    def sync_cells_from_source_note_metadata(
        self,
        board_id: int | None = None,
        *,
        project_id: int | None = None,
    ) -> int:
        """Đồng bộ metadata từ source_note vào cell của Research Board.

        Chỉ cập nhật các source_note còn active. Dữ liệu cũ của row legacy vẫn được giữ.
        """
        return board_sync_cells_from_source_note_metadata(board_id=board_id, project_id=project_id)

    def cleanup_deprecated_source_note_metadata(
        self,
        *,
        project_id: int | None = None,
    ) -> int:
        """Dọn các callout metadata deprecated trong toàn bộ source_note active.

        Returns:
            Số lượng source_note đã được chỉnh sửa file markdown.
        """
        return board_sync_cleanup_deprecated_source_note_metadata(project_id=project_id)

    def list_source_note_rows(self, board_id: int | None = None) -> list[BoardRow]:
        """Liệt kê hàng đã gắn source_note cho board hiện tại."""
        return crud_list_source_note_rows(board_id=board_id)

    # ------------------------------------------------------------------
    # Rows
    # ------------------------------------------------------------------

    def create_row(
        self,
        label: str,
        board_id: int | None = None,
        source_note_id: int | None = None,
    ) -> BoardRow:
        return crud_create_row(label, board_id=board_id, source_note_id=source_note_id)

    def list_rows(self, board_id: int | None = None) -> list[BoardRow]:
        return crud_list_rows(board_id=board_id)

    def rename_row(self, row_id: int, label: str, board_id: int | None = None) -> None:
        crud_rename_row(row_id, label, board_id=board_id)

    def delete_row(self, row_id: int, board_id: int | None = None) -> None:
        crud_delete_row(row_id, board_id=board_id)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    def create_column(self, label: str, board_id: int | None = None) -> BoardColumn:
        return crud_create_column(label, board_id=board_id)

    def list_columns(self, board_id: int | None = None, *, visible_only: bool = False) -> list[BoardColumn]:
        return crud_list_columns(board_id=board_id, visible_only=visible_only)

    def apply_column_configuration(
        self,
        board_id: int | None,
        configurations: list[dict[str, object]],
    ) -> None:
        """Áp dụng cấu hình cột từ dialog Tùy chỉnh.

        Mỗi cấu hình gồm: id (int|None), label (str), visible (bool).
        - Cột hệ thống meta-analysis nếu bị loại khỏi danh sách sẽ được ẩn thay vì xóa.
        - Cột tự tạo bị loại khỏi danh sách sẽ bị xóa.
        """
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            existing = (
                session.query(BoardColumn)
                .filter(BoardColumn.board_id == resolved_board_id)
                .order_by(BoardColumn.sort_order, BoardColumn.id)
                .all()
            )
            by_id = {int(c.id): c for c in existing}
            kept_ids: set[int] = set()
            used_labels: set[str] = set()

            for idx, cfg in enumerate(configurations):
                raw_label = str(cfg.get("label", "")).strip()
                if not raw_label:
                    raise PKMError("Tên tiêu chí không được để trống.")

                lowered = raw_label.lower()
                if lowered in used_labels:
                    raise PKMError(f"Tiêu chí bị trùng: {raw_label}")
                used_labels.add(lowered)

                raw_id = cfg.get("id")
                col_id = int(raw_id) if isinstance(raw_id, int) else None
                visible = bool(cfg.get("visible", True))

                if col_id is not None and col_id in by_id:
                    col = by_id[col_id]
                    col.label = raw_label
                    col.sort_order = idx
                    col.is_visible = visible
                    kept_ids.add(col_id)
                else:
                    col = BoardColumn(
                        board_id=resolved_board_id,
                        label=raw_label,
                        sort_order=idx,
                        is_visible=visible,
                    )
                    session.add(col)
                    session.flush()
                    kept_ids.add(int(col.id))

            tail_order = len(configurations)
            for col in existing:
                if int(col.id) in kept_ids:
                    continue
                if str(col.label) in META_ANALYSIS_COLUMNS:
                    # Cột hệ thống: không xóa dữ liệu, chỉ ẩn.
                    col.is_visible = False
                    col.sort_order = tail_order
                    tail_order += 1
                else:
                    session.delete(col)

            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

    def rename_column(self, col_id: int, label: str, board_id: int | None = None) -> None:
        crud_rename_column(col_id, label, board_id=board_id)

    def delete_column(self, col_id: int, board_id: int | None = None) -> None:
        crud_delete_column(col_id, board_id=board_id)

    # ------------------------------------------------------------------
    # Cells
    # ------------------------------------------------------------------

    def get_cell(self, row_id: int, col_id: int, board_id: int | None = None) -> BoardCell | None:
        return crud_get_cell(row_id, col_id, board_id=board_id)

    def update_cell(
        self,
        row_id: int,
        col_id: int,
        content_md: str = "",
        linked_note_id: int | None = None,
        board_id: int | None = None,
    ) -> BoardCell:
        return crud_update_cell(row_id, col_id, content_md=content_md, linked_note_id=linked_note_id, board_id=board_id)

    def get_all_cells(self, board_id: int | None = None) -> list[BoardCell]:
        return crud_get_all_cells(board_id=board_id)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_markdown(self, board_id: int | None = None) -> str:
        return board_export_markdown(board_id=board_id)

    def export_csv(self, board_id: int | None = None) -> str:
        return board_export_csv(board_id=board_id)
