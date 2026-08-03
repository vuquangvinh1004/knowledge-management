# Documentation Index

Trang này là bản đồ điều hướng cho toàn bộ hệ tài liệu của dự án. Nếu bạn mới vào repo, hãy đi theo thứ tự "bắt đầu nhanh" bên dưới, rồi mới mở các nhóm tài liệu chi tiết.

## Bắt đầu nhanh

1. [`START_HERE_FOR_AI_AGENT.md`](onboarding/START_HERE_FOR_AI_AGENT.md)
2. [`PKM_ARCHITECTURE.md`](architecture/PKM_ARCHITECTURE.md)
3. [`PKM_ROADMAP.md`](roadmap/PKM_ROADMAP.md)
4. [`PKM_SPEC_FINAL.md`](spec/PKM_SPEC_FINAL.md)
5. [`REQUIREMENTS.md`](onboarding/REQUIREMENTS.md)
6. [`PKM_README_PROJECT_STARTER.md`](onboarding/PKM_README_PROJECT_STARTER.md)

## Nhóm tài liệu

### Architecture

- [`PKM_ARCHITECTURE.md`](architecture/PKM_ARCHITECTURE.md): nguồn chân lý kiến trúc, business rules, schema, migration policy

### Roadmap

- [`PKM_ROADMAP.md`](roadmap/PKM_ROADMAP.md): tiến độ phase, sprint, bug tracker, risk tracker

### Spec

- [`PKM_SPEC_FINAL.md`](spec/PKM_SPEC_FINAL.md): đặc tả sản phẩm, phạm vi v1, UX và luồng người dùng

### Onboarding

- [`START_HERE_FOR_AI_AGENT.md`](onboarding/START_HERE_FOR_AI_AGENT.md): file đọc đầu tiên cho mọi phiên làm việc
- [`REQUIREMENTS.md`](onboarding/REQUIREMENTS.md): bản tóm tắt ngắn để khởi động nhanh
- [`PKM_README_PROJECT_STARTER.md`](onboarding/PKM_README_PROJECT_STARTER.md): file điều hướng bộ tài liệu khởi tạo
- [`AI_AGENT_WORKFLOW.md`](onboarding/AI_AGENT_WORKFLOW.md): quy trình làm việc và checklist sau task
- [`START_PROMPT_FOR_AGENT.txt`](onboarding/START_PROMPT_FOR_AGENT.txt): prompt mẫu ngắn

### Standards

- [`CODING_STANDARDS.md`](standards/CODING_STANDARDS.md): quy ước code và guardrails
- [`TESTING_STRATEGY.md`](standards/TESTING_STRATEGY.md): chiến lược test, coverage, regression rules
- [`PROJECT_STRUCTURE.md`](standards/PROJECT_STRUCTURE.md): cấu trúc thư mục mục tiêu

### Schema

- [`SCHEMA_NOTES.md`](schema/SCHEMA_NOTES.md): ghi chú mô hình dữ liệu lõi

### Extraction

- [`EXTRACTION_RULES.md`](extraction/EXTRACTION_RULES.md): quy tắc trích xuất, anchor, preview

### Export

- [`EXPORT_FORMATS.md`](export/EXPORT_FORMATS.md): contract export và format bundle

### Release

- [`CHANGELOG.md`](release/CHANGELOG.md): nhật ký thay đổi
- [`RELEASE_CHECKLIST.md`](release/RELEASE_CHECKLIST.md): checklist trước khi build / release

### Maintenance

- [`DECISION_LOG.md`](maintenance/DECISION_LOG.md): quyết định kỹ thuật quan trọng
- [`GITHUB_SETUP.md`](maintenance/GITHUB_SETUP.md): hướng dẫn thiết lập GitHub liên quan dự án
- [`PERFORMANCE_IMPROVEMENTS.md`](maintenance/PERFORMANCE_IMPROVEMENTS.md): ghi chú và cải tiến hiệu năng

### Reference

- [`DESIGN.md`](reference/DESIGN.md): tài liệu thiết kế tham chiếu
- [`philosophy_of_software_design.md`](reference/philosophy_of_software_design.md): tài liệu tham khảo về thiết kế phần mềm
- [`Chen_doi_tuong_trong_Markdown.md`](reference/Chen_doi_tuong_trong_Markdown.md): tài liệu tham khảo Markdown
- [`List of LaTeX environments.pdf`](reference/List of LaTeX environments.pdf): tài liệu PDF tham khảo

## Tài nguyên ngoài docs

- [`README.md`](../README.md): trang giới thiệu ở root
- [`vendor/design.md-0.1.0/README.md`](../vendor/design.md-0.1.0/README.md): bundle DESIGN.md tham chiếu bên thứ ba
- [`scripts/dev/launch_research_pkm.vbs`](../scripts/dev/launch_research_pkm.vbs): launcher Windows

## Gợi ý đọc theo mục đích

1. Muốn hiểu app thật nhanh: đọc `START_HERE_FOR_AI_AGENT.md` -> `PKM_ARCHITECTURE.md` -> `PKM_ROADMAP.md`
2. Muốn sửa UI hoặc luồng người dùng: thêm `PKM_SPEC_FINAL.md`
3. Muốn sửa dữ liệu / migration: thêm `SCHEMA_NOTES.md` và phần schema trong `PKM_ARCHITECTURE.md`
4. Muốn sửa export / extraction: đọc `EXTRACTION_RULES.md` và `EXPORT_FORMATS.md`
5. Muốn nắm quy ước code / test / structure: đọc `CODING_STANDARDS.md`, `TESTING_STRATEGY.md`, `PROJECT_STRUCTURE.md`

