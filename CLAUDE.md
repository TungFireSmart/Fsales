# CLAUDE.md — Fsales PCCC

> **Ngày chốt: 6/8/2026.** File này là **BỘ ĐỊNH TUYẾN**, không phải sách giáo khoa.
> Đừng đọc cả repo trước mỗi việc — chỉ đọc đúng hàng tương ứng trong bảng **ĐỌC THEO LOẠI VIỆC**.
> Xong mỗi mạch việc: cập nhật `VIEC-CAN-LAM.md` + ghi 1 dòng vào `NHAT-KY-FSALES.md`.

---

## 🧭 ĐỊNH TUYẾN & PHẠM VI

**Đây là dự án `D:\Fsales_PCCC`** — phần mềm quản lý bán hàng nội bộ của công ty PCCC.vn.
App desktop **PyQt6 + MySQL**, đóng gói PyInstaller thành `.exe`, phát cho nhân viên qua `auto_update.py`.

⛔ **Nếu `D:\TrainBot` cũng được mount thì đó là DỰ ÁN KHÁC** (vault nội dung website pccc.vn/firesmart.vn).
Không lấy tri thức web/SEO sang đây, không lấy quy ước file của vault đó sang đây (xem mục **KHÁC BIỆT VỚI TRAINBOT**).

✅ **Trong phạm vi:** code app desktop · nghiệp vụ lead→báo giá→đơn hàng→kho→báo cáo ·
module tư vấn PCCC / BOM · module khảo sát công trình · nhà cung cấp · schema MySQL · đóng gói/phát hành.

⛔ **NGOÀI PHẠM VI — đã gỡ khỏi phần mềm ngày 6/8/2026:** mọi **AI agent tích hợp trong app**
(tab chat, planner sinh SQL, LLM sinh lời chào, cầu nối OpenClaw). Xem mục **AI ĐÃ GỠ** bên dưới.
Đừng dựng lại, đừng "khôi phục cho tiện" — nếu cần thì hỏi anh Tùng trước.

🎯 **Hướng dài hạn đã chốt (6/8/2026):** chuyển dần sang **web app**. Mọi thiết kế mới phải tách
**tầng nghiệp vụ khỏi tầng UI PyQt** để tái dùng được cho web sau này (`VIEC-CAN-LAM.md` → `W1`).

---

## 📖 ĐỌC THEO LOẠI VIỆC

| Loại việc | Đọc BẮT BUỘC (chỉ những file này) | Đọc thêm khi cần |
|---|---|---|
| **Sửa nghiệp vụ lead** | `lead_handle.py` → `UI/new_lead.py`, `UI/lead_update.py` | `main.py` (`show_lead`, `nhan_viec`) |
| **"Không nhận được cơ hội mới"** | `chan_doan_check_busy.py` (chỉ đọc, chạy trước) → `misc.refresh_user_busy()` → `main.py` (`nhan_viec`) | `VIEC-CAN-LAM.md` nhóm `B#` |
| **Lead do "Anna" tạo** | ① mục **ANNA** dưới → `main.py:352-400` | `sale_lead.nguoi_tao_lead`, `sale_lead.status` |
| **Sửa báo giá** | `quotation.py` → `quotation_save.py` → `UI/win_bao_gia.py` | `price_list_manager.py`, `bao_gia_mau*.xlsx` |
| **Sửa đơn hàng** | `order_handle.py` (import `Ui_Don_hang` từ `UI/don_hang.py`) → ① mục **BẤT BIẾN ĐƠN HÀNG** dưới | `UI/don_hang.py` (chỉ đọc, KHÔNG sửa) |
| **Sửa kho** | `stock_handle.py` → `stock_ui_utils.py` → `UI/nhap_xuat_kho.py` | `mau_phieu_xuat_kho*.xlsx` |
| **Trả lại hàng** | `AI_AGENT_RETURN_GOODS_SCOPE.md` → `order_handle.py` → `stock_handle.py` | `main.py` (`_parse_return_request_from_log`) |
| **Báo cáo / thống kê** | `baocao.py` → `UI/report.py` | `misc.py` (helper SQL) |
| **Tư vấn PCCC / BOM** | `tu_van_pccc.py` → `pccc_rules.py` → `bom_catalog.json` | `tu_van_pccc_excel.py`, `HUONG_DAN_NHAP_BANG_GIA_BOM.md` |
| **Khảo sát công trình** | `khao_sat_data.py` → `khao_sat_helpers.py` → `UI/khao_sat_form.py` | `create_table_khao_sat.sql`, `alter_table_khao_sat_v*.sql` |
| **Nhà cung cấp** | `crm.py` → `UI/supplier_detail.py`, `UI/supplier_product_editor.py` | bảng `fs_suppliers`, `fs_supplier_products` |
| **Nhập báo giá NCC từ Drive** | `crm.py` (`_import_one`) → ① mục **PHỤ THUỘC NGOÀI** dưới | — |
| **Đổi schema DB** | mục **QUY TẮC ĐỔI SCHEMA** dưới | các file `create_table_*.sql`, `alter_table_*.sql` |
| **Đóng gói / phát hành** | `docs/HUONG-DAN-PHAT-HANH.md` → `version.py` → `main.spec` → `auto_update.py` | `update_config.json`, `installer/` |
| **Tốc độ / app bị treo** | ① mục **TỐC ĐỘ** dưới → `misc.py` (pool + phân loại lỗi) | `VIEC-CAN-LAM.md` nhóm `P#` |
| **Việc chạm nhiều mảng** | đọc hàng của **từng mảng**, không đọc file của mảng khác | — |

