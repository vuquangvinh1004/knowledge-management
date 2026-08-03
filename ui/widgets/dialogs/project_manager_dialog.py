"""Dialog quản lý Project mode.

Chức năng:
- Tạo / đổi tên / kết thúc / xóa mềm project.
- Kích hoạt project hoặc quay về Global mode.
- Thêm / xóa Global notes trong danh sách tham khảo của project.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QInputDialog,
    QFileDialog,
)

from core.services.note_service import NoteService
from core.services.project_service import ProjectService


class ProjectManagerDialog(QDialog):
    """Dialog quản lý project và notes tham chiếu."""

    project_context_changed = Signal()

    def __init__(self, parent=None, *, notes_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quản lý dự án nghiên cứu")
        self.setMinimumSize(920, 540)
        self._notes_dir = Path(notes_dir) if notes_dir else None
        self._project_service = ProjectService()
        self._note_service = NoteService(self._notes_dir) if self._notes_dir else None
        self._build_ui()
        self._reload_all()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        self._lbl_mode = QLabel("Chế độ hiện tại: Toàn cục")
        self._lbl_mode.setObjectName("project_mode_label")
        root.addWidget(self._lbl_mode)

        content = QHBoxLayout()
        content.setSpacing(10)

        left = QVBoxLayout()
        left.addWidget(QLabel("Danh sách dự án"))
        self._project_list = QListWidget()
        self._project_list.currentItemChanged.connect(self._on_project_changed)
        left.addWidget(self._project_list, stretch=1)

        left_actions = QHBoxLayout()
        self._btn_create = QPushButton("Tạo")
        self._btn_create.clicked.connect(self._on_create_project)
        left_actions.addWidget(self._btn_create)

        self._btn_rename = QPushButton("Đổi tên")
        self._btn_rename.clicked.connect(self._on_rename_project)
        left_actions.addWidget(self._btn_rename)

        self._btn_activate = QPushButton("Kích hoạt")
        self._btn_activate.clicked.connect(self._on_activate_project)
        left_actions.addWidget(self._btn_activate)
        left.addLayout(left_actions)

        left_actions2 = QHBoxLayout()
        self._btn_close = QPushButton("Kết thúc")
        self._btn_close.clicked.connect(self._on_close_project)
        left_actions2.addWidget(self._btn_close)

        self._btn_delete = QPushButton("Xóa mềm")
        self._btn_delete.clicked.connect(self._on_delete_project)
        left_actions2.addWidget(self._btn_delete)

        self._btn_package = QPushButton("Đóng gói")
        self._btn_package.clicked.connect(self._on_package_project)
        left_actions2.addWidget(self._btn_package)

        self._btn_global = QPushButton("Về toàn cục")
        self._btn_global.clicked.connect(self._on_global_mode)
        left_actions2.addWidget(self._btn_global)
        left.addLayout(left_actions2)

        content.addLayout(left, stretch=1)

        right = QHBoxLayout()

        col_global = QVBoxLayout()
        col_global.addWidget(QLabel("Ghi chú toàn cục"))
        self._global_notes = QListWidget()
        self._global_notes.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        col_global.addWidget(self._global_notes, stretch=1)
        right.addLayout(col_global, stretch=1)

        mid = QVBoxLayout()
        mid.addStretch()
        self._btn_add_ref = QPushButton("Thêm >>")
        self._btn_add_ref.clicked.connect(self._on_add_refs)
        mid.addWidget(self._btn_add_ref)
        self._btn_remove_ref = QPushButton("<< Gỡ")
        self._btn_remove_ref.clicked.connect(self._on_remove_refs)
        mid.addWidget(self._btn_remove_ref)
        mid.addStretch()
        right.addLayout(mid)

        col_refs = QVBoxLayout()
        col_refs.addWidget(QLabel("Ghi chú tham chiếu trong dự án"))
        self._ref_notes = QListWidget()
        self._ref_notes.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        col_refs.addWidget(self._ref_notes, stretch=1)
        right.addLayout(col_refs, stretch=1)

        content.addLayout(right, stretch=2)
        root.addLayout(content, stretch=1)

    def _selected_project_id(self) -> int | None:
        item = self._project_list.currentItem()
        if item is None:
            return None
        data = item.data(Qt.ItemDataRole.UserRole)
        return int(data) if data is not None else None

    def _reload_all(self) -> None:
        self._reload_projects()
        self._reload_global_notes()
        self._reload_project_refs()
        self._update_mode_label()

    def _reload_projects(self) -> None:
        current = self._selected_project_id()
        self._project_list.clear()
        for p in self._project_service.list_projects(include_closed=True):
            tag = "(đã kết thúc)" if p.status == "closed" else ""
            item = QListWidgetItem(f"{p.name} {tag}".strip())
            item.setData(Qt.ItemDataRole.UserRole, int(p.id))
            self._project_list.addItem(item)
            if current is not None and p.id == current:
                self._project_list.setCurrentItem(item)

    def _reload_global_notes(self) -> None:
        self._global_notes.clear()
        if self._note_service is None:
            return
        for note in self._note_service.list_global():
            item = QListWidgetItem(f"[{note.note_type}] {note.title}")
            item.setData(Qt.ItemDataRole.UserRole, int(note.id))
            self._global_notes.addItem(item)

    def _reload_project_refs(self) -> None:
        self._ref_notes.clear()
        pid = self._selected_project_id()
        if pid is None:
            return
        for note in self._project_service.list_note_refs(pid):
            item = QListWidgetItem(f"[{note.note_type}] {note.title}")
            item.setData(Qt.ItemDataRole.UserRole, int(note.id))
            self._ref_notes.addItem(item)

    def _update_mode_label(self) -> None:
        active_id = self._project_service.get_active_project_id()
        if active_id is None:
            self._lbl_mode.setText("Chế độ hiện tại: Toàn cục")
            return
        try:
            p = self._project_service.get_project(active_id)
            self._lbl_mode.setText(f"Chế độ hiện tại: Dự án - {p.name}")
        except Exception:
            self._lbl_mode.setText("Chế độ hiện tại: Toàn cục")

    def _on_project_changed(self, _current, _previous) -> None:
        self._reload_project_refs()

    def _on_create_project(self) -> None:
        name, ok = QInputDialog.getText(self, "Tạo dự án", "Tên dự án:")
        if not ok:
            return
        try:
            self._project_service.create_project(name)
            self._reload_projects()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_rename_project(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            return
        current = self._project_service.get_project(pid)
        name, ok = QInputDialog.getText(self, "Đổi tên dự án", "Tên mới:", text=current.name)
        if not ok:
            return
        try:
            self._project_service.rename_project(pid, name)
            self._reload_projects()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_activate_project(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            return
        try:
            self._project_service.activate_project(pid)
            self._update_mode_label()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_global_mode(self) -> None:
        self._project_service.deactivate_project()
        self._update_mode_label()
        self.project_context_changed.emit()

    def _on_close_project(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            return
        reply = QMessageBox.question(
            self,
            "Kết thúc dự án",
            "Đánh dấu dự án này là đã kết thúc?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._project_service.close_project(pid)
            self._reload_projects()
            self._update_mode_label()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_delete_project(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            return
        reply = QMessageBox.question(
            self,
            "Xóa mềm dự án",
            "Xóa mềm dự án này? Các ghi chú chỉ thuộc dự án sẽ trở về toàn cục.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._project_service.soft_delete_project(pid)
            self._reload_all()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_package_project(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            QMessageBox.information(self, "Đóng gói dự án", "Vui lòng chọn dự án trước.")
            return

        from config.paths import EXPORTS_DIR

        target = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục lưu gói dự án",
            str(EXPORTS_DIR),
        )
        if not target:
            return

        try:
            path = self._project_service.export_project_bundle(pid, Path(target))
            reply = QMessageBox.question(
                self,
                "Đóng gói thành công",
                f"Đã xuất gói dự án tại:\n{path}\n\nBạn có muốn mở thư mục này ngay không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi đóng gói", str(exc))

    def _on_add_refs(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            QMessageBox.information(self, "Thêm ghi chú", "Vui lòng chọn dự án trước.")
            return
        selected = self._global_notes.selectedItems()
        if not selected:
            return
        try:
            for item in selected:
                nid = item.data(Qt.ItemDataRole.UserRole)
                if nid is not None:
                    self._project_service.add_note_ref(pid, int(nid))
            self._reload_project_refs()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))

    def _on_remove_refs(self) -> None:
        pid = self._selected_project_id()
        if pid is None:
            return
        selected = self._ref_notes.selectedItems()
        if not selected:
            return
        try:
            for item in selected:
                nid = item.data(Qt.ItemDataRole.UserRole)
                if nid is not None:
                    self._project_service.remove_note_ref(pid, int(nid))
            self._reload_project_refs()
            self.project_context_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Lỗi", str(exc))
