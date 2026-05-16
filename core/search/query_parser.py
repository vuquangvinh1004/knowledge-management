"""Chuẩn bị query string để đưa vào FTS5.

Hỗ trợ:
- Từ đơn: 'python'
- Cụm từ: '"machine learning"'
- Loại trừ: '-bad_word'
- Nhiều từ: 'python machine learning' → 'python machine learning' (FTS5 OR mặc định)
"""
from __future__ import annotations

import re

# Ký tự không an toàn trong FTS5 query (ngoài dấu nháy và dấu trừ đầu từ)
_UNSAFE = re.compile(r'[^\w\s"\-*]', re.UNICODE)


def build_fts_query(user_input: str) -> str:
    """
    Chuyển input người dùng thành FTS5 query string an toàn.

    Quy tắc:
    - Trim whitespace
    - Xóa ký tự đặc biệt không hợp lệ
    - Từ đơn giữ nguyên; nhiều từ: mỗi từ tìm trong content (implicit AND mặc định FTS5)
    - Cụm trong dấu nháy kép được giữ nguyên
    - Từ bắt đầu bằng '-' giữ nguyên (loại trừ)
    - Thêm '*' suffix để hỗ trợ prefix search nếu từ không kết thúc bằng *

    Args:
        user_input: Chuỗi tìm kiếm người dùng nhập.

    Returns:
        FTS5-compatible query string, hoặc chuỗi rỗng nếu input không hợp lệ.
    """
    raw = user_input.strip()
    if not raw:
        return ""

    # Xóa ký tự đặc biệt nguy hiểm (giữ lại chữ, số, space, dấu nháy kép, dấu trừ, *)
    cleaned = _UNSAFE.sub(" ", raw).strip()
    if not cleaned:
        return ""

    # Phân tích từng token (tôn trọng cụm trong nháy kép)
    tokens = _tokenize(cleaned)
    if not tokens:
        return ""

    result_tokens: list[str] = []
    for token in tokens:
        if token.startswith('"') and token.endswith('"'):
            # cụm từ — giữ nguyên
            result_tokens.append(token)
        elif token.startswith("-"):
            # loại trừ — giữ nguyên phần sau dấu trừ, thêm * nếu chưa có
            word = token[1:]
            if word and not word.endswith("*"):
                result_tokens.append(f"-{word}*")
            elif word:
                result_tokens.append(token)
        else:
            # từ thường — thêm * để prefix search
            if not token.endswith("*"):
                result_tokens.append(f"{token}*")
            else:
                result_tokens.append(token)

    return " ".join(result_tokens)


def _tokenize(text: str) -> list[str]:
    """Tách text thành token, tôn trọng cụm trong dấu nháy kép."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '"':
            # Tìm nháy kép đóng
            j = text.find('"', i + 1)
            if j == -1:
                j = n
            tokens.append(text[i : j + 1])
            i = j + 1
        elif text[i].isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace():
                j += 1
            tokens.append(text[i:j])
            i = j
    return [t for t in tokens if t.strip()]
