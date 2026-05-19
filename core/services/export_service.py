"""Service xuất dữ liệu PKM ra file bên ngoài.

Hỗ trợ:
- Export source bundle: note + extracts của một source → Markdown file
- Export board snapshot: Markdown table hoặc CSV
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

from core.storage.models import Extract, Note, Project, ProjectNoteRef, Source
from core.storage.session import get_session
from core.utils.exceptions import PKMError
from core.utils.logger import get_logger

logger = get_logger()


class ExportService:
    """Xuất dữ liệu ra file."""

    def __init__(self, exports_dir: Path) -> None:
        self._exports_dir = Path(exports_dir)
        self._exports_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Source bundle
    # ------------------------------------------------------------------

    def export_source_bundle(self, source_id: int, notes_dir: Path) -> Path:
        """
        Xuất note chính + toàn bộ extracts của một source thành Markdown file.

        Args:
            source_id: ID của source cần xuất.
            notes_dir: Thư mục chứa file Markdown của notes.

        Returns:
            Path của file Markdown đã xuất.

        Raises:
            PKMError: Nếu source không tồn tại.
        """
        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None or source.is_deleted:
                raise PKMError(f"Không tìm thấy source id={source_id}.")

            # Note chính
            source_note = (
                session.query(Note)
                .filter(
                    Note.source_id == source_id,
                    Note.note_type == "source_note",
                    Note.is_deleted == 0,
                )
                .first()
            )

            # Extracts
            extracts = (
                session.query(Extract)
                .filter(Extract.source_id == source_id)
                .order_by(Extract.page_no)
                .all()
            )

            src_title = source.title or f"Source {source_id}"
            src_authors = source.authors or ""
            src_year = source.year or ""
            src_public_id = str(source.public_id or "")
            src_code = str(source.source_code or "")

            note_content = ""
            if source_note:
                note_file = Path(source_note.file_path)
                if note_file.exists():
                    note_content = note_file.read_text(encoding="utf-8")

            lines: list[str] = [
                f"# {src_title}",
                "",
                f"**Public ID:** {src_public_id}" if src_public_id else "",
                f"**Mã nguồn:** {src_code}" if src_code else "",
                f"**Tác giả:** {src_authors}" if src_authors else "",
                f"**Năm:** {src_year}" if src_year else "",
                "",
                "---",
                "",
                "## Ghi chú",
                "",
                note_content or "_Chưa có ghi chú._",
                "",
            ]

            if extracts:
                lines += ["---", "", "## Trích xuất", ""]
                for ext in extracts:
                    lines.append(f"### Trang {ext.page_no} — {ext.extract_type}")
                    lines.append("")
                    lines.append(ext.content_md)
                    lines.append("")
                    lines.append(f"> Nguồn: `{ext.source_anchor}`")
                    lines.append("")

        # Tạo file
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in src_title if c.isalnum() or c in " _-")[:40].strip()
        filename = f"{safe_title}_{timestamp}.md"
        output_path = self._exports_dir / filename
        output_path.write_text("\n".join(l for l in lines if l is not None), encoding="utf-8")

        logger.info(f"Đã xuất source bundle: {output_path}")
        return output_path

    def export_project_bundle(self, project_id: int) -> Path:
        """Đóng gói project thành thư mục Markdown standalone.

        Output:
            exports_dir / {project_name}_{project_id} /
              ├── README.md
              ├── own/*.md
              └── refs/*.md
        """
        with get_session() as session:
            project = session.get(Project, project_id)
            if project is None or project.is_deleted:
                raise PKMError(f"Không tìm thấy project id={project_id}.")

            own_notes = (
                session.query(Note)
                .filter(Note.project_id == project_id, Note.is_deleted == 0)
                .order_by(Note.updated_at.desc())
                .all()
            )

            ref_notes = (
                session.query(Note)
                .join(ProjectNoteRef, ProjectNoteRef.note_id == Note.id)
                .filter(ProjectNoteRef.project_id == project_id, Note.is_deleted == 0)
                .order_by(Note.title)
                .all()
            )

            project_name = str(project.name or f"Project {project_id}")
            project_desc = str(project.description or "")
            project_status = str(project.status or "active")
            project_public_id = str(project.public_id or "")
            created_at = project.created_at

        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in project_name).strip()
        if not safe_name:
            safe_name = f"project_{project_id}"

        bundle_dir = self._exports_dir / f"{safe_name}_{project_id}"
        own_dir = bundle_dir / "own"
        refs_dir = bundle_dir / "refs"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        own_dir.mkdir(exist_ok=True)
        refs_dir.mkdir(exist_ok=True)

        readme_path = bundle_dir / "README.md"
        lines: list[str] = [
            f"# {project_name}",
            "",
            f"**Project Public ID:** {project_public_id}" if project_public_id else "",
            "",
            f"**Mô tả:** {project_desc}",
            "",
            f"**Trạng thái:** {project_status}",
            "",
            f"**Tạo lúc:** {created_at}",
            "",
            f"**Đóng gói lúc:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "---",
            "",
            f"## Notes riêng của project ({len(own_notes)} notes)",
            "",
        ]
        for note in own_notes:
            note_public_id = str(getattr(note, "public_id", "") or "")
            if note_public_id:
                lines.append(f"- [{note.title}](own/{Path(note.file_path).name}) — `{note_public_id}`")
            else:
                lines.append(f"- [{note.title}](own/{Path(note.file_path).name})")

        lines += ["", f"## Notes tham khảo từ Global ({len(ref_notes)} notes)", ""]
        for note in ref_notes:
            note_public_id = str(getattr(note, "public_id", "") or "")
            if note_public_id:
                lines.append(f"- [{note.title}](refs/{Path(note.file_path).name}) — `{note_public_id}`")
            else:
                lines.append(f"- [{note.title}](refs/{Path(note.file_path).name})")

        readme_path.write_text("\n".join(lines), encoding="utf-8")

        copied_own = 0
        for note in own_notes:
            src = Path(note.file_path)
            if src.exists():
                shutil.copy2(src, own_dir / src.name)
                copied_own += 1
            else:
                logger.warning(f"ExportService: own note file không tìm thấy: {src}")

        copied_refs = 0
        for note in ref_notes:
            src = Path(note.file_path)
            if src.exists():
                shutil.copy2(src, refs_dir / src.name)
                copied_refs += 1
            else:
                logger.warning(f"ExportService: ref note file không tìm thấy: {src}")

        logger.info(
            f"Đã xuất project bundle: {bundle_dir} "
            f"(project={project_id}, own={copied_own}, refs={copied_refs})"
        )
        return bundle_dir

    # ------------------------------------------------------------------
    # Board export
    # ------------------------------------------------------------------

    def export_board_markdown(
        self,
        output_filename: str | None = None,
        board_id: int | None = None,
    ) -> Path:
        """Xuất Research Board thành Markdown file."""
        from core.services.board_service import BoardService

        svc = BoardService()
        content = svc.export_markdown(board_id=board_id)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"board_{timestamp}.md"
        output_path = self._exports_dir / filename
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Đã xuất board Markdown: {output_path}")
        return output_path

    def export_board_csv(
        self,
        output_filename: str | None = None,
        board_id: int | None = None,
    ) -> Path:
        """Xuất Research Board thành CSV file."""
        from core.services.board_service import BoardService

        svc = BoardService()
        content = svc.export_csv(board_id=board_id)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = output_filename or f"board_{timestamp}.csv"
        output_path = self._exports_dir / filename
        output_path.write_text(content, encoding="utf-8", newline="")

        logger.info(f"Đã xuất board CSV: {output_path}")
        return output_path
