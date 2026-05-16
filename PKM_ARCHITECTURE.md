# RESEARCH-FOCUSED PKM ARCHITECTURE

> QUAN TRỌNG CHO AI AGENT
>
> File này là nguồn chân lý cho toàn bộ dự án Ứng dụng Desktop Quản lý Kiến thức Cá nhân phục vụ nghiên cứu.
>
> AI Agent bắt buộc phải đọc và tuân thủ file này trước khi:
>
> 1. Bắt đầu xây dựng bất kỳ phần nào của ứng dụng
> 2. Tạo mới, sửa, xóa hoặc refactor bất kỳ module, service, view, model, bảng dữ liệu hoặc file format nội bộ nào
> 3. Thay đổi extraction pipeline, source anchor format, storage layout, note format hoặc export contract
> 4. Thay đổi database schema, migration, settings hoặc cơ chế lưu dữ liệu cục bộ
> 5. Thêm thư viện mới ảnh hưởng đến runtime, UI, render PDF, search hoặc packaging
> 6. Thay đổi hành vi autosave, backup/restore hoặc single-instance lock
>
> Mọi thay đổi về kiến trúc, hành vi lõi, database schema, tech stack, cấu trúc thư mục, chuẩn coding hoặc chuẩn UI phải được ghi ngay vào phần CHANGELOG ở cuối file này.

---

## 1. Tổng quan dự án

### 1.1. Mô tả

Đây là một ứng dụng desktop cá nhân để quản lý tri thức nghiên cứu trên máy tính cục bộ. Ứng dụng phục vụ cho một người dùng duy nhất, tối ưu cho workflow đọc tài liệu PDF, trích xuất nội dung, ghi chú bằng Markdown và tổng hợp liên tài liệu.

Ứng dụng tập trung vào các nghiệp vụ sau:

1. Quản lý bộ tài liệu nguồn PDF
2. Hiển thị PDF nhiều tab
3. Đồng bộ 1:1 giữa source và note chính
4. Trích xuất text có dẫn nguồn
5. Trích bảng và chuyển sang Markdown
6. Chụp ảnh sơ đồ, hình và lưu vào assets
7. Liên kết ghi chú hai chiều và gắn tag
8. Tìm kiếm note, extract và metadata nguồn
9. Tổng hợp nghiên cứu trên Research Board
10. Xuất clean text cho AI bên ngoài

Ứng dụng không phải note app đa mục đích, không phải reference manager hoàn chỉnh, và không phải hệ thống cộng tác nhiều người dùng. Nó là công cụ local-first, source-grounded, note-centric dành cho nghiên cứu chuyên sâu.

### 1.2. Mục tiêu sản phẩm

| Mục tiêu | Diễn giải |
|---|---|
| Quản lý tài liệu nghiên cứu trên Desktop | Thay cho việc mở PDF, note, hình ảnh và bảng biểu rời rạc ở nhiều nơi |
| Tách rõ source và tri thức cá nhân | PDF là nguồn gốc, Markdown là lớp tư duy và tổng hợp |
| Truy vết nguồn mạnh | Mọi extract quan trọng phải quay lại được tài liệu gốc |
| Local first và an toàn | Dữ liệu lưu trên máy, có autosave, backup/restore, migration |
| Nền tảng cho AI workflow | Dễ xuất dữ liệu sạch, có cấu trúc và còn ngữ cảnh nguồn |
| Dễ mở rộng sau này | Có thể thêm local search tốt hơn, embeddings hoặc local LLM mà không phá kiến trúc |

### 1.3. Phạm vi phiên bản v1.0

Phiên bản v1.0 bắt buộc phải có:

1. Ứng dụng desktop bằng PySide6
2. SQLite local database
3. Single-instance lock
4. Schema versioning và migration runner
5. Source library PDF
6. Dual-pane PDF + Markdown
7. Binding 1:1 giữa source PDF và source note
8. Text extraction có page link
9. Table crop với preview và convert Markdown
10. Image capture vào assets
11. Tagging và `[[wikilink]]`
12. Backlinks cơ bản
13. Search cơ bản
14. Research Board bản đầu
15. Export clean text bundle
16. Autosave, backup và restore
17. Keyboard shortcuts tối thiểu
18. Empty states và warning states rõ ràng

Phiên bản v1.0 chưa bắt buộc phải có:

1. OCR mặc định cho scanned PDF
2. Cloud sync
3. Multi-user collaboration
4. Web clipper
5. Citation manager chuẩn BibTeX đầy đủ
6. Local LLM runtime tích hợp sẵn
7. Vector search production-grade
8. Plugin marketplace

### 1.4. Đối tượng sử dụng

1. Người dùng cá nhân làm nghiên cứu chuyên sâu
2. Người đọc nhiều PDF học thuật và muốn ghi chú theo kiểu source-grounded
3. Người cần chuẩn bị dữ liệu sạch để làm việc với AI ngoài ứng dụng

---

## 2. Nguyên tắc sản phẩm và ranh giới kiến trúc

### 2.1. Nguyên tắc bắt buộc

| Nguyên tắc | Nội dung |
|---|---|
| Desktop first | Mọi luồng chính phải tối ưu cho desktop trước |
| Local first | Dữ liệu và cấu hình mặc định lưu trên máy người dùng |
| Source grounded | Mọi tri thức quan trọng phải truy về được source |
| Note centric | Note là đơn vị tư duy chính của người dùng |
| Clear separation | Source, note, extract, asset và board cell là các loại dữ liệu khác nhau |
| Safe persistence | Có autosave, backup/restore, migration và không làm mất dữ liệu im lặng |
| Maintainability | Code phải testable, dễ refactor, dễ thêm tính năng mới |
| Vietnamese UI | Toàn bộ giao diện hiển thị cho người dùng phải bằng tiếng Việt |

### 2.2. Những điều AI Agent không được tự ý làm

1. Không tự ý chuyển dự án sang Electron, Tauri, web app, mobile app hoặc framework khác.
2. Không nhét business logic vào QWidget, QDialog, QMainWindow hoặc delegate.
3. Không coi note và extract là cùng một thực thể.
4. Không tạo extract không có source anchor tối thiểu.
5. Không xóa cứng source, note hoặc asset mà không có delete policy rõ ràng.
6. Không bỏ qua migration khi thay đổi schema SQLite.
7. Không cho phép app mở nhiều instance ghi cùng một DB nếu chưa có lock hợp lệ.
8. Không parse bảng từ PDF rồi commit thẳng mà không có bước preview/confirm.
9. Không đánh dấu task là xong nếu chỉ có mock UI mà chưa có logic thật và test tương ứng.
10. Không thêm phụ thuộc nặng cho toàn bộ app chỉ để phục vụ một chức năng hẹp nếu chưa đánh giá tác động.
11. Không thay đổi source anchor format hoặc markdown conventions mà không cập nhật file này và ROADMAP.

---

## 3. Tech stack chính thức

### 3.1. Công nghệ cốt lõi

| Thành phần | Công nghệ | Version đề xuất | Lý do lựa chọn |
|---|---|---:|---|
| Desktop framework | PySide6 | >= 6.6 | Ổn định, mạnh cho desktop split view, tab, model/view |
| Python | Python | >= 3.11 | Type hints tốt, ecosystem mạnh |
| Database | SQLite | >= 3.40 | Serverless, local first |
| ORM | SQLAlchemy | >= 2.0 | Tách persistence rõ ràng, dễ test |
| Migration | Alembic | >= 1.13 | Kiểm soát schema theo version |
| PDF engine | PyMuPDF | >= 1.24 | Render nhanh, extract text, access page geometry |
| Table extraction | pdfplumber | >= 0.11 | Phù hợp crop và parse bảng có kiểm soát |
| Markdown | markdown-it-py hoặc render pipeline tương đương | n/a | Dùng cho preview HTML |
| Search | SQLite FTS5 hoặc index nội bộ | n/a | Đủ cho v1 local search |
| Logging | loguru hoặc logging chuẩn | >= 0.7 nếu dùng | Dễ trace |
| Testing | pytest, pytest-qt, pytest-cov | >= 7.4 | Unit test, UI test, coverage |
| Packaging | PyInstaller | >= 6.0 | Đóng gói Windows desktop |

### 3.2. Công nghệ tùy chọn có kiểm soát

| Công nghệ | Trạng thái | Ghi chú |
|---|---|---|
| QWebEngine | Tùy chọn có kiểm soát | Dùng cho preview hoặc editor-based web view nếu thật sự cần |
| pyqtgraph | Tùy chọn | Nếu Research Board hoặc metrics cần chart nhẹ |
| python-docx | Tùy chọn | Nếu cần export outline/report ra Word |

### 3.3. Lựa chọn bị loại khỏi v1.0

| Công nghệ | Trạng thái | Lý do |
|---|---|---|
| Electron | Không dùng | Nặng và lệch hướng Python desktop |
| FastAPI/Django | Không dùng | Không phải web app |
| PostgreSQL | Không dùng | Dư thừa cho local app cá nhân |
| External vector DB | Không dùng | Chưa cần cho v1 |
| Cloud database | Không dùng | Trái với local-first |

---

## 4. Cấu trúc thư mục chuẩn

