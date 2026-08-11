# VIỆC CẦN LÀM — Fsales PCCC

> Sổ việc **DUY NHẤT** của dự án. Lập ngày 6/8/2026.

## ⚙️ QUY TẮC DÙNG FILE NÀY (Claude đọc trước khi ghi)

1. **Đầu mỗi phiên: đọc file này** trước khi đề xuất việc mới.
2. **Làm xong một việc ⇒ sửa file này NGAY** — đổi `Trạng thái` sang `✅`, ghi ngày + commit hash vào `Ghi chú`.
   **Không xoá dòng** (để lần sau khỏi đề xuất lại); dòng ✅ quá 60 ngày thì chuyển xuống mục **9. Lưu trữ**.
3. **Phát sinh việc mới ⇒ thêm dòng ngay**, `ID` = số kế tiếp trong nhóm. Chống trùng trước khi thêm.
4. **Không lặp lại nội dung file gốc** — mỗi dòng 1 câu + đường dẫn tới file chi tiết.
5. **Ký hiệu:** `⏳` chờ · `🔄` đang làm · `✅` xong · `⛔` chặn (thiếu dữ kiện / chờ anh Tùng) · `❌` bác bỏ.
6. **Tiền tố ID:** `S#` bảo mật · `T#` việc anh Tùng phải tự làm · `Q#` cần quyết định · `L#` làm được ngay ·
   `W#` chuẩn bị lên web · `D#` dọn dẹp.

---

