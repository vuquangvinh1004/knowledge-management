# REQUIREMENTS FOR RESEARCH-FOCUSED PERSONAL KNOWLEDGE MANAGEMENT APP

## 1. Project vision

Xây dựng ứng dụng Desktop quản lý kiến thức cá nhân theo mô hình local-first, phục vụ workflow nghiên cứu chuyên sâu dựa trên PDF. Mục tiêu không phải là một note app chung chung, mà là một môi trường làm việc nơi người dùng đọc PDF, trích xuất nội dung có dẫn nguồn, viết note Markdown, liên kết tri thức và tổng hợp nhiều tài liệu để chuẩn bị cho viết lách hoặc làm việc với AI ngoài ứng dụng.

## 2. Core product philosophy

- Desktop first
- Local first
- PDF is the source of truth
- Notes are personal knowledge, not raw source replicas
- Every important extract must remain source-grounded
- Architecture must stay modular and migration-safe

## 3. Primary interface architecture

Ứng dụng có 3 vùng chức năng chính:

### 3.1. Dual Pane Workspace

- Bên trái: PDF Viewer, hỗ trợ nhiều tab
- Bên phải: Markdown Editor, hỗ trợ nhiều tab
- Cơ chế đồng bộ: mỗi source PDF có một source note mặc định theo binding 1:1
- Khi đổi tab PDF bên trái, source note tương ứng bên phải phải tự động hiển thị

### 3.2. Research Board

- Hiển thị dạng ma trận
- Hàng: tài liệu hoặc study
- Cột: chủ đề nghiên cứu như Mục tiêu, Phương pháp, Kết quả, Hạn chế
- Mỗi ô có thể chứa note text hoặc liên kết tới note/extract

### 3.3. Sidebar

- Danh sách nguồn PDF
- Danh sách note
- Tag explorer
- Điều hướng nhanh tới search, board và settings

## 4. Functional requirements

### 4.1. Source management

- Import PDF vào thư viện nguồn
- Theo dõi metadata cơ bản
- Lưu fingerprint/hash file
- Lưu last opened page
- Hỗ trợ relink khi source đổi đường dẫn

### 4.2. Extraction

- Text highlight → chèn quote block vào Markdown kèm source anchor
- Table crop → preview parse → convert sang Markdown table
- Image capture → lưu asset cục bộ → chèn tham chiếu vào note

### 4.3. Knowledge connections

- Hỗ trợ `[[wikilink]]`
- Hỗ trợ backlinks
- Hỗ trợ tag cho note
- Cho phép tạo concept notes và synthesis notes độc lập với source note

### 4.4. Search

- Search nội dung note
- Search extract text
- Search metadata source
- Filter theo tag, note type hoặc source

### 4.5. Export

- Export note Markdown
- Export clean text bundle theo source, tag hoặc project
- Export dữ liệu đủ sạch để nạp vào NotebookLM, ChatGPT hoặc công cụ AI khác

## 5. Data structure

### File system

- `/data/sources` lưu PDF gốc
- `/data/notes` lưu Markdown notes
- `/data/assets` lưu ảnh/snapshot trích xuất
- `/data/exports` lưu file export
- `/data/backups` lưu backup

### Database (SQLite)

Core tables:

- `sources`
- `notes`
- `extracts`
- `assets`
- `tags`
- `note_tags`
- `links`
- `board_rows`
- `board_columns`
- `board_cells`
- `app_settings`

## 6. Non-negotiable rules

1. Local-first là nguyên tắc lõi.
2. PDF luôn là source of truth.
3. Extract phải có `source_id`, `page_no` và `source_anchor`.
4. Note khác extract, không trộn model.
5. Schema phải có versioning và migration runner.
6. Không viết business logic trong UI.
7. Table extraction phải có preview trước khi commit.

## 7. Suggested tech stack

- Python
- PySide6
- SQLite
- SQLAlchemy + Alembic
- PyMuPDF
- pdfplumber
- Markdown file-based notes
- SQLite FTS5 hoặc index nội bộ

## 8. Development order

### Phase 1

- App shell
- Config, paths, logging
- DB + migrations
- SourceService + NoteService

### Phase 2

- Library view
- PDF viewer cơ bản
- Markdown editor cơ bản
- Binding 1:1 source note

### Phase 3

- Text extraction
- Table crop + preview
- Image capture
- ExtractService + anchor generator

### Phase 4

- Wikilinks
- Backlinks
- Search
- Research Board

### Phase 5

- Export bundles
- Autosave
- Backup/restore
- Packaging + docs

## 9. Initial task for AI Agent

Hãy đọc `PKM_ARCHITECTURE.md`, `PKM_ROADMAP.md` và `START_HERE_FOR_AI_AGENT.md` trước khi code. Dựa trên kiến trúc đã chốt, hãy bắt đầu Phase 1 bằng cách:

1. Khởi tạo project skeleton theo cấu trúc thư mục chuẩn
2. Thiết lập config paths, SQLite connection, migration runner và single-instance lock
3. Tạo main window skeleton với sidebar, toolbar, central stacked widget và status strip
4. Tạo bộ test cơ bản cho app shell và migration bootstrapping

Mọi thay đổi phải tuân thủ chặt chẽ local-first, source-grounded extraction và schema versioning.
