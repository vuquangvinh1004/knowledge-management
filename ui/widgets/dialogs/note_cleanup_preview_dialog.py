"""Dialog preview danh sách note không còn dùng trước khi dọn."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NoteCleanupPreviewDialog(QDialog):
    """Preview candidate cleanup, cho phép bỏ chọn note muốn giữ lại."""

    def __init__(self, candidates: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candidates = candidates
        self._selected_note_ids: set[int] = set()
        self.setWindowTitle("Dọn note không còn dùng (có preview)")
        self.setMinimumWidth(760)
        self.setMinimumHeight(520)
        self._build_ui()
        self._load_candidates()

    @property
    def selected_note_ids(self) -> set[int]:
        return set(self._selected_note_ids)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        description = QLabel(
            "Danh sách dưới đây là note nghi ngờ không còn dùng. "
            "Bỏ chọn để giữ lại note, giữ chọn để dọn (soft-delete)."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self._chk_only_safe = QCheckBox("Chỉ chọn sẵn note auto-stub hoặc thiếu file")
        self._chk_only_safe.setChecked(True)
        self._chk_only_safe.stateChanged.connect(self._reload_checks)
        layout.addWidget(self._chk_only_safe)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list)

        action_row = QHBoxLayout()
        btn_select_all = QPushButton("Chọn tất cả")
        btn_select_all.clicked.connect(lambda: self._set_all_check_state(Qt.CheckState.Checked))
        action_row.addWidget(btn_select_all)

        btn_clear_all = QPushButton("Bỏ chọn tất cả")
        btn_clear_all.clicked.connect(lambda: self._set_all_check_state(Qt.CheckState.Unchecked))
        action_row.addWidget(btn_clear_all)
        action_row.addStretch()
        layout.addLayout(action_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Áp dụng dọn")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        buttons.accepted.connect(self._accept_with_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_candidates(self) -> None:
        self._list.clear()
        for item in self._candidates:
            note_id = int(item.get("note_id", 0))
            title = str(item.get("title", "")).strip() or "(không có tiêu đề)"
            note_type = str(item.get("note_type", ""))
            reason = str(item.get("reason", ""))
            incoming = int(item.get("incoming", 0))
            outgoing = int(item.get("outgoing", 0))
            is_auto_stub = bool(item.get("is_auto_stub", False))

            reason_text = "Thiếu file" if reason == "missing-file" else "Mồ côi, không có link"
            type_text = note_type.replace("_note", "")
            suffix = "auto-stub" if is_auto_stub else ""
            details = f"{title}  |  loại: {type_text}  |  lý do: {reason_text}"
            if suffix:
                details += f"  |  {suffix}"
            details += f"  |  in={incoming}, out={outgoing}"

            row = QListWidgetItem(details)
            row.setData(Qt.ItemDataRole.UserRole, note_id)
            row.setData(Qt.ItemDataRole.UserRole + 1, reason)
            row.setData(Qt.ItemDataRole.UserRole + 2, is_auto_stub)
            row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            row.setCheckState(Qt.CheckState.Unchecked)
            self._list.addItem(row)

        self._reload_checks()

    def _reload_checks(self) -> None:
        only_safe = self._chk_only_safe.isChecked()
        for i in range(self._list.count()):
            row = self._list.item(i)
            reason = str(row.data(Qt.ItemDataRole.UserRole + 1) or "")
            is_auto_stub = bool(row.data(Qt.ItemDataRole.UserRole + 2))
            should_check = (reason == "missing-file") or is_auto_stub
            if only_safe:
                row.setCheckState(Qt.CheckState.Checked if should_check else Qt.CheckState.Unchecked)

    def _set_all_check_state(self, state: Qt.CheckState) -> None:
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(state)

    def _accept_with_selection(self) -> None:
        selected_ids: set[int] = set()
        for i in range(self._list.count()):
            row = self._list.item(i)
            if row.checkState() == Qt.CheckState.Checked:
                selected_ids.add(int(row.data(Qt.ItemDataRole.UserRole)))
        self._selected_note_ids = selected_ids
        self.accept()