**Quy tắc token:** không chắc thuộc loại nào → đọc file này + hỏi anh Tùng, đừng mở lần lượt cả repo.
⛔ **KHÔNG đọc `_trash_20260322_1151/`, `build/`, `dist/`, `.venv/`, `*.bak`** trừ khi anh Tùng hỏi thẳng về lịch sử.

---

## ⚡ THÔNG TIN CỐ ĐỊNH NHANH

| Mục | Giá trị |
|---|---|
| DB | MySQL `fs_mrb` @ `db.fs.rsa.vn:3118` — credential đọc từ `fsales_config.json` **ngoài repo**, không hardcode (xem BẢO MẬT) |
| Helper SQL | `misc.sql_all()` · `misc.sql_one()` · `misc.sql_commit()` — có retry 3 lần, timeout 3 giây |
| Entry point | `main.py` → `class MainWindow(QMainWindow)` |
| Quyền quản lý | `user.power >= 40` |
| Cờ "đã chốt" | `ds_bao_gia.thanh_cong = 'T'` · `ds_don_hang.da_hoan_thanh = 'T'` |
| Nguồn doanh số | **CHỈ** `ds_don_hang.tien_hang` — không bao giờ từ `ds_bao_gia` |
| Tuần ISO | `YEARWEEK(col, 1)` |
| Bảng đang dùng | `sale_lead`, `ds_bao_gia`, `ds_don_hang`, `ds_don_thue`, `ton_kho`, `nhap_kho`, `xuat_kho`, `gia_tong_hop`, `ds_cong_ty`, `ds_ca_nhan`, `user`, `lich_su_gd`, `fs_suppliers`, `fs_supplier_products`, `fs_supplier_files`, `fs_supplier_product_images`, `sale_lead_khao_sat`, `sale_lead_khoi_nha`, `sale_lead_khu_vuc`, `sale_lead_audit_log` |

---

## 🚫 AI ĐÃ GỠ (6/8/2026) — ĐỪNG DỰNG LẠI

Anh Tùng quyết định bỏ toàn bộ AI agent tích hợp trong phần mềm, chỉ dùng phần nghiệp vụ.
Đã `git rm` (lịch sử git vẫn lấy lại được bằng `git show <commit>:<file>`):

| Đã gỡ | Là gì |
|---|---|
| `AI/` (14 file) | chat window, planner sinh SQL, safe executor, memory, ontology, client OpenClaw |
| `openclaw_bridge_server.py` | FastAPI @ `127.0.0.1:8765` nối app với OpenClaw |
| `llm_client.py`, `greeting_service.py` | gọi LLM sinh câu chào ở `label_noti` |
| `win_ai_manager_chat.py`, `ui_ai_manager_chat.ui` | form chat cũ, không còn được dùng |
| `.env`, `fsales_chat_history.json` | key LLM + lịch sử hội thoại |

