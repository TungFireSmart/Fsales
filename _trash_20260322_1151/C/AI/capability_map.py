CAPABILITY_MAP = {
    "doanh số": {
        "supported": True,
        "source": "ds_don_hang",
        "note": "Tính theo đơn hàng đã chốt"
    },
    "báo giá": {
        "supported": True,
        "source": "ds_bao_gia"
    },
    "tồn kho": {
        "supported": True,
        "source": "ton_kho",
        "note": "Giá trị hiện tại, không có lịch sử theo ngày"
    },
    "lợi nhuận": {
        "supported": False,
        "reason": "Chưa có chi phí thực tế & giá bán gắn đơn hàng"
    },
    "kpi tỷ lệ chốt": {
        "supported": False,
        "reason": "Chưa chuẩn hóa định nghĩa"
    }
}
