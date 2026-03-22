# AI_AGENT_PROJECT_MAP.md

Mục tiêu: giúp AI agent nắm nhanh kiến trúc project `D:\Fsales_PCCC` để triển khai nâng cấp (đặc biệt luồng **trả lại hàng**).

## 1) Tổng quan

Đây là ứng dụng desktop PyQt6 cho nghiệp vụ FSales (lead -> báo giá -> đơn hàng -> xuất kho -> báo cáo).

Luồng chính hiện tại:
1. `main.py` (màn hình chính, login, danh sách lead)
2. `lead_handle.py` (tạo/cập nhật lead)
3. `quotation.py` (tạo/chỉnh báo giá)
4. `order_handle.py` + `don_hang.py` (màn hình xử lý đơn hàng)
5. `stock_handle.py` (xuất/nhập kho)
6. `baocao.py` (báo cáo)

## 2) Vai trò của `don_hang.py`

Đúng như bạn nói: `don_hang.py` ở root là **file giao diện sinh tự động** từ Qt Designer (`UI/don_hang.ui`).

- Dấu hiệu: header `Form implementation generated from reading ui file ...`.
- Không nên sửa logic nghiệp vụ trong file này vì dễ bị ghi đè khi generate lại.
- Logic xử lý đơn hàng nằm chủ yếu ở `order_handle.py`.

## 3) Files/Module quan trọng cho nâng cấp trả lại hàng

### Core nghiệp vụ
- `order_handle.py`
  - `tao_don_hang(...)`
  - `save_data(...)`
  - `xuat_kho(...)`
  - đang là điểm chốt trạng thái `sale_lead`, `ds_bao_gia`, `ds_don_hang`.
- `stock_handle.py`
  - xử lý phiếu xuất/nhập kho; cần mở rộng để xử lý nhập kho do trả lại.
- `misc.py`
  - helper DB (`sql_one`, `sql_all`, `sql_commit`) và tiện ích dùng xuyên suốt.

### UI liên quan
- `UI/don_hang.ui` + `UI/don_hang.py`
  - đã có nút `but_tra_lai_hang` trong bản root `don_hang.py`.
- `don_hang.py` (root)
  - bản generate cũ/mới tùy thời điểm build, cần đồng bộ với `UI/don_hang.py` khi đóng gói.

### Điểm lưu ý kiến trúc
- Có song song file UI generate ở root và trong thư mục `UI/`.
- Cần thống nhất “nguồn sự thật” là `UI/*.ui` -> generate `UI/*.py` -> import vào logic handle.

## 4) Cấu trúc thư mục thực tế (nhìn nhanh)

- `AI/` : module AI chat/planner/safe-executor.
- `UI/` : file `.ui` và file py generate từ Qt.
- `Threads/` : luồng xử lý SQL phụ trợ.
- `assets/` : logo/tài nguyên.
- `build/`, `dist/`, `installer/` : artifact đóng gói, không phải nơi sửa logic chính.
- `.venv/` : môi trường Python local.

## 5) Quy tắc sửa code an toàn cho agent

1. **Không sửa trực tiếp file UI generate** (`don_hang.py`, `UI/*.py`) cho nghiệp vụ.
2. Sửa logic trong `order_handle.py`, `stock_handle.py`, module service/helper.
3. Nếu cần thêm control UI: sửa `UI/*.ui` và regenerate.
4. Tránh đổi cột DB hiện tại khi chưa có migration plan.
5. Khi sửa trạng thái đơn hàng, luôn rà lại đồng bộ giữa:
   - `ds_don_hang`
   - `ds_bao_gia` (`dat_hang`, `thanh_toan`)
   - `sale_lead` (`status`, `dat_hang`)

## 6) Trọng tâm cho phase tới (trả lại hàng)

- Hook sự kiện nút `but_tra_lai_hang` vào logic thật (hiện UI đã có control).
- Định nghĩa rõ rule cập nhật:
  - tồn kho (nhập trả)
  - công nợ/đã thanh toán/phải thu
  - trạng thái đơn hàng và lead
  - nhật ký giao dịch (`lich_su_gd`) để audit.
