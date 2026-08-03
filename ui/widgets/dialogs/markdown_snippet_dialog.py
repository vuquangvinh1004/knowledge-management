"""Dialogs cấu hình mẫu Markdown cho nút Chèn... trong workspace."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.markdown_snippet_service import MarkdownSnippet, MarkdownSnippetService


class MarkdownSnippetEditDialog(QDialog):
    """Dialog tạo mới hoặc chỉnh sửa một mẫu Markdown."""

    def __init__(self, snippet: MarkdownSnippet | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Định nghĩa đối tượng chèn")
        self.setMinimumSize(560, 420)
        self._snippet = snippet
        self._build_ui()
        if snippet is not None:
            self._edit_name.setText(snippet.name)
            self._edit_description.setPlainText(snippet.description)
            self._edit_template.setPlainText(snippet.template)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._edit_name = QLineEdit()
        self._edit_name.setPlaceholderText("Ví dụ: $$ Math $$")
        form.addRow("Tên", self._edit_name)

        self._edit_description = QPlainTextEdit()
        self._edit_description.setPlaceholderText("Mô tả ngắn về đối tượng sẽ chèn")
        self._edit_description.setFixedHeight(72)
        form.addRow("Mô tả", self._edit_description)

        self._edit_template = QPlainTextEdit()
        self._edit_template.setPlaceholderText("Nhập cấu trúc mẫu sẽ chèn vào editor")
        self._edit_template.setMinimumHeight(220)
        self._edit_template.setFont(_fixed_width_font())
        form.addRow("Cấu trúc mẫu", self._edit_template)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def name_text(self) -> str:
        return self._edit_name.text().strip()

    @property
    def description_text(self) -> str:
        return self._edit_description.toPlainText().strip()

    @property
    def template_text(self) -> str:
        return self._edit_template.toPlainText()

    def _accept(self) -> None:
        if not self.name_text:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên đối tượng.")
            return
        if not self.template_text.strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập cấu trúc mẫu.")
            return
        self.accept()


class MarkdownSnippetCustomizeDialog(QDialog):
    """Dialog quản lý danh sách mẫu hiển thị trong menu Chèn...."""

    _ROLE_SNIPPET_ID = Qt.ItemDataRole.UserRole

    def __init__(self, snippet_service: MarkdownSnippetService, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tùy chỉnh đối tượng chèn")
        self.setMinimumSize(760, 520)
        self._snippet_service = snippet_service
        self._catalog = self._snippet_service.list_available()
        self._visible_ids = [snippet.snippet_id for snippet in self._snippet_service.list_visible()]
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        helper = QLabel(
            "Chọn các đối tượng thường dùng để hiển thị trên menu Chèn.... "
            "Đánh dấu checkbox để hiển thị; bỏ dấu để ẩn khỏi danh sách sổ xuống."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        content = QHBoxLayout()

        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        self._list = QListWidget()
        self._list.itemChanged.connect(self._on_item_changed)
        self._list.currentItemChanged.connect(self._refresh_preview)
        left_lay.addWidget(self._list)

        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMinimumHeight(160)
        self._preview.setFont(_fixed_width_font())
        left_lay.addWidget(self._preview)
        content.addWidget(left, stretch=1)

        buttons_col = QVBoxLayout()
        self._btn_move_up = QPushButton("↑")
        self._btn_move_up.setToolTip("Đưa đối tượng đang chọn lên trên")
        self._btn_move_up.clicked.connect(self._move_selected_up)
        buttons_col.addWidget(self._btn_move_up)

        self._btn_move_down = QPushButton("↓")
        self._btn_move_down.setToolTip("Đưa đối tượng đang chọn xuống dưới")
        self._btn_move_down.clicked.connect(self._move_selected_down)
        buttons_col.addWidget(self._btn_move_down)

        self._btn_delete = QPushButton("Xóa")
        self._btn_delete.clicked.connect(self._delete_selected)
        buttons_col.addWidget(self._btn_delete)

        self._btn_edit = QPushButton("Sửa")
        self._btn_edit.clicked.connect(self._edit_selected)
        buttons_col.addWidget(self._btn_edit)

        self._btn_new = QPushButton("Tạo mới")
        self._btn_new.clicked.connect(self._create_new)
        buttons_col.addWidget(self._btn_new)
        buttons_col.addStretch()
        content.addLayout(buttons_col)
        layout.addLayout(content)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Lưu")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Hủy")
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_list(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for snippet in self._catalog:
            item = QListWidgetItem(snippet.name)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setData(self._ROLE_SNIPPET_ID, snippet.snippet_id)
            item.setToolTip(snippet.description or snippet.template)
            item.setCheckState(
                Qt.CheckState.Checked if snippet.snippet_id in self._visible_ids else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)
        self._list.blockSignals(False)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        self._refresh_preview()

    def _current_snippet(self) -> MarkdownSnippet | None:
        item = self._list.currentItem()
        if item is None:
            return None
        snippet_id = item.data(self._ROLE_SNIPPET_ID)
        for snippet in self._catalog:
            if snippet.snippet_id == snippet_id:
                return snippet
        return None

    def _refresh_preview(self) -> None:
        snippet = self._current_snippet()
        if snippet is None:
            self._preview.setPlainText("")
            return
        description = snippet.description or "(Không có mô tả)"
        built_in = "Mặc định" if snippet.built_in else "Tùy chỉnh"
        self._preview.setPlainText(
            f"Loại: {built_in}\n"
            f"Mô tả: {description}\n\n"
            f"Cấu trúc mẫu:\n{snippet.template}"
        )

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        snippet_id = item.data(self._ROLE_SNIPPET_ID)
        if item.checkState() == Qt.CheckState.Checked:
            if snippet_id not in self._visible_ids:
                self._visible_ids.append(snippet_id)
            return
        next_visible = [current_id for current_id in self._visible_ids if current_id != snippet_id]
        if next_visible != self._visible_ids:
            self._visible_ids = next_visible

    def _edit_selected(self) -> None:
        snippet = self._current_snippet()
        if snippet is None:
            return
        dlg = MarkdownSnippetEditDialog(snippet, self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        for index, current in enumerate(self._catalog):
            if current.snippet_id != snippet.snippet_id:
                continue
            self._catalog[index] = MarkdownSnippet(
                snippet_id=current.snippet_id,
                name=dlg.name_text,
                description=dlg.description_text,
                template=dlg.template_text,
                built_in=current.built_in,
            )
            break
        self._refresh_list()

    def _create_new(self) -> None:
        dlg = MarkdownSnippetEditDialog(parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        snippet_id = self._build_custom_snippet_id(dlg.name_text)
        self._catalog.append(
            MarkdownSnippet(
                snippet_id=snippet_id,
                name=dlg.name_text,
                description=dlg.description_text,
                template=dlg.template_text,
                built_in=False,
            )
        )
        if snippet_id not in self._visible_ids:
            self._visible_ids.append(snippet_id)
        self._refresh_list()

    def _delete_selected(self) -> None:
        snippet = self._current_snippet()
        if snippet is None:
            return
        if snippet.built_in:
            QMessageBox.information(
                self,
                "Không thể xóa",
                "Đối tượng mặc định không thể bị xóa. Bạn có thể bỏ chọn để ẩn khỏi menu Chèn....",
            )
            return
        answer = QMessageBox.question(
            self,
            "Xóa đối tượng",
            f"Bạn có chắc muốn xóa '{snippet.name}' khỏi danh sách khả dụng không?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._catalog = [item for item in self._catalog if item.snippet_id != snippet.snippet_id]
        self._visible_ids = [snippet_id for snippet_id in self._visible_ids if snippet_id != snippet.snippet_id]
        self._refresh_list()

    def _save_and_accept(self) -> None:
        self._rebuild_visible_ids_from_catalog_order()
        self._snippet_service.save_catalog(self._catalog)
        self._snippet_service.set_visible_ids(self._visible_ids)
        self.accept()

    def _move_selected_up(self) -> None:
        row = self._list.currentRow()
        if row <= 0:
            return
        self._catalog[row - 1], self._catalog[row] = self._catalog[row], self._catalog[row - 1]
        self._refresh_list()
        self._list.setCurrentRow(row - 1)

    def _move_selected_down(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._catalog) - 1:
            return
        self._catalog[row], self._catalog[row + 1] = self._catalog[row + 1], self._catalog[row]
        self._refresh_list()
        self._list.setCurrentRow(row + 1)

    def _rebuild_visible_ids_from_catalog_order(self) -> None:
        visible_set = set(self._visible_ids)
        self._visible_ids = [snippet.snippet_id for snippet in self._catalog if snippet.snippet_id in visible_set]

    def _build_custom_snippet_id(self, name: str) -> str:
        existing_ids = {snippet.snippet_id for snippet in self._catalog}
        base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "snippet-moi"
        snippet_id = base_slug
        suffix = 2
        while snippet_id in existing_ids:
            snippet_id = f"{base_slug}-{suffix}"
            suffix += 1
        return snippet_id


def _fixed_width_font() -> QFont:
    """Trả về font monospace khả dụng để hiển thị mẫu Markdown ổn định."""
    return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