```text
research_pkm/
│
├── main.py
├── PKM_ARCHITECTURE.md
├── PKM_ROADMAP.md
├── PKM_SPEC_FINAL.md
├── START_HERE_FOR_AI_AGENT.md
├── REQUIREMENTS.md
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── paths.py
│   └── database.py
│
├── core/
│   ├── __init__.py
│   ├── app_kernel/
│   │   ├── __init__.py
│   │   ├── bootstrap.py
│   │   ├── startup_checks.py
│   │   ├── shutdown_manager.py
│   │   └── app_lock.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── source_service.py
│   │   ├── note_service.py
│   │   ├── extract_service.py
│   │   ├── asset_service.py
│   │   ├── tag_service.py
│   │   ├── link_service.py
│   │   ├── board_service.py
│   │   ├── search_service.py
│   │   ├── export_service.py
│   │   ├── settings_service.py
│   │   ├── backup_service.py
│   │   └── migration_service.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── pdf_text.py
│   │   ├── pdf_table.py
│   │   ├── pdf_image.py
│   │   ├── anchors.py
│   │   └── normalizers.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fts_index.py
│   │   └── query_parser.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── connection.py
│   │   ├── session.py
│   │   └── migrations/
│   │       └── versions/
│   └── utils/
│       ├── __init__.py
│       ├── constants.py
│       ├── validators.py
│       ├── exceptions.py
│       ├── helpers.py
│       └── logger.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── views/
│   │   ├── dashboard_view.py
│   │   ├── library_view.py
│   │   ├── workspace_view.py
│   │   ├── board_view.py
│   │   └── settings_view.py
│   ├── widgets/
│   │   ├── pdf_viewer.py
│   │   ├── markdown_editor.py
│   │   ├── dual_pane_host.py
│   │   ├── sidebar_tree.py
│   │   ├── search_panel.py
│   │   ├── status_strip.py
│   │   ├── empty_state.py
│   │   ├── warning_banner.py
│   │   └── dialogs/
│   └── styles/
│       ├── themes.py
│       └── qss_styles.py
│
├── data/
│   ├── database/
│   │   └── research_pkm.db
│   ├── sources/
│   ├── notes/
│   ├── assets/
│   ├── exports/
│   ├── backups/
│   ├── temp/
│   └── logs/
│
├── docs/
│   ├── markdown_conventions.md
│   ├── source_anchor_spec.md
│   ├── export_bundle_spec.md
│   ├── release_notes.md
│   └── migration_notes.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── ui/
│   └── fixtures/
│
└── scripts/
    ├── dev/
    └── release/
```

### 4.1. Quy tắc cấu trúc

1. Không đặt logic truy cập database trong UI.
2. Không đặt extraction logic rải rác trong nhiều widget.
3. Không trộn asset IO và markdown mutation vào cùng một service nếu không cần.
4. Mọi dữ liệu cục bộ phải nằm dưới `data/`.
5. Mọi thay đổi schema phải đi qua migration.
6. Mọi service phải có trách nhiệm rõ ràng và không chồng chéo mơ hồ.

---

## 5. Kiến trúc hệ thống

### 5.1. Các lớp chính

Ứng dụng gồm 6 lớp chính:

1. App Shell  
   Chịu trách nhiệm main window, điều hướng, toolbar, status bar, theme, workspace host.

2. Workspace Layer  
   Chịu trách nhiệm Library, Dual Pane, Research Board, Search UI.

3. Service Layer  
   Chịu trách nhiệm nghiệp vụ, orchestration giữa UI, extraction, index và DB.

4. Extraction Layer  
   Chịu trách nhiệm render PDF, trích text, crop bảng, capture ảnh, sinh source anchor.

5. Search/Index Layer  
   Chịu trách nhiệm lập chỉ mục và query trên notes, extracts, tags, metadata.

6. Persistence Layer  
   Chịu trách nhiệm models, sessions, migrations, settings, backup/restore.

### 5.2. Kiến trúc logic tổng thể

```text
┌────────────────────────────────────────────────────────────┐
│                         App Shell                          │
│  Main Window | Navigation | Toolbar | Status | Theme      │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    Workspace / Views                       │
│ Dashboard | Library | Dual Pane | Board | Search | Config │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                       Service Layer                        │
│ Source | Note | Extract | Asset | Tag | Link | Board      │
└────────────────────────────────────────────────────────────┘
              │                     │
              ▼                     ▼
┌───────────────────────┐   ┌──────────────────────────────┐
│ Extraction / Search   │   │ Persistence Layer            │
│ PDF | Anchors | FTS   │   │ SQLite | ORM | Migrations    │
│ Normalizers | Query   │   │ Settings | Backup | Restore  │
└───────────────────────┘   └──────────────────────────────┘
```

### 5.3. App shell boundaries

1. Shell chỉ chịu trách nhiệm layout và điều hướng.
2. Shell không được chứa logic extract hoặc parse PDF.
3. Shell không được chứa SQL trực tiếp.
4. Workspace là vùng hiển thị nghiệp vụ, nhưng business rules vẫn thuộc service/extraction layer.

---

## 6. Business rules chính thức

### 6.1. Source import

1. Mỗi source phải có `file_hash` hoặc fingerprint tương đương để hỗ trợ chống nhập trùng ở mức kỹ thuật.
2. Metadata đọc từ file PDF chỉ là dữ liệu gợi ý, không mặc định xem là chân lý hoàn toàn.
3. Source bị đổi path phải có cơ chế relink hoặc cảnh báo, không silently orphan.

### 6.2. Source note binding 1:1

1. Mỗi source PDF có thể có đúng một source note mặc định.
2. Chuyển tab PDF bên trái phải kích hoạt source note tương ứng bên phải.
3. Ngoài source note, người dùng vẫn có thể tạo concept note hoặc synthesis note độc lập.

### 6.3. Extract rules

1. Text extract phải lưu tối thiểu: `source_id`, `page_no`, `anchor`, `content_md`, `extract_type`.
2. Table extract phải có bước preview trước khi commit vào note hoặc DB.
3. Image capture phải lưu file vào `data/assets/` và chèn tham chiếu relative path vào note.
4. Không tạo extract “mồ côi” không có source_id.

### 6.4. Source anchor format

Format chuẩn v1:

```text
source://<source_id>?page=<page_no>&rect=<x0>,<y0>,<x1>,<y1>
```

Quy tắc:

1. `rect` là tùy chọn nhưng nên có nếu extract đến từ selection/crop cụ thể.
2. Nếu không có `rect`, anchor tối thiểu vẫn phải có `source_id` và `page_no`.
3. Không thay đổi format này mà không cập nhật docs và migration strategy.

### 6.5. Note model

1. Note phải có `note_type` rõ ràng: `source_note`, `concept_note`, `synthesis_note`, `board_note`.
2. Markdown là định dạng lưu gốc cho nội dung note.
3. `[[wikilink]]` phải resolve qua note title hoặc slug ổn định, không phụ thuộc vị trí file tạm thời.

### 6.6. Delete policy

### 6.5a. Taxonomy note và quy ước đặt tên (chính thức)

Hệ thống có đúng 4 loại note với vai trò và câu hỏi trung tâm riêng biệt:

| Loại | Câu hỏi trung tâm | Quy ước đặt tên |
|---|---|---|
| `source_note` | "Nguồn này nói gì?" | `source - {Tác giả} ({Năm})` — e.g. `source - Lent et al. (1994)` |
| `concept_note` | "Khái niệm này là gì?" | Tên khái niệm trực tiếp — e.g. `SCCT`, `TPB` |
| `synthesis_note` | "Nhiều ý ghép lại cho thấy điều gì?" | Bắt đầu bằng `~` |
| `board_note` | "Bảng phân tích cho thấy bức tranh chung nào?" | Bắt đầu bằng `!` |

**Quy tắc auto-naming cho `source_note` khi import PDF:**

1. Khi người dùng import PDF tại tab Thư viện nguồn, hệ thống đọc metadata PDF qua PyMuPDF `doc.metadata`.
2. Nếu có `author`:
   - 2 tác giả: dùng `{Ho1} & {Ho2}`
   - >=3 tác giả: dùng `{Ho1} et al.`
3. Nếu có `year`: lấy năm — e.g. `1994`
4. Auto-generate title: `source - {Tác giả} ({Năm})` — e.g. `source - Lent et al. (1994)`
5. `ImportSourceDialog` hiển thị title đã generate để người dùng xác nhận hoặc chỉnh tay.
6. Nếu metadata không có author/year → dùng filename (không có đuôi) làm title tạm.
7. Soft-warning nếu title quá chung chung (`ghi chú 1`, `note mới`, title ngắn hơn 5 ký tự, v.v.).
8. `source_note` title nên được cập nhật khi người dùng chỉnh metadata author/year.

**Quy tắc nhận diện note type khi tạo qua wikilink:**

1. `[[Nội dung]]` → tạo/resolve `concept_note`
2. `[[~ Nội dung]]` → tạo/resolve `synthesis_note`
3. `[[! Nội dung]]` → tạo/resolve `board_note`
4. Popup gợi ý khi gõ `[[` phải hiển thị nhãn theo loại note: `source -`, `concept -`, `synthesis -`, `board -`.

**Soft-warning cho note quality (không block cứng):**

| Loại note | Warning hiển thị |
|---|---|
| `source_note` | Thiếu author hoặc year trong metadata |
| `concept_note` | Không có bất kỳ outgoing wikilink nào |
| `board_note` | Chưa được gắn với board table nào |
| `synthesis_note` | Không có outgoing links tới note khác |
| Tất cả | Title quá chung chung hoặc quá ngắn |

### 6.6. Delete policy

1. Source: ưu tiên soft-delete hoặc trash state nếu đã có note/extract liên quan.
2. Note: có thể xóa mềm; nếu note bị link từ note khác thì phải cảnh báo.
3. Asset: không xóa cứng nếu còn note tham chiếu.
4. Extract: cho phép xóa, nhưng chỉ khi không làm hỏng cấu trúc note hiện tại một cách âm thầm.

### 6.7. Search integrity

1. Index search là dữ liệu phái sinh, có thể rebuild.
2. Không lưu search index như nguồn chân lý duy nhất.
3. Re-index lỗi phải báo rõ và không làm mất notes/source.

