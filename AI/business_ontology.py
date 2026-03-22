BUSINESS_ONTOLOGY = """
Fsales là hệ thống CRM + quản lý bán hàng + kho nội bộ.

=== KHÁI NIỆM CỐT LÕI ===

1. Lead
- Lead là khách hàng tiềm năng.
- Một lead được tạo khi có nhu cầu mua hàng.
- Lead có thể được phân công cho một sale phụ trách.
- Lead có thể trải qua các trạng thái: mới, đang xử lý, đã báo giá, đã chốt, thất bại.

2. Báo giá
- Báo giá được tạo cho một lead.
- Một lead có thể có nhiều báo giá.
- Báo giá phản ánh giá trị dự kiến bán hàng.
- Báo giá chưa chốt KHÔNG phải doanh số.
- Báo giá có thể được sửa nhiều lần trước khi chốt.

3. Đơn hàng
- Đơn hàng được tạo khi một báo giá được chốt.
- Đơn hàng là cơ sở duy nhất để tính doanh số.
- Chỉ đơn hàng đã hoàn thành mới được tính doanh số.
- Một đơn hàng gắn với một báo giá và một lead.

4. Doanh số
- Doanh số là tổng giá trị bán hàng thực tế.
- Doanh số được tính từ đơn hàng, không tính từ báo giá chưa chốt.
- Doanh số thường được quan tâm theo: ngày, tuần, tháng, năm.
- Doanh số có thể được tổng hợp theo sale.

5. Sale
- Sale là người phụ trách lead và tạo báo giá.
- Hiệu suất sale được đánh giá qua:
  + số báo giá
  + số đơn hàng
  + doanh số
  + tỷ lệ chốt

6. Kho hàng
- Kho lưu trữ hàng hóa thực tế.
- Tồn kho là số lượng hàng còn lại.
- Tồn kho ảnh hưởng trực tiếp đến khả năng giao hàng và chốt đơn.
- Giá đầu vào dùng để tính giá trị tồn kho và lợi nhuận, không phải doanh số.

7. Mối quan hệ nghiệp vụ
- Lead → Báo giá → Đơn hàng → Doanh số
- Kho → ảnh hưởng → khả năng chốt đơn
- Sale → phụ trách → Lead và Báo giá
- Quản lý quan tâm đến: doanh số, hiệu suất sale, rủi ro tồn kho, lead quá hạn.

=== NGUYÊN TẮC SUY LUẬN ===

- Không nhầm lẫn giữa báo giá và doanh số.
- Không tính doanh số từ dữ liệu chưa chốt.
- Khi hỏi về hiệu suất sale, cần xác định rõ theo báo giá hay theo doanh số.
- Khi hỏi về thời gian, cần xác định rõ: tuần, tháng, năm.
"""
