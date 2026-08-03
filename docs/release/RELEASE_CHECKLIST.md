# RELEASE CHECKLIST

## Trước khi build

- [ ] Đã đọc lại [`PKM_ARCHITECTURE.md`](../architecture/PKM_ARCHITECTURE.md)
- [ ] Đã đọc lại [`PKM_ROADMAP.md`](../roadmap/PKM_ROADMAP.md)
- [ ] Không còn bug High liên quan đến migration, source anchor, save/load
- [ ] Test pass
- [ ] Coverage đạt mục tiêu
- [ ] Migration chạy được trên DB mới
- [ ] Migration chạy được trên DB cũ mẫu
- [ ] Backup/restore hoạt động
- [ ] Single-instance lock hoạt động

## Kiểm tra chức năng lõi

- [ ] Import PDF vào library
- [ ] Mở PDF trong dual-pane
- [ ] Tạo source note tự động hoặc mở đúng note đã bind
- [ ] Extract text hoạt động
- [ ] Crop bảng có preview
- [ ] Capture image tạo asset đúng
- [ ] Tagging hoạt động
- [ ] Wikilink và backlinks hoạt động
- [ ] Search ra kết quả đúng
- [ ] Research Board lưu/đọc được
- [ ] Export clean text bundle hoạt động

## Kiểm tra dữ liệu

- [ ] Không mất note sau khi đóng/mở app
- [ ] Đổi tên source không làm mất binding
- [ ] File PDF bị di chuyển có cơ chế relink hoặc cảnh báo
- [ ] Delete policy đúng

## Tài liệu

- [ ] README cập nhật
- [ ] CHANGELOG cập nhật
- [ ] ROADMAP cập nhật
- [ ] ARCHITECTURE changelog cập nhật nếu cần
