"""Service truy cập và cập nhật cài đặt ứng dụng.

Bao lấp AppSettings và hỗ trợ các khóa cài đặt có kích thước.
"""
from __future__ import annotations

from config.settings import get_settings
from core.utils.logger import get_logger

logger = get_logger()

# Giá trị mặc định cho cài đặt ứng dụng
_DEFAULTS: dict[str, object] = {
    "theme": "light",
    "autosave_delay_ms": 2000,
    "backup_keep_count": 10,
    "window_width": 1280,
    "window_height": 800,
    "window_maximized": False,
    "last_opened_source_id": None,
    "search_default_limit": 50,
    "fts_rebuild_on_startup": False,
    "graph_layout_positions": {},
    "graph_virtualize_default": True,
    "graph_virtualize_max_nodes": 120,
    "editor.fontFamily": "Cascadia Code, Consolas, Courier New, monospace",
    "editor.fontLigatures": True,
}


class SettingsService:
    """Truy cập và cập nhật cài đặt ứng dụng."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def get(self, key: str, default=None):
        """Lấy giá trị cài đặt, fallback về default bảng, sau đó tham số default."""
        fallback = _DEFAULTS.get(key, default)
        return self._settings.get(key, fallback)

    def set(self, key: str, value) -> None:
        """Cập nhật giá trị cài đặt và lưu ngay."""
        self._settings.set(key, value)
        self._settings.save()
        logger.debug(f"Cài đặt {key!r} = {value!r}")

    def all_defaults(self) -> dict:
        """Trả về tất cả cài đặt hiện tại (merge default và user overrides)."""
        result = dict(_DEFAULTS)
        for key in _DEFAULTS:
            result[key] = self.get(key)
        return result

    def reset_to_defaults(self) -> None:
        """Khôi phục toàn bộ cài đặt về mặc định."""
        for key, value in _DEFAULTS.items():
            self._settings.set(key, value)
        self._settings.save()
        logger.info("Đã khôi phục cài đặt về mặc định.")
