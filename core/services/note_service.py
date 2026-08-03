"""Service quản lý ghi chú Markdown.

Business rules:
- Mỗi source chỉ có đúng một source_note.
- slug phải unique và ổn định (không đổi sau khi tạo).
- Markdown lưu vào file trên disk và path lưu vào DB.
- Soft-delete trước khi xóa cứng nếu có link tới note.
"""
from __future__ import annotations

from pathlib import Path

from core.storage.models import Note
from core.services.note_crud import (
    build_template as crud_build_template,
    create_note as crud_create_note,
    get_by_id as crud_get_by_id,
    get_by_slug as crud_get_by_slug,
    get_source_note as crud_get_source_note,
    list_all as crud_list_all,
    list_by_project as crud_list_by_project,
    list_global as crud_list_global,
    read_content as crud_read_content,
    save_content as crud_save_content,
    title_warnings as crud_title_warnings,
    update_summary as crud_update_summary,
    update_title as crud_update_title,
)
from core.services.note_lifecycle import (
    audit_missing_source_note_files as lifecycle_audit_missing_source_note_files,
    cleanup_unused_notes as lifecycle_cleanup_unused_notes,
    get_note_delete_impact as lifecycle_get_note_delete_impact,
    get_unused_note_candidates as lifecycle_get_unused_note_candidates,
    hard_delete as lifecycle_hard_delete,
    list_notes_for_management as lifecycle_list_notes_for_management,
    mark_hard_deleted as lifecycle_mark_hard_deleted,
    normalize_source_note_titles as lifecycle_normalize_source_note_titles,
    refresh_wikilink_note_catalog as lifecycle_refresh_wikilink_note_catalog,
    restore as lifecycle_restore,
    soft_delete as lifecycle_soft_delete,
)
from core.services.note_metadata import get_meta as metadata_get_meta, update_meta as metadata_update_meta


