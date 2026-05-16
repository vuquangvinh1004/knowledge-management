"""Entry point của ứng dụng Desktop Quản lý Kiến thức Nghiên cứu."""
from __future__ import annotations

import sys
from pathlib import Path


def _configure_windows_app_identity() -> None:
    """Đặt AppUserModelID để taskbar nhóm đúng app/icon trên Windows."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "research.pkm.desktop.app"
        )
    except Exception as exc:  # noqa: BLE001
        # Không chặn app khởi động nếu không set được app id,
        # nhưng cần log để có thể chẩn đoán khi đóng gói/release.
        try:
            from core.utils.logger import get_logger

            get_logger().warning("Không thể set AppUserModelID trên Windows: {}", exc)
        except Exception:
            pass


def _resolve_app_icon_path() -> Path | None:
    """Tìm file icon cho app ở cả chế độ dev và bản đóng gói."""
    runtime_dirs: list[Path] = []
    if getattr(sys, "frozen", False):
        runtime_dirs.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            runtime_dirs.append(Path(meipass))

    runtime_dirs.append(Path(__file__).resolve().parent)

    relative_candidates = [
        Path("assets") / "icons" / "QL_kien_thuc-icon.ico",
        Path("assets") / "icons" / "QL_kien_thuc_2_3D-icon.ico",
        Path("QL_kien_thuc-icon.ico"),
        Path("QL_kien_thuc_2_3D-icon.ico"),
    ]

    checked: set[Path] = set()
    for base_dir in runtime_dirs:
        for rel in relative_candidates:
            p = (base_dir / rel).resolve()
            if p in checked:
                continue
            checked.add(p)
            if p.exists():
                return p
    return None


def main() -> int:
    # Bootstrap trước khi khởi tạo QApplication
    try:
        from core.app_kernel.bootstrap import bootstrap
        app_lock, shutdown_manager, missing_soft = bootstrap()
    except Exception as exc:
        # Hiển thị QMessageBox cho MỌI loại lỗi khởi động
        # (kể cả ConfigError, AppLockError) — không để lỗi im lặng trên Windows
        from PySide6.QtWidgets import QApplication, QMessageBox
        from core.utils.exceptions import AppLockError

        _app = QApplication.instance() or QApplication(sys.argv)

        if isinstance(exc, AppLockError):
            title = "Ứng dụng đang chạy"
        else:
            title = "Lỗi khởi động"

        QMessageBox.critical(None, title, str(exc))
        return 1

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from ui.main_window import MainWindow
    from ui.styles.themes import apply_theme
    from config.settings import get_settings

    _configure_windows_app_identity()

    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setApplicationName("Research PKM")
    qt_app.setOrganizationName("PKM")

    from core.utils.logger import get_logger

    logger = get_logger()
    icon_path = _resolve_app_icon_path()
    if icon_path is not None:
        app_icon = QIcon(str(icon_path))
        if app_icon.isNull():
            logger.warning("Đã tìm thấy icon nhưng không load được: {}", icon_path)
            app_icon = None
        else:
            qt_app.setWindowIcon(app_icon)
    else:
        logger.warning("Không tìm thấy file icon ứng dụng. App sẽ dùng icon mặc định.")
        app_icon = None

    # Áp dụng theme từ settings
    theme = get_settings().get("theme", "light")
    apply_theme(qt_app, theme)

    window = MainWindow()
    if app_icon is not None:
        window.setWindowIcon(app_icon)
    window.show()

    # Hiển thị cảnh báo tính năng không khả dụng nếu có soft dep thiếu
    if missing_soft:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(
            window,
            "Tính năng bị giới hạn",
            "Một số tính năng không khả dụng do thiếu thư viện:\n• "
            + "\n• ".join(missing_soft)
            + "\n\nChạy `pip install -r requirements.txt` để cài đặt đầy đủ.",
        )

    exit_code = qt_app.exec()

    shutdown_manager.run()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

