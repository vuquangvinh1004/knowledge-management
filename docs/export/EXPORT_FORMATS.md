# EXPORT FORMATS

## Mục tiêu

Export phải phục vụ 3 nhóm nhu cầu:

1. đưa dữ liệu vào AI ngoài ứng dụng
2. chia sẻ bản tổng hợp nghiên cứu
3. sao lưu ở dạng dễ đọc, không phụ thuộc app

## 1. Clean text bundle

### Dùng khi
- nạp vào ChatGPT
- nạp vào NotebookLM
- dùng với local LLM

### Thành phần
- metadata dự án
- danh sách source
- note đã chọn
- extract đã chọn
- optional board summary

### Format khuyến nghị

```text
# PROJECT: [Tên dự án]

## SOURCE 1
Title:
Authors:
Year:

### Extracts
...

### Notes
...
```

## 2. Markdown bundle

Xuất thành thư mục:

- `bundle/manifest.json`
- `bundle/sources.md`
- `bundle/notes/*.md`
- `bundle/assets/*`

## 3. JSON export

Dùng cho tích hợp kỹ thuật.

Nên gồm:

- source metadata
- notes
- extracts
- tags
- links

## 4. Quy tắc export

1. Mọi export cần chọn scope rõ:
   - theo source
   - theo tag
   - theo note
   - theo board
   - theo project
2. Export text cho AI phải giữ source context tối thiểu.
3. Không export path tuyệt đối nếu có thể dùng path tương đối.
4. Nếu export có ảnh, phải có lựa chọn nhúng hoặc copy asset.
