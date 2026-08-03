# Hướng dẫn Push lên GitHub

Git repository đã được khởi tạo thành công. Dưới đây là hướng dẫn để push lên GitHub:

## Bước 1: Tạo repository trên GitHub

1. Đăng nhập vào [GitHub.com](https://github.com)
2. Nhấp vào **+** ở góc trên cùng → **New repository**
3. Đặt tên: `research-pkm` (hoặc tên khác tùy ý)
4. Mô tả: `Personal Knowledge Management Desktop App for Research`
5. Chọn **Public** hoặc **Private** tùy ý
6. **Không** chọn "Initialize this repository with a README, .gitignore, or license" (vì chúng tôi đã có local repo)
7. Nhấp **Create repository**

## Bước 2: Thêm remote và push

Sau khi tạo repository trên GitHub, bạn sẽ thấy URL. Chạy các lệnh dưới đây (thay `YOUR_USERNAME` bằng username GitHub của bạn):

```bash
# Thêm remote URL
git remote add origin https://github.com/YOUR_USERNAME/research-pkm.git

# Đổi tên branch sang main (tùy chọn, GitHub mặc định là main)
git branch -M main

# Push code lên GitHub
git push -u origin main
```

Hoặc nếu bạn muốn dùng SSH (yêu cầu cấu hình SSH key trước):

```bash
git remote add origin git@github.com:YOUR_USERNAME/research-pkm.git
git branch -M main
git push -u origin main
```

## Bước 3: Xác thực

Khi chạy `git push`, nếu dùng HTTPS, bạn sẽ được yêu cầu:
- **Username**: Tên GitHub
- **Password**: Token truy cập cá nhân (Personal Access Token - PAT)
  - Tạo PAT tại: https://github.com/settings/tokens
  - Chọn scopes: `repo`, `workflow`

## Bước 4: Kiểm tra

Truy cập vào `https://github.com/YOUR_USERNAME/research-pkm` để xem code của bạn đã được push lên GitHub.

## Các lệnh Git cơ bản sau này

```bash
# Xem trạng thái files
git status

# Commit thay đổi mới
git add -A
git commit -m "Your commit message"

# Push lên GitHub
git push

# Pull từ GitHub
git pull
```

## Ghi chú

- Repository hiện đã có **1 commit**: "Initial commit: Research PKM v1.0-alpha"
- Branch hiện tại: **master** (có thể đổi sang **main** khi push)
- Tất cả files đã được tracked (trong .gitignore: .venv, __pycache__, data/, logs/, .DS_Store, v.v.)

---

**Cần giúp?** Tham khảo: https://docs.github.com/en/get-started/quickstart/create-a-repo
