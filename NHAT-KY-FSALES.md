# NHẬT KÝ DỰ ÁN — Fsales PCCC

> **Append-only.** Mỗi mục ≤ 3 dòng: *đã làm gì · vì sao · file nào đụng tới*.
> Mục quá 12 tháng → cắt sang `docs/luu-tru/nhat-ky-<năm>.md`.
> Trạng thái việc nằm ở `VIEC-CAN-LAM.md`, **không chép sang đây**.

---

## 2026

### 11/8/2026 — Bộ cài không bao giờ chạy: sai một cờ Windows (U15, U16)

- Anh Tùng bấm OK ở hộp thoại cập nhật rồi không thấy gì. Đo `%TEMP%\fsales-update\`:
  bộ cài tải hoàn hảo (sha256 khớp manifest), **không có `install.log`**, `capnhat.bat`
  còn nguyên ⇒ bộ cài **chưa từng chạy**, `.bat` chết giữa chừng.
- Gốc: `.bat` chạy bằng `DETACHED_PROCESS` (= không console) thay vì `CREATE_NEW_CONSOLE`
  ⇒ `timeout` chết, UAC không lên, `pause` treo vô hình. Kèm `main.py` gọi
  `launch_installer()` trước hộp thoại. Đụng `auto_update.py`, `main.py`, `version.py` → 3.0.24.
- ⚠️ Bản vá nằm trong chính updater hỏng ⇒ **3.0.24 phải phát bằng link tải tay** (`U16`).

### 11/8/2026 — Vá cờ "bận" khoá nhân viên không nhận được cơ hội mới (B1–B3)

- Nga báo không nhận được lead. Đo ra **316 lead bị tính là bận, 308 đã có báo giá**, cũ nhất
  398 ngày: `refresh_user_busy()` không loại lead đã báo giá, còn `main.py` thì tự đẩy lead
  quá 3/10 ngày sang hai trạng thái tính-là-bận không có đường thoát ⇒ khoá vĩnh viễn.
- Sửa **logic thay vì dữ liệu**: thêm `NOT EXISTS ds_bao_gia` (Nga 316 → 8), chuyển lệnh
  tính cờ xuống cuối hàm normalize, và cho `nhan_viec()` tính cờ sống thay vì đọc cache.
  Đụng `misc.py`, `main.py`; thêm `chan_doan_check_busy.py` (chỉ đọc).
- ⚠️ **Chưa có tác dụng cho tới khi phát hành bản mới** (`B4`) — cờ do app từng máy ghi.

### 11/8/2026 — Bỏ hẳn luật "một nhân viên một cơ hội" (B7)

- Anh Tùng quyết bỏ tận gốc thay vì chỉ vá cách đếm: gỡ chốt chặn trong
  `main.py.nhan_viec()`, không ai bị chặn nhận cơ hội mới nữa. `B3` bị thay thế.
- `check_busy` **vẫn tính và ghi**, nhưng chỉ còn để ưu tiên khi chia việc tự động
  (`misc.pick_auto_assign_user` — ưu tiên chứ không chặn, hết người rảnh vẫn giao).
- Đã cắm chú thích chống dựng lại ở `nhan_viec()` và `misc.is_user_busy()`.
  Đụng `main.py`, `misc.py`, `chan_doan_check_busy.py`.

### 11/8/2026 — Dọn nốt tắc nghẽn để phát hành 3.0.23 (B6, B9)

- `B6`: viết `nhan_viec_by_id()` (trước đây nút gọi hàm **chưa từng tồn tại** ⇒ `AttributeError`),
  xoá `nhan_viec(result)`. Lỗi nặng hơn đi kèm: 3 nút chọn lead qua `currentRow()`, mà bấm nút
  trong ô bảng không đổi dòng đang chọn ⇒ **nhận nhầm cơ hội người khác, im lặng**. Nay truyền
  thẳng `lead_id`. Đụng `main.py`.
- `B9`: thêm `kiem_tra_truoc_phat_hanh.py` + một dòng đầu checklist trong
  `docs/HUONG-DAN-PHAT-HANH.md`. Repo không có test nào, đây là lớp chắn rẻ tiền đầu tiên.
- Bump `version.py` → **3.0.23**, tạo `release/FsalesInstaller-3.0.23.iss` (AppId giữ nguyên).

### 11/8/2026 — Tắt màn hình "Cơ hội mới" (B10)

- Kiểm lại giả định "lead đã gán phụ trách thì người khác không thấy": **sai**.
  `show_co_hoi_moi()` query `WHERE status='Mới'` không lọc `phu_trach`, lại gắn nút
  "Nhận việc" lên mọi dòng cho mọi người ⇒ ai cũng cướp được lead đã giao.
- Anh Tùng quyết bỏ chức năng. Tắt tập trung qua `_tat_nut_co_hoi_moi()` vì nút được
  bật lại ở 4 chỗ; gỡ khỏi `_set_main_loading_lock`, bỏ `clicked.connect`, bỏ luôn luật
  ẩn theo tên `{'Vương','Huệ','Đức'}` nay đã thừa. `B8` khép lại theo. Đụng `main.py`.

### 11/8/2026 — Anh Tùng chạy thử app thật, không lỗi

- Đã mở app từ mã nguồn sau toàn bộ đợt sửa B1–B12: đăng nhập, màn hình chính, không lỗi.
  Gỡ được điểm mù "mọi thứ mới kiểm tới mức `ast.parse`" của đợt này.
- ⚠️ Vẫn còn hai lớp chưa phủ: bản `.exe` đóng gói (PyInstaller có thể thiếu hidden import
  mà chạy mã nguồn không lộ) và luồng cập nhật trên máy nhân viên — việc `B13`.

### 6/8/2026 — Revoke key OpenAI; chốt GIỮ mật khẩu MySQL (S1, S2, S3)

- Anh Tùng revoke key OpenAI ⇒ key còn trong lịch sử git đã vô hại. Không cần chạy
  `git filter-repo` cho `Fsales_PCCC`.
- **Anh Tùng chốt: giữ nguyên mật khẩu MySQL, không đổi**, đánh giá rủi ro chấp nhận được.
  Nên `misc.py` giữ `DB_MAC_DINH` để app chạy ngay, không phải phát kèm file config.
- Vẫn dựng đủ 4 đường ghi đè (biến môi trường → file cạnh exe → `_internal/` → `%APPDATA%`),
  đã test cả trường hợp file config hỏng thì rơi về mặc định chứ không làm app chết.
  Khi nào cần siết lại thì chỉ việc **xoá `DB_MAC_DINH`** (`S11`).
- 🔴 Còn treo: **chưa xác minh repo `Fsales_PCCC` là public hay private** (`S6`). Đây là yếu tố
  quyết định mức rủi ro của quyết định trên — public thì ai cũng đọc được mật khẩu CSDL sản xuất.

### 6/8/2026 — Viết lại lịch sử git của repo Fsales_update

- `git filter-repo` 2 đợt: xoá 14 bản cũ nhất (1,5 GB → 325 MB), rồi xoá nốt 3.0.14 + 3.0.20
  (325 MB → **202 MB**). Git giờ **không còn file `.exe` nào** — bộ cài đi qua GitHub Releases.
  15 `manifest.json` và các `.sha256` vẫn còn nguyên để tra cứu lịch sử phát hành.
- Đợt 2 có chuyển tạm 2 file `.exe` ra ngoài rồi trả về sau khi rewrite, nên chúng **vẫn còn
  trên đĩa** — `filter-repo` xoá khỏi lịch sử là xoá luôn khỏi thư mục làm việc (đợt 1 đã mất
  14 file `.exe` cũ trên đĩa vì chưa biết điều này).
- Trước khi chạy phải dọn 15 file bị báo "modified" — kiểm ra chỉ là **khác ký tự xuống dòng**
  (`git diff --ignore-all-space` trống), không mất nội dung nào.
- ⚠️ Lịch sử mới **chưa force-push**. Chừng nào chưa push thì bản gốc trên GitHub vẫn là đường lui.
  Hướng dẫn + cảnh báo ở `D:\Fsales_update\DA-DON-LICH-SU-GIT.md` (`U14`).

### 6/8/2026 — Xác nhận đợt vá: app chạy OK và nhanh hơn hẳn

- Anh Tùng chạy thử bản đã vá: hoạt động bình thường, **nhanh hơn nhiều** ⇒ chẩn đoán
  "mở kết nối MySQL mới cho từng câu lệnh" là đúng nguyên nhân chính (`L2`, `P3`).
- `installer_url` tải về đúng file `.exe` thật (`U6`) ⇒ loại trừ giả thuyết link trả về HTML.
- Anh Tùng chuyển phát hành sang **GitHub Releases**. Thêm `.gitignore` (`*.exe`) cho repo
  `Fsales_update` để không đẩy bộ cài vào git nữa; `tao-manifest.py` mặc định sinh URL Releases.
  ⚠️ 16 file `.exe` cũ vẫn nằm trong lịch sử commit, `.git` còn 1,5 GB (`U13`).

### 6/8/2026 — Dọn rác repo

- Xoá: 27 file `_patch*.py`/`_bom_*.py` rỗng 0–1 byte · 5 file `*.bak` · `_trash_20260322_1151/` ·
  `backups/` · `build/` (273 MB) · `Threads/` (chỉ còn `.pyc` mồ côi, không còn `.py`) ·
  mọi `__pycache__` · file Excel/PDF lạc chỗ ở root · `UI.gui.py` (stub 272 byte do gõ nhầm `pyuic6`).
- **Git track: 11.175 → 193 file** — `.venv/` (10.901 file) bị track từ trước khi có `.gitignore`,
  nay `git rm --cached`. Bổ sung `.gitignore` + ngoại lệ `!main.spec`.
- Kiểm sau khi dọn: 47/47 file `.py` parse OK, mọi module được import đều còn, 13/13 mục
  `datas` trong `main.spec` còn đủ file. **Chưa mở app chạy thật** (`L2`).
- Đợt 2 (anh Tùng chọn): xoá `Fonts/` 13 MB (0 tham chiếu), `hop_dong_out/` (app tự `mkdir` lại),
  `FsalesIOS/` **kèm `.github/workflows/ios-build.yml`** — giữ workflow mà xoá project thì CI báo đỏ
  mỗi lần push. Git track còn **140 file**.
- Không đụng: `login.txt`, `token_drive.pickle`, `google_drive_credential.json` (dữ liệu chạy thật
  của app), `dist/`, `release/*.iss`.

### 6/8/2026 — Phát hành 3.0.22 + truy tiếp lỗi "cài xong vẫn chạy bản cũ"

- Đối chiếu 15 file `.iss`: **`AppId` chưa từng bị đổi** ⇒ loại trừ giả thuyết đó (`U4`).
- Phát hiện rủi ro trong chính code em viết hôm trước: truyền `/DIR="thư mục đang chạy"` sẽ cài bản mới
  vào **bản sao lạc** nếu người dùng lỡ mở nó (bản 3.0.10 từng phải sửa đúng chuyện này —
  shortcut `Fsales_2024`, `Fire_Smart`). Đổi sang đọc `InstallLocation` từ Registry theo `AppId`,
  và mở lại exe **trong thư mục vừa cài** chứ không phải `sys.executable`.
- Bỏ `CREATE_NO_WINDOW`: `.iss` để `PrivilegesRequired=admin` nên Windows luôn hỏi UAC; ẩn cửa sổ đi
  thì người dùng bấm "No" mà không biết, và thất bại trong im lặng.
- Sinh manifest 3.0.22 bằng `D:\Fsales_update\tao-manifest.py` (mới) — sha256 + size đọc thẳng từ file,
  đã đối chiếu khớp: `dd61021e…`, 60.456.669 byte.

### 6/8/2026 — Sửa 2 lỗi sau khi xoá nút "Chat với Anna"

- Anh Tùng xoá `but_chat` khỏi `gui.ui`/`gui.py` ⇒ `main.py` còn dòng `self.uic.but_chat.hide()`
  nên `MainWindow.__init__` ném `AttributeError`. Đã bỏ hẳn dòng đó.
- Kéo theo `RuntimeError: wrapped C/C++ object ... LoginWorkerSignals has been deleted`:
  `__init__` chết giữa chừng nên Qt huỷ signals trong khi luồng đăng nhập vẫn chạy. Hai nguyên nhân:
  (a) `worker` là biến cục bộ nên Python thu hồi nó cùng `signals` khi luồng còn chạy — nay giữ
  tham chiếu ở `main._login_worker`; (b) `emit` không được bọc, và nằm trong `try` nên lỗi
  nhân đôi sang `error.emit`. Nay bọc bằng `_phat()`, nuốt `RuntimeError`.
- Tiện thể đổi `SELECT *` + `result[3]` thành `SELECT power` + `result[0]` trong `login_worker.py`.

### 6/8/2026 — Tăng tốc: thêm connection pool cho MySQL

- `misc.py` trước đây mở **một kết nối MySQL mới cho từng câu lệnh** — toàn app 385 lượt gọi SQL
  ⇒ 385 lần bắt tay TCP + xác thực qua Internet. Đây là nguyên nhân chính khiến app chậm.
- Thay bằng `MySQLConnectionPool` (5 kết nối, `pool_reset_session`), có `ping(reconnect)` chống
  kết nối chết, và **đường lui** về kết nối trực tiếp nếu pool hỏng. Chữ ký 3 helper giữ nguyên.
- Thêm phân loại lỗi: chỉ retry lỗi **kết nối**. Trước đây SQL sai cú pháp cũng bị chạy lại 3 lần
  = đơ giao diện ~10 giây rồi mới báo lỗi; nay trả về ngay.

### 6/8/2026 — Sửa lỗi tự cập nhật (phải cài tay / cài xong vẫn bản cũ)

- Tìm ra 5 lỗi trong `auto_update.py`: chạy bộ cài khi app còn sống (file bị khoá) · không truyền
  `/DIR` nên cài thành bản thứ hai · không có `/SILENT` nên bắt bấm Next · tải 70 MB đồng bộ trên
  luồng UI · không kiểm tra tính toàn vẹn file tải.
- Viết lại: tải theo khối ở luồng nền có thanh tiến trình, kiểm `sha256` + `size`, sinh `capnhat.bat`
  chờ PID app thoát hẳn rồi mới cài `/SILENT /DIR="thư mục đang chạy"`, xong tự mở lại app.
- Thêm `version.py` làm nguồn số phiên bản duy nhất; `docs/HUONG-DAN-PHAT-HANH.md` ghi rõ 5 bước
  phát hành và cảnh báo **không được đổi `AppId`** trong Inno Setup.

### 6/8/2026 — Gỡ toàn bộ AI agent khỏi phần mềm

- Quyết định của anh Tùng: bỏ AI tích hợp trong app, chỉ dùng phần nghiệp vụ.
  `git rm`: `AI/` (14 file), `openclaw_bridge_server.py`, `llm_client.py`, `greeting_service.py`,
  `win_ai_manager_chat.py`, `ui_ai_manager_chat.ui`, `.env`, `fsales_chat_history.json`.
- `main.py`: bỏ import `AIChatWindow` + `generate_greeting`, xoá `open_ai_chat()`, ẩn nút `but_chat`.
  `generate_greeting()` thành hàm cục bộ chọn ngẫu nhiên từ `LOI_CHAO` — chính là danh sách `FALLBACK`
  vốn có trong `greeting_service.py`, nên hành vi không đổi khi LLM trước đây lỗi.
- **Giữ lại** logic lead của "Anna" (`main.py`) và nhập báo giá NCC từ Drive (`crm.py`) —
  đó là nghiệp vụ thật, không phải AI chat.

### 6/8/2026 — Lập bộ quy tắc làm việc cho dự án

- Dựng `CLAUDE.md` (router theo loại việc), `VIEC-CAN-LAM.md` (sổ việc duy nhất), file này.
  Vì repo đã 30+ module, có file 134 KB, không có router thì mỗi phiên đều đốt token đọc lại từ đầu.
- Nguồn: khảo sát repo + đối chiếu bộ quy tắc `D:\TrainBot`, **lược bỏ** phần vault/`.backup`/`_RAC-CHO-XOA`
  vì Fsales có git còn TrainBot thì không.

### 6/8/2026 — Phát hiện credential bị track trong git

- `git ls-files` xác nhận `.env`, `AI/ai_config.py` (OpenAI key plaintext), `misc.py` (password MySQL
  production), và cả `.venv/` (~16.000 file) đang bị git track, repo có remote GitHub.
- Đã `git rm` hai file đầu trong đợt gỡ AI, **nhưng key/password vẫn nằm trong lịch sử commit**
  và trong các bản `.exe` đã phát. Phải revoke key + đổi mật khẩu — `VIEC-CAN-LAM.md` nhóm `S#`.

### 6/8/2026 — Chốt hướng dài hạn: chuyển dần sang web

- Quyết định của anh Tùng. Hệ quả: mọi thiết kế mới phải tách tầng nghiệp vụ khỏi PyQt (`W1`),
  client không giữ credential DB (`W2`).
- Không viết lại app ngay; làm dần theo module.
