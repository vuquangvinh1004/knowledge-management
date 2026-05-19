"""Service quản lý Research Board theo board scope.

Sprint B refactor:
- Thêm entity `boards`
- Mọi thao tác rows/columns/cells được scope bởi `board_id`
"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from pathlib import Path

from core.storage.models import Board, BoardCell, BoardColumn, BoardRow, Note
from core.storage.session import get_session
from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()

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
        title = title.strip()
        if not title:
            raise PKMError("Tên board không được để trống.")

        now = datetime.now(timezone.utc)
        with get_session() as session:
            board = Board(
                title=title,
                board_type=board_type.strip() or "general",
                linked_note_id=linked_note_id,
                scope=scope,
                created_at=now,
                updated_at=now,
            )
            session.add(board)
            session.flush()
            session.expunge(board)
        return board

    def list_boards(self) -> list[Board]:
        with get_session() as session:
            boards = session.query(Board).order_by(Board.updated_at.desc(), Board.id.desc()).all()
            for b in boards:
                session.expunge(b)
            return boards

    def get_board(self, board_id: int) -> Board:
        with get_session() as session:
            board = session.get(Board, board_id)
            if board is None:
                raise PKMError(f"Không tìm thấy board id={board_id}.")
            session.expunge(board)
            return board

    def get_default_board(self) -> Board:
        with get_session() as session:
            board = (
                session.query(Board)
                .filter(Board.scope == "default")
                .order_by(Board.id.asc())
                .first()
            )
            if board is None:
                now = datetime.now(timezone.utc)
                board = Board(
                    title="Research Board mặc định",
                    board_type="general",
                    scope="default",
                    created_at=now,
                    updated_at=now,
                )
                session.add(board)
                session.flush()
            session.expunge(board)
            return board

    def rename_board(self, board_id: int, title: str) -> None:
        title = title.strip()
        if not title:
            raise PKMError("Tên board không được để trống.")
        with get_session() as session:
            board = session.get(Board, board_id)
            if board is None:
                raise PKMError(f"Không tìm thấy board id={board_id}.")
            board.title = title
            board.updated_at = datetime.now(timezone.utc)

    def delete_board(self, board_id: int) -> None:
        with get_session() as session:
            board = session.get(Board, board_id)
            if board is None:
                raise PKMError(f"Không tìm thấy board id={board_id}.")
            session.delete(board)

    def set_linked_note(self, board_id: int, note_id: int | None) -> None:
        """Gắn hoặc bỏ gắn board_note cho board."""
        with get_session() as session:
            board = session.get(Board, board_id)
            if board is None:
                raise PKMError(f"Không tìm thấy board id={board_id}.")
            board.linked_note_id = note_id
            board.updated_at = datetime.now(timezone.utc)

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
        template = template_name.strip().lower()
        title = title.strip()
        if not title:
            raise PKMError("Tên board/note không được để trống.")

        if template in {"meta_analysis", "literature"}:
            board_type = template
            columns = META_ANALYSIS_COLUMNS if template == "meta_analysis" else LITERATURE_COLUMNS
            board = self.create_board(title=title, board_type=board_type)
            for col in columns:
                self.create_column(col, board_id=board.id)

            linked_note_id: int | None = None
            if create_linked_board_note:
                if notes_dir is None:
                    raise PKMError("Thiếu notes_dir để tạo board_note đi kèm.")
                linked_note_id = self._create_board_note(title=title, notes_dir=notes_dir)
                self.set_linked_note(board.id, linked_note_id)

            return self.get_board(board.id), linked_note_id

        if template == "board_note":
            if notes_dir is None:
                raise PKMError("Thiếu notes_dir để tạo board_note.")
            note_id = self._create_board_note(title=title, notes_dir=notes_dir)
            return None, note_id

        raise PKMError(f"Template không hợp lệ: {template_name!r}.")

    def _create_board_note(self, title: str, notes_dir: Path) -> int:
        """Tạo board_note markdown từ template chuẩn."""
        from core.services.note_service import NoteService

        note_title = title if title.lower().startswith("board ") else f"board {title}"
        note = NoteService(notes_dir).create_note(
            title=note_title,
            note_type="board_note",
            initial_content=NoteService.build_template("board_note", note_title),
        )
        return note.id

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_board_id(self, board_id: int | None) -> int:
        if board_id is not None:
            return board_id
        return self.get_default_board().id

    def ensure_full_meta_columns(self, board_id: int | None = None) -> list[BoardColumn]:
        """Đảm bảo board có đủ bộ cột meta-analysis 30 cột theo thứ tự chuẩn.

        Ghi chú: không xóa cột legacy để tránh mất dữ liệu cũ; UI sẽ chỉ dùng bộ 30 cột chuẩn.
        """
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            existing = (
                session.query(BoardColumn)
                .filter(BoardColumn.board_id == resolved_board_id)
                .order_by(BoardColumn.sort_order, BoardColumn.id)
                .all()
            )

            # Dọn dẹp triệt để các tiêu chí đã bị loại khỏi chuẩn hệ thống.
            for col in existing:
                if str(col.label) in REMOVED_META_ANALYSIS_COLUMNS:
                    session.delete(col)

            session.flush()
            existing = (
                session.query(BoardColumn)
                .filter(BoardColumn.board_id == resolved_board_id)
                .order_by(BoardColumn.sort_order, BoardColumn.id)
                .all()
            )
            by_label: dict[str, BoardColumn] = {str(col.label): col for col in existing}

            for idx, label in enumerate(META_ANALYSIS_COLUMNS):
                col = by_label.get(label)
                if col is None:
                    col = BoardColumn(
                        board_id=resolved_board_id,
                        label=label,
                        sort_order=idx,
                        is_visible=True,
                    )
                    session.add(col)
                else:
                    col.sort_order = idx

            board = session.get(Board, resolved_board_id)
            if board:
                board.board_type = "meta_analysis"
                board.updated_at = datetime.now(timezone.utc)

            session.flush()
            cols = (
                session.query(BoardColumn)
                .filter(
                    BoardColumn.board_id == resolved_board_id,
                    BoardColumn.label.in_(META_ANALYSIS_COLUMNS),
                )
                .order_by(BoardColumn.sort_order, BoardColumn.id)
                .all()
            )
            for c in cols:
                session.expunge(c)
            return cols

    def sync_rows_with_source_notes(
        self,
        board_id: int | None = None,
        *,
        project_id: int | None = None,
    ) -> list[BoardRow]:
        """Đồng bộ hàng board theo source_note (1 hàng = 1 source_note).

        Không xóa hàng legacy không gắn source_note để tránh mất dữ liệu cũ.
        """
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService
        from core.services.project_service import ProjectService

        resolved_board_id = self._resolve_board_id(board_id)

        note_svc = NoteService(NOTES_DIR)
        notes = note_svc.list_all(note_type="source_note", include_deleted=False)

        if project_id is not None:
            allowed = ProjectService().get_project_note_ids(project_id)
            notes = [n for n in notes if int(n.id) in allowed]

        notes = sorted(notes, key=lambda n: str(n.title or "").lower())

        with get_session() as session:
            rows = (
                session.query(BoardRow)
                .filter(BoardRow.board_id == resolved_board_id)
                .all()
            )
            by_source_note_id = {
                int(r.source_note_id): r
                for r in rows
                if isinstance(r.source_note_id, int)
            }

            for idx, note in enumerate(notes):
                row = by_source_note_id.get(int(note.id))
                if row is None:
                    row = BoardRow(
                        board_id=resolved_board_id,
                        source_note_id=int(note.id),
                        label=str(note.title or f"source_note {note.id}"),
                        sort_order=idx,
                    )
                    session.add(row)
                else:
                    row.label = str(note.title or row.label)
                    row.sort_order = idx

            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

            session.flush()
            linked_rows = (
                session.query(BoardRow)
                .filter(
                    BoardRow.board_id == resolved_board_id,
                    BoardRow.source_note_id.is_not(None),
                )
                .order_by(BoardRow.sort_order, BoardRow.id)
                .all()
            )
            for r in linked_rows:
                session.expunge(r)
            return linked_rows

    @staticmethod
    def _normalize_meta_key(text: str) -> str:
        return " ".join(str(text or "").strip().upper().split())

    @classmethod
    def _strip_deprecated_metadata_blocks(cls, markdown: str) -> tuple[str, int]:
        """Xóa các callout metadata deprecated khỏi markdown source_note.

        Chỉ xóa block quote theo cấu trúc:
        > [!TIÊU CHÍ]
        > giá trị...
        """
        lines = markdown.splitlines()
        removed = 0
        out: list[str] = []
        idx = 0
        removed_keys = {cls._normalize_meta_key(k) for k in REMOVED_META_ANALYSIS_COLUMNS}

        while idx < len(lines):
            line = lines[idx]
            callout = _META_CALLOUT_RE.match(line)
            if not callout:
                out.append(line)
                idx += 1
                continue

            raw_key = cls._normalize_meta_key(callout.group(1))
            if raw_key not in removed_keys:
                out.append(line)
                idx += 1
                continue

            # Bỏ cả block của tiêu chí deprecated cho tới trước callout/heading kế tiếp.
            removed += 1
            idx += 1
            while idx < len(lines):
                current = lines[idx]
                if current.startswith("## "):
                    break
                if _META_CALLOUT_RE.match(current):
                    break
                idx += 1

            # Dọn các dòng trống dư ngay sau block đã xóa.
            while idx < len(lines) and lines[idx].strip() == "":
                idx += 1

        cleaned = "\n".join(out).rstrip() + "\n"
        return cleaned, removed

    @classmethod
    def _parse_source_note_metadata(cls, markdown: str) -> dict[str, str]:
        """Parse section '## Metadata' theo cấu trúc quote callout.

        Định dạng hỗ trợ:
        > [!TÊN TIÊU CHÍ]
        > Giá trị dòng 1
        > Giá trị dòng 2
        """
        lines = markdown.splitlines()

        def _parse_from(start_idx: int) -> dict[str, str]:
            parsed: dict[str, str] = {}
            idx = start_idx
            while idx < len(lines):
                line = lines[idx]
                if line.startswith("## "):
                    break

                callout = _META_CALLOUT_RE.match(line)
                if not callout:
                    idx += 1
                    continue

                raw_key = cls._normalize_meta_key(callout.group(1))
                idx += 1

                value_lines: list[str] = []
                while idx < len(lines):
                    current = lines[idx]
                    if current.startswith("## "):
                        break
                    if _META_CALLOUT_RE.match(current):
                        break

                    stripped = current.strip()
                    if current.lstrip().startswith(">"):
                        payload = current.lstrip()[1:]
                        if payload.startswith(" "):
                            payload = payload[1:]
                        value_lines.append(payload.rstrip())
                        idx += 1
                        continue

                    # Backward-compatible: chấp nhận dòng thường nếu người dùng không giữ prefix '>'
                    if stripped:
                        value_lines.append(current.rstrip())
                        idx += 1
                        continue

                    value_lines.append("")
                    idx += 1

                value = "\n".join(value_lines).strip()
                normalized_placeholder = cls._normalize_meta_key(value).rstrip(".")
                if normalized_placeholder in {"THÔNG TIN TIÊU CHÍ", "THONG TIN TIEU CHI"}:
                    value = ""

                if raw_key:
                    parsed[raw_key] = value
            return parsed

        metadata_start: int | None = None
        notes_start: int | None = None
        for i, line in enumerate(lines):
            normalized = line.strip()
            if metadata_start is None and _META_SECTION_RE.match(normalized):
                metadata_start = i + 1
            if notes_start is None and _MY_NOTES_SECTION_RE.match(normalized):
                notes_start = i + 1

        if metadata_start is not None:
            return _parse_from(metadata_start)
        if notes_start is not None:
            return _parse_from(notes_start)
        return {}

    def sync_cells_from_source_note_metadata(
        self,
        board_id: int | None = None,
        *,
        project_id: int | None = None,
    ) -> int:
        """Đồng bộ metadata từ source_note vào cell của Research Board.

        Chỉ cập nhật các source_note còn active. Dữ liệu cũ của row legacy vẫn được giữ.
        """
        resolved_board_id = self._resolve_board_id(board_id)
        now = datetime.now(timezone.utc)

        with get_session() as session:
            rows = (
                session.query(BoardRow)
                .filter(
                    BoardRow.board_id == resolved_board_id,
                    BoardRow.source_note_id.is_not(None),
                )
                .all()
            )
            if not rows:
                return 0

            note_ids = [int(r.source_note_id) for r in rows if r.source_note_id is not None]
            notes = (
                session.query(Note)
                .filter(
                    Note.id.in_(note_ids),
                    Note.note_type == "source_note",
                    Note.is_deleted == 0,
                )
                .all()
            )

            note_by_id = {int(n.id): n for n in notes if n.id is not None}
            if not note_by_id:
                return 0

            columns = (
                session.query(BoardColumn)
                .filter(
                    BoardColumn.board_id == resolved_board_id,
                    BoardColumn.label.in_(META_ANALYSIS_COLUMNS),
                )
                .all()
            )
            col_by_key = {
                self._normalize_meta_key(str(c.label)): c
                for c in columns
            }
            if not col_by_key:
                return 0

            row_ids = [int(r.id) for r in rows if r.id is not None]
            col_ids = [int(c.id) for c in columns if c.id is not None]
            existing_cells = (
                session.query(BoardCell)
                .filter(
                    BoardCell.row_id.in_(row_ids),
                    BoardCell.col_id.in_(col_ids),
                )
                .all()
            )
            existing_map = {(int(c.row_id), int(c.col_id)): c for c in existing_cells}

            changed = 0
            for row in rows:
                row_id = int(row.id)
                source_note_id = int(row.source_note_id or 0)
                note = note_by_id.get(source_note_id)
                if note is None:
                    continue

                file_path = Path(str(note.file_path or ""))
                if not file_path.exists():
                    continue

                metadata = self._parse_source_note_metadata(file_path.read_text(encoding="utf-8"))
                if not metadata:
                    continue

                for key, value in metadata.items():
                    col = col_by_key.get(key)
                    if col is None:
                        continue

                    map_key = (row_id, int(col.id))
                    current = existing_map.get(map_key)
                    if current is None:
                        session.add(
                            BoardCell(
                                row_id=row_id,
                                col_id=int(col.id),
                                content_md=value,
                                updated_at=now,
                            )
                        )
                        changed += 1
                        continue

                    if (current.content_md or "") != value:
                        current.content_md = value
                        current.updated_at = now
                        changed += 1

            if changed > 0:
                board = session.get(Board, resolved_board_id)
                if board is not None:
                    board.updated_at = now
            return changed

    def cleanup_deprecated_source_note_metadata(
        self,
        *,
        project_id: int | None = None,
    ) -> int:
        """Dọn các callout metadata deprecated trong toàn bộ source_note active.

        Returns:
            Số lượng source_note đã được chỉnh sửa file markdown.
        """
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService
        from core.services.project_service import ProjectService

        note_svc = NoteService(NOTES_DIR)
        notes = note_svc.list_all(note_type="source_note", include_deleted=False)

        if project_id is not None:
            allowed = ProjectService().get_project_note_ids(project_id)
            notes = [n for n in notes if int(n.id) in allowed]

        changed_notes = 0
        for note in notes:
            file_path = Path(str(note.file_path or ""))
            if not file_path.exists():
                continue

            original = file_path.read_text(encoding="utf-8")
            cleaned, removed_blocks = self._strip_deprecated_metadata_blocks(original)
            if removed_blocks <= 0 or cleaned == original:
                continue

            file_path.write_text(cleaned, encoding="utf-8")
            changed_notes += 1

        if changed_notes > 0:
            logger.info(f"Đã cleanup callout metadata deprecated cho {changed_notes} source_note")
        return changed_notes

    def list_source_note_rows(self, board_id: int | None = None) -> list[BoardRow]:
        """Liệt kê hàng đã gắn source_note cho board hiện tại."""
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            rows = (
                session.query(BoardRow)
                .filter(
                    BoardRow.board_id == resolved_board_id,
                    BoardRow.source_note_id.is_not(None),
                )
                .order_by(BoardRow.sort_order, BoardRow.id)
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows

    def _assert_row_in_board(self, row_id: int, board_id: int, session) -> None:
        row = session.get(BoardRow, row_id)
        if row is None or row.board_id != board_id:
            raise PKMError(f"Row id={row_id} không thuộc board id={board_id}.")

    def _assert_col_in_board(self, col_id: int, board_id: int, session) -> None:
        col = session.get(BoardColumn, col_id)
        if col is None or col.board_id != board_id:
            raise PKMError(f"Column id={col_id} không thuộc board id={board_id}.")

    # ------------------------------------------------------------------
    # Rows
    # ------------------------------------------------------------------

    def create_row(
        self,
        label: str,
        board_id: int | None = None,
        source_note_id: int | None = None,
    ) -> BoardRow:
        label = label.strip()
        if not label:
            raise PKMError("Nhãn hàng không được để trống.")
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            if source_note_id is not None:
                source_note = session.get(Note, int(source_note_id))
                if source_note is None or source_note.is_deleted or source_note.note_type != "source_note":
                    raise PKMError("source_note_id không hợp lệ cho board row.")

            max_order = (
                session.query(BoardRow)
                .filter(BoardRow.board_id == resolved_board_id)
                .count()
            )
            row = BoardRow(
                board_id=resolved_board_id,
                source_note_id=source_note_id,
                label=label,
                sort_order=max_order,
            )
            session.add(row)
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(row)
        return row

    def list_rows(self, board_id: int | None = None) -> list[BoardRow]:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            rows = (
                session.query(BoardRow)
                .filter(BoardRow.board_id == resolved_board_id)
                .order_by(BoardRow.sort_order, BoardRow.id)
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows

    def rename_row(self, row_id: int, label: str, board_id: int | None = None) -> None:
        label = label.strip()
        if not label:
            raise PKMError("Nhãn hàng không được để trống.")
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            self._assert_row_in_board(row_id, resolved_board_id, session)
            row = session.get(BoardRow, row_id)
            row.label = label
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

    def delete_row(self, row_id: int, board_id: int | None = None) -> None:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            self._assert_row_in_board(row_id, resolved_board_id, session)
            row = session.get(BoardRow, row_id)
            session.delete(row)
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    def create_column(self, label: str, board_id: int | None = None) -> BoardColumn:
        label = label.strip()
        if not label:
            raise PKMError("Nhãn cột không được để trống.")
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            max_order = (
                session.query(BoardColumn)
                .filter(BoardColumn.board_id == resolved_board_id)
                .count()
            )
            col = BoardColumn(
                board_id=resolved_board_id,
                label=label,
                sort_order=max_order,
                is_visible=True,
            )
            session.add(col)
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(col)
        return col

    def list_columns(self, board_id: int | None = None, *, visible_only: bool = False) -> list[BoardColumn]:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            query = (
                session.query(BoardColumn)
                .filter(BoardColumn.board_id == resolved_board_id)
            )
            if visible_only:
                query = query.filter(BoardColumn.is_visible.is_(True))

            cols = query.order_by(BoardColumn.sort_order, BoardColumn.id).all()
            for c in cols:
                session.expunge(c)
            return cols

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
        label = label.strip()
        if not label:
            raise PKMError("Nhãn cột không được để trống.")
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            self._assert_col_in_board(col_id, resolved_board_id, session)
            col = session.get(BoardColumn, col_id)
            col.label = label
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

    def delete_column(self, col_id: int, board_id: int | None = None) -> None:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            self._assert_col_in_board(col_id, resolved_board_id, session)
            col = session.get(BoardColumn, col_id)
            session.delete(col)
            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Cells
    # ------------------------------------------------------------------

    def get_cell(self, row_id: int, col_id: int, board_id: int | None = None) -> BoardCell | None:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            row = session.get(BoardRow, row_id)
            col = session.get(BoardColumn, col_id)
            if row is None or col is None:
                return None
            if row.board_id != resolved_board_id or col.board_id != resolved_board_id:
                return None
            cell = (
                session.query(BoardCell)
                .filter(BoardCell.row_id == row_id, BoardCell.col_id == col_id)
                .first()
            )
            if cell:
                session.expunge(cell)
            return cell

    def update_cell(
        self,
        row_id: int,
        col_id: int,
        content_md: str = "",
        linked_note_id: int | None = None,
        board_id: int | None = None,
    ) -> BoardCell:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            self._assert_row_in_board(row_id, resolved_board_id, session)
            self._assert_col_in_board(col_id, resolved_board_id, session)
            cell = (
                session.query(BoardCell)
                .filter(BoardCell.row_id == row_id, BoardCell.col_id == col_id)
                .first()
            )
            if cell is None:
                cell = BoardCell(
                    row_id=row_id,
                    col_id=col_id,
                    content_md=content_md,
                    linked_note_id=linked_note_id,
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(cell)
            else:
                cell.content_md = content_md
                cell.linked_note_id = linked_note_id
                cell.updated_at = datetime.now(timezone.utc)

            board = session.get(Board, resolved_board_id)
            if board:
                board.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(cell)
            return cell

    def get_all_cells(self, board_id: int | None = None) -> list[BoardCell]:
        resolved_board_id = self._resolve_board_id(board_id)
        with get_session() as session:
            cells = (
                session.query(BoardCell)
                .join(BoardRow, BoardRow.id == BoardCell.row_id)
                .join(BoardColumn, BoardColumn.id == BoardCell.col_id)
                .filter(
                    BoardRow.board_id == resolved_board_id,
                    BoardColumn.board_id == resolved_board_id,
                )
                .all()
            )
            for c in cells:
                session.expunge(c)
            return cells

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_markdown(self, board_id: int | None = None) -> str:
        rows = self.list_rows(board_id=board_id)
        cols = self.list_columns(board_id=board_id, visible_only=True)

        if not rows or not cols:
            return "_Board chưa có dữ liệu._"

        header = "| | " + " | ".join(c.label for c in cols) + " |"
        separator = "|---" + "|---" * len(cols) + "|"

        md_rows: list[str] = [header, separator]
        for row in rows:
            cells_map: dict[int, str] = {}
            with get_session() as session:
                cells = (
                    session.query(BoardCell)
                    .filter(BoardCell.row_id == row.id)
                    .all()
                )
                for c in cells:
                    cells_map[c.col_id] = (c.content_md or "").replace("\n", " ")

            cell_values = [cells_map.get(c.id, "") for c in cols]
            md_rows.append("| " + row.label + " | " + " | ".join(cell_values) + " |")

        return "\n".join(md_rows)

    def export_csv(self, board_id: int | None = None) -> str:
        rows = self.list_rows(board_id=board_id)
        cols = self.list_columns(board_id=board_id, visible_only=True)

        buf = io.StringIO()
        writer = csv.writer(buf)

        writer.writerow([""] + [c.label for c in cols])
        for row in rows:
            cells_map: dict[int, str] = {}
            with get_session() as session:
                cells = (
                    session.query(BoardCell)
                    .filter(BoardCell.row_id == row.id)
                    .all()
                )
                for c in cells:
                    cells_map[c.col_id] = c.content_md or ""

            row_data = [row.label] + [cells_map.get(c.id, "") for c in cols]
            writer.writerow(row_data)

        return buf.getvalue()
