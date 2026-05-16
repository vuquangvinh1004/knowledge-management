"""Quản lý cài đặt ứng dụng.

Cài đặt được lưu dưới dạng JSON tại data/settings.json.
Sử dụng singleton get_settings() để truy cập từ mọi nơi.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.paths import SETTINGS_FILE


DEFAULT_EDITOR_FONT_FAMILY = "Cascadia Code, Consolas, Courier New, monospace"

EDITOR_FONT_PRESETS: tuple[str, ...] = (
    "Cascadia Code, Consolas, Courier New, monospace",
    "Cascadia Code, Roboto Mono, monospace",
    "Cascadia Mono, Consolas, monospace",
    "Aptos Mono, Consolas, monospace",
    "JetBrains Mono, Consolas, monospace",
    "IBM Plex Mono, Consolas, monospace",
    "Source Code Pro, Consolas, monospace",
    "Roboto Mono, Consolas, monospace",
    "DejaVu Sans Mono, monospace",
    "Noto Sans Mono, monospace",
    "Ubuntu Mono, Consolas, monospace",
)


_DEFAULTS: dict[str, Any] = {
    "window_width": 1280,
    "window_height": 800,
    "window_maximized": False,
    "sidebar_width": 220,
    "dual_pane_split": 0.5,
    "theme": "light",
    "last_opened_sources": [],
    "autosave_interval_seconds": 30,
    "editor.fontFamily": DEFAULT_EDITOR_FONT_FAMILY,
    "editor.fontLigatures": True,
}


class AppSettings:
    """Quản lý và lưu trữ cài đặt ứng dụng."""

    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self._path = path
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Đọc cài đặt từ file. Nếu file chưa tồn tại, dùng giá trị mặc định."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        # Merge defaults cho các key còn thiếu
        for key, value in _DEFAULTS.items():
            self._data.setdefault(key, value)

    def save(self) -> None:
        """Lưu cài đặt ra file JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value


_settings_instance: AppSettings | None = None


def get_settings() -> AppSettings:
    """Trả về singleton AppSettings."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
    return _settings_instance