## 1. 🔴 BẢO MẬT — làm trước mọi thứ khác

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| S1 | **Revoke key OpenAI** cũ | ✅ | 6/8/2026 — anh Tùng đã làm. Key cũ trong lịch sử git giờ vô hại |
| S2 | ~~Đổi mật khẩu MySQL~~ | ❌ | **Anh Tùng chốt 6/8/2026: giữ mật khẩu cũ, không đổi.** Đánh giá rủi ro chấp nhận được với repo hiện tại |
| S3 | Tách credential MySQL ra ngoài mã nguồn | ⚠️ | 6/8/2026 — **cơ chế đã có** (biến môi trường → `fsales_config.json` cạnh exe → `_internal/` → `%APPDATA%\FSales\`) nhưng **vẫn giữ mật khẩu mặc định trong `misc.py`** theo quyết định của anh Tùng. App chạy được ngay, không cần file config. Muốn bỏ mặc định thì chỉ cần xoá `DB_MAC_DINH` |
| S6 | 🔴 **Kiểm repo GitHub `Fsales_PCCC` là public hay private** | ⏳ | Đây là câu hỏi quyết định mức rủi ro của `S2`/`S3`. **Public** ⇒ bất kỳ ai cũng đọc được mật khẩu và kết nối thẳng vào CSDL sản xuất (lead, báo giá, đơn hàng, thông tin khách hàng). **Private** ⇒ rủi ro thấp, quyết định giữ mật khẩu là hợp lý |
| S11 | Đổi mật khẩu + bỏ mặc định khi có người nghỉ việc hoặc repo chuyển public | ⏳ | Ghi sẵn để lần sau không phải nghĩ lại. Cơ chế đọc config đã dựng xong, chỉ việc xoá `DB_MAC_DINH` trong `misc.py` |
| S4 | `git rm --cached .venv/` (~16.000 file bị track) | ⏳ | Độc lập, làm lúc nào cũng được |
| S5 | Dọn lịch sử git (`git filter-repo`) xoá key + password khỏi 30 commit | ⏳ | Chặn bởi S1, S2. Phải báo trước cho ai đang clone repo |
| S6 | Kiểm repo GitHub đang **public hay private** | ⏳ | Nếu public thì S1/S2 là khẩn cấp trong ngày |
| S7 | Thêm `.env` vào `.gitignore` để không lỡ commit lại | ✅ | 6/8/2026 |

## 2. 🧹 SAU KHI GỠ AI (6/8/2026)

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| L1 | Gỡ `AI/`, `openclaw_bridge_server.py`, `llm_client.py`, `greeting_service.py`, `win_ai_manager_chat.py`, `ui_ai_manager_chat.ui`, `.env`, `fsales_chat_history.json` | ✅ | 6/8/2026 — `git rm`, lịch sử vẫn lấy lại được |
| L2 | **Mở app chạy thử thật** sau khi gỡ AI + vá tốc độ | ✅ | 6/8/2026 — anh Tùng xác nhận chạy OK, và **nhanh hơn nhiều** |
| D6 | Xoá hẳn nút `but_chat` khỏi `UI/gui.ui` + `UI/gui.py` | ✅ | 6/8/2026 — anh Tùng tự xoá. `main.py` đã bỏ dòng `.hide()` tương ứng |
| D8 | Xoá nốt nút `but_chat` ("Chat AI") còn sót trong `UI/report.ui` + `UI/report.py` | ⏳ | Nút này **không nối vào hàm nào**, nên hiện không gây lỗi — chỉ là nút chết trên màn hình báo cáo |
| L3 | Bỏ đường dẫn cứng `C:\Users\Admin\.openclaw\workspace\fsales_connector\cli.py` trong `crm.py` | ⏳ | Nghiệp vụ nhập báo giá NCC từ Drive — **giữ chức năng**, chỉ bỏ phụ thuộc vào workspace OpenClaw. Hiện chỉ chạy được trên máy anh Tùng |
| L4 | Bỏ `main.spec` các hidden import không còn cần (nếu có) | ⏳ | Kiểm sau khi build lại |

## 2b. ⚡ TỐC ĐỘ & ỔN ĐỊNH (đợt vá 6/8/2026)

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| P1 | Thêm connection pool vào `misc.py` | ✅ | 6/8/2026 — pool 5 kết nối, có ping chống kết nối chết, có đường lui về kết nối trực tiếp |
| P2 | Chỉ retry lỗi kết nối, không retry lỗi SQL | ✅ | 6/8/2026 — trước đây SQL sai cũng đơ 10 giây |
| P3 | **Đo lại tốc độ thật sau khi vá** | ⏳ | 🔴 Cần anh Tùng mở app bấm thử vài màn hình nặng (danh sách lead, tồn kho) và cho biết nhanh lên bao nhiêu |
| P4 | Gỡ N+1: `stock_handle.py` có **27 lượt SQL trong vòng lặp** | ⏳ | Chỗ chậm còn lại lớn nhất. ⚠️ Đụng tới kho �⇒ theo quy tắc **đo trước, mỗi lần một thay đổi** |
| P5 | Đẩy query nặng sang luồng nền | ⏳ | Cả app chỉ có `login_worker.py` chạy nền; 384 lượt còn lại chạy trên luồng UI nên DB chậm là đơ cửa sổ. Dùng khuôn `UpdateDownloadWorker` vừa viết |
| P6 | Gộp query trong `main.py:743` (vòng lặp gọi `sql_one` 2 lần/vòng) | ⏳ | Quét tác vụ trả hàng |

## 2c. 🐛 CỜ "BẬN" KHOÁ NHÂN VIÊN (phát hiện 11/8/2026)

Nhân viên báo không nhận được cơ hội mới, app hiện *"vẫn còn cơ hội cũ chưa xử lý"*.
Đo thực tế: **Hoàng Thị Thanh Nga có 316 lead bị đếm là bận, 308 trong đó đã có báo giá**,
lead cũ nhất 398 ngày. Nguyên nhân: `misc.refresh_user_busy()` không loại lead đã báo giá,
trong khi `main.py` tự đẩy lead quá 3 / 10 ngày sang `Cần cập nhật lại` / `Đã quá 10 ngày`
— hai trạng thái tính là bận và **không có đường thoát tự động**.

**Kết luận cuối (11/8/2026):** anh Tùng quyết **bỏ hẳn luật "một nhân viên một cơ hội"**
(`B7`) — tức là gỡ tận gốc thứ sinh ra cả nhóm lỗi này, không chỉ vá cách đếm.
`B1`/`B2` vẫn giữ vì cờ còn dùng cho việc chia lead tự động; `B3` bị `B7` thay thế.

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| B1 | `refresh_user_busy()` chỉ đếm lead **chưa có báo giá** | ✅ | 11/8/2026 — thêm `NOT EXISTS ds_bao_gia` vào `misc.py`. Nga 316 → 8. Không đụng một dòng dữ liệu nào |
| B2 | Chuyển `refresh_busy_for_all_users_with_open_leads()` xuống **cuối** `_normalize_and_refresh_lead_statuses` | ✅ | 11/8/2026 — trước đây chạy ở bước 1, tức trước khi bước 2/3 đổi status ⇒ cờ phản ánh trạng thái cũ, sai lệch kéo dài ≥1 chu kỳ (throttle 5 phút) |
| B3 | ~~`nhan_viec()` tính cờ sống thay vì đọc cache bảng `user`~~ | ❌ | 11/8/2026 — **bị B7 thay thế**: chốt chặn đã bỏ hẳn nên không còn chỗ nào đọc cờ để quyết định. Phần vá `TypeError` cũng biến mất theo |
| B4 | 🔴 **Phát hành bản mới cho toàn bộ nhân viên** | 🔄 | Code sẵn sàng: `version.py` = **3.0.23**, có `release/FsalesInstaller-3.0.23.iss` (AppId giữ nguyên). ✅ **11/8/2026 anh Tùng đã mở app chạy thật từ mã nguồn, không thấy lỗi** — gỡ được điểm mù "chưa ai chạy thử". Còn lại là việc tay: build → bộ cài → manifest, theo `docs/HUONG-DAN-PHAT-HANH.md`. Máy chạy `.exe` cũ **vẫn còn chốt chặn** trong bản build của nó |
| B13 | Thử cập nhật trên **một máy nhân viên** trước khi báo cả công ty | ⏳ | Bước cuối trong checklist phát hành. Chạy từ mã nguồn ≠ chạy từ `.exe` đóng gói: PyInstaller có thể thiếu hidden import mà lúc chạy mã nguồn không lộ ra. Nên chọn máy của Nga — vừa là người bị kẹt, vừa kiểm được đúng luồng vừa sửa |
| B5 | Dọn lead tồn đọng đã nhận nhưng chưa báo giá | ⏳ | Hạ ưu tiên sau B7: không còn chặn ai nữa nên **không gấp**, chỉ là vệ sinh dữ liệu. Chạy `chan_doan_check_busy.py` để lấy danh sách. Nga có 8: #3794, #5435, #5616, #5748, #6099, #6117, #6355, #6797 |
| B6 | `main.py:582` gọi `self.nhan_viec_by_id(lid)` — **hàm này không tồn tại** | ✅ | 11/8/2026 — viết `nhan_viec_by_id(lead_id)` làm đường duy nhất, xoá `nhan_viec(result)`. Đồng thời sửa lỗi nặng hơn: 3 nút cũ chọn lead qua `currentRow()`, mà bấm nút trong ô bảng **không đổi dòng đang chọn** ⇒ có thể nhận nhầm cơ hội của người khác (hoặc `-1` = dòng cuối) mà không báo lỗi. Nay mọi nút truyền thẳng `lead_id` |
| B8 | ~~Hai người bấm "Nhận việc" cùng lúc trên một lead~~ | ✅ | 11/8/2026 — **hết đường xảy ra** sau `B10`: màn hình duy nhất cho phép người ngoài nhận lead đã bị tắt. Màn hình còn lại (`show_lead_with_status`) vốn đã kiểm `self.user == phu_trach or power > 40`. Nếu sau này mở lại hồ chung thì phải xử lại việc này |
| B10 | **Tắt nút "Cơ hội MỚI"** | ✅ | 11/8/2026 — anh Tùng quyết bỏ chức năng. `show_co_hoi_moi()` query `WHERE status='Mới'` **không lọc `phu_trach`** rồi gắn nút "Nhận việc" lên mọi dòng cho mọi người, không kiểm quyền ⇒ ai cũng cướp được lead đã giao. Nút bị bật lại ở **4 chỗ** nên phải tắt tập trung qua `_tat_nut_co_hoi_moi()`; đã gỡ khỏi `_set_main_loading_lock` và bỏ `clicked.connect`. Giữ nút xám + tooltip thay vì ẩn, để nhân viên biết là chủ ý |
| B11 | Xoá hẳn `show_co_hoi_moi()` + nút trong `UI/gui.ui` | ⏳ | Sau khi `B10` chạy thực địa vài tuần mà không ai kêu. Nhớ sửa `UI/gui.ui` rồi `pyuic6 UI/gui.ui -o UI/gui.py`, **không sửa tay** `UI/gui.py` |
| B12 | Luật ẩn nút theo tên `{'Vương','Huệ','Đức'}` đã bị xoá cùng `B10` | ⏳ | Ghi lại để không ai tưởng bị mất: luật cũ chỉ ẩn nút "Cơ hội mới" với 3 người này. Giờ tắt cho tất cả nên luật thành thừa. Nếu ý định ban đầu là hạn chế 3 người này ở chỗ khác nữa thì cần anh Tùng xác nhận |
| B9 | Không có kiểm tra tự động trước khi phát hành | ✅ | 11/8/2026 — thêm `kiem_tra_truoc_phat_hanh.py`: import mọi module, soi `self.X()` gọi hàm không tồn tại, xác nhận B1/B7 đúng trạng thái, đối chiếu `version.py` ↔ `.iss` ↔ `AppId`, và in bảng so sánh luật cũ/mới cho từng nhân viên |
| B7 | **Bỏ hẳn luật "một nhân viên một cơ hội"** | ✅ | 11/8/2026 — anh Tùng quyết. Gỡ chốt chặn trong `main.py.nhan_viec()`. `check_busy` vẫn được tính nhưng chỉ còn để *ưu tiên* khi chia việc tự động (`misc.pick_auto_assign_user`), không chặn ai. Đã ghi chú chống dựng lại ở cả `nhan_viec()` và `misc.is_user_busy()` |

## 3. 🔄 TỰ CẬP NHẬT (sửa 6/8/2026)

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| U1 | Viết lại `auto_update.py`: cài im lặng, đúng thư mục, chờ app thoát, kiểm sha256 | ✅ | 6/8/2026 |
| U2 | Tách `version.py` làm nguồn phiên bản duy nhất | ✅ | 6/8/2026 |
| U3 | Viết `docs/HUONG-DAN-PHAT-HANH.md` | ✅ | 6/8/2026 |
| U4 | ~~Kiểm `AppId` có bị đổi giữa các bản không~~ | ✅ | 6/8/2026 — **KHÔNG đổi**. `{B210A5E9-4E37-4D65-A91F-56F3B05B7E09}` giống hệt qua cả 15 file `.iss` từ 3.0.2 → 3.0.22. Loại trừ giả thuyết này |
| U5 | Bổ sung `sha256` + `size` vào `manifest.json` | ✅ | 6/8/2026 — sinh bằng `D:\Fsales_update\tao-manifest.py`, đã đối chiếu khớp file thật |
| U8 | Cài vào **thư mục đã đăng ký trong Registry**, không phải thư mục đang chạy | ✅ | 6/8/2026 — đọc `InstallLocation` theo `AppId`. Sửa rủi ro cài bản mới vào bản sao lạc (`Fsales_2024`, `Fire_Smart` — xem ghi chú bản 3.0.10) |
| U9 | Hiện cửa sổ console khi cập nhật | ✅ | 6/8/2026 — `.iss` để `PrivilegesRequired=admin` nên Windows luôn hỏi UAC. Ẩn cửa sổ ⇒ người dùng bấm "No" mà không hiểu, thất bại trong im lặng |
| U6 | **Kiểm `installer_url` tải về có phải file .exe thật không** | ✅ | 6/8/2026 — anh Tùng xác nhận tải OK |
| U10 | Chuyển sang **GitHub Releases** | ✅ | 6/8/2026 — anh Tùng đã đổi `installer_url` sang `github.com/.../releases/download/v3.0.22/...`. Thêm `.gitignore` (`*.exe`) vào repo `Fsales_update` để không đẩy bộ cài vào git nữa; `tao-manifest.py` mặc định sinh URL Releases |
| U13 | Dọn **toàn bộ** `.exe` khỏi lịch sử repo `Fsales_update` | ✅ | 6/8/2026 — 2 đợt `git filter-repo`. **`.git` 1,5 GB → 202 MB**, còn **0 file `.exe`** trong git. 15 `manifest.json` + các `.sha256` vẫn đủ. 8 bộ cài từ 3.0.14→3.0.22 vẫn nguyên trên đĩa |
| U14 | **Force-push lịch sử mới lên GitHub** | ✅ | 6/8/2026 — `53f50be...84a4550 (forced update)`, đẩy 161 object / 21 KB. `local main == origin/main`. ⚠️ Ai còn bản clone cũ phải clone lại |
| U15 | 🔴 **Bộ cài KHÔNG BAO GIỜ chạy — bấm OK rồi không có gì xảy ra** | ✅ | 11/8/2026 — anh Tùng báo khi lên 3.0.23. **Đo trước:** `%TEMP%\fsales-update\` có `FsaleSetup.exe` 57.148.406 byte sha256 khớp manifest (tải hoàn hảo), **không có `install.log`** (Inno tạo log ngay khi khởi động ⇒ bộ cài chưa từng chạy), `capnhat.bat` **còn nguyên** (dòng cuối là lệnh tự xoá ⇒ chết giữa chừng), `D:\Fsales\Fsales.exe` vẫn ngày 6/8 = 3.0.22. **Ba lỗi:** ① `.bat` chạy bằng `DETACHED_PROCESS` = *không có console nào cả* (cờ hiện console là `CREATE_NEW_CONSOLE`) ⇒ UAC không lên, và khi thất bại `.bat` rơi vào `pause` treo vĩnh viễn **không cửa sổ nào để thấy** — chú thích trong code ghi "cố ý hiện console" nhưng cờ ngược lại; ② vòng chờ dùng `timeout` vốn cần console ⇒ 60 giây co còn vài ms ⇒ chạy bộ cài khi exe còn khoá; ③ `main.py` gọi `launch_installer()` **trước** hộp thoại. **Vá:** `CREATE_NEW_CONSOLE`, `ping` thay `timeout`, tách `chaycai.ps1` xin quyền bằng `Start-Process -Verb RunAs`, đảo thứ tự trong `main.py`. Đụng `auto_update.py`, `main.py` |
| U16 | 🔴 **Phát hành 3.0.24 phải gửi LINK TẢI TAY, không dùng tự cập nhật** | ⏳ | Bản vá nằm **bên trong chính updater bị hỏng** ⇒ máy ≤ 3.0.23 tải 3.0.24 về đủ nhưng vẫn kẹt y hệt, vì đoạn chạy bộ cài là code cũ trong `.exe` của họ. Xem mục **PHÁT HÀNH TRỰC TIẾP QUA LINK** trong `docs/HUONG-DAN-PHAT-HANH.md`. Từ 3.0.25 mới quay lại tự cập nhật được |
| U9b | Xem lại `U9` — "đã hiện cửa sổ console" là **kết luận sai** | ✅ | 11/8/2026 — 6/8 ghi ✅ dựa trên việc *bỏ* `CREATE_NO_WINDOW`, nhưng cờ thay vào là `DETACHED_PROCESS` nên thực tế **không có console nào**. Bài học: bỏ một cờ ≠ đặt đúng cờ ngược lại; và không được đánh ✅ cho thứ chưa nhìn thấy chạy thật |
| U11 | Sửa mã hoá file `.iss` (mục `[Tasks]` hiện `Táº¡o biá»ƒu tÆ°á»£ng`) | ⏳ | Lưu file `.iss` dạng **UTF-8 có BOM** thì Inno mới đọc đúng tiếng Việt |
| U12 | Cân nhắc `DisableDirPage=yes` trong `.iss` | ⏳ | Hiện `=no` nên khi cài tay nhân viên có thể chọn thư mục khác → sinh bản sao lạc |
| U7 | **Thử cập nhật trên 1 máy** trước khi phát cả công ty | ⏳ | 🔴 Bắt buộc |

## 4. 🌐 CHUẨN BỊ LÊN WEB (hướng dài hạn, chốt 6/8/2026)

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| W1 | Tách tầng nghiệp vụ khỏi PyQt: `*_handle.py` không được `import PyQt6` | ⏳ | Việc lớn, làm dần từng module. Bắt đầu từ `order_handle.py` |
| W2 | Client không giữ credential DB — chỉ giữ token phiên, mọi query đi qua API | ⏳ | Cách duy nhất chữa triệt để S1–S5 |
| W3 | Chọn stack web | ⛔ | Chờ anh Tùng |
| W4 | Liệt kê module bắt buộc chạy desktop (in Excel/Word, đọc file cục bộ) | ⏳ | Quyết định phạm vi bản web đầu tiên |

## 4. 🧹 DỌN DẸP

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| D1 | Xoá 27 file `_patch*.py`/`_bom_*.py`/`_gen_ui.py` rỗng | ✅ | 6/8/2026 |
| D2 | Xoá 5 file `*.bak` | ✅ | 6/8/2026 |
| D3 | Xoá `_trash_20260322_1151/`, `backups/`, `build/`, `Threads/`, mọi `__pycache__` | ✅ | 6/8/2026 |
| D9 | `git rm --cached .venv/` + `__pycache__` | ✅ | 6/8/2026 — git track **11.175 → 193 file** |
| D10 | Xoá `UI.gui.py` (stub 272 byte do gõ nhầm `pyuic6 UI.gui.ui`) | ✅ | 6/8/2026 — sinh ra hôm nay lúc 16:00 khi xoá nút chat |
| D11 | Bổ sung `.gitignore`: `backups/`, `*.bak`, `_patch*.py`, `*.zip`, `tools/`, và **ngoại lệ `!main.spec`** | ✅ | 6/8/2026 — `*.spec` bị ignore nhưng `main.spec` phải giữ |
| D12 | ⛔ **Quyết định nhóm file nặng còn lại** | ⛔ | Chờ anh Tùng. `dist/` 290 MB (nguồn cho Inno Setup) · `release/` 333 MB (giữ 16 file `.iss`, bỏ ~260 MB bộ cài cũ?) · `installer/FsaleSetup.exe` 67 MB (4/2025) · `tools/innosetup-6.7.1.exe` 11 MB |
| D13 | Xoá `hop_dong_out/` | ✅ | 6/8/2026 — `crm.py:1950` có `mkdir(parents=True, exist_ok=True)` nên app tự tạo lại khi xuất hợp đồng |
| D14 | Xoá `Fonts/` (13 MB) | ✅ | 6/8/2026 — xác minh 0 tham chiếu trong `.py`/`.spec`/`.qss`/`.iss` |
| D15 | Xoá `FsalesIOS/` **+ `.github/workflows/ios-build.yml`** | ✅ | 6/8/2026 — workflow chỉ build đúng dự án iOS đó (`paths: FsalesIOS/**`); giữ lại workflow mà xoá project thì mỗi lần push CI báo đỏ. Lịch sử git vẫn lấy lại được |
| D4 | ~~Đồng bộ file UI generate ở root với `UI/*.py`~~ | ❌ | Bác 6/8/2026 — kiểm thực tế thì root **không còn** file UI generate nào; `order_handle.py:24` đã import `UI.don_hang`. Việc này do `AI_AGENT_PROJECT_MAP.md` (13/3/2026) mô tả sai hiện trạng |
| D5 | Dời file Excel/PDF tạm ở root vào thư mục riêng | ⏳ | `bao_gia_affetti_2025-07-01.pdf` một mình đã 4,8 MB |
| D7 | Đổi tên 3 file `AI_AGENT_*.md` cho khỏi hiểu nhầm là dự án còn AI | ⏳ | Nội dung `AI_AGENT_RETURN_GOODS_SCOPE.md` vẫn dùng được (nghiệp vụ trả hàng) |

## 5. 📋 CẦN QUYẾT ĐỊNH (chờ anh Tùng)

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| Q1 | ~~Giữ OpenAI hay chuyển Claude?~~ | ❌ | Không còn liên quan — đã gỡ AI khỏi app 6/8/2026 |
| Q2 | Có ép nhân viên cập nhật `.exe` được không? | ⛔ | Quyết định việc đổi schema DB có an toàn hay không |
| Q3 | Repo GitHub public hay private? | ⛔ | Xem S6 |
| Q4 | **Anna còn đang chạy không?** Nếu đã dừng thì gỡ được logic thu hồi lead ở `main.py` | ⛔ | Xem CLAUDE.md → mục ANNA. Hiện **giữ nguyên** theo quyết định 6/8/2026 |

## 6. ✅ ĐÃ XONG

| ID | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| L0 | Dựng `CLAUDE.md` router + sổ việc + nhật ký | ✅ | 6/8/2026 |

## 9. 🗄️ LƯU TRỮ (dòng ✅ quá 60 ngày)

*(chưa có)*

---

## NHẬT KÝ SỬA FILE NÀY

- **6/8/2026** — lập file. Nguồn: khảo sát repo `D:\Fsales_PCCC` (30 commit, remote GitHub),
  đọc `misc.py`, `main.py`, `crm.py`, `AI_AGENT_*.md`; đối chiếu bộ quy tắc của `D:\TrainBot`.
- **6/8/2026** — cập nhật sau khi gỡ AI khỏi phần mềm: bỏ nhóm `A#` (module AI), thêm `L2`, `L3`, `D6`, `D7`, `Q4`.
