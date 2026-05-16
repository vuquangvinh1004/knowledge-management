# CODING STANDARDS

## Quy tắc chính

1. Python 3.11+
2. Type hints bắt buộc
3. Public API phải có docstring
4. Mỗi file một trách nhiệm chính
5. Max line length đề xuất: 100
6. Không viết business logic trong UI

## Đặt tên

- class: `PascalCase`
- function và variable: `snake_case`
- constant: `UPPER_SNAKE_CASE`

## Service contract

Service nên trả:
- object/domain model rõ ràng
- hoặc raise exception có nghĩa

Không nên trả tuple mơ hồ nếu payload phức tạp.

## Complexity guardrails

1. Mỗi thay đổi phải làm hệ thống "dễ sửa hơn" hoặc ít nhất không khó hơn.
2. Tránh change amplification: bug fix nhỏ không nên cần chạm nhiều module không liên quan.
3. Tránh temporal decomposition thuần túy (tách module theo thứ tự thời gian thay vì theo knowledge/domain).
4. Ưu tiên module sâu: interface gọn, logic đủ mạnh ở bên trong.
5. Hạn chế pass-through method/variable; nếu lớp chỉ chuyển tiếp lệnh, cân nhắc merge hoặc đổi abstraction.

## Interface and abstraction

1. Public method phải có contract rõ: input, output, failure mode.
2. Không để caller phải biết chi tiết triển khai nội bộ để dùng API đúng.
3. API mới phải ưu tiên trường hợp dùng phổ biến nhất (common case easy).
4. Giá trị config nên có default hợp lý; không đẩy gánh nặng cấu hình không cần thiết ra caller.

## Naming precision

1. Tên phải phản ánh đúng domain meaning, tránh generic name (`data`, `info`, `handler`, `process`).
2. Cùng một khái niệm phải dùng cùng một tên xuyên suốt repository.
3. Nếu khó đặt tên rõ ràng, xem đó là dấu hiệu abstraction chưa đúng và cần thiết kế lại.

## Comment policy

1. Comment tập trung vào "what/why", không lặp lại "how" hiển nhiên từ code.
2. Public API cần mô tả ngắn điều kiện biên, side effects và failure behavior.
3. Khi có quyết định cross-module, phải có tham chiếu tới Decision Log.

## Cross-module changes

1. Với thay đổi ảnh hưởng 2 module trở lên, bắt buộc ghi 2 phương án thiết kế ngắn trước khi triển khai.
2. Nếu đổi contract service/UI hoặc service/service, phải cập nhật test contract tương ứng trong cùng task.

## Exception handling

Không dùng `except Exception: pass`.

Mọi lỗi cần:
- log rõ
- rollback nếu có transaction
- báo lên UI bằng message dễ hiểu nếu là lỗi người dùng thấy

Phân mức lỗi bắt buộc:

1. Recoverable: warning log + fallback rõ ràng.
2. User-actionable: hiển thị thông báo tiếng Việt kèm hành động gợi ý.
3. Data-integrity risk: fail-fast + rollback + không tiếp tục âm thầm.

## Refactor policy

Refactor không được:
- đổi behavior nghiệp vụ ngầm
- đổi source anchor format
- đổi storage layout
- đổi schema semantics
mà không cập nhật tài liệu.
