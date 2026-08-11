# Đề xuất mở rộng vai trò Anna — dựa trên bài học từ trycompai/crm

> **Trạng thái: ĐỀ XUẤT, chưa làm gì.** File này không đụng vào app desktop, không dựng lại AI
> trong app — đúng theo `CLAUDE.md` mục **AI ĐÃ GỠ**. Đây là bản đọc trước để anh Tùng quyết,
> nếu đồng ý thì mới chuyển các mục thành dòng trong `VIEC-CAN-LAM.md` (đề xuất tiền tố `A#`).

## 1. Phạm vi

Anh Tùng đã chọn hướng: **không đụng AI trong app, mở rộng vai trò của Anna** — agent ngoài
(OpenClaw), hiện đang tự tạo lead vào `sale_lead`. Hướng này thực ra khớp gần như chính xác với
triết lý cốt lõi của `trycompai/crm` mà tôi vừa nghiên cứu: *agent không phải một tính năng gắn
vào app, agent là một tiến trình riêng, đọc/ghi vào nơi lưu dữ liệu chung, và app chỉ là nơi
hiển thị kết quả.* Anna đã đứng đúng vị trí đó rồi — vấn đề là mở rộng nó **an toàn** và **có
lý do rõ ràng cho từng hành động**, hai thứ mà đợt gỡ AI hồi 6/8/2026 cho thấy đang thiếu.

## 2. Anna hiện đang làm gì (đọc trực tiếp từ code, không đoán)

Từ `main.py:406-464` và `misc.py:373-388`:

- Anna tạo lead với `sale_lead.nguoi_tao_lead = 'Anna'`, đặt tiêu đề tạm
  (`LEAD_TITLE_PLACEHOLDER_ANNA`) và `status = 'Anna đã giao việc'`.
- Fsales tự **thu hồi** lead này nếu quá **1 giờ** mà chưa có báo giá (`ds_bao_gia`) hoặc đơn hàng
  (`ds_don_hang`) gắn với `lead_id` đó — trả `status` về `'Mới'`, xoá `phu_trach`.
- Mỗi lần thu hồi được ghi vào `sale_lead_audit_log` qua `misc.audit_log(actor, action, field,
  old_value, new_value, lead_id)` — actor ghi cứng là `'system'`, không phải Anna, action là
  `AUTO_RELEASE` / `UPDATE_OWNER`.
- Thời hạn 1 giờ là **hằng số cứng trong code Fsales** (`TIMESTAMPDIFF(HOUR, ..., NOW()) >= 1`),
  không phải một giá trị Anna tự đặt kèm lý do.

## 3. Điểm mù cần anh Tùng làm rõ trước khi mở rộng

`CLAUDE.md` tự nhận: *"Anna nằm ngoài repo. Nhìn code trong đây không biết Anna đang làm gì,
tạo bao nhiêu lead, còn chạy hay đã dừng."* Trước khi mở rộng, có một câu hỏi bảo mật cụ thể mà
tôi không tự trả lời được vì không có quyền vào repo/workspace OpenClaw của Anna:

**Anna hiện ghi vào MySQL bằng credential nào?**

Nếu Anna dùng chung mật khẩu mặc định đang hardcode trong `misc.py` (`DB_MAC_DINH` — mục BẢO MẬT
của `CLAUDE.md` đã ghi rõ đây là rủi ro chấp nhận-được-tạm-thời), thì việc *mở rộng* những gì Anna
làm — cho nó đọc thêm dữ liệu nhạy cảm, gọi thêm API ngoài để làm giàu thông tin khách hàng — sẽ
mở rộng luôn diện tích của rủi ro đó. Đây đúng là hình dạng của lỗi đã khiến phải gỡ AI khỏi app
hồi 6/8/2026 (key/mật khẩu plaintext, không kiểm soát được đường ra). Nên trả lời câu này trước
khi làm bất kỳ mục nào ở phần 5.

## 4. Bài học từ trycompai/crm áp vào Anna — cụ thể, không chung chung

### a) Ghi "quan sát được", không ghi "suy đoán" — evidence, không phải confidence

Nếu Anna mở rộng sang việc tự điền thông tin công ty/liên hệ (industry, quy mô, người phụ trách),
áp nguyên tắc: Anna không tự gán "tôi chắc 80%". Thay vào đó phân hai loại ghi:

