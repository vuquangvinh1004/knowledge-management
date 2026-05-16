# ỨNG DỤNG DESKTOP QUẢN LÝ KIẾN THỨC CÁ NHÂN PHỤC VỤ NGHIÊN CỨU

## TÀI LIỆU ĐẶC TẢ TỔNG HỢP — PHIÊN BẢN CUỐI

---

## MỤC LỤC

1. Mục tiêu ứng dụng
2. Phạm vi hệ thống
3. Nguyên tắc thiết kế
4. Tech stack và kiến trúc
5. Cấu trúc giao diện
6. Chi tiết các module chức năng
7. Quy tắc extraction và tổ chức tri thức
8. Import, Export và nhập liệu
9. Search, Research Board và tổng hợp nghiên cứu
10. Quản lý dữ liệu và an toàn
11. Thiết kế database
12. Kiến trúc service layer
13. Quy tắc giao diện và UX
14. Phím tắt
15. Performance baseline
16. Lộ trình phát triển
17. Quy tắc viết code
18. Tiêu chí hoàn thành tối thiểu
19. Hướng mở rộng tương lai

---

## 1. MỤC TIÊU ỨNG DỤNG

Ứng dụng được xây dựng để phục vụ một người dùng duy nhất là người làm nghiên cứu hoặc học thuật cần đọc PDF, trích xuất nội dung, ghi chú cá nhân và tổng hợp liên tài liệu trên máy tính cá nhân.

- Chạy trên Desktop
- Dữ liệu lưu cục bộ trên máy người dùng
- Không cần tài khoản, không cần phân quyền
- Không cần kết nối mạng để sử dụng các chức năng chính
- Ngôn ngữ giao diện: Tiếng Việt

Ứng dụng hỗ trợ người dùng thực hiện nhanh và chính xác các công việc:

- Quản lý thư viện PDF nghiên cứu
- Mở nhiều tài liệu cùng lúc
- Gắn note Markdown tương ứng với từng tài liệu
- Bôi chọn văn bản và chuyển thành trích dẫn có dẫn nguồn
- Chọn vùng bảng, xem trước và chuyển thành Markdown table
- Chụp ảnh sơ đồ hoặc hình từ PDF vào thư mục asset
- Tạo note khái niệm và note tổng hợp
- Liên kết hai chiều giữa các note bằng `[[ ]]`
- Gắn tag theo chủ đề nghiên cứu
- Tìm kiếm nội dung và metadata
- Tổng hợp nhiều tài liệu trên Research Board
- Xuất clean text để nạp vào NotebookLM, ChatGPT hoặc công cụ AI khác

---

## 2. PHẠM VI HỆ THỐNG

### Bao gồm trong v1

- Quản lý nguồn PDF
- Dual-pane PDF + Markdown
- Binding 1:1 giữa source PDF và source note
- Trích text từ PDF sang Markdown có deep-link nguồn
- Table crop + convert sang Markdown
- Image capture từ PDF vào assets
- Tagging
- Wikilink `[[ ]]`
- Backlinks cơ bản
- Search cơ bản
- Research Board bản đầu
- Export notes và clean text bundles
- Autosave
- Backup và restore
- Single-instance lock
- Schema migration

### Không bao gồm trong v1

- Cloud sync
- Cộng tác nhiều người dùng
- Web clipper nâng cao
- OCR mặc định cho mọi tài liệu scan
- Local LLM runtime tích hợp sẵn
- Reference manager chuẩn đầy đủ như Zotero replacement
- Plugin marketplace

---

## 3. NGUYÊN TẮC THIẾT KẾ

1. PDF là nguồn gốc, note là lớp tri thức cá nhân.
2. Tốc độ thao tác quan trọng hơn quy trình phức tạp.
3. Truy vết nguồn phải rõ ràng và bền vững.
4. Không biến ứng dụng thành note app chung chung.
5. Dữ liệu phải an toàn, lưu cục bộ, có sao lưu và phục hồi.
6. Kiến trúc phải đủ rõ để sau này thêm local search nâng cao hoặc local LLM mà không làm lại từ đầu.

---

## 4. TECH STACK VÀ KIẾN TRÚC

