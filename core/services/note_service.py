"""Service quản lý ghi chú Markdown.

Business rules:
- Mỗi source chỉ có đúng một source_note.
- slug phải unique và ổn định (không đổi sau khi tạo).
- Markdown lưu vào file trên disk và path lưu vào DB.
- Soft-delete trước khi xóa cứng nếu có link tới note.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from sqlalchemy.exc import IntegrityError

from core.storage.models import (
    Asset,
    Board,
    BoardCell,
    Extract,
    Link,
    Note,
    Project,
    ProjectNoteRef,
    Source,
)
from core.storage.session import get_session
from core.storage.query_optimization import (
    get_note_delete_impact as query_get_note_delete_impact,
    list_notes_for_management_efficient,
)
from core.services.note_templates import build_note_template, get_note_title_warnings
from core.utils.constants import NOTE_TYPES
from core.utils.exceptions import NoteNotFoundError, PKMError
from core.utils.helpers import slugify
from core.utils.logger import get_logger

logger = get_logger()


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
        """
        Raises:
            NoteNotFoundError: Nếu không tìm thấy hoặc đã xóa.
        """
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            session.expunge(note)
            return note

    def get_by_slug(self, slug: str) -> Note:
        """
        Raises:
            NoteNotFoundError: Nếu không tìm thấy.
        """
        with get_session() as session:
            note = (
                session.query(Note)
                .filter(Note.slug == slug, Note.is_deleted == 0)
                .first()
            )
            if note is None:
                raise NoteNotFoundError(f"Không tìm thấy note slug={slug!r}.")
            session.expunge(note)
            return note

    def get_source_note(self, source_id: int) -> Note | None:
        """Lấy source_note liên kết với source (1:1). Trả None nếu chưa có."""
        with get_session() as session:
            note = (
                session.query(Note)
                .filter(
                    Note.source_id == source_id,
                    Note.note_type == "source_note",
                    Note.is_deleted == 0,
                )
                .first()
            )
            if note:
                session.expunge(note)
            return note

    def list_all(self, note_type: str | None = None, include_deleted: bool = False) -> list[Note]:
        """Lấy danh sách notes, tùy chọn lọc theo note_type."""
        with get_session() as session:
            query = session.query(Note)
            if not include_deleted:
                query = query.filter(Note.is_deleted == 0)
            if note_type:
                query = query.filter(Note.note_type == note_type)
            notes = query.order_by(Note.updated_at.desc()).all()
            for n in notes:
                session.expunge(n)
            return notes

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    def build_template(note_type: str, title: str) -> str:
        """Public wrapper cho template markdown theo note_type."""
        return build_note_template(note_type, title)

    @staticmethod
    def title_warnings(note_type: str, title: str) -> list[str]:
        """Public wrapper cho soft-warning chất lượng title."""
        return get_note_title_warnings(note_type, title)

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
        if note_type not in NOTE_TYPES:
            raise PKMError(f"note_type không hợp lệ: {note_type!r}. Phải là một trong {NOTE_TYPES}.")

        if note_type == "source_note" and source_id is None:
            raise PKMError("`source_note` bắt buộc phải có source_id.")

        if note_type == "source_note" and source_id is not None:
            existing = self.get_source_note(source_id)
            if existing:
                raise PKMError(
                    f"Source id={source_id} đã có source_note id={existing.id}. "
                    "Mỗi source chỉ được có một source_note."
                )

        slug = self._unique_slug(title)
        note_file = self._notes_dir / f"{slug}.md"
        resolved_content = initial_content if initial_content != "" else build_note_template(note_type, title)

        # Ghi file markdown
        self._notes_dir.mkdir(parents=True, exist_ok=True)
        note_file.write_text(resolved_content, encoding="utf-8")

        now = datetime.now(timezone.utc)
        note = Note(
            source_id=source_id,
            title=title,
            slug=slug,
            note_type=note_type,
            file_path=str(note_file),
            project_id=project_id,
            created_at=now,
            updated_at=now,
        )
        try:
            with get_session() as session:
                session.add(note)
                session.flush()
                session.expunge(note)
        except IntegrityError as exc:
            # slug collision không lường trước
            note_file.unlink(missing_ok=True)
            raise PKMError(f"Không thể tạo note (slug trùng): {exc}") from exc

        scope_label = f"project_id={project_id}" if project_id is not None else "global"
        logger.info(f"Tạo note id={note.id} slug={slug!r} type={note_type!r} scope={scope_label}")
        return note

    def list_by_project(self, project_id: int) -> list[Note]:
        """Trả danh sách project-only notes có project_id = project_id."""
        with get_session() as session:
            notes = (
                session.query(Note)
                .filter(Note.project_id == project_id, Note.is_deleted == 0)
                .order_by(Note.updated_at.desc())
                .all()
            )
            for n in notes:
                session.expunge(n)
            return notes

    def list_global(self, note_type: str | None = None) -> list[Note]:
        """Trả danh sách Global notes (project_id IS NULL)."""
        with get_session() as session:
            query = session.query(Note).filter(Note.project_id.is_(None), Note.is_deleted == 0)
            if note_type:
                query = query.filter(Note.note_type == note_type)
            notes = query.order_by(Note.updated_at.desc()).all()
            for n in notes:
                session.expunge(n)
            return notes

    def list_notes_for_management(self, include_deleted: bool = False) -> list[dict]:
        """Liệt kê note cho màn hình quản lý ghi chú.

        Trả về dữ liệu đã gắn scope label (Global / Project) để UI hiển thị.
        
        Optimized: Dùng JOIN thay vì N+1 queries để fetch project names.
        """
        with get_session() as session:
            items = list_notes_for_management_efficient(session, include_deleted=include_deleted)
            # Convert NoteManagementItem DTO back to dict format for backward compatibility
            return [
                {
                    "note_id": item.note_id,
                    "title": item.title,
                    "note_type": item.note_type,
                    "source_id": item.source_id,
                    "project_id": item.project_id,
                    "scope_label": item.scope_label,
                    "file_path": item.file_path,
                    "is_deleted": item.is_deleted,
                    "updated_at": item.updated_at,
                }
                for item in items
            ]

    def get_note_delete_impact(self, note_id: int) -> dict:
        """Phân tích ảnh hưởng nếu soft-delete note.

        Dùng để hiển thị cảnh báo rõ ràng trước khi người dùng xác nhận xóa.
        
        Optimized: Dùng aggregation queries thay vì separate COUNT queries.
        """
        try:
            with get_session() as session:
                impact = query_get_note_delete_impact(session, note_id)
                # Convert DTO back to dict format for backward compatibility
                return {
                    "note_id": impact.note_id,
                    "title": impact.title,
                    "note_type": impact.note_type,
                    "is_source_note": impact.is_source_note,
                    "source_id": impact.source_id,
                    "project_id": impact.project_id,
                    "incoming_links": impact.incoming_links_count,
                    "outgoing_links": impact.outgoing_links_count,
                    "extract_refs": impact.extract_refs_count,
                    "asset_refs": impact.asset_refs_count,
                    "board_cell_refs": impact.board_cell_refs_count,
                    "linked_boards": impact.linked_boards_count,
                    "project_refs": impact.project_refs_count,
                }
        except Exception as e:
            if "Không tìm thấy" in str(e):
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            raise

    def audit_missing_source_note_files(self) -> list[dict]:
        """Audit read-only các source_note có record DB nhưng thiếu file markdown."""
        with get_session() as session:
            notes = (
                session.query(Note)
                .filter(
                    Note.note_type == "source_note",
                    Note.is_deleted == 0,
                )
                .all()
            )

            source_ids = {int(n.source_id) for n in notes if n.source_id is not None}
            source_map: dict[int, Source] = {}
            if source_ids:
                for src in session.query(Source).filter(Source.id.in_(source_ids)).all():
                    if src.id is not None:
                        source_map[int(src.id)] = src

            issues: list[dict] = []
            for note in notes:
                file_path = Path(str(note.file_path or ""))
                if file_path.exists():
                    continue

                src_id = int(note.source_id) if note.source_id is not None else None
                src = source_map.get(src_id) if src_id is not None else None
                issues.append(
                    {
                        "note_id": int(note.id),
                        "source_id": src_id,
                        "source_code": str(getattr(src, "source_code", "") or ""),
                        "source_title": str(getattr(src, "title", "") or ""),
                        "note_title": str(note.title or ""),
                        "file_path": str(note.file_path or ""),
                    }
                )

            issues.sort(key=lambda x: (x.get("source_id") or 0, x.get("note_id") or 0))
            return issues

    # ------------------------------------------------------------------
    # Read/Write file content
    # ------------------------------------------------------------------

    def read_content(self, note_id: int) -> str:
        """Đọc nội dung markdown của note từ file trên disk."""
        note = self.get_by_id(note_id)
        return Path(note.file_path).read_text(encoding="utf-8")

    def save_content(self, note_id: int, content: str) -> None:
        """Ghi nội dung markdown vào file và cập nhật updated_at trong DB."""
        note = self.get_by_id(note_id)
        Path(note.file_path).write_text(content, encoding="utf-8")
        with get_session() as session:
            db_note = session.get(Note, note_id)
            if db_note:
                db_note.updated_at = datetime.now(timezone.utc)
        logger.debug(f"Lưu nội dung note id={note_id}")

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_title(self, note_id: int, new_title: str) -> Note:
        """Cập nhật tiêu đề note (slug KHÔNG thay đổi để giữ liên kết ổn định)."""
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            note.title = new_title
            note.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(note)
        logger.info(f"Cập nhật title note id={note_id} → {new_title!r}")
        return note

    def update_summary(self, note_id: int, summary: str) -> None:
        """Cập nhật summary của note."""
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            note.summary = summary
            note.updated_at = datetime.now(timezone.utc)

    def get_meta(self, note_id: int) -> dict:
        """Lấy metadata JSON của note dưới dạng dict."""
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            raw = note.meta_json or "{}"
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def update_meta(self, note_id: int, meta: dict) -> None:
        """Cập nhật meta_json của note với validation theo note_type."""
        if not isinstance(meta, dict):
            raise PKMError("meta phải là dict JSON hợp lệ.")

        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None or note.is_deleted:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")

            validated = self._validate_meta_for_note_type(str(note.note_type), meta)
            note.meta_json = json.dumps(validated, ensure_ascii=False)
            note.updated_at = datetime.now(timezone.utc)

    def _validate_meta_for_note_type(self, note_type: str, meta: dict) -> dict:
        """Validate meta theo từng note_type và trả về dict đã chuẩn hóa."""
        clean = {str(k): v for k, v in meta.items()}

        if note_type == "source_note":
            allowed = {"author", "year", "source_type", "publication", "topic"}
            out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
            if "year" in out:
                year_str = str(out["year"]).strip()
                if not (year_str.isdigit() and len(year_str) == 4):
                    raise PKMError("Meta `year` của source_note phải là 4 chữ số.")
                out["year"] = year_str
            if "author" in out:
                out["author"] = str(out["author"]).strip()
            return out

        if note_type == "concept_note":
            allowed = {"domain", "keywords"}
            out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
            if "keywords" in out and isinstance(out["keywords"], str):
                out["keywords"] = [s.strip() for s in out["keywords"].split(",") if s.strip()]
            return out

        if note_type == "board_note":
            allowed = {"board_type", "scope", "source_count"}
            out = {k: clean.get(k) for k in allowed if clean.get(k) not in (None, "")}
            if "source_count" in out:
                try:
                    out["source_count"] = int(out["source_count"])
                except Exception as exc:
                    raise PKMError("Meta `source_count` của board_note phải là số nguyên.") from exc
            return out

        # synthesis_note hoặc loại khác: giữ metadata text đơn giản
        return {k: v for k, v in clean.items() if v not in (None, "")}

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def soft_delete(self, note_id: int) -> None:
        """Soft-delete note (giữ file và record DB)."""
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            note.is_deleted = 1
            note.updated_at = datetime.now(timezone.utc)
        logger.info(f"Soft-delete note id={note_id}")

    def hard_delete(self, note_id: int, delete_file: bool = True) -> None:
        """
        Xóa cứng note khỏi DB.

        Args:
            delete_file: Nếu True, xóa cả file markdown trên disk.
        """
        with get_session() as session:
            note = session.get(Note, note_id)
            if note is None:
                raise NoteNotFoundError(f"Không tìm thấy note id={note_id}.")
            file_path = Path(note.file_path)
            session.delete(note)

        if delete_file and file_path.exists():
            file_path.unlink()
        logger.info(f"Hard-delete note id={note_id}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _unique_slug(self, title: str) -> str:
        """Sinh slug unique từ title, thêm suffix -2, -3... nếu cần."""
        base = slugify(title) or "note"
        slug = base
        counter = 2
        while True:
            with get_session() as session:
                existing = session.query(Note).filter(Note.slug == slug).first()
            if existing is None:
                return slug
            slug = f"{base}-{counter}"
            counter += 1

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def normalize_source_note_titles(self) -> int:
        """Chuẩn hóa toàn bộ title `source_note` theo metadata hiện có (idempotent)."""
        from core.services.source_service import SourceService

        updated_count = 0
        with get_session() as session:
            source_rows = session.query(Source).all()
            source_map = {int(s.id): s for s in source_rows if s.id is not None}

            notes = (
                session.query(Note)
                .filter(Note.note_type == "source_note", Note.is_deleted == 0)
                .all()
            )

            for note in notes:
                if note.source_id is None:
                    continue
                source = source_map.get(int(note.source_id))
                if source is None:
                    continue

                meta = {}
                if note.meta_json:
                    try:
                        parsed = json.loads(note.meta_json)
                        if isinstance(parsed, dict):
                            meta = parsed
                    except Exception:
                        meta = {}

                effective_authors = str(meta.get("author") or source.authors or "").strip() or None
                effective_year = str(meta.get("year") or source.year or "").strip() or None

                new_title = SourceService.build_source_note_title(
                    authors=effective_authors,
                    year=effective_year,
                    fallback_filename=note.title,
                )
                if new_title != note.title:
                    note.title = new_title
                    note.updated_at = datetime.now(timezone.utc)
                    updated_count += 1

        return updated_count

    def refresh_wikilink_note_catalog(self) -> dict[str, int]:
        """Làm mới catalog note cho wikilink suggestions.

        - Soft-delete note có file_path không còn tồn tại.
        - Dọn link trỏ vào note đã bị soft-delete.
        - Dọn orphan auto-stub notes (không còn liên kết và nội dung chỉ là skeleton `# title`).
        """
        soft_deleted_missing_file = 0
        removed_stale_links = 0
        removed_orphan_stub_notes = 0

        with get_session() as session:
            active_notes = session.query(Note).filter(Note.is_deleted == 0).all()

            link_rows = session.query(Link.from_note_id, Link.to_note_id).all()
            incoming_count: dict[int, int] = {}
            outgoing_count: dict[int, int] = {}
            for from_id, to_id in link_rows:
                f_id = int(from_id)
                t_id = int(to_id)
                outgoing_count[f_id] = outgoing_count.get(f_id, 0) + 1
                incoming_count[t_id] = incoming_count.get(t_id, 0) + 1

            for note in active_notes:
                file_path = Path(str(note.file_path or ""))
                if note.file_path and not file_path.exists():
                    note.is_deleted = 1
                    note.updated_at = datetime.now(timezone.utc)
                    soft_deleted_missing_file += 1
                    continue

                note_id = int(note.id)
                note_type = str(note.note_type)
                if note_type in {"concept_note", "synthesis_note", "board_note"}:
                    has_incoming = incoming_count.get(note_id, 0) > 0
                    has_outgoing = outgoing_count.get(note_id, 0) > 0
                    if not has_incoming and not has_outgoing and self._is_auto_stub_note(note):
                        note.is_deleted = 1
                        note.updated_at = datetime.now(timezone.utc)
                        removed_orphan_stub_notes += 1

            stale_note_ids = {
                int(n.id)
                for n in session.query(Note).filter(Note.is_deleted == 1).all()
                if n.id is not None
            }
            if stale_note_ids:
                stale_links = session.query(Link).filter(
                    (Link.from_note_id.in_(stale_note_ids)) | (Link.to_note_id.in_(stale_note_ids))
                ).all()
                for lnk in stale_links:
                    session.delete(lnk)
                    removed_stale_links += 1

        return {
            "soft_deleted_missing_file": soft_deleted_missing_file,
            "removed_stale_links": removed_stale_links,
            "removed_orphan_stub_notes": removed_orphan_stub_notes,
        }

    def get_unused_note_candidates(self) -> list[dict]:
        """Liệt kê candidate note không còn dùng để người dùng preview trước khi dọn."""
        candidates: list[dict] = []

        with get_session() as session:
            active_notes = session.query(Note).filter(Note.is_deleted == 0).all()

            link_rows = session.query(Link.from_note_id, Link.to_note_id).all()
            incoming_count: dict[int, int] = {}
            outgoing_count: dict[int, int] = {}
            for from_id, to_id in link_rows:
                f_id = int(from_id)
                t_id = int(to_id)
                outgoing_count[f_id] = outgoing_count.get(f_id, 0) + 1
                incoming_count[t_id] = incoming_count.get(t_id, 0) + 1

            for note in active_notes:
                note_id = int(note.id)
                note_type = str(note.note_type)
                title = str(note.title or "")
                file_path_str = str(note.file_path or "")
                file_path = Path(file_path_str)

                if not file_path.exists():
                    candidates.append(
                        {
                            "note_id": note_id,
                            "title": title,
                            "note_type": note_type,
                            "file_path": file_path_str,
                            "reason": "missing-file",
                            "is_auto_stub": False,
                            "incoming": incoming_count.get(note_id, 0),
                            "outgoing": outgoing_count.get(note_id, 0),
                        }
                    )
                    continue

                if note_type in {"concept_note", "synthesis_note", "board_note"}:
                    in_cnt = incoming_count.get(note_id, 0)
                    out_cnt = outgoing_count.get(note_id, 0)
                    if in_cnt == 0 and out_cnt == 0:
                        candidates.append(
                            {
                                "note_id": note_id,
                                "title": title,
                                "note_type": note_type,
                                "file_path": file_path_str,
                                "reason": "orphan-no-link",
                                "is_auto_stub": self._is_auto_stub_note(note),
                                "incoming": in_cnt,
                                "outgoing": out_cnt,
                            }
                        )

        return sorted(candidates, key=lambda x: (x["reason"], x["note_type"], x["title"].lower()))

    def cleanup_unused_notes(self, note_ids: set[int]) -> dict[str, int]:
        """Soft-delete các note người dùng đã chọn và dọn stale links liên quan."""
        if not note_ids:
            return {"soft_deleted": 0, "removed_stale_links": 0}

        soft_deleted = 0
        removed_stale_links = 0

        with get_session() as session:
            notes = (
                session.query(Note)
                .filter(Note.id.in_(note_ids), Note.is_deleted == 0)
                .all()
            )
            deleted_ids: set[int] = set()
            for note in notes:
                note.is_deleted = 1
                note.updated_at = datetime.now(timezone.utc)
                soft_deleted += 1
                deleted_ids.add(int(note.id))

            if deleted_ids:
                stale_links = session.query(Link).filter(
                    (Link.from_note_id.in_(deleted_ids)) | (Link.to_note_id.in_(deleted_ids))
                ).all()
                for lnk in stale_links:
                    session.delete(lnk)
                    removed_stale_links += 1

        return {"soft_deleted": soft_deleted, "removed_stale_links": removed_stale_links}

    def _is_auto_stub_note(self, note: Note) -> bool:
        """Nhận diện note auto-stub tạo từ wikilink cũ (nội dung rất ngắn, chỉ có heading title)."""
        file_path = Path(str(note.file_path or ""))
        if not file_path.exists():
            return False
        try:
            content = file_path.read_text(encoding="utf-8").strip()
        except Exception:
            return False

        title = str(note.title or "").strip()
        if not title:
            return False

        skeletons = {
            f"# {title}",
            f"# Concept - {title}",
            f"# Synthesis - {title}",
            f"# Board - {title}",
        }
        return content in skeletons

    @staticmethod
    def _normalize_note_title_for_catalog(note_type: str, title: str) -> str:
        """Chuẩn hóa title bị chèn prefix hiển thị từ popup cũ."""
        t = title.strip()
        lower = t.lower()

        if note_type == "concept_note":
            if lower.startswith("concept - "):
                return t[len("concept - "):].strip()
            return t

        if note_type == "synthesis_note":
            stripped = t
            if lower.startswith("synthesis - "):
                stripped = t[len("synthesis - "):].strip()
            if stripped.lower().startswith("concept - synthesis - "):
                stripped = stripped[len("concept - synthesis - "):].strip()
            if stripped.lower().startswith("concept - "):
                stripped = stripped[len("concept - "):].strip()
            if stripped and not stripped.startswith("~"):
                stripped = f"~ {stripped}".strip()
            return stripped

        if note_type == "board_note":
            stripped = t
            if lower.startswith("board - "):
                stripped = t[len("board - "):].strip()
            if stripped and not stripped.startswith("!"):
                stripped = f"! {stripped}".strip()
            return stripped

        return t
