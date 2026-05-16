# PROJECT STARTER KIT
# ỨNG DỤNG DESKTOP QUẢN LÝ KIẾN THỨC CÁ NHÂN PHỤC VỤ NGHIÊN CỨU

## 1. Mục đích của bộ tài liệu này

Bộ tài liệu này là điểm khởi động chính thức cho dự án ứng dụng Desktop quản lý kiến thức cá nhân phục vụ nghiên cứu chuyên sâu.

Bộ tài liệu được tạo ra để:

- thống nhất định hướng phát triển
- giảm việc AI Agent hiểu sai mục tiêu sản phẩm
- khóa các nguyên tắc kỹ thuật và nghiệp vụ quan trọng
- giúp mọi phiên làm việc mới bắt đầu đúng bối cảnh
- giúp theo dõi tiến độ và thay đổi có kiểm soát

File này là bản điều hướng tổng. Nó không thay thế cho các file còn lại.

---

## 2. Các file trong bộ khởi tạo

### 2.1. START_HERE_FOR_AI_AGENT.md

Đây là file AI Agent phải đọc đầu tiên trong mọi phiên làm việc mới.

Mục đích:

- nhắc lại mục tiêu dự án
- chốt tech stack
- nhấn mạnh các nguyên tắc khóa không được mơ hồ
- cung cấp checklist trước và sau khi code
- cung cấp prompt mẫu cho task mới, fix bug và refactor

### 2.2. PKM_ARCHITECTURE.md

Đây là nguồn chân lý kiến trúc của dự án.

Mục đích:

- mô tả đầy đủ kiến trúc hệ thống
- chốt ranh giới giữa UI, services, extraction, indexing, persistence
- chốt business rules chính thức
- chốt tech stack, cấu trúc thư mục, schema dữ liệu và migration policy
- chốt các nguyên tắc bắt buộc như local-first, source-grounded, note-extract separation, schema versioning

Mọi thay đổi có tính kiến trúc, nghiệp vụ lõi hoặc dữ liệu phải cập nhật vào file này.

### 2.3. PKM_ROADMAP.md

Đây là bản đồ triển khai của dự án.

Mục đích:

- chia phase phát triển
- xác định sprint ưu tiên
- ghi acceptance criteria
- ghi bug tracker và technical risk tracker
- ghi trạng thái từng hạng mục
- buộc AI Agent cập nhật tiến độ sau mỗi task

### 2.4. PKM_SPEC_FINAL.md

Đây là tài liệu đặc tả tổng hợp ở mức sản phẩm.

Mục đích:

- mô tả ứng dụng từ góc nhìn chức năng
- ghi rõ luồng người dùng chính
- chốt phạm vi v1
- chốt mô hình dữ liệu logic, giao diện và UX
- hỗ trợ AI Agent hiểu đúng mục tiêu sử dụng thực tế

### 2.5. REQUIREMENTS.md

Đây là bản tóm tắt ngắn gọn, giàu tín hiệu và dễ nạp cho AI Agent khi bắt đầu code.

Mục đích:

- làm prompt kỹ thuật gốc cho agent
- nêu bối cảnh, mục tiêu và ranh giới kỹ thuật
- chỉ rõ build order giai đoạn đầu

---

## 3. Thứ tự đọc bắt buộc cho AI Agent

### Mức tối thiểu trước khi code

1. Đọc `START_HERE_FOR_AI_AGENT.md`
2. Đọc `PKM_ARCHITECTURE.md`
3. Đọc `PKM_ROADMAP.md`

### Nếu task liên quan đến UI hoặc workflow người dùng

Ngoài 3 file trên, phải đọc thêm `PKM_SPEC_FINAL.md`.

### Nếu task liên quan đến schema hoặc dữ liệu

Phải đọc kỹ:

- phần data model trong `PKM_ARCHITECTURE.md`
- migration policy
- local file layout
- quy tắc source-note-extract
- quy tắc nullability và data integrity

### Nếu task chỉ là bắt đầu nhanh một sprint mới

Đọc thêm `REQUIREMENTS.md` để giữ đúng bối cảnh và build order.

---

## 4. Quy tắc vận hành dự án

### 4.1. File nào là nguồn chân lý

- `START_HERE_FOR_AI_AGENT.md` là file khởi động ngắn gọn
- `PKM_ARCHITECTURE.md` là nguồn chân lý về kiến trúc và nguyên tắc lõi
- `PKM_ROADMAP.md` là nguồn chân lý về tiến độ và trạng thái phát triển
- `PKM_SPEC_FINAL.md` là nguồn chân lý về mục tiêu chức năng và UX
- `REQUIREMENTS.md` là prompt ngắn để khởi động agent nhanh

Nếu có xung đột giữa README này và ARCHITECTURE, ưu tiên theo `PKM_ARCHITECTURE.md`.

Nếu có xung đột giữa trạng thái thực tế và ROADMAP, phải cập nhật `PKM_ROADMAP.md`.

