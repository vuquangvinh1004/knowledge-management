# EXTRACTION RULES

## Nguyên tắc chung

Extraction pipeline phải ưu tiên:

1. truy vết nguồn
2. preview trước khi commit nếu extraction không chắc chắn
3. output Markdown dễ đọc
4. không phá cấu trúc note hiện có

## 1. Text extraction

### Đầu vào
- source_id
- page_no
- selected_rect hoặc selected_text

### Đầu ra tối thiểu
- source_id
- page_no
- source_anchor
- content_text
- content_md

### Format Markdown khuyến nghị

```md
> [!quote] Trích dẫn
> Nội dung trích dẫn...
>
> Nguồn: [[Tên tài liệu]], tr. 12
```

Hoặc:

```md
> Nội dung trích dẫn...

Nguồn: [Tên tài liệu, tr. 12](source://123?page=12&rect=...)
```

## 2. Table extraction

### Quy tắc

1. Không commit thẳng bảng sau khi crop.
2. Luôn có preview.
3. Cho phép người dùng sửa trước khi chèn.
4. Nếu parse thất bại, fallback sang image capture hoặc raw text block.

### Output Markdown khuyến nghị

```md
| Cột A | Cột B |
|---|---|
| ... | ... |
```

## 3. Image capture

### Quy tắc

1. Asset file phải được lưu cục bộ.
2. Cần giữ page và rect nếu lấy từ PDF.
3. Khi chèn vào note, nên dùng relative path.

Ví dụ:

```md
![Sơ đồ chuỗi cung ứng](../assets/source_12/fig_03.png)
```

## 4. Source anchor format

Format khuyến nghị:

```text
source://<source_id>?page=<page_no>&rect=<x1,y1,x2,y2>
```

Nếu chưa có rect:

```text
source://<source_id>?page=<page_no>
```

## 5. Các lỗi không được chấp nhận

- Extract không có source anchor
- Bảng parse sai nhưng vẫn commit tự động
- Ảnh capture xong nhưng không lưu metadata truy vết
- Trộn note riêng của người dùng vào block extract mà không phân tách
