"""Dialog tạo note mới theo loại note."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QStringListModel, Qt, QTimer
from PySide6.QtWidgets import (
    QCompleter,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
)

from core.services.note_service import NoteService


_TYPE_ITEMS = (
    ("concept_note", "Concept note"),
    ("synthesis_note", "Synthesis note"),
    ("board_note", "Board note"),
)


class NewNoteDialog(QDialog):
    """Dialog chọn loại note, tiêu đề và nội dung template."""

    def __init__(
        self,
        parent=None,
        *,
        notes_dir: Path | None = None,
        current_note_title: str | None = None,
        active_project_id: int | None = None,
        active_project_name: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tạo note mới")
        self.setMinimumSize(620, 500)
        self._notes_dir = Path(notes_dir) if notes_dir else None
        self._current_note_title = (current_note_title or "").strip()
        self._active_project_id = active_project_id
        self._active_project_name = (active_project_name or "").strip()
        self._known_wikilinks: list[tuple[str, str]] = []
        self._wikilink_display_to_title: dict[str, str] = {}
        self._last_auto_title = ""
        self._build_ui()
        self._setup_wikilink_features()
        self._apply_template(reset_title=True)

    @property
    def note_type(self) -> str:
        return self._combo_type.currentData()

    @property
    def title_text(self) -> str:
        return self._edit_title.text().strip()

    @property
    def content_text(self) -> str:
        return self._edit_content.toPlainText()

    @property
    def save_scope(self) -> str:
        """global | project"""
        return str(self._combo_scope.currentData()) if hasattr(self, "_combo_scope") else "global"

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self._combo_type = QComboBox()
        for note_type, label in _TYPE_ITEMS:
            self._combo_type.addItem(label, note_type)
        self._combo_type.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Loại note:", self._combo_type)

        self._edit_title = QLineEdit()
        self._edit_title.setPlaceholderText("Nhập tiêu đề note")
        self._edit_title.textChanged.connect(self._on_title_changed)
        form.addRow("Tiêu đề:", self._edit_title)

        self._combo_scope = QComboBox()
        self._combo_scope.addItem("Lưu vào Global", "global")
        if self._active_project_id is not None:
            name = self._active_project_name or f"Project #{self._active_project_id}"
            self._combo_scope.addItem(f"Lưu vào Project: {name}", "project")
            project_idx = self._combo_scope.findData("project")
            if project_idx >= 0:
                self._combo_scope.setCurrentIndex(project_idx)
            form.addRow("Phạm vi lưu:", self._combo_scope)

        layout.addLayout(form)

        self._lbl_warning = QLabel("")
        self._lbl_warning.setObjectName("note_dialog_warning")
        self._lbl_warning.setWordWrap(True)
        layout.addWidget(self._lbl_warning)

        self._edit_content = QPlainTextEdit()
        self._edit_content.setPlaceholderText("Template markdown sẽ hiển thị ở đây")
        layout.addWidget(self._edit_content, stretch=1)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Tạo note")
        self._button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    def _setup_wikilink_features(self) -> None:
        """Autocomplete wikilink trong ô nội dung của dialog."""
        self._wikilink_model = QStringListModel(self)
        self._wikilink_completer = QCompleter(self._wikilink_model, self)
        self._wikilink_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._wikilink_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._wikilink_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._wikilink_completer.setWidget(self._edit_content)
        self._wikilink_completer.activated.connect(self._on_wikilink_activated)

        self._edit_content.installEventFilter(self)
        self._wikilink_completer.popup().installEventFilter(self)

    @staticmethod
    def _build_wikilink_label(note_type: str, title: str) -> str:
        prefix_map = {
            "source_note": "source -",
            "concept_note": "concept -",
            "synthesis_note": "synthesis -",
            "board_note": "board -",
        }
        prefix = prefix_map.get(note_type, "note -")
        if title.lower().startswith(prefix):
            return title
        return f"{prefix} {title}"

    @staticmethod
    def _normalize_wikilink_target(raw_target: str) -> str:
        clean = raw_target.strip()
        lower = clean.lower()
        if lower.startswith("concept - "):
            return clean[len("concept - "):].strip()
        if lower.startswith("synthesis - "):
            stripped = clean[len("synthesis - "):].strip()
            return stripped if stripped.startswith("~") else f"~ {stripped}".strip()
        if lower.startswith("board - "):
            stripped = clean[len("board - "):].strip()
            return stripped if stripped.startswith("!") else f"! {stripped}".strip()
        return clean

    def _refresh_known_wikilinks(self) -> None:
        self._known_wikilinks = []
        if self._notes_dir is None:
            if self._current_note_title:
                self._known_wikilinks = [(self._current_note_title, "concept_note")]
            return

        try:
            notes = NoteService(self._notes_dir).list_all()
            entries: list[tuple[str, str]] = []
            for note in notes:
                title = (note.title or "").strip()
                note_type = str(getattr(note, "note_type", "concept_note"))
                if title:
                    entries.append((title, note_type))
            if self._current_note_title:
                entries.append((self._current_note_title, "concept_note"))

            dedup: dict[str, tuple[str, str]] = {}
            for title, note_type in entries:
                dedup[title.lower()] = (title, note_type)
            self._known_wikilinks = sorted(dedup.values(), key=lambda x: x[0].lower())
        except Exception:
            self._known_wikilinks = []

    def _current_wikilink_context(self) -> tuple[int, str] | None:
        cursor = self._edit_content.textCursor()
        pos = cursor.position()
        text = self._edit_content.toPlainText()
        if pos < 0 or pos > len(text):
            return None

        start_marker = text.rfind("[[", 0, pos)
        if start_marker < 0:
            return None
        end_marker = text.rfind("]]", 0, pos)
        if end_marker > start_marker:
            return None

        token = text[start_marker + 2:pos]
        if "\n" in token or "]" in token:
            return None
        return start_marker + 2, token

    def _update_wikilink_popup(self) -> None:
        if not self._edit_content.hasFocus():
            self._wikilink_completer.popup().hide()
            return

        ctx = self._current_wikilink_context()
        if ctx is None:
            self._wikilink_completer.popup().hide()
            return

        _, note_part = ctx
        prefix = note_part.strip().lower()
        self._refresh_known_wikilinks()

        matches: list[str] = []
        self._wikilink_display_to_title = {}
        for title, note_type in self._known_wikilinks:
            display = self._build_wikilink_label(note_type, title)
            if prefix in title.lower() or prefix in display.lower():
                matches.append(display)
                self._wikilink_display_to_title[display] = title

        if not matches:
            self._wikilink_completer.popup().hide()
            return

        self._wikilink_model.setStringList(matches)
        self._wikilink_completer.setCompletionPrefix(note_part)
        rect = self._edit_content.cursorRect()
        rect.setWidth(360)
        self._wikilink_completer.complete(rect)

    def _on_wikilink_activated(self, completion: str) -> None:
        mapped = self._wikilink_display_to_title.get(str(completion), str(completion))
        self._insert_wikilink_completion(self._normalize_wikilink_target(mapped))

    def _accept_current_wikilink_completion(self) -> bool:
        popup = self._wikilink_completer.popup()
        popup_index = popup.currentIndex()
        if popup_index.isValid():
            completion = str(popup_index.data()).strip()
        else:
            completion = ""
            if self._wikilink_model.rowCount() > 0:
                completion = str(self._wikilink_model.data(self._wikilink_model.index(0, 0))).strip()
        if completion:
            mapped = self._wikilink_display_to_title.get(completion, completion)
            self._insert_wikilink_completion(self._normalize_wikilink_target(mapped))
            return True
        return False

    def _insert_wikilink_completion(self, completion: str) -> None:
        ctx = self._current_wikilink_context()
        if ctx is None:
            return
        content_start, _token = ctx
        cursor = self._edit_content.textCursor()
        end_pos = cursor.position()
        cursor.setPosition(content_start)
        cursor.setPosition(end_pos, cursor.MoveMode.KeepAnchor)
        cursor.insertText(f"{completion}]] ")
        self._edit_content.setTextCursor(cursor)
        self._wikilink_completer.popup().hide()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if obj is self._wikilink_completer.popup():
                if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    return self._accept_current_wikilink_completion()
                if key == Qt.Key.Key_Escape:
                    self._wikilink_completer.popup().hide()
                    return True
                return False

            if obj is self._edit_content:
                if self._wikilink_completer.popup().isVisible():
                    if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        return self._accept_current_wikilink_completion()
                    if key == Qt.Key.Key_Escape:
                        self._wikilink_completer.popup().hide()
                        return True

                handled = super().eventFilter(obj, event)
                QTimer.singleShot(0, self._update_wikilink_popup)
                return handled

        return super().eventFilter(obj, event)

    def _default_title_for(self, note_type: str) -> str:
        if note_type == "concept_note":
            return "Khái niệm mới"
        if note_type == "synthesis_note":
            return "~ Câu hỏi tổng hợp mới"
        return "! Board tổng hợp mới"

    def _on_type_changed(self) -> None:
        self._apply_template(reset_title=True)

    def _on_title_changed(self) -> None:
        self._update_warning_label()

    def _apply_template(self, reset_title: bool = False) -> None:
        note_type = self.note_type
        if reset_title:
            suggested = self._default_title_for(note_type)
            self._edit_title.setText(suggested)
            self._last_auto_title = suggested

        template = NoteService.build_template(note_type, self.title_text or self._default_title_for(note_type))
        self._edit_content.setPlainText(template)
        self._update_warning_label()

    def _update_warning_label(self) -> None:
        warnings = NoteService.title_warnings(self.note_type, self.title_text)
        if warnings:
            self._lbl_warning.setText("Cảnh báo: " + " | ".join(warnings))
        else:
            self._lbl_warning.setText("")

    def _on_accept(self) -> None:
        title = self.title_text
        if not title:
            self._lbl_warning.setText("Cảnh báo: Vui lòng nhập tiêu đề note.")
            return

        if self.note_type == "synthesis_note" and not title.startswith("~"):
            title = f"~ {title}"
            self._edit_title.setText(title)
        if self.note_type == "board_note" and not title.startswith("!"):
            title = f"! {title}"
            self._edit_title.setText(title)

        if not self.content_text.strip():
            self._edit_content.setPlainText(NoteService.build_template(self.note_type, title))
        self.accept()