### Tech stack bắt buộc

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ chính | Python |
| Giao diện Desktop | PySide6 |
| Cơ sở dữ liệu | SQLite |
| ORM | SQLAlchemy |
| Migration | Alembic |
| Xử lý PDF | PyMuPDF |
| Trích bảng | pdfplumber |
| Ghi chú | Markdown file-based |
| Search | SQLite FTS5 hoặc index nội bộ |

### Kiến trúc phân lớp

```text
UI Layer          →  Widgets, Views, Dialogs (PySide6)
Service Layer     →  SourceService, NoteService, ExtractService, ...
Extraction Layer  →  PDF text, table, image, anchor generation
Search Layer      →  FTS index, query parser
Data Access Layer →  SQLAlchemy models, SQLite, migrations
Export Layer      →  clean text bundles, markdown exports
Config Layer      →  settings, paths, app lifecycle
```

Quy tắc bắt buộc: Business logic không được viết trực tiếp bên trong UI widget. UI layer chỉ gọi service.

---

## 5. CẤU TRÚC GIAO DIỆN

### 5.1. Ngôn ngữ giao diện

Toàn bộ giao diện phải dùng tiếng Việt.

Tên biến, hàm, class trong code dùng tiếng Anh để giữ tính nhất quán kỹ thuật.

### 5.2. Mô hình cửa sổ

Ứng dụng có một cửa sổ chính duy nhất với layout:

```text
┌──────────────────────────────────────────────────────────┐
│  Thanh tiêu đề: Quản lý Kiến thức Nghiên cứu            │
├──────────────────────────────────────────────────────────┤
│  Thanh công cụ (toolbar)                                │
├─────────────┬────────────────────────────────────────────┤
│             │                                            │
│  Điều hướng │        Vùng nội dung chính                 │
│  (sidebar)  │                                            │
│             │                                            │
├─────────────┴────────────────────────────────────────────┤
│  Thanh trạng thái (status bar)                           │
└──────────────────────────────────────────────────────────┘
```

### 5.3. Thanh điều hướng chính

Gồm 5 mục cố định:

- Trang chính
- Thư viện nguồn
- Không gian làm việc
- Research Board
- Thiết lập

### 5.4. Thanh công cụ

Context-aware, hiển thị nút phù hợp với màn hình đang mở:

| Nút | Phím tắt | Ngữ cảnh |
|---|---|---|
| Thêm nguồn | Ctrl+N | Thư viện nguồn |
| Lưu note | Ctrl+S | Khi đang làm việc note |
| Tìm kiếm | Ctrl+F | Toàn cục |
| Export clean text | Ctrl+Shift+E | Khi có dữ liệu |
| Tải lại / Re-index | F5 | Theo ngữ cảnh |
| Sao lưu | — | Toàn cục |
| Khôi phục | — | Toàn cục |

### 5.5. Màn hình khởi động

Hiển thị khi mở app:

- Danh sách source gần đây
- Số lượng tài liệu, note, extract
- Nút nhanh: Thêm PDF, mở project gần nhất, tạo note khái niệm

---

## 6. CHI TIẾT CÁC MODULE CHỨC NĂNG

### 6.1. Module Thư viện nguồn

#### Thông tin source

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| Đường dẫn file | Có | Phải duy nhất |
| Hash file | Có | Dùng chống trùng/relink |
| Tiêu đề | Không | Có thể lấy từ metadata hoặc sửa tay |
| Tác giả | Không | |
| Năm | Không | |
| DOI | Không | |
| Metadata JSON | Hệ thống | |

#### Chức năng

- Import một hoặc nhiều PDF
- Hiển thị danh sách nguồn
- Lọc theo tag, năm, tác giả, trạng thái
- Mở source trong workspace
- Relink source khi đường dẫn thay đổi
- Đánh dấu xóa mềm

---

### 6.2. Workspace Dual Pane

Giao diện làm việc chính gồm 2 panel tỷ lệ mặc định 50/50:

- Bên trái: PDF Viewer, hỗ trợ nhiều tab
- Bên phải: Markdown Editor, hỗ trợ nhiều tab

#### Quy tắc đồng bộ

- Mỗi source PDF có một source note mặc định
- Khi đổi tab PDF bên trái, source note tương ứng bên phải phải tự động hiển thị
- Nếu source chưa có note, hệ thống có thể tạo source note mặc định theo template

#### Empty states