### 6.8. NULL semantics

1. `NULL` trong DB cho metadata hoặc anchor nghĩa là chưa có dữ liệu, không đồng nghĩa chuỗi rỗng.
2. `content_md` của extract không được là NULL khi extract đã commit.
3. Path asset/source không được silently normalize thành chuỗi trống.

---

## 7. Database schema chính thức

### 7.1. Bảng dữ liệu

Phiên bản v1.0 sử dụng các bảng chính sau:

1. sources
2. notes
3. extracts
4. assets
5. tags
6. note_tags
7. links
8. board_columns
9. board_rows
10. board_cells
11. app_settings
12. backups_log tùy chọn

### 7.2. Trường bắt buộc cần chú ý

- `sources.file_path`
- `sources.file_hash`
- `notes.note_type`
- `extracts.extract_type`
- `extracts.source_anchor`
- `app_settings.schema_version`

### 7.3. Schema logic đề xuất

#### sources

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
file_path         TEXT NOT NULL UNIQUE
file_hash         TEXT NOT NULL
title             TEXT
authors           TEXT
year              TEXT
doi               TEXT
metadata_json     TEXT
last_opened_page  INTEGER
is_deleted        INTEGER NOT NULL DEFAULT 0
created_at        TEXT NOT NULL
updated_at        TEXT NOT NULL
```

#### notes

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
source_id         INTEGER REFERENCES sources(id)
title             TEXT NOT NULL
slug              TEXT NOT NULL UNIQUE
note_type         TEXT NOT NULL
file_path         TEXT NOT NULL UNIQUE
summary           TEXT
is_deleted        INTEGER NOT NULL DEFAULT 0
created_at        TEXT NOT NULL
updated_at        TEXT NOT NULL
```

#### extracts

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
source_id         INTEGER NOT NULL REFERENCES sources(id)
note_id           INTEGER REFERENCES notes(id)
page_no           INTEGER NOT NULL
extract_type      TEXT NOT NULL   -- text | table | image
source_anchor     TEXT NOT NULL
content_md        TEXT NOT NULL
extra_json        TEXT
#### notes (CẬP NHẬT Phase 6 — thêm meta_json)

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
source_id         INTEGER REFERENCES sources(id)
title             TEXT NOT NULL
slug              TEXT NOT NULL UNIQUE
note_type         TEXT NOT NULL
file_path         TEXT NOT NULL UNIQUE
summary           TEXT
meta_json         TEXT    -- JSON metadata theo loại note
is_deleted        INTEGER NOT NULL DEFAULT 0
created_at        TEXT NOT NULL
updated_at        TEXT NOT NULL
```

meta_json schema theo type:

- `source_note`: `{"author": "Lent et al.", "year": "1994", "source_type": "journal", "publication": "...", "topic": "..."}`
- `concept_note`: `{"domain": "..."}`
- `synthesis_note`: `{"central_question": "...", "theme": "..."}`
- `board_note`: `{"board_type": "meta_analysis|literature|...", "scope": "...", "source_count": 0}`

```

#### tags

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
name              TEXT NOT NULL UNIQUE
color             TEXT
created_at        TEXT NOT NULL
```

#### note_tags

```sql
note_id           INTEGER NOT NULL REFERENCES notes(id)
tag_id            INTEGER NOT NULL REFERENCES tags(id)
PRIMARY KEY (note_id, tag_id)
```

#### links

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
from_note_id      INTEGER NOT NULL REFERENCES notes(id)
to_note_id        INTEGER NOT NULL REFERENCES notes(id)
link_type         TEXT NOT NULL   -- wikilink | manual | inferred
created_at        TEXT NOT NULL
```

#### boards (THÊM Phase 6 — entity board độc lập)

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
title             TEXT NOT NULL
board_type        TEXT    -- meta_analysis | literature | theory | factor | method | gap | other
linked_note_id    INTEGER REFERENCES notes(id) ON DELETE SET NULL
scope             TEXT
created_at        TEXT NOT NULL
updated_at        TEXT NOT NULL
```

#### board_rows (CẬP NHẬT Phase 6 — thêm board_id)

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
board_id          INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE
label             TEXT NOT NULL
sort_order        INTEGER NOT NULL DEFAULT 0
```

#### board_columns (CẬP NHẬT Phase 6 — thêm board_id)

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
board_id          INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE
label             TEXT NOT NULL
sort_order        INTEGER NOT NULL DEFAULT 0
```

#### board_cells (không đổi)

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
row_id            INTEGER NOT NULL REFERENCES board_rows(id)
col_id            INTEGER NOT NULL REFERENCES board_columns(id)
linked_note_id    INTEGER REFERENCES notes(id)
content_md        TEXT
updated_at        TEXT NOT NULL
```

#### app_settings

```sql
id                INTEGER PRIMARY KEY AUTOINCREMENT
setting_key       TEXT NOT NULL UNIQUE
setting_value     TEXT NOT NULL
```

Quy tắc:

1. Mọi thay đổi schema phải có migration file.
2. Không sửa schema production local trực tiếp mà không có migration.
3. Không được tự động xóa DB cũ để thay DB mới.
4. Nếu migration thất bại, app phải dừng an toàn và báo lỗi.

---

### 7.4. Board templates chuẩn (Phase 6)

Khi khởi tạo board, người dùng chọn từ 3 template. `BoardService.create_from_template(template_name, title)` tu dong tao cot va board record tuong ung:

#### Template "Đầy đủ" (meta_analysis — 34 cột)

ID, Ma nghien cuu, Tac gia, Nam, Tieu de, Quoc gia/Boi canh, Loai nguon, Muc tieu nghien cuu, Cau hoi nghien cuu, Ly thuyet/khung phan tich, Chu de chinh, Bien doc lap, Bien phu thuoc, Bien trung gian/dieu tiet, Doi tuong nghien cuu, Co mau, Phuong phap nghien cuu, Cong cu phan tich, Thiet ke nghien cuu, Thang do/chi bao, Ket qua chinh, Huong tac dong, Effect size, Loai effect size, SE/SD, CI thap, CI cao, p-value, Chat luong nghien cuu, Han che, Ghi chu ma hoa, Link source_note, Link concept_note, Link synthesis_note

#### Template "Chỉ tổng hợp tài liệu" (literature — 20 cột)

ID, Ma nghien cuu, Tac gia, Nam, Tieu de, Quoc gia/Boi canh, Loai nguon, Muc tieu nghien cuu, Cau hoi nghien cuu, Ly thuyet/khung phan tich, Chu de chinh, Bien doc lap, Bien phu thuoc, Phuong phap nghien cuu, Ket qua chinh, Han che, Ghi chu ma hoa, Link source_note, Link concept_note, Link synthesis_note

#### Template "Tạo Board note" (board_note markdown)

Không tạo board table. Tạo một `board_note` moi voi template Markdown chuan gom: Muc dich cua board, Bang nen, Cau truc phan tich, Cac mau hinh noi bat, Nhom/chum noi dung chinh, Khoang trong / diem con thieu, Ham y doi voi he thong note, Ham y doi voi nghien cuu, Ket luan tam thoi.

**Quy tắc gắn board ↔ board_note:**

- Template (i) và (ii): sau khi tạo board, hệ thống hỏi có muốn tạo kèm `board_note` khong; neu co thi ``boards.linked_note_id` = note mới tạo.
- Template (iii): chỉ tạo note, không tạo board table; ``board_note` có thể gắn vào board sau.
- Trong `BoardView`, nếu `board.linked_note_id` tồn tại thì hiện nút "Mở Board note".

---

## 8. Settings và lưu trữ cục bộ

### 8.1. Settings bắt buộc

1. Default source folder
2. Default notes folder
3. Default assets folder
4. Autosave interval
5. Export folder
6. Backup folder
7. Recent projects limit
8. UI theme neu kha thi
9. Markdown preview mode
10. Search scope defaults

### 8.2. Data safety rules

1. Có autosave.
2. Có manual save.
3. Có backup.
4. Có restore.
5. Không được silently discard user changes.
6. Save lỗi phải báo rõ.
7. Import hoặc extraction lỗi một phần phải có báo cáo chi tiết.

### 8.3. Single-instance lock

1. App chỉ được có một instance ghi dữ liệu trên cùng DB tại một thời điểm.
2. Dùng lock file hoặc cơ chế tương đương.
3. Nếu phát hiện instance khác đang chạy, cảnh báo bằng tiếng Việt và không mở thêm instance ghi dữ liệu.

---

## 9. UI và UX pattern chính thức

### 9.1. Cấu trúc main window

