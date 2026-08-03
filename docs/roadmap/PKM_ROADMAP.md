# RESEARCH-FOCUSED PKM ROADMAP

> Cập nhật: 2026-05-19 (Dual-ID public_id UUIDv7 rollout)
> Phiên bản mục tiêu: v1.0.0-alpha
> Mục tiêu: desktop app ổn định, local-first, source-grounded, đủ mạnh cho đọc PDF, trích xuất, ghi chú và tổng hợp nghiên cứu
> Cập nhật UI shell gần nhất: 2026-05-18 (tối giản GC Nguồn, chuyển GC Khái niệm/GC Tổng hợp sang single-editor + document tabs)

---

## 1. Tổng quan tiến độ

```text
Phase 0  Product Definition and Specs      ██████████  100%
Phase 1  Foundation and App Shell          ██████████  100%
Phase 2  Data Layer and Core Services      ██████████  100%
Phase 3  Dual Pane and Extraction          ██████████  100%
Phase 4  Search, Links and Board           ██████████  100%
Phase 5  Export, Data Safety and Release   ██████████  100%
Phase 6  Note System & Research Board v2   █████████░   90%
Phase 7  Project Mode                      ██████████  100%
-----------------------------------------------------------
Tổng thể v1.2                              ██████████  100%
```

---

## 2. Mục tiêu phát triển theo phase

### Phase 0. Product Definition and Specs

Mục tiêu: Chốt đặc tả sản phẩm, nguyên tắc kiến trúc, data model logic và lộ trình bắt buộc cho AI Agent.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Product scope | Done | Cao | Single-user, local desktop |
| Architecture document | Done | Cao | `docs/architecture/PKM_ARCHITECTURE.md` |
| Roadmap document | Done | Cao | `docs/roadmap/PKM_ROADMAP.md` |
| Spec final | Done | Cao | `docs/spec/PKM_SPEC_FINAL.md` |
| Starter + start files | Done | Cao | `docs/onboarding/PKM_README_PROJECT_STARTER.md`, `docs/onboarding/START_HERE_FOR_AI_AGENT.md` |
| Critical rules locked | Done | Cao | local-first, source grounded, extract != note, schema versioning |

Deliverable: Có bộ tài liệu đủ để AI Agent phát triển nhất quán, không làm lệch bản chất sản phẩm.

### Phase 1. Foundation and App Shell

Mục tiêu: Xây dựng lõi ứng dụng desktop và khung vận hành chung.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Khởi tạo cấu trúc thư mục chuẩn | Done | Cao | Đúng theo architecture |
| Thiết lập config và paths | Done | Cao | `config/paths.py`, `config/settings.py`, `config/database.py` |
| Main window skeleton | Done | Cao | Navigation sidebar, toolbar, central stacked widget, status strip |
| Logging infrastructure | Done | Trung bình | loguru + log files rotation theo ngày |
| Constants và exceptions | Done | Trung bình | `core/utils/constants.py`, `core/utils/exceptions.py` |
| Single-instance lock | Done | Cao | `core/app_kernel/app_lock.py` — PID-based, stale lock detection |
| Test framework setup | Done | Cao | pytest, pytest-qt, fixtures — 49 tests pass |

Deliverable: Ứng dụng mở được, có main window, có shell layout chuẩn, có logger, có lock file và test setup cơ bản.

**Improvement pass (2026-04-23):**

- startup_checks.py: tách hard deps (block launch) vs soft deps (warning only)
- bootstrap.py: trả về `missing_soft` để UI có thể hiển thị cảnh báo tính năng
- main.py: QMessageBox cho MỌI loại lỗi khởi động (không để lỗi im lặng trên Windows)
- ui/styles/: implement QSS light theme cơ bản (sidebar, toolbar, status bar, empty state)
- tests/unit/test_bootstrap.py: 10 tests mới — 49/49 pass

### Phase 2. Data Layer and Core Services

Mục tiêu: Hoàn thiện database, migration, models và services lõi.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| SQLite connection và session management | Done | Cao | `core/storage/connection.py`, `core/storage/session.py` |
| ORM models cho schema v1 | Done | Cao | `core/storage/models.py` — 11 tables |
| app_settings + schema_version | Done | Cao | seeded in initial migration |
| Migration runner | Done | Cao | Alembic + `core/services/migration_service.py` |
| SourceService | Done | Cao | `core/services/source_service.py` — import/update/delete/relink |
| NoteService | Done | Cao | `core/services/note_service.py` — CRUD + file I/O |
| ExtractService | Done | Cao | `core/services/extract_service.py` — commit + anchor validation |
| TagService + LinkService | Done | Trung bình | `core/services/tag_service.py`, `core/services/link_service.py` |
| BackupService | Done | Trung bình | `core/services/backup_service.py` |
| Unit tests cho migration và services lõi | Done | Cao | 130/130 tests pass (81 Phase 2 mới) |

**Completed: 2026-04-22 — 130/130 unit tests pass.**

Deliverable: Có schema ổn định, migration chạy được, CRUD lõi hoạt động và data semantics rõ ràng. ✅

### Phase 3. Dual Pane and Extraction

Mục tiêu: Hoàn thiện vùng làm việc chính với PDF viewer, markdown editor và extraction pipeline.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Dashboard view | Done | Trung bình | Dữ liệu thực từ DB, recent sources, stats |
| Library view | Done | Cao | Danh sách, lọc, import, soft-delete, context menu |
| Dual pane shell | Done | Cao | `DualPaneHost` QSplitter 50/50 |
| PDF viewer basic render | Done | Cao | `PDFViewerWidget` — PyMuPDF, zoom, navigation, rubber-band |
| Markdown editor basic | Done | Cao | `MarkdownEditorWidget` — autosave, Ctrl+S, insert extract/table/image |
| Binding 1:1 source ↔ source note | Done | Cao | Auto-create source_note khi mở source |
| Text extraction to markdown | Done | Cao | Rubber-band selection → extract text → quote block + anchor |
| Table crop + preview + markdown | Done | Cao | pdfplumber pipeline → `TablePreviewDialog` → confirm → insert |
| Image capture to assets | Done | Trung bình | Rubber-band → PNG → `AssetService` → insert ref |
| Integration tests | Done | Cao | 8 tests trong `tests/integration/test_phase3_workflow.py` |

