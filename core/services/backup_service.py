"""Service sao lưu và khôi phục database.

Chiến lược backup:
- Sao chép file .db sang thư mục backups với timestamp trong tên file.
- Không xóa backup cũ mà không có policy rõ ràng.
- Restore: sao chép backup đè lên DB hiện tại (cần restart app sau).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.utils.exceptions import BackupError
from core.utils.logger import get_logger

logger = get_logger()


@dataclass
class BackupEntry:
    """Thông tin một file backup."""

    path: Path
    created_at: datetime
    size_bytes: int

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / 1_048_576, 2)


class BackupService:
    """Tạo, liệt kê và khôi phục backup."""

    def __init__(self, db_path: Path, backups_dir: Path) -> None:
        """
        Args:
            db_path: Đường dẫn đến file database hiện tại.
            backups_dir: Thư mục lưu các file backup.
        """
        self._db_path = Path(db_path)
        self._backups_dir = Path(backups_dir)

    def create_backup(self, label: str = "") -> BackupEntry:
        """
        Tạo một backup mới.

        Args:
            label: Nhãn tùy chọn (được thêm vào tên file).

        Returns:
            BackupEntry chứa thông tin file backup vừa tạo.

        Raises:
            BackupError: Nếu sao lưu thất bại.
        """
        if not self._db_path.exists():
            raise BackupError(f"File database không tồn tại: {self._db_path}")

        self._backups_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        backup_name = f"research_pkm_backup_{timestamp}{suffix}.db"
        backup_path = self._backups_dir / backup_name

        try:
            shutil.copy2(self._db_path, backup_path)
        except OSError as exc:
            raise BackupError(f"Sao lưu thất bại: {exc}") from exc

        entry = BackupEntry(
            path=backup_path,
            created_at=now,
            size_bytes=backup_path.stat().st_size,
        )
        logger.info(f"Tạo backup: {backup_path} ({entry.size_mb} MB)")
        return entry

    def list_backups(self, newest_first: bool = True) -> list[BackupEntry]:
        """
        Liệt kê các file backup hiện có.

        Returns:
            Danh sách BackupEntry sắp xếp theo thời gian.
        """
        if not self._backups_dir.exists():
            return []

        entries = []
        for p in self._backups_dir.glob("research_pkm_backup_*.db"):
            stat = p.stat()
            entries.append(
                BackupEntry(
                    path=p,
                    created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    size_bytes=stat.st_size,
                )
            )
        entries.sort(key=lambda e: e.created_at, reverse=newest_first)
        return entries

    def restore_backup(self, backup_path: Path) -> None:
        """
        Khôi phục database từ file backup.

        Cảnh báo: Hàm này đè lên DB hiện tại. Nên đảm bảo app đã đóng session
        và có tạo backup mới trước khi restore.

        Args:
            backup_path: Đường dẫn tới file backup cần restore.

        Raises:
            BackupError: Nếu file backup không tồn tại hoặc restore thất bại.
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise BackupError(f"Không tìm thấy file backup: {backup_path}")

        # Tạo safety backup của DB hiện tại trước khi đè
        if self._db_path.exists():
            pre_restore_backup = self._db_path.parent / (
                self._db_path.stem + "_pre_restore.db"
            )
            shutil.copy2(self._db_path, pre_restore_backup)
            logger.info(f"Safety backup trước restore: {pre_restore_backup}")

        try:
            shutil.copy2(backup_path, self._db_path)
        except OSError as exc:
            raise BackupError(f"Restore thất bại: {exc}") from exc

        logger.info(f"Restore thành công từ: {backup_path}")

    def prune_old_backups(self, keep: int = 10) -> int:
        """
        Xóa các backup cũ nhất, giữ lại `keep` cái mới nhất.

        Args:
            keep: Số backup tối đa giữ lại.

        Returns:
            Số file backup đã xóa.
        """
        entries = self.list_backups(newest_first=True)
        to_delete = entries[keep:]
        for entry in to_delete:
            try:
                entry.path.unlink()
                logger.info(f"Xóa backup cũ: {entry.path}")
            except OSError as exc:
                logger.warning(f"Không thể xóa backup {entry.path}: {exc}")
        return len(to_delete)
