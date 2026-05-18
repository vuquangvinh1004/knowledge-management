"""QSS stylesheet cho ứng dụng PKM."""

_LIGHT_QSS = """
/* === App shell === */
QMainWindow {
    background-color: #F5F5F5;
}

/* === General === */
QWidget {
    color: #333333;
    font-size: 13px;
}

QLabel {
    color: #333333;
    background-color: transparent;
}

QLineEdit {
    color: #1A1A2E;
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #3A5CE6;
}

QLineEdit:disabled {
    background-color: #F0F2F8;
    color: #888888;
}

QSpinBox {
    color: #1A1A2E;
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
    min-width: 60px;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
}

QComboBox {
    color: #1A1A2E;
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
}

QComboBox:focus {
    border-color: #3A5CE6;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
    selection-background-color: #3A5CE6;
    selection-color: white;
}

QPushButton {
    color: #333333;
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #EEF0F8;
    border-color: #3A5CE6;
}

QPushButton:pressed {
    background-color: #3A5CE6;
    color: white;
}

QPushButton:disabled {
    color: #AAAAAA;
    background-color: #F5F5F5;
    border-color: #E0E0E0;
}

/* === Group boxes === */
QGroupBox {
    font-size: 13px;
    font-weight: 600;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    padding-bottom: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    left: 10px;
    color: #1A1A2E;
    background-color: #F5F5F5;
}

/* === Sidebar === */
QWidget#sidebar_widget {
    background-color: #FBFCFF;
    border-right: 1px solid #D0D4E8;
}

QLabel#sidebar_section_header {
    font-size: 11px;
    font-weight: 700;
    color: #5A6076;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

QPushButton[flat="true"] {
    text-align: left;
    padding: 8px 16px;
    font-size: 13px;
    color: #333333;
    border: none;
    border-radius: 0;
    background-color: transparent;
}

QPushButton[flat="true"]:hover {
    background-color: #E9EDFB;
    color: #1A1A2E;
}

QPushButton[flat="true"]:checked {
    background-color: #E5EEFF;
    color: #1E40AF;
    font-weight: 700;
    border-left: 3px solid #3A5CE6;
    padding-left: 13px;
}

QListWidget#sidebar_project_list {
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 6px;
    color: #1A1A2E;
}

QListWidget#sidebar_project_list::item {
    padding: 7px 10px;
}

QListWidget#sidebar_project_list::item:selected {
    background-color: #E5EEFF;
    color: #1E40AF;
}

QPushButton#sidebar_project_global_btn,
QPushButton#sidebar_project_manage_btn {
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    color: #1A1A2E;
    padding: 4px 10px;
    border-radius: 4px;
}

QPushButton#sidebar_project_global_btn:hover,
QPushButton#sidebar_project_manage_btn:hover {
    background-color: #EEF0F8;
    border-color: #3A5CE6;
}

/* === Primary button === */
QPushButton#primary_button {
    background-color: #3A5CE6;
    color: white;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 6px;
    border: none;
}

QPushButton#primary_button:hover {
    background-color: #2F4CC8;
}

/* === Workspace extraction actions === */
QPushButton[workspaceRole="extract-action"] {
    background-color: #7B3FE4;
    color: #FFFFFF;
    border: 1px solid #6432BC;
    font-weight: 600;
}

QPushButton[workspaceRole="extract-action"]:hover {
    background-color: #6A35C6;
    border-color: #5B2BAF;
}

QPushButton[workspaceRole="extract-action"]:pressed,
QPushButton[workspaceRole="extract-action"]:checked {
    background-color: #5B2BAF;
    border-color: #4E2398;
    color: #FFFFFF;
}

QPushButton[workspaceRole="extract-action"]:disabled {
    background-color: #EEE6FF;
    color: #8A7AAE;
    border-color: #D9C9FB;
}

/* === Toolbar === */
QToolBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E0E0E0;
    spacing: 4px;
    padding: 4px 8px;
}

QToolBar QToolButton {
    font-size: 12px;
    color: #333333;
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid transparent;
}

QToolBar QToolButton:hover {
    background-color: #EEF0F8;
    border-color: #D0D4E8;
}

QToolBar QToolButton:pressed {
    background-color: #3A5CE6;
    color: white;
}

QToolBar QToolButton:checked {
    background-color: #3A5CE6;
    color: white;
    border-color: #2F4CC8;
}

/* Toolbar trong workspace */
QWidget#editor_header,
QWidget#pdf_nav_bar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E0E0E0;
}

QWidget#extraction_toolbar {
    background-color: #FFFFFF;
    border-top: 1px solid #E0E0E0;
}

QLabel#editor_title,
QLabel#extraction_source_label {
    color: #1A1A2E;
    font-weight: 600;
}

QLabel#editor_save_status,
QLabel#editor_backlinks {
    color: #5A6076;
}

QToolButton {
    color: #1A1A2E;
    background-color: #FFFFFF;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    padding: 4px 10px;
}

QToolButton:hover {
    background-color: #EEF0F8;
    border-color: #3A5CE6;
}

QToolButton:checked {
    background-color: #3A5CE6;
    border-color: #3A5CE6;
    color: #FFFFFF;
}

QLabel#editor_quality_warning,
QLabel#note_dialog_warning,
QLabel#import_hint_label,
QLabel#wikilink_hint_label {
    color: #8A4B00;
    font-size: 11px;
}

/* === Status bar === */
QStatusBar#main_status_bar {
    background-color: #F7F9FD;
    border-top: 1px solid #D0D4E8;
    font-size: 11px;
    color: #5A6076;
}

QStatusBar#main_status_bar QLabel#status_permanent_label {
    color: #1A1A2E;
    font-weight: 600;
}

/* === View headers === */
QLabel#view_header {
    font-size: 18px;
    font-weight: bold;
    color: #1A1A2E;
}

/* === Empty state === */
QLabel#empty_state_message {
    font-size: 13px;
    color: #888888;
    line-height: 1.6;
}

QPushButton#empty_state_action {
    background-color: #3A5CE6;
    color: white;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 6px;
    border: none;
}

QPushButton#empty_state_action:hover {
    background-color: #2F4CC8;
}

/* === Source detail panel === */
QWidget#source_detail_panel {
    background-color: #FFFFFF;
    border-left: 1px solid #D0D4E8;
}

QWidget#source_detail_panel QStackedWidget,
QWidget#source_detail_panel QScrollArea,
QWidget#source_detail_panel QScrollArea > QWidget > QWidget,
QWidget#source_detail_panel QWidget {
    background-color: #FFFFFF;
    color: #1A1A2E;
}

QWidget#source_detail_panel QGroupBox {
    color: #5C6076;
    border: 1px solid #DDE1EE;
    background-color: #FFFFFF;
}

QWidget#source_detail_panel QGroupBox::title {
    color: #5C6076;
    background-color: #FFFFFF;
}

QWidget#source_detail_panel QPushButton {
    color: #1A1A2E;
    background-color: #FFFFFF;
    border: 1px solid #C8D0E8;
    border-radius: 4px;
}

QWidget#source_detail_panel QPushButton:hover {
    background-color: #EEF0F8;
    border-color: #3A5CE6;
}

QLabel#source_detail_title {
    font-size: 14px;
    font-weight: 700;
    color: #1A1A2E;
}

QLabel#detail_section_header {
    font-size: 11px;
    font-weight: 600;
    color: #777777;
    padding-top: 4px;
}

QLabel#source_abstract_text {
    font-size: 12px;
    color: #444444;
    line-height: 1.5;
}

QLabel#source_path_text {
    font-size: 11px;
    color: #888888;
}

/* === List widgets === */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    outline: 0;
    color: #1A1A2E;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #F0F0F0;
    color: #1A1A2E;
}

QListWidget::item:selected {
    background-color: #3A5CE6;
    color: white;
}

QListWidget::item:hover {
    background-color: #EEF0F8;
}

/* === Table widgets === */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    gridline-color: #E8E8E8;
    color: #1A1A2E;
}

QHeaderView::section {
    background-color: #F0F2F8;
    color: #333333;
    font-weight: 600;
    padding: 6px 10px;
    border: none;
    border-right: 1px solid #E0E0E0;
    border-bottom: 1px solid #E0E0E0;
}

QTableWidget::item:selected {
    background-color: #3A5CE6;
    color: white;
}

/* === Scrollbar === */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #C0C4D8;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    height: 8px;
    background: transparent;
}

QScrollBar::handle:horizontal {
    background: #C0C4D8;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* === Splitter === */
QWidget#workspace_host {
    background-color: #FBFCFF;
}

QSplitter::handle {
    background-color: #D0D4E8;
}

QSplitter::handle:horizontal {
    width: 1px;
}

/* === Workspace source tabs === */
QTabWidget#source_tabs::pane {
    border: 1px solid #D0D4E8;
    border-top: none;
    background-color: #FFFFFF;
}

QTabWidget#source_tabs QTabBar::tab {
    background-color: #B22323;
    color: #FFFFFF;
    padding: 2px 12px;
    height: 22px;
    min-height: 22px;
    max-height: 22px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 600;
}

QTabWidget#source_tabs QTabBar::tab:selected {
    background-color: #C62828;
    color: #FFFFFF;
    font-weight: 700;
}

QTabWidget#source_tabs QTabBar::close-button {
    image: none;
    width: 12px;
    height: 12px;
}

/* === Draft workspace reference tabs (compact) === */
QTabWidget#workspace_ref_tabs::pane {
    border: 1px solid #D0D4E8;
    border-top: none;
    background-color: #FFFFFF;
}

QTabWidget#workspace_ref_tabs QTabBar::tab {
    background-color: #B22323;
    color: #FFFFFF;
    padding: 1px 10px;
    height: 20px;
    min-height: 20px;
    max-height: 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 600;
}

QTabWidget#workspace_ref_tabs QTabBar::tab:selected {
    background-color: #C62828;
    color: #FFFFFF;
    font-weight: 700;
}

QTabWidget#workspace_ref_tabs QTabBar::close-button {
    image: none;
    width: 11px;
    height: 11px;
}

/* === Text editors === */
QPlainTextEdit {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: none;
    font-size: 13px;
    selection-background-color: #3A5CE6;
    selection-color: white;
}

QPlainTextEdit#markdown_editor {
    background-color: #FFFFFF;
    color: #111827;
    font-size: 14px;
    padding: 12px;
}

QTextEdit {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
    border-radius: 4px;
    font-size: 13px;
    padding: 6px 8px;
    selection-background-color: #3A5CE6;
    selection-color: white;
}

QTextEdit:focus {
    border-color: #3A5CE6;
}

QTextEdit#note_preview {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}

/* === Dialog === */
QDialog {
    background-color: #F5F5F5;
}

QMenu {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
}

QMenu::item:selected {
    background-color: #3A5CE6;
    color: #FFFFFF;
}

QListView {
    background-color: #FFFFFF;
    color: #1A1A2E;
    border: 1px solid #D0D4E8;
}

QListView::item:selected {
    background-color: #3A5CE6;
    color: #FFFFFF;
}

QWidget#stats_bar {
    background-color: #FFFFFF;
    border: 1px solid #E0E4F2;
    border-radius: 8px;
    padding: 8px 10px;
}

QLabel#stat_name {
    font-size: 11px;
    color: #6B7285;
    font-weight: 600;
}

QLabel#stat_label {
    font-size: 18px;
    color: #1A1A2E;
    font-weight: 700;
}
"""


def get_light_qss() -> str:
    return _LIGHT_QSS
