# DECISION LOG

Dùng file này để ghi các quyết định kỹ thuật quan trọng nhưng không nhất thiết là thay đổi kiến trúc cấp cao.

## Format

`YYYY-MM-DD | Chủ đề | Quyết định | Lý do | Ảnh hưởng`

## Trường bắt buộc cho quyết định quan trọng

1. Bối cảnh vấn đề (pain hiện tại).
2. Ít nhất 2 phương án đã cân nhắc.
3. Lý do chọn phương án cuối.
4. Tác động complexity:
	- giảm/tăng change amplification?
	- giảm/tăng cognitive load?
	- có tạo unknown unknowns mới không?
5. Contract bị ảnh hưởng (nếu có).
6. Kế hoạch test/regression đi kèm.
7. Kế hoạch rollback hoặc migration path (nếu liên quan schema/data semantics).

## Mẫu

2026-04-22 | Markdown editor | Chọn hybrid editor + preview thay vì full QWebEngine editor | Giảm độ phức tạp chỉnh sửa và tăng khả năng kiểm soát keybindings | Ảnh hưởng ui/widgets/markdown_editor.py và docs

## Mẫu mở rộng (khuyến nghị)

2026-05-03 | Workspace orchestration |
Quyết định: thêm lớp UseCase/Orchestrator thay vì tiếp tục nhét domain flow trong widget |
Phương án đã cân nhắc: (A) giữ logic trong UI và dọn từng hàm nhỏ, (B) tách use-case service |
Lý do chọn: B giảm leakage và contract rõ hơn giữa UI-service |
Complexity impact: giảm change amplification ở dual-pane/editor, giảm unknown unknowns khi sửa luồng extract/save |
Contract ảnh hưởng: API gọi giữa widget và service |
Test plan: thêm/điều chỉnh unit + integration + smoke liên quan |
Ảnh hưởng: core/services/workspace_orchestrator.py, ui/widgets/*
