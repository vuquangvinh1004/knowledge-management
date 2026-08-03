# START HERE FOR AI AGENT
# ỨNG DỤNG DESKTOP QUẢN LÝ KIẾN THỨC CÁ NHÂN PHỤC VỤ NGHIÊN CỨU

> QUAN TRỌNG CHO AI AGENT
>
> Đây là file khởi đầu bắt buộc cho mọi phiên làm việc mới của AI Agent trong dự án này.
>
> Trước khi viết code, sửa code, refactor, thay schema, thêm tính năng, sửa bug, thêm test hoặc cập nhật UI, AI Agent bắt buộc phải:
>
> 1. Đọc file [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
> 2. Đọc file [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md)
> 3. Đọc file này để nắm lại các nguyên tắc khóa, thứ tự ưu tiên và checklist thực thi
>
> Nếu có mâu thuẫn giữa nhiều nguồn mô tả, thứ tự ưu tiên là:
>
> 1. [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
> 2. [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md)
> 3. [`START_HERE_FOR_AI_AGENT.md`](./START_HERE_FOR_AI_AGENT.md)
> 4. [`PKM_SPEC_FINAL.md`](../spec/PKM_SPEC_FINAL.md)
> 5. Các ghi chú task mới nhất của người dùng

---

## 1. Mục tiêu dự án

Xây dựng một ứng dụng Desktop cá nhân để quản lý tri thức nghiên cứu theo mô hình local-first.

Đây là ứng dụng:

- một người dùng duy nhất
- chạy cục bộ trên Desktop
- local-first
- offline-first cho các chức năng lõi
- không có login
- không có phân quyền
- không hỗ trợ nhiều user trong v1
- không bắt buộc kết nối mạng để dùng lõi ứng dụng

Ứng dụng phải mạnh ở:

- đọc và đối chiếu PDF trong app
- trích xuất nội dung có dẫn nguồn sang Markdown
- lưu note cá nhân, liên kết hai chiều và gắn tag
- quản lý assets cục bộ
- hỗ trợ tổng hợp nghiên cứu nhiều tài liệu
- export clean text cho AI bên ngoài
- sẵn sàng tích hợp local LLM trong tương lai

Không phát triển theo hướng một note app chung chung.
Không thêm tính năng enterprise hoặc cloud-first nếu chưa có quyết định mới.

---

## 2. Tech stack bắt buộc

AI Agent không được tự ý thay đổi tech stack.

### Stack chính thức

- Python
- PySide6
- SQLite
- SQLAlchemy + Alembic
- PyMuPDF
- pdfplumber
- Markdown file-based notes
- QWebEngine hoặc editor/preview hybrid theo architecture

### Không được tự ý chuyển sang

- Electron
- Tauri
- Web app
- Mobile app
- PostgreSQL
- Stack JS làm lõi giao diện
- Cloud database làm persistence mặc định

Nếu muốn đề xuất thay đổi stack, chỉ dừng ở mức đề xuất, không tự thực hiện.

---

## 3. 5 nguyên tắc khóa không được mơ hồ

### 3.1. Local-first là nguyên tắc lõi

Source, notes, assets, database index và settings phải hoạt động cục bộ.

### 3.2. PDF là nguồn gốc

PDF gốc là tài liệu tham chiếu chính. Note không thay thế source. Mọi tổng hợp phải quay lại được source.

### 3.3. Extract phải có truy vết nguồn

Mọi extract text, table hoặc image phải giữ đủ thông tin để quay lại đúng source và đúng page. Nếu có thể, phải giữ cả rect anchor.

### 3.4. Note khác extract

- Extract = block có dẫn nguồn từ tài liệu
- Note = phần suy nghĩ, diễn giải, tổng hợp hoặc kết nối của người dùng

Không trộn 2 loại này trong cùng một model mơ hồ.

### 3.5. Schema phải có versioning

Ứng dụng phải có `schema_version`, migration runner và cơ chế nâng cấp an toàn. Không được sửa DB tùy tiện.

---

## 4. Kiến trúc bắt buộc

AI Agent phải giữ ranh giới rõ giữa các lớp:

- UI layer
- Service/Application layer
- Extraction layer
- Search/Index layer
- Persistence/Data access layer
- Export layer
- Configuration layer

### Không được làm

- không viết business logic trực tiếp trong widget UI
- không để view gọi raw SQL trực tiếp
- không nhét logic parse PDF vào code điều hướng giao diện
- không trộn note storage với asset/file IO một cách tùy tiện
- không để một file ôm quá nhiều trách nhiệm

---

## 5. Trải nghiệm người dùng bắt buộc

Ứng dụng phải ưu tiên:

- thao tác đọc và ghi chú nhanh
- chuyển đổi mượt giữa PDF và note tương ứng
- extraction ít bước bấm
- truy vết nguồn rõ ràng
- không làm mất dữ liệu thầm lặng
- không block UI khi render PDF, parse bảng hoặc export lớn

### UI language

Toàn bộ giao diện hiển thị bằng tiếng Việt.

### Keyboard shortcuts tối thiểu

- `Ctrl+S` lưu note hiện tại
- `Ctrl+F` tìm kiếm
- `Ctrl+N` tạo note mới theo ngữ cảnh
- `Ctrl+Tab` chuyển tab
- `Ctrl+Shift+E` export clean text
- `F5` làm mới preview hoặc re-index view hiện tại
- `Ctrl+C`, `Ctrl+V`, `Ctrl+A`

---

## 6. Phạm vi v1 phải giữ chặt

### Có trong v1

- import PDF
- dual-pane PDF + Markdown
- binding 1:1 giữa source note và source PDF
- text extraction với page link
- table crop và convert Markdown có preview
- image capture vào assets
- tags
- `[[wikilink]]`
- backlinks
- search cơ bản
- source metadata cơ bản
- research board bản đầu
- export clean text cho AI
- autosave
- backup/restore
- single-instance lock
- schema migration

### Không tự ý thêm vào v1

- cloud sync
- cộng tác nhiều người
- AI tự sinh nội dung trong app như tính năng bắt buộc
- vector DB nặng hoặc hạ tầng mạng phức tạp
- OCR pipeline mặc định cho mọi tài liệu
- plugin marketplace
- web clipping phức tạp

---

## 7. Cấu trúc thư mục phải đi theo kiến trúc

AI Agent phải dùng cấu trúc thư mục đã định trong [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md).

Nếu cần thêm thư mục hoặc file mới:

- phải hợp với ranh giới kiến trúc
- không tạo file rời rạc ở root nếu không cần thiết
- không đặt script tạm lâu dài trong root project

---

## 8. Trước khi bắt đầu một task mới, AI Agent phải tự kiểm tra

### 8.1. Câu hỏi bắt buộc

1. Task này thuộc phase nào trong roadmap?
2. Task này có đụng đến schema không?
3. Task này có đụng đến source anchor format không?
4. Task này có cần migration không?
5. Task này có cần test mới hoặc regression test không?
6. Task này có làm thay đổi hành vi người dùng không?
7. Task này có làm đổi tài liệu architecture hoặc roadmap không?

### 8.2. Nếu câu trả lời là có

AI Agent phải:

- cập nhật file tài liệu liên quan
- thêm test phù hợp
- báo rõ những file đã sửa
- không đánh dấu task hoàn thành khi chưa cập nhật tài liệu bắt buộc

---

## 9. Checklist bắt buộc trước khi code

- [ ] Đã đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
- [ ] Đã đọc [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md)
- [ ] Đã xác định phase hiện tại
- [ ] Đã xác định module, service, UI nào bị ảnh hưởng
- [ ] Đã xác định có cần migration hay không
- [ ] Đã xác định test cần viết hoặc cập nhật
- [ ] Đã kiểm tra task có chạm vào 5 nguyên tắc khóa không

Nếu chưa tick đủ các mục này, không được bắt đầu code.

---

## 10. Checklist bắt buộc sau khi hoàn thành một task

- [ ] Code chạy được
- [ ] Không phá hành vi cũ
- [ ] Đã viết hoặc cập nhật test liên quan
- [ ] Test đã pass
- [ ] Đã cập nhật [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md) nếu trạng thái phase/task thay đổi
- [ ] Đã cập nhật [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) nếu có đổi kiến trúc, schema, rule hoặc standard
- [ ] Đã ghi rõ file thay đổi
- [ ] Đã ghi rõ rủi ro còn lại nếu có

---

## 11. Mẫu prompt khởi động bắt buộc cho mọi phiên code mới

```text
Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md), [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md) và [`START_HERE_FOR_AI_AGENT.md`](./START_HERE_FOR_AI_AGENT.md) trước khi code.
Tuân thủ tuyệt đối tech stack, kiến trúc phân lớp, business rules, nguyên tắc local-first, source-grounded extraction, roadmap phase, acceptance criteria và checklist sau mỗi task.
Không tự ý thay đổi schema, stack, anchor format, storage layout hoặc data semantics nếu chưa cập nhật tài liệu tương ứng.
```

### 11.1. Strategic Design Checklist (bắt buộc trước khi sửa code đáng kể)

Áp dụng cho mọi task có refactor hoặc thay đổi từ 2 module trở lên.

1. Viết nhanh 2 phương án thiết kế trước khi code (không cần dài, nhưng phải khác nhau).
2. Chọn phương án làm giảm interface surface của hệ thống, không chỉ giảm số dòng code.
3. Tự kiểm tra 3 dấu hiệu complexity:
   - đổi 1 chỗ có bắt buộc sửa nhiều chỗ khác không?
   - người mới nhìn vào có đoán được luồng chính không?
   - có rule nghiệp vụ nào đang bị lặp ở nhiều lớp không?
4. Nếu câu trả lời xấu ở bất kỳ điểm nào, phải refactor thiết kế trước khi thêm tính năng.

### 11.2. Red Flags cần dừng lại để chỉnh thiết kế

1. Xuất hiện nhiều pass-through method không thêm abstraction.
2. UI bắt đầu chứa logic nghiệp vụ hoặc fallback dữ liệu.
3. Một business rule xuất hiện ở nhiều file không cùng module.
4. Thêm một tính năng nhỏ nhưng phải sửa trên 5 file không liên quan trực tiếp.
5. Dùng `except ...: pass` để "đi tiếp cho nhanh".

Nếu gặp red flag, bắt buộc chuyển sang hướng "pull complexity downward": gom logic xuống service/use-case, để UI chỉ còn orchestration nhẹ.

---

## 12. Mẫu prompt cho task tính năng mới

```text
Trước khi bắt đầu:
1. Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
2. Đọc [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md)
3. Đọc [`START_HERE_FOR_AI_AGENT.md`](./START_HERE_FOR_AI_AGENT.md)
4. Xác định phase hiện tại và acceptance criteria liên quan

Nhiệm vụ: [mô tả task]

Sau khi hoàn thành:
1. Viết hoặc cập nhật test liên quan
2. Cập nhật ROADMAP nếu trạng thái thay đổi
3. Cập nhật ARCHITECTURE nếu có thay đổi về kiến trúc, schema, anchor, business rules hoặc coding standards
4. Báo cáo file đã thay đổi, kết quả test, rủi ro còn lại
```

---

## 13. Mẫu prompt cho task fix bug

```text
Trước khi bắt đầu:
1. Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
2. Đọc [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md), nhất là bug tracker và risk tracker
3. Đọc [`START_HERE_FOR_AI_AGENT.md`](./START_HERE_FOR_AI_AGENT.md)
4. Xác định bug có liên quan đến extraction correctness, source anchor, migration hoặc data integrity hay không

Nhiệm vụ: Fix [BUG-ID hoặc mô tả bug]

Sau khi hoàn thành:
1. Thêm regression test
2. Cập nhật bug tracker trong ROADMAP
3. Cập nhật CHANGELOG trong ARCHITECTURE nếu cần
4. Báo rõ root cause, hướng sửa và kết quả test
```

---

## 14. Mẫu báo cáo tối thiểu sau mỗi task

AI Agent không được chỉ nói “đã xong”.

Phải báo tối thiểu 5 mục:

1. Task đã thực hiện
2. Files đã thay đổi
3. Kết quả test
4. Rủi ro còn lại
5. Tài liệu nào đã được cập nhật

---

## 15. Điều kiện để một task được xem là Done

Một task chỉ được xem là hoàn thành khi đồng thời thỏa:

- code chạy được
- đúng phạm vi task
- không phá hành vi cũ
- test liên quan pass
- không vi phạm các nguyên tắc khóa
- không vi phạm ranh giới kiến trúc
- tài liệu đã cập nhật nếu cần

---

## 16. Chỉ dẫn cuối cùng cho AI Agent

Hãy phát triển ứng dụng này như một công cụ nghiên cứu desktop cá nhân, bền, rõ ràng, truy vết được nguồn và an toàn dữ liệu.

Ưu tiên theo thứ tự:

1. đọc PDF ổn định
2. extraction đúng nguồn
3. note và links dùng được thật
4. dữ liệu cục bộ an toàn
5. UI tiếng Việt, dễ dùng
6. code modular, dễ bảo trì

Không thêm độ phức tạp kiểu enterprise nếu không cần.
Không tự ý làm lệch product scope sang note app chung chung.
Không bỏ qua tài liệu kiến trúc và roadmap.