**Completed: 2026-04-23 — 156/156 tests pass (26 mới: 18 unit + 8 integration).**

Deliverable: Người dùng có thể mở source, xem PDF, ghi chú và trích xuất nội dung có truy vết nguồn. ✅

### Phase 4. Search, Links and Board

Mục tiêu: Hoàn thiện liên kết tri thức, tìm kiếm và tổng hợp liên tài liệu.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| `[[wikilink]]` parse và resolve | Done | Cao | Auto-scan sau save, tạo Link record qua LinkService |
| Backlinks view | Done | Trung bình | Đếm backlinks hiển thị trong header MarkdownEditor |
| Tagging UI | Done | Trung bình | `NoteTagsDialog` — add/remove tags từ editor |
| Search service + FTS index | Done | Cao | SQLite FTS5, `SearchService`, `fts_index.py`, `query_parser.py` |
| Search panel UI | Done | Cao | `SearchPanelDialog` — debounce 300ms, filter note/extract |
| Research Board basic | Done | Trung bình | `BoardView` với QTableWidget, add/rename/delete row/col |
| Edit board cell | Done | Trung bình | Double-click cell → `_CellEditDialog` → lưu content_md |
| Export board snapshot | Done | Thấp | Markdown + CSV qua `ExportService` |
| Export source bundle | Done | Cao | Note + extracts của source → Markdown file |
| Tests cho search/links/board | Done | Cao | 44 tests: 18 unit search + 14 unit board + 12 integration |

**Completed: 2026-04-23 — 200/200 tests pass (44 mới: 10 file, 3 service mới, 3 widget mới).**

Deliverable: Người dùng có thể kết nối note, tìm lại tri thức và tạo lớp tổng hợp nghiên cứu liên tài liệu. ✅

### Phase 5. Export, Data Safety and Release Prep

Mục tiêu: Hoàn thiện luồng export cho AI và tăng độ bền hệ thống.

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Export clean text bundle | Done | Cao | ExportService.export_source_bundle() |
| Export notes + references pack | Done | Trung bình | export_source_bundle() với extracts |
| Autosave | Done | Cao | MarkdownEditor 2s debounce autosave |
| Backup/restore | Done | Cao | BackupService + UI button trong SettingsView |
| Delete confirmations | Done | Cao | QMessageBox.question trước soft_delete |
| UI smoke tests | Done | Cao | 25 smoke tests, 233 pass total |
| Coverage >= 80% | Done | Cao | core/ = 83%, overall = 78% |
| PyInstaller config | Done | Trung bình | research_pkm.spec (Windows onedir) |
| User documentation | Deprioritized | Trung bình | optional cho v1-alpha |
| Release checklist | Deprioritized | Trung bình | optional cho v1-alpha |

Deliverable: Ứng dụng đủ ổn định để đóng gói và dùng thật cho workflow nghiên cứu cơ bản.

### Phase 6. Note System & Research Board v2

Mục tiêu: Chuẩn hóa hệ thống 4 loại note, thêm multi-board với template, tích hợp board_note ↔ board table.

#### Sprint A — Note Creation & Auto-naming (ít rủi ro, không migration)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| `NewNoteDialog` cho concept_note, synthesis_note, board_note | Done | Cao | Thêm dialog mới với chọn type + chỉnh template markdown |
| Template Markdown per note_type | Done | Cao | `NoteService.build_template()` cho 4 loại note |
| Auto-naming source_note từ PDF metadata | Done | Cao | `SourceService.build_source_note_title()` + `ImportSourceDialog` confirm title |
| Soft-warning note quality trong editor | Done | Trung bình | Cảnh báo title/naming + thiếu metadata author/year + thiếu wikilink |
| Tests cho NewNoteDialog và auto-naming | Done | Cao | Bổ sung unit test + UI smoke (82 passed, 1 test cũ deselected) |

Acceptance criteria Sprint A:

- Người dùng tạo được concept_note/synthesis_note/board_note từ dialog mới
- source_note title tự động generate đúng format `source {Tác giả} {Năm}` khi có metadata
- Template Markdown hiển thị đúng per type
- Soft-warning hiển thị khi note thiếu metadata hoặc title quá chung chung

**Completed: 2026-04-24 — Sprint A done.**

#### Sprint B — Multi-board Schema & Migration (schema breaking change)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Alembic migration: thêm bảng `boards` | Done | Cao | Tạo revision `0004_add_boards_scope` |
| Alembic migration: thêm `board_id` vào `board_rows` + `board_columns` | Done | Cao | Backfill vào default board, FK + index |
| Refactor `BoardService` scope theo `board_id` | Done | Cao | CRUD rows/cols/cells và export đều support `board_id` |
| `BoardSelectorPanel` — tạo/chọn/xóa board | Done | Cao | Tích hợp vào BoardView: chọn/chuyển/đổi tên/xóa board theo UI |
| Board CRUD: create/rename/delete board entity | Done | Cao | `create_board()`, `rename_board()`, `delete_board()` |
| Tests cho migration và multi-board service | Done | Cao | Cập nhật `test_migration.py` + `test_board_service.py` |

Acceptance criteria Sprint B:

- Migration chạy sạch trên DB cũ (data hiện có không mất)
- BoardService hoạt động đúng với board_id scope
- Người dùng tạo, chuyển giữa nhiều boards trong BoardView

**Completed: 2026-04-24 — Sprint B done (schema + service + BoardSelectorPanel UI).**

#### Sprint C — Board Templates & Board Note Integration

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| `BoardService.create_from_template(template_name, title)` | Done | Cao | Hỗ trợ `meta_analysis` (34), `literature` (20), `board_note` |
| Template selector UI — nút "Khởi tạo" với dropdown 3 lựa chọn | Done | Cao | Đã tích hợp trong BoardView với 3 lựa chọn (i)(ii)(iii) |
| Gắn board_note ↔ board table (`boards.linked_note_id`) | Done | Cao | Hỏi tạo board_note sau (i)/(ii); có nút "Mở Board note" |
| Column resize và freeze cho board lớn (34 cột) | In Progress | Trung bình | Đã thêm resize interactive + default width + scroll ngang ổn định |
| Export board với template đúng header | Done | Trung bình | Export CSV/Markdown theo cột template của board đang chọn |
| Tests cho board templates và board_note integration | Done | Cao | Bổ sung unit tests cho template + linkage, UI smoke cho BoardView |

