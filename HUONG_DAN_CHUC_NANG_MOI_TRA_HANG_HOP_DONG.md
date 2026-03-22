# HƯỚNG DẪN SỬ DỤNG CHỨC NĂNG MỚI

Tài liệu này hướng dẫn 2 chức năng mới vừa nâng cấp trong FSales:
1. Quy trình nhận hàng trả lại theo đơn hàng
2. Tạo hợp đồng theo báo giá

---

## 1) Quy trình nhận hàng trả lại theo đơn hàng

### 1.1. Mục tiêu
Quy trình trả lại hàng được tách theo vai trò để tránh sai sót:
- **Sales** lập phiếu yêu cầu trả lại hàng
- **Manager** duyệt / từ chối
- **Kế toán** thực thi sau khi đã duyệt

---

### 1.2. Sales lập phiếu yêu cầu trả lại hàng

**Điều kiện quyền:** user power `<= 40`

**Cách thao tác:**
1. Mở đơn hàng cần xử lý.
2. Bấm nút **Trả lại hàng**.
3. Hệ thống mở màn hình **Phiếu yêu cầu trả lại hàng** gồm:
   - Tiêu đề phiếu
   - Tên khách hàng, tên công ty, số điện thoại liên hệ
   - Bảng chi tiết đơn hàng (readonly)
   - Cột nhập **SL trả lại**
   - Ô nhập **Lý do trả lại hàng** (bắt buộc)
   - Chọn phương án VAT:
     - `Không xử lý hóa đơn`
     - `Cần xuất hóa đơn giảm trừ`
4. Bấm xác nhận để **Gửi duyệt**.

**Kết quả:**
- Phiếu được lưu trạng thái `PENDING_APPROVAL`.
- Chưa cập nhật tài chính/kho ở bước này.

---

### 1.3. Manager duyệt / từ chối

**Điều kiện quyền:** user power `> 50`

**Cách thao tác:**
1. Trên màn hình chính, trong bảng lead sẽ có dòng:
   - `[TRẢ HÀNG - CHỜ DUYỆT] ...`
2. Bấm **Duyệt/Từ chối**.
3. Màn hình duyệt hiển thị đầy đủ:
   - Thông tin khách hàng
   - Bảng hàng hóa và SL trả lại
   - Tiền hàng giảm trừ, VAT giảm trừ, tổng giảm trừ dự kiến
4. Chọn:
   - **Duyệt** -> chuyển `APPROVED`
   - **Từ chối** -> chuyển `REJECTED`

---

### 1.4. Kế toán thực thi sau duyệt

**Điều kiện quyền:** user power `41..50`

**Cách thao tác:**
1. Trên màn hình chính, tìm dòng:
   - `[TRẢ HÀNG - CHỜ KẾ TOÁN] ...`
2. Bấm **Thực thi**.
3. Màn hình thực thi hiển thị lại đầy đủ nội dung phiếu.
4. Bấm **Thực thi** để áp dụng nghiệp vụ.

**Hệ thống sẽ làm:**
- Cập nhật công nợ/đã thanh toán/phải thu theo phiếu trả hàng.
- Đồng bộ trạng thái đơn hàng, báo giá, lead tương ứng.
- Ghi log workflow (`RETURN_APPLIED`, `RETURN_REQ_EXECUTED`).
- Hỏi mở phiếu nhập kho trả lại.

---

### 1.5. Logic VAT trong giảm trừ

- Nếu chọn **Không xử lý hóa đơn**:
  - VAT giảm trừ = `0`
  - Tổng giảm trừ = tiền hàng
- Nếu chọn **Cần xuất hóa đơn giảm trừ**:
  - VAT giảm trừ = VAT theo phần hàng trả
  - Tổng giảm trừ = tiền hàng + VAT

---

### 1.6. Resume khi công việc bị dừng giữa chừng

Nếu phiếu đã `EXECUTED` nhưng chưa nhập kho trả lại, hệ thống vẫn cho kế toán tiếp tục từ bước dở dang:
- Hiển thị dòng: `[TRẢ HÀNG - CẦN TIẾP TỤC] ...`
- Cho mở lại luồng phiếu nhập kho trả lại.

---

## 2) Tạo hợp đồng theo báo giá

### 2.1. Mục tiêu
Tạo file hợp đồng Word từ template có sẵn trong project:
- `mau_hop_dong.docx`

---

### 2.2. Cách thao tác

1. Mở màn hình báo giá.
2. Bấm **Tạo hợp đồng**.
3. Hệ thống mở màn hình kiểm tra thông tin công ty/khách hàng (CRM detail).
4. Kiểm tra/chỉnh thông tin nếu cần.
5. Bấm nút **Tạo hợp đồng** ở màn hình này.
6. Hệ thống mở **Save dialog**:
   - Cho chọn thư mục lưu
   - Cho đổi tên file hợp đồng
7. Bấm Save để tạo file `.docx`.

---

### 2.3. Nguồn dữ liệu điền vào hợp đồng

- **Số hợp đồng**: `so_bg + "/HĐKT"`
- **Ngày ký**: ngày tạo hợp đồng
- **Thông tin còn lại**: lấy theo thông tin của lead liên kết báo giá

Các placeholder tổng tiền hiện hỗ trợ:
- `{tong_tien_hang}`
- `{tong_vat}`
- `{tong_cong}`
- `{tien-bang-chu}`

---

### 2.4. Bảng danh mục hàng trong hợp đồng

Template đã có bảng placeholder `{{ITEM_TABLE}}` để đổ danh mục hàng theo báo giá.

Lưu ý hiện tại:
- Không ghi thuế chi tiết từng dòng hàng (theo yêu cầu mới).
- Thuế chỉ thể hiện ở phần tổng bên dưới qua placeholder tổng.

---

## 3) Checklist test nhanh cho user

### Trả hàng
- [ ] Sales tạo phiếu và gửi duyệt được
- [ ] Manager thấy phiếu chờ duyệt và duyệt/từ chối được
- [ ] Kế toán chỉ thực thi sau khi đã duyệt
- [ ] Logic VAT đúng theo lựa chọn
- [ ] Trường hợp dở dang có thể resume

### Hợp đồng
- [ ] Bấm Tạo hợp đồng mở đúng màn hình kiểm tra
- [ ] Nút Tạo hợp đồng tạo được file .docx
- [ ] Save dialog cho đổi tên/chọn thư mục lưu
- [ ] Placeholder chính được điền đúng dữ liệu
- [ ] Bảng danh mục hàng được đổ đúng từ báo giá

---

Nếu cần, có thể tách thêm tài liệu này thành:
- Hướng dẫn cho Sales
- Hướng dẫn cho Manager
- Hướng dẫn cho Kế toán
để training nội bộ dễ hơn.
