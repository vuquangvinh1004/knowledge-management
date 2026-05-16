# SCHEMA NOTES

## Mục đích

Tài liệu này mô tả logic dữ liệu lõi, ngoài phần schema chính thức trong `PKM_ARCHITECTURE.md`.

## Thực thể lõi

### 1. sources

Đại diện cho tài liệu nguồn, thường là PDF.

Trường khuyến nghị:

- `id`
- `file_path`
- `file_hash`
- `title`
- `authors`
- `year`
- `doi`
- `journal`
- `abstract`
- `metadata_json`
- `page_count`
- `last_opened_page`
- `created_at`
- `updated_at`

### 2. notes

Đại diện cho file Markdown và tri thức người dùng.

- `id`
- `source_id` nullable
- `title`
- `slug`
- `file_path`
- `note_type`
- `summary`
- `created_at`
- `updated_at`

`note_type` khuyến nghị:

- `source_note`
- `concept_note`
- `synthesis_note`
- `board_note`
- `scratch_note`

### 3. extracts

Đại diện cho block trích xuất từ source.

- `id`
- `source_id`
- `note_id` nullable
- `extract_type`
- `page_no`
- `rect_json` nullable
- `source_anchor`
- `content_md`
- `content_text`
- `created_at`

`extract_type` khuyến nghị:

- `text`
- `table`
- `image`

### 4. assets

Ảnh được cắt/chụp từ source hoặc được người dùng gắn vào note.

- `id`
- `source_id` nullable
- `note_id` nullable
- `file_path`
- `asset_type`
- `page_no` nullable
- `rect_json` nullable
- `caption`
- `created_at`

### 5. tags + note_tags + extract_tags

Tag nên là bảng độc lập, không nhét trực tiếp vào JSON text nếu muốn filter tốt.

### 6. links

Liên kết giữa note với note hoặc note với source.

- `from_note_id`
- `to_note_id`
- `link_type`
- `created_at`

### 7. board_* tables

Nên tách board thành bảng riêng:

- `boards`
- `board_columns`
- `board_rows`
- `board_cells`

## Quy tắc cứng

1. `source_anchor` không được rỗng với extract chính thức.
2. `source_note` phải có thể map ngược về `source_id`.
3. Không dùng một cột JSON duy nhất để chứa toàn bộ graph tri thức.
4. `file_hash` dùng để phát hiện trùng hoặc file bị thay thế.
5. Không xóa cứng source nếu còn note hoặc extract tham chiếu mà chưa xác nhận.