- **Ghi thẳng** khi bằng chứng mạnh — ví dụ: khách hàng tự điền form, chữ ký email trùng khớp,
  dữ liệu từ chính `sale_lead` do người dùng nhập.
- **Chỉ đề xuất, chờ sale duyệt** khi bằng chứng yếu — ví dụ: đoán ngành nghề công ty từ tên miền,
  suy luận từ dữ liệu bên ngoài không xác thực.

Hiện tại Anna chỉ tạo lead với tiêu đề placeholder chờ sale đặt tên — đây thực ra **đã đúng
nguyên tắc này một cách tự nhiên** (không tự bịa tên lead). Giữ nguyên tinh thần đó khi mở rộng
sang các trường dữ liệu khác.

### b) Hành động tự động phải có lý do gắn theo từng bản ghi, không phải hằng số cứng toàn cục

`trycompai/crm` có nguyên tắc: *"một agent không thể nói vì sao 14 ngày nữa nó sẽ quay lại thì
không có lý do, nó chỉ có một giá trị mặc định."* Quy tắc 1-giờ-thu-hồi hiện tại của Fsales đúng
là một giá trị mặc định toàn cục — hợp lý cho hiện trạng, nhưng nếu Anna mở rộng sang việc tự đặt
lịch nhắc lại (ví dụ "28 ngày nữa hỏi lại khách này vì họ nói đang chờ duyệt ngân sách"), nên có
một cột `ly_do` / `next_check_at` đi kèm mỗi lead do Anna tạo, thay vì một con số cứng áp cho
mọi lead như nhau. Sale nhìn vào thấy "Anna sẽ hỏi lại khách này ngày X vì Y" thay vì một hộp đen.

### c) `sale_lead_audit_log` đã là "ledger" đúng hướng — nhưng thiếu actor thật

`misc.audit_log` đã làm đúng điều `trycompai/crm` gọi là "evidence ledger": mọi thay đổi trạng
thái đều có dòng nhật ký. Điểm cần vá: hành động tự động ghi `actor='system'` chứ không phải
`'Anna'` hay `'auto_release_1h'` — nên nếu sau này có nhiều loại tự động hoá (không chỉ Anna),
sẽ không phân biệt được cái gì gây ra thay đổi. Đề xuất: actor cụ thể theo nguồn (`'Anna'`,
`'system:auto_release'`...) để `sale_lead_audit_log` thực sự trả lời được câu "ai/cái gì đã làm
việc này và vì sao" — đúng tinh thần ledger của `trycompai/crm`.

### d) Ranh giới "báo sự kiện" vs "quyết định" — Fsales đã đứng đúng phía

