DB_ONTOLOGY = """
Fsales sử dụng cơ sở dữ liệu quan hệ (MySQL).
Dưới đây là cấu trúc dữ liệu ở mức NGHIỆP VỤ, không phải schema SQL.

=================================================
1. BẢNG SALE_LEAD – KHÁCH HÀNG TIỀM NĂNG
=================================================
Bảng: sale_lead

Mục đích:
- Lưu thông tin khách hàng tiềm năng (lead).
- Là điểm bắt đầu của mọi quy trình bán hàng.

Các cột chính:
- sale_lead.lead_id: (INT) Mã lead – khóa chính.
- sale_lead.name: (TEXT) Tên khách hàng.
- sale_lead.company: (TEXT) Tên công ty.
- sale_lead.sdt: (TEXT) Số điện thoại.
- sale_lead.mst: (TEXT) Mã số thuế.
- sale_lead.address: (TEXT) Địa chỉ.
- sale_lead.email: (TEXT) Email.
- sale_lead.phu_trach: (TEXT) Sale phụ trách lead.
- sale_lead.nguoi_tao_lead: (TEXT) Người tạo lead.
- sale_lead.status: (TEXT) Trạng thái lead
  (ví dụ: mới, đang xử lý, đã báo giá, đã chốt, thất bại).
- sale_lead.time_create: (DATETIME) Thời điểm tạo lead.
- sale_lead.time_nhan_viec: (DATETIME) Thời điểm sale nhận xử lý.

Ý nghĩa nghiệp vụ:
- Một lead có thể có N báo giá.
- Một lead có thể sinh ra 0 hoặc nhiều đơn hàng.
- Lead KHÔNG đồng nghĩa với doanh số.

=================================================
2. BẢNG DS_BAO_GIA – BÁO GIÁ
=================================================
Bảng: ds_bao_gia

Mục đích:
- Lưu các báo giá được tạo cho lead.
- Phản ánh đề xuất bán hàng, KHÔNG phải doanh thu thực tế.

Các cột chính:
- ds_bao_gia.so_bg: (INT) Số báo giá – khóa chính.
- ds_bao_gia.lead_id: (INT) Liên kết tới sale_lead.lead_id.
- ds_bao_gia.sotien: (NUMERIC) Giá trị báo giá.
- ds_bao_gia.user: (TEXT) Sale tạo báo giá.
- ds_bao_gia.ngaythang: (DATE) Ngày tạo báo giá.
- ds_bao_gia.thanh_cong: (TEXT) Trạng thái chốt ('T' = đã chốt).

Ý nghĩa nghiệp vụ:
- Một lead có thể có nhiều báo giá.
- Báo giá CHƯA chốt KHÔNG được tính là doanh số.
- Báo giá có thể sửa nhiều lần trước khi chốt.

=================================================
3. BẢNG DS_DON_HANG – ĐƠN HÀNG / DOANH SỐ
=================================================
Bảng: ds_don_hang

Mục đích:
- Lưu đơn hàng thực tế đã chốt.
- Là NGUỒN DUY NHẤT để tính doanh số.

Các cột chính:
- ds_don_hang.so_bg: (INT) Số báo giá gốc.
- ds_don_hang.lead_id: (INT) Lead tương ứng.
- ds_don_hang.tien_hang: (NUMERIC) Giá trị đơn hàng (doanh số).
- ds_don_hang.vat: (NUMERIC) Thuế VAT.
- ds_don_hang.ngaythang: (DATE) Ngày tạo đơn hàng.
- ds_don_hang.nguoi_tao: (TEXT) Sale tạo đơn.
- ds_don_hang.da_hoan_thanh: (TEXT) Trạng thái hoàn thành ('T' = hoàn tất).

Ý nghĩa nghiệp vụ:
- Chỉ ds_don_hang.tien_hang mới được dùng để tính DOANH SỐ.
- Báo giá KHÔNG thay thế cho đơn hàng.
- Doanh số thường được tổng hợp theo sale và thời gian.

=================================================
4. BẢNG GIA_TONG_HOP – MASTER DATA SẢN PHẨM
=================================================
Bảng: gia_tong_hop

Mục đích:
- Lưu thông tin chuẩn về sản phẩm.

Các cột chính:
- gia_tong_hop.model: (TEXT) Mã sản phẩm – khóa logic.
- gia_tong_hop.ten_san_pham: (TEXT) Tên sản phẩm.
- gia_tong_hop.nhan_hieu: (TEXT) Nhãn hiệu.
- gia_tong_hop.don_vi: (TEXT) Đơn vị tính.
- gia_tong_hop.vat: (NUMERIC) Thuế VAT.
- gia_tong_hop.gia_dau_vao: (NUMERIC) Giá vốn.

Ý nghĩa nghiệp vụ:
- Dùng cho báo giá, kho, lợi nhuận.
- Giá đầu vào KHÔNG phải doanh số.

=================================================
5. BẢNG TON_KHO – TỒN KHO
=================================================
Bảng: ton_kho

Mục đích:
- Lưu số lượng tồn kho hiện tại.

Các cột chính:
- ton_kho.model: (TEXT) Mã sản phẩm.
- ton_kho.ten_san_pham: (TEXT) Tên sản phẩm.
- ton_kho.ton: (NUMERIC) Số lượng tồn.
- ton_kho.gia_dau_vao: (NUMERIC) Giá vốn.
- ton_kho.ma_kho: (TEXT) Mã kho.

Ý nghĩa nghiệp vụ:
- Tồn kho ảnh hưởng KHẢ NĂNG giao hàng.
- Giá trị tồn kho = ton * gia_dau_vao.
- Hệ thống hiện tại KHÔNG lưu lịch sử tồn kho theo ngày.

=================================================
6. BẢNG USER – SALE / QUẢN LÝ
=================================================
Bảng: user

Mục đích:
- Lưu thông tin người dùng hệ thống.

Các cột chính:
- user.full_name: (TEXT) Tên người dùng.
- user.phone_number: (TEXT) Số điện thoại đăng nhập.
- user.power: (INT) Quyền (>=40 là quản lý).
- user.check_busy: (INT) Trạng thái bận.

Ý nghĩa nghiệp vụ:
- Sale phụ trách lead, báo giá, đơn hàng.
- Quản lý xem tổng hợp toàn hệ thống.

=================================================
7. QUAN HỆ GIỮA CÁC BẢNG
=================================================
- sale_lead.lead_id ↔ ds_bao_gia.lead_id
- sale_lead.lead_id ↔ ds_don_hang.lead_id
- ds_bao_gia.so_bg ↔ ds_don_hang.so_bg
- gia_tong_hop.model ↔ ton_kho.model

=================================================
8. NGUYÊN TẮC SUY LUẬN BẮT BUỘC
=================================================
- Doanh số → chỉ dùng ds_don_hang.tien_hang.
- Không suy doanh số từ ds_bao_gia nếu chưa chốt.
- Khi hỏi "theo sale" → dùng user / nguoi_tao.
- Khi hỏi "toàn công ty" → KHÔNG group_by sale.
- Khi hỏi theo thời gian:
  + Tuần → YEARWEEK(date_col, 1)
  + Tháng → YEAR + MONTH
  + Năm → YEAR
- Tồn kho phản ánh rủi ro bán hàng, KHÔNG phản ánh doanh số.
"""
