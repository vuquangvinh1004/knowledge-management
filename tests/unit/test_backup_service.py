"""Unit tests cho BackupService."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.services.backup_service import BackupService
from core.utils.exceptions import BackupError


@pytest.fixture
def fake_db(tmp_path: Path) -> Path:
    """Tạo file DB giả để test backup."""
    db_file = tmp_path / "test.db"
    db_file.write_bytes(b"SQLite DB content")
    return db_file


@pytest.fixture
def backups_dir(tmp_path: Path) -> Path:
    return tmp_path / "backups"


@pytest.fixture
def service(fake_db, backups_dir) -> BackupService:
    return BackupService(db_path=fake_db, backups_dir=backups_dir)


class TestCreateBackup:
    def test_creates_backup_file(self, service, backups_dir):
        entry = service.create_backup()
        assert entry.path.exists()
        assert backups_dir in entry.path.parents

    def test_backup_has_timestamp_in_name(self, service):
        entry = service.create_backup()
        assert "research_pkm_backup_" in entry.filename

    def test_backup_with_label(self, service):
        entry = service.create_backup(label="pre-upgrade")
        assert "pre-upgrade" in entry.filename

    def test_backup_size_nonzero(self, service):
        entry = service.create_backup()
        assert entry.size_bytes > 0

    def test_missing_db_raises(self, tmp_path, backups_dir):
        svc = BackupService(db_path=tmp_path / "nonexistent.db", backups_dir=backups_dir)
        with pytest.raises(BackupError):
            svc.create_backup()


class TestListBackups:
    def test_empty_when_no_backups(self, service):
        assert service.list_backups() == []

    def test_list_returns_entries(self, service):
        service.create_backup(label="a")
        service.create_backup(label="b")
        entries = service.list_backups()
        assert len(entries) == 2

    def test_list_newest_first(self, service):
        """list_backups() phải trả về danh sách theo thứ tự created_at giảm dần."""
        for i in range(3):
            service.create_backup(label=f"b{i}")

        newest = service.list_backups(newest_first=True)
        oldest = service.list_backups(newest_first=False)

        assert len(newest) == 3
        assert len(oldest) == 3

        # newest_first=True: created_at phải giảm dần (hoặc bằng nhau)
        dates_desc = [e.created_at for e in newest]
        assert all(dates_desc[i] >= dates_desc[i + 1] for i in range(len(dates_desc) - 1))

        # newest_first=False: created_at phải tăng dần (hoặc bằng nhau)
        dates_asc = [e.created_at for e in oldest]
        assert all(dates_asc[i] <= dates_asc[i + 1] for i in range(len(dates_asc) - 1))


class TestRestoreBackup:
    def test_restore_replaces_db(self, service, fake_db, backups_dir):
        entry = service.create_backup()
        # Thay đổi DB gốc
        fake_db.write_bytes(b"MODIFIED CONTENT")
        service.restore_backup(entry.path)
        # DB phải được khôi phục
        assert fake_db.read_bytes() == b"SQLite DB content"

    def test_restore_creates_pre_restore_safety(self, service, fake_db, backups_dir):
        entry = service.create_backup()
        service.restore_backup(entry.path)
        safety = fake_db.parent / (fake_db.stem + "_pre_restore.db")
        assert safety.exists()

    def test_restore_missing_backup_raises(self, service, tmp_path):
        with pytest.raises(BackupError):
            service.restore_backup(tmp_path / "missing_backup.db")


class TestPruneBackups:
    def test_prune_keeps_n_newest(self, service):
        for i in range(5):
            service.create_backup(label=f"b{i}")
        service.prune_old_backups(keep=3)
        assert len(service.list_backups()) == 3

    def test_prune_returns_count_deleted(self, service):
        for i in range(4):
            service.create_backup(label=f"c{i}")
        deleted = service.prune_old_backups(keep=2)
        assert deleted == 2
