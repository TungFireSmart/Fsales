METRIC_DICTIONARY = {
    "doanh số": {
        "description": "Tổng giá trị bán hàng thực tế",
        "table": "ds_don_hang",
        "field": "tien_hang",
        "aggregation": "SUM",
        "condition": "đơn hàng đã chốt / hoàn thành",
        "note": "Không tính từ báo giá chưa chốt"
    },

    "số báo giá": {
        "description": "Số lượng báo giá được tạo",
        "table": "ds_bao_gia",
        "aggregation": "COUNT",
        "note": "Không phản ánh doanh số"
    },

    "doanh số theo sale": {
        "description": "Doanh số được tạo bởi từng sale",
        "table": "ds_don_hang",
        "field": "tien_hang",
        "group_by": "nguoi_tao",
        "aggregation": "SUM"
    },

    "báo giá theo sale": {
        "description": "Số báo giá mỗi sale tạo ra",
        "table": "ds_bao_gia",
        "group_by": "user",
        "aggregation": "COUNT"
    },

    "tồn kho": {
        "description": "Giá trị hàng tồn kho",
        "table": "ton_kho",
        "aggregation": "SUM(ton * gia_dau_vao)",
        "note": "Giá trị đầu vào, không phải doanh thu"
    },

    "lead quá hạn": {
        "description": "Lead chưa xử lý quá số ngày cho phép",
        "table": "sale_lead",
        "condition": "time_create quá X ngày và chưa chốt"
    }
}