```text
┌─────────────────────────────────────────────────────────────────┐
│  Ứng dụng Quản lý Kiến thức Nghiên cứu         [ _ ][ □ ][ X ] │
├────────────────┬────────────────────────────────────────────────┤
│ Trang chính    │ Toolbar theo ngữ cảnh                         │
│ Thư viện nguồn │────────────────────────────────────────────────│
│ Không gian làm │                                                │
│ Research Board │         Vùng nội dung trung tâm               │
│ Thiết lập      │                                                │
├────────────────┴────────────────────────────────────────────────┤
│ Trạng thái: Sẵn sàng | DB: OK | Autosave: Bật | Theme: Sáng    │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2. Quy tắc UX bắt buộc

1. Thao tác dài như render PDF lớn, crop bảng, export bundle, backup/restore phải có progress indicator nếu đủ dài.
2. Không block UI thread bằng xử lý nặng.
3. Mọi lỗi phải có thông báo dễ hiểu bằng tiếng Việt.
4. Các view phụ thuộc dữ liệu phải có empty state rõ ràng.
5. Chuyển tab và chuyển source-note phải mượt, không reset vô lý.
6. Selection trên PDF và insertion vào note phải ít bước bấm nhất có thể.

---

## 10. Service layer chính thức

Các service bắt buộc:

1. SourceService
2. NoteService
3. ExtractService
4. AssetService
5. TagService
6. LinkService
7. BoardService
8. SearchService
9. ExportService
10. SettingsService
11. BackupService
12. MigrationService
13. AppLockService

Quy tắc:

1. UI chỉ gọi service, không gọi SQL trực tiếp.
2. Extraction layer không được phụ thuộc UI.
3. Service phải trả về error có cấu trúc hoặc exception rõ nghĩa.

---

## 10.1. Service Cheatsheet — Khi nào dùng service nào?

### Tóm tắt 13 services chính

| Service | Mục đích | Trách nhiệm chính | Ví dụ use case |
|---|---|---|---|
| **SourceService** | CRUD cho PDF sources | Import, list, delete, get metadata | "Thêm PDF vào thư viện" |
| **NoteService** | CRUD cho note Markdown | Create, read, update, delete note + metadata | "Tạo concept note mới" |
| **ExtractService** | Quản lý extract (text, table, image) | Create, list, delete extract; validate source anchor | "Lấy đoạn text từ PDF" |
| **AssetService** | Quản lý asset (ảnh, file tạm) | Save image, delete, list assets; handle file IO | "Lưu screenshot từ PDF" |
| **LinkService** | Quản lý liên kết hai chiều | Create/delete links; resolve [[wikilinks]]; relink sau import | "Tạo [[Concept A]] để link" |
| **TagService** | CRUD cho tag | Create, list, attach, detach tags | "Gắn tag '#research' cho note" |
| **BoardService** | Quản lý Research Board | Create/delete board; add/remove rows/cols; manage cells | "Tạo meta-analysis board mới" |
| **SearchService** | Full-text search và indexing | Index note/extract; query by keyword; rebuild FTS | "Tìm note chứa từ 'resilience'" |
| **ExportService** | Export bundle sạch | Generate clean text bundle; export metadata | "Xuất research findings ra" |
| **SettingsService** | Quản lý cài đặt ứng dụng | Read/write settings.json; validate | "Thay đổi folder backup" |
| **BackupService** | Backup/restore | Create backup archive; restore state; validate integrity | "Backup database hàng ngày" |
| **MigrationService** | Schema versioning + runner | Run migration; track version; handle rollback | "Nâng cấp schema DB" |
| **NoteUpdateOrchestrator** | Atomic note save transactions | Orchestrate: update → index → relink | "Lưu note với tất cả side-effects" |

### Decision Tree: Chọn service nào?

```
┌─ Người dùng thêm PDF mới?
│  → SourceService.import_source()
│
├─ Người dùng tạo/sửa note?
│  → NoteService (CRUD)
│  → Nếu sửa content + metadata + links một lúc?
│     → NoteUpdateOrchestrator.save_note()
│
├─ Người dùng lấy/lưu extract từ PDF?
│  → ExtractService (CRUD)
│  → Có phần validation source anchor?
│     → ExtractService.validate_anchor()
│
├─ Người dùng quản lý hình ảnh, file tạm?
│  → AssetService (file IO)
│
├─ Người dùng tạo/sửa [[wikilink]] trong note?
│  → LinkService.resolve_wikilinks_in_note()
│  → Hoặc khi import source cần relink?
│     → LinkService.relink_notes()
│
├─ Người dùng gắn tag cho note?
│  → TagService (attach/detach)
│
├─ Người dùng tạo hoặc sửa Research Board?
│  → BoardService (create, add rows/cols, update cells)
│
├─ Người dùng tìm kiếm note/extract?
│  → SearchService.search()
│  → Thêm note mới hoặc update content?
│     → SearchService.index_note_by_id() (tự động từ NoteUpdateOrchestrator)
│
├─ Người dùng muốn xuất findings?
│  → ExportService.export_bundle()
│
├─ Người dùng thay đổi cài đặt?
│  → SettingsService (read/write)
│
├─ Người dùng backup/restore?
│  → BackupService (create, restore)
│
└─ Database cần nâng cấp schema?
   → MigrationService.run_migrations()
```

### Service Dependencies Graph

```
UI / Views
   │
   ├─ NoteUpdateOrchestrator
   │   ├─ NoteService
   │   ├─ SearchService
   │   └─ LinkService
   │
   ├─ SourceService ─────────────┐
   │                             │
   ├─ LinkService ──────────────┤─ NoteService
   │                             │
   ├─ ExtractService ───────────┤
   │                             ▼
   ├─ AssetService ────────────► Persistence Layer (ORM, session)
   │                             ▲
   ├─ TagService ──────────────┤
   │                             │
   ├─ BoardService ────────────┤
   │                             │
   ├─ SearchService ──────────┤─ FTS5 Index
   │                             │
   ├─ ExportService ──────────┘
   │
   ├─ SettingsService ──────────► app_settings table
   │
   ├─ BackupService ────────────► Backup archive (file IO)
   │
   └─ MigrationService ────────► Alembic runner
