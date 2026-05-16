# AI AGENT WORKFLOW

## Trước mỗi task

AI Agent phải trả lời ngầm các câu hỏi sau:

1. Task này thuộc phase nào?
2. Có đụng đến schema không?
3. Có đụng đến extraction contract không?
4. Có đụng đến export contract không?
5. Có cần test mới không?
6. Có cần cập nhật tài liệu nào không?

## Báo cáo sau mỗi task

Bắt buộc 5 mục:

1. Task đã thực hiện
2. Files đã thay đổi
3. Kết quả test
4. Rủi ro còn lại
5. Tài liệu đã cập nhật

## Khi nào phải cập nhật `PKM_ARCHITECTURE.md`

- đổi tech stack
- đổi schema
- đổi source anchor format
- đổi storage layout
- đổi delete policy
- đổi service boundaries

## Khi nào phải cập nhật `PKM_ROADMAP.md`

- task/phase đổi trạng thái
- thêm blocker
- fix bug lớn
- thay acceptance criteria

## Khi nào phải dừng và hỏi lại

- yêu cầu mâu thuẫn với 5 nguyên tắc khóa
- user muốn đổi bản chất sản phẩm
- task phát sinh phá vỡ cấu trúc dữ liệu đã khóa
