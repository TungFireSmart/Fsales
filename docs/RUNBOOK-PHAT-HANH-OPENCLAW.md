# RUNBOOK PHÁT HÀNH FSALES 3.0.24 — DÀNH CHO OPENCLAW

> **Viết ngày 11/8/2026 cho agent tự chạy.** Con người đọc bản tóm tắt ở
> `docs/HUONG-DAN-PHAT-HANH.md`; file này là bản **thi hành từng lệnh**.
>
> Đọc hết mục **0. LUẬT CHƠI** trước khi chạy lệnh đầu tiên.

---

## 0. LUẬT CHƠI — ĐỌC TRƯỚC, KHÔNG ĐƯỢC BỎ QUA

1. **Chạy đúng thứ tự bước 0 → 9.** Không nhảy cóc, không gộp bước.
2. **Mỗi bước có một CỔNG KIỂM (🚦).** Cổng không xanh ⇒ **DỪNG NGAY**, báo anh Tùng
   kèm nguyên văn output. **Không tự chữa, không tự đoán, không thử cách khác.**
3. **Không sửa bất kỳ file `.py` nào** trong `D:\Fsales_PCCC`. Runbook này chỉ
   *build và phát hành* thứ đã có sẵn. Thấy code sai ⇒ báo, đừng vá.
4. **Không đụng cơ sở dữ liệu.** Không chạy `run_sql_file.py`, không `UPDATE`, không
   `DELETE`. Phát hành là việc của file, không phải của dữ liệu.
5. **Không đụng máy nhân viên.** Không gửi tin nhắn, không cài đặt từ xa. Bước cuối
   chỉ *soạn sẵn* nội dung để anh Tùng tự gửi.
6. **Không `git push --force`** ở bất kỳ repo nào.
7. Gặp lỗi lạ không có trong bảng lỗi ⇒ **DỪNG**, chép nguyên văn, báo anh Tùng.
8. Toàn bộ runbook chạy trên **máy anh Tùng** (ổ `D:` phải tồn tại). Máy khác là sai chỗ.
9. 🔴 **Mọi cổng kiểm quan trọng đều là script Python, không phải lệnh shell.**
   Chạy nguyên văn, đừng "dịch" sang PowerShell hay thêm bớt dấu nháy.
   *(Bài học 11/8/2026: bản runbook đầu dùng `find /c /v ""` và `findstr /C:"..."` —
   cú pháp riêng của `cmd.exe`. OpenClaw chạy và vỡ ngay: `FIND: Parameter format not
   correct` và `'/\' is not recognized as an internal or external command`. Cổng kiểm
   cho agent thì không được phụ thuộc vào shell nào đang chạy.)*

### Số liệu cố định của lần phát hành này

