"""Service quản lý tài liệu nguồn PDF.

Business rules:
- Mỗi source phải có file_hash để chống nhập trùng.
- Source chưa có note liên quan có thể xóa cứng.
- Source đã có note/extract phải soft-delete trước.
- Đổi path phải relink, không để orphan im lặng.
"""
from __future__ import annotations

from pathlib import Path
import re

from sqlalchemy.orm import Session

from core.storage.models import Source
from core.storage.session import get_session
from core.utils.exceptions import (
    SourceDuplicateError,
    SourceFileNotFoundError,
    SourceNotFoundError,
)
from core.utils.helpers import compute_file_hash, slugify
from core.utils.logger import get_logger

logger = get_logger()


def _int_to_source_code(n: int) -> str:
    """Chuyển số thứ tự thành mã 4 ký tự AA00-ZZ99.

    Thứ tự: AA00, AA01, ..., AA99, AB00, ..., ZZ98, ZZ99.
    Tối đa 67600 source (26*26*100).
    """
    digits = n % 100
    letter_idx = n // 100
    letter1 = chr(65 + letter_idx // 26)
    letter2 = chr(65 + letter_idx % 26)
    return f"{letter1}{letter2}{digits:02d}"


class SourceService:
    """CRUD và quản lý lifecycle cho Source."""

    @staticmethod
    def _normalize_year(year: str | None) -> str | None:
        """Chuẩn hóa năm về định dạng 4 chữ số nếu hợp lệ."""
        if not year:
            return None
        digits = "".join(ch for ch in str(year) if ch.isdigit())
        if len(digits) >= 4:
            candidate = digits[:4]
            if 1900 <= int(candidate) <= 2100:
                return candidate
        return None

    @staticmethod
    def _extract_author_surnames(authors: str | None) -> list[str]:
        """Tách danh sách họ tác giả từ chuỗi metadata authors."""
        if not authors:
            return []

        raw = authors.strip()
        if not raw:
            return []

        normalized = re.sub(r"\s+(and|&|va)\s+", ";", raw, flags=re.IGNORECASE)
        parts = [p.strip() for p in re.split(r";", normalized) if p.strip()]
        if not parts:
            return []

        surnames: list[str] = []
        for part in parts:
            if "," in part:
                surname = part.split(",", 1)[0].strip()
            else:
                tokens = part.split()
                surname = tokens[-1].strip() if tokens else ""
            if surname:
                surnames.append(surname)
        return surnames

    @staticmethod
    def build_source_note_title(
        *,
        authors: str | None,
        year: str | None,
        fallback_filename: str,
    ) -> str:
        """Sinh title source_note theo quy ước `{Tác giả} ({Năm})`.

        Nếu thiếu cả author và year, fallback về tên file (không đuôi).
        """
        surnames = SourceService._extract_author_surnames(authors)
        year_part = SourceService._normalize_year(year)

        author_part: str | None = None
        if len(surnames) >= 3:
            author_part = f"{surnames[0]} et al."
        elif len(surnames) == 2:
            author_part = f"{surnames[0]} & {surnames[1]}"
        elif len(surnames) == 1:
            author_part = surnames[0]

        if author_part and year_part:
            return f"{author_part} ({year_part})"
        if author_part:
            return author_part
        if year_part:
            return f"({year_part})"
        return fallback_filename.strip() or "source_note"

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_id(self, source_id: int) -> Source:
        """
        Lấy source theo ID.

        Raises:
            SourceNotFoundError: Nếu không tìm thấy hoặc đã bị xóa.
        """
        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None or source.is_deleted:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")
            session.expunge(source)
            return source

    def list_all(self, include_deleted: bool = False) -> list[Source]:
        """Lấy danh sách tất cả sources (mặc định bỏ qua đã xóa)."""
        with get_session() as session:
            query = session.query(Source)
            if not include_deleted:
                query = query.filter(Source.is_deleted == 0)
            sources = query.order_by(Source.created_at.desc()).all()
            for s in sources:
                session.expunge(s)
            return sources

    def find_by_hash(self, file_hash: str) -> Source | None:
        """Tìm source theo file_hash (dùng để chống nhập trùng)."""
        with get_session() as session:
            source = (
                session.query(Source)
                .filter(Source.file_hash == file_hash, Source.is_deleted == 0)
                .first()
            )
            if source:
                session.expunge(source)
            return source

    def get_by_source_code(self, source_code: str) -> Source | None:
        """Tìm source theo source_code (AA00-ZZ99). Trả None nếu không tìm thấy."""
        with get_session() as session:
            source = (
                session.query(Source)
                .filter(Source.source_code == source_code.upper(), Source.is_deleted == 0)
                .first()
            )
            if source:
                session.expunge(source)
            return source

    def _generate_next_source_code(self, session) -> str:
        """Sinh source_code kế tiếp chưa được dùng (AA00-ZZ99)."""
        total = session.query(Source).filter(Source.source_code.is_not(None)).count()
        code = _int_to_source_code(total)
        # Đảm bảo không trùng (phòng khi có gap do xóa/rollback)
        offset = 0
        while session.query(Source).filter(Source.source_code == code).first() is not None:
            offset += 1
            code = _int_to_source_code(total + offset)
        return code

    def ensure_source_code(self, source_id: int) -> str:
        """Đảm bảo source có source_code; chỉ sinh khi còn thiếu.

        Trả về source_code hiện tại hoặc vừa được gán mới.
        """
        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None or source.is_deleted:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")

            if source.source_code:
                return str(source.source_code)

            code = self._generate_next_source_code(session)
            source.source_code = code
            return code

    # ------------------------------------------------------------------
    # Create / Import
    # ------------------------------------------------------------------

    def import_source(
        self,
        file_path: Path,
        title: str | None = None,
        authors: str | None = None,
        year: str | None = None,
        doi: str | None = None,
    ) -> Source:
        """
        Import một file PDF vào thư viện.

        Args:
            file_path: Đường dẫn tuyệt đối tới file PDF.
            title: Tiêu đề (nếu None sẽ thử trích từ PDF metadata, fallback tên file).
            authors, year, doi: Metadata tùy chọn (nếu None sẽ thử trích từ PDF).

        Returns:
            Source đã tạo.

        Raises:
            SourceFileNotFoundError: Nếu file không tồn tại.
            SourceDuplicateError: Nếu file đã được import (trùng hash).
        """
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise SourceFileNotFoundError(f"File không tồn tại: {file_path}")

        file_hash = compute_file_hash(file_path)
        existing = self.find_by_hash(file_hash)
        if existing:
            raise SourceDuplicateError(
                f"File đã được import trước đó (id={existing.id}): {existing.file_path}"
            )

        # Tự động trích metadata từ PDF
        auto_meta = SourceService.extract_pdf_metadata(file_path)
        resolved_title = title or auto_meta.get("title") or file_path.stem
        resolved_authors = authors or auto_meta.get("authors")
        resolved_year = year or auto_meta.get("year")

        # Lưu metadata bổ sung vào metadata_json
        import json
        meta_extra: dict = {}
        if auto_meta.get("pages_count"):
            meta_extra["pages_count"] = auto_meta["pages_count"]
        if auto_meta.get("keywords"):
            meta_extra["keywords"] = auto_meta["keywords"]
        if auto_meta.get("subject"):
            meta_extra["subject"] = auto_meta["subject"]

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        source = Source(
            file_path=str(file_path),
            file_hash=file_hash,
            title=resolved_title,
            authors=resolved_authors,
            year=resolved_year,
            doi=doi,
            metadata_json=json.dumps(meta_extra, ensure_ascii=False) if meta_extra else None,
            created_at=now,
            updated_at=now,
        )
        with get_session() as session:
            session.add(source)
            session.flush()
            session.expunge(source)

        logger.info(f"Import source: id={source.id} path={file_path}")
        return source

    @staticmethod
    def extract_pdf_metadata(file_path: Path) -> dict:
        """
        Trích xuất metadata từ file PDF bằng PyMuPDF.

        Returns:
            dict với các khóa: title, authors, year, keywords, subject, pages_count.
            Các giá trị None nếu không trích được.
        """
        result: dict = {
            "title": None,
            "authors": None,
            "year": None,
            "keywords": None,
            "subject": None,
            "pages_count": 0,
        }
        try:
            import fitz  # noqa: PLC0415
            doc = fitz.open(str(file_path))
            result["pages_count"] = doc.page_count
            meta = doc.metadata or {}
            if meta.get("title", "").strip():
                result["title"] = meta["title"].strip()
            if meta.get("author", "").strip():
                result["authors"] = meta["author"].strip()
            if meta.get("keywords", "").strip():
                result["keywords"] = meta["keywords"].strip()
            if meta.get("subject", "").strip():
                result["subject"] = meta["subject"].strip()
            # Năm từ creationDate: D:YYYYMMDDHHmmSS
            creation = meta.get("creationDate", "")
            if creation:
                year_str = creation[2:6] if creation.startswith("D:") else creation[:4]
                if year_str.isdigit() and 1900 <= int(year_str) <= 2100:
                    result["year"] = year_str
            doc.close()
        except Exception as exc:
            logger.debug(f"Không thể đọc PDF metadata từ {file_path}: {exc}")
        return result

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_metadata(
        self,
        source_id: int,
        *,
        title: str | None = None,
        authors: str | None = None,
        year: str | None = None,
        doi: str | None = None,
        # Extended fields stored in metadata_json
        abstract: str | None = None,
        keywords: str | None = None,
        item_type: str | None = None,
        journal: str | None = None,
        volume: str | None = None,
        issue: str | None = None,
        pages: str | None = None,
        url: str | None = None,
        issn: str | None = None,
        language: str | None = None,
        publisher: str | None = None,
    ) -> Source:
        """
        Cập nhật metadata của source.

        Các trường title/authors/year/doi lưu vào cột DB trực tiếp.
        Các trường mở rộng (abstract, keywords, journal, ...) lưu vào metadata_json.
        """
        _JSON_FIELDS = {
            "abstract": abstract,
            "keywords": keywords,
            "item_type": item_type,
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "url": url,
            "issn": issn,
            "language": language,
            "publisher": publisher,
        }
        json_updates = {k: v for k, v in _JSON_FIELDS.items() if v is not None}

        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None or source.is_deleted:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")
            if title is not None:
                source.title = title
            if authors is not None:
                source.authors = authors
            if year is not None:
                source.year = year
            if doi is not None:
                source.doi = doi
            if json_updates:
                import json
                try:
                    extra = json.loads(source.metadata_json or "{}")
                except Exception:
                    extra = {}
                extra.update(json_updates)
                source.metadata_json = json.dumps(extra, ensure_ascii=False)
            from datetime import datetime, timezone
            source.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(source)
        logger.info(f"Cập nhật metadata source id={source_id}")
        return source

    def update_last_opened_page(self, source_id: int, page_no: int) -> None:
        """Lưu trang PDF cuối cùng người dùng đang xem."""
        with get_session() as session:
            source = session.get(Source, source_id)
            if source and not source.is_deleted:
                source.last_opened_page = page_no

    def relink_path(self, source_id: int, new_path: Path) -> Source:
        """
        Cập nhật đường dẫn file khi nguồn bị di chuyển.

        Raises:
            SourceFileNotFoundError: Nếu new_path không tồn tại.
        """
        new_path = Path(new_path).resolve()
        if not new_path.exists():
            raise SourceFileNotFoundError(f"File mới không tồn tại: {new_path}")

        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None or source.is_deleted:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")
            source.file_path = str(new_path)
            source.file_hash = compute_file_hash(new_path)
            from datetime import datetime, timezone
            source.updated_at = datetime.now(timezone.utc)
            session.flush()
            session.expunge(source)
        logger.info(f"Relink source id={source_id} → {new_path}")
        return source

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def soft_delete(self, source_id: int) -> None:
        """
        Đánh dấu source đã xóa (soft-delete).
        Notes và extracts liên quan vẫn còn trong DB.
        """
        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")
            source.is_deleted = 1
            from datetime import datetime, timezone
            source.updated_at = datetime.now(timezone.utc)
        logger.info(f"Soft-delete source id={source_id}")

    def hard_delete(self, source_id: int) -> None:
        """
        Xóa cứng source khỏi DB.

        Raises:
            SourceNotFoundError: Nếu source không tồn tại.
        """
        with get_session() as session:
            source = session.get(Source, source_id)
            if source is None:
                raise SourceNotFoundError(f"Không tìm thấy source id={source_id}.")
            session.delete(source)
        logger.info(f"Hard-delete source id={source_id}")