```

### Hidden Complexity per Service

#### NoteService

**Trách nhiệm thực:**
- CRUD cho note file + metadata trong DB
- Keep slug unique và stable
- Lazy-load relationships (optimize query)
- Handle soft-delete

**Complexity ẩn:**
- Note slug dùng để resolve [[wikilink]], không thể đổi tùy tiện
- note_type ảnh hưởng auto-naming rules cho source_note
- Content file và DB record phải đồng bộ (nếu để lag thì dễ ghép sai)
- Delete note phải check incoming/outgoing links trước

**Khi nào dùng:**
- Thêm concept note mới
- Update note title hoặc metadata
- Xóa note (nhưng check impact trước dùng `get_note_delete_impact()`)
- Load note để chỉnh sửa

**Khi nào KHÔNG dùng:**
- Không dùng để update content + index + relink lúc lúc (dùng NoteUpdateOrchestrator)
- Không dùng để resolve [[wikilink]] (dùng LinkService.resolve_wikilinks_in_note())
- Không dùng để search note (dùng SearchService)

#### LinkService

**Trách nhiệm thực:**
- Manage bidirectional links: wikilink, manual, inferred
- Parse [[...]] pattern từ markdown
- Resolve wikilink label → target note (dùng slug)
- Upsert/delete links atomically
- Cleanup stale links

**Complexity ẩn:**
- [[text]] có thể resolve theo slug hoặc exact title match
- Cùng một note có thể được link với weight khác nhau (count occurrences)
- Wikilink không tìm được target thì được lưu lại không (soft fail)
- Xóa source note phải xóa cả outgoing wikilinks

**Khi nào dùng:**
- Tạo manual link giữa 2 note
- Parse và resolve [[wikilink]] khi save note
- Tìm incoming links tới một note
- Cleanup wikilinks khi update note content

**Khi nào KHÔNG dùng:**
- Không dùng để find notes (dùng SearchService hoặc graph query nếu cần)
- Không dùng để load note (dùng NoteService)

#### SearchService

**Trách nhiệm thực:**
- Full-text index trên note + extract
- FTS5 query, rebuild index
- Soft-delete handling (không index deleted items)

**Complexity ẩn:**
- Index là derived data, có thể rebuild anytime
- Content update phải trigger re-index (tự động từ NoteUpdateOrchestrator)
- Rebuild index chậm nếu quá nhiều note (nên async)
- Query parser phải handle diacritics và special chars

**Khi nào dùng:**
- User gõ keyword vào search box
- Manual rebuild index (admin, troubleshooting)
- List orphan notes (N+1 optimization)

**Khi nào KHÔNG dùng:**
- Không dùng để get_by_id (dùng NoteService)
- Không dùng để manage links (dùng LinkService)

#### NoteUpdateOrchestrator

**Trách nhiệm thực:**
- Atomic transaction: save note content + metadata + index + relink
- Validate note trước save (soft validation)
- Guarantee side-effects thứ tự và consistency

**Complexity ẩn:**
- Phải gọi đúng thứ tự: NoteService → SearchService → LinkService
- Nếu step nào fail, toàn bộ rollback
- Validation chỉ warning (không block save)

**Khi nào dùng:**
- UI autosave sau khi user sửa markdown editor
- Batch update nhiều note cùng lúc
- Ensure nếu save content thì cũng index + relink (không thể save riêng lẻ)

**Khi nào KHÔNG dùng:**
- Chỉ update metadata (không sửa content) → dùng NoteService.update_meta()
- Chỉ add/remove link → dùng LinkService.upsert_manual_link()
- Chỉ re-index (không sửa content) → dùng SearchService.index_note_by_id()

#### ExtractService

**Trách nhiệm thực:**
- CRUD cho extract record (text, table, image)
- Validate source anchor format
- Link extract → note

**Complexity ẩn:**
- Extract phải có source_anchor (không có là lỗi)
- Extract có thể orphan từ note (delete extract nhưng giữ content)
- Image extract thường lưu file tách (asset) + reference trong extract

**Khi nào dùng:**
- Lưu text selection từ PDF
- Lưu table crop hoặc image capture

**Khi nào KHÔNG dùng:**
- Không dùng để save content vào note (dùng NoteService)
- Không dùng để search extract (dùng SearchService)

#### BoardService

**Trách nhiệm thực:**
- Create/update board
- Manage rows, columns, cells
- Link board → board_note nếu cần
- Validate cell content (optional)

**Complexity ẩn:**
- Board có 3 template: meta_analysis (34 col), literature (20 col), board_note (markdown)
- Thêm column/row phải cập nhật sort_order
- Delete column/row phải xóa tất cả cells (cascade)
- Cell có thể link tới note hoặc chứa markdown

**Khi nào dùng:**
- Tạo board mới từ template
- Thêm/xóa row hoặc column
- Update cell content hoặc linked_note

**Khi nào KHÔNG dùng:**
- Không dùng để update board_note metadata (dùng NoteService)

#### Query Optimization

**Module:** `core/storage/query_optimization.py`

**Mục đích:** Tập hợp các helper functions để tối ưu query pattern (eager-load, DTO conversion, eliminate N+1):

- `eager_load_note_with_relationships(session, note_id)` — Load note + all relationships (source, extracts, assets, tags, links, project) trong 1-2 queries
- `eager_load_notes_list(session, note_ids)` — Batch load notes + relationships, return dict
- `get_note_delete_impact(session, note_id)` — Analyze incoming/outgoing links + references, return DTO with counts
- `list_orphan_note_ids_efficient(session)` — Find notes without any links
- `list_notes_for_management_efficient(session)` — List notes + project names (1 query with LEFT JOIN)
- `QueryCounter` — Debug utility

**Khi nào dùng:**
- Khi cần load note kèm tất cả relationships (eager-load là bắt buộc)
- Khi cần impact analysis trước delete (dùng `get_note_delete_impact()`)
- Khi list orphan notes (dùng subquery thay loop)

**Khi nào KHÔNG dùng:**
- Query đơn giản (load note by id) → dùng NoteService.get_by_id()
- Search → dùng SearchService

---

## 11. Quy tắc phát triển cho AI Agent

### 11.1. Coding standards

1. Tuân thủ PEP 8.
2. Bắt buộc dùng type hints.
3. Bắt buộc có docstring cho class và function public theo format:
   ```python
   def save_note(self, note_id: int, content: str) -> None:
       """Lưu nội dung note và trigger re-index + relink.
       
       Args:
           note_id: ID của note.
           content: Nội dung Markdown mới.
       
       Returns:
           None
       
       Raises:
           NoteNotFoundError: Nếu note không tồn tại.
           NoteSaveError: Nếu lưu file thất bại.
       
       Notes:
           - Tự động index trong FTS5
           - Tự động resolve [[wikilink]] từ content
           - Nếu bất kỳ step nào fail, không save gì cả
       """
   ```
4. Mỗi file chỉ nên có một trách nhiệm chính.
5. Max line length đề xuất là 100.
6. Bắt buộc tách interface, service, extraction, persistence và UI rõ ràng.
7. Bắt buộc document hidden complexity (điều gì khó thay đổi, phụ thuộc ẩn, side-effect) trong docstring "Notes:" hoặc "Complexity:" section:
   ```python
   def resolve_wikilinks_in_note(self, note_id: int) -> list[int]:
       """...
       
       Complexity:
       - slug được dùng để resolve [[...]], không được thay đổi tùy tiện
       - mỗi target note có thể được link multiple times (count occurrences)
       - wikilink không tìm được → soft fail (log warning nhưng không throw)
       - xóa source note phải cleanup tất cả outgoing wikilinks
       """
   ```

### 11.2. Testing requirements

| Loại test | Bắt buộc cho v1.0 |
|---|---|
| Unit tests cho anchor generation | Co |
| Unit tests cho text/table normalization | Co |
| Unit tests cho markdown/link resolution | Co |
| Unit tests cho migration runner | Co |
| Integration tests cho import source → create note → extract → search | Co |
| UI smoke tests cho main shell và dual pane | Co |
| Coverage target | Tối thiểu 80% cho core services, extraction và search |

### 11.3. Error handling

1. Không được `except Exception` rồi bỏ qua im lặng.
2. Mọi lỗi extraction phải chỉ rõ source, page hoặc action gây lỗi nếu có thể.
3. Mọi lỗi DB phải rollback transaction.
4. Mọi lỗi migration phải log rõ và dừng an toàn.
5. Mọi lỗi save_state hoặc autosave phải có fallback rõ ràng.

### 11.4. Logging policy

Bắt buộc log các nhóm sự kiện sau:

1. App start và shutdown
2. DB migration
3. Backup và restore
4. Import source và export bundle
5. Create, update, delete source/note/extract
6. Re-index search
7. Warning và error quan trọng

### 11.5. Definition of Done bắt buộc

Một task chỉ được xem là hoàn thành khi thỏa tất cả điều kiện sau:

1. Code chạy được
2. Không phá hành vi hiện có
3. Có test phù hợp
4. Test pass
5. Có cập nhật ROADMAP
6. Có cập nhật CHANGELOG trong file này nếu có ảnh hưởng kiến trúc hoặc schema

### 11.6. Complexity Guardrails (bắt buộc cho mọi task mới)

Các quy tắc dưới đây là tiêu chuẩn thiết kế để giảm độ phức tạp tích lũy theo thời gian.

1. Complexity gate trước merge:
   - Không chấp nhận thay đổi nếu tạo thêm "change amplification" (một thay đổi nhỏ phải sửa nhiều nơi không liên quan).
   - Không chấp nhận thay đổi nếu tăng "unknown unknowns" (khó đoán điểm cần sửa ở lần sau).
   - Không chấp nhận thay đổi nếu tăng cognitive load mà không có lợi ích rõ ràng.
2. Module phải đủ "deep":
   - Ưu tiên interface nhỏ, implementation đủ mạnh.
   - Tránh tạo lớp mỏng chỉ pass-through method/variable mà không thêm giá trị abstraction.
3. Information hiding:
   - Kiến thức dễ thay đổi (format, rule mapping, fallback policy) phải gom vào một module chịu trách nhiệm.
   - Không để cùng một rule nghiệp vụ xuất hiện ở nhiều lớp UI/service khác nhau.
4. Design it twice cho thay đổi lớn:
   - Với thay đổi ảnh hưởng từ 2 module trở lên, phải nêu ít nhất 2 phương án trước khi code.
   - Decision log phải ghi vì sao chọn phương án hiện tại và vì sao bỏ phương án còn lại.
5. Error policy theo mức:
   - Cấm `except ...: pass` ở production path.
   - Lỗi có thể phục hồi: log cảnh báo có ngữ cảnh + fallback rõ ràng.
   - Lỗi nghiệp vụ người dùng thấy được: hiển thị thông điệp tiếng Việt rõ ràng.
   - Lỗi phá vỡ tính đúng dữ liệu: fail-fast, rollback transaction, không tiếp tục âm thầm.
6. Naming và consistency:
   - Tên API phải mô tả đúng ý nghĩa nghiệp vụ, không mơ hồ (`process_data`, `handle_stuff`, v.v.).
   - Một khái niệm chỉ dùng một tên thống nhất trong toàn codebase.
7. Documentation gần code:
   - Public API và business rule không hiển nhiên phải có docstring/comment ngắn mô tả "what + why".
   - Nếu thay đổi contract liên module, phải cập nhật docs tương ứng trong cùng task.
7. Nếu thay đổi schema thì phải có migration notes
8. Nếu thay đổi UI hoặc hành vi người dùng thì phải cập nhật README hoặc docs liên quan

---

## 12. Kế hoạch đóng gói và phát hành

### 12.1. Mục tiêu phát hành v1.0

1. Windows là nền tảng ưu tiên đầu tiên.
2. Có file `.exe` hoặc installer hoàn chỉnh.
3. Có thư mục dữ liệu local khởi tạo tự động.
4. Có DB local và settings mặc định được khởi tạo an toàn.
5. Có hướng dẫn dùng cơ bản và backup/restore.

### 12.2. Công cụ đóng gói

1. PyInstaller cho build standalone
2. Inno Setup cho installer Windows nếu cần

### 12.3. Ràng buộc phát hành

1. Không phát hành nếu migration chưa được kiểm tra.
2. Không phát hành nếu single-instance lock chưa ổn định.
3. Không phát hành nếu source anchor còn không nhất quán ở pipeline chính.
4. Không phát hành nếu extraction làm mất truy vết nguồn trong các workflow lõi.

---

## 13. Checklist bắt buộc trước khi AI Agent code

- [ ] Đã đọc file này từ đầu đến cuối
- [ ] Đã đọc `PKM_ROADMAP.md`
- [ ] Hiểu rõ ranh giới giữa UI, services, extraction, search và persistence
- [ ] Hiểu rõ 5 điểm khóa: local-first, source grounded, extract vs note, delete policy, schema versioning
- [ ] Có kế hoạch test cho task sắp làm
- [ ] Biết file nào sẽ bị tác động
- [ ] Biết có cần migration hay không

---

## 14. CHANGELOG

Quy tắc ghi chú:

1. Format: `YYYY-MM-DD | [Agent] | [Category] | Description`
2. Categories: ADDED, CHANGED, FIXED, REMOVED, DEPRECATED
3. Nếu có thay đổi schema, phải ghi thêm dòng “Migration Notes”

### 2026-04-22

ADDED | OpenAI GPT-5.4 Thinking | INITIAL | Khởi tạo tài liệu kiến trúc chuẩn cho Ứng dụng Desktop Quản lý Kiến thức Cá nhân phục vụ nghiên cứu. Xác lập tech stack, cấu trúc thư mục, ranh giới shell-service-extraction-search-persistence, business rules, database policy, UI rules, testing requirements, migration rules và checklist bắt buộc cho AI Agent.

CHANGED | OpenAI GPT-5.4 Thinking | BUSINESS_RULES | Khóa 5 nguyên tắc không được mơ hồ trong toàn dự án: local-first, source grounded, extract khác note, delete policy rõ ràng và SQLite phải có schema versioning.

ADDED | OpenAI GPT-5.4 Thinking | DATA_SAFETY | Chính thức đưa single-instance lock, autosave, backup/restore, source anchor format và empty state tiếng Việt vào phạm vi kiến trúc v1.0.

### 2026-04-22 — Phase 2 Data Layer hoàn thành

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SCHEMA | Triển khai toàn bộ schema v1 với 11 bảng: sources, notes, extracts, assets, tags, note_tags, links, board_rows, board_columns, board_cells, app_settings. File: `core/storage/models.py`.

### 2026-04-23 — Performance Optimization Phase 1-3 hoàn thành

ADDED | GitHub Copilot (Claude Haiku 4.5) | OPTIMIZATION | Thực hiện 3 performance tasks:

#### Task 1: Query Optimization ✅
- Tạo `core/storage/query_optimization.py` (300+ LOC) với helper functions: `eager_load_note_with_relationships()`, `eager_load_notes_list()`, `get_note_delete_impact()`, `list_orphan_note_ids_efficient()`, `list_notes_for_management_efficient()`
- Giải quyết N+1 query patterns trong SearchService, NoteService
- Tạo Alembic migration 0008 với 10 database indexes trên FK columns
- Kết quả: 6-20x performance improvement cho query patterns chính
- Validation: 375/375 tests pass

#### Task 2: Note Save Transaction ✅
- Tạo `core/services/note_update_orchestrator.py` để atomic transaction note save
- Pull complexity downward: orchestrate content → metadata → index → relink trong 1 method
- Thêm `LinkService.resolve_wikilinks_in_note()` để parse + resolve [[wikilinks]] từ markdown
- Soft validation trước save (không block, chỉ warning)
- Batch save support cho bulk operations
- Validation: 375/375 tests pass, no regressions

#### Task 3: Service Interface Docs ✅
- Thêm "Service Cheatsheet" section với:
  - Bảng 13 services: mục đích, trách nhiệm, ví dụ use case
  - Decision tree để chọn service phù hợp
  - Service dependency graph
  - Hidden complexity per service
- Cập nhật coding standards: bắt buộc docstring + complexity notes
- Định rõ transaction guarantees và orchestrator pattern

CHANGED | GitHub Copilot (Claude Haiku 4.5) | DOCUMENTATION | Cập nhật PKM_ARCHITECTURE.md phần "Service layer" với chi tiết decision tree và complexity analysis cho mỗi service chính (NoteService, LinkService, SearchService, NoteUpdateOrchestrator, BoardService, ExtractService). Thêm ví dụ docstring standard với Args, Returns, Raises, Notes, Complexity sections.

ADDED | GitHub Copilot (Claude Haiku 4.5) | DOCUMENTATION | Cập nhật PERFORMANCE_IMPROVEMENTS.md tracking 3 tasks hoàn thành với metrics: 375/375 tests pass, 450+ LOC code added, 0 breaking changes.



ADDED | GitHub Copilot (Claude Sonnet 4.6) | DATABASE | SQLAlchemy engine singleton (`core/storage/connection.py`) với PRAGMA foreign_keys=ON per-connection. Session context manager (`core/storage/session.py`) với expire_on_commit=False và auto-rollback.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | MIGRATION | Alembic setup hoàn chỉnh: `alembic.ini` (ASCII only), `core/storage/migrations/env.py` (render_as_batch=True cho SQLite), initial migration `20260422_0001_initial_schema_v1.py` tạo tất cả bảng và seed schema_version=1. MigrationService chạy programmatic.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | 6 services mới: SourceService (import/update/soft-delete/hard-delete/relink), NoteService (CRUD + file I/O + 1:1 source note rule), ExtractService (commit với anchor validation đầy đủ), TagService (get_or_create idempotent), LinkService (wikilink/manual/inferred, resolve_wikilink), BackupService (create/list/restore/prune).

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | BOOTSTRAP | bootstrap.py cập nhật lên 7 bước: thêm bước 5 (init_engine + init_session_factory) và bước 6 (run_migrations) sau startup_checks.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | TESTING | 81 unit tests mới cho Phase 2 (7 file). Tổng cộng 130/130 tests pass.

### 2026-04-23 — Phase 3 Dual Pane và Extraction hoàn thành

ADDED | GitHub Copilot (Claude Sonnet 4.6) | EXTRACTION | Extraction layer hoàn chỉnh: `core/extraction/anchors.py` (re-export), `normalizers.py` (normalize_text, table_to_markdown), `pdf_text.py` (open_document, render_page_to_bytes, extract_region_text), `pdf_table.py` (extract_table_from_region, tables_on_page), `pdf_image.py` (capture_region).

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | `core/services/asset_service.py` — save_image_asset, list_by_source, delete_asset. Lưu PNG vào ASSETS_DIR, tạo bản ghi Asset trong DB.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | UI_WIDGETS | Ba widget lõi cho dual pane: `PDFViewerWidget` (render PyMuPDF, zoom 8 bước, rubber-band selection), `MarkdownEditorWidget` (QPlainTextEdit + autosave 2s debounce + insert_extract/insert_table/insert_asset_ref), `DualPaneHost` (QSplitter 50/50, extraction toolbar, điều phối signals).

ADDED | GitHub Copilot (Claude Sonnet 4.6) | UI_DIALOGS | `ImportSourceDialog` — chọn file PDF + form metadata → gọi SourceService.import_source(). `TablePreviewDialog` — preview + chỉnh sửa bảng Markdown trước khi commit (enforce business rule).

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | UI_VIEWS | DashboardView: dữ liệu thực từ DB (recent sources, stats). LibraryView: danh sách real, filter, context menu, soft-delete. WorkspaceView: host DualPaneHost với QStackedWidget, empty state. MainWindow: wire up tất cả signals (import, open source, save note, backup).

ADDED | GitHub Copilot (Claude Sonnet 4.6) | TESTING | 26 tests mới: 18 unit (test_extraction.py) + 8 integration (test_phase3_workflow.py). Tổng 156/156 pass.

### 2026-04-23 — Phase 4 Search, Links và Board hoàn thành

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SEARCH | FTS5 search layer: `core/search/fts_index.py` (ensure_fts_table, index_note, index_extract, remove_from_index, search, rebuild_index), `core/search/query_parser.py` (build_fts_query với prefix wildcard + exclusion + phrase). SQLite FTS5 virtual table `fts_content` được tạo IF NOT EXISTS — không cần Alembic migration.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | `core/services/search_service.py` — SearchService orchestrates FTS index, index_note_by_id, index_extract_by_id, rebuild_all, search → list[SearchResult].

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | `core/services/board_service.py` — BoardService CRUD: create/rename/delete rows+cols, get/update cells, export_markdown, export_csv.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | `core/services/export_service.py` — ExportService: export_source_bundle (note+extracts → Markdown), export_board_markdown, export_board_csv.

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | UI_WIDGETS | MarkdownEditorWidget: thêm "Nhãn" button (→ NoteTagsDialog), backlinks counter (← N liên kết),_scan_and_create_wikilinks() sau save,_refresh_backlinks() sau load/save. Fixed QShortcut import từ PySide6.QtGui.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | UI_WIDGETS | `ui/widgets/search_panel.py` — SearchPanelDialog: QLineEdit + debounce 300ms + filter combo + QListWidget results. Signals: note_open_requested, source_open_requested.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | UI_DIALOGS | `ui/widgets/dialogs/note_tags_dialog.py` — NoteTagsDialog: add/remove tags từ note.

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | UI_VIEWS | BoardView: đầy đủ QTableWidget rows×cols, toolbar (add row/col, export MD/CSV), double-click cell edit, context menu rename/delete. Dùng BoardService.

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | UI_SHELL | MainWindow: wire_action_search → SearchPanelDialog,_action_export → ExportService. Xóa class MainWindow trùng lặp (bug từ session trước).

ADDED | GitHub Copilot (Claude Sonnet 4.6) | TESTING | 44 tests mới: test_search.py (18), test_board_service.py (14), test_phase4_workflow.py (12). Tổng 200/200 pass.

### 2026-04-23 — UI/Workflow refinement + FEAT-01 Phase A

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | Tối giản toolbar chính: bỏ các action trùng luồng theo tab (`Thêm nguồn`, `Lưu ghi chú`, `Tìm kiếm`, `Xuất văn bản`), giữ action `Sao lưu` ở mức toàn cục.

FIXED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | MarkdownEditorWidget: bổ sung highlight trực quan cho `[[wikilink]]`, cải thiện resolve wikilink bằng `slugify` để tương thích tiếng Việt; giữ quy ước tách biệt heading `#` và hashtag `#tag`.

