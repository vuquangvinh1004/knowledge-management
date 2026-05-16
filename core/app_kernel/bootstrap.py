"""Khởi động ứng dụng theo thứ tự bắt buộc:
1. Đảm bảo data dirs tồn tại
2. Setup logger
3. Acquire app lock
4. Chạy startup checks
5. Khởi tạo database engine + session factory
6. Chạy migration
"""
from __future__ import annotations

from config.paths import ensure_data_dirs, LOGS_DIR, LOCK_FILE, DATABASE_FILE
from core.utils.logger import setup_logger, get_logger
from core.app_kernel.app_lock import AppLock
from core.app_kernel.startup_checks import run_all_checks
from core.app_kernel.shutdown_manager import ShutdownManager

_lock: AppLock | None = None
_shutdown_manager: ShutdownManager | None = None


def bootstrap() -> tuple[AppLock, ShutdownManager, list[str]]:
    """
    Khởi tạo toàn bộ cơ sở hạ tầng ứng dụng.

    Returns:
        (app_lock, shutdown_manager, missing_soft_deps) để caller quản lý vòng đời
        và hiển thị cảnh báo tính năng không khả dụng nếu cần.
    """
    global _lock, _shutdown_manager

    # 1. Tạo data dirs trước khi làm bất cứ điều gì
    ensure_data_dirs()

    # 2. Setup logger (sau khi log dir tồn tại)
    setup_logger(LOGS_DIR)
    logger = get_logger()
    logger.info("Bootstrap bắt đầu...")

    # 3. Acquire single-instance lock
    _lock = AppLock(LOCK_FILE)
    _lock.acquire()  # raise AppLockError nếu instance khác đang chạy

    # 4. Startup checks — trả về soft deps thiếu để UI hiển thị cảnh báo
    missing_soft = run_all_checks()

    # 5. Khởi tạo database engine + session factory
    from core.storage.connection import init_engine
    from core.storage.session import init_session_factory
    init_engine(DATABASE_FILE)
    init_session_factory()
    logger.info(f"Database engine sẵn sàng: {DATABASE_FILE}")

    # 6. Chạy migration để đảm bảo schema up-to-date
    from core.services.migration_service import run_migrations
    run_migrations()

    # 7. Tạo shutdown manager và đăng ký release lock
    _shutdown_manager = ShutdownManager()
    _shutdown_manager.register(_lock.release)

    logger.info("Bootstrap hoàn tất.")
    return _lock, _shutdown_manager, missing_soft


