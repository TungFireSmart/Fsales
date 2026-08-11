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

## 2b. Cấu hình CSDL — không cần làm gì thêm

Anh Tùng chốt 6/8/2026: **giữ mật khẩu mặc định trong `misc.py`**, không phát kèm file
config. Bộ cài không cần thêm gì, app chạy được ngay sau khi cài.

Nếu về sau muốn ghi đè trên một máy cụ thể mà không sửa mã nguồn: đặt biến môi trường
`FSALES_DB_PASSWORD`, hoặc thả `fsales_config.json` cạnh `Fsales.exe`
(mẫu: `fsales_config.example.json`). Cả hai đều thắng giá trị mặc định.

⛔ Nếu sau này bỏ mặc định đi thì **không** được thêm `fsales_config.json` vào `datas` của
`main.spec` — làm vậy là nhúng lại mật khẩu vào `.exe`. Phải để **bộ cài** đặt nó cạnh exe
kèm cờ `onlyifdoesntexist`, nếu không mỗi lần cập nhật sẽ ghi đè config của nhân viên.

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

## 🔴 PHÁT HÀNH TRỰC TIẾP QUA LINK — BẮT BUỘC CHO BẢN 3.0.24

**Mọi máy đang chạy ≤ 3.0.23 đều KHÔNG tự cập nhật lên 3.0.24 được.**

Lý do: bản vá nằm **bên trong chính cái updater bị hỏng**. Máy nhân viên sẽ tải bộ cài
3.0.24 về đủ và đúng, rồi vẫn kẹt y hệt ở bước chạy bộ cài — vì đoạn chạy bộ cài là code
của bản 3.0.22/3.0.23 đang nằm trong `.exe` trên máy họ, không phải code mới.

⇒ Bản 3.0.24 phải **gửi link cho nhân viên tự tải và cài tay**. Từ 3.0.25 trở đi mới quay
lại tự cập nhật được.

**Các bước:**

1. Upload `Fsales-Setup-EXE-3.0.24.exe` lên GitHub Releases tag `v3.0.24`
   (Releases → Draft a new release → chọn tag → kéo file vào → Publish).
2. Lấy link tải trực tiếp, dạng:
   `https://github.com/TungFireSmart/Fsales_update/releases/download/v3.0.24/Fsales-Setup-EXE-3.0.24.exe`
3. Mở link đó bằng **trình duyệt ẩn danh** để chắc chắn tải được khi chưa đăng nhập GitHub.
4. Gửi nhân viên kèm đúng 4 câu này:

   > Tải file này về: `<link>`
   > **Đóng FSales trước khi cài.**
   > Chuột phải file vừa tải → **Run as administrator** → bấm **Yes**.
   > Cứ bấm Next tới hết, **đừng đổi thư mục cài** mà nó gợi ý sẵn.

   🔴 Câu cuối quan trọng nhất: bộ cài tự lấy thư mục của bản đã cài trên máy đó
   (theo `AppId`). Nhân viên tự đổi chỗ là sinh **hai bản song song**, shortcut cũ vẫn
   trỏ bản cũ ⇒ đúng triệu chứng "cài xong vẫn chạy bản cũ".

5. Vẫn cập nhật `manifest.json` lên 3.0.24 như bước 5 — để máy nào cài tay xong thì từ
   lần sau nhận đúng mốc so sánh, và máy nào bỏ sót vẫn được nhắc.

**Cách kiểm nhân viên đã cài chưa:** bảo họ mở FSales, nhìn số phiên bản ở góc cửa sổ
(`label_version`), phải là `v3.0.24`.

---

## Cách hoạt động sau khi sửa (cập nhật 11/8/2026)

