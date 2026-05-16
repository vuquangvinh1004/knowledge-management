# Changelog

Tat ca thay doi dang ke cua du an se duoc ghi o day.

## 2026-05-12

### Changed

- Hardening: bo sung logging cho cac luong truoc day nuot exception trong main window va startup identity.
- Documentation: cap nhat README theo trang thai hien tai (Phase 7 hoan tat, 375 tests).
- Project governance: bo sung LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.
- Tooling: them pyproject.toml cho cau hinh ruff/mypy.
- CI: them workflow chay test tren Windows cho pull request va push.
- License policy: chot public license la MIT va bo sung thong tin ro rang trong README/CONTRIBUTING.
- Refactor: tach logic template + title warning cua note sang module `core/services/note_templates.py` de giam do lon cua NoteService.
- Refactor (wave 2): tach orchestration cua MainWindow sang module `ui/handlers/main_window_handlers.py` va giu MainWindow theo huong layout + signal wiring.
- Repo cleanup: tao `archive/` va chuyen 4 file markdown nang cap cu o root vao `archive/root_legacy_notes/`.
- Fix icon: khoi phuc icon bi di chuyen nham vao archive, dua ve `assets/icons/`, cap nhat runtime icon resolution trong `main.py` va cap nhat `research_pkm.spec` de bundle + set icon cho exe.
