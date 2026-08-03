"""Màn hình Thiết lập ứng dụng.

Cho phép người dùng xem và điều chỉnh: số lượng backup giữ lại,
thư mục xuất, rebuild FTS index, và reset cài đặt.
Business logic KHÔNG nằm ở đây — gọi qua SettingsService / BackupService.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.settings import DEFAULT_EDITOR_FONT_FAMILY, EDITOR_FONT_PRESETS
from config.settings import DEFAULT_EDITOR_FONT_SIZE

from core.utils.logger import get_logger

logger = get_logger()

_MODE_BADGE_BASE = (
    "padding: 2px 10px;"
    "border-radius: 10px;"
    "font-weight: 700;"
)


class SettingsView(QWidget):
    """Màn hình thiết lập ứng dụng."""

    backup_requested = Signal(int)
    rebuild_fts_requested = Signal()
    reset_settings_requested = Signal()
    normalize_source_titles_requested = Signal()
    refresh_wikilink_catalog_requested = Signal()
    cleanup_unused_notes_requested = Signal()
    audit_missing_source_note_files_requested = Signal()
    source_titles_normalized = Signal()
    wikilink_catalog_refreshed = Signal()
    editor_preferences_changed = Signal(str, bool, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        header = QLabel("Thiết lập")
        header.setObjectName("view_header")
        layout.addWidget(header)

        # --- Nhóm: Sao lưu ---
        grp_backup = QGroupBox("Sao lưu dữ liệu")
        form_backup = QFormLayout(grp_backup)
        form_backup.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self._spin_backup_keep = QSpinBox()
        self._spin_backup_keep.setRange(1, 100)
        self._spin_backup_keep.setValue(10)
        self._spin_backup_keep.setToolTip("Số lượng file backup được giữ lại tối đa")
        form_backup.addRow("Số bản sao lưu giữ lại:", self._spin_backup_keep)

        row_backup = QHBoxLayout()
        self._btn_backup_now = QPushButton("Sao lưu ngay")
        self._btn_backup_now.clicked.connect(self._request_backup)
        row_backup.addWidget(self._btn_backup_now)
        row_backup.addStretch()
        form_backup.addRow("", row_backup)
        layout.addWidget(grp_backup)

        # --- Nhóm: Bảo trì & tìm kiếm ---
        grp_search = QGroupBox("Bảo trì & tìm kiếm")
        form_search = QFormLayout(grp_search)

        row_fts = QHBoxLayout()
        self._btn_rebuild_fts = QPushButton("Xây dựng lại chỉ mục tìm kiếm")
        self._btn_rebuild_fts.setToolTip(
            "Xây dựng lại toàn bộ chỉ mục tìm kiếm từ cơ sở dữ liệu"
        )
        self._btn_rebuild_fts.clicked.connect(self._request_rebuild_fts)
        row_fts.addWidget(self._btn_rebuild_fts)
        self._lbl_fts_status = QLabel("")
        row_fts.addWidget(self._lbl_fts_status)
        row_fts.addStretch()
        form_search.addRow("Chỉ mục tìm kiếm FTS5:", row_fts)

        row_maintenance = QHBoxLayout()
        self._btn_normalize_source_titles = QPushButton("Chuẩn hóa tên source note")
        self._btn_normalize_source_titles.setToolTip(
            "Chạy lại tác vụ chuẩn hóa tên source note theo metadata hiện có (không thay đổi khi chạy nhiều lần)"
        )
        self._btn_normalize_source_titles.clicked.connect(self._request_normalize_source_titles)
        row_maintenance.addWidget(self._btn_normalize_source_titles)

        self._btn_refresh_wikilink_catalog = QPushButton("Làm mới danh sách wikilink")
        self._btn_refresh_wikilink_catalog.setToolTip(
            "Làm mới danh sách note cho popup [[wikilink]] và dọn bản ghi note/liên kết cũ"
        )
        self._btn_refresh_wikilink_catalog.clicked.connect(self._request_refresh_wikilink_catalog)
        row_maintenance.addWidget(self._btn_refresh_wikilink_catalog)

        self._btn_cleanup_unused_notes = QPushButton("Dọn ghi chú không còn dùng")
        self._btn_cleanup_unused_notes.setToolTip(
            "Xem trước danh sách ghi chú nghi ngờ không còn dùng, chọn giữ/xóa rồi mới áp dụng"
        )
        self._btn_cleanup_unused_notes.clicked.connect(self._request_cleanup_unused_notes)
        row_maintenance.addWidget(self._btn_cleanup_unused_notes)

        self._btn_audit_source_notes = QPushButton("Kiểm tra source note thiếu file")
        self._btn_audit_source_notes.setToolTip(
            "Quét chỉ đọc các source note có bản ghi trong cơ sở dữ liệu nhưng file Markdown không tồn tại"
        )
        self._btn_audit_source_notes.clicked.connect(self._request_audit_missing_source_note_files)
        row_maintenance.addWidget(self._btn_audit_source_notes)
        row_maintenance.addStretch()
        form_search.addRow("Bảo trì ghi chú:", row_maintenance)
        layout.addWidget(grp_search)

        # --- Nhóm: Trình soạn thảo ---
        grp_editor = QGroupBox("Trình soạn thảo")
        form_editor = QFormLayout(grp_editor)

        self._lbl_mode_info = QLabel("Chế độ: Toàn cục")
        self._lbl_mode_info.setObjectName("settings_mode_indicator")
        self._lbl_mode_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_mode_info.setMinimumWidth(160)
        self._apply_mode_badge_style("Chế độ: Toàn cục")
        form_editor.addRow("Chế độ hiện tại:", self._lbl_mode_info)

        self._combo_editor_font = QComboBox()
        self._combo_editor_font.setEditable(True)
        self._combo_editor_font.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo_editor_font.setToolTip(
            "Danh sách ưu tiên phông chữ monospace cho ghi chú, ví dụ: Cascadia Code, Consolas, Courier New, monospace"
        )
        self._combo_editor_font.addItems(list(EDITOR_FONT_PRESETS) + [
            "Consolas, Cascadia Code, monospace",
            "Consolas, Aptos Mono, monospace",
        ])
        self._combo_editor_font.currentTextChanged.connect(self._on_editor_preferences_changed)
        form_editor.addRow("Phông chữ:", self._combo_editor_font)

        self._chk_editor_ligatures = QCheckBox("Bật ký tự nối cho phông chữ")
        self._chk_editor_ligatures.toggled.connect(self._on_editor_preferences_changed)
        form_editor.addRow("Ký tự nối:", self._chk_editor_ligatures)

        self._spin_editor_font_size = QSpinBox()
        self._spin_editor_font_size.setRange(10, 24)
        self._spin_editor_font_size.setValue(DEFAULT_EDITOR_FONT_SIZE)
        self._spin_editor_font_size.setSuffix(" pt")
        self._spin_editor_font_size.setToolTip(
            "Điều chỉnh cỡ chữ vùng ghi chú và trình soạn thảo Markdown"
        )
        self._spin_editor_font_size.valueChanged.connect(self._on_editor_preferences_changed)
        form_editor.addRow("Cỡ chữ:", self._spin_editor_font_size)

        layout.addWidget(grp_editor)

        # --- Nhóm: Thông tin ---
        grp_info = QGroupBox("Thông tin ứng dụng")
        form_info = QFormLayout(grp_info)

        from core.utils.constants import APP_NAME, APP_VERSION
        form_info.addRow("Tên ứng dụng:", QLabel(APP_NAME))
        form_info.addRow("Phiên bản:", QLabel(APP_VERSION))

        from config.paths import DATABASE_FILE, DATA_DIR
        form_info.addRow("Cơ sở dữ liệu:", QLabel(str(DATABASE_FILE)))
        form_info.addRow("Thư mục dữ liệu:", QLabel(str(DATA_DIR)))
        layout.addWidget(grp_info)

        # --- Reset ---
        row_reset = QHBoxLayout()
        self._btn_reset = QPushButton("Khôi phục cài đặt mặc định")
        self._btn_reset.setToolTip("Đặt lại tất cả cài đặt về giá trị mặc định")
        self._btn_reset.clicked.connect(self._request_reset_settings)
        row_reset.addStretch()
        row_reset.addWidget(self._btn_reset)
        layout.addLayout(row_reset)

        layout.addStretch()

    def _load_settings(self) -> None:
        """Tải cài đặt hiện tại vào form."""
        try:
            from core.services.settings_service import SettingsService
            svc = SettingsService()
            self._spin_backup_keep.setValue(int(svc.get("backup_keep_count", 10)))
            font_family = str(svc.get("editor.fontFamily", DEFAULT_EDITOR_FONT_FAMILY))
            ligatures = self._coerce_bool(svc.get("editor.fontLigatures", True), default=True)
            font_size = self._coerce_font_size(
                svc.get("editor.fontSize", DEFAULT_EDITOR_FONT_SIZE),
                default=DEFAULT_EDITOR_FONT_SIZE,
            )

            self._combo_editor_font.blockSignals(True)
            self._chk_editor_ligatures.blockSignals(True)
            self._spin_editor_font_size.blockSignals(True)
            try:
                self._combo_editor_font.setCurrentText(font_family)
                self._chk_editor_ligatures.setChecked(ligatures)
                self._spin_editor_font_size.setValue(font_size)
            finally:
                self._combo_editor_font.blockSignals(False)
                self._chk_editor_ligatures.blockSignals(False)
                self._spin_editor_font_size.blockSignals(False)
        except Exception as exc:
            logger.warning(f"Không thể tải cài đặt: {exc}")

    def _on_editor_preferences_changed(self, *_args) -> None:
        """Lưu cài đặt editor font và phát signal để áp dụng ngay."""
        try:
            from core.services.settings_service import SettingsService

            svc = SettingsService()
            font_family = self._combo_editor_font.currentText().strip()
            if not font_family:
                font_family = DEFAULT_EDITOR_FONT_FAMILY
            ligatures = self._chk_editor_ligatures.isChecked()
            font_size = self._spin_editor_font_size.value()

            svc.set("editor.fontFamily", font_family)
            svc.set("editor.fontLigatures", ligatures)
            svc.set("editor.fontSize", font_size)
            self.editor_preferences_changed.emit(font_family, ligatures, font_size)
        except Exception as exc:
            logger.warning(f"Không thể lưu cài đặt editor font: {exc}")

    def reload_settings(self) -> None:
        """Tải lại settings từ storage vào form."""
        self._load_settings()

    def set_maintenance_buttons_enabled(self, enabled: bool) -> None:
        """Bật/tắt nhóm nút bảo trì để đồng bộ trạng thái bận/rảnh."""
        self._btn_backup_now.setEnabled(enabled)
        self._btn_rebuild_fts.setEnabled(enabled)
        self._btn_normalize_source_titles.setEnabled(enabled)
        self._btn_refresh_wikilink_catalog.setEnabled(enabled)
        self._btn_cleanup_unused_notes.setEnabled(enabled)
        self._btn_audit_source_notes.setEnabled(enabled)

    def set_fts_status(self, text: str) -> None:
        """Cập nhật nhãn trạng thái FTS."""
        self._lbl_fts_status.setText(text)

    @staticmethod
    def _coerce_bool(value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    @staticmethod
    def _coerce_font_size(value: object, default: int) -> int:
        if not isinstance(value, (int, float, str)):
            return default
        try:
            size = int(value)
        except (TypeError, ValueError):
            return default
        return max(10, min(24, size))

    def set_mode_text(self, text: str) -> None:
        """Cập nhật mode hiển thị trong tab Thiết lập."""
        self._lbl_mode_info.setText(text)
        self._apply_mode_badge_style(text)

    def _apply_mode_badge_style(self, mode_text: str) -> None:
        """Áp dụng màu badge cho chế độ: Toàn cục xanh lá, Dự án xanh dương."""
        if "Dự án" in mode_text or "Project" in mode_text:
            style = _MODE_BADGE_BASE + "background-color: #DBEAFE; color: #1E40AF;"
        else:
            style = _MODE_BADGE_BASE + "background-color: #DCFCE7; color: #166534;"
        self._lbl_mode_info.setStyleSheet(style)

    def _request_backup(self) -> None:
        self.backup_requested.emit(self._spin_backup_keep.value())

    def _request_rebuild_fts(self) -> None:
        self.rebuild_fts_requested.emit()

    def _request_reset_settings(self) -> None:
        self.reset_settings_requested.emit()

    def _request_normalize_source_titles(self) -> None:
        self.normalize_source_titles_requested.emit()

    def _request_refresh_wikilink_catalog(self) -> None:
        self.refresh_wikilink_catalog_requested.emit()

    def _request_cleanup_unused_notes(self) -> None:
        self.cleanup_unused_notes_requested.emit()

    def _request_audit_missing_source_note_files(self) -> None:
        self.audit_missing_source_note_files_requested.emit()

