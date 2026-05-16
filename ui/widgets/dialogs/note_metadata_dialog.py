"""Dialog chỉnh metadata cho note theo note_type."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from core.services.note_service import NoteService


class NoteMetadataDialog(QDialog):
    """Chỉnh `meta_json` cho note hiện tại."""

    def __init__(self, note_id: int, note_type: str, note_service: NoteService, parent=None) -> None:
        super().__init__(parent)
        self._note_id = note_id
        self._note_type = note_type
        self._note_service = note_service
        self.setWindowTitle("Metadata note")
        self.setMinimumWidth(460)
        self._build_ui()
        self._load_meta()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._form = QFormLayout()
        self._fields: dict[str, QLineEdit] = {}

        keys: list[tuple[str, str]]
        if self._note_type == "source_note":
            keys = [
                ("author", "Tác giả"),
                ("year", "Năm"),
                ("source_type", "Loại nguồn"),
                ("publication", "Nguồn xuất bản"),
                ("topic", "Chủ đề"),
            ]
        elif self._note_type == "concept_note":
            keys = [("domain", "Lĩnh vực"), ("keywords", "Từ khóa (phân tách bằng dấu ,)")]
        elif self._note_type == "board_note":
            keys = [
                ("board_type", "Loại board"),
                ("scope", "Phạm vi"),
                ("source_count", "Số lượng nguồn"),
            ]
        else:
            keys = [("focus", "Trọng tâm"), ("question", "Câu hỏi")]

        for key, label in keys:
            edit = QLineEdit()
            self._fields[key] = edit
            self._form.addRow(f"{label}:", edit)

        layout.addLayout(self._form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_meta(self) -> None:
        meta = self._note_service.get_meta(self._note_id)
        for key, edit in self._fields.items():
            value = meta.get(key)
            if isinstance(value, list):
                edit.setText(", ".join(str(v) for v in value))
            elif value is not None:
                edit.setText(str(value))

    def _save(self) -> None:
        payload = {k: e.text().strip() for k, e in self._fields.items() if e.text().strip()}
        try:
            self._note_service.update_meta(self._note_id, payload)
            self.accept()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Lỗi metadata", str(exc))
