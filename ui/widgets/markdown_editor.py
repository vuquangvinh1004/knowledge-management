"""Widget soạn thảo Markdown với autosave và chèn extract.

Business rules:
- Autosave debounce 2 giây sau lần thay đổi cuối.
- Ctrl+S kích hoạt manual save.
- Không gọi service trực tiếp trong UI — thông qua NoteService public API.
"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QEvent, QStringListModel, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeySequence,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.services.workspace_orchestrator import WorkspaceOrchestrator
from config.settings import DEFAULT_EDITOR_FONT_FAMILY
from core.utils.logger import get_logger

logger = get_logger()

_AUTOSAVE_DELAY_MS = 2000


class _MarkdownSyntaxHighlighter(QSyntaxHighlighter):
    """Tô màu syntax quan trọng: hashtag và wikilink."""

    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
    _TAG_PATTERN = re.compile(r"(?<!\w)#(?!\s)[\w\-]+", re.UNICODE)
    _WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]\n]+)\]\]")
    _MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]\n]+\]\([^\)\n]+\)")
    _BLOCKQUOTE_PATTERN = re.compile(r"^\s*>\s?.*")
    _CHECKLIST_PATTERN = re.compile(r"^\s*-\s\[(?: |x|X)\]\s?.*")
    _TABLE_ROW_PATTERN = re.compile(r"^\s*\|.*\|\s*$")
    _INLINE_MATH_PATTERN = re.compile(r"(?<!\\)(?<!\$)\$(?!\$)(.+?)(?<!\\)\$(?!\$)")
    _INLINE_MATH_PAREN_PATTERN = re.compile(r"\\\((.+?)\\\)")
    _DISPLAY_MATH_INLINE_DOLLAR_PATTERN = re.compile(r"(?<!\\)\$\$(.+?)(?<!\\)\$\$")
    _DISPLAY_MATH_INLINE_BRACKET_PATTERN = re.compile(r"\\\[(.+?)\\\]")
    _DISPLAY_BLOCK_DOLLAR_DELIM = re.compile(r"^\s*(?<!\\)\$\$\s*$")
    _DISPLAY_BLOCK_BRACKET_OPEN = re.compile(r"^\s*\\\[\s*$")
    _DISPLAY_BLOCK_BRACKET_CLOSE = re.compile(r"^\s*\\\]\s*$")
    _MATH_COMMAND_PATTERN = re.compile(r"\\[A-Za-z]+|\\.")
    _MATH_NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
    _MATH_OPERATOR_PATTERN = re.compile(
        r"(?:\+|\-|\*|/|=|<|>|\||&)|"
        r"(?:\\pm|\\times|\\cdot|\\div|\\leq|\\geq|\\neq|\\approx|\\to|\\in)"
    )
    _MATH_BRACKET_PATTERN = re.compile(r"[{}()\[\]]")
    _MATH_DELIMITER_PATTERN = re.compile(r"\$\$|\$|\\\(|\\\)|\\\[|\\\]")

    _STATE_NONE = 0
    _STATE_DISPLAY_MATH_DOLLAR = 1
    _STATE_DISPLAY_MATH_BRACKET = 2

    def __init__(self, parent) -> None:
        super().__init__(parent)

        # Kích thước font: base=11pt, H1=14(+3), H2=13(+2), H3=12(+1), H4-H6=11(+0)
        _BASE_PT = 11

        def _hfmt(size: int) -> QTextCharFormat:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#5B4B8A"))
            fmt.setFontWeight(700)
            fmt.setFontPointSize(size)
            return fmt

        self._heading_formats: dict[int, QTextCharFormat] = {
            1: _hfmt(_BASE_PT + 3),
            2: _hfmt(_BASE_PT + 2),
            3: _hfmt(_BASE_PT + 1),
            4: _hfmt(_BASE_PT),
            5: _hfmt(_BASE_PT),
            6: _hfmt(_BASE_PT),
        }

        self._tag_format = QTextCharFormat()
        self._tag_format.setForeground(QColor("#1D4ED8"))
        self._tag_format.setFontWeight(700)

        self._wikilink_format = QTextCharFormat()
        self._wikilink_format.setForeground(QColor("#0F766E"))
        self._wikilink_format.setFontItalic(True)
        self._wikilink_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)

        self._markdown_link_format = QTextCharFormat()
        self._markdown_link_format.setForeground(QColor("#1D4ED8"))
        self._markdown_link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        self._blockquote_line_format = QTextCharFormat()
        self._blockquote_line_format.setForeground(QColor("#1F3B73"))
        self._blockquote_line_format.setBackground(QColor("#DCFCE7"))

        self._table_line_format = QTextCharFormat()
        self._table_line_format.setBackground(QColor("#ECEFF3"))

        self._init_math_formats()

    def _init_math_formats(self) -> None:
        """Tạo palette math theo kiểu code editor, tự thích nghi dark/light."""
        app = QApplication.instance()
        if isinstance(app, QApplication):
            base = app.palette().base().color()
        else:
            base = QColor("#FFFFFF")
        is_dark = base.lightness() < 128

        if is_dark:
            bg_inline = QColor("#1E293B")
            bg_display = QColor("#172554")
            fg_base = QColor("#E2E8F0")
            fg_command = QColor("#86EFAC")
            fg_number = QColor("#FDE68A")
            fg_operator = QColor("#FCA5A5")
            fg_bracket = QColor("#93C5FD")
            fg_delim = QColor("#C4B5FD")
        else:
            bg_inline = QColor("#F3F7FF")
            bg_display = QColor("#E5EEFF")
            fg_base = QColor("#111827")
            fg_command = QColor("#166534")
            fg_number = QColor("#92400E")
            fg_operator = QColor("#B42318")
            fg_bracket = QColor("#1D4ED8")
            fg_delim = QColor("#6D28D9")

        self._math_inline_format = QTextCharFormat()
        self._math_inline_format.setForeground(fg_base)
        self._math_inline_format.setBackground(bg_inline)
        self._math_inline_format.setFontFamily("Roboto Mono")

        self._math_display_format = QTextCharFormat()
        self._math_display_format.setForeground(fg_base)
        self._math_display_format.setBackground(bg_display)
        self._math_display_format.setFontFamily("Roboto Mono")
        self._math_display_format.setFontWeight(600)

        self._math_command_format = QTextCharFormat(self._math_display_format)
        self._math_command_format.setForeground(fg_command)

        self._math_number_format = QTextCharFormat(self._math_display_format)
        self._math_number_format.setForeground(fg_number)

        self._math_operator_format = QTextCharFormat(self._math_display_format)
        self._math_operator_format.setForeground(fg_operator)

        self._math_bracket_format = QTextCharFormat(self._math_display_format)
        self._math_bracket_format.setForeground(fg_bracket)

        self._math_delimiter_format = QTextCharFormat(self._math_display_format)
        self._math_delimiter_format.setForeground(fg_delim)

    def _highlight_math_span(self, text: str, start: int, end: int, is_display: bool) -> None:
        """Highlight token math trong một đoạn [start, end) của block hiện tại."""
        if start >= end:
            return

        base_format = self._math_display_format if is_display else self._math_inline_format
        self.setFormat(start, end - start, base_format)

        segment = text[start:end]

        for match in self._MATH_COMMAND_PATTERN.finditer(segment):
            self.setFormat(start + match.start(), match.end() - match.start(), self._math_command_format)

        for match in self._MATH_NUMBER_PATTERN.finditer(segment):
            self.setFormat(start + match.start(), match.end() - match.start(), self._math_number_format)

        for match in self._MATH_OPERATOR_PATTERN.finditer(segment):
            self.setFormat(start + match.start(), match.end() - match.start(), self._math_operator_format)

        for match in self._MATH_BRACKET_PATTERN.finditer(segment):
            self.setFormat(start + match.start(), match.end() - match.start(), self._math_bracket_format)

        for match in self._MATH_DELIMITER_PATTERN.finditer(segment):
            self.setFormat(start + match.start(), match.end() - match.start(), self._math_delimiter_format)

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        prev_state = self.previousBlockState()
        if prev_state == self._STATE_DISPLAY_MATH_DOLLAR:
            self._highlight_math_span(text, 0, len(text), is_display=True)
            if self._DISPLAY_BLOCK_DOLLAR_DELIM.match(text):
                self.setCurrentBlockState(self._STATE_NONE)
            else:
                self.setCurrentBlockState(self._STATE_DISPLAY_MATH_DOLLAR)
            return

        if prev_state == self._STATE_DISPLAY_MATH_BRACKET:
            self._highlight_math_span(text, 0, len(text), is_display=True)
            if self._DISPLAY_BLOCK_BRACKET_CLOSE.match(text):
                self.setCurrentBlockState(self._STATE_NONE)
            else:
                self.setCurrentBlockState(self._STATE_DISPLAY_MATH_BRACKET)
            return

        self.setCurrentBlockState(self._STATE_NONE)

        if self._DISPLAY_BLOCK_DOLLAR_DELIM.match(text):
            self._highlight_math_span(text, 0, len(text), is_display=True)
            self.setCurrentBlockState(self._STATE_DISPLAY_MATH_DOLLAR)
            return

        if self._DISPLAY_BLOCK_BRACKET_OPEN.match(text):
            self._highlight_math_span(text, 0, len(text), is_display=True)
            self.setCurrentBlockState(self._STATE_DISPLAY_MATH_BRACKET)
            return

        heading_match = self._HEADING_PATTERN.match(text)
        if heading_match:
            level = len(heading_match.group(1))
            fmt = self._heading_formats.get(level, self._heading_formats[6])
            self.setFormat(0, len(text), fmt)

        if self._BLOCKQUOTE_PATTERN.match(text):
            self.setFormat(0, len(text), self._blockquote_line_format)

        if self._TABLE_ROW_PATTERN.match(text):
            self.setFormat(0, len(text), self._table_line_format)

        for match in self._TAG_PATTERN.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self._tag_format)

        for match in self._WIKILINK_PATTERN.finditer(text):
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self._wikilink_format,
            )

        for match in self._MARKDOWN_LINK_PATTERN.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self._markdown_link_format)

        for match in self._DISPLAY_MATH_INLINE_DOLLAR_PATTERN.finditer(text):
            self._highlight_math_span(text, match.start(), match.end(), is_display=True)

        for match in self._DISPLAY_MATH_INLINE_BRACKET_PATTERN.finditer(text):
            self._highlight_math_span(text, match.start(), match.end(), is_display=True)

        for match in self._INLINE_MATH_PATTERN.finditer(text):
            self._highlight_math_span(text, match.start(), match.end(), is_display=False)

        for match in self._INLINE_MATH_PAREN_PATTERN.finditer(text):
            self._highlight_math_span(text, match.start(), match.end(), is_display=False)


class MarkdownEditorWidget(QWidget):
    """
    Editor Markdown đơn giản được gắn với một Note cụ thể.

    Signals:
        content_changed: Phát khi nội dung bị chỉnh sửa (chưa lưu).
        note_saved: Phát sau khi lưu thành công (note_id).
    """

    content_changed = Signal()
    note_saved = Signal(int)  # note_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from config.paths import ASSETS_DIR, NOTES_DIR

        self._orchestrator = WorkspaceOrchestrator(NOTES_DIR, ASSETS_DIR)
        self._note_id: int | None = None
        self._current_note_type: str | None = None
        self._current_source_id: int | None = None
        self._is_modified = False
        self._notes_dir: Path | None = None
        self._known_tags: set[str] = set()
        self._known_wikilinks: list[tuple[str, str]] = []
        self._wikilink_display_to_title: dict[str, str] = {}
        self._show_note_actions = True
        self._build_ui()
        self._setup_autosave()
        self._setup_shortcuts()
        self._setup_hashtag_features()
        self._setup_wikilink_features()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tiêu đề bar
        header = QWidget()
        header.setObjectName("editor_header")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(8, 4, 8, 4)

        self._lbl_title = QLabel("(Chưa mở ghi chú)")
        self._lbl_title.setObjectName("editor_title")
        self._lbl_save_status = QLabel("")
        self._lbl_save_status.setObjectName("editor_save_status")
        self._lbl_save_status.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._btn_tags = QPushButton("Tags")
        self._btn_tags.setObjectName("editor_tags_btn")
        self._btn_tags.setToolTip("Quản lý nhãn của ghi chú này")
        self._btn_tags.setEnabled(False)
        self._btn_tags.clicked.connect(self._open_tags_dialog)

        self._btn_wikilinks = QPushButton("Wikilinks")
        self._btn_wikilinks.setObjectName("editor_wikilinks_btn")
        self._btn_wikilinks.setToolTip("nguyên lý các [[wikilink]] của ghi chú này")
        self._btn_wikilinks.setEnabled(False)
        self._btn_wikilinks.clicked.connect(self._open_wikilinks_dialog)

        self._btn_new_note = QPushButton("Note mới")
        self._btn_new_note.setObjectName("editor_new_note_btn")
        self._btn_new_note.setToolTip("Tạo concept/synthesis/board note")
        self._btn_new_note.setEnabled(False)
        self._btn_new_note.clicked.connect(self._open_new_note_dialog)

        self._btn_meta = QPushButton("Metadata")
        self._btn_meta.setObjectName("editor_meta_btn")
        self._btn_meta.setToolTip("Chỉnh metadata theo loại note")
        self._btn_meta.setEnabled(False)
        self._btn_meta.clicked.connect(self._open_metadata_dialog)

        self._lbl_backlinks = QLabel("")
        self._lbl_backlinks.setObjectName("editor_backlinks")
        self._lbl_backlinks.setToolTip("Số ghi chú khác liên kết đến ghi chú này")

        self._lbl_quality_warning = QLabel("")
        self._lbl_quality_warning.setObjectName("editor_quality_warning")
        self._lbl_quality_warning.setWordWrap(True)

        h_lay.addWidget(self._lbl_title)
        h_lay.addStretch()
        h_lay.addWidget(self._btn_new_note)
        h_lay.addWidget(self._btn_meta)
        h_lay.addWidget(self._lbl_backlinks)
        h_lay.addWidget(self._btn_wikilinks)
        h_lay.addWidget(self._btn_tags)
        h_lay.addWidget(self._lbl_save_status)
        layout.addWidget(header)
        layout.addWidget(self._lbl_quality_warning)

        # Editor
        self._editor = QPlainTextEdit()
        self._editor.setObjectName("markdown_editor")
        self._apply_editor_font()
        self._editor.setPlaceholderText(
            "Ghi chú Markdown của bạn ở đây...\n\n"
            "Hỗ trợ [[wikilink]], # heading, #hashtag, > blockquote, | bảng |\n"
            "Quy ước: heading dùng '# ' (có khoảng trắng), hashtag dùng '#tag'."
        )
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Empty state
        self._empty_label = QLabel(
            "Chưa có ghi chú nào được mở.\nMở PDF từ Thư viện để bắt đầu."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setObjectName("empty_state_message")
        layout.addWidget(self._empty_label)

        self._set_note_loaded(False)

    def _setup_autosave(self) -> None:
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(_AUTOSAVE_DELAY_MS)
        self._autosave_timer.timeout.connect(self._do_save)

    def _setup_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._do_save)
        new_note_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_note_shortcut.activated.connect(self._open_new_note_dialog)

    def _setup_hashtag_features(self) -> None:
        """Thiết lập autocomplete và tô màu hashtag kiểu Obsidian."""
        self._hashtag_model = QStringListModel(self)
        self._hashtag_completer = QCompleter(self._hashtag_model, self)
        self._hashtag_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._hashtag_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._hashtag_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._hashtag_completer.setWidget(self._editor)
        self._hashtag_completer.activated.connect(self._insert_hashtag_completion)

        self._editor.installEventFilter(self)
        # Cài event filter lên popup để bắt phím Tab khi popup đang mở
        self._hashtag_completer.popup().installEventFilter(self)
        self._syntax_highlighter = _MarkdownSyntaxHighlighter(self._editor.document())
        self._editor.cursorPositionChanged.connect(self._refresh_blockquote_overlays)

    def _setup_wikilink_features(self) -> None:
        """Thiết lập autocomplete cho [[wikilink]]."""
        self._wikilink_model = QStringListModel(self)
        self._wikilink_completer = QCompleter(self._wikilink_model, self)
        self._wikilink_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._wikilink_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._wikilink_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._wikilink_completer.setWidget(self._editor)
        self._wikilink_completer.activated.connect(self._on_wikilink_activated)
        self._wikilink_completer.popup().installEventFilter(self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_note(self, note_id: int, notes_dir: Path) -> None:
        """
        Tải nội dung note từ file vào editor.

        Args:
            note_id: ID của note trong DB.
            notes_dir: Thư mục chứa các file .md.
        """
        from core.services.note_service import NoteService

        self._notes_dir = notes_dir
        svc = NoteService(notes_dir)
        try:
            note = svc.get_by_id(note_id)
            content = svc.read_content(note_id)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Không thể tải note id={note_id}: {exc}")
            return

        self._note_id = note_id
        self._current_note_type = str(note.note_type)
        source_id_raw = getattr(note, "source_id", None)
        self._current_source_id = source_id_raw if isinstance(source_id_raw, int) else None
        self._lbl_title.setText(str(note.title))
        self._editor.blockSignals(True)
        self._editor.setPlainText(content)
        self._editor.blockSignals(False)
        self._is_modified = False
        self._lbl_save_status.setText("Đã lưu")
        self._btn_tags.setEnabled(self._show_note_actions)
        self._btn_wikilinks.setEnabled(self._show_note_actions)
        self._btn_new_note.setEnabled(self._show_note_actions)
        self._btn_meta.setEnabled(self._show_note_actions)
        self._set_note_loaded(True)
        self._refresh_known_tags()
        self._refresh_known_wikilinks()
        self._refresh_backlinks()
        self._refresh_quality_warning()
        self._refresh_blockquote_overlays()

    def set_note_actions_visible(self, visible: bool) -> None:
        """Hiện/ẩn nhóm nút thao tác note ở header editor."""
        self._show_note_actions = visible
        self._btn_tags.setVisible(visible)
        self._btn_wikilinks.setVisible(visible)
        self._btn_new_note.setVisible(visible)
        self._btn_meta.setVisible(visible)
        self._lbl_backlinks.setVisible(visible)
        self._lbl_quality_warning.setVisible(visible)
        if not visible:
            self._btn_tags.setEnabled(False)
            self._btn_wikilinks.setEnabled(False)
            self._btn_new_note.setEnabled(False)
            self._btn_meta.setEnabled(False)

    def unload_note(self) -> None:
        """Thoát khỏi note hiện tại (lưu trước nếu còn thay đổi)."""
        if self._is_modified:
            self._do_save()
        self._note_id = None
        self._current_note_type = None
        self._current_source_id = None
        self._editor.clear()
        self._lbl_title.setText("(Chưa mở ghi chú)")
        self._lbl_save_status.setText("")
        self._lbl_backlinks.setText("")
        self._lbl_quality_warning.setText("")
        self._btn_tags.setEnabled(False)
        self._btn_wikilinks.setEnabled(False)
        self._btn_new_note.setEnabled(False)
        self._btn_meta.setEnabled(False)
        self._set_note_loaded(False)
        self._known_tags.clear()
        self._known_wikilinks.clear()
        self._wikilink_display_to_title.clear()
        self._hashtag_completer.popup().hide()
        self._wikilink_completer.popup().hide()
        self._editor.setExtraSelections([])

    def get_content(self) -> str:
        """Nội dung Markdown hiện tại trong editor."""
        return self._editor.toPlainText()

    def enable_scratch_mode(self, title: str = "Soạn thảo tạm thời (Markdown)") -> None:
        """Bật editor ở chế độ soạn thảo file tạm, không gắn note DB."""
        from config.paths import NOTES_DIR

        self._autosave_timer.stop()
        self._note_id = None
        self._current_note_type = None
        self._current_source_id = None
        self._notes_dir = NOTES_DIR
        self.set_note_actions_visible(False)
        self._set_note_loaded(True)
        self._lbl_title.setText(title)
        self._lbl_save_status.setText("")
        self._lbl_backlinks.setText("")
        self._lbl_quality_warning.setText("")
        self._refresh_known_tags()
        self._refresh_known_wikilinks()
        self.mark_saved(show_saved_badge=False)

    def set_markdown_content(self, content: str) -> None:
        """Gán nội dung Markdown trực tiếp cho editor."""
        self._editor.blockSignals(True)
        self._editor.setPlainText(content)
        self._editor.blockSignals(False)
        self._refresh_blockquote_overlays()
        self.mark_saved(show_saved_badge=False)

    def set_editor_title(self, title: str) -> None:
        """Đổi nhãn tiêu đề trên header của editor."""
        self._lbl_title.setText(title)

    def mark_saved(self, show_saved_badge: bool = True) -> None:
        """Đánh dấu trạng thái editor đã lưu."""
        self._is_modified = False
        self._lbl_save_status.setText("Đã lưu" if show_saved_badge else "")

    def set_save_status_text(self, text: str) -> None:
        """Gán trạng thái lưu trên header editor."""
        self._lbl_save_status.setText(text)

    def has_unsaved_changes(self) -> bool:
        """Cho biết editor có thay đổi chưa lưu hay không."""
        return self._is_modified

    def insert_extract(
        self,
        text: str,
        anchor: str,
        source_code: str | None = None,
        page_no: int | None = None,
        extract_id: int | None = None,
        rect: tuple | None = None,
    ) -> None:
        """
        Chèn khối trích dẫn văn bản vào vị trí con trỏ.

        Format mới:
            > Nội dung trích xuất
            >
            > Nguồn: AA01_2_text-12 (90.67,459.33,543.33,548.67)

        Nếu thiếu source_code/page_no/extract_id, fallback về anchor URL cũ.
        """
        lines = [f"> {line}" for line in text.strip().splitlines()] or ["> "]
        lines.append(">")
        if source_code and page_no is not None and extract_id is not None:
            rect_str = (
                f"({rect[0]:.2f},{rect[1]:.2f},{rect[2]:.2f},{rect[3]:.2f})"
                if rect else ""
            )
            citation = f"Nguồn: {source_code}_{page_no}_text-{extract_id}"
            if rect_str:
                citation += f" {rect_str}"
            lines.append(f"> {citation}")
        else:
            lines.append(f"> — [{anchor}]({anchor})")
        block = "\n".join(lines) + "\n\n"
        self._insert_at_cursor(block)

    def insert_table(
        self,
        table_md: str,
        anchor: str,
        source_code: str | None = None,
        page_no: int | None = None,
        extract_id: int | None = None,
        rect: tuple | None = None,
    ) -> None:
        """Chèn bảng Markdown và dòng nguồn vào editor.

        Format mới:
            | bảng |
            > Nguồn: AA01_2_table-12 (90.67,459.33,543.33,548.67)
        """
        if source_code and page_no is not None and extract_id is not None:
            rect_str = (
                f"({rect[0]:.2f},{rect[1]:.2f},{rect[2]:.2f},{rect[3]:.2f})"
                if rect else ""
            )
            citation = f"Nguồn: {source_code}_{page_no}_table-{extract_id}"
            if rect_str:
                citation += f" {rect_str}"
            block = f"\n{table_md}\n\n> {citation}\n\n"
        else:
            block = f"\n{table_md}\n\n> Nguồn: [{anchor}]({anchor})\n\n"
        self._insert_at_cursor(block)

    def insert_asset_ref(self, asset_path: str, caption: str = "") -> None:
        """Chèn tham chiếu ảnh asset vào editor."""
        ref = f"\n![{caption}]({asset_path})\n\n"
        self._insert_at_cursor(ref)

    def insert_snippet(self, snippet_text: str) -> None:
        """Chèn snippet Markdown vào đúng vị trí con trỏ hiện tại."""
        cursor = self._editor.textCursor()
        cursor.insertText(snippet_text)
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()
        self._editor.ensureCursorVisible()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _do_save(self) -> None:
        if self._note_id is None or not self._is_modified or self._notes_dir is None:
            return
        try:
            content = self._editor.toPlainText()
            self._orchestrator.save_note_content(self._note_id, content)
            self._is_modified = False
            self._lbl_save_status.setText("Đã lưu")
            self.note_saved.emit(self._note_id)
            logger.debug(f"Lưu note id={self._note_id}")
            # Sau khi lưu: quét wikilinks và cập nhật backlinks
            self._orchestrator.sync_note_relations(self._note_id, content)
            self._refresh_backlinks()
            self._refresh_known_tags()
            self._refresh_known_wikilinks()
            self._refresh_quality_warning()
        except Exception as exc:  # noqa: BLE001
            self._lbl_save_status.setText("Lỗi lưu!")
            logger.error(f"Không thể lưu note id={self._note_id}: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_text_changed(self) -> None:
        if not self._is_modified:
            self._is_modified = True
            self._lbl_save_status.setText("Chưa lưu*")
        self._autosave_timer.start()
        QTimer.singleShot(0, self._update_hashtag_popup)
        QTimer.singleShot(0, self._update_wikilink_popup)
        if self._show_note_actions:
            QTimer.singleShot(0, self._refresh_quality_warning)
        QTimer.singleShot(0, self._refresh_blockquote_overlays)
        self.content_changed.emit()

    @staticmethod
    def _resolve_editor_font_family(font_family_setting: str) -> str:
        """Chọn font khả dụng đầu tiên từ danh sách ưu tiên trong setting."""
        available = {name.lower(): name for name in QFontDatabase.families()}
        requested = [part.strip() for part in font_family_setting.split(",") if part.strip()]

        for family in requested:
            key = family.lower()
            if key in {"monospace", "monospaced"}:
                fallback = [
                    "Roboto Mono",
                    "Fira Code",
                    "Cascadia Code",
                    "JetBrains Mono",
                    "Consolas",
                    "Courier New",
                ]
                for candidate in fallback:
                    ckey = candidate.lower()
                    if ckey in available:
                        return available[ckey]
                return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
            if key in available:
                return available[key]

        return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()

    @staticmethod
    def _apply_ligature_features(font: QFont, enabled: bool) -> None:
        """Bật/tắt ligature OpenType (liga/calt) nếu Qt hỗ trợ."""
        try:
            liga = QFont.Tag.fromString("liga")
            calt = QFont.Tag.fromString("calt")
            value = 1 if enabled else 0
            font.setFeature(liga, value)
            font.setFeature(calt, value)
        except Exception:
            # Một số platform/font có thể không hỗ trợ feature tags.
            return

    def _apply_editor_font(self) -> None:
        """Áp dụng font editor từ cài đặt global."""
        from core.services.settings_service import SettingsService

        svc = SettingsService()
        font_family_setting = str(svc.get("editor.fontFamily", DEFAULT_EDITOR_FONT_FAMILY))
        ligatures_enabled = bool(svc.get("editor.fontLigatures", True))
        self.apply_editor_preferences(font_family_setting, ligatures_enabled)

    def apply_editor_preferences(self, font_family_setting: str, ligatures_enabled: bool) -> None:
        """Public API: áp dụng font family + ligatures cho editor hiện tại."""
        family = self._resolve_editor_font_family(font_family_setting)
        editor_font = QFont(family, 12)
        editor_font.setStyleHint(QFont.StyleHint.Monospace)
        self._apply_ligature_features(editor_font, ligatures_enabled)
        self._editor.setFont(editor_font)
        self._editor.setTabStopDistance(self._editor.fontMetrics().horizontalAdvance(" ") * 4)

    def _refresh_blockquote_overlays(self) -> None:
        """Tô nền full-width cho blockquote và checklist để tăng phân biệt khi soạn thảo."""
        try:
            selections: list[QTextEdit.ExtraSelection] = []
            block = self._editor.document().firstBlock()
            while block.isValid():
                text = block.text()
                if _MarkdownSyntaxHighlighter._BLOCKQUOTE_PATTERN.match(text):
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = QTextCursor(block)
                    sel.cursor.clearSelection()
                    sel.format.setBackground(QColor("#F8EEDB"))
                    sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                    selections.append(sel)
                elif _MarkdownSyntaxHighlighter._CHECKLIST_PATTERN.match(text):
                    sel = QTextEdit.ExtraSelection()
                    sel.cursor = QTextCursor(block)
                    sel.cursor.clearSelection()
                    sel.format.setBackground(QColor("#EFE7FF"))
                    sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                    selections.append(sel)
                block = block.next()

            self._editor.setExtraSelections(selections)
        except RuntimeError:
            return

    def _refresh_quality_warning(self) -> None:
        """Hiển thị soft-warning chất lượng note hiện tại."""
        try:
            if self._note_id is None or self._current_note_type is None:
                self._lbl_quality_warning.setText("")
                return

            warnings = self._orchestrator.build_quality_warnings(
                note_id=self._note_id,
                note_type=self._current_note_type,
                note_title=self._lbl_title.text(),
                content=self._editor.toPlainText(),
                current_source_id=self._current_source_id,
            )

            if warnings:
                self._lbl_quality_warning.setText("Cảnh báo: " + " | ".join(warnings))
            else:
                self._lbl_quality_warning.setText("")
        except RuntimeError:
            return

    def _open_new_note_dialog(self) -> None:
        """Mở NewNoteDialog để tạo concept/synthesis/board note."""
        if not self._show_note_actions:
            return
        if self._notes_dir is None or self._note_id is None:
            QMessageBox.information(self, "Tạo note", "Vui lòng mở một note trước khi tạo note mới.")
            return

        from core.services.project_service import ProjectService
        from ui.widgets.dialogs.new_note_dialog import NewNoteDialog

        active_project_id = self._orchestrator.active_project_id
        active_project_name = None
        if active_project_id is not None:
            try:
                active_project_name = ProjectService().get_project(active_project_id).name
            except Exception:
                active_project_name = None

        dlg = NewNoteDialog(
            self,
            notes_dir=self._notes_dir,
            current_note_title=self._lbl_title.text().strip(),
            active_project_id=active_project_id,
            active_project_name=active_project_name,
        )
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        try:
            note = self._orchestrator.create_note_in_scope(
                title=dlg.title_text,
                note_type=dlg.note_type,
                initial_content=dlg.content_text,
                save_to_project=(dlg.save_scope == "project"),
            )
            self._insert_at_cursor(f"[[{note.title}]]\n")
            scope_text = "Project" if dlg.save_scope == "project" else "Global"
            QMessageBox.information(
                self,
                "Tạo note thành công",
                f"Đã tạo note: {note.title}\nPhạm vi lưu: {scope_text}\nĐã chèn wikilink vào note hiện tại.",
            )
            self._refresh_known_wikilinks()
            self._refresh_quality_warning()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo note mới:\n{exc}")

    def _open_metadata_dialog(self) -> None:
        """Mở dialog chỉnh metadata của note hiện tại."""
        if not self._show_note_actions:
            return
        if self._note_id is None or self._notes_dir is None or self._current_note_type is None:
            return

        from core.services.note_service import NoteService
        from ui.widgets.dialogs.note_metadata_dialog import NoteMetadataDialog

        note_svc = NoteService(self._notes_dir)
        dlg = NoteMetadataDialog(
            note_id=self._note_id,
            note_type=self._current_note_type,
            note_service=note_svc,
            parent=self,
        )
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._refresh_quality_warning()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """Bắt phím từ editor hoặc popup để điều khiển hashtag/wikilink autocomplete."""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            # Popup hashtag
            if obj is self._hashtag_completer.popup():
                if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    return self._accept_current_hashtag_completion()
                if key == Qt.Key.Key_Escape:
                    self._hashtag_completer.popup().hide()
                    return True
                return False

            # Popup wikilink
            if obj is self._wikilink_completer.popup():
                if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    return self._accept_current_wikilink_completion()
                if key == Qt.Key.Key_Escape:
                    self._wikilink_completer.popup().hide()
                    return True
                return False

            # Editor
            if obj is self._editor:
                if (
                    key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                    and not self._hashtag_completer.popup().isVisible()
                    and not self._wikilink_completer.popup().isVisible()
                ):
                    if self._handle_checklist_enter():
                        return True
                    if self._handle_blockquote_enter():
                        return True

                if self._hashtag_completer.popup().isVisible():
                    if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        return self._accept_current_hashtag_completion()
                    if key == Qt.Key.Key_Escape:
                        self._hashtag_completer.popup().hide()
                        return True

                if self._wikilink_completer.popup().isVisible():
                    if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        return self._accept_current_wikilink_completion()
                    if key == Qt.Key.Key_Escape:
                        self._wikilink_completer.popup().hide()
                        return True

                handled = super().eventFilter(obj, event)
                QTimer.singleShot(0, self._update_hashtag_popup)
                QTimer.singleShot(0, self._update_wikilink_popup)
                return handled

        return super().eventFilter(obj, event)

    def _handle_blockquote_enter(self) -> bool:
        """Xử lý Enter trong blockquote theo cơ chế auto-continue/exit.

        - Enter trong dòng `> nội dung` -> tạo dòng mới với `> `.
        - Enter trên dòng chỉ có `>` hoặc `> ` -> thoát blockquote.
        """
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            return False

        block = cursor.block()
        line_text = block.text()
        match = re.match(r"^(\s*)>\s?(.*)$", line_text)
        if not match:
            return False

        indent = match.group(1)
        body = match.group(2)

        # Dòng quote rỗng -> Enter lần nữa để thoát khỏi quote block.
        if body.strip() == "":
            start = block.position()
            end = start + len(line_text)
            cursor.beginEditBlock()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertBlock()
            cursor.endEditBlock()
            self._editor.setTextCursor(cursor)
            return True

        cursor.insertText(f"\n{indent}> ")
        return True

    def _handle_checklist_enter(self) -> bool:
        """Xử lý Enter trong checklist theo cơ chế auto-continue/exit.

        - Enter trong dòng `- [ ] nội dung` hoặc `- [x] nội dung` -> tạo dòng mới `- [ ] `.
        - Enter trên dòng chỉ có `- [ ]` -> thoát checklist.
        """
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            return False

        block = cursor.block()
        line_text = block.text()
        match = re.match(r"^(\s*)-\s\[( |x|X)\]\s?(.*)$", line_text)
        if not match:
            return False

        indent = match.group(1)
        body = match.group(3)

        if body.strip() == "":
            start = block.position()
            end = start + len(line_text)
            cursor.beginEditBlock()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertBlock()
            cursor.endEditBlock()
            self._editor.setTextCursor(cursor)
            return True

        cursor.insertText(f"\n{indent}- [ ] ")
        return True

    def _accept_current_hashtag_completion(self) -> bool:
        """Chèn hashtag đang chọn trong popup; fallback item đầu tiên nếu cần."""
        # PRIMARY: lấy từ popup row đang được highlight (không dùng currentCompletion()
        # vì nó trả về prefix, không phải item đang chọn)
        popup = self._hashtag_completer.popup()
        popup_index = popup.currentIndex()
        if popup_index.isValid():
            completion = str(popup_index.data()).strip()
        else:
            # fallback: item đầu tiên trong model
            completion = ""
            if self._hashtag_model.rowCount() > 0:
                completion = str(
                    self._hashtag_model.data(self._hashtag_model.index(0, 0))
                ).strip()
        if completion:
            self._insert_hashtag_completion(completion)
            return True
        return False

    def _insert_at_cursor(self, text: str) -> None:
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._editor.setTextCursor(cursor)
        self._editor.ensureCursorVisible()

    def _set_note_loaded(self, loaded: bool) -> None:
        self._editor.setVisible(loaded)
        self._empty_label.setVisible(not loaded)

    def refresh_wikilink_catalog(self) -> None:
        """Public API: làm mới danh sách note dùng cho popup [[wikilink]]."""
        self._refresh_known_wikilinks()
        self._wikilink_display_to_title.clear()

    # ------------------------------------------------------------------
    # Wikilinks & Backlinks
    # ------------------------------------------------------------------

    def _scan_and_create_wikilinks(self) -> None:
        """Tương thích ngược: gọi orchestrator để sync wikilink."""
        if self._note_id is None or self._notes_dir is None:
            return
        self._orchestrator.sync_note_relations(self._note_id, self._editor.toPlainText())

    def _extract_hashtags(self, content: str) -> set[str]:
        """Trích hashtag từ Markdown (không lấy heading '# ')."""
        pattern = re.compile(r"(?<!\w)#(?!\s)([\w\-]+)", re.UNICODE)
        return {m.group(1).strip().lower() for m in pattern.finditer(content)}

    def _sync_hashtags_to_note_tags(self) -> None:
        """Tương thích ngược: gọi orchestrator để sync hashtag->tags."""
        if self._note_id is None:
            return
        self._orchestrator.sync_note_relations(self._note_id, self._editor.toPlainText())

    def _refresh_known_tags(self) -> None:
        """Nạp danh sách tags đã có để phục vụ autocomplete."""
        self._known_tags = self._orchestrator.known_tags(self._editor.toPlainText())

    def _refresh_known_wikilinks(self) -> None:
        """Nạp danh sách tiêu đề note cho gợi ý [[wikilink]].
        
        Trong scratch mode (no active project), lấy tất cả notes.
        Trong note mode, lấy notes của active project (excluding current note).
        """
        self._known_wikilinks = []
        self._wikilink_display_to_title = {}
        if self._notes_dir is None:
            return
        try:
            # Truyền note_id=None để lấy toàn bộ catalog của project hiện tại
            # hoặc tất cả notes nếu không có active project
            self._known_wikilinks = self._orchestrator.wikilink_catalog(self._note_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể nạp wikilink catalog: {exc}")
            self._known_wikilinks = []
            self._wikilink_display_to_title = {}

    @staticmethod
    def _normalize_wikilink_target(raw_target: str) -> tuple[str, str]:
        """Chuẩn hóa title từ wikilink marker và suy ra note_type mục tiêu."""
        return WorkspaceOrchestrator.normalize_wikilink_target(raw_target)

    @staticmethod
    def _build_wikilink_label(note_type: str, title: str) -> str:
        """Sinh nhãn hiển thị trong popup: `<type> - <title>`."""
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

    def _current_hashtag_context(self) -> tuple[int, str] | None:
        """Lấy token hashtag đang được gõ tại vị trí con trỏ."""
        cursor = self._editor.textCursor()
        pos = cursor.position()
        text = self._editor.toPlainText()
        if pos < 0 or pos > len(text):
            return None

        start = pos
        while start > 0 and not text[start - 1].isspace():
            start -= 1

        token = text[start:pos]
        if not token.startswith("#"):
            return None

        if start > 0 and text[start - 1].isalnum():
            return None

        # Heading marker ở đầu dòng (vd: '# ') không được xem là hashtag.
        if token in {"#", "##", "###", "####", "#####", "######"}:
            line_start = text.rfind("\n", 0, start) + 1
            if start == line_start:
                return None

        return start, token

    def _update_hashtag_popup(self) -> None:
        """Cập nhật popup gợi ý hashtag theo prefix hiện tại."""
        try:
            popup = self._hashtag_completer.popup()
        except RuntimeError:
            return

        if self._note_id is None or not self._editor.hasFocus():
            popup.hide()
            return

        ctx = self._current_hashtag_context()
        if ctx is None:
            popup.hide()
            return

        _, token = ctx
        prefix = token[1:].strip().lower()

        available_tags = set(self._known_tags)
        available_tags.update(self._extract_hashtags(self._editor.toPlainText()))
        matches = sorted(t for t in available_tags if t.startswith(prefix))
        if prefix and prefix not in matches:
            matches.append(prefix)  # Cho phép tạo mới

        if not prefix and not matches:
            popup.hide()
            return

        items = [f"#{name}" for name in matches]
        if not items:
            popup.hide()
            return

        self._hashtag_model.setStringList(items)
        self._hashtag_completer.setCompletionPrefix(token)
        rect = self._editor.cursorRect()
        rect.setWidth(240)
        self._hashtag_completer.complete(rect)

    def _current_wikilink_context(
        self,
    ) -> tuple[int, str, str, str] | None:
        """Lấy context wikilink tại con trỏ.

        Returns:
            (content_start, note_part, mode, sub_token) hoặc None.
            mode = 'note' | 'heading' | 'block'
            note_part: phần title note (trước # hoặc >)
            sub_token: phần gõ sau dấu phân cách
        """
        cursor = self._editor.textCursor()
        pos = cursor.position()
        text = self._editor.toPlainText()
        if pos < 0 or pos > len(text):
            return None

        start_marker = text.rfind("[[", 0, pos)
        if start_marker < 0:
            return None

        # Nếu đã có đóng ]] sau [[ và trước con trỏ thì không còn context gợi ý.
        end_marker = text.rfind("]]", 0, pos)
        if end_marker > start_marker:
            return None

        token = text[start_marker + 2:pos]
        if "\n" in token or "]" in token:
            return None

        content_start = start_marker + 2

        # Kiểm tra chế độ heading: [[NoteTitle#
        if "#" in token:
            hash_pos = token.index("#")
            note_part = token[:hash_pos]
            sub_token = token[hash_pos + 1:]
            # Block: [[NoteTitle#^
            if sub_token.startswith("^"):
                # Bỏ qua ^ block, xử lý như heading
                return content_start, note_part, "heading", sub_token[1:]
            return content_start, note_part, "heading", sub_token

        return content_start, token, "note", ""

    def _extract_headings_from_note(self, note_title: str) -> list[str]:
        """Trích xuất heading từ note theo title; nếu title rỗng → note hiện tại (same-note link)."""
        if not note_title.strip():
            return self._parse_headings(self._editor.toPlainText())
        if self._notes_dir is None:
            return []
        try:
            from core.services.note_service import NoteService
            note_svc = NoteService(self._notes_dir)
            all_notes = note_svc.list_all()
            target = next(
                (n for n in all_notes if n.title.lower() == note_title.strip().lower()),
                None,
            )
            if target is None:
                return []
            return self._parse_headings(note_svc.read_content(target.id))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể trích heading cho note {note_title!r}: {exc}")
            return []

    @staticmethod
    def _parse_headings(content: str) -> list[str]:
        """Trích xuất danh sách text heading từ nội dung Markdown."""
        headings = []
        for line in content.splitlines():
            m = re.match(r"^(#{1,6})\s+(.+)$", line)
            if m:
                headings.append(m.group(2).strip())
        return headings

    def _update_wikilink_popup(self) -> None:
        """Hiển thị popup gợi ý title note / heading / block khi đang gõ [[."""
        try:
            popup = self._wikilink_completer.popup()
        except RuntimeError:
            return

        if not self._editor.hasFocus():
            popup.hide()
            return

        ctx = self._current_wikilink_context()
        if ctx is None:
            popup.hide()
            return

        content_start, note_part, mode, sub_token = ctx
        sub_prefix = sub_token.strip().lower()

        if mode == "note":
            # Chế độ gợi ý title note (hoạt động cả lúc edit note lẫn scratch mode)
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
                popup.hide()
                return
            # Thêm dòng gợi ý ở cuối
            hint_items = ["── Gõ # để liên kết với đề mục (heading)"]
            self._wikilink_model.setStringList(matches + hint_items)
            self._wikilink_completer.setCompletionPrefix(note_part)
            rect = self._editor.cursorRect()
            rect.setWidth(360)
            self._wikilink_completer.complete(rect)

        elif mode == "heading":
            # Chế độ gợi ý heading trong note được chọn
            headings = self._extract_headings_from_note(note_part)
            matches = [h for h in headings if sub_prefix in h.lower()] if sub_prefix else headings
            if not matches:
                popup.hide()
                return
            self._wikilink_model.setStringList(matches)
            self._wikilink_completer.setCompletionPrefix(sub_token)
            rect = self._editor.cursorRect()
            rect.setWidth(360)
            self._wikilink_completer.complete(rect)

    def _insert_hashtag_completion(self, completion: str) -> None:
        """Chèn hashtag đã chọn vào editor."""
        ctx = self._current_hashtag_context()
        if ctx is None:
            return

        start_pos, _token = ctx
        cursor = self._editor.textCursor()
        end_pos = cursor.position()
        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(f"{completion} ")
        self._editor.setTextCursor(cursor)
        self._hashtag_completer.popup().hide()

        normalized = completion[1:].strip().lower() if completion.startswith("#") else completion
        if normalized:
            self._known_tags.add(normalized)

    def _accept_current_wikilink_completion(self) -> bool:
        """Chèn wikilink đang chọn trong popup (PRIMARY: popup row, không dùng currentCompletion)."""
        popup = self._wikilink_completer.popup()
        popup_index = popup.currentIndex()
        if popup_index.isValid():
            completion = str(popup_index.data()).strip()
        else:
            completion = ""
            if self._wikilink_model.rowCount() > 0:
                completion = str(
                    self._wikilink_model.data(self._wikilink_model.index(0, 0))
                ).strip()
        # Bỏ qua các dòng hint (bắt đầu bằng ──)
        if completion.startswith("──"):
            return True  # consume keystroke nhưng không insert
        if completion:
            mapped = self._wikilink_display_to_title.get(completion, completion)
            normalized_title, _ = self._normalize_wikilink_target(mapped)
            self._insert_wikilink_completion(normalized_title)
            return True
        return False

    def _on_wikilink_activated(self, completion: str) -> None:
        mapped = self._wikilink_display_to_title.get(str(completion), str(completion))
        normalized_title, _ = self._normalize_wikilink_target(mapped)
        self._insert_wikilink_completion(normalized_title)

    def _insert_wikilink_completion(self, completion: str) -> None:
        """Chèn title/heading/block được chọn vào cặp [[...]]."""
        ctx = self._current_wikilink_context()
        if ctx is None:
            return
        content_start, note_part, mode, _sub_token = ctx
        cursor = self._editor.textCursor()
        end_pos = cursor.position()
        cursor.setPosition(content_start)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        if mode == "heading":
            cursor.insertText(f"{note_part}#{completion}]] ")
        else:  # mode == "note"
            cursor.insertText(f"{completion}]] ")
        self._editor.setTextCursor(cursor)
        self._wikilink_completer.popup().hide()

    def _refresh_backlinks(self) -> None:
        """Cập nhật nhãn đếm số backlinks."""
        if self._note_id is None:
            self._lbl_backlinks.setText("")
            return
        try:
            count = self._orchestrator.backlinks_count(self._note_id)
            if count:
                self._lbl_backlinks.setText(f"← {count} liên kết")
            else:
                self._lbl_backlinks.setText("")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Không thể cập nhật backlink count cho note id={self._note_id}: {exc}")
            self._lbl_backlinks.setText("")

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    def _open_tags_dialog(self) -> None:
        """Mở dialog quản lý tags của note hiện tại."""
        if not self._show_note_actions:
            return
        if self._note_id is None:
            return
        from ui.widgets.dialogs.note_tags_dialog import NoteTagsDialog
        dlg = NoteTagsDialog(self._note_id, self)
        dlg.exec()
        self._refresh_known_tags()

    def _open_wikilinks_dialog(self) -> None:
        """Mở dialog quản lý wikilinks của note hiện tại."""
        if not self._show_note_actions:
            return
        if self._note_id is None:
            return
        from ui.widgets.dialogs.note_wikilinks_dialog import NoteWikilinksDialog
        dlg = NoteWikilinksDialog(self._note_id, self)
        dlg.exec()
        self._refresh_known_wikilinks()
        self._refresh_backlinks()
