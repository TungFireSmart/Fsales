CODE_ONTOLOGY = """
Fsales là ứng dụng desktop Python (PyQt6) gồm các module chính:

=== UI ===
- main.py: cửa sổ chính, điều hướng
- quotation.py: tạo/sửa báo giá
- stock_handle.py: nhập/xuất/tồn kho
- report.py: báo cáo tổng hợp

=== DATA ACCESS ===
- misc.py: lớp truy cập DB (sql_all, sql_one, sql_commit)
- ai_safe_executor.py: truy vấn DB an toàn cho AI (SELECT-only)

=== BUSINESS LOGIC ===
- quotation_save.py: tính tiền, lưu báo giá
- order_handle.py: tạo đơn hàng từ báo giá
- lead_handle.py: quản lý lead

=== AI SYSTEM ===
- ai_planner.py: hiểu câu hỏi, lập kế hoạch truy vấn
- ai_safe_executor.py: thực thi kế hoạch
- ai_memory.py: nhớ ngữ cảnh hội thoại
- ai_logic.py: điều phối AI
- business_ontology.py: bản đồ nghiệp vụ
- metric_dictionary.py: từ điển số liệu

=== GIỚI HẠN HIỆN TẠI ===
- Chưa có khái niệm lợi nhuận (profit)
- Chưa có lịch sử tồn kho theo ngày
- Chưa có KPI tỷ lệ chốt chuẩn hóa
- AI không sửa code trực tiếp
"""
