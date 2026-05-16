"""Ngoại lệ tùy chỉnh cho ứng dụng PKM."""


class PKMError(Exception):
    """Ngoại lệ gốc của ứng dụng PKM."""


class ConfigError(PKMError):
    """Lỗi cấu hình ứng dụng."""


class DatabaseError(PKMError):
    """Lỗi kết nối hoặc truy vấn database."""


class MigrationError(PKMError):
    """Lỗi khi chạy schema migration."""


class SourceNotFoundError(PKMError):
    """Không tìm thấy source trong database."""


class SourceFileNotFoundError(PKMError):
    """File nguồn PDF không tồn tại tại đường dẫn đã lưu."""


class SourceDuplicateError(PKMError):
    """Source đã tồn tại trong thư viện (trùng hash hoặc đường dẫn)."""


class NoteNotFoundError(PKMError):
    """Không tìm thấy note trong database."""


class ExtractAnchorMissingError(PKMError):
    """Extract thiếu source anchor, không được phép commit."""


class ExtractOrphanError(PKMError):
    """Extract không có source_id, vi phạm nguyên tắc source-grounded."""


class AppLockError(PKMError):
    """Không thể lấy lock — ứng dụng đang chạy ở instance khác."""


class AssetFileError(PKMError):
    """Lỗi liên quan đến file asset (thiếu, không ghi được, v.v.)."""


class ExportError(PKMError):
    """Lỗi khi export dữ liệu."""


class BackupError(PKMError):
    """Lỗi khi thực hiện backup hoặc restore."""


class SearchIndexError(PKMError):
    """Lỗi khi thao tác với search index."""