| Mục | Giá trị |
|---|---|
| Phiên bản mới | `3.0.24` |
| Phiên bản trước | `3.0.23` |
| Repo mã nguồn | `D:\Fsales_PCCC` |
| Repo phát hành | `D:\Fsales_update` (GitHub: `TungFireSmart/Fsales_update`) |
| File `.iss` | `D:\Fsales_PCCC\release\FsalesInstaller-3.0.24.iss` |
| Tên bộ cài sẽ ra | `Fsales-Setup-EXE-3.0.24.exe` |
| Thư mục bộ cài ra | `D:\Fsales_update\updates\3.0.24\` |
| `AppId` (⛔ không bao giờ đổi) | `{B210A5E9-4E37-4D65-A91F-56F3B05B7E09}` |

### 🔴 Điều quan trọng nhất phải hiểu trước khi làm

Bản 3.0.24 vá **chính cái cơ chế tự cập nhật**. Máy nào đang chạy ≤ 3.0.23 sẽ tải bộ cài
3.0.24 về đủ và đúng, rồi **vẫn kẹt y hệt** — vì đoạn chạy bộ cài là code cũ nằm trong
`.exe` trên máy họ, không phải code mới.

⇒ Lần này **bắt buộc phát bằng link tải tay**. Runbook vẫn cập nhật `manifest.json`
(để lần sau so sánh đúng mốc), nhưng **không được nói với ai rằng máy sẽ tự cập nhật**.

---

## 0. COMMIT CÔNG VIỆC ĐANG TREO — LÀM TRƯỚC MỌI THỨ

> **Thêm 11/8/2026** sau khi OpenClaw dừng đúng ở cổng 1 lần chạy đầu.
> Anh Tùng đã duyệt: **gộp thành một commit duy nhất, rồi push**.

### 0.1 Vì sao có bước này

Repo `D:\Fsales_PCCC` **chưa commit gì từ 6/8/2026**. Commit gần nhất là
`2f67523 Fix bundled BOM catalog lookup`. Ở `HEAD` git vẫn track **11.175 file**
(gồm `.venv/` 10.901 file và `AI/` 16 file), trong khi vùng chờ chỉ còn **140 file**.

Nghĩa là: gỡ AI · dọn rác · gỡ `.venv` khỏi git · vá cờ "bận" 11/8 · vá updater
hôm nay — tất cả mới nằm trong thư mục làm việc, **chưa vào lịch sử git**. Một lệnh
`git reset --hard` là mất sạch. Không được build bản phát hành từ mã nguồn chưa có
trong lịch sử: hỏng thì không biết quay về đâu.

### 0.2 Chạy cổng kiểm — MỘT LỆNH DUY NHẤT

```bat
cd /d D:\Fsales_PCCC
.venv\Scripts\python.exe kiem_tra_truoc_commit.py
```

Script tự làm hết: đúng repo · đúng nhánh · commit gần nhất còn nguyên · có khoá git
sót không · `.gitignore` còn giữ được `main.spec` không · và quan trọng nhất —
`git add -A` sẽ kéo **chính xác** những file nào vào commit.

🚦 **CỔNG 0a — đọc DÒNG CUỐI CÙNG của output:**

| Dòng cuối | Làm gì |
|---|---|
| `✅ SAN SANG COMMIT` | Sang mục 0.3 |
| `❌ DUNG` | **DỪNG**. Script đã in rõ mục nào chưa đạt. Chép nguyên văn gửi anh Tùng |

Script cũng trả **mã thoát**: `0` = sẵn sàng, `1` = phải dừng.

**Ngoại lệ duy nhất được tự xử lý:** nếu script dừng vì `.git/index.lock` **và** nó in ra
dòng `Day la tan du cua tien trinh git chet do (0 byte, qua cu)`, thì làm theo mục 0.2b
rồi chạy lại script. Mọi lý do dừng khác ⇒ báo anh Tùng, không tự chữa.

### 0.2b Gỡ khoá git cũ còn sót (chỉ khi script bảo thế)

Ngày 11/8/2026 phát hiện `D:\Fsales_PCCC\.git\index.lock` — **file 0 byte, tạo lúc 09:10**,
tàn dư của một tiến trình git chết dở từ sáng. Còn file này thì **mọi lệnh `git add` /
`git commit` đều fail** với `fatal: Unable to create ... index.lock: File exists`.

Kiểm không còn tiến trình git nào đang chạy:

```bat
tasklist /FI "IMAGENAME eq git.exe"
```

🚦 **CỔNG 0a-bis — đủ CẢ BA mới được xoá:**

- `tasklist` báo `No tasks are running which match the specified criteria.`
- Script ở mục 0.2 đã xác nhận file **0 byte** và **cũ hơn 60 phút**.
- Anh Tùng xác nhận đã **đóng PyCharm** (repo có thư mục `.idea/`; PyCharm cũng chạy git).

```bat
del D:\Fsales_PCCC\.git\index.lock
.venv\Scripts\python.exe kiem_tra_truoc_commit.py
```

⛔ Thiếu bất kỳ điều kiện nào ⇒ **DỪNG**, báo anh Tùng. Xoá khoá lúc git đang ghi dở
là hỏng vùng chờ — mà vùng chờ đang giữ ~11.000 thao tác chưa commit.

### 0.3 Đọc kỹ danh sách file sắp commit

Ở mục `[5]` script in ra toàn bộ thao tác mà `git add -A` sẽ làm. Nhìn qua một lượt
trước khi commit.

🚦 **CỔNG 0b:**

- Mục `[5]` phải kết thúc bằng `✅ Khong keo vao file nao thuoc danh sach cam`.
- Danh sách chỉ gồm file mã nguồn, tài liệu `.md`, và `release/*.iss`. Khoảng **19 dòng**.
- **Không có dòng `remove` nào là ĐÚNG.** Khoảng 11.000 lệnh xoá `.venv/`, `AI/`,
  `__pycache__` **đã nằm sẵn trong vùng chờ** từ ngày 6/8 nên `git add -A` không phải
  làm gì thêm với chúng. Chúng vẫn sẽ vào commit.
- Thấy bất kỳ dòng `add` nào chạm `.venv/`, `dist/`, `.exe`, `.env`,
  `fsales_config.json` ⇒ script đã tự đánh ❌ ⇒ **DỪNG NGAY, KHÔNG COMMIT**.

⛔ Lý do sống còn: `fsales_config.json` và `.env` chứa **credential CSDL sản xuất**;
`dist/` + `release/*.exe` nặng ~600 MB sẽ làm phình vĩnh viễn lịch sử git — repo
`Fsales_update` đã từng phình lên 1,5 GB đúng vì lỗi này và phải chạy `git filter-repo`
để cứu.

### 0.4 Commit và push

```bat
cd /d D:\Fsales_PCCC
git add -A
git commit -F docs\thong-diep-commit.txt
git log -1 --format=%%H
git push origin main
```

Kiểm lại sau khi push (dùng Python cho chắc, không phụ thuộc shell):

```bat
.venv\Scripts\python.exe -c "import subprocess as s;r=lambda *a:s.run(['git',*a],capture_output=True,text=True).stdout;print('con lai chua commit:',len([x for x in r('status','--short').splitlines() if x.strip()]));print('so file duoc track :',len(r('ls-files').splitlines()));print('commit moi nhat    :',r('log','-1','--format=%h %s').strip())"
```

File `docs\thong-diep-commit.txt` **đã có sẵn trong repo**, không cần tạo. Nội dung
(tiếng Việt không dấu để tránh lệch mã trên `cmd.exe`):

```
Dua toan bo cong viec 6/8 - 11/8/2026 vao lich su git

Tu 6/8/2026 den nay chua commit lan nao. HEAD van track 11.175 file
(gom .venv/ 10.901 file va AI/ 16 file) trong khi index chi con 140.
Gop lam mot commit theo quyet dinh cua anh Tung ngay 11/8/2026.

Gom cac mach viec:
- Go toan bo AI tich hop trong app (AI/, openclaw_bridge_server.py,
  llm_client.py, greeting_service.py). Anna la agent ngoai, khong dung toi.
- Don rac: go .venv/ va __pycache__ khoi git, xoa _trash_*, Fonts/,
  FsalesIOS/, hop_dong_out/. Git 11.175 -> 140 file duoc track.
- Tach credential CSDL ra ngoai ma nguon (bon duong doc config trong misc.py).
- Va co "ban" khoa nhan vien khong nhan duoc co hoi moi (B1, B2, B7):
  refresh_user_busy chi dem lead chua co bao gia; bo han luat mot nhan vien
  mot co hoi.
- Va loi tu cap nhat: bo cai khong bao gio chay do dung DETACHED_PROCESS
  thay vi CREATE_NEW_CONSOLE (U15). Bump 3.0.24 + FsalesInstaller-3.0.24.iss.
- Sua .gitignore: chu thich cuoi dong lam hong dong !main.spec va _patch*.py.
- Them CLAUDE.md, VIEC-CAN-LAM.md, NHAT-KY-FSALES.md, kiem_tra_truoc_phat_hanh.py,
  chan_doan_check_busy.py va bo tai lieu trong docs/.
```

🚦 **CỔNG 0c — lệnh kiểm trên phải in ra:**

- `con lai chua commit: 0`
- `so file duoc track : 141` (khoảng 140, không được là 11.175)
- `commit moi nhat` là commit vừa tạo, **không phải** `2f67523`
- `git commit` đã báo con số thay đổi khoảng **11.000+ file**
- `git push` thành công, không có xung đột

⛔ **Cấm tuyệt đối ở bước này:** `git push --force` · `git reset --hard` ·
`git filter-repo` · `git rebase` · xoá hay sửa bất kỳ commit cũ nào. Chỉ được **thêm
một commit mới lên trên**. Push bị từ chối vì lệch với remote ⇒ **DỪNG**, báo anh Tùng,
đừng tự `pull --rebase` hay `force`.

---

## 1. Kiểm môi trường

```bat
cd /d D:\Fsales_PCCC
git status --short
git rev-parse --abbrev-ref HEAD
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -c "import PyInstaller, sys; print('PyInstaller', PyInstaller.__version__)"
where gh
gh auth status
```

Tìm trình biên dịch Inno Setup:

```bat
.venv\Scripts\python.exe -c "import os;c=[r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',r'C:\Program Files\Inno Setup 6\ISCC.exe'];f=[p for p in c if os.path.exists(p)];print('ISCC:',f[0] if f else 'KHONG TIM THAY')"
```

🚦 **CỔNG 1 — phải đúng tất cả:**

- `git status --short` **rỗng**. Nếu chưa rỗng thì **bước 0 chưa xong** — quay lại
  làm bước 0 cho đủ, đừng đi tiếp. Còn thay đổi lạ **ngoài** những gì bước 0 mô tả
  ⇒ **DỪNG**, báo anh Tùng, đừng tự commit hộ.
- Python và PyInstaller in ra số phiên bản, không lỗi.
- `gh auth status` báo đã đăng nhập và có quyền vào `TungFireSmart/Fsales_update`.
- Dòng `ISCC:` in ra một đường dẫn thật. In `KHONG TIM THAY` ⇒ Inno Setup chưa cài ⇒
  **DỪNG** và báo (bộ cài có sẵn tại `D:\Fsales_PCCC\tools\innosetup-6.7.1.exe`, nhưng
  **cài phần mềm là việc của anh Tùng**, không phải của agent).

Ghi nhớ đường dẫn `ISCC.exe` tìm được, các bước sau gọi là `<ISCC>`.

---

## 2. Kiểm tra trước phát hành (script có sẵn)

```bat
cd /d D:\Fsales_PCCC
.venv\Scripts\python.exe kiem_tra_truoc_phat_hanh.py
```

Script này tự kiểm: import mọi module · soi `self.X()` gọi hàm không tồn tại ·
đối chiếu `version.py` ↔ `.iss` ↔ `AppId` · kiểm kết nối CSDL · xác nhận các chốt
chặn cũ không bị dựng lại.

🚦 **CỔNG 2:** phải **xanh hết**. Bất kỳ dòng đỏ / nghiêm trọng nào ⇒ **DỪNG**, chép
nguyên văn, báo anh Tùng. **Tuyệt đối không sửa code cho script xanh lên.**

---

## 3. Xác nhận thủ công 4 con số

```bat
cd /d D:\Fsales_PCCC
.venv\Scripts\python.exe -c "from version import APP_VERSION as v;print('APP_VERSION        :',v);[print(l.rstrip()) for l in open('release/FsalesInstaller-'+v+'.iss',encoding='utf-8-sig') if l.startswith(('#define MyAppVersion','AppId','OutputDir','OutputBaseFilename'))]"
```

🚦 **CỔNG 3 — phải khớp chính xác:**

| Phải in ra | Giá trị đúng |
|---|---|
| `APP_VERSION` | `3.0.24` |
| `MyAppVersion` | `"3.0.24"` |
| `AppId` | `{{B210A5E9-4E37-4D65-A91F-56F3B05B7E09}` |
| `OutputDir` | `D:\Fsales_update\updates\3.0.24` |
| `OutputBaseFilename` | `Fsales-Setup-EXE-3.0.24` |

⛔ `AppId` khác đi **một ký tự** cũng phải DỪNG. Đổi `AppId` là Windows coi đây là phần
mềm khác ⇒ cài thành bản thứ hai, bản cũ vẫn còn, shortcut cũ vẫn trỏ bản cũ. Đây đúng
là triệu chứng "cài xong vẫn chạy bản cũ" mà dự án đã mất nhiều tháng mới tìm ra.

---

## 4. Build `.exe`

```bat
cd /d D:\Fsales_PCCC
.venv\Scripts\pyinstaller.exe main.spec --noconfirm
```

Mất vài phút. Xong thì kiểm:

```bat
dir dist\Fsales\Fsales.exe
```

🚦 **CỔNG 4:**

- PyInstaller kết thúc với `Building EXE ... completed successfully`.
- `dist\Fsales\Fsales.exe` tồn tại và có **ngày giờ là hôm nay**.
- Trong log build **không có** dòng `ERROR:` nào. Dòng `WARNING:` thì bỏ qua được.

---

## 5. 🔴 Mở app thử — CỔNG NGƯỜI THẬT

```bat
start "" D:\Fsales_PCCC\dist\Fsales\Fsales.exe
```

🚦 **CỔNG 5 — đây là cổng DUY NHẤT agent không tự đóng được.**

Báo anh Tùng, chờ anh xác nhận **cả ba** rồi mới đi tiếp:

1. App mở lên được, hiện màn hình đăng nhập.
2. Đăng nhập được, vào tới màn hình chính.
3. Số phiên bản ở góc cửa sổ hiện đúng **`v3.0.24`**.

**Vì sao bắt buộc:** repo không có test tự động, và chạy từ mã nguồn ≠ chạy từ `.exe`
đóng gói — PyInstaller có thể thiếu hidden import mà lúc chạy mã nguồn không lộ ra.
Ở bước này mọi thứ mới chỉ nằm trên máy anh Tùng, hỏng thì build lại là xong.
Qua bước 7 rồi mới phát hiện hỏng thì đã nằm trên GitHub.

⏸️ **Anh Tùng chưa xác nhận ⇒ đứng yên. Không đoán, không đi tiếp.**

Xác nhận xong thì đóng app trước khi sang bước 6.

---

## 6. Build bộ cài bằng Inno Setup

```bat
"<ISCC>" "D:\Fsales_PCCC\release\FsalesInstaller-3.0.24.iss"
dir D:\Fsales_update\updates\3.0.24\Fsales-Setup-EXE-3.0.24.exe
```

🚦 **CỔNG 6:**

- ISCC in `Successful compile`.
- File `D:\Fsales_update\updates\3.0.24\Fsales-Setup-EXE-3.0.24.exe` tồn tại.
- Kích thước **trong khoảng 40–90 MB**. Nhỏ hơn 40 MB là dấu hiệu build thiếu ⇒ **DỪNG**
  (để so: bản 3.0.23 nặng 57.148.406 byte).

---

## 7. Sinh manifest

```bat
cd /d D:\Fsales_update
python tao-manifest.py 3.0.24 --notes "- Sua loi tu cap nhat: bo cai khong bao gio chay do sai co Windows (DETACHED_PROCESS thay vi CREATE_NEW_CONSOLE) nen UAC khong hien va script cai dat treo vo hinh.\n- Vong cho app thoat dung ping thay timeout (timeout can console moi chay duoc).\n- Bo cai duoc xin quyen Administrator dung cach qua PowerShell Start-Process -Verb RunAs.\n- Hop thoai bao truoc khi cai duoc chuyen len truoc, app thoat han roi moi cai."
```

Script tự đọc file `.exe` nên `sha256` và `size` không thể sai. Nó ghi ra 2 chỗ:
`updates/3.0.24/manifest.json` (lưu trữ) và `updates/latest/manifest.json` (app đọc file này).

🚦 **CỔNG 7:**

- In ra 3 dòng `✅`.
- `version : 3.0.24`
- `url` kết thúc bằng `/v3.0.24/Fsales-Setup-EXE-3.0.24.exe`
- `size` khớp đúng số byte của file ở bước 6.

---

## 8. Đẩy lên GitHub

**Thứ tự bắt buộc: tạo release TRƯỚC, commit manifest SAU.**
Làm ngược lại thì có một khoảng thời gian `manifest.json` trỏ tới link 404 — máy nhân
viên nào mở app đúng lúc đó sẽ báo lỗi tải.

```bat
cd /d D:\Fsales_update

gh release create v3.0.24 ^
  "D:\Fsales_update\updates\3.0.24\Fsales-Setup-EXE-3.0.24.exe" ^
  --repo TungFireSmart/Fsales_update ^
  --title "FSales 3.0.24" ^
  --notes "Sua loi tu cap nhat: bo cai khong bao gio chay. Ban nay PHAI cai tay bang link tai, may dang chay <= 3.0.23 khong tu cap nhat len duoc."
```

Chờ upload xong (~57 MB), rồi kiểm link tải được thật:

```bat
D:\Fsales_PCCC\.venv\Scripts\python.exe -c "import urllib.request as u;q=u.Request('https://github.com/TungFireSmart/Fsales_update/releases/download/v3.0.24/Fsales-Setup-EXE-3.0.24.exe',headers={'User-Agent':'kiem-tra'});r=u.urlopen(q,timeout=30);print('HTTP        :',r.status);print('content-type:',r.headers.get('Content-Type'));print('so byte     :',r.headers.get('Content-Length'));r.close()"
```

🚦 **CỔNG 8a:**

- `HTTP` là `200`.
- `so byte` khớp đúng kích thước file ở bước 6.
- `content-type` **không phải** `text/html`. Là `text/html` nghĩa là link trả về một
  trang web chứ không phải file ⇒ **DỪNG**.

Xong mới commit manifest:

```bat
cd /d D:\Fsales_update
git add updates/3.0.24/manifest.json updates/latest/manifest.json updates/3.0.24/Fsales-Setup-EXE-3.0.24.exe.sha256
git status --short
git commit -m "Phat hanh 3.0.24 - sua loi bo cai khong bao gio chay"
git push origin main
```

🚦 **CỔNG 8b:**

- `git status --short` **không được liệt kê file `.exe` nào** (file `.exe.sha256` thì
  được — nó chỉ vài chục byte). Repo này có `.gitignore` chặn `*.exe` vì lịch sử git
  từng phình lên 1,5 GB do 16 bộ cài cũ. Thấy `.exe` trong danh sách ⇒ **DỪNG NGAY**,
  đừng commit, báo anh Tùng.
- `git push` thành công.
- Mở `https://raw.githubusercontent.com/TungFireSmart/Fsales_update/main/updates/latest/manifest.json`
  thấy `"version": "3.0.24"`. (GitHub raw có CDN, có thể chậm vài phút — đợi rồi thử lại,
  đừng push lại.)

---

## 9. Soạn thông báo — ⛔ SOẠN THÔI, KHÔNG GỬI

Ghi ra file `D:\Fsales_update\updates\3.0.24\thong-bao-nhan-vien.txt`, nội dung đúng như dưới,
rồi báo anh Tùng là đã sẵn sàng để anh tự gửi.

```
FSales có bản mới 3.0.24. Lần này mọi người phải cài tay giúp anh, app không tự cập nhật được.

1. Tải file này về:
   https://github.com/TungFireSmart/Fsales_update/releases/download/v3.0.24/Fsales-Setup-EXE-3.0.24.exe

2. ĐÓNG FSales trước khi cài.

3. Chuột phải vào file vừa tải -> "Run as administrator" -> bấm "Yes".

4. Cứ bấm Next tới hết. ĐỪNG ĐỔI thư mục cài mà nó gợi ý sẵn.

5. Mở FSales lên, nhìn góc cửa sổ phải thấy v3.0.24 là xong.

Ai vướng chỗ nào nhắn anh.
```

🚦 **CỔNG 9:**

- File đã ghi ra đúng đường dẫn trên.
- **Chưa gửi cho ai.** Agent không được nhắn tin, không được gửi email, không được
  đụng vào máy nhân viên. Việc gửi là của anh Tùng.

---

## 10. Báo cáo kết thúc

Gửi anh Tùng đúng bảng này, điền số thật:

```
PHÁT HÀNH 3.0.24 — XONG
  Bộ cài     : D:\Fsales_update\updates\3.0.24\Fsales-Setup-EXE-3.0.24.exe
  Kích thước : ......... byte
  sha256     : .........
  Release    : https://github.com/TungFireSmart/Fsales_update/releases/tag/v3.0.24
  Manifest   : đã push, latest = 3.0.24
  Thông báo  : đã soạn tại updates\3.0.24\thong-bao-nhan-vien.txt — CHỜ ANH GỬI
  Còn lại    : anh gửi link cho nhân viên, và thử cài trên 1 máy trước khi báo cả công ty
```

---

## BẢNG LỖI — GẶP THÌ TRA Ở ĐÂY

| Lỗi | Nghĩa là gì | Làm gì |
|---|---|---|
| `git status` có thay đổi chưa commit (bước 1) | Có ai đó đang sửa dở | **DỪNG**, báo anh Tùng. Đừng commit hộ |
| `kiem_tra_truoc_phat_hanh.py` báo đỏ | Đúng việc của nó | **DỪNG**, chép nguyên văn. ⛔ Không sửa code cho nó xanh |
| `AppId` lệch | Sẽ cài thành bản thứ hai song song | **DỪNG** ngay, đây là lỗi nặng nhất trong danh sách |
| PyInstaller `ModuleNotFoundError` lúc chạy `.exe` | Thiếu hidden import trong `main.spec` | **DỪNG**, báo tên module. Việc sửa `main.spec` là của anh Tùng |
| ISCC báo `Cannot open file` | Đường dẫn `MySourceDir` trong `.iss` không tồn tại | Kiểm `dist\Fsales\` có ở đó không. Chưa build ⇒ quay lại bước 4 |
| Bộ cài < 40 MB | Build thiếu file | **DỪNG**, đừng phát |
| `gh release create` báo tag đã tồn tại | Ai đó đã tạo v3.0.24 rồi | **DỪNG**. ⛔ Không xoá release cũ, không `--clobber` |
| `curl` trả `content-type: text/html` | Link trả về trang web chứ không phải file | **DỪNG**, chưa được commit manifest |
| `git status` thấy file `.exe` sắp commit | `.gitignore` bị hỏng | **DỪNG NGAY**. Repo từng phình 1,5 GB vì lỗi này |
| Manifest raw vẫn hiện `3.0.23` | CDN của GitHub đang cache | Đợi 5 phút thử lại. ⛔ Đừng push lại, đừng đổi URL |
| Lỗi không có trong bảng này | — | **DỪNG**, chép nguyên văn, báo anh Tùng |

---

## PHỤ LỤC — VÌ SAO RUNBOOK NÀY KHẮT KHE THẾ

Ba lần phát hành gần nhất (3.0.22 → 3.0.23) **không máy nào cập nhật được**, mà mãi đến
11/8/2026 mới phát hiện. Nguyên nhân là một cờ Windows đặt sai trong `auto_update.py`:
`DETACHED_PROCESS` (= không có console nào) bị dùng thay cho `CREATE_NEW_CONSOLE`
(= mở cửa sổ console). Hậu quả dây chuyền: `timeout` chết ⇒ vòng chờ 60 giây co còn vài
mili giây · hộp thoại UAC không lên ⇒ bộ cài không chạy · script rơi vào `pause` và treo
vĩnh viễn **không có cửa sổ nào để thấy**.

Lỗi đó tồn tại được lâu như vậy vì **nó thất bại trong im lặng** và vì việc "đã hiện cửa
sổ console" từng bị đánh dấu ✅ dựa trên việc đọc code, chứ chưa ai nhìn thấy cửa sổ nào
hiện ra thật.

Cho nên: **cổng nào bảo dừng thì dừng**, và **cổng 5 phải có người thật xác nhận**.
Một lần phát hành hỏng ở đây là cả công ty kẹt thêm một chu kỳ nữa.