```
App khởi động → sau 1,5 giây đọc manifest (có chống cache CDN)
   → thấy bản mới, hỏi người dùng
   → tải ở LUỒNG NỀN, có thanh tiến trình, app vẫn dùng được
   → kiểm sha256 + kích thước
   → HIỆN HỘP THOẠI BÁO TRƯỚC, người dùng bấm OK        ← 11/8: chuyển lên TRƯỚC
   → sinh capnhat.bat + chaycai.ps1, app THOÁT
   → .bat chạy trong CỬA SỔ CONSOLE RIÊNG                ← 11/8: CREATE_NEW_CONSOLE
   → .bat chờ tiến trình app chết hẳn (ping, tối đa 60s) ← 11/8: bỏ `timeout`
   → chaycai.ps1 xin quyền admin (UAC) rồi chạy bộ cài   ← 11/8: Start-Process -Verb RunAs
      /SILENT /DIR="thư mục đã đăng ký trong Registry"
   → tự mở lại app (quyền thường, không phải admin)
```

### Ba lỗi đã vá ngày 11/8/2026 (bản 3.0.22/3.0.23 hỏng cả ba)

| # | Lỗi | Vì sao chết |
|---|---|---|
| 1 | `.bat` chạy bằng `DETACHED_PROCESS` | Cờ đó nghĩa là **không có console nào cả** (cờ để hiện console là `CREATE_NEW_CONSOLE`). Không console ⇒ UAC không lên ⇒ bộ cài không chạy ⇒ `.bat` rơi vào `pause` và **treo vĩnh viễn mà không có cửa sổ nào để thấy** |
| 2 | Vòng chờ dùng `timeout /t 1` | `timeout.exe` cần handle input của console. Thiếu console là nó chết ngay ⇒ vòng chờ 60 giây co lại còn vài mili giây ⇒ chạy bộ cài khi `Fsales.exe` còn khoá file |
| 3 | `main.py` gọi `launch_installer()` **trước** hộp thoại | `.bat` bắt đầu đếm PID trong lúc app còn sống và người dùng còn chưa bấm OK |

**Dấu vết nhận biết máy nào dính lỗi này:** trong `%TEMP%\fsales-update\` có
`capnhat.bat` **còn nguyên** (dòng cuối của nó là lệnh tự xoá, còn nghĩa là chết giữa
chừng) và **không có** `install.log` (Inno Setup tạo log ngay khi khởi động).

## Khi cập nhật vẫn hỏng thì xem gì

| Hiện tượng | Xem ở đâu |
|---|---|
| Cài xong vẫn bản cũ | `%TEMP%\fsales-update\install.log` — kiểm dòng `Dest filename` xem cài vào thư mục nào |
| Không thấy bản mới | Mở thẳng URL manifest trên trình duyệt, xem `version` đã đúng chưa |
| Tải xong báo lỗi sha256 | Tính lại hash của file thật rồi sửa manifest |
| **Không có `install.log`** | Bộ cài **chưa từng chạy**. Xem bảng ba lỗi ở trên. Chữa ngay: chạy tay `%TEMP%\fsales-update\FsaleSetup.exe` (chuột phải → Run as administrator) |
| `capnhat.bat` còn nằm đó | Script chết giữa chừng. Chạy tay nó bằng nháy đúp để xem lỗi hiện ra |
| Cửa sổ đen hiện rồi tắt luôn | Xem `install.log`; nếu mã lỗi 1223 là người dùng bấm "No" ở UAC |

Các file trung gian đều nằm ở `%TEMP%\fsales-update\`:
`FsaleSetup.exe` (bộ cài đã tải) · `capnhat.bat` · `chaycai.ps1` · `install.log`.

---

## Danh sách kiểm trước khi phát

- [ ] **Chạy `.venv\Scripts\python.exe kiem_tra_truoc_phat_hanh.py` — phải xanh hết**
      (thêm 11/8/2026, việc `B9`). Nó bắt: import gãy · `self.X()` gọi hàm không tồn tại ·
      lệch số giữa `version.py` và `.iss` · `AppId` bị đổi · chốt chặn cũ bị dựng lại.
      Script **không** thay được việc mở app bấm thử.
- [ ] `version.py` đã bump
- [ ] `AppVersion` trong `.iss` khớp `version.py`
- [ ] `AppId` trong `.iss` **không đổi**
- [ ] Đã mở thử `.exe` vừa build, tiêu đề hiện đúng phiên bản
- [ ] `sha256` + `size` trong manifest khớp file thật
- [ ] `installer_url` tải được bằng trình duyệt ẩn danh
- [ ] Thử cập nhật trên **một máy** trước khi báo cả công ty
