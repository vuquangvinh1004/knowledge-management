# Research-Focused PKM

Ứng dụng Desktop quản lý kiến thức cá nhân phục vụ nghiên cứu, theo mô hình local-first, source-grounded và note-centric.

## Mục tiêu

Ứng dụng này được thiết kế cho workflow nghiên cứu chuyên sâu:

- quản lý PDF nguồn
- đọc PDF nhiều tab trong app
- ghi chú bằng Markdown
- trích xuất text, bảng, hình từ PDF sang note
- gắn tag, tạo `[[wikilink]]`, xem backlinks
- tổng hợp liên tài liệu bằng Research Board
- xuất clean text bundle để dùng với AI ngoài ứng dụng

## Bộ tài liệu bắt buộc

AI Agent và người phát triển phải đọc theo thứ tự sau trước khi code:

1. [`START_HERE_FOR_AI_AGENT.md`](docs/onboarding/START_HERE_FOR_AI_AGENT.md)
2. [`PKM_ARCHITECTURE.md`](docs/architecture/PKM_ARCHITECTURE.md)
3. [`PKM_ROADMAP.md`](docs/roadmap/PKM_ROADMAP.md)
4. [`PKM_SPEC_FINAL.md`](docs/spec/PKM_SPEC_FINAL.md)

Nếu cần bản rút gọn để khởi động nhanh, đọc thêm:

- [`REQUIREMENTS.md`](docs/onboarding/REQUIREMENTS.md)
- [`PKM_README_PROJECT_STARTER.md`](docs/onboarding/PKM_README_PROJECT_STARTER.md)

## Cấu trúc tài liệu

- [`PKM_ARCHITECTURE.md`](docs/architecture/PKM_ARCHITECTURE.md): nguồn chân lý kiến trúc
- [`PKM_ROADMAP.md`](docs/roadmap/PKM_ROADMAP.md): tiến độ và phase thực hiện
- [`PKM_SPEC_FINAL.md`](docs/spec/PKM_SPEC_FINAL.md): đặc tả tổng hợp sản phẩm
- [`START_HERE_FOR_AI_AGENT.md`](docs/onboarding/START_HERE_FOR_AI_AGENT.md): file mở đầu cho mọi phiên code
- [`REQUIREMENTS.md`](docs/onboarding/REQUIREMENTS.md): bản brief ngắn cho AI Agent
- [`docs/README.md`](docs/README.md): bản đồ điều hướng toàn bộ hệ tài liệu
- [`docs/`](docs): tài liệu bổ sung về schema, extraction, export, testing, coding standards, release

## Tech stack chính thức

- Python 3.11+
- PySide6
- SQLite
- SQLAlchemy 2.x
- Alembic
- PyMuPDF
- pdfplumber
- Markdown file-based notes
- pytest / pytest-qt

## Trạng thái hiện tại

**Phase 0-7 hoàn thành.**

Phiên bản hiện tại đã có:

- hệ thống 4 loại note với template mặc định
- Project Mode (global/project scope)
- multi-board + board templates + board note integration
- metadata cho note và các luồng quản trị note nâng cao
- test coverage rộng với **375/375 tests pass**

Chi tiết tiến độ và sprint xem trong [`PKM_ROADMAP.md`](docs/roadmap/PKM_ROADMAP.md).

## Chạy ứng dụng

```powershell
.\.venv\Scripts\python.exe main.py
```

## Chạy test

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Public-ready files

Repo đã có các file nền tảng để public:

- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- [`CHANGELOG.md`](docs/release/CHANGELOG.md)
- `.github/workflows/ci.yml`

## Giay phep

Du an su dung giay phep MIT. Xem chi tiet tai `LICENSE`.

## Quy tắc cứng

- Local-first
- PDF là source gốc
- Extract phải có source anchor
- Schema phải có versioning (Alembic)
- 4 loại note rõ ràng: source_note, concept_note, synthesis_note, board_note
- Note khác extract
- Schema phải có versioning
- Không viết business logic trực tiếp trong UI

## Khởi động dự án mới với AI Agent

Dùng prompt sau:

```text
Đọc [`START_HERE_FOR_AI_AGENT.md`](docs/onboarding/START_HERE_FOR_AI_AGENT.md), [`PKM_ARCHITECTURE.md`](docs/architecture/PKM_ARCHITECTURE.md), [`PKM_ROADMAP.md`](docs/roadmap/PKM_ROADMAP.md) và [`PKM_SPEC_FINAL.md`](docs/spec/PKM_SPEC_FINAL.md) trước khi code.
Tuân thủ tuyệt đối tech stack, kiến trúc phân lớp, data semantics, extraction rules, export contracts, roadmap phase, acceptance criteria và checklist sau mỗi task.
Không tự ý thay đổi schema, stack, storage layout, note format hoặc source anchor format nếu chưa cập nhật tài liệu tương ứng.
```

Xem them huong dan dong gop tai CONTRIBUTING.md truoc khi gui pull request.