class NoteService:
    """CRUD và lifecycle cho Note."""

    def __init__(self, notes_dir: Path) -> None:
        """
        Args:
            notes_dir: Thư mục gốc lưu file markdown note.
        """
        self._notes_dir = Path(notes_dir)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(self, note_id: int) -> Note:
        return crud_get_by_id(note_id)

    def get_by_slug(self, slug: str) -> Note:
        return crud_get_by_slug(slug)

    def get_source_note(self, source_id: int) -> Note | None:
        """Lấy source_note liên kết với source (1:1). Trả None nếu chưa có."""
        return crud_get_source_note(source_id)

    def list_all(self, note_type: str | None = None, include_deleted: bool = False) -> list[Note]:
        """Lấy danh sách notes, tùy chọn lọc theo note_type."""
        return crud_list_all(note_type=note_type, include_deleted=include_deleted)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    def build_template(note_type: str, title: str) -> str:
        """Public wrapper cho template markdown theo note_type."""
        return crud_build_template(note_type, title)

    @staticmethod
    def title_warnings(note_type: str, title: str) -> list[str]:
        """Public wrapper cho soft-warning chất lượng title."""
        return crud_title_warnings(note_type, title)

    def create_note(
        self,
        title: str,
        note_type: str,
        source_id: int | None = None,
        initial_content: str = "",
        project_id: int | None = None,
    ) -> Note:
        """
        Tạo note mới và lưu file markdown tương ứng.

        Args:
            title: Tiêu đề note.
            note_type: Phải thuộc NOTE_TYPES.
            source_id: Gắn với source (bắt buộc nếu note_type == 'source_note').
            initial_content: Nội dung markdown khởi đầu.
            project_id: ID project nếu đây là project-only note. None = Global note.

        Returns:
            Note đã tạo.

        Raises:
            PKMError: Nếu note_type không hợp lệ hoặc source_note đã tồn tại.
        """
        return crud_create_note(
            self._notes_dir,
            title=title,
            note_type=note_type,
            source_id=source_id,
            initial_content=initial_content,
            project_id=project_id,
        )

    def list_by_project(self, project_id: int) -> list[Note]:
        """Trả danh sách project-only notes có project_id = project_id."""
        return crud_list_by_project(project_id)

    def list_global(self, note_type: str | None = None) -> list[Note]:
        """Trả danh sách Global notes (project_id IS NULL)."""
        return crud_list_global(note_type=note_type)

    def list_notes_for_management(self, include_deleted: bool = False) -> list[dict]:
        """Liệt kê note cho màn hình quản lý ghi chú."""
        return lifecycle_list_notes_for_management(include_deleted=include_deleted)

    def get_note_delete_impact(self, note_id: int) -> dict:
        """Phân tích ảnh hưởng nếu soft-delete note."""
        return lifecycle_get_note_delete_impact(note_id)

    def audit_missing_source_note_files(self) -> list[dict]:
        """Audit read-only các source_note có record DB nhưng thiếu file markdown."""
        return lifecycle_audit_missing_source_note_files()

    # ------------------------------------------------------------------
    # Read/Write file content
    # ------------------------------------------------------------------

    def read_content(self, note_id: int) -> str:
        """Đọc nội dung markdown của note từ file trên disk."""
        return crud_read_content(note_id)

    def save_content(self, note_id: int, content: str) -> None:
        """Ghi nội dung markdown vào file và cập nhật updated_at trong DB."""
        crud_save_content(note_id, content)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_title(self, note_id: int, new_title: str) -> Note:
        """Cập nhật tiêu đề note (slug KHÔNG thay đổi để giữ liên kết ổn định)."""
        return crud_update_title(note_id, new_title)

    def update_summary(self, note_id: int, summary: str) -> None:
        """Cập nhật summary của note."""
        crud_update_summary(note_id, summary)

    def get_meta(self, note_id: int) -> dict:
        """Lấy metadata JSON của note dưới dạng dict."""
        return metadata_get_meta(note_id)

    def update_meta(self, note_id: int, meta: dict) -> None:
        """Cập nhật meta_json của note với validation theo note_type."""
        metadata_update_meta(note_id, meta)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def soft_delete(self, note_id: int) -> None:
        """Soft-delete note (xóa tạm, giữ file và record DB)."""
        lifecycle_soft_delete(note_id)

    def restore(self, note_id: int) -> None:
        """Khôi phục note từ trạng thái xóa tạm (is_deleted = 1)."""
        lifecycle_restore(note_id)

    def mark_hard_deleted(self, note_id: int, delete_file: bool = True) -> None:
        """Đánh dấu note ở trạng thái xóa cứng (is_deleted = 2), chưa purge record DB.

        Trạng thái này dùng cho workflow 2 bước:
        - Bước 1: xóa cứng logic (chuyển đỏ trong UI)
        - Bước 2: xóa hoàn toàn khỏi DB (hard_delete)
        """
        lifecycle_mark_hard_deleted(note_id, delete_file=delete_file)

    def hard_delete(self, note_id: int, delete_file: bool = True) -> None:
        """
        Xóa cứng note khỏi DB.

        Args:
            delete_file: Nếu True, xóa cả file markdown trên disk.
        """
        lifecycle_hard_delete(note_id, delete_file=delete_file)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def normalize_source_note_titles(self) -> int:
        """Chuẩn hóa toàn bộ title `source_note` theo metadata hiện có (idempotent)."""
        return lifecycle_normalize_source_note_titles(self._notes_dir)

    def refresh_wikilink_note_catalog(self) -> dict[str, int]:
        """Làm mới catalog note cho wikilink suggestions.

        - Soft-delete note có file_path không còn tồn tại.
        - Dọn link trỏ vào note đã bị soft-delete.
        - Dọn orphan auto-stub notes (không còn liên kết và nội dung chỉ là skeleton `# title`).
        """
        return lifecycle_refresh_wikilink_note_catalog(self._notes_dir)

    def get_unused_note_candidates(self) -> list[dict]:
        """Liệt kê candidate note không còn dùng để người dùng preview trước khi dọn."""
        return lifecycle_get_unused_note_candidates()

    def cleanup_unused_notes(self, note_ids: set[int]) -> dict[str, int]:
        """Soft-delete các note người dùng đã chọn và dọn stale links liên quan."""
        return lifecycle_cleanup_unused_notes(note_ids)