FIXED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | SourceDetailPanel: chuẩn hóa trạng thái hiển thị/enable của nút mở tài liệu để tránh trạng thái mờ/khó đọc.

ADDED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | Thêm `core/services/graph_service.py` (FEAT-01 Phase A): sinh graph snapshot node/edge từ `notes` + `links`, filter cơ bản theo `note_type`, `tag`, `source_id`, hỗ trợ loại node cô lập.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung test cho GraphService và regression tests cho markdown editor (heading-vs-hashtag, wikilink slugify resolve).

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | FEAT-01 Phase B: thêm `ui/widgets/graph_view.py` với `GraphViewWidget` (`QGraphicsView`) render node/edge từ GraphService, pan/zoom cơ bản, filter theo note_type/tag/source_id, click node để mở source/note liên quan.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | `BoardView` thêm entry-point mở Graph view (dialog), relay signals `note_open_requested` và `source_open_requested` để MainWindow điều hướng đúng ngữ cảnh.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Thêm smoke tests cho Graph view (`TestGraphViewSmoke`) và kiểm tra `BoardView` có nút `Graph view`.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | FEAT-01 Phase C: mở rộng `GraphViewWidget` với tìm kiếm node theo title/slug/tag, highlight hàng xóm theo mức 1-hop/2-hop, fit-to-view và tương tác click để chọn node + double-click để mở.