Acceptance criteria Sprint C:

- Người dùng khởi tạo board từ 3 template đúng số cột
- board_note được tạo và gắn với board khi chọn
- Nút "Mở Board note" navigate đúng vào editor

**Completed (functional): 2026-04-24 — Sprint C tính năng chính đã triển khai.**

#### Sprint D — Note Metadata (meta_json) & Quality

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Alembic migration: thêm `meta_json` vào bảng `notes` | Done | Cao | Revision `0005_add_note_meta_json` |
| `NoteService.update_meta()` + schema per type | Done | Cao | Validate JSON theo note_type + sanitize payload |
| Metadata form trong editor: author/year cho source_note | Done | Trung bình | Nút `Metadata` trong editor, dialog theo note_type |
| Metadata form cho concept_note (domain) và board_note (board_type, scope) | Done | Thấp | Có form theo type (domain/keywords, board_type/scope/source_count) |
| Orphan note detection trong SearchService | Done | Trung bình | `list_orphan_note_ids()` dựa trên incoming/outgoing links |
| Dashboard: thống kê notes by type, orphan count | Done | Thấp | DashboardView hiển thị thêm counts theo note_type + orphan |
| Tests cho meta_json migration và NoteService update | Done | Cao | Bổ sung test migration + note metadata + orphan search |
| Bảo trì an toàn: dọn note không còn dùng có preview giữ/xóa trước apply | Done | Cao | Settings thêm nút preview cleanup + service API list/apply cleanup theo lựa chọn |

Acceptance criteria Sprint D:

- Migration chạy sạch, meta_json là NULL cho notes hiện có
- source_note lưu được author/year vào meta_json
- Dashboard hiện đúng stats by type

Deliverable Phase 6: Hệ thống 4 loại note có template chuẩn, multi-board với 3 template sẵn sàng (bao gồm 34-cột meta-analysis chuẩn), board_note tích hợp với board table, auto-naming từ PDF metadata.

**Completed (scope hiện tại): 2026-04-24 — Sprint D done, còn hạng mục tối ưu cột freeze của Sprint C.**

### Phase 7. Project Mode

Mục tiêu: Bổ sung chế độ Project — cho phép người dùng nhóm note theo dự án nghiên cứu, tách biệt với Global notes, hỗ trợ đóng gói và kết thúc project.

**Quyết định thiết kế (2026-05-04):**

- `notes.project_id IS NULL` = Global note (mặc định)
- `notes.project_id IS NOT NULL` = Project-only note (chỉ thuộc 1 project)
- `project_note_refs` = Global notes được kéo vào project để tham khảo
- Source PDF luôn là Global — không có project scope
- Xóa project = soft-delete (`is_deleted = 1`), note project-only SET NULL → trở thành Global
- Đóng gói project = export folder Markdown standalone (không còn tham chiếu DB)
- Search trong Project mode = chỉ trong notes thuộc project (own + refs)

#### Sprint 7A — Schema & Migration & ProjectService

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Alembic migration 0007: bảng `projects` | Done | Cao | `is_deleted`, `status`, `closed_at`, `meta_json` |
| Alembic migration 0007: bảng `project_note_refs` | Done | Cao | UNIQUE(project_id, note_id) |
| Alembic migration 0007: cột `notes.project_id` FK | Done | Cao | nullable, ON DELETE SET NULL |
| Cập nhật ORM models | Done | Cao | `Project`, `ProjectNoteRef`, relationship trong `Note` |
| `ProjectService` | Done | Cao | CRUD, activate, add/remove ref, get_project_notes, export_bundle |
| Unit tests ProjectService | Done | Cao | `tests/unit/test_project_service.py` |

Acceptance criteria Sprint 7A:

- Migration chạy sạch trên DB cũ (data không mất)
- `Project`, `ProjectNoteRef` ORM model hoạt động đúng
- `ProjectService` CRUD + scope rules đúng
- Unit tests pass

**Completed: 2026-05-04 — Sprint 7A done. 332/332 tests pass (+35 mới).**

#### Sprint 7B — WorkspaceOrchestrator & NoteService Extension

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| `NoteService.create_note()` thêm `project_id` param | Done | Cao | |
| `NoteService.list_by_project()` + `list_global()` | Done | Cao | Trả own notes và Global notes riêng |
| `WorkspaceOrchestrator.active_project_id` | Done | Cao | Persist vào `AppSettingRow` qua `ProjectService` |
| `WorkspaceOrchestrator.create_note_in_scope()` | Done | Cao | Tạo note với scope Global hoặc Project |
| `SearchService` thêm `project_note_ids` filter | Done | Cao | `project_note_ids: set[int] \| None` |
| Unit tests NoteService + SearchService + Orchestrator | Done | Cao | 19 tests mới, 351 total |

**Completed: 2026-05-04 — Sprint 7B done. 351/351 tests pass (+19 mới).**

#### Sprint 7C — UI: Sidebar, Project Dialog, Note Create

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Sidebar section "Dự án" | Done | Cao | Danh sách projects, activate/deactivate, mở quản lý |
| `ProjectManagerDialog` | Done | Cao | Tạo/đổi tên/kết thúc/xóa mềm project, thêm/xóa note refs |
| Mode indicator ở toolbar | Done | Trung bình | Hiển thị `Mode: Global` hoặc `Mode: Project - {name}` |
| `NoteCreateDialog` thêm lựa chọn scope | Done | Cao | `NewNoteDialog` có chọn lưu Global/Project |
| Project filter trong Library/Workspace view | Done | Cao | Chỉ mở/hiển thị sources liên quan notes của project |
| UI smoke tests | Done | Cao | Thêm smoke test cho indicator/project dialog/new-note scope |

**Completed: 2026-05-04 — Sprint 7C done. 354/354 tests pass (+3 mới).**

#### Sprint 7D — Export Bundle & Close Project

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| `ProjectService.export_project_bundle()` | Done | Cao | Delegate qua `ExportService.export_project_bundle()` |
| `ExportService` tích hợp bundle project | Done | Trung bình | Thêm method export project bundle standalone |
| "Đóng gói project" UI action | Done | Cao | `ProjectManagerDialog` có nút `Đóng gói` + chọn thư mục output |
| "Kết thúc project" UI action | Done | Trung bình | Đã có từ Sprint 7C trong `ProjectManagerDialog` |
| Integration tests bundle + close | Done | Cao | Thêm `tests/integration/test_phase7_project_mode.py` |