| Tình huống | Thông báo |
|---|---|
| Chưa có source | “Chưa có tài liệu nguồn. Hãy thêm PDF để bắt đầu.” |
| Source chưa có note | “Tài liệu này chưa có ghi chú nguồn. Bạn có thể tạo note mặc định.” |
| Source file mất liên kết | “Không tìm thấy file PDF tại đường dẫn đã lưu. Hãy relink nguồn.” |

---

### 6.3. PDF Viewer

#### Chức năng bắt buộc

- Mở PDF nhiều tab
- Điều hướng trang
- Zoom in/out
- Jump đến page
- Hiển thị selection cơ bản
- Hỗ trợ crop vùng để trích bảng hoặc ảnh

#### Trạng thái cần lưu

- Trang đang mở cuối cùng của mỗi source
- Mức zoom cuối cùng của tab hiện tại
- Session tabs gần nhất nếu khả thi

---

### 6.4. Markdown Editor

#### Loại note

| Loại note | Ý nghĩa |
|---|---|
| source_note | Ghi chú gắn trực tiếp với một PDF |
| concept_note | Ghi chú khái niệm độc lập |
| synthesis_note | Ghi chú tổng hợp nhiều nguồn |
| board_note | Ghi chú liên quan board hoặc synthesis cell |

#### Chức năng

- Soạn thảo Markdown
- Autosave
- Render preview nếu khả thi
- Hỗ trợ `[[wikilink]]`
- Gắn tag cho note
- Chèn extract hoặc asset vào note

---

### 6.5. Text Extraction

#### Workflow

1. Người dùng chọn văn bản trên PDF
2. Hệ thống lấy text + page + anchor
3. Hệ thống chuẩn hóa text cơ bản
4. Hệ thống chèn block vào note hiện tại hoặc tạo extract riêng

#### Kết quả Markdown đề xuất

```markdown
> Trích dẫn từ [Nguồn, tr. X](source://123?page=5&rect=...)
>
> Nội dung trích dẫn...
```

Quy tắc:

- Không được tạo extract không có source anchor
- Nếu text raw quá bẩn, phải cho phép chỉnh tay sau khi chèn
#### Loại note và câu hỏi trung tâm

| Loại note | Câu hỏi trung tâm | Quy ước đặt tên |
|---|---|---|
| `source_note` | "Nguồn này nói gì?" | `source - {Tác giả} ({Năm})` — e.g. `source - Lent et al. (1994)` |
| `concept_note` | "Khái niệm này là gì?" | Tên khái niệm trực tiếp — e.g. `SCCT`, `TPB` |
| `synthesis_note` | "Nhiều ý ghép lại cho thấy điều gì?" | Bắt đầu bằng `~ ` — e.g. `~ so sánh SCCT và TPB` |
| `board_note` | "Bảng phân tích cho thấy bức tranh gì?" | Bắt đầu bằng `! ` — e.g. `! tổng hợp mô hình chuỗi cung ứng` |

#### Tạo note mới

- `source_note`: tự động tạo khi mở PDF trong Workspace (binding 1:1)
- `concept_note`, `synthesis_note`, `board_note`: tạo qua **`NewNoteDialog`** — chọn type, nhập title, editor hiển thị template Markdown per type
- Sau khi chọn type, nội dung editor được khởi tạo với template chuẩn tương ứng
- Trong `NewNoteDialog`, khi gõ `[[` phải có autocomplete từ note sẵn có (bao gồm note đang mở)
- Nhãn phân loại (`source -`, `concept -`, `synthesis -`, `board -`) chỉ hiển thị trong popup gợi ý, không chèn vào nội dung note
- Soft-warning nếu title quá chung chung hoặc thiếu naming convention

#### Naming convention (soft, không block cứng)

- `source_note`: `source - {Tác giả} ({Năm})` — auto-generate từ PDF metadata khi import
- `concept_note`: tên khái niệm trực tiếp, không dùng prefix
- `synthesis_note`: bắt đầu bằng `~ ` — e.g. `~ So sánh SCCT và TPB trong nghiên cứu chọn ngành`
- `board_note`: bắt đầu bằng `! ` — e.g. `! các nhân tố ảnh hưởng đến chọn ngành`
- Popup khi gõ `[[` hiển thị nhãn loại note theo format: `source -`, `concept -`, `synthesis -`, `board -`

#### Chức năng

- Soạn thảo Markdown
- Autosave
- Render preview nếu khả thi
- Hỗ trợ `[[wikilink]]`
- Gắn tag cho note
- Chèn extract hoặc asset vào note
- Soft-warning quality: thiếu outgoing links, thiếu metadata, title chung chung

1. Người dùng chọn vùng hình/biểu đồ/sơ đồ trên PDF
2. Hệ thống render vùng này thành ảnh
3. Lưu ảnh vào `assets`
4. Chèn tham chiếu relative path vào note

Ví dụ:

```markdown
![Sơ đồ chuỗi cung ứng](../assets/asset_001.png)
```

---

### 6.8. Tags, Wikilinks và Backlinks

#### Tagging

- Gắn tag cho note
- Filter notes theo tag
- Có thể mở rộng gắn tag cho extract ở giai đoạn sau

#### Wikilinks

- Hỗ trợ `[[Tên note]]`
- Resolve theo slug hoặc title ổn định

#### Backlinks

- Mỗi note có panel hoặc section hiển thị note nào đang trỏ về nó

---

## 7. QUY TẮC EXTRACTION VÀ TỔ CHỨC TRI THỨC

### 7.1. Source anchor

Format chuẩn:

```text
source://<source_id>?page=<page_no>&rect=<x0>,<y0>,<x1>,<y1>
```

Nếu không có `rect`, anchor tối thiểu vẫn phải có `source_id` và `page_no`.

### 7.2. Extract khác note

- Extract là nội dung được lấy hoặc sinh ra trực tiếp từ source và luôn có anchor
- Note là nội dung người dùng viết và có thể chứa extract, liên kết hoặc tổng hợp

### 7.3. Board cell

Research Board là lớp tổng hợp. Ô trên board có thể chứa:

- text người dùng nhập tay
- liên kết tới note
- extract kéo thả vào ô

Không xem board cell là extract gốc.

### 7.4. Search index

Search index là dữ liệu phái sinh và có thể rebuild từ DB + files. Không dùng search index làm nguồn chân lý duy nhất.

---

## 8. IMPORT, EXPORT VÀ NHẬP LIỆU

### 8.1. Import PDF

### 8.1. Import PDF

- Chọn file hoặc thư mục
- Đọc metadata cơ bản từ PDF (author, year qua PyMuPDF `doc.metadata`)
- Tính hash file
- Thêm vào thư viện nguồn
- **Auto-generate title cho source_note**: `source - {Tác giả} ({Năm})` nếu có metadata; nếu không → dùng filename (không đuôi)
- `ImportSourceDialog` hiển thị title đã generate để người dùng xác nhận hoặc chỉnh trước khi lưu
- Tạo source_note tự động với title đã xác nhận
#### Phạm vi export

- Một note riêng lẻ
- Nhiều note theo tag
- Bundle theo source
- Bundle theo project hoặc board

#### Định dạng

| Định dạng | Phạm vi |
|---|---|
| Markdown | Note riêng lẻ, bundle |
| TXT | Clean text bundle |
| JSON | Metadata + structure nếu cần |

---

## 9. SEARCH, RESEARCH BOARD VÀ TỔNG HỢP NGHIÊN CỨU

### 9.1. Search

Search phải cho phép tìm theo:

- nội dung note
- extract text
- tiêu đề note
- metadata source
- tag

Kết quả search nên phân nhóm tối thiểu theo note, extract và source.

### 9.2. Research Board

Research Board là màn hình độc lập để tổng hợp tài liệu theo ma trận.

#### Cấu trúc gợi ý

- Hàng: source hoặc study
- Cột: chủ đề như Mục tiêu, Phương pháp, Dữ liệu, Kết quả, Hạn chế

#### Chức năng v1

- Tạo/sửa/xóa hàng cột
- Nhập text vào cell
- Link note vào cell
- Kéo extract vào cell nếu khả thi

### 9.3. Clean text bundle

Mục tiêu là đóng gói tri thức đã xử lý thành văn bản sạch để nạp vào AI bên ngoài. Bundle có thể gồm:

- metadata nguồn
- note đã chọn
- extract quan trọng
- heading rõ ràng
- giữ link nguồn ở mức cần thiết

---

## 10. QUẢN LÝ DỮ LIỆU VÀ AN TOÀN

### 10.1. Single-instance lock

Chỉ cho phép 1 instance ghi vào cùng một database tại một thời điểm.

### 10.2. Autosave

- Tự lưu note theo interval cấu hình
- Interval mặc định 30 giây
- Không làm mất lịch sử undo/redo nếu sau này có

### 10.3. Backup và restore

- Backup DB và nếu cần cả notes/assets manifest
- Restore phải có xác nhận rõ
- Không silently ghi đè dữ liệu hiện tại

### 10.4. Xử lý lỗi lưu

Nếu save thất bại: hiển thị lỗi rõ, giữ nguyên trạng thái in-memory hợp lý, không discard silently.

---

## 11. THIẾT KẾ DATABASE

### 11.1. Schema versioning

Bảng `app_settings` lưu `schema_version`. Migration runner chạy khi khởi động:

1. Đọc `schema_version` hiện tại
2. So sánh với `CURRENT_SCHEMA_VERSION` trong code
3. Nếu thấp hơn, chạy migration tuần tự
4. Nếu thất bại, dừng app an toàn và báo lỗi

### 11.2. Danh sách bảng

- sources
- notes
- extracts
- assets
- tags
- board_rows
- board_columns
- board_cells
### 9.2. Research Board

Research Board là màn hình độc lập để tổng hợp tài liệu theo ma trận. Phiên bản v1.1 hỗ trợ nhiều boards độc lập, mỗi board có thể khởi tạo từ template chuẩn.

#### Cấu trúc

- Mỗi board là entity độc lập (`boards` table) với title và board_type
- Hàng: source hoặc study; Cột: theo template hoặc tùy chỉnh
- Board có thể gắn với một `board_note` để diễn giải bức tranh tổng thể

#### Khởi tạo board — nút "Khởi tạo" với 3 lựa chọn

| Lựa chọn | Mô tả |
|---|---|
| (i) Đầy đủ (34 cột) | Template meta-analysis chuẩn đầy đủ bao gồm cả cột thống kê (Effect size, SE/SD, CI, p-value) |
| (ii) Chỉ tổng hợp tài liệu (20 cột) | Subset không có cột thống kê, phù hợp cho literature review |
| (iii) Tạo Board note | Không tạo board table; tạo `board_note` với template Markdown chuẩn để diễn giải toàn cục |

#### Chức năng v1.1

- Tạo/sửa/xóa nhiều boards độc lập; `BoardSelectorPanel` để chọn board đang làm việc
- Khởi tạo từ template (3 lựa chọn trên)
- Tạo/sửa/xóa hàng và cột; nhập text, link note vào cell
- Sau khi tạo board từ (i) hoặc (ii): hỏi có muốn tạo kèm `board_note` để diễn giải không
- Nút "Mở Board note" nếu board đã gắn `board_note`
- Export board ra CSV và Markdown
| `AssetService` | Save asset, reference checks, safe delete |
| `TagService` | CRUD tag, assign/unassign |
| `LinkService` | Wikilinks, backlinks, resolve link graph |
| `BoardService` | Rows, columns, cells, linked notes |
| `SearchService` | Indexing và query |
| `ExportService` | Markdown/TXT/JSON bundles |
| `SettingsService` | app_settings CRUD |
| `BackupService` | backup/restore |
| `MigrationService` | schema versioning |

---

## 13. QUY TẮC GIAO DIỆN VÀ UX

### 13.1. Bảng và panel

- Sidebar phải rõ nguồn và note hiện tại
- Selection trên PDF phải phản hồi rõ
- Editor phải lưu được trạng thái bẩn/chưa lưu
- Search results phải mở đúng note hoặc source liên quan

### 13.2. Feedback

- Hiện xác nhận sau khi lưu thành công
- Cảnh báo non-blocking khi có vấn đề dữ liệu
- Thông báo lỗi rõ ràng khi import/extraction/export thất bại
- Thông báo tiến trình khi xử lý lớn

### 13.3. Performance

- Dùng worker thread cho extraction lớn, re-index hoặc export lớn
- Không block UI thread

---

## 14. PHÍM TẮT

| Phím tắt | Hành động |
|---|---|
| Ctrl+S | Lưu note |
| Ctrl+F | Tìm kiếm |
| Ctrl+N | Tạo mới theo ngữ cảnh |
| Ctrl+Tab | Chuyển tab |
| Ctrl+Shift+E | Export clean text |
| F5 | Re-index hoặc refresh theo ngữ cảnh |
| Ctrl+C | Sao chép |
| Ctrl+V | Dán |
| Ctrl+A | Chọn tất cả |

---

## 15. PERFORMANCE BASELINE

### Quy mô mục tiêu

| Tham số | Điển hình | Tối đa v1 |
|---|---|---|
| Số PDF trong 1 project | 20 – 50 | 100 |
| Số tab PDF mở đồng thời | 2 – 5 | 10 |
| Số note | 50 – 300 | 1000 |
| Số extract | 100 – 1000 | 5000 |

### Mục tiêu hiệu năng

- Chuyển source-note: < 200ms khi dữ liệu đã mở
- Mở PDF cỡ vừa: không đơ UI
- Chèn text extract: phản hồi gần như tức thời
- Re-index project vừa: không treo giao diện
- Export bundle: không treo giao diện

---

## 16. LỘ TRÌNH PHÁT TRIỂN

### Phase 1 — Nền tảng

- Project skeleton, cấu trúc thư mục, packaging
- Main window, navigation, status bar
- Single-instance lock
- SQLite setup, MigrationService, schema version table
- SettingsService, màn hình Thiết lập

### Phase 2 — Dữ liệu lõi

- SourceService
- NoteService
- ExtractService
- AssetService
- Schema đầy đủ v1
- Backup/restore cơ bản

### Phase 3 — Workspace chính

- Library view
- PDF viewer
- Markdown editor
- Binding 1:1 source ↔ note
- Text extraction
- Table crop + preview
- Image capture

### Phase 4 — Tổ chức tri thức

- Tags
- Wikilinks
- Backlinks
- Search
- Research Board

### Phase 5 — Hoàn thiện

- Export bundles
- Autosave
- UI polish
- Performance optimization
- Coverage, smoke tests, release docs

---

## 17. QUY TẮC VIẾT CODE

- Dùng Python type hints trong tất cả function/method
- Business logic không được nằm trong file UI
- Tổ chức theo service-oriented pattern
- Không hard-code hằng số thuộc về cấu hình
- Hàm tính anchor, normalize hoặc parse phải là pure function khi có thể
- Đặt tên rõ ràng theo convention Python
- Tránh side effect trong UI callbacks

---

## 18. TIÊU CHÍ HOÀN THÀNH TỐI THIỂU

Build được xem là đạt khi người dùng có thể:

- [ ] Import PDF vào thư viện nguồn
- [ ] Mở PDF trong workspace
- [ ] Tự động có hoặc tạo source note tương ứng
- [ ] Trích text từ PDF sang Markdown có anchor nguồn
- [ ] Crop bảng và chèn Markdown table sau bước preview
- [ ] Chụp ảnh từ PDF vào assets và chèn vào note
- [ ] Tạo note khái niệm và synthesis note
- [ ] Dùng `[[wikilink]]` giữa các note
- [ ] Tìm kiếm notes, extracts và metadata cơ bản
- [ ] Sử dụng Research Board bản đầu
- [ ] Export clean text bundle
- [ ] Đóng và mở lại app mà không mất dữ liệu
- [ ] Nâng cấp app mà không làm hỏng schema cũ

---

## 19. HƯỚNG MỞ RỘNG TƯƠNG LAI

- OCR module cho scanned PDFs

### Trong kế hoạch Phase 6 (v1.1)

- `NewNoteDialog` cho concept_note, synthesis_note, board_note với template Markdown per type
- Auto-naming source_note từ PDF metadata khi import
- Multi-board: entity `boards` độc lập, `BoardSelectorPanel`
- Board templates: Đầy đủ 34 cột, Chỉ tổng hợp 20 cột, Tạo Board note
- `board_note` ↔ board table linkage qua `boards.linked_note_id`
- `meta_json` per note type (author/year/source_type cho source, domain cho concept, v.v.)
- Note quality warnings và orphan detection
- Dashboard stats by note type

### Dài hạn (v2+)

- OCR module cho scanned PDFs
- Citation formatting templates
- Better local search với embeddings
- Local LLM connector
- Multi-project workspace
- Batch export cho systematic review
- Import CSV vào board table
- Graph view local (note đang mở ↔ neighbors)
4. Extract khác note.
5. SQLite phải có schema versioning.