ADDED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | FEAT-01 Phase D: mở rộng `GraphService` với virtualize (`limit_nodes`) cho đồ thị lớn, trả metadata `is_virtualized` và `virtualized_from` để UI hiển thị trạng thái tối ưu.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | FEAT-01 Phase D: `GraphViewWidget` hỗ trợ gom cụm theo tag, lưu layout cục bộ qua `SettingsService`, lưu preference virtualize/max-nodes và xóa/lưu layout theo ngữ cảnh.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung unit tests cho virtualize của GraphService và smoke tests cho UX controls/search của GraphView.

### 2026-04-24 — Phase 6 Planning: Note System & Research Board Enhancement

PLANNED | GitHub Copilot (Claude Sonnet 4.6) | ARCHITECTURE | Thêm section 6.5a: Taxonomy note 4 loại với quy ước đặt tên chính thức và soft-warning cho note quality. Auto-naming `source_note` từ PDF metadata khi import.

PLANNED | GitHub Copilot (Claude Sonnet 4.6) | SCHEMA | Phase 6 sẽ cần 2 migration: (1) `meta_json TEXT` vào bảng `notes`, (2) bảng `boards` mới + thêm `board_id NOT NULL` vào `board_rows` và `board_columns`. Migration (2) là breaking change với data hiện có (board cũ không có board_id).

PLANNED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | Refactor `BoardService` để scope tất cả thao tác theo `board_id`. Thêm `create_from_template(template_name, title)` với 3 template: `meta_analysis` (34 cột), `literature` (20 cột), `board_note` (markdown note, không tạo board table).

PLANNED | GitHub Copilot (Claude Sonnet 4.6) | UI | Thêm `NewNoteDialog` cho concept_note/synthesis_note/board_note với template Markdown per type. Cập nhật `ImportSourceDialog` auto-generate title từ PDF metadata. Thêm `BoardSelectorPanel` cho multi-board trong `BoardView`.

### 2026-04-24 — Phase 6 Sprint D implemented (Note Metadata & Quality)

ADDED | GitHub Copilot (GPT-5.3-Codex) | SCHEMA | Bổ sung cột `notes.meta_json` và ORM field tương ứng để lưu metadata theo `note_type`.

Migration Notes | Revision `20260424_0005_add_note_meta_json.py`: thêm `meta_json TEXT NULL` vào bảng `notes`, giữ tương thích dữ liệu cũ (giá trị mặc định NULL).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `NoteService` thêm `get_meta()` và `update_meta()` với validate payload theo `source_note`/`concept_note`/`board_note`; `SearchService` thêm `list_orphan_note_ids()` và `count_notes_by_type()`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `MarkdownEditorWidget` thêm nút `Metadata` mở dialog cấu hình metadata theo loại note; warning quality cho `source_note` kiểm tra cả `meta_json.author`/`meta_json.year`.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | Thêm `ui/widgets/dialogs/note_metadata_dialog.py` cho chỉnh metadata note theo từng `note_type` bằng giao diện tiếng Việt.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | `DashboardView` hiển thị thêm thống kê theo note type (`source_note`, `concept_note`, `synthesis_note`, `board_note`) và số `note mồ côi`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `ImportSourceDialog` đồng bộ metadata `author/year/source_type` vào `meta_json` của `source_note` ngay sau import.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung test migration cho `meta_json`, unit test metadata của `NoteService`, và unit test orphan detection của `SearchService`.

### 2026-04-24 — Phase 6 Note Naming & Wikilink Marker refinement

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `SourceService.build_source_note_title()` chuyển sang format `source - {Tác giả} ({Năm})`; rule tác giả: 2 tác giả dùng `A & B`, từ 3 tác giả dùng `A et al.`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `ImportSourceDialog` tự cập nhật gợi ý title `source_note` theo tác giả/năm trong form, cho phép override thủ công khi cần.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | Popup gợi ý `[[wikilink]]` hiển thị nhãn loại note (`source -`, `concept -`, `synthesis -`, `board -`) nhưng khi chèn vẫn dùng title thật của note.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `NewNoteDialog` chuẩn hóa marker khi tạo note mới: `[[...]]` cho `concept_note`, `[[~ ...]]` cho `synthesis_note`, `[[! ...]]` cho `board_note`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `NoteService.title_warnings()` cập nhật naming convention mới (`source -`, `~`, `!`) để tránh cảnh báo sai theo quy tắc cũ.

### 2026-04-24 — Safe cleanup preview cho note không còn dùng

ADDED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `NoteService` thêm `get_unused_note_candidates()` để liệt kê trước note nghi ngờ không còn dùng (`missing-file`, `orphan-no-link`) và `cleanup_unused_notes(note_ids)` để chỉ soft-delete theo lựa chọn người dùng, kèm dọn stale links liên quan.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | Thêm `ui/widgets/dialogs/note_cleanup_preview_dialog.py` hiển thị preview dạng checklist, cho phép giữ/xóa từng note trước khi áp dụng.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | `SettingsView` bổ sung nút thứ ba "Dọn note không còn dùng (có preview)"; luồng dọn chuyển sang an toàn hơn: preview -> user chọn -> apply.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung unit tests cho candidate preview/apply cleanup và smoke test xác nhận nút bảo trì mới trong Settings.

### 2026-04-24 — Lightweight source_note rename migration + NewNoteDialog wikilink UX

ADDED | GitHub Copilot (GPT-5.3-Codex) | MIGRATION | Thêm revision `0006_rename_source_note_titles` để tự động đổi title `source_note` cũ sang format `source - {Tác giả} ({Năm})` dựa trên metadata đã có trong DB (ưu tiên `notes.meta_json`, fallback `sources.authors/year`).

Migration Notes | Revision `20260424_0006_rename_source_note_titles.py`: data migration only (không đổi schema), không downgrade title cũ do không thể khôi phục chính xác.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `NewNoteDialog` hỗ trợ autocomplete `[[wikilink]]` từ các note sẵn có và note đang mở; popup vẫn hiển thị nhãn phân loại để phân biệt nhanh.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | Cả `MarkdownEditorWidget` và `NewNoteDialog` chỉ chèn title thật vào nội dung note khi chọn item từ popup; nhãn `source/concept/synthesis/board` không đi vào nội dung Markdown.

### 2026-04-24 — Settings maintenance buttons + wikilink demote flow

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | `SettingsView` thêm 2 hành động bảo trì: (1) chạy thủ công chuẩn hóa title `source_note` (idempotent), (2) làm mới catalog note cho popup `[[wikilink]]` và dọn orphan/link stale.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `NoteService` thêm `normalize_source_note_titles()` và `refresh_wikilink_note_catalog()`; trong đó refresh catalog chỉ dọn orphan stub note, soft-delete note thiếu file markdown và dọn link trỏ tới note đã xóa mềm (không chuẩn hóa title).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | `MainWindow` nối signal từ Settings để refresh catalog wikilink ở Workspace và làm mới các view liên quan ngay sau thao tác bảo trì.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `NoteWikilinksDialog`: khi xóa wikilink đã chọn, nội dung `[[...]]` tương ứng trong note được hạ về text thường chữ thường (đen, không nghiêng), đảm bảo trạng thái hiển thị đồng nhất với dữ liệu link hiện có.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | Bổ sung chuẩn hóa token wikilink legacy (`concept -`, `synthesis -`, `board -`) trước khi chèn để ngăn prefix hiển thị bị lưu vào nội dung note.

### 2026-05-03 — Workspace orchestration & error handling hardening

ADDED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | Thêm `core/services/workspace_orchestrator.py` (`WorkspaceOrchestrator`) để gom use-case mở source + bind source_note, commit extract, lưu asset, lưu note và đồng bộ relations (wikilink/tag/backlink/quality warning).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `ui/widgets/dual_pane_host.py` chuyển phần orchestration business sang `WorkspaceOrchestrator` (open source-note, commit text/table extract, save image asset, update last_opened_page).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `ui/widgets/markdown_editor.py` rút bớt logic domain khỏi widget: save/sync relations, catalog tags/wikilinks, backlink count và quality warning đều điều phối qua `WorkspaceOrchestrator`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | ERROR_POLICY | Loại bỏ các nhánh `except ...: pass` trong luồng dual-pane/editor/graph đã chỉnh; thay bằng log có ngữ cảnh và thông báo UI phù hợp với mức lỗi.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `GraphService.build_graph()` đồng bộ contract: hỗ trợ cả `source_id` (legacy) và `source_code` (ưu tiên `source_code` khi cùng cung cấp).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `GraphViewWidget` bật mặc định hiển thị isolated nodes để tránh đồ thị rỗng gây khó tìm node; bổ sung logging cho nạp tag suggestions.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Regression check sau refactor: toàn bộ suite `python -m pytest -q` xanh `297/297`.

### 2026-05-03 — Design guardrails theo triết lý giảm complexity

CHANGED | GitHub Copilot (GPT-5.3-Codex) | ARCHITECTURE_POLICY | Bổ sung mục `11.6 Complexity Guardrails` để chuẩn hóa kiểm soát độ phức tạp: complexity gate, deep module, information hiding, design-it-twice, error policy theo mức, naming consistency và documentation gần code.

### 2026-05-04 — Phase 7 Sprint 7A: Project Mode — Schema & Service

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SCHEMA | Thêm bảng `projects` (id, name, description, status active\|closed\|archived, is_deleted, created_at, updated_at, closed_at, meta_json) và bảng `project_note_refs` (project_id FK, note_id FK, added_at, UNIQUE constraint).

CHANGED | GitHub Copilot (Claude Sonnet 4.6) | SCHEMA | Thêm cột `notes.project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL`. NULL = Global note; non-NULL = Project-only note (thuộc đúng 1 project).

