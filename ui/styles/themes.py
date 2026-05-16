"""Quản lý theme và áp dụng stylesheet cho ứng dụng."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

from ui.styles.qss_styles import get_light_qss


def apply_theme(app: QApplication, theme: str = "light") -> None:
    """
    Áp dụng QSS stylesheet theo theme.
    Hiện tại chỉ hỗ trợ 'light'. Dark theme sẽ được thêm sau.
    """
    if theme == "light":
        app.setStyleSheet(get_light_qss())
    else:
        # Fallback về light nếu theme chưa được implement
        app.setStyleSheet(get_light_qss())