### 4.2. Sau mỗi task, AI Agent phải làm gì

Sau mỗi task, AI Agent phải:

- báo rõ task đã làm
- liệt kê file đã thay đổi
- báo kết quả test
- báo rủi ro còn lại
- cập nhật `PKM_ROADMAP.md`
- cập nhật changelog trong `PKM_ARCHITECTURE.md` nếu task làm thay đổi kiến trúc, schema, rule hoặc cấu trúc dự án

### 4.3. Khi nào cần cập nhật ARCHITECTURE

Phải cập nhật `PKM_ARCHITECTURE.md` nếu có thay đổi liên quan đến:

- kiến trúc hệ thống
- extraction pipeline
- source anchor format
- database schema
- migration policy
- local storage layout
- tech stack
- coding standards
- acceptance rules cấp hệ thống

### 4.4. Khi nào cần cập nhật ROADMAP

Phải cập nhật `PKM_ROADMAP.md` nếu có thay đổi liên quan đến:

- tiến độ phase
- trạng thái task
- bug tracker
- technical risk tracker
- sprint ưu tiên
- blocker mới
- task vừa hoàn thành

---

## 5. 5 nguyên tắc khóa phải luôn nhớ

### 5.1. Local-first là nguyên tắc lõi

Dữ liệu gốc, ghi chú, assets và index phải hoạt động cục bộ. Không được biến v1 thành cloud app trá hình.

### 5.2. PDF là nguồn gốc, note là lớp tri thức cá nhân

Không được làm mờ ranh giới giữa source gốc và nội dung đã xử lý của người dùng.

### 5.3. Extract phải truy vết được nguồn

Mọi đoạn trích, ảnh, bảng hoặc block sinh ra từ PDF phải giữ được page và source anchor đủ để quay lại tài liệu gốc.

### 5.4. Note khác extract

Extract là mẩu nội dung có dẫn nguồn. Note là nội dung tư duy, tổng hợp, diễn giải hoặc liên kết của người dùng. Không trộn 2 loại dữ liệu này thành một bảng mơ hồ.

### 5.5. Schema phải có versioning và migration

Không sửa database tùy tiện. Không được tạo tình huống app mới không đọc được dữ liệu cũ.

---

## 6. Cách dùng bộ tài liệu này trong thực tế

### Trường hợp 1: bắt đầu dự án từ đầu

Đọc lần lượt:

1. `PKM_README_PROJECT_STARTER.md`
2. `START_HERE_FOR_AI_AGENT.md`
3. `PKM_ARCHITECTURE.md`
4. `PKM_ROADMAP.md`
5. `PKM_SPEC_FINAL.md`
6. `REQUIREMENTS.md`

### Trường hợp 2: mở một phiên code mới

Đọc tối thiểu:

1. `START_HERE_FOR_AI_AGENT.md`
2. `PKM_ARCHITECTURE.md`
3. `PKM_ROADMAP.md`

### Trường hợp 3: sửa bug hoặc refactor

Đọc tối thiểu:

1. `START_HERE_FOR_AI_AGENT.md`
2. phần liên quan trong `PKM_ARCHITECTURE.md`
3. bug tracker và risk tracker trong `PKM_ROADMAP.md`

---

## 7. Gợi ý prompt mở đầu cho AI Agent

```text
Hãy đọc lần lượt các file sau trước khi code:
1. START_HERE_FOR_AI_AGENT.md
2. PKM_ARCHITECTURE.md
3. PKM_ROADMAP.md
4. PKM_SPEC_FINAL.md nếu task liên quan đến UI hoặc workflow
5. REQUIREMENTS.md nếu cần bắt đầu sprint mới

Sau đó:
- tuân thủ tech stack đã chốt
- tuân thủ business rules đã khóa
- không thay đổi schema, anchor format, storage layout hoặc cấu trúc dự án nếu chưa cập nhật tài liệu
- sau mỗi task phải báo file thay đổi, kết quả test, rủi ro còn lại và cập nhật roadmap/changelog tương ứng
```

---

## 8. Danh sách file chính trong starter kit

- `PKM_README_PROJECT_STARTER.md`
- `START_HERE_FOR_AI_AGENT.md`
- `PKM_ARCHITECTURE.md`
- `PKM_ROADMAP.md`
- `PKM_SPEC_FINAL.md`
- `REQUIREMENTS.md`

---

## 9. Khuyến nghị lưu trong repo

Nên đặt 6 file này ở thư mục gốc của repo để AI Agent và người phát triển luôn nhìn thấy ngay khi mở dự án.

---

## 10. Kết luận

Hãy coi bộ tài liệu này là hợp đồng vận hành giữa người dùng và AI Agent. Mục tiêu không chỉ là viết code chạy được, mà là phát triển ứng dụng một cách nhất quán, có thể tiếp tục mở rộng và không làm lệch bản chất sản phẩm.
