# TESTING STRATEGY

## Mục tiêu

Đảm bảo app bền ở 4 tầng:

1. persistence
2. extraction
3. service logic
4. UI shell cơ bản

## 1. Unit tests bắt buộc

- validators
- anchor builders/parsers
- markdown renderers
- extraction post-processors
- services lõi
- migration runner
- service contract tests (input/output/failure behavior)
- exception-path tests cho luồng có fallback

## 2. Integration tests bắt buộc

Các luồng chính:

1. import source → create source note → bind 1:1
2. open source → extract text → commit vào note
3. crop table → preview → commit markdown
4. create concept note → add wikilink → backlinks xuất hiện
5. drag extract vào board cell → board save/load đúng
6. export bundle → file tạo đúng cấu trúc
7. thay đổi một module không làm vỡ contract module kế cận (anti change-amplification)
8. error flow không bị nuốt lỗi im lặng (không có silent failure ở luồng chính)

## 3. UI smoke tests

- app shell mở được
- sidebar navigation hoạt động
- dual pane render được
- đổi tab source thì note sync đúng
- dialog extraction mở được

## 4. Coverage mục tiêu

- core services: >= 80%
- extraction utils: >= 85%
- migration and storage: >= 85%

Ngoài coverage, bắt buộc có:

- ít nhất 1 test fail-case cho mỗi service mới hoặc mỗi contract thay đổi
- ít nhất 1 regression test cho bug đã fix trong sprint hiện tại

## 5. Regression rules

Bug liên quan đến:
- source anchor
- markdown corruption
- note/source binding
- migration
- delete policy

phải có regression test bắt buộc.

Thêm bắt buộc cho giai đoạn tiếp theo:

- service contract drift (đổi tham số/semantics gây lệch test)
- pass-through refactor gây side-effect ở UI
- fallback logic làm sai dữ liệu nhưng không raise/log

## 6. Design-quality checks trong test review

1. Test phải giúp phát hiện unknown unknowns (đặc biệt ở boundary module).
2. Với module orchestration/use-case, cần test cả happy path và degraded path.
3. Mọi bug do complexity leakage phải có test tái hiện trước khi fix.