Migration Notes | Revision `20260504_0007_add_project_mode.py`: backward-compatible — tất cả notes hiện tại có project_id = NULL (Global). Không mất dữ liệu cũ.

ADDED | GitHub Copilot (Claude Sonnet 4.6) | SERVICES | Thêm `core/services/project_service.py` (`ProjectService`): CRUD project, activate/deactivate (lưu vào AppSettingRow key `active_project_id`), add/remove Global note refs, get_project_notes (trả `own` + `refs`), get_project_note_ids (dùng để filter search), soft_delete_project (SET NULL notes project-only → Global), export_project_bundle (copy Markdown files → standalone folder).

ADDED | GitHub Copilot (Claude Sonnet 4.6) | TESTING | 35 unit tests mới trong `tests/unit/test_project_service.py`. Tổng 332/332 pass.

**Business rules Project Mode (khóa từ 2026-05-04):**

- Source PDF không có project scope — luôn là Global.
- `note.project_id IS NULL` = Global note, hiển thị mọi mode.
- `note.project_id IS NOT NULL` = Project-only note, chỉ hiển thị khi project đang active.
- Chỉ Global notes (project_id IS NULL) mới có thể add vào `project_note_refs`.
- Xóa project (soft-delete) → note project-only SET NULL → trở thành Global.
- Đóng gói project = export folder Markdown standalone, không ảnh hưởng DB.
- Search trong Project mode = chỉ notes thuộc project (own + refs), không tìm toàn Global.

### 2026-05-04 — Phase 7 Sprint 7B: Service integration for Project context

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `NoteService.create_note()` hỗ trợ tham số `project_id`; thêm API `list_by_project()` và `list_global()` để tách rõ scope note.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `WorkspaceOrchestrator` thêm context project (`active_project_id`, `is_project_mode`, `get_active_project_note_ids`, `create_note_in_scope`) để UI không tự quyết định business logic scope.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SEARCH | `SearchService.search()` hỗ trợ filter `project_note_ids` nhằm giới hạn kết quả note theo phạm vi project khi cần.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung 19 tests cho scope project trong `NoteService`, `SearchService`, `WorkspaceOrchestrator`; tổng 351/351 pass tại thời điểm hoàn tất Sprint 7B.

### 2026-05-04 — Phase 7 Sprint 7C: Project Mode UI

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `SidebarWidget` có section `Dự án` (danh sách project, nút chuyển Global, nút mở quản lý) và signals cho activate/deactivate project.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | Thêm `ui/widgets/dialogs/project_manager_dialog.py` để tạo/đổi tên/kết thúc/xóa mềm project và thêm/xóa Global note refs.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | `MainWindow` thêm mode indicator trên toolbar (`Mode: Global` / `Mode: Project - {name}`), kết nối sidebar project signals, và đồng bộ project context vào `LibraryView` + `WorkspaceView`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `NewNoteDialog` thêm lựa chọn phạm vi lưu note (Global hoặc Project) khi đang ở Project mode; `MarkdownEditorWidget` gọi `WorkspaceOrchestrator.create_note_in_scope()` theo lựa chọn này.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | `LibraryView` và `WorkspaceView` áp dụng filter theo project context: chỉ hiển thị/mở sources liên quan notes của project active.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SEARCH_UI | `SearchPanelDialog` truyền `project_note_ids` khi có project active để kết quả tìm kiếm note tuân thủ scope project.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung smoke tests cho mode indicator, project manager dialog, scope selector trong new note dialog; tổng suite đạt 354/354 pass.

### 2026-05-04 — Phase 7 Sprint 7D: Project Bundle Export & Close Flow

CHANGED | GitHub Copilot (GPT-5.3-Codex) | EXPORT | `ExportService` bổ sung `export_project_bundle(project_id)` để xuất project thành thư mục Markdown standalone (`README.md`, `own/`, `refs/`).

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `ProjectService.export_project_bundle()` refactor thành delegate qua `ExportService` để tập trung hóa logic export và giảm lặp code.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_DIALOGS | `ProjectManagerDialog` thêm action `Đóng gói` với chọn thư mục output (QFileDialog), gọi service export và hiển thị kết quả cho người dùng.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Thêm integration tests `tests/integration/test_phase7_project_mode.py` (close project, export bundle qua ExportService, export qua ProjectService delegate, lỗi project không tồn tại, snapshot bundle sau soft-delete).

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Cập nhật UI smoke test cho ProjectManagerDialog có nút `Đóng gói` và thêm test tương tác luồng package button; toàn bộ suite đạt 360/360 pass.

### 2026-05-07 — Post-Phase7 Hardening: Source-note resilience + Note management UI

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SERVICES | `WorkspaceOrchestrator` thêm `ensure_source_note()` để đảm bảo source luôn có `source_note` hợp lệ trên disk; nếu record cũ thiếu file markdown thì soft-delete record lỗi và tự tạo note mới an toàn.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WORKSPACE | `DualPaneHost.open_source()` nhận `recovery_notice` từ orchestrator và hiển thị thông báo tiếng Việt rõ ràng khi app tự phục hồi ghi chú nguồn.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | IMPORT_WORKFLOW | `ImportSourceDialog` dùng orchestrator để đảm bảo invariant “mỗi PDF có 1 source_note” ngay khi nhập vào Thư viện nguồn.

ADDED | GitHub Copilot (GPT-5.3-Codex) | UI_VIEWS | Thêm `NoteManagementView` trong điều hướng chính để quản trị vòng đời note: liệt kê toàn bộ notes với nhãn Global/Project, tạo mới, mở chỉnh sửa có cảnh báo, xóa mềm có phân tích ảnh hưởng.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SETTINGS_MAINTENANCE | `SettingsView` thêm action audit read-only cho source_note thiếu file markdown nhằm giúp người dùng phát hiện sớm sai lệch trước khi thao tác.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung unit tests và UI smoke tests cho auto-recovery notice, audit missing source-note files, và màn hình quản lý ghi chú.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_LABELS | Sidebar đổi nhãn `Research Board` -> `Bảng nghiên cứu` và section header `Dự án` -> `Project` theo yêu cầu hiển thị mới.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_NOTE_MANAGEMENT | `NoteManagementView` bổ sung bộ lọc nâng cao (text + note type + scope + include deleted), khung preview nội dung note trước chỉnh sửa, và tùy chọn `Xóa cứng` với cảnh báo 2 lớp.

### 2026-05-07 — Markdown Editor Quote UX (Zettlr-like)

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `MarkdownEditorWidget` bổ sung xử lý Enter trong blockquote: nếu dòng quote đang có nội dung thì tiếp tục tạo dòng `> ` mới; nếu dòng quote rỗng (`> `) thì thoát blockquote để quay lại đoạn thường.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | Bổ sung quote shading theo full-row bằng `QTextEdit.ExtraSelection` + `FullWidthSelection` để vùng quote rõ ràng hơn khi soạn thảo.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Thêm smoke tests cho hành vi Enter tiếp tục/thoát blockquote và overlay shading; xác nhận lại toàn bộ `tests/ui/test_smoke.py` đạt 54/54 pass.

### 2026-05-07 — Editor Font Preferences in Settings

CHANGED | GitHub Copilot (GPT-5.3-Codex) | SETTINGS_UI | `SettingsView` bổ sung cấu hình font cho editor với 2 khóa `editor.fontFamily` và `editor.fontLigatures`, cho phép người dùng tùy chỉnh danh sách ưu tiên font và bật/tắt ligature.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `MarkdownEditorWidget` đọc cài đặt font từ Settings và resolve theo danh sách ưu tiên (ưu tiên `Fira Code`, fallback `Roboto Mono`, sau đó monospace khả dụng), đồng thời áp dụng OpenType features `liga`/`calt` theo cấu hình.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung test defaults cho `SettingsService` và smoke assertion cho controls font trong SettingsView; `tests/unit/test_settings_service.py` đạt 9/9 pass, nhóm smoke Settings/Markdown editor đạt 11/11 pass.

### 2026-05-07 — Non-render Math Expression Highlighting

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_WIDGETS | `MarkdownEditorWidget` bổ sung nhận diện cú pháp biểu thức toán LaTeX để hiển thị dễ nhận biết (không render công thức): `$...$`, `$$...$$`, `\(...\)`, `\[...\]`, bao gồm cả block nhiều dòng với trạng thái highlighter.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_THEME | Áp dụng math code-like theme trong editor bằng `QTextCharFormat` (foreground/background + mono font) để phân biệt nội dung toán với văn bản thường mà không tăng phụ thuộc render engine.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_THEME | Tinh chỉnh math palette theo dark/light mode dựa trên Qt palette và tô màu chi tiết theo token LaTeX (delimiter, command, number, operator, bracket) để gần phong cách syntax coloring của code editor.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_THEME | Loại bỏ hardcode `font-family` cho `QPlainTextEdit#markdown_editor` trong QSS để lựa chọn font từ Settings được áp dụng nhất quán cho nội dung note.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | Dời mode indicator (`Mode: Global/Project`) khỏi toolbar sang `SettingsView` để ưu tiên không gian thanh công cụ cho thao tác chính.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | Gỡ hoàn toàn nút `Project` trên toolbar để tránh trùng vai trò với khu vực Project trong sidebar/settings.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SETTINGS | Mode indicator trong `SettingsView` được nâng cấp thành badge màu: Global (xanh lá) và Project (xanh dương) để tăng tốc độ nhận diện trạng thái làm việc.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTING | Bổ sung smoke tests xác nhận highlight cho inline math và display math block; nhóm `TestMarkdownEditorSmoke` đạt 12/12 pass.