**Thay thế trong `main.py`:** `generate_greeting()` giờ là hàm cục bộ chọn ngẫu nhiên từ `LOI_CHAO`
— chính là danh sách `FALLBACK` vốn có sẵn trong `greeting_service.py`, nên hành vi không đổi.
Nút `but_chat` vẫn còn trong `UI/gui.ui` nên `main.py` **ẩn nó lúc chạy**; xoá hẳn là việc `D6`.

---

## ⚡ TỐC ĐỘ — ĐÃ CHẨN ĐOÁN 6/8/2026

Bốn nguyên nhân làm app chậm và hay treo. Hai cái đầu **đã sửa**:

| # | Nguyên nhân | Trạng thái |
|---|---|---|
| 1 | `misc.py` mở **kết nối MySQL mới cho từng câu lệnh** — 385 lượt gọi SQL = 385 lần bắt tay qua Internet | ✅ đã có pool (6/8/2026) |
| 2 | Retry **mọi loại lỗi** 3 lần → SQL sai cú pháp cũng đơ 10 giây | ✅ chỉ retry lỗi kết nối |
| 3 | **384/385 lượt SQL chạy trên luồng giao diện** → DB chậm là cả cửa sổ đóng băng | ⏳ `P5` |
| 4 | **N+1**: `stock_handle.py` có 27 lượt SQL nằm trong vòng lặp | ⏳ `P4` |

🔴 **Quy tắc mới:** viết code mới thì **không gọi SQL trong vòng lặp**. Gom lại thành một câu
`WHERE ... IN (...)` hoặc `JOIN`. Mỗi lượt gọi là một vòng đi–về tới `db.fs.rsa.vn`.

🔴 **Query nặng phải chạy ở luồng nền.** Khuôn có sẵn: `login_worker.py` và
`UpdateDownloadWorker` trong `auto_update.py` (`QRunnable` + `pyqtSignal` + `QThreadPool`).

---

## 🤖 ANNA — VẪN GIỮ, KHÔNG PHẢI AI TRONG APP

"Anna" là agent **bên ngoài** (OpenClaw), tự tạo lead vào DB. Nó **không nằm trong repo này**,
nên gỡ AI khỏi app không đụng gì tới nó. Nghiệp vụ liên quan **vẫn chạy và phải giữ**:

- `sale_lead.nguoi_tao_lead = 'Anna'` · `sale_lead.status = 'Anna đã giao việc'`
- `main.py` — chuẩn hoá trạng thái cũ *"Đã giao việc từ Anna"* về `'Đã nhận việc'`
- `main.py` — **tự thu hồi** lead Anna giao quá 1 giờ mà chưa có báo giá / đơn hàng

⚠️ Gỡ đoạn tự thu hồi này thì lead Anna giao sẽ **treo vĩnh viễn**, không ai nhận. Đừng đụng vào.

---

## 🔌 PHỤ THUỘC NGOÀI — DỄ GÃY

`crm.py` (`_import_one`, nhập báo giá NCC từ Google Drive) gọi bằng **đường dẫn tuyệt đối**:

```
py  = D:\Fsales_PCCC\.venv\Scripts\python.exe
cli = C:\Users\Admin\.openclaw\workspace\fsales_connector\cli.py
```

⚠️ Chỉ chạy được trên **máy anh Tùng**. Máy nhân viên bấm nút này là lỗi.
Đây là nghiệp vụ thật (không phải AI chat) nên **giữ**, nhưng cần tách ra khỏi workspace OpenClaw
và bỏ đường dẫn cứng — việc `L3`.

---

## 🔴 NGUYÊN TẮC KHÔNG ĐƯỢC VI PHẠM

