# PROJECT STRUCTURE

## Cấu trúc thư mục đề xuất

```text
research_pkm/
│
├── main.py
├── README.md
├── docs/
│   ├── architecture/PKM_ARCHITECTURE.md
│   ├── roadmap/PKM_ROADMAP.md
│   ├── spec/PKM_SPEC_FINAL.md
│   ├── onboarding/START_HERE_FOR_AI_AGENT.md
│   ├── onboarding/REQUIREMENTS.md
│   ├── onboarding/PKM_README_PROJECT_STARTER.md
│   ├── onboarding/AI_AGENT_WORKFLOW.md
│   ├── standards/CODING_STANDARDS.md
│   ├── standards/TESTING_STRATEGY.md
│   ├── standards/PROJECT_STRUCTURE.md
│   ├── schema/SCHEMA_NOTES.md
│   ├── extraction/EXTRACTION_RULES.md
│   ├── export/EXPORT_FORMATS.md
│   ├── reference/DESIGN.md
│   ├── reference/philosophy_of_software_design.md
│   ├── reference/Chen_doi_tuong_trong_Markdown.md
│   ├── reference/List of LaTeX environments.pdf
│   ├── maintenance/DECISION_LOG.md
│   ├── maintenance/GITHUB_SETUP.md
│   ├── maintenance/PERFORMANCE_IMPROVEMENTS.md
│   ├── release/CHANGELOG.md
│   └── release/RELEASE_CHECKLIST.md
├── vendor/
│   └── design.md-0.1.0/
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── paths.py
│   ├── settings.py
│   └── database.py
│
├── core/
│   ├── __init__.py
│   ├── app_kernel/
│   │   ├── __init__.py
│   │   ├── bootstrap.py
│   │   ├── startup_checks.py
│   │   ├── shutdown_manager.py
│   │   └── app_lock.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── source_service.py
│   │   ├── note_service.py
│   │   ├── extract_service.py
│   │   ├── asset_service.py
│   │   ├── tag_service.py
│   │   ├── link_service.py
│   │   ├── search_service.py
│   │   ├── board_service.py
│   │   ├── export_service.py
│   │   ├── backup_service.py
│   │   ├── migration_service.py
│   │   └── settings_service.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── text_extractor.py
│   │   ├── table_extractor.py
│   │   ├── image_capture.py
│   │   ├── anchors.py
│   │   └── markdown_renderers.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fts_index.py
│   │   ├── query_parser.py
│   │   └── ranking.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── connection.py
│   │   ├── session.py
│   │   └── migrations/
│   │       └── versions/
│   └── utils/
│       ├── __init__.py
│       ├── constants.py
│       ├── validators.py
│       ├── exceptions.py
│       ├── helpers.py
│       └── logger.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── views/
│   │   ├── dashboard_view.py
│   │   ├── library_view.py
│   │   ├── dual_pane_view.py
│   │   ├── board_view.py
│   │   ├── search_view.py
│   │   └── settings_view.py
│   ├── widgets/
│   │   ├── pdf_viewer.py
│   │   ├── markdown_editor.py
│   │   ├── note_preview.py
│   │   ├── source_tabs.py
│   │   ├── note_tabs.py
│   │   ├── sidebar_tree.py
│   │   ├── status_strip.py
│   │   ├── warning_banner.py
│   │   └── dialogs/
│   └── styles/
│       ├── themes.py
│       └── qss_styles.py
│
├── data/
│   ├── database/
│   ├── sources/
│   ├── notes/
│   ├── assets/
│   ├── exports/
│   ├── backups/
│   ├── temp/
│   └── logs/
│
├── docs/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── ui/
│   └── fixtures/
│
└── scripts/
    ├── dev/
    └── release/
```

## Quy tắc cấu trúc

1. Không đặt SQL trực tiếp trong UI.
2. Không đặt extraction logic trong widget.
3. Không để renderer Markdown và persistence note lẫn vào nhau.
4. Mọi file dữ liệu người dùng phải nằm dưới `data/`.
5. Mọi thay đổi schema phải đi qua migration.
6. Mọi contract export phải được ghi trong `docs/export/EXPORT_FORMATS.md`.
