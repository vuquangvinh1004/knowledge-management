"""Service quản lý extracts (đoạn nội dung trích xuất từ PDF).

Business rules:
- Extract phải có source_id và source_anchor hợp lệ.
- content_md không được NULL hoặc rỗng khi commit.
- Table extract phải được confirm trước khi gọi commit_extract.
- Không tạo extract mồ côi (thiếu source_id).
"""
from __future__ import annotations

from datetime import datetime, timezone

from core.storage.models import Extract
from core.storage.session import get_session
from core.utils.constants import EXTRACT_TYPES
from core.utils.exceptions import ExtractAnchorMissingError, ExtractOrphanError, PKMError
from core.utils.helpers import parse_source_anchor
from core.utils.logger import get_logger

logger = get_logger()


class ExtractService:
    """Commit và quản lý lifecycle cho Extract."""

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(self, extract_id: int) -> Extract:
        """
        Raises:
            PKMError: Nếu không tìm thấy.
        """
        with get_session() as session:
            extract = session.get(Extract, extract_id)
            if extract is None:
                raise PKMError(f"Không tìm thấy extract id={extract_id}.")
            session.expunge(extract)
            return extract

    def list_by_source(self, source_id: int) -> list[Extract]:
        """Lấy tất cả extracts của một source, theo thứ tự page_no."""
        with get_session() as session:
            extracts = (
                session.query(Extract)
                .filter(Extract.source_id == source_id)
                .order_by(Extract.page_no, Extract.created_at)
                .all()
            )
            for e in extracts:
                session.expunge(e)
            return extracts

    def list_by_note(self, note_id: int) -> list[Extract]:
        """Lấy tất cả extracts đã được gắn vào một note."""
        with get_session() as session:
            extracts = (
                session.query(Extract)
                .filter(Extract.note_id == note_id)
                .order_by(Extract.page_no, Extract.created_at)
                .all()
            )
            for e in extracts:
                session.expunge(e)
            return extracts

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def commit_extract(
        self,
        source_id: int,
        page_no: int,
        extract_type: str,
        source_anchor: str,
        content_md: str,
        note_id: int | None = None,
        extra_json: str | None = None,
    ) -> Extract:
        """
        Commit một extract vào DB sau khi đã validate.

        Args:
            source_id: ID của source (bắt buộc).
            page_no: Số trang (bắt buộc).
            extract_type: 'text' | 'table' | 'image'.
            source_anchor: Anchor dạng source://<id>?page=<n>&rect=...
            content_md: Nội dung đã convert sang markdown (không được rỗng).
            note_id: ID note để gắn extract vào (tùy chọn).
            extra_json: Dữ liệu phụ (metadata bảng, bounding box...).

        Returns:
            Extract đã lưu.

        Raises:
            ExtractOrphanError: Nếu thiếu source_id.
            ExtractAnchorMissingError: Nếu anchor không hợp lệ.
            PKMError: Nếu extract_type không hợp lệ hoặc content_md rỗng.
        """
        if not source_id:
            raise ExtractOrphanError("source_id là bắt buộc — không tạo extract mồ côi.")

        if extract_type not in EXTRACT_TYPES:
            raise PKMError(f"extract_type không hợp lệ: {extract_type!r}. Phải là {EXTRACT_TYPES}.")

        if not content_md or not content_md.strip():
            raise PKMError("content_md không được rỗng khi commit extract.")

        # Validate anchor tối thiểu
        try:
            parsed = parse_source_anchor(source_anchor)
        except ValueError as exc:
            raise ExtractAnchorMissingError(
                f"source_anchor không hợp lệ: {source_anchor!r} — {exc}"
            ) from exc

        if str(parsed["source_id"]) != str(source_id):
            raise ExtractAnchorMissingError(
                f"source_anchor source_id={parsed['source_id']!r} không khớp với source_id={source_id}."
            )

        now = datetime.now(timezone.utc)
        extract = Extract(
            source_id=source_id,
            note_id=note_id,
            page_no=page_no,
            extract_type=extract_type,
            source_anchor=source_anchor,
            content_md=content_md,
            extra_json=extra_json,
            created_at=now,
            updated_at=now,
        )
        with get_session() as session:
            session.add(extract)
            session.flush()
            session.expunge(extract)

        logger.info(
            f"Commit extract id={extract.id} type={extract_type!r} "
            f"source={source_id} page={page_no}"
        )
        return extract

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def attach_to_note(self, extract_id: int, note_id: int) -> None:
        """Gắn extract vào note (sau khi note được tạo)."""
        with get_session() as session:
            extract = session.get(Extract, extract_id)
            if extract is None:
                raise PKMError(f"Không tìm thấy extract id={extract_id}.")
            extract.note_id = note_id
            extract.updated_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_extract(self, extract_id: int) -> None:
        """Xóa extract khỏi DB."""
        with get_session() as session:
            extract = session.get(Extract, extract_id)
            if extract is None:
                raise PKMError(f"Không tìm thấy extract id={extract_id}.")
            session.delete(extract)
        logger.info(f"Xóa extract id={extract_id}")
