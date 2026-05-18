"""Quản lý catalog snippet Markdown cho thao tác chèn nhanh trong editor."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from core.services.settings_service import SettingsService


@dataclass(slots=True)
class MarkdownSnippet:
    """Định nghĩa một snippet có thể chèn vào editor."""

    snippet_id: str
    name: str
    description: str
    template: str
    built_in: bool = False


class MarkdownSnippetService:
    """Sở hữu catalog snippet và cài đặt hiển thị menu chèn."""

    _CATALOG_KEY = "editor.insert_snippets.catalog"
    _VISIBLE_KEY = "editor.insert_snippets.visible_ids"

    _DEFAULT_SNIPPETS: tuple[MarkdownSnippet, ...] = (
        MarkdownSnippet(
            snippet_id="math",
            name="$$ Math $$",
            description="Khối công thức toán học dạng display math.",
            template="$$\nBiểu thức toán #(Eq.01)\n$$\n",
            built_in=True,
        ),
        MarkdownSnippet(
            snippet_id="table",
            name="| Table |",
            description="Bảng Markdown với dòng căn lề mẫu.",
            template=(
                "| Tiêu đề 1 | Tiêu đề 2 | Tiêu đề 3 |\n"
                "| :--- | :---: | ---: |\n"
                "| Căn trái | Căn giữa | Căn phải |\n"
                "| Dữ liệu | Dữ liệu | Dữ liệu |\n"
            ),
            built_in=True,
        ),
        MarkdownSnippet(
            snippet_id="checklist",
            name="[x] Checklist",
            description="Danh sách checkbox Markdown.",
            template=(
                "- [ ] Công việc chưa làm\n"
                "- [x] Công việc đã hoàn thành\n"
            ),
            built_in=True,
        ),
        MarkdownSnippet(
            snippet_id="url",
            name="[](URL)",
            description="Liên kết Markdown với chữ hiển thị và URL.",
            template="[Chữ hiển thị](https://example.com)\n",
            built_in=True,
        ),
        MarkdownSnippet(
            snippet_id="align",
            name="&& Align",
            description="Khối toán nhiều dòng với các điểm căn thẳng hàng.",
            template=(
                "$$\n"
                "    &= [Biểu thức 1] \\\\n"
                "    &= [Biểu thức 2]\n"
                "$$\n"
            ),
            built_in=True,
        ),
    )
    _DEFAULT_VISIBLE_IDS: tuple[str, ...] = ("math", "table", "checklist", "url")

    def __init__(self, settings_service: SettingsService | None = None) -> None:
        self._settings_service = settings_service or SettingsService()

    def list_available(self) -> list[MarkdownSnippet]:
        """Trả về toàn bộ snippet khả dụng, gồm built-in và custom."""
        raw_catalog = self._settings_service.get(self._CATALOG_KEY, None)
        if not isinstance(raw_catalog, list) or not raw_catalog:
            return list(self._DEFAULT_SNIPPETS)

        defaults_by_id = {snippet.snippet_id: snippet for snippet in self._DEFAULT_SNIPPETS}
        custom_by_id: dict[str, MarkdownSnippet] = {}
        for item in raw_catalog:
            snippet = self._deserialize_snippet(item)
            if snippet is None:
                continue
            if snippet.snippet_id in defaults_by_id:
                defaults_by_id[snippet.snippet_id] = MarkdownSnippet(
                    snippet_id=snippet.snippet_id,
                    name=snippet.name,
                    description=snippet.description,
                    template=snippet.template,
                    built_in=True,
                )
            else:
                custom_by_id[snippet.snippet_id] = snippet

        merged: list[MarkdownSnippet] = []
        for default in self._DEFAULT_SNIPPETS:
            merged.append(defaults_by_id[default.snippet_id])
        merged.extend(custom_by_id.values())
        return merged

    def list_visible(self) -> list[MarkdownSnippet]:
        """Danh sách snippet đang hiện trên menu `Chèn...`."""
        catalog = self.list_available()
        by_id = {snippet.snippet_id: snippet for snippet in catalog}
        visible_ids = self._normalize_visible_ids(self._settings_service.get(self._VISIBLE_KEY, None), by_id)
        return [by_id[snippet_id] for snippet_id in visible_ids if snippet_id in by_id]

    def get_by_id(self, snippet_id: str) -> MarkdownSnippet | None:
        """Tìm snippet theo id."""
        for snippet in self.list_available():
            if snippet.snippet_id == snippet_id:
                return snippet
        return None

    def set_visible_ids(self, visible_ids: list[str]) -> None:
        """Lưu thứ tự và tập snippet hiển thị trong menu `Chèn...`."""
        by_id = {snippet.snippet_id: snippet for snippet in self.list_available()}
        normalized = self._normalize_visible_ids(visible_ids, by_id)
        self._settings_service.set(self._VISIBLE_KEY, normalized)

    def save_catalog(self, snippets: list[MarkdownSnippet]) -> None:
        """Lưu toàn bộ catalog snippet sau khi chỉnh sửa."""
        serialized = [self._serialize_snippet(snippet) for snippet in snippets]
        self._settings_service.set(self._CATALOG_KEY, serialized)

    def update_snippet(self, snippet_id: str, *, name: str, description: str, template: str) -> MarkdownSnippet:
        """Cập nhật một snippet hiện có và lưu catalog."""
        catalog = self.list_available()
        updated: MarkdownSnippet | None = None
        for index, snippet in enumerate(catalog):
            if snippet.snippet_id != snippet_id:
                continue
            updated = MarkdownSnippet(
                snippet_id=snippet.snippet_id,
                name=name.strip(),
                description=description.strip(),
                template=template,
                built_in=snippet.built_in,
            )
            catalog[index] = updated
            break
        if updated is None:
            raise ValueError(f"Không tìm thấy snippet id={snippet_id}.")
        self.save_catalog(catalog)
        return updated

    def create_snippet(self, *, name: str, description: str, template: str) -> MarkdownSnippet:
        """Tạo snippet mới do người dùng định nghĩa."""
        base_slug = self._slugify(name) or "snippet-moi"
        existing_ids = {snippet.snippet_id for snippet in self.list_available()}
        snippet_id = base_slug
        suffix = 2
        while snippet_id in existing_ids:
            snippet_id = f"{base_slug}-{suffix}"
            suffix += 1

        snippet = MarkdownSnippet(
            snippet_id=snippet_id,
            name=name.strip(),
            description=description.strip(),
            template=template,
            built_in=False,
        )
        catalog = self.list_available()
        catalog.append(snippet)
        self.save_catalog(catalog)

        visible_ids = [item.snippet_id for item in self.list_visible()]
        visible_ids.append(snippet.snippet_id)
        self.set_visible_ids(visible_ids)
        return snippet

    def delete_snippet(self, snippet_id: str) -> None:
        """Xóa một snippet custom khỏi catalog."""
        snippet = self.get_by_id(snippet_id)
        if snippet is None:
            return
        if snippet.built_in:
            raise ValueError("Không thể xóa đối tượng mặc định.")

        catalog = [item for item in self.list_available() if item.snippet_id != snippet_id]
        self.save_catalog(catalog)

        visible_ids = [item.snippet_id for item in self.list_visible() if item.snippet_id != snippet_id]
        self.set_visible_ids(visible_ids)

    @staticmethod
    def _serialize_snippet(snippet: MarkdownSnippet) -> dict[str, object]:
        return asdict(snippet)

    @staticmethod
    def _deserialize_snippet(raw: object) -> MarkdownSnippet | None:
        if not isinstance(raw, dict):
            return None
        snippet_id = str(raw.get("snippet_id") or "").strip()
        name = str(raw.get("name") or "").strip()
        template = str(raw.get("template") or "")
        if not snippet_id or not name or not template:
            return None
        return MarkdownSnippet(
            snippet_id=snippet_id,
            name=name,
            description=str(raw.get("description") or "").strip(),
            template=template,
            built_in=bool(raw.get("built_in", False)),
        )

    def _normalize_visible_ids(self, raw_visible_ids: object, by_id: dict[str, MarkdownSnippet]) -> list[str]:
        if not isinstance(raw_visible_ids, list):
            raw_visible_ids = list(self._DEFAULT_VISIBLE_IDS)

        normalized: list[str] = []
        for raw_id in raw_visible_ids:
            snippet_id = str(raw_id).strip()
            if not snippet_id or snippet_id not in by_id or snippet_id in normalized:
                continue
            normalized.append(snippet_id)

        if not normalized:
            normalized = [snippet_id for snippet_id in self._DEFAULT_VISIBLE_IDS if snippet_id in by_id]
        return normalized

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug