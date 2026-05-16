# PRD / Spec ngắn cho module Note + Board + Graph View

## 1. Mục tiêu

Xây dựng module quản lý tri thức cho phép người dùng:

- tạo và quản lý 4 loại note: `source`, `concept`, `synthesis`, `board`
- tạo liên kết giữa note bằng wikilink
- tạo và gắn board với bảng phân tích/meta-analysis
- hiển thị graph view để đọc mạng tri thức theo loại node và quan hệ

Module này phải phục vụ tốt cho 3 ngữ cảnh:

- ghi chú học thuật
- tổng hợp tài liệu / meta-analysis
- duyệt và điều hướng tri thức bằng graph

---

## 2. Phạm vi chức năng

### 2.1. In scope

- CRUD cho 4 loại note
- parser wikilink `[[...]]`
- tag cơ bản
- phân loại note theo `source`, `concept`, `synthesis`, `board`
- form tạo note theo type với template khác nhau
- tạo/cập nhật board từ bảng phân tích chung
- graph view toàn vault hoặc theo bộ lọc
- local graph theo note đang mở
- tìm kiếm note theo tên, loại, tag
- bộ lọc graph theo type và mật độ liên kết

### 2.2. Out of scope giai đoạn đầu

- AI auto-write note
- OCR / auto-ingest PDF phức tạp
- realtime collaboration
- versioning nâng cao kiểu Git
- semantic graph không dựa trên link người dùng tạo

---

## 3. Taxonomy chính thức

Hệ thống chỉ có đúng 4 loại note:

- `source_note`: ghi lại một nguồn cụ thể
- `concept_note`: giải thích một khái niệm cụ thể
- `synthesis_note`: tổng hợp nhiều note/ý theo một vấn đề
- `board_note`: diễn giải bức tranh tổng thể từ một bảng phân tích hệ thống

### 3.1. Câu hỏi trung tâm cho từng loại

- `source` → “Nguồn này nói gì?”
- `concept` → “Khái niệm này là gì?”
- `synthesis` → “Nhiều ý này ghép lại cho thấy điều gì?”
- `board` → “Toàn bộ bảng phân tích này cho thấy bức tranh chung nào?”

### 3.2. Rule nền

- một note chỉ có 1 `note_type`
- không hỗ trợ note đa loại
- type quyết định template khởi tạo, icon/màu trong UI, và hành vi gợi ý liên kết

---

## 4. Luồng tri thức chuẩn

Luồng chuẩn duy nhất của hệ thống:

`source_note` → `concept_note` → bảng phân tích chung → `board_note` → `synthesis_note`

Giải thích:

- `source_note` là đầu vào bằng chứng
- `concept_note` là lớp chuẩn hóa tri thức
- bảng phân tích là lớp cấu trúc hóa dữ liệu tổng hợp
- `board_note` là lớp diễn giải toàn cục từ bảng
- `synthesis_note` là lớp lập luận/tổng hợp chuyên đề rút từ nguồn, concept và board

Lưu ý triển khai:

- không bắt buộc user phải đi qua toàn bộ pipeline
- nhưng UI onboarding và help text phải dùng đúng pipeline này

---

## 5. Quy ước đặt tên

### 5.1. Naming conventions

- Source: `source {TacGia} {Nam}`
- Concept: dùng trực tiếp tên khái niệm, ví dụ `SCCT`, `TPB`, `Yếu tố cá nhân`
- Board: `board {chu_de_phan_tich}`
- Synthesis: câu hỏi hoặc kết luận ngắn, không bắt buộc prefix

### 5.2. Validation mềm

- cảnh báo nếu tên note quá chung chung như `note mới`, `ghi chú 1`
- không chặn cứng, nhưng gợi ý sửa tên

---

## 6. Schema dữ liệu tối thiểu

## 6.1. Entity: Note

```ts
Note {
  id: string
  title: string
  slug: string
  note_type: 'source' | 'concept' | 'synthesis' | 'board'
  content_md: string
  summary?: string
  tags: string[]
  aliases: string[]
  status?: 'draft' | 'active' | 'archived'
  created_at: datetime
  updated_at: datetime
  created_by?: string
}
```

## 6.2. Entity: NoteLink

Quan hệ suy ra từ parser hoặc được user tạo trực tiếp.

```ts
NoteLink {
  id: string
  source_note_id: string
  target_note_id: string
  link_type: 'wikilink' | 'manual' | 'derived'
  anchor_text?: string
  created_at: datetime
}
```

## 6.3. Entity: BoardTable

Lưu metadata của bảng phân tích gắn với `board_note`.

```ts
BoardTable {
  id: string
  board_note_id: string
  name: string
  table_type?: 'meta_analysis' | 'literature' | 'theory' | 'factor' | 'method' | 'gap' | 'other'
  scope?: string
  source_count?: number
  unit_of_analysis?: string
  column_schema_json?: json
  created_at: datetime
  updated_at: datetime
}
```

## 6.4. Entity: BoardTableRow

Nếu muốn hệ thống lưu luôn dữ liệu bảng.

```ts
BoardTableRow {
  id: string
  board_table_id: string
  row_index: number
  row_data_json: json
}
```

## 6.5. Entity: NoteMeta tùy chọn

Nếu cần metadata riêng theo loại note.

```ts
SourceMeta { note_id, author, year, source_type, publication, topic }
ConceptMeta { note_id, domain }
SynthesisMeta { note_id, central_question, theme }
BoardMeta { note_id, board_type, scope, source_count }
```

Khuyến nghị MVP:

- gộp metadata riêng vào JSON field `meta_json` trong bảng `Note`
- chỉ tách bảng riêng khi query/report phức tạp

---

## 7. Parser và logic link

### 7.1. Wikilink parser

Hỗ trợ parse dạng:

- `[[SCCT]]`
- `[[SCCT|Social Cognitive Career Theory]]`

Giai đoạn đầu chưa cần hỗ trợ embed hoặc transclusion phức tạp.

### 7.2. Nguyên tắc resolve link

- match theo `title` trước
- nếu không có, match theo `alias`
- nếu vẫn không có, cho phép tạo unresolved link
- unresolved link phải hiện rõ trong UI để user tạo note đích sau

### 7.3. Chiều liên kết

- hệ thống lưu directed edge từ note nguồn đến note đích
- UI graph có thể render không hướng nếu cần, nhưng DB nên giữ hướng để phân tích backlink

### 7.4. Backlink

- mỗi note phải có phần “Backlinks”
- backlinks được tính từ bảng `NoteLink`

---

## 8. Quy tắc liên kết giữa các loại note

Đây là rule gợi ý, không phải hard constraint tuyệt đối.

### 8.1. `source_note` nên link tới

- `concept_note`
- `board_note` khi nguồn nằm trong board nào đó

### 8.2. `concept_note` nên link tới

- `source_note`
- `concept_note` khác
- `board_note`
- `synthesis_note`

### 8.3. `board_note` nên link tới

- các `source_note` nền
- các `concept_note` quan trọng
- các `synthesis_note` được rút ra từ board

### 8.4. `synthesis_note` nên link tới

- `concept_note`
- `source_note`
- `board_note`

### 8.5. Cảnh báo graph hygiene

- hạn chế tạo `board_note` link tới quá nhiều node không chọn lọc
- ưu tiên link đến node quan trọng, tránh biến board thành “siêu hub” rối graph

---

## 9. UI/UX tạo note

## 9.1. Tạo note mới

User chọn 1 trong 4 type:

- Source
- Concept
- Synthesis
- Board

Sau khi chọn type, form đổi theo template.

## 9.2. Trường chung cho mọi note

- Title
- Note type
- Content markdown editor
- Tags
- Aliases
- Status

## 9.3. Trường riêng theo type

### Source

- Author
- Year
- Source type
- Publication
- Topic

### Concept

- Domain
- Related concepts

### Board

- Board type
- Scope
- Related table / create table
- Source count
- Unit of analysis

### Synthesis

- Central question
- Theme
- Related board

## 9.4. Template khởi tạo

Mỗi type có nút “Create from template”.
Template text lấy từ file chuẩn hóa đã biên soạn.

## 9.5. Suggest links

Trong editor, khi user gõ `[[`, hệ thống autocomplete note theo:

- title
- alias
- ưu tiên note gần đây
- ưu tiên note cùng type liên quan theo ngữ cảnh

---

## 10. UI/UX cho board và bảng phân tích

## 10.1. Board note view

Một `board_note` nên có 2 panel:

- panel note markdown diễn giải
- panel bảng phân tích nền

### 10.2. Chế độ bảng

User có thể:

- tạo cột
- thêm dòng
- sửa cell
- import CSV ở giai đoạn sau
- gắn row với note/link khi cần

### 10.3. Board summary block

Hiển thị nhanh:

- số nguồn
- số concept được nhắc
- số synthesis rút ra
- số unresolved links

---

## 11. Graph view

## 11.1. Mục tiêu graph

- giúp điều hướng tri thức
- phản ánh cấu trúc note theo type
- làm rõ cụm chủ đề và orphan note
- không cố gắng suy luận ngữ nghĩa vượt quá link do user tạo

## 11.2. Node model

Mỗi note là một node.

Node phải có thuộc tính render:

- label = title
- type = source/concept/synthesis/board
- size = hàm theo degree hoặc số backlink
- color/shape = theo type

Khuyến nghị hiển thị:

- source: một màu riêng
- concept: một màu riêng
- synthesis: một màu riêng
- board: một màu riêng, dễ nhận ra nhất

## 11.3. Edge model

Mỗi wikilink là một edge.

- directed trong data model
- tùy chọn hiển thị arrow hoặc không trong UI

## 11.4. Bộ lọc graph

- theo note type
- theo tag
- chỉ show local graph quanh note hiện tại
- theo degree threshold
- ẩn unresolved links
- chỉ hiện 1 hoặc 2 bước liên kết

## 11.5. Local graph

Khi mở 1 note, user có thể xem:

- outgoing links
- incoming links
- liên kết 2 hop nếu bật mở rộng

## 11.6. Chỉ số cơ bản cho graph

- total notes
- notes by type
- total links
- orphan notes
- top hub notes
- unresolved links

---

## 12. Rule kiểm soát chất lượng note

Hệ thống nên có warning mềm, không chặn cứng.

### 12.1. Warning gợi ý

- `source_note` không có author/year
- `concept_note` không có nguồn nền nào
- `board_note` không gắn bảng phân tích nào
- `synthesis_note` không link tới note khác
- note không có wikilink nào
- note có title quá chung chung

### 12.2. Orphan note

Hiển thị danh sách note không có incoming và outgoing links.

---

## 13. Search và navigation

- full-text search theo title + content
- filter theo type
- filter theo tag
- filter theo year/author với source
- filter theo board type
- sort theo updated_at, backlink count, title

---

## 14. API gợi ý

```http
POST   /notes
GET    /notes/:id
PATCH  /notes/:id
DELETE /notes/:id
GET    /notes?type=concept&query=scct

GET    /notes/:id/links
GET    /notes/:id/backlinks

POST   /boards/:noteId/table
PATCH  /boards/:noteId/table
GET    /boards/:noteId/table

GET    /graph
GET    /graph?scope=local&noteId=...
GET    /graph?types=concept,board
```

---

## 15. Acceptance criteria cho MVP

- user tạo được 4 loại note
- user gõ wikilink và hệ thống parse được link
- graph hiển thị được node + edge từ wikilink
- graph lọc được theo type
- mỗi note xem được backlinks
- board note gắn được với ít nhất 1 bảng phân tích
- naming conventions được gợi ý trong UI
- warning mềm hoạt động cho các thiếu sót phổ biến

---

## 16. Quyết định triển khai khuyến nghị

- dùng markdown làm nguồn nội dung chính
- parse wikilink ở server hoặc worker background nhẹ
- lưu normalized link graph trong DB riêng để query graph nhanh
- render graph bằng library force-directed
- hỗ trợ taxonomy 4 loại như first-class citizen ngay từ schema, không để type là tag tự do

---

## 17. Rủi ro nếu làm sai taxonomy

- graph biến thành tập node đồng dạng, khó đọc
- board note bị lẫn với synthesis note
- source note không còn là lớp bằng chứng rõ ràng
- link semantics mơ hồ, khó phát triển analytics sau này

---

## 18. Kết luận

Taxonomy 4 loại note là đủ gọn để dùng thực tế nhưng đủ giàu để triển khai graph view có nghĩa. Developer nên xem `note_type` là trục thiết kế trung tâm cho schema, UI và graph. Nếu khóa taxonomy ngay từ đầu, các tính năng sau như suggestion, analytics, template, local graph và board analysis sẽ mở rộng thuận lợi hơn.