`trycompai/crm` cấm API tự ra quyết định nghiệp vụ — API chỉ báo "việc gì vừa xảy ra", agent mới
là bên quyết định. Kiến trúc Anna hiện tại vô tình đã đúng hướng này: Fsales (app + DB) không tự
"nghĩ" ra lead, nó chỉ lưu những gì Anna quyết định tạo. Điều cần giữ khi mở rộng: **đừng để logic
quyết định của Anna bị chép một bản vào trong app** (ví dụ: đừng thêm rule "nếu Anna nói X thì
app tự làm Y" cứng trong `main.py`) — nguyên nhân gốc của một sự cố thật trong `trycompai/crm` là
hai bản sao logic khớp danh tính bị trôi dạt khác nhau tới mức một bản khớp *mọi* công ty trên
đời. Nếu cần app phản ứng theo hành vi của Anna, nên qua dữ liệu (một cột trạng thái/cờ) chứ
không phải hai nơi cùng tự suy luận.

### e) Đừng cho agent vừa có mạng vừa có credential DB trực tiếp

Đây là nguyên tắc bảo mật cứng nhất trong `trycompai/crm`: sandbox chạy lệnh của agent **không
bao giờ** được cấp cả quyền mạng lẫn `DATABASE_URL` cùng lúc — "một shell có cả hai là hình dạng
của một vụ rò rỉ dữ liệu." Đây chính xác là câu hỏi ở mục 3: nếu Anna vừa gọi API/web bên ngoài
(để làm giàu dữ liệu khách hàng) **vừa** cầm credential MySQL sản xuất trực tiếp, đó là cấu hình
rủi ro cao — dữ liệu khách hàng có thể rò ra ngoài qua một câu lệnh sai hoặc một tool bị lừa.
Hướng an toàn hơn: Anna ghi/đọc qua một lớp trung gian hẹp (API riêng hoặc user MySQL chỉ có
quyền `INSERT`/`UPDATE` đúng những bảng cần, không phải user full quyền dùng chung với app).

### f) Đây chính là lý do W1/W2 (đã chốt sẵn trong sổ việc) đáng làm sớm hơn dự kiến

`VIEC-CAN-LAM.md` đã có sẵn hai việc dài hạn: `W1` (tách tầng nghiệp vụ khỏi PyQt) và `W2`
(client không giữ credential DB, mọi query qua API). Nếu quyết định mở rộng Anna, `W2` không chỉ
phục vụ mục tiêu "lên web" nữa — nó **chính là hạ tầng an toàn cần có để Anna hoạt động rộng hơn
mà không cầm credential MySQL sản xuất trực tiếp**. Một API mỏng, chỉ mở đúng vài hành động Anna
cần (tạo lead, đọc trạng thái lead của mình, cập nhật ghi chú) — không phải kết nối SQL thô — là
cách áp nguyên tắc "API chỉ báo sự kiện, agent quyết định" một cách an toàn cho cả Anna lẫn hướng
web sau này. Hai việc đang tưởng như độc lập hoá ra cùng một hạ tầng.

## 5. Đề xuất cụ thể (chờ anh Tùng duyệt từng mục — chưa làm gì)

Không mục nào ở đây đụng vào file UI hay logic app desktop hiện có. Tất cả nằm ở "phía Anna" hoặc
là một API mới, tách biệt.

| # | Đề xuất | Vì sao | Phụ thuộc |
|---|---|---|---|
| A1 | Trả lời câu hỏi mục 3: Anna hiện dùng credential MySQL nào | Chặn mọi việc mở rộng khác — phải biết diện rủi ro hiện tại trước | Anh Tùng |
| A2 | Đổi `actor` trong `audit_log` khi Anna/hệ thống tự động hành động, từ `'system'` chung chung thành nguồn cụ thể | Ledger hiện có bắt đầu trả lời được "ai/cái gì đã làm" | Không phụ thuộc, làm được ngay trong `main.py` (không đụng UI) |
| A3 | Thêm cột `ly_do_thu_hoi` (hoặc tương tự) khi tự động thu hồi lead Anna, thay vì chỉ đổi status | Biến hằng số 1-giờ thành quyết định có ghi lý do, đúng tinh thần "agent phải nói được vì sao" | Cần alter table nhỏ, theo đúng quy tắc **QUY TẮC ĐỔI SCHEMA** trong `CLAUDE.md` |
| A4 | Thiết kế một API mỏng (không phải SQL thô) cho riêng Anna: tạo lead, đọc lead của mình, cập nhật ghi chú — user MySQL đứng sau API này chỉ có quyền tối thiểu | Gỡ rủi ro "agent vừa có mạng vừa có credential DB rộng" — đồng thời là bước đầu của `W2` | Cần quyết định stack (`W3` đang chờ anh Tùng) hoặc làm một API rất nhỏ độc lập với hướng web dài hạn |
| A5 | Nếu mở rộng Anna sang làm giàu dữ liệu (tra cứu công ty, LinkedIn...): thiết kế mỗi nguồn là tuỳ chọn bật/tắt, và phân biệt rõ "ghi thẳng" vs "đề xuất chờ duyệt" theo độ mạnh bằng chứng | Áp mục 4a — tránh lặp lại kiểu lỗi "AI tự tin nhưng sai" | Sau A1, A4 |

## 6. Việc KHÔNG đề xuất

Để tránh hiểu nhầm là đang lách quyết định 6/8/2026: không đề xuất thêm bất kỳ giao diện chat/AI
nào vào app desktop, không đề xuất khôi phục `AI/`, `openclaw_bridge_server.py`, hay bất cứ thứ
gì đã bị `git rm`. Nếu sau này thực sự cần một giao diện để sale "hỏi Anna" ngay trong app (giống
tab **Agent** của `trycompai/crm`, gắn theo từng lead) — đó là một quyết định khác, cần hỏi anh
Tùng riêng, không nằm trong phạm vi đề xuất này.

---

**Tham khảo:** `nghien-cuu-trycompai-crm-cho-fsales.md` (thư mục gốc dự án — bản nghiên cứu tổng
quan về kiến trúc `trycompai/crm`); `CLAUDE.md` mục AI ĐÃ GỠ, BẢO MẬT; `VIEC-CAN-LAM.md` nhóm `W#`.
