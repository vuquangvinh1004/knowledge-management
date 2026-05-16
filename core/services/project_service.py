"""Service quản lý dự án nghiên cứu (Project mode).

Business rules:
- note.project_id IS NULL  → Global note (hiển thị mọi mode).
- note.project_id IS NOT NULL → Project-only note (chỉ thuộc 1 project).
- project_note_refs → Global note được kéo vào project để tham khảo.
- Source PDF không có project scope — luôn là Global.
- Xóa project = soft-delete (is_deleted = 1). Notes project-only SET NULL → Global.
- Đóng gói project = export folder Markdown standalone.
- Search trong Project mode chỉ trong notes thuộc project (own + refs).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update

from core.services.export_service import ExportService
from core.storage.models import AppSettingRow, Note, Project, ProjectNoteRef
from core.storage.session import get_session
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()

_ACTIVE_PROJECT_KEY = "active_project_id"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectService:
    """CRUD và workflow cho Project mode."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_project(self, name: str, description: str = "") -> Project:
        """Tạo project mới với status=active."""
        name = name.strip()
        if not name:
            raise PKMError("Tên project không được để trống.")

        with get_session() as session:
            now = _utcnow()
            project = Project(
                name=name,
                description=description.strip(),
                status="active",
                is_deleted=0,
                created_at=now,
                updated_at=now,
            )
            session.add(project)
            session.flush()
            session.refresh(project)
            result = Project(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                is_deleted=project.is_deleted,
                created_at=project.created_at,
                updated_at=project.updated_at,
                closed_at=project.closed_at,
                meta_json=project.meta_json,
            )
            logger.info(f"ProjectService: created project id={project.id} name={project.name!r}")
            return result

    def get_project(self, project_id: int) -> Project:
        """Lấy project theo ID. Raise PKMError nếu không tìm thấy hoặc đã xóa."""
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")
            return project

    def list_projects(self, include_closed: bool = False) -> list[Project]:
        """Liệt kê tất cả projects chưa bị xóa mềm.

        Args:
            include_closed: Nếu True, bao gồm cả projects có status='closed'.
        """
        with get_session() as session:
            stmt = select(Project).where(Project.is_deleted == 0)
            if not include_closed:
                stmt = stmt.where(Project.status == "active")
            stmt = stmt.order_by(Project.updated_at.desc())
            return list(session.scalars(stmt))

    def rename_project(self, project_id: int, new_name: str) -> None:
        """Đổi tên project."""
        new_name = new_name.strip()
        if not new_name:
            raise PKMError("Tên project không được để trống.")

        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")
            project.name = new_name
            project.updated_at = _utcnow()
            logger.info(f"ProjectService: renamed project id={project_id} to {new_name!r}")

    def close_project(self, project_id: int) -> None:
        """Đóng project (status → closed). Project vẫn còn trong DB."""
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")
            project.status = "closed"
            project.closed_at = _utcnow()
            project.updated_at = _utcnow()
            logger.info(f"ProjectService: closed project id={project_id}")

        # Nếu project đang active thì deactivate
        if self.get_active_project_id() == project_id:
            self.deactivate_project()

    def soft_delete_project(self, project_id: int) -> None:
        """Xóa mềm project.

        Notes project-only sẽ tự động SET NULL (→ Global) theo ON DELETE SET NULL của FK.
        ProjectNoteRefs bị CASCADE DELETE.
        """
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")

            # Trước khi set is_deleted, SET NULL manually vì SQLite FK SET NULL
            # chỉ kích hoạt khi DELETE hàng thật — với soft-delete ta phải làm tay
            session.execute(
                update(Note)
                .where(Note.project_id == project_id)
                .values(project_id=None, updated_at=_utcnow())
            )
            project.is_deleted = 1
            project.updated_at = _utcnow()
            logger.info(f"ProjectService: soft-deleted project id={project_id}")

        if self.get_active_project_id() == project_id:
            self.deactivate_project()

    # ------------------------------------------------------------------
    # Activate / Deactivate
    # ------------------------------------------------------------------

    def activate_project(self, project_id: int) -> None:
        """Đặt project làm project đang active (lưu vào AppSettingRow)."""
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")

            row = session.scalars(
                select(AppSettingRow).where(AppSettingRow.setting_key == _ACTIVE_PROJECT_KEY)
            ).first()
            if row:
                row.setting_value = str(project_id)
            else:
                session.add(AppSettingRow(setting_key=_ACTIVE_PROJECT_KEY, setting_value=str(project_id)))
            logger.info(f"ProjectService: activated project id={project_id}")

    def deactivate_project(self) -> None:
        """Bỏ chọn project đang active (về Global mode)."""
        with get_session() as session:
            row = session.scalars(
                select(AppSettingRow).where(AppSettingRow.setting_key == _ACTIVE_PROJECT_KEY)
            ).first()
            if row:
                session.delete(row)
                logger.info("ProjectService: deactivated project (back to Global mode)")

    def get_active_project_id(self) -> Optional[int]:
        """Trả về ID của project đang active, hoặc None nếu đang ở Global mode."""
        with get_session() as session:
            row = session.scalars(
                select(AppSettingRow).where(AppSettingRow.setting_key == _ACTIVE_PROJECT_KEY)
            ).first()
            if row is None:
                return None
            try:
                return int(row.setting_value)
            except (ValueError, TypeError):
                logger.warning("ProjectService: active_project_id setting is corrupt, clearing.")
                session.delete(row)
                return None

    # ------------------------------------------------------------------
    # Note References (Global notes kéo vào project)
    # ------------------------------------------------------------------

    def add_note_ref(self, project_id: int, note_id: int) -> None:
        """Thêm Global note vào danh sách tham khảo của project.

        Chỉ cho phép nếu note.project_id IS NULL (đây là Global note).
        Raise PKMError nếu note đã là project-only note của project khác.
        """
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Project id={project_id} không tìm thấy.")

            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise PKMError(f"Note id={note_id} không tìm thấy.")

            if note.project_id is not None:
                raise PKMError(
                    f"Note id={note_id} là project-only note của project id={note.project_id}. "
                    "Chỉ Global notes (project_id IS NULL) mới có thể thêm vào project refs."
                )

            # Kiểm tra đã tồn tại chưa
            existing = session.get(ProjectNoteRef, (project_id, note_id))
            if existing:
                logger.debug(f"ProjectService: note_ref project={project_id} note={note_id} đã tồn tại, bỏ qua.")
                return

            ref = ProjectNoteRef(project_id=project_id, note_id=note_id, added_at=_utcnow())
            session.add(ref)
            logger.info(f"ProjectService: added note ref project={project_id} note={note_id}")

    def remove_note_ref(self, project_id: int, note_id: int) -> None:
        """Xóa Global note khỏi danh sách tham khảo của project."""
        with get_session() as session:
            ref = session.get(ProjectNoteRef, (project_id, note_id))
            if ref is None:
                logger.warning(f"ProjectService: note_ref project={project_id} note={note_id} không tìm thấy.")
                return
            session.delete(ref)
            logger.info(f"ProjectService: removed note ref project={project_id} note={note_id}")

    def list_note_refs(self, project_id: int) -> list[Note]:
        """Trả danh sách Global notes đang được ref vào project."""
        with get_session() as session:
            stmt = (
                select(Note)
                .join(ProjectNoteRef, ProjectNoteRef.note_id == Note.id)
                .where(
                    ProjectNoteRef.project_id == project_id,
                    Note.is_deleted == 0,
                )
                .order_by(Note.title)
            )
            return list(session.scalars(stmt))

    # ------------------------------------------------------------------
    # Query notes thuộc project (own + refs)
    # ------------------------------------------------------------------

    def get_project_notes(self, project_id: int) -> dict[str, list[Note]]:
        """Trả toàn bộ notes liên quan đến project.

        Returns:
            {
                "own": [Note, ...],   # notes có project_id = project_id
                "refs": [Note, ...],  # Global notes được ref vào project
            }
        """
        with get_session() as session:
            own_stmt = (
                select(Note)
                .where(Note.project_id == project_id, Note.is_deleted == 0)
                .order_by(Note.updated_at.desc())
            )
            own = list(session.scalars(own_stmt))

            ref_stmt = (
                select(Note)
                .join(ProjectNoteRef, ProjectNoteRef.note_id == Note.id)
                .where(
                    ProjectNoteRef.project_id == project_id,
                    Note.is_deleted == 0,
                )
                .order_by(Note.title)
            )
            refs = list(session.scalars(ref_stmt))

        return {"own": own, "refs": refs}

    def get_project_note_ids(self, project_id: int) -> set[int]:
        """Trả set tất cả note IDs thuộc project (own + refs) — dùng để filter search."""
        result = self.get_project_notes(project_id)
        ids: set[int] = set()
        for note in result["own"]:
            ids.add(note.id)
        for note in result["refs"]:
            ids.add(note.id)
        return ids

    # ------------------------------------------------------------------
    # Export bundle
    # ------------------------------------------------------------------

    def export_project_bundle(self, project_id: int, output_dir: Path) -> Path:
        """Đóng gói project thành folder Markdown standalone.

        Delegates qua ExportService để tập trung hóa logic export.
        """
        bundle_dir = ExportService(output_dir).export_project_bundle(project_id)
        logger.info(f"ProjectService: exported project id={project_id} → {bundle_dir}")
        return bundle_dir
