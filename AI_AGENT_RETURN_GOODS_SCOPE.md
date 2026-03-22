# AI_AGENT_RETURN_GOODS_SCOPE.md

Mục tiêu: scope kỹ thuật để triển khai chức năng **trả lại hàng** cho project `D:\Fsales_PCCC`.

## 1) Tình trạng hiện tại

- UI đơn hàng đã có nút `but_tra_lai_hang` (trong `don_hang.py` root).
- Chưa thấy logic nghiệp vụ trả lại hàng tương ứng trong `order_handle.py`.
- Luồng hiện có thiên về chốt đơn + xuất kho, chưa có luồng đảo chiều (reverse flow).

## 2) Vị trí nên implement

- UI event binding: `order_handle.py` tại hàm tạo màn hình đơn hàng (`tao_don_hang`).
- Nghiệp vụ DB: tách thành hàm riêng trong `OrderHandle`, ví dụ:
  - `tra_lai_hang(so_bg, lead_id, ...)`
- Kho: gọi hàm nhập kho phù hợp trong `stock_handle.py` (hoặc bổ sung hàm mới nếu chưa có).

## 3) Yêu cầu dữ liệu tối thiểu cho một lần trả hàng

- `so_bg` / `lead_id`
- Danh sách hàng trả (model, số lượng trả, đơn giá tham chiếu)
- Lý do trả hàng
- Người thực hiện
- Thời điểm trả

## 4) Side effects cần đồng bộ

1. **Kho**: tăng lại tồn kho theo số lượng trả.
2. **Đơn hàng (`ds_don_hang`)**:
   - cập nhật giá trị thực thu/phải thu sau trả hàng
   - ghi chú + trạng thái xử lý trả hàng
   - append lịch sử vào `lich_su_gd`
3. **Báo giá (`ds_bao_gia`)**:
   - cập nhật cờ thanh toán nếu công nợ thay đổi
4. **Lead (`sale_lead`)**:
   - cập nhật trạng thái phù hợp theo nghiệp vụ sau trả hàng

## 5) Gợi ý trạng thái (để thống nhất trước khi code)

- `Đã đặt hàng`
- `Đã giao hàng`
- `Đã thanh toán`
- `Đã trả lại hàng` (nếu business chấp nhận thêm trạng thái mới)
- Hoặc giữ status cũ + ghi rõ trong `ghi_chu/lich_su_gd` nếu chưa muốn thêm status.

## 6) Checklist triển khai cho AI agent

1. Gắn sự kiện `but_tra_lai_hang.clicked`.
2. Thiết kế popup xác nhận + nhập thông tin trả hàng.
3. Viết hàm xử lý transaction-safe:
   - validate đầu vào
   - cập nhật kho
   - cập nhật đơn/báo giá/lead
   - ghi lịch sử
4. Hiển thị thông báo thành công/thất bại rõ ràng trên UI.
5. Test các case:
   - trả một phần
   - trả toàn bộ
   - trả khi đơn đã thanh toán
   - trả nhiều lần trên cùng đơn.

## 7) Nguyên tắc an toàn

- Mọi cập nhật trả hàng nên nằm trong transaction.
- Không xóa cứng dữ liệu cũ; dùng lịch sử để truy vết.
- Ưu tiên cộng/trừ số liệu theo delta, tránh overwrite mù.
