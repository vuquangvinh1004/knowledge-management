"""Hằng số ứng dụng PKM."""

# App info
APP_NAME = "Quản lý Kiến thức Nghiên cứu"
APP_NAME_EN = "Research PKM"
APP_VERSION = "1.0.0-alpha"
SCHEMA_VERSION = 1

# Source anchor
SOURCE_ANCHOR_SCHEME = "source"

# Note types
NOTE_TYPE_SOURCE = "source_note"
NOTE_TYPE_CONCEPT = "concept_note"
NOTE_TYPE_SYNTHESIS = "synthesis_note"
NOTE_TYPE_BOARD = "board_note"
NOTE_TYPES = (NOTE_TYPE_SOURCE, NOTE_TYPE_CONCEPT, NOTE_TYPE_SYNTHESIS, NOTE_TYPE_BOARD)

# Extract types
EXTRACT_TYPE_TEXT = "text"
EXTRACT_TYPE_TABLE = "table"
EXTRACT_TYPE_IMAGE = "image"
EXTRACT_TYPES = (EXTRACT_TYPE_TEXT, EXTRACT_TYPE_TABLE, EXTRACT_TYPE_IMAGE)

# Link types
LINK_TYPE_WIKILINK = "wikilink"
LINK_TYPE_MANUAL = "manual"
LINK_TYPE_INFERRED = "inferred"

# Asset types
ASSET_TYPE_IMAGE = "image"
ASSET_TYPE_SNAPSHOT = "snapshot"

# UI
SIDEBAR_DEFAULT_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 56
STATUS_BAR_HEIGHT = 24
TOOLBAR_HEIGHT = 40

# Autosave
AUTOSAVE_INTERVAL_SECONDS = 30

# Lock
LOCK_TIMEOUT_SECONDS = 5

# Board metadata criteria (dùng cho Research Board và template source_note)
BOARD_META_ANALYSIS_OMITTED_CRITERIA = (
	"ID",
	"Link source_note",
	"Link concept_note",
	"Link synthesis_note",
)

BOARD_META_ANALYSIS_CRITERIA = (
	"Mã nghiên cứu",
	"Tác giả",
	"Năm",
	"Tiêu đề",
	"Quốc gia/Bối cảnh",
	"Loại nguồn",
	"Mục tiêu nghiên cứu",
	"Câu hỏi nghiên cứu",
	"Lý thuyết/khung phân tích",
	"Chủ đề chính",
	"Biến độc lập",
	"Biến phụ thuộc",
	"Biến trung gian/điều tiết",
	"Đối tượng nghiên cứu",
	"Cỡ mẫu",
	"Phương pháp nghiên cứu",
	"Công cụ phân tích",
	"Thiết kế nghiên cứu",
	"Thang đo/chỉ báo",
	"Kết quả chính",
	"Hướng tác động",
	"Effect size",
	"Loại effect size",
	"SE/SD",
	"CI thấp",
	"CI cao",
	"p-value",
	"Chất lượng nghiên cứu",
	"Hạn chế",
	"Ghi chú mã hóa",
)
