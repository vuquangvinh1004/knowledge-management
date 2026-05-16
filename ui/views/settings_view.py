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
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.settings import DEFAULT_EDITOR_FONT_FAMILY, EDITOR_FONT_PRESETS

from core.utils.logger import get_logger

logger = get_logger()

_MODE_BADGE_BASE = (
    "padding: 2px 10px;"
    "border-radius: 10px;"
    "font-weight: 700;"
)


class SettingsView(QWidget):
    """Màn hình thiết lập ứng dụng."""

    source_titles_normalized = Signal()
    wikilink_catalog_refreshed = Signal()
    editor_preferences_changed = Signal(str, bool)

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
        self._btn_backup_now.clicked.connect(self._do_backup)
        row_backup.addWidget(self._btn_backup_now)
        row_backup.addStretch()
        form_backup.addRow("", row_backup)
        layout.addWidget(grp_backup)

        # --- Nhóm: Search ---
        grp_search = QGroupBox("Tìm kiếm")
        form_search = QFormLayout(grp_search)

        row_fts = QHBoxLayout()
        self._btn_rebuild_fts = QPushButton("Rebuild FTS Index")
        self._btn_rebuild_fts.setToolTip(
            "Xây dựng lại toàn bộ chỉ mục tìm kiếm từ database"
        )
        self._btn_rebuild_fts.clicked.connect(self._rebuild_fts)
        row_fts.addWidget(self._btn_rebuild_fts)
        self._lbl_fts_status = QLabel("")
        row_fts.addWidget(self._lbl_fts_status)
        row_fts.addStretch()
        form_search.addRow("Chỉ mục FTS5:", row_fts)

        row_maintenance = QHBoxLayout()
        self._btn_normalize_source_titles = QPushButton("Chuẩn hóa tên Source-note")
        self._btn_normalize_source_titles.setToolTip(
            "Chạy lại tác vụ chuẩn hóa tên Source-note theo metadata hiện có (idempotent)"
        )
        self._btn_normalize_source_titles.clicked.connect(self._normalize_source_note_titles)
        row_maintenance.addWidget(self._btn_normalize_source_titles)

        self._btn_refresh_wikilink_catalog = QPushButton("Làm mới danh sách Wikilink")
        self._btn_refresh_wikilink_catalog.setToolTip(
            "Làm mới catalog note cho popup [[wikilink]] và dọn bản ghi note/link stale"
        )
        self._btn_refresh_wikilink_catalog.clicked.connect(self._refresh_wikilink_catalog)
        row_maintenance.addWidget(self._btn_refresh_wikilink_catalog)

        self._btn_cleanup_unused_notes = QPushButton("Dọn ghi chú không còn dùng (có xem trước)")
        self._btn_cleanup_unused_notes.setToolTip(
            "Xem trước danh sách ghi chú nghi ngờ không còn dùng, chọn giữ/xóa rồi mới áp dụng"
        )
        self._btn_cleanup_unused_notes.clicked.connect(self._cleanup_unused_notes_with_preview)
        row_maintenance.addWidget(self._btn_cleanup_unused_notes)

        self._btn_audit_source_notes = QPushButton("Kiểm tra source-note lỗi file (chỉ xem)")
        self._btn_audit_source_notes.setToolTip(
            "Quét read-only các source-note có record DB nhưng file markdown không tồn tại"
        )
        self._btn_audit_source_notes.clicked.connect(self._audit_missing_source_note_files)
        row_maintenance.addWidget(self._btn_audit_source_notes)
        row_maintenance.addStretch()
        form_search.addRow("Bảo trì ghi chú:", row_maintenance)
        layout.addWidget(grp_search)

        # --- Nhóm: Trình soạn thảo ---
        grp_editor = QGroupBox("Trình soạn thảo")
        form_editor = QFormLayout(grp_editor)

        self._lbl_mode_info = QLabel("Mode: Global")
        self._lbl_mode_info.setObjectName("settings_mode_indicator")
        self._lbl_mode_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_mode_info.setMinimumWidth(160)
        self._apply_mode_badge_style("Mode: Global")
        form_editor.addRow("Mode hiện tại:", self._lbl_mode_info)

        self._combo_editor_font = QComboBox()
        self._combo_editor_font.setEditable(True)
        self._combo_editor_font.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._combo_editor_font.setToolTip(
            "Danh sách ưu tiên font monospace cho note, ví dụ: Cascadia Code, Consolas, Courier New, monospace"
        )
        self._combo_editor_font.addItems(list(EDITOR_FONT_PRESETS) + [
            "Consolas, Cascadia Code, monospace",
            "Consolas, Aptos Mono, monospace",
        ])
        self._combo_editor_font.currentTextChanged.connect(self._on_editor_preferences_changed)
        form_editor.addRow("Font editor:", self._combo_editor_font)

        self._chk_editor_ligatures = QCheckBox("Bật ligature cho font editor")
        self._chk_editor_ligatures.toggled.connect(self._on_editor_preferences_changed)
        form_editor.addRow("Ligatures:", self._chk_editor_ligatures)

        layout.addWidget(grp_editor)

        # --- Nhóm: Thông tin ---
        grp_info = QGroupBox("Thông tin ứng dụng")
        form_info = QFormLayout(grp_info)

        from core.utils.constants import APP_NAME, APP_VERSION
        form_info.addRow("Tên ứng dụng:", QLabel(APP_NAME))
        form_info.addRow("Phiên bản:", QLabel(APP_VERSION))

        from config.paths import DATABASE_FILE, DATA_DIR
        form_info.addRow("Database:", QLabel(str(DATABASE_FILE)))
        form_info.addRow("Thư mục dữ liệu:", QLabel(str(DATA_DIR)))
        layout.addWidget(grp_info)

        # --- Reset ---
        row_reset = QHBoxLayout()
        self._btn_reset = QPushButton("Khôi phục cài đặt mặc định")
        self._btn_reset.setToolTip("Đặt lại tất cả cài đặt về giá trị mặc định")
        self._btn_reset.clicked.connect(self._reset_settings)
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
            self._combo_editor_font.setCurrentText(font_family)
            ligatures = bool(svc.get("editor.fontLigatures", True))
            self._chk_editor_ligatures.setChecked(ligatures)
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

            svc.set("editor.fontFamily", font_family)
            svc.set("editor.fontLigatures", ligatures)
            self.editor_preferences_changed.emit(font_family, ligatures)
        except Exception as exc:
            logger.warning(f"Không thể lưu cài đặt editor font: {exc}")

    def set_mode_text(self, text: str) -> None:
        """Cập nhật mode hiển thị trong tab Thiết lập."""
        self._lbl_mode_info.setText(text)
        self._apply_mode_badge_style(text)

    def _apply_mode_badge_style(self, mode_text: str) -> None:
        """Áp dụng màu badge cho mode: Global xanh lá, Project xanh dương."""
        if "Project" in mode_text:
            style = _MODE_BADGE_BASE + "background-color: #DBEAFE; color: #1E40AF;"
        else:
            style = _MODE_BADGE_BASE + "background-color: #DCFCE7; color: #166534;"
        self._lbl_mode_info.setStyleSheet(style)

    def _do_backup(self) -> None:
        """Tạo backup ngay."""
        from config.paths import DATABASE_FILE, BACKUPS_DIR
        from core.services.backup_service import BackupService
        try:
            keep = self._spin_backup_keep.value()
            svc = BackupService(DATABASE_FILE, BACKUPS_DIR)
            entry = svc.create_backup()
            # Lưu cài đặt keep count
            from core.services.settings_service import SettingsService
            SettingsService().set("backup_keep_count", keep)
            QMessageBox.information(
                self, "Sao lưu thành công", f"Đã tạo backup:\n{entry.path}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi sao lưu", str(exc))

    def _rebuild_fts(self) -> None:
        """Rebuild FTS index."""
        self._lbl_fts_status.setText("Đang rebuild...")
        self._btn_rebuild_fts.setEnabled(False)
        try:
            from config.paths import DATABASE_FILE, NOTES_DIR
            from core.services.search_service import SearchService
            svc = SearchService(str(DATABASE_FILE), NOTES_DIR)
            count = svc.rebuild_all()
            self._lbl_fts_status.setText(f"✓ {count} items đã index")
        except Exception as exc:
            self._lbl_fts_status.setText("Lỗi rebuild!")
            logger.error(f"Rebuild FTS lỗi: {exc}")
        finally:
            self._btn_rebuild_fts.setEnabled(True)

    def _reset_settings(self) -> None:
        """Khôi phục cài đặt về mặc định."""
        reply = QMessageBox.question(
            self,
            "Khôi phục cài đặt",
            "Bạn có chắc muốn khôi phục tất cả cài đặt về mặc định?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core.services.settings_service import SettingsService
            SettingsService().reset_to_defaults()
            self._load_settings()
            QMessageBox.information(self, "Đã khôi phục", "Cài đặt đã được khôi phục về mặc định.")

    def _normalize_source_note_titles(self) -> None:
        """Chạy chuẩn hóa title source_note thủ công."""
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        self._btn_normalize_source_titles.setEnabled(False)
        try:
            updated = NoteService(NOTES_DIR).normalize_source_note_titles()
            QMessageBox.information(
                self,
                "Chuẩn hóa hoàn tất",
                f"Đã cập nhật {updated} source_note.",
            )
            self.source_titles_normalized.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            self._btn_normalize_source_titles.setEnabled(True)

    def _refresh_wikilink_catalog(self) -> None:
        """Làm mới catalog note để popup wikilink lấy dữ liệu sạch nhất."""
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        self._btn_refresh_wikilink_catalog.setEnabled(False)
        try:
            stats = NoteService(NOTES_DIR).refresh_wikilink_note_catalog()
            QMessageBox.information(
                self,
                "Đã làm mới catalog note",
                (
                    f"Note thiếu file đã soft-delete: {stats.get('soft_deleted_missing_file', 0)}\n"
                    f"Orphan stub note đã dọn: {stats.get('removed_orphan_stub_notes', 0)}\n"
                    f"Link stale đã dọn: {stats.get('removed_stale_links', 0)}"
                ),
            )
            self.wikilink_catalog_refreshed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            self._btn_refresh_wikilink_catalog.setEnabled(True)

    def _cleanup_unused_notes_with_preview(self) -> None:
        """Preview candidate note không còn dùng và chỉ dọn phần người dùng đã chọn."""
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService
        from ui.widgets.dialogs.note_cleanup_preview_dialog import NoteCleanupPreviewDialog

        self._btn_cleanup_unused_notes.setEnabled(False)
        try:
            svc = NoteService(NOTES_DIR)
            candidates = svc.get_unused_note_candidates()
            if not candidates:
                QMessageBox.information(
                    self,
                    "Không có note cần dọn",
                    "Hiện tại không phát hiện note không còn dùng.",
                )
                return

            dlg = NoteCleanupPreviewDialog(candidates, self)
            if dlg.exec() != dlg.DialogCode.Accepted:
                return

            selected_ids = dlg.selected_note_ids
            if not selected_ids:
                QMessageBox.information(
                    self,
                    "Chưa dọn note nào",
                    "Bạn đã chọn giữ lại toàn bộ note trong danh sách preview.",
                )
                return

            stats = svc.cleanup_unused_notes(selected_ids)
            QMessageBox.information(
                self,
                "Đã áp dụng dọn note",
                (
                    f"Đã soft-delete: {stats.get('soft_deleted', 0)} note\n"
                    f"Đã dọn stale links: {stats.get('removed_stale_links', 0)}"
                ),
            )
            self.wikilink_catalog_refreshed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            self._btn_cleanup_unused_notes.setEnabled(True)

    def _audit_missing_source_note_files(self) -> None:
        """Quét read-only source_note thiếu file và hiển thị báo cáo nhanh."""
        from config.paths import NOTES_DIR
        from core.services.note_service import NoteService

        self._btn_audit_source_notes.setEnabled(False)
        try:
            issues = NoteService(NOTES_DIR).audit_missing_source_note_files()
            if not issues:
                QMessageBox.information(
                    self,
                    "Kiểm tra source-note",
                    "Không phát hiện source-note nào bị thiếu file markdown.",
                )
                return

            preview_lines: list[str] = []
            for item in issues[:20]:
                code = item.get("source_code") or "----"
                sid = item.get("source_id") or "?"
                nid = item.get("note_id") or "?"
                title = item.get("note_title") or "(không tiêu đề)"
                preview_lines.append(f"- [{code}|source={sid}|note={nid}] {title}")

            more = ""
            if len(issues) > 20:
                more = f"\n... và {len(issues) - 20} mục khác."

            QMessageBox.warning(
                self,
                "Phát hiện source-note thiếu file",
                (
                    f"Tổng số phát hiện: {len(issues)}\n\n"
                    "Danh sách mẫu:\n"
                    f"{'\n'.join(preview_lines)}"
                    f"{more}\n\n"
                    "Đây là thao tác chỉ xem. Không có thay đổi dữ liệu."
                ),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            self._btn_audit_source_notes.setEnabled(True)