- 🔴 **KHÔNG hardcode credential.** `misc.py` đang hardcode host/user/**password** MySQL production
  và bị git track → mật khẩu nằm trong lịch sử commit của repo có remote GitHub, đồng thời bị
  PyInstaller nhúng thẳng vào `.exe` phát cho nhân viên. Xem mục BẢO MẬT.
  *(Bài học 6/8/2026: `AI/ai_config.py` cũng để `OPENAI_API_KEY` plaintext ngay dưới dòng chú thích
  "⚠️ KHÔNG COMMIT FILE NÀY" — chú thích không thay được `.gitignore`.)*

- 🔴 **KHÔNG sửa logic nghiệp vụ trong file UI generate** (`UI/*.py` sinh từ `.ui`).
  Cần thêm control → sửa `UI/*.ui` rồi regenerate. Logic đặt ở `*_handle.py`.
  *(Bài học: file generate bị ghi đè mỗi lần chạy `pyuic6`, sửa tay là mất.)*

- 🔴 **NGUỒN SỰ THẬT UI là `UI/*.ui`** → generate ra `UI/*.py` → import vào `*_handle.py`.
  Xác minh 6/8/2026: `order_handle.py:24` đang import `from UI.don_hang import Ui_Don_hang` — **đúng chuẩn**.
  Ở root chỉ còn `hinhanh_rc.py` (resource Qt, được sinh ra, không sửa tay).

- 🔴 **ĐO TRƯỚC, LÀM SAU.** Không sửa vì "nguyên tắc chung nói vậy". Đụng tới tiền/kho thì
  phải đếm số dòng bị ảnh hưởng bằng `SELECT COUNT(*)` trước khi `UPDATE`.

- 🔴 **MỖI LẦN MỘT THAY ĐỔI** khi động vào trạng thái đơn hàng / tồn kho. Sửa hàng loạt rồi có chuyện
  thì không biết cái nào gây ra.

- 🔴 **KẾT QUẢ RỖNG PHẢI BỊ NGHI NGỜ.** Query trả 0 dòng đúng lúc mình đang mong nó rỗng là
  dấu hiệu nguy hiểm nhất — kiểm lại tên bảng/cột trước khi kết luận.

- 🔴 **Không đổi cột DB hiện có khi chưa có migration plan.** Có ≥3 phiên bản `.exe` cũ đang chạy
  ngoài thực địa (`auto_update.py` không ép cập nhật) — đổi cột là làm hỏng máy chưa update.

- 🔴 **Không bịa tên bảng/cột.** Không chắc thì
  `SELECT * FROM information_schema.columns WHERE table_schema = DATABASE()`.

- 🔴 **KHÔNG dựng lại luật "một nhân viên một cơ hội".** Bỏ ngày 11/8/2026 (việc `B7`).
  `main.py.nhan_viec()` **không được** chặn ai vì `user.check_busy`. Cờ đó nay chỉ dùng để
  *ưu tiên* trong `misc.pick_auto_assign_user()`. Muốn giới hạn khối lượng việc thì làm ở
  khâu **chia** việc, đừng chặn ở khâu **nhận** việc.

- 🔴 **Mọi trạng thái gán tự động phải có đường thoát.** Rule nào tự đổi `status` theo tuổi
  lead thì phải trả lời được: cái gì đưa nó ra khỏi trạng thái đó? Không có lối ra ⇒ dữ liệu
  tích tụ vô hạn và khoá người dùng.
  *(Bài học 11/8/2026: `'Đã quá 10 ngày'` không có lối ra, lại nằm trong danh sách "đang bận" ⇒
  Hoàng Thị Thanh Nga tích 316 lead trong 13 tháng và không nhận được cơ hội mới nào. 308/316
  lead đó **đã báo giá xong** — tức nhân viên đã làm hết việc mà vẫn bị tính là chưa xong.)*

- 🔴 **Đừng tin cờ cache trong DB ở điểm ra quyết định — tính lại tại chỗ.** Cột dẫn xuất
  (`user.check_busy`…) chỉ đúng tại thời điểm ghi. Ai cũng ghi được, và hàm ghi nó có throttle.
  *(Bài học 11/8/2026: `nhan_viec()` đọc `user.check_busy` nên chặn nhân viên theo số liệu cũ;
  hàm cập nhật cờ lại chạy TRƯỚC các lệnh đổi status trong cùng một lượt.)*

- 🔴 **Bỏ một cờ không có nghĩa là đã đặt đúng cờ ngược lại.** Đụng cờ hệ điều hành thì
  phải tra tài liệu giá trị đúng, đừng suy ra từ tên.
  *(Bài học 11/8/2026: `auto_update.py` bỏ `CREATE_NO_WINDOW` rồi ghi chú "cố ý hiện cửa sổ
  console", nhưng cờ thay vào là `DETACHED_PROCESS` — nghĩa là KHÔNG có console nào cả.
  Cờ đúng để hiện console là `CREATE_NEW_CONSOLE`. Hậu quả: `timeout` chết ⇒ vòng chờ
  60 giây co còn vài ms · UAC không lên ⇒ bộ cài không chạy · `pause` treo vĩnh viễn không
  cửa sổ nào để thấy. Suốt 3 bản phát hành không ai cập nhật được.)*

- 🔴 **Không đánh ✅ cho thứ chưa nhìn thấy chạy thật.** Đọc code thấy "hợp lý" không phải
  là bằng chứng. *(Bài học 11/8/2026: việc `U9` "hiện cửa sổ console" được đánh ✅ ngày 6/8
  trong khi thực tế chưa từng có cửa sổ nào hiện ra.)*

- 🔴 **Vá nằm trong cơ chế tự cập nhật thì không tự phát được.** Sửa `auto_update.py` xong
  phải hỏi ngay: máy đang chạy bản cũ có nhận được bản vá này không? Nếu đoạn hỏng nằm ở
  phía *máy khách*, câu trả lời luôn là **không** ⇒ phải phát bằng link tải tay một lần.
  *(Bài học 11/8/2026, việc `U16`.)*

- 🔴 **Quy trình viết cho agent tự chạy thì cổng kiểm phải là script Python, không phải
  lệnh shell.** `find /c /v ""`, `findstr /C:"..."`, `if exist` là cú pháp riêng của
  `cmd.exe`; chạy qua PowerShell hoặc qua một lớp bọc có đổi cách thoát dấu nháy là vỡ.
  *(Bài học 11/8/2026: OpenClaw dừng ở cổng 0 với `FIND: Parameter format not correct`
  và `'/\' is not recognized as an internal or external command`. Đã thay bằng
  `kiem_tra_truoc_commit.py`.)*

- 🔴 **Đừng đoán output của lệnh rồi viết cổng kiểm theo phỏng đoán đó — chạy thử trước.**
  *(Bài học 11/8/2026: cổng `0b` viết "phải thấy các dòng `remove`", đo thật thì
  `git add -A --dry-run` in ra 19 dòng `add` và **không có dòng `remove` nào** — vì
  ~11.000 lệnh xoá đã nằm sẵn trong vùng chờ. Để nguyên thì agent dừng oan.)*

- 🔴 **Sửa logic trước, sửa dữ liệu sau.** Gặp dữ liệu hỏng hàng loạt thì tìm luật sinh ra nó
  trước khi chạy `UPDATE`. Vá dữ liệu mà để nguyên luật là vài ngày sau hỏng lại.
  *(Bài học 11/8/2026: định sửa tay 1 lead, hoá ra 316 lead; đổi một dòng điều kiện trong
  `refresh_user_busy` gỡ được 308 lead mà không ghi đè một dòng lịch sử bán hàng nào.)*

---

## 💰 BẤT BIẾN ĐƠN HÀNG (bắt buộc rà mỗi khi đổi trạng thái)

Ba bảng phải luôn khớp nhau. Sửa một cái mà quên hai cái kia là sinh dữ liệu rác:

| Bảng | Cột trạng thái |
|---|---|
| `ds_don_hang` | `da_hoan_thanh` |
| `ds_bao_gia` | `dat_hang`, `thanh_toan`, `thanh_cong` |
| `sale_lead` | `status`, `dat_hang` |

Mọi thay đổi phải ghi vết vào **`lich_su_gd`** (nhật ký giao dịch) để audit — kể cả khi trả lại hàng.

---

## 🗄️ QUY TẮC ĐỔI SCHEMA

1. Viết file `alter_table_<tên>_v<N>.sql` — **không sửa file `.sql` cũ**, luôn tạo bản mới có số phiên bản.
2. Chạy bằng `run_sql_file.py`, không gõ tay trong client.
3. Chỉ **ADD COLUMN có DEFAULT** hoặc **CREATE TABLE mới**. Muốn DROP/RENAME → hỏi anh Tùng, vì
   `.exe` phiên bản cũ ngoài thực địa vẫn đang SELECT cột đó.

---

## 🔐 BẢO MẬT — VIỆC CHƯA XONG

Trạng thái ngày 6/8/2026 — **phần nguy hiểm đã xử lý xong**:

| Việc | Trạng thái |
|---|---|
| Revoke key OpenAI cũ | ✅ 6/8/2026 ⇒ key còn trong lịch sử git nhưng **đã vô hại** |
| Đổi mật khẩu MySQL | ✅ 6/8/2026 ⇒ mật khẩu cũ trong lịch sử git **đã vô hại** |
| Tách credential khỏi mã nguồn | ✅ 6/8/2026 — xem dưới |
| Gỡ `.venv/` (10.901 file) khỏi git | ✅ 6/8/2026 |

**Credential CSDL** — `misc.py` đọc theo thứ tự:

1. Biến môi trường `FSALES_DB_PASSWORD` (+ `_HOST` `_PORT` `_USER` `_NAME`)
2. `fsales_config.json` cạnh `Fsales.exe`
3. `_internal/fsales_config.json` (bản đóng gói)
4. `%APPDATA%\FSales\fsales_config.json`
5. **`DB_MAC_DINH` trong `misc.py`** ← đang dùng đường này

🔴 **Quyết định 6/8/2026 (anh Tùng): GIỮ mật khẩu mặc định trong mã nguồn.** App chạy được ngay,
không phải phát kèm file config. Anh Tùng đánh giá rủi ro chấp nhận được.

⚠️ **Hệ quả phải nhớ:** mật khẩu nằm trong lịch sử git và trong mọi `.exe` đã phát. Ai đọc được
repo là kết nối thẳng vào CSDL sản xuất. **Chưa xác minh repo là public hay private** (`S6`) —
nếu public thì phải xử lý ngay.

📌 **Khi nào phải đổi:** có người nghỉ việc · repo chuyển sang public · nghi lộ.
Lúc đó chỉ cần **xoá `DB_MAC_DINH`** trong `misc.py` — bốn đường đọc phía trên đã dựng sẵn và
đã test (`S11`). Mẫu config: `fsales_config.example.json`.

⛔ Nếu bỏ mặc định thì **không** thêm `fsales_config.json` vào `datas` của `main.spec` — làm vậy là
nhúng lại mật khẩu vào `.exe`. Phải để **bộ cài** đặt nó cạnh exe kèm cờ `onlyifdoesntexist`.

---

## 🕳️ ĐIỂM MÙ CỦA CHÍNH BỘ NHỚ NÀY

1. **`AI_AGENT_PROJECT_MAP.md` / `AI_AGENT_FILE_INDEX.md` chốt ngày 13/3/2026** — sau đó đã thêm module
   khảo sát (tháng 6), BOM (tháng 6), nhà cung cấp (tháng 3–6), và đã gỡ AI (8/2026).
   ⇒ Phải kiểm lại trước khi tin. Tên file có chữ `AI_AGENT_` là do lịch sử, **không** có nghĩa
   là dự án còn AI.
   *(Bài học 6/8/2026: `AI_AGENT_PROJECT_MAP.md` mục 2 và 3 viết "`don_hang.py` ở root là file giao diện
   sinh tự động" và đề nghị "đồng bộ bản root với `UI/don_hang.py` khi đóng gói". Kiểm thực tế thì
   **file đó không còn ở root nữa** — đã xoá, code import `UI.don_hang`. Suýt tạo một việc không
   tồn tại trong sổ việc chỉ vì tin tài liệu cũ.)*

2. **Không có test tự động nào trong repo.** Mọi "đã chạy được" đều là chạy tay. Không được kết luận
   "sửa xong không hỏng gì" nếu chưa mở app thử. Riêng đợt gỡ AI 6/8/2026 mới chỉ kiểm tới mức
   `ast.parse` — **chưa ai mở app chạy thật** (`L2`).

3. **Anna nằm ngoài repo.** Nhìn code trong đây không biết Anna đang làm gì, tạo bao nhiêu lead,
   còn chạy hay đã dừng. Muốn biết phải hỏi anh Tùng hoặc query `sale_lead`.

---

## 🧹 DỌN RÁC — ĐÃ LÀM 6/8/2026

Đã xoá: 27 file `_patch*.py`/`_bom_*.py` rỗng · 5 file `*.bak` · `_trash_20260322_1151/` ·
`backups/` · `build/` (273 MB) · `Threads/` (chỉ còn `.pyc` mồ côi) · mọi `__pycache__` ·
file Excel/PDF lạc chỗ ở root · `UI.gui.py` (stub 272 byte do gõ nhầm `pyuic6 UI.gui.ui`).

**Git: 11.175 → 193 file được track** (gỡ `.venv/` 10.901 file + `__pycache__` khỏi index).

🔴 **Quy tắc giữ repo sạch:**
- Không tạo file `_patch*.py` để vá code — sửa thẳng file thật, git lo phần lịch sử.
- Không tạo `*.bak` / thư mục `backups/` — `git show <commit>:<file>` thay thế được.
- Chạy `pyuic6` phải đúng cú pháp `pyuic6 UI/gui.ui -o UI/gui.py`. Gõ `UI.gui.ui`
  sinh ra file rác ở thư mục gốc. *(Bài học 6/8/2026: sinh ra `UI.gui.py` 272 byte không có class nào.)*
- `.gitignore` đã có ngoại lệ `!main.spec` — đừng xoá dòng đó, `*.spec` bị ignore nhưng
  `main.spec` là file build chính.

Đợt 2 (6/8/2026): xoá `Fonts/` · `hop_dong_out/` · `FsalesIOS/` kèm `.github/workflows/ios-build.yml`.
**Git còn 140 file.** Dự án iOS đã tách khỏi repo này — nếu cần lại thì lấy từ lịch sử git.

**Còn lại trên đĩa, chờ anh Tùng quyết** (xem `VIEC-CAN-LAM.md` → `D12`):
`dist/` 290 MB (nguồn cho Inno Setup) · `release/` 333 MB (16 file `.iss` cần giữ + ~260 MB bộ cài cũ) ·
`installer/FsaleSetup.exe` 67 MB (4/2025) · `tools/` 11 MB.

---

## 🔀 KHÁC BIỆT VỚI TRAINBOT — ĐỪNG COPY NHẦM

`D:\TrainBot` **không có git**, nên nó phải tự dựng cơ chế an toàn bằng file. Fsales **có git**.
Do đó:

| TrainBot làm | Fsales | Lý do |
|---|---|---|
| `.backup/<ngày>/` copy cuối mỗi mạch việc | ❌ **không copy** | git đã lo. *(Chính TrainBot cũng đã bỏ quy ước này ngày 22/7/2026.)* |
| `_RAC-CHO-XOA/`, `*.bak` | ❌ **không dùng** | `git rm` + lịch sử commit thay thế |
| Vault "mỗi fact = 1 file `.md`" | ❌ **không dùng** | Sự thật của Fsales nằm trong **code và DB**, không phải file markdown |
| Nhật ký append-only khổng lồ | ⚠️ **có giới hạn** | `NHAT-KY` bên TrainBot đã phình 221 KB tới mức router phải cảnh báo đừng mở. Ở đây: mỗi mục ≤ 3 dòng, quá 12 tháng thì cắt sang `docs/luu-tru/` |
| CLAUDE.md làm router | ✅ **copy** | Repo 30+ module, file 100 KB+ — không có router thì đốt token |
| Sổ việc duy nhất, không xoá dòng ✅ | ✅ **copy** | `VIEC-CAN-LAM.md` |
| Quy tắc kèm `*(Bài học <ngày>)*` | ✅ **copy** | Quy tắc không có lý do sẽ bị vi phạm hoặc xoá nhầm |
| Khai báo điểm mù của bộ nhớ | ✅ **copy** | Xem mục ĐIỂM MÙ ở trên |
| Khai báo rõ NGOÀI PHẠM VI kèm ngày | ✅ **copy** | Xem mục AI ĐÃ GỠ |
| Đo trước làm sau · mỗi lần một thay đổi · nghi ngờ kết quả rỗng | ✅ **copy** | Áp thẳng vào nghiệp vụ tiền/kho |

---

## 📌 CUỐI MỖI MẠCH VIỆC

1. Cập nhật `VIEC-CAN-LAM.md` **ngay trong phiên** — đổi trạng thái, ghi ngày. Không xoá dòng đã xong.
2. Thêm 1 mục ≤ 3 dòng vào `NHAT-KY-FSALES.md`: *đã làm gì · vì sao · file nào đụng tới*.
3. Rút ra bài học từ sự cố ⇒ thêm vào mục **NGUYÊN TẮC KHÔNG ĐƯỢC VI PHẠM**, kèm `*(Bài học <ngày>: <sự cố>)*`.
