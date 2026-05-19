"""Template và heuristic cho NoteService.

Module này tách riêng để NoteService gọn hơn, dễ test và bảo trì.
Không chứa logic persistence.
"""
from __future__ import annotations

import re

from core.utils.constants import BOARD_META_ANALYSIS_CRITERIA


_GENERIC_TITLE_PATTERNS = (
    re.compile(r"^note(\s+moi|\s*\d+)?$", re.IGNORECASE),
    re.compile(r"^ghi\s*chu(\s*\d+)?$", re.IGNORECASE),
    re.compile(r"^untitled(\s*\d+)?$", re.IGNORECASE),
)


def build_note_template(note_type: str, title: str) -> str:
    """Sinh template markdown mặc định theo loại note."""
    safe_title = title.strip() or "(Chưa đặt tiêu đề)"

    if note_type == "source_note":
        metadata_blocks = "\n\n".join(
            f"> [!{criterion.upper()}]\n>"
            for criterion in BOARD_META_ANALYSIS_CRITERIA
        )
        return (
            f"# {safe_title}\n\n"
            "## Thông tin nguồn\n"
            "- Tác giả:\n"
            "- Năm:\n"
            "- Loại nguồn:\n"
            "- Chủ đề:\n\n"
            "## Tóm tắt ngắn\n"
            "\n\n"
            "## Ý chính\n"
            "- \n"
            "- \n"
            "- \n\n"
            "## Khái niệm đáng chú ý\n"
            "- [[...]]\n"
            "- [[...]]\n\n"
            "## Trích dẫn / dữ kiện quan trọng\n"
            "- \n\n"
            "## Ghi chú của tôi\n"
            "- \n\n"
            "## Metadata\n"
            f"{metadata_blocks}\n"
        )

    if note_type == "concept_note":
        return (
            f"# Concept - {safe_title}\n\n"
            "## Định nghĩa\n"
            "\n\n"
            "## Thành phần chính\n"
            "- \n"
            "- \n\n"
            "## Ý nghĩa trong nghiên cứu\n"
            "\n\n"
            "## Liên hệ với các khái niệm khác\n"
            "- [[...]]\n"
            "- [[...]]\n\n"
            "## Nguồn liên quan\n"
            "- [[...]]\n\n"
            "## Ghi chú của tôi\n"
            "- \n"
        )

    if note_type == "synthesis_note":
        return (
            f"# Synthesis - {safe_title}\n\n"
            "## Câu hỏi trung tâm\n"
            "\n\n"
            "## Các note liên quan\n"
            "- [[...]]\n"
            "- [[...]]\n\n"
            "## Điểm giống\n"
            "- \n\n"
            "## Điểm khác\n"
            "- \n\n"
            "## Hàm ý cho đề tài\n"
            "- \n\n"
            "## Kết luận tạm thời\n"
            "- \n"
        )

    if note_type == "board_note":
        return (
            f"# Board - {safe_title}\n\n"
            "## Mục đích của board\n"
            "\n\n"
            "## Bảng nền / nguồn dữ liệu phân tích\n"
            "- Tên bảng:\n"
            "- Phạm vi:\n"
            "- Số lượng nguồn:\n\n"
            "## Cấu trúc phân tích của bảng\n"
            "\n\n"
            "## Các mẫu hình nổi bật\n"
            "### Mẫu hình 1\n"
            "\n\n"
            "## Các nhóm/chùm nội dung chính\n"
            "### Nhóm 1\n"
            "\n\n"
            "## Khoảng trống / điểm còn thiếu\n"
            "- \n\n"
            "## Hàm ý đối với hệ thống note\n"
            "- [[...]]\n\n"
            "## Hàm ý đối với nghiên cứu\n"
            "- \n\n"
            "## Kết luận tạm thời\n"
            "- \n"
        )

    return f"# {safe_title}\n\n"


def get_note_title_warnings(note_type: str, title: str) -> list[str]:
    """Trả về soft-warning cho chất lượng title theo note_type."""
    warnings: list[str] = []
    t = title.strip()
    t_lower = t.lower()

    if not t:
        warnings.append("Tiêu đề đang để trống.")
        return warnings

    if any(p.match(t) for p in _GENERIC_TITLE_PATTERNS):
        warnings.append("Tiêu đề đang quá chung chung.")

    if note_type == "source_note" and not t_lower.startswith("source"):
        warnings.append("`source_note` nên bắt đầu bằng 'source - '.")

    if note_type == "board_note" and not t.startswith("!"):
        warnings.append("`board_note` nên bắt đầu bằng '! '.")

    if note_type == "synthesis_note" and not t.startswith("~"):
        warnings.append("`synthesis_note` nên bắt đầu bằng '~ '.")

    if note_type == "synthesis_note" and len(t) < 12:
        warnings.append("`synthesis_note` nên là câu hỏi hoặc kết luận rõ nghĩa.")

    if note_type == "concept_note" and len(t) < 3:
        warnings.append("`concept_note` nên dùng tên khái niệm cụ thể.")

    return warnings
