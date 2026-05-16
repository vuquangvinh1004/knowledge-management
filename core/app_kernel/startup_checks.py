"""Kiểm tra điều kiện cần thiết trước khi ứng dụng khởi động."""
from __future__ import annotations

import sys
from pathlib import Path

import config.paths as _paths
from core.utils.exceptions import ConfigError
from core.utils.logger import get_logger

logger = get_logger()

REQUIRED_PYTHON_VERSION = (3, 11)

# Tham chiếu module-level để monkeypatch được trong tests
SOURCES_DIR: Path = _paths.SOURCES_DIR
NOTES_DIR: Path = _paths.NOTES_DIR
ASSETS_DIR: Path = _paths.ASSETS_DIR
DATABASE_DIR: Path = _paths.DATABASE_DIR

# Dependency bắt buộc — app không thể chạy nếu thiếu
_HARD_DEPS: dict[str, str] = {
    "PySide6": "PySide6",
    "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic",
    "loguru": "loguru",
}

# Dependency tùy chọn — thiếu sẽ cảnh báo nhưng không chặn app
_SOFT_DEPS: dict[str, str] = {
    "fitz": "PyMuPDF (cần để xem PDF)",
    "pdfplumber": "pdfplumber (cần để trích xuất bảng)",
}


def check_python_version() -> None:
    """Kiểm tra Python >= 3.11."""
    if sys.version_info < REQUIRED_PYTHON_VERSION:
        raise ConfigError(
            f"Yêu cầu Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} "
            f"trở lên. Phiên bản hiện tại: {sys.version}"
        )
    logger.debug(f"Python version OK: {sys.version}")


def check_data_dirs() -> None:
    """Kiểm tra các thư mục data bắt buộc đã tồn tại."""
    import core.app_kernel.startup_checks as _self
    required = [_self.SOURCES_DIR, _self.NOTES_DIR, _self.ASSETS_DIR, _self.DATABASE_DIR]
    missing = [str(d) for d in required if not d.exists()]
    if missing:
        raise ConfigError(
            "Thiếu thư mục dữ liệu bắt buộc:\n" + "\n".join(missing)
        )
    logger.debug("Data directories OK.")


def check_dependencies() -> tuple[list[str], list[str]]:
    """
    Kiểm tra dependencies.

    Returns:
        (missing_hard, missing_soft): danh sách tên package thiếu theo từng nhóm.
        Raise ConfigError nếu có hard dep thiếu.
    """
    import core.app_kernel.startup_checks as _self

    missing_hard = []
    for module, display_name in _self._HARD_DEPS.items():
        try:
            __import__(module)
        except ImportError:
            missing_hard.append(display_name)

    missing_soft = []
    for module, display_name in _self._SOFT_DEPS.items():
        try:
            __import__(module)
        except ImportError:
            missing_soft.append(display_name)

    if missing_hard:
        raise ConfigError(
            f"Thiếu dependency bắt buộc: {', '.join(missing_hard)}.\n"
            "Chạy `pip install -r requirements.txt` để cài đặt."
        )

    if missing_soft:
        logger.warning(
            f"Thiếu dependency tùy chọn: {', '.join(missing_soft)}. "
            "Một số tính năng sẽ không khả dụng."
        )

    logger.debug("Dependency check hoàn tất.")
    return missing_hard, missing_soft


def run_all_checks() -> list[str]:
    """
    Chạy tất cả startup checks theo thứ tự.

    Returns:
        Danh sách soft deps còn thiếu (để UI có thể hiển thị cảnh báo nếu cần).
    """
    check_python_version()
    check_data_dirs()
    _, missing_soft = check_dependencies()
    logger.info("Tất cả startup checks passed.")
    return missing_soft