**Completed: 2026-05-04 — Sprint 7D done. 360/360 tests pass (+6 tests mới: 5 integration + 1 UI smoke).**

#### 2026-05-07 — Post-Phase7 Hardening (không đổi schema)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Tự phục hồi source_note khi file markdown bị mất lúc mở source | Done | Cao | `WorkspaceOrchestrator.ensure_source_note()` + thông báo UI rõ ràng |
| Đảm bảo mỗi PDF có source_note ngay lúc import thư viện | Done | Cao | `ImportSourceDialog` gọi orchestrator thay vì tự tạo rời rạc |
| Bảo trì read-only: audit source_note thiếu file | Done | Trung bình | Nút mới trong `SettingsView` (chỉ xem, không ghi DB) |
| Tab mới “Quản lý ghi chú” | Done | Cao | Hiển thị all notes kèm nhãn Global/Project; tạo/chỉnh sửa/xóa có cảnh báo ảnh hưởng |
| Quản lý ghi chú nâng cao | Done | Cao | Thêm filter nâng cao, preview trước chỉnh sửa, và tùy chọn xóa cứng (cảnh báo 2 lớp) |
| Chuẩn hóa nhãn sidebar | Done | Thấp | `Research Board` -> `Bảng nghiên cứu`, `Dự án` -> `Project` |
| Test hồi quy | Done | Cao | Thêm unit + UI smoke cho auto-recovery, audit và note management |

Deliverable: tăng độ bền dữ liệu note và hoàn thiện quản trị note ở cấp UI mà không đổi migration/schema.

#### 2026-05-12 — Public-readiness Cleanup (không đổi schema)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Giảm nuốt lỗi im lặng ở startup/UI | Done | Cao | Thêm logging có ngữ cảnh ở `main.py` và `ui/main_window.py` |
| Bổ sung bộ governance docs để public repo | Done | Cao | Thêm LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG |
| Chốt license public | Done | Cao | Dùng MIT, ghi rõ tại README + CONTRIBUTING |
| Chuẩn hóa quality tooling config | Done | Trung bình | Thêm `pyproject.toml` cho ruff/mypy |
| CI test tự động | Done | Cao | Thêm workflow `.github/workflows/ci.yml` chạy pytest trên Windows |
| Giảm độ lớn NoteService | Done | Trung bình | Tách template/title warning sang `core/services/note_templates.py` |
| Giảm độ phình MainWindow (đợt 2) | Done | Cao | Tách orchestration sang `ui/handlers/main_window_handlers.py` |
| Dọn root workspace | Done | Trung bình | Chuyển 4 file markdown nháp nâng cấp vào `archive/root_legacy_notes/` |
| Fix icon runtime và bản đóng gói | Done | Cao | Khôi phục icon về `assets/icons/`, cập nhật `main.py` + `research_pkm.spec` |

Deliverable: repo sẵn sàng public với bộ tài liệu quản trị chuẩn, CI cơ bản và hành vi logging minh bạch hơn khi có lỗi runtime.

#### 2026-05-19 — Board Meta-analysis hardening (schema + UI workflow)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Migration 0009: thêm `board_rows.source_note_id` + unique constraint | Done | Cao | Enforce dần quy tắc 1 hàng = 1 source_note |
| BoardService: luôn đảm bảo full 34 cột meta-analysis | Done | Cao | `ensure_full_meta_columns()` idempotent, giữ dữ liệu legacy |
| BoardService: đồng bộ hàng theo source_note | Done | Cao | `sync_rows_with_source_notes()` + lọc theo project scope |
| BoardView: bỏ nút/menu `Khởi tạo` | Done | Cao | Chuyển workflow sang bảng chuẩn hóa |
| BoardView: thêm hành động `Đồng bộ nguồn` | Done | Cao | Mục tiêu 1 hàng = 1 source_note |
| Note Management: thêm thẻ `GC Board` | Done | Cao | Tạo/quản lý `board_note` cùng nhóm tab note |

Deliverable: tab Bảng nghiên cứu chuyển sang vai trò ma trận phân tích nguồn chuẩn 34 cột, còn `board_note` được quản lý ở lớp note theo tab riêng.

#### 2026-05-19 — Follow-up fixes (GC Note Delete + Board UI Simplification)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Fix lỗi xóa cứng note còn liên kết (`links`) | Done | Cao | `NoteService.hard_delete()` dọn liên kết trước khi delete note |
| Phân biệt note đã soft-delete trong tab GC | Done | Trung bình | Tab note đổi màu + tooltip trạng thái khi bật `Bao gồm đã xóa` |
| Bỏ khung selector phía trên tab Bảng nghiên cứu | Done | Trung bình | BoardView tối giản, tập trung hiển thị bảng tổng hợp |

Deliverable: cải thiện tính ổn định thao tác xóa cứng và trải nghiệm nhận diện trạng thái note/board rõ ràng hơn.

