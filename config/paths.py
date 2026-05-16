"""Quản lý đường dẫn ứng dụng.

Tất cả đường dẫn được tính từ BASE_DIR (thư mục gốc dự án).
Không sử dụng đường dẫn tuyệt đối cứng ở nơi khác — luôn import từ đây.
"""
from pathlib import Path

# Thư mục gốc dự án (chứa main.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục data
DATA_DIR = BASE_DIR / "data"
SOURCES_DIR = DATA_DIR / "sources"
NOTES_DIR = DATA_DIR / "notes"
ASSETS_DIR = DATA_DIR / "assets"
EXPORTS_DIR = DATA_DIR / "exports"
BACKUPS_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"
TEMP_DIR = DATA_DIR / "temp"
DATABASE_DIR = DATA_DIR / "database"

# Đường dẫn database SQLite
DATABASE_FILE = DATABASE_DIR / "research_pkm.db"

# Lock file (single-instance)
LOCK_FILE = TEMP_DIR / "research_pkm.lock"

# Settings file
SETTINGS_FILE = DATA_DIR / "settings.json"


DATA_DIRS = [
    DATA_DIR,
    SOURCES_DIR,
    NOTES_DIR,
    ASSETS_DIR,
    EXPORTS_DIR,
    BACKUPS_DIR,
    LOGS_DIR,
    TEMP_DIR,
    DATABASE_DIR,
]


def ensure_data_dirs() -> None:
    """Tạo tất cả thư mục data nếu chưa tồn tại."""
    for d in DATA_DIRS:
        d.mkdir(parents=True, exist_ok=True)
