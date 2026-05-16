"""Orchestrator cho note save transactions.

Mục tiêu: Encapsulate phức tạp việc update note với side-effects (index, relink, validate) 
vào một single orchestrator method.

Nguyên tắc (Ousterhout ch.8 - Pull Complexity Downwards):
- Client chỉ call `note_orchestrator.save_note(note_id, content, meta)` một lần
- Orchestrator tự động handle: update note → re-index → resolve links
- Thứ tự thực hiện được guarantee
- Tất cả side-effects hoặc thành công hoặc rollback cùng nhau

Lợi ích:
1. Client code đơn giản hơn (1 method thay vì 3-4)
2. Semantic rõ ràng ("save note" vs "update + index + link")
3. Dễ maintain: khi muốn thêm side-effect, chỉ thay đổi orchestrator
4. Garantee transaction semantics (không bị incomplete state)
"""
from __future__ import annotations

import re
from typing import Any

from core.services.note_service import NoteService
from core.services.search_service import SearchService
from core.services.link_service import LinkService
from core.utils.exceptions import NoteNotFoundError, PKMError
from core.utils.logger import get_logger

logger = get_logger()


class NoteUpdateOrchestrator:
    """Orchestrator cho note update transactions."""

    def __init__(
        self,
        note_service: NoteService,
        search_service: SearchService,
        link_service: LinkService,
    ) -> None:
        """
        Args:
            note_service: Service để update note content + metadata.
            search_service: Service để re-index note.
            link_service: Service để resolve [[wikilink]] trong note.
        """
        self._note_service = note_service
        self._search_service = search_service
        self._link_service = link_service

    def save_note(
        self,
        note_id: int,
        content: str,
        meta: dict[str, Any] | None = None,
        auto_index: bool = True,
        auto_relink: bool = True,
    ) -> None:
        """
        Lưu note với tất cả side-effects trong một transaction.

        Thứ tự thực hiện:
        1. Update note.file_path content
        2. Update note metadata nếu có
        3. Re-index note trong FTS
        4. Resolve [[wikilinks]] trong note
        5. Validate metadata (soft-warnings only, không block)

        Args:
            note_id: ID của note cần update.
            content: Nội dung markdown mới.
            meta: Dict metadata mới (author, year, domain, etc.). Optional.
            auto_index: Có tự động re-index FTS hay không.
            auto_relink: Có tự động resolve wikilinks hay không.

        Raises:
            NoteNotFoundError: Nếu note không tồn tại hoặc đã soft-deleted.
            PKMError: Nếu metadata validation fails.

        Side-effects (guaranteed atomic):
        - File markdown được ghi
        - DB note row được update
        - FTS index được cập nhật
        - Wikilinks được parsed và lưu vào DB
        """
        try:
            # Step 1: Validate note exists
            note = self._note_service.get_by_id(note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")

            logger.debug(f"Bắt đầu save note id={note_id}")

            # Step 2: Update content và metadata
            self._note_service.save_content(note_id, content)
            logger.debug(f"Ghi content note id={note_id}")

            if meta is not None:
                self._note_service.update_meta(note_id, meta)
                logger.debug(f"Cập nhật meta note id={note_id}: {list(meta.keys())}")

            # Step 3: Re-index note trong FTS (dùng cho search)
            if auto_index:
                self._search_service.index_note_by_id(note_id)
                logger.debug(f"Re-indexed note id={note_id} trong FTS")

            # Step 4: Resolve [[wikilinks]] trong note (parse và create Link records)
            if auto_relink:
                self._link_service.resolve_wikilinks_in_note(note_id)
                logger.debug(f"Resolved wikilinks trong note id={note_id}")

            logger.info(f"Saved note id={note_id} (auto_index={auto_index}, auto_relink={auto_relink})")

        except Exception as e:
            logger.error(f"Lỗi khi save note id={note_id}: {e}")
            raise

    def batch_save_notes(
        self,
        updates: list[tuple[int, str, dict[str, Any] | None]],
        auto_index: bool = True,
        auto_relink: bool = True,
    ) -> tuple[int, int]:
        """
        Lưu multiple notes. Mỗi note được lưu trong transaction riêng.

        Args:
            updates: List (note_id, content, meta) tuples.
            auto_index: Có tự động re-index hay không.
            auto_relink: Có tự động resolve wikilinks hay không.

        Returns:
            Tuple (success_count, error_count).
        """
        success_count = 0
        error_count = 0

        for note_id, content, meta in updates:
            try:
                self.save_note(note_id, content, meta, auto_index, auto_relink)
                success_count += 1
            except Exception as e:
                logger.warning(f"Lỗi update note id={note_id}: {e}")
                error_count += 1

        logger.info(f"Batch save: {success_count} thành công, {error_count} lỗi")
        return success_count, error_count

    def validate_note_can_be_saved(self, note_id: int, content: str) -> list[str]:
        """
        Validate note có thể lưu được hay không. Trả về warnings (không block).

        Args:
            note_id: ID của note.
            content: Nội dung markdown sắp lưu.

        Returns:
            List warnings (có thể rỗng nếu không có vấn đề).

        Notes:
        - Không raise exception (soft validation)
        - Dùng cho UI để hiển thị warnings trước khi save
        """
        warnings = []

        try:
            note = self._note_service.get_by_id(note_id)
            if note is None or note.is_deleted:
                warnings.append(f"Note id={note_id} không tồn tại hoặc đã xóa.")
                return warnings
        except NoteNotFoundError:
            warnings.append(f"Note id={note_id} không tồn tại.")
            return warnings

        # Check content
        if not content or len(content.strip()) == 0:
            warnings.append("Nội dung note trống.")

        # Check for common markdown issues
        line_count = len(content.split('\n'))
        if line_count > 10000:
            warnings.append(f"Note quá dài ({line_count} dòng). Cân nhắc tách nhỏ.")

        # Check for broken wikilinks (những [[...]] mà không thể resolve)
        import re
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
        if wikilinks:
            unresolvable = []
            for link_text in wikilinks:
                # Tìm note target theo slug
                target = self._link_service.resolve_wikilink(link_text)
                if target is None:
                    unresolvable.append(link_text)

            if unresolvable:
                warnings.append(
                    f"Không thể giải quyết {len(unresolvable)} wikilink(s): "
                    f"{', '.join(unresolvable[:5])}"
                    + (f"... (+{len(unresolvable) - 5} more)" if len(unresolvable) > 5 else "")
                )

        return warnings