#### 2026-05-20 — Display Refinements & Criteria Management (Board UX improvements)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Mở rộng hiển thị ô bảng (word wrap) | Done | Cao | Tăng width mặc định từ 220→280px, bỏ truncate 80 ký, enable resizeRowsToContents |
| Fix quote/blockquote background khi tràn dòng | Done | Cao | Thêm background color (#EFF4F9) cho blockquote line format trong markdown editor |
| Thêm button "Tùy chỉnh" tiêu chí bảng | Done | Cao | New dialog `BoardCriteriaManagerDialog` với CRUD + drag-reorder; tích hợp toolbar BoardView |
| Xác thực CRUD tiêu chí + cascade delete | Done | Cao | create_column + delete_column với cascade xóa ô; list_columns giữ thứ tự |
| Migration 0010: thêm `board_columns.is_visible` | Done | Cao | Lưu trạng thái checkbox ẩn/hiện tiêu chí, không bị reset sau restart |
| Checkbox hiển thị tiêu chí trong dialog Tùy chỉnh | Done | Cao | Tích chọn = hiển thị trên bảng; bỏ chọn = ẩn khỏi bảng |
| BoardView chỉ hiển thị cột đang bật | Done | Cao | Dùng `list_columns(visible_only=True)` thay vì luôn render toàn bộ cột |
| Bảo toàn dữ liệu tiêu chí hệ thống khi "xóa" | Done | Cao | Tiêu chí hệ thống không xóa cứng; được chuyển sang hidden để tránh mất dữ liệu |
| Loại bỏ triệt để tiêu chí không bắt buộc | Done | Cao | Xóa khỏi bộ tiêu chí hệ thống: `ID`, `Mã nghiên cứu`, `Hướng tác động`, `Effect size`, `Loại effect size`, `SE/SD`, `CI thấp`, `CI cao`, `p-value`, `Chất lượng nghiên cứu`, `Ghi chú mã hóa`, và 3 link-note |
| Fix persist thứ tự tiêu chí sau restart | Done | Cao | Sửa `ensure_full_meta_columns()` để không ghi đè `sort_order` cột đã tồn tại; bảo toàn thứ tự người dùng đã lưu |
| Trang chính: thêm bảng Danh sách ghi chú | Done | Cao | Hiển thị STT, tên, loại, chế độ (Global/Project), trạng thái note theo màu |
| Sort và filter theo header cho bảng ghi chú | Done | Cao | Click header để sort; chuột phải header để lọc theo cột và xóa bộ lọc |
| Đổi tên note bằng chuột phải trên tab ghi chú | Done | Cao | Menu `Sửa tên` trên tab note (tương tự worksheet); cập nhật title và đồng bộ toàn app ngay |
| Bảng ghi chú: thay ID bằng STT | Done | Cao | Cột đầu là STT (thứ tự hiển thị), khóa sort/filter cho STT; các cột còn lại vẫn sort/filter |
| Source note: bỏ tiền tố `source -` khi sinh title mới | Done | Cao | Cập nhật `build_source_note_title()` để trả về `{Tác giả} ({Năm})`; dashboard tự bỏ prefix legacy khi hiển thị |
| Trạng thái note 3 mức trên dashboard | Done | Cao | Đang sử dụng (xanh), Xóa tạm (xám), Đã xóa (đỏ) dựa trên `notes.is_deleted` = 0/1/2 |
| Context menu theo trạng thái note trên dashboard | Done | Cao | Xóa tạm: `Khôi phục`/`Xóa cứng`; Đã xóa: `Xóa hoàn toàn` (có cảnh báo) |
| Đồng bộ quotes Metadata trong source_note template | Done | Cao | Template `## Metadata` chỉ còn quotes của tiêu chí hệ thống bắt buộc |
| Test hồi quy UI + unit | Done | Cao | 428 tests pass; thêm unit tests cho restore/hard-mark delete và smoke tests cho dashboard actions |

Deliverable: bảng tổng hợp hiển thị đầy đủ nội dung, quote blocks có background nhất quán khi tràn dòng, người dùng quản lý tiêu chí linh hoạt hơn.

#### 2026-05-19 — Dual-ID rollout (public_id UUIDv7)

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Reset sạch dữ liệu runtime cho sandbox | Done | Cao | Xóa toàn bộ `data/*` runtime (giữ `.gitkeep`) để chuẩn bị thay đổi cơ chế ID |
| Thêm utility sinh `public_id` | Done | Cao | `core/utils/public_id.py` dùng UUIDv7 (fallback UUID4) |
| ORM bổ sung cột `public_id` | Done | Cao | Áp dụng cho `projects`, `sources`, `notes`, `extracts`, `assets`, `tags`, `links`, `boards`, `board_rows`, `board_columns`, `board_cells` |
| Migration 0011 thêm + backfill + unique | Done | Cao | Revision `0011_add_public_id_uuidv7` thêm `public_id`, backfill toàn bộ record hiện có, khóa `NOT NULL` + `UNIQUE` |
| Regression tests cho schema/runtime | Done | Cao | Cập nhật `test_migration.py`, `test_note_service.py`, `test_source_service.py` xác nhận `public_id` hoạt động |

Deliverable: hệ thống dùng mô hình Dual-ID ổn định: ID số nguyên giữ cho FK nội bộ, `public_id` UUIDv7 dùng cho định danh công khai/mở rộng liên thông.

#### 2026-05-19 — Source-note creation workflow hardening

| Hạng mục | Trạng thái | Ưu tiên | Ghi chú |
| --- | --- | --- | --- |
| Import thư viện chỉ lưu source thô | Done | Cao | `ImportSourceDialog` bỏ hoàn toàn trường/logic tạo `source_note` khi import |
| Source code chỉ sinh khi tạo source_note | Done | Cao | `SourceService.import_source()` không gán `source_code`; `NoteService.create_note(source_note)` gọi `ensure_source_code()` |
| GC Nguồn: CTA đổi thành `Tạo note mới` | Done | Cao | Empty state của `WorkspaceView` chuyển từ `Vào Thư viện` sang luồng tạo source_note có chủ đích |
| Tạo source_note qua Library có confirm | Done | Cao | Chế độ chọn tài liệu trong `LibraryView` + xác nhận Có/Không trước khi tạo |
| Chặn tạo trùng source_note | Done | Cao | Nếu source đã có source_note thì báo và không cho tạo mới |
| Library detail panel tối giản action | Done | Trung bình | Chỉ giữ `Mở tài liệu` + `Chỉnh sửa thông tin`, bỏ nút `Ghi chú nguồn` |
| Dashboard header filter badge | Done | Trung bình | Cột đang lọc hiển thị badge `[F]` ngay trên header |

Deliverable: tách rõ workflow `import source` và `create source_note`, giảm tạo dữ liệu ngoài ý muốn và tăng khả năng nhận diện trạng thái lọc ở Trang chính.

---

## 3. Sprint ưu tiên đề xuất

### Sprint 1

Mục tiêu: Đặt nền tảng shell app.

1. Cấu trúc thư mục
2. Settings, paths, logger
3. Main window skeleton
4. Single-instance lock
5. Test setup

### Sprint 2

Mục tiêu: Hoàn thiện data layer.

1. SQLite setup
2. SQLAlchemy models
3. app_settings và schema_version
4. Migration runner
5. SourceService và NoteService

### Sprint 3

Mục tiêu: Hoàn thiện dual pane cơ bản.

1. Library view
2. PDF viewer cơ bản
3. Markdown editor cơ bản
4. Binding source-note 1:1
5. Empty states cơ bản

### Sprint 4

Mục tiêu: Hoàn thiện extraction.

1. Text extraction
2. Anchor generation
3. Table crop + preview
4. Image capture
5. Integration tests

### Sprint 5

Mục tiêu: Hoàn thiện knowledge layer.

1. Wikilinks
2. Backlinks
3. Tagging
4. Search
5. Research Board

### Sprint 6

Mục tiêu: Củng cố độ bền và chuẩn bị release.

1. Export bundles
2. Autosave
3. Backup/restore
4. Coverage và UI smoke tests
5. Packaging và quickstart docs

---

## 4. Tiêu chí chấp nhận cho từng nhóm tính năng

### 4.1. App Shell

Một task shell chỉ được chấp nhận nếu:

1. App mở được ổn định
2. Main window có navigation, toolbar, central host và status strip
3. Chuyển view không gây crash
4. Single-instance lock hoạt động
5. Có test smoke cơ bản

### 4.2. Data Layer

Một task data layer chỉ được chấp nhận nếu:

1. DB schema khớp architecture
2. Migration chạy đúng trên DB mới và DB nâng cấp
3. Không mất dữ liệu khi update schema
4. Có test ít nhất một case đúng và một case lỗi

### 4.3. Extraction

Một task extraction chỉ được chấp nhận nếu:

1. Source anchor được sinh đúng format
2. Extract giữ đủ source/page context
3. Preview hoạt động nếu task liên quan table/image crop
4. Có unit tests cho normalizer hoặc parser liên quan

### 4.4. Dual Pane

Một task dual pane chỉ được chấp nhận nếu:

1. PDF và note mở được song song
2. Binding 1:1 source ↔ source note hoạt động
3. Chuyển source không làm mất note chưa lưu
4. Có empty state và warning hợp lý
5. Không chứa extraction logic nặng trong UI class

### 4.5. Search / Links / Board

Một task knowledge layer chỉ được chấp nhận nếu:

1. Link hoặc search index không làm hỏng note gốc
2. Query trả kết quả đúng với dữ liệu hiện có
3. Rebuild index không làm mất dữ liệu nguồn
4. Có tests tương ứng cho case đúng và case lỗi

### 4.6. Data Safety

Một task data safety chỉ được chấp nhận nếu:

1. Không silently discard user changes
2. Save lỗi có thông báo rõ
3. Delete có confirmation đúng policy
4. Backup/restore được kiểm tra thực tế

## 5. Bug tracker khởi tạo

| ID | Mô tả | Mức độ | Trạng thái |
| --- | --- | --- | --- |
| BUG-01 | Chưa chốt editor strategy giữa QTextEdit thuần và QWebEngine hybrid | Medium | Open |
| BUG-02 | Rủi ro source anchor không ổn định khi thay đổi file path hoặc re-import | High | Open |
| BUG-03 | Table extraction từ PDF bố cục phức tạp có thể sai cột hoặc mất dòng | High | Open |
| BUG-04 | Search index có thể stale sau khi note đổi tên hoặc đổi slug | Medium | Open |
| BUG-05 | Rủi ro hiệu năng khi mở PDF lớn nhiều tab liên tiếp | Medium | Open |
| BUG-06 | Markdown editor hiển thị tối (kế thừa theme hệ thống) | High | Fixed (2026-04-23) — QSS explicit color rules thêm cho QPlainTextEdit/QTextEdit |
| BUG-07 | Sidebar thư viện không hiển thị thông tin tài liệu | High | Fixed (2026-04-23) — SourceDetailPanel viết lại với QStackedWidget + Zotero fields |
| BUG-08 | _on_page_changed trong DualPaneHost gọi sai method | Medium | Fixed (2026-04-23) — đổi sang update_last_opened_page() |
| BUG-09 | Sidebar Thư viện nguồn bị nền tối/chữ khó đọc trên một số môi trường theme | High | Fixed (2026-04-23) — khóa style panel sáng + tăng tương phản text/button |
| BUG-10 | Không có điều hướng trang PDF bằng phím mũi tên trái/phải trong Workspace | Medium | Fixed (2026-04-23) — thêm shortcuts Left/Right trong PDFViewerWidget |
| BUG-11 | Chưa có hashtag autocomplete kiểu Obsidian trong Markdown editor | Medium | Fixed (2026-04-23) — autocomplete khi gõ #, Enter để hoàn thành, tô màu hashtag xanh |
| BUG-12 | Thiếu phản hồi trực quan cho `[[wikilink]]` và resolve slug chưa ổn định với tiếng Việt | High | Fixed (2026-04-23) — tô màu wikilink + resolve bằng slugify |
| BUG-13 | Toolbar trên cùng trùng chức năng theo tab gây rối thao tác | Medium | Fixed (2026-04-23) — bỏ Thêm nguồn/Lưu ghi chú/Tìm kiếm/Xuất văn bản khỏi toolbar chính |
| BUG-14 | Nút Mở tài liệu ở sidebar Thư viện nguồn hiển thị không rõ trên một số trạng thái | Medium | Fixed (2026-04-23) — chuẩn hóa trạng thái enabled/disabled + contrast rõ |

Quy tắc xử lý bug:

1. Khi fix bug phải cập nhật bảng này.
2. Nếu bug làm thay đổi business rule hoặc contract, phải cập nhật cả architecture.
3. Mọi bug liên quan runtime, persistence, extraction correctness, anchor format hoặc import mapping bắt buộc có regression test.

---

## 6. Risk tracker khởi tạo

| ID | Rủi ro | Hướng xử lý sơ bộ |
| --- | --- | --- |
| RISK-01 | Text extract từ PDF nhiều cột bị sai thứ tự đọc | Dùng normalizer + cho phép chỉnh tay trong note |
| RISK-02 | Table auto-parse không ổn định | Thiết kế preview + confirm, không commit tự động |
| RISK-03 | QWebEngine làm editor quá nặng | Cho phép chiến lược editor native + preview riêng |
| RISK-04 | Đồng bộ tab PDF/note bị lệch state | Dùng source_id làm key, không dựa tab index |
| RISK-05 | Asset bị orphan khi đổi/xóa note | Dùng AssetService + reference scan trước delete |

---

## 7. Backlog mở rộng sau alpha

### FEAT-01. Graph View kiểu Obsidian

Hiện trạng (2026-04-23):

1. FEAT-01 đã hoàn tất qua 4 phase A/B/C/D.
2. Có `GraphService` sinh node/edge + filter cơ bản và virtualize cho đồ thị lớn.
3. Có `GraphViewWidget` (`QGraphicsView`) với render node/edge, pan/zoom, search node, highlight 1-hop/2-hop, fit-to-view.

Tính khả thi:

1. Khả thi cao cho bản v1.1 nếu triển khai theo pha nhỏ.
2. Không cần đổi schema bắt buộc ở bước đầu (dùng `links` hiện có).
3. Có thể bắt đầu bằng graph tĩnh (pan/zoom/click node) trước khi thêm force simulation nâng cao.

Lộ trình đề xuất:

1. Phase A (service): Done (2026-04-23) — `GraphService` trả node/edge từ `notes` + `links`, filter theo note_type/tag/source, hỗ trợ bỏ node cô lập.
2. Phase B (UI cơ bản): Done (2026-04-23) — thêm `GraphViewWidget` dùng `QGraphicsView` để render node/edge, có filter cơ bản, click node để mở source/note liên quan qua MainWindow relay.
3. Phase C (UX): Done (2026-04-23) — thêm tìm kiếm node, highlight hàng xóm 1-hop/2-hop, fit-to-view.
4. Phase D (tối ưu): Done (2026-04-23) — gom cụm theo tag, lưu layout cục bộ, virtualize khi đồ thị lớn.

Tiêu chí chấp nhận tối thiểu FEAT-01:

1. Hiển thị được đồ thị note-link từ dữ liệu thật.
2. Click node mở đúng note/source liên quan.
3. Có filter theo ít nhất một chiều (tag hoặc note_type).
4. Có test service cho sinh node/edge và test smoke cho GraphView.

---

## 8. Hướng dẫn sử dụng AI Agent

### 8.1. Prompt khởi đầu bắt buộc

```text
Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) và [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) trước khi code. Tuân thủ tech stack, cấu trúc thư mục, business rules, acceptance criteria và checklist sau mỗi task.
```

### 8.2. Prompt cho task tính năng mới

```text
Trước khi bắt đầu:
1. Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
2. Đọc [`PKM_ROADMAP.md`](./PKM_ROADMAP.md)
3. Xác định phase và sprint của task

Nhiệm vụ: [mô tả tính năng]

Sau khi hoàn thành:
1. Cập nhật trạng thái task trong ROADMAP
2. Cập nhật CHANGELOG trong ARCHITECTURE
3. Viết tests liên quan
4. Báo cáo file đã thay đổi và kết quả test
```

### 8.3. Prompt cho task fix bug

```text
Trước khi bắt đầu:
1. Đọc [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) mục business rules, data safety và coding standards
2. Đọc [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) mục bug tracker và risk tracker

Nhiệm vụ: Fix [BUG-ID]

Sau khi hoàn thành:
1. Cập nhật bug tracker
2. Thêm regression test
3. Ghi rõ root cause và solution vào CHANGELOG
4. Báo cáo test pass
```

### 8.4. Prompt cho task refactor

```text
Trước khi bắt đầu:
1. Kiểm tra boundaries trong [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
2. Đảm bảo không làm thay đổi business behavior và các nguyên tắc khóa

Nhiệm vụ: [mô tả refactor]

Sau khi hoàn thành:
1. Xác nhận không đổi business behavior
2. Cập nhật CHANGELOG nếu cấu trúc hoặc interface đổi
3. Chạy full tests liên quan
```

### 7.5. Checklist bắt buộc sau mỗi task

- [ ] Chạy tests liên quan
- [ ] Không vi phạm boundaries giữa UI, services, extraction, search, persistence
- [ ] Không phá các nguyên tắc khóa
- [ ] Cập nhật ROADMAP
- [ ] Cập nhật ARCHITECTURE CHANGELOG
- [ ] Nếu có schema change thì có migration notes
- [ ] Báo cáo tóm tắt thay đổi

---

## 8. Tài liệu AI Agent phải đọc theo từng nhu cầu

| Nhu cầu | File cần đọc |
| --- | --- |
| Kiến trúc tổng thể | [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) |
| Business rules và extraction rules | [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) mục 6 |
| Schema database | [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md) mục 7 |
| Tiến độ project | [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) |
| Task ưu tiên tiếp theo | [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) mục 2 và 3 |
| Bug hiện có | [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) mục 5 |
| Risk kỹ thuật | [`PKM_ROADMAP.md`](./PKM_ROADMAP.md) mục 6 |

---

## 9. Quy tắc báo cáo tiến độ

Mỗi lần AI Agent hoàn thành task phải báo theo mẫu tối thiểu:

1. Task đã thực hiện
2. Files đã thay đổi
3. Kết quả test
4. Rủi ro còn lại
5. Cập nhật nào đã ghi vào ROADMAP và ARCHITECTURE

Không được chỉ báo “đã xong” mà không có các thông tin trên.

---

## 10. Tiêu chí sẵn sàng phát hành v1.0

v1.0 chỉ được xem là sẵn sàng khi thỏa đồng thời:

1. Toàn bộ Phase 1 đến Phase 5 hoàn thành ở mức tối thiểu cho phạm vi v1.0
2. Coverage đạt mục tiêu cho phần core services, extraction và search
3. Không còn bug mức High ở extraction correctness, persistence, migration, anchor format hoặc single-instance lock
4. Build standalone chạy được trên Windows không cần cài Python
5. Có tài liệu hướng dẫn sử dụng cơ bản
6. Có backup/restore hoạt động
7. Đã kiểm thử ít nhất một project nghiên cứu có từ 30 PDF trở lên với workflow đọc, extract, note và export cơ bản

---

## 11. Cập nhật roadmap

### 2026-04-22

ADDED | OpenAI GPT-5.4 Thinking | Khởi tạo roadmap phát triển chuẩn cho Ứng dụng Desktop Quản lý Kiến thức Cá nhân phục vụ nghiên cứu từ giai đoạn đặc tả đến chuẩn bị phát hành. Xác định phase, sprint, acceptance criteria, bug tracker, risk tracker và bộ hướng dẫn bắt buộc cho AI Agent.

### 2026-05-03

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Maintenance pass theo review chất lượng | Hoàn thành 3 hạng mục: (1) thêm `WorkspaceOrchestrator` để kéo bớt orchestration khỏi `DualPaneHost` và `MarkdownEditorWidget`; (2) chuẩn hóa error handling ở các luồng đã chạm tới, bỏ `pass` im lặng và thay bằng contextual logging + thông báo UI phù hợp; (3) đồng bộ contract `GraphService.build_graph` với tests (hỗ trợ cả `source_id` và `source_code`).

TEST STATUS | `python -m pytest -q` | 297/297 passed.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Process hardening theo philosophy_of_software_design | Bổ sung guardrails vào tài liệu vận hành: complexity gate, deep-module rule, design-it-twice checklist, anti pass-through, contract/regression expectations và decision-log fields để giảm lỗi mới và giảm tích lũy độ phức tạp.

### 2026-05-07

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Post-Phase7 Hardening + Note Management UI | Bổ sung tự phục hồi source_note thiếu file markdown trong luồng mở source, đảm bảo invariant mỗi PDF luôn có 1 source_note ngay tại import, thêm tab Quản lý ghi chú với bộ lọc nâng cao/preview/xóa cứng, và đổi nhãn sidebar `Research Board` -> `Bảng nghiên cứu`, `Dự án` -> `Project`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Markdown quote UX | `MarkdownEditorWidget` hỗ trợ hành vi Enter kiểu Zettlr cho blockquote: Enter trong quote có nội dung sẽ tiếp tục chuỗi "> ", Enter trên dòng "> " rỗng sẽ thoát blockquote; đồng thời áp dụng shading full-row cho dòng quote để dễ đọc.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Settings + Editor UX | `SettingsView` thêm tùy chọn font editor (`editor.fontFamily`) và ligatures (`editor.fontLigatures`), mặc định `Fira Code, Roboto Mono, monospace` và `true`; thay đổi được áp dụng tức thì cho Markdown editor đang mở.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Markdown Editor UX | Bổ sung nhận diện và tô nổi bật biểu thức toán LaTeX (không render) trong editor theo phong cách code theme để dễ phân biệt: hỗ trợ các mẫu `$...$`, `$$...$$`, `\(...\)`, `\[...\]`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Markdown Editor UX | Tinh chỉnh palette math theo tông VS Code Dark/Light và tô màu theo token giống code editor (delimiter, lệnh `\command`, số, toán tử, ngoặc) để biểu thức toán dễ đọc hơn khi soạn thảo.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | Settings + UI Shell | Sửa mismatch giữa Cài đặt font editor và hiển thị note bằng cách bỏ hardcode `font-family` của `QPlainTextEdit#markdown_editor` trong QSS để editor tuân thủ đúng `editor.fontFamily`/`editor.fontLigatures`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | Chuyển hiển thị `Mode: Global/Project` từ toolbar trên cùng sang tab `Thiết lập` (nhóm Trình soạn thảo) để giảm nhiễu giao diện chính.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SHELL | Loại bỏ hoàn toàn nút `Project` trên toolbar; trạng thái mode chỉ còn hiển thị trong tab `Thiết lập`.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | UI_SETTINGS | Mode trong tab `Thiết lập` hiển thị dạng badge màu để nhận biết nhanh: Global màu xanh lá, Project màu xanh dương.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | WORKSPACE_V2 | Nâng cấp `Không gian làm việc` sang 2 khung độc lập: PDF tham khảo nhiều tab ở panel trái và editor Markdown scratch (file-based, không gắn note DB) ở panel phải; hỗ trợ lưu thủ công `.md` và cảnh báo lưu khi đóng ứng dụng nếu còn thay đổi chưa lưu.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | LIBRARY_TO_WORKSPACE | `Thư viện nguồn` thêm action `Mở tài liệu` để mở trực tiếp PDF vào workspace tham khảo mới, tách biệt với action `Ghi chú nguồn`.

FIXED | GitHub Copilot (GPT-5.3-Codex) | NOTE_DELETE | Sửa lỗi xóa cứng note đã soft-delete: cho phép phân tích impact trên deleted note để không còn báo lỗi "Không tìm thấy note id=..." trước khi xác nhận xóa cứng.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | WORKSPACE_UX | Tinh gọn header `Không gian làm việc`: bỏ tiêu đề text dư thừa, thêm nhãn trạng thái file scratch theo thời gian thực (`<file>.md • Đã lưu/Chưa lưu*`) và thêm nút `Đóng tất cả` tab PDF tham khảo.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTS_UI | Bổ sung smoke tests cho UX mới của `DraftWorkspaceView` (status label, không còn tiêu đề trên cùng, đóng tất cả tab) và test `MainWindow.closeEvent` chặn đóng app khi workspace trả về từ chối xác nhận lưu.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | WORKSPACE_READING_SPACE | Tối ưu không gian đọc bên trái trong `Không gian làm việc`: toolbar PDF compact hơn, tab tài liệu dùng compact style riêng, và thêm toggle `Tập trung đọc` để ẩn toolbar điều hướng PDF khi cần đọc liên tục.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTS_UI | Thêm regression smoke test cho read-focus mode (`DraftWorkspaceView`) để đảm bảo bật chế độ đọc tập trung sẽ ẩn toolbar PDF đúng hành vi.

CHANGED | GitHub Copilot (GPT-5.3-Codex) | WORKSPACE_EXTRACTION | Dời 3 thao tác `Trích văn bản` / `Trích bảng` / `Chụp ảnh` từ `GC Nguồn` sang `Không gian làm việc`; extraction giờ gắn với PDF tham khảo + scratch markdown editor, còn `GC Nguồn` bỏ toolbar trích xuất để tránh dư thừa chức năng.

ADDED | GitHub Copilot (GPT-5.3-Codex) | TESTS_UI | Thêm smoke tests xác nhận các nút trích xuất của workspace chỉ bật khi đã mở tài liệu tham khảo và `DualPaneHost` không còn hiển thị `extraction_toolbar`.

TEST STATUS | `python -m pytest tests/ui/test_smoke.py -q` | 54/54 passed.
