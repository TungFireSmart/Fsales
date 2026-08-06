# HƯỚNG DẪN PHÁT HÀNH BẢN MỚI — Fsales

> Chốt 6/8/2026, sau khi sửa `auto_update.py`.
> Làm **đủ và đúng thứ tự** 5 bước, thiếu bước nào là máy nhân viên sẽ không nhận bản mới.

---

## 1. Bump số phiên bản — CHỈ MỘT CHỖ

`version.py`:

```python
APP_VERSION = "3.0.22"
```

⚠️ Số này phải **lớn hơn** bản đang chạy ngoài thực địa, so theo từng nhóm số
(`3.0.9 < 3.0.10`). Quên bump ⇒ máy nhân viên coi như "đã mới nhất" và không tải gì cả.

## 2. Sửa file `.iss` của Inno Setup cho khớp

```
AppVersion=3.0.22
AppId={{...}}          ; ⛔ GIỮ NGUYÊN, KHÔNG BAO GIỜ ĐỔI
DefaultDirName={autopf}\Fsales
```

🔴 **`AppId` phải giữ nguyên qua mọi phiên bản.** Đổi `AppId` là Windows coi đây
là một phần mềm khác ⇒ cài thành bản thứ hai, bản cũ vẫn còn, shortcut cũ vẫn trỏ
bản cũ. Đây chính là triệu chứng "cài xong vẫn chạy bản cũ".

## 3. Build

```bat
pyinstaller main.spec --noconfirm
```

Rồi build bộ cài bằng Inno Setup → ra `FsaleSetup.exe`.

**Kiểm trước khi phát:** mở `dist\Fsales\Fsales.exe`, nhìn tiêu đề cửa sổ phải hiện
đúng số phiên bản mới. Sai ở đây thì đừng phát tiếp.

## 4. Tính sha256 và kích thước

```powershell
Get-FileHash .\FsaleSetup.exe -Algorithm SHA256 | Format-List
(Get-Item .\FsaleSetup.exe).Length
```

## 5. Đẩy manifest lên repo `Fsales_update`

`updates/latest/manifest.json`:

```json
{
  "version": "3.0.22",
  "installer_url": "https://github.com/TungFireSmart/Fsales_update/releases/download/v3.0.22/FsaleSetup.exe",
  "notes": "Tăng tốc kết nối CSDL, sửa lỗi tự cập nhật",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb924...",
  "size": 69753922
}
```

`sha256` và `size` là **tuỳ chọn nhưng nên có** — thiếu thì app vẫn chạy được,
nhưng mất lớp bảo vệ chống file tải dở/hỏng.

⚠️ Đừng để `installer_url` trỏ vào `raw.githubusercontent.com` cho file 70 MB.
Dùng **GitHub Releases**. File lớn trong repo thường bị chặn hoặc rất chậm.

---

## Cách hoạt động sau khi sửa (6/8/2026)

```
App khởi động → sau 1,5 giây đọc manifest (có chống cache CDN)
   → thấy bản mới, hỏi người dùng
   → tải ở LUỒNG NỀN, có thanh tiến trình, app vẫn dùng được
   → kiểm sha256 + kích thước
   → sinh capnhat.bat, app THOÁT
   → .bat chờ tiến trình app chết hẳn (tối đa 60 giây)   ← bước bản cũ THIẾU
   → chạy bộ cài /SILENT /DIR="đúng thư mục đang chạy"   ← bản cũ THIẾU /DIR
   → tự mở lại app
```

## Khi cập nhật vẫn hỏng thì xem gì

| Hiện tượng | Xem ở đâu |
|---|---|
| Cài xong vẫn bản cũ | `%TEMP%\fsales-update\install.log` — kiểm dòng `Dest filename` xem cài vào thư mục nào |
| Không thấy bản mới | Mở thẳng URL manifest trên trình duyệt, xem `version` đã đúng chưa |
| Tải xong báo lỗi sha256 | Tính lại hash của file thật rồi sửa manifest |
| Bộ cài không chạy | Chạy tay `%TEMP%\fsales-update\capnhat.bat` để xem lỗi |

Các file trung gian đều nằm ở `%TEMP%\fsales-update\`.

---

## Danh sách kiểm trước khi phát

- [ ] `version.py` đã bump
- [ ] `AppVersion` trong `.iss` khớp `version.py`
- [ ] `AppId` trong `.iss` **không đổi**
- [ ] Đã mở thử `.exe` vừa build, tiêu đề hiện đúng phiên bản
- [ ] `sha256` + `size` trong manifest khớp file thật
- [ ] `installer_url` tải được bằng trình duyệt ẩn danh
- [ ] Thử cập nhật trên **một máy** trước khi báo cả công ty
