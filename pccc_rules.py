"""
pccc_rules.py — Logic tra cứu QCVN 10:2025/BCA cho module Tư vấn PCCC.

Port từ PCCC_Advisor_v5.html sang Python thuần (không phụ thuộc Qt/DB).
Căn cứ:
  - QCVN 10:2025/BCA (Bảng A.1, B.1, E.1, F.1, G.1)
  - Nghị định 105/2025/NĐ-CP (Phụ lục I, Điều 27)
  - Luật PCCC & CNCH 55/2024/QH15
  - TCVN 7568-14:2025, TCVN 13456:2022, TCVN 7336:2021

Đầu vào chung (dict `i`):
    dt    : tổng diện tích sàn (m²)
    cao   : chiều cao PCCC (m)
    tang  : số tầng nổi
    ham   : số tầng hầm
    nguoi : số người / chỗ ngồi
    chau  : số cháu (mầm non)
    binhPerFloor (tùy chọn): m² / 1 bình ABC mỗi tầng (mặc định 100)
    binhReserve  (tùy chọn): % dự phòng số bình (mặc định 10)
"""

from math import ceil


def _R(req: bool, basis: str) -> dict:
    """Trả kết quả tra cứu: {req: bool, basis: str}."""
    return {"req": bool(req), "basis": basis}


# =====================================================================
# BẢNG A.1 — Yêu cầu BÁO CHÁY TỰ ĐỘNG (bc) và CHỮA CHÁY TỰ ĐỘNG (cc)
# =====================================================================
# Mỗi công năng:
#   k     : mã (slug)
#   t     : tên hiển thị
#   muc   : số mục trong Bảng A.1
#   bc(i) : có cần báo cháy tự động? -> dict {req, basis}
#   cc(i) : có cần chữa cháy tự động? -> dict {req, basis}
#   nguoi (tùy chọn): True nếu công năng phụ thuộc số người
#   chau  (tùy chọn): True nếu công năng phụ thuộc số cháu (mầm non)

CONG_NANG_LIST = [
    {"k": "nha_o_kd", "t": "Nhà ở riêng lẻ kết hợp KD dịch vụ (KD < 30% sàn)", "muc": 1,
     "bc": lambda i: _R(i["tang"] >= 7, "≥ 7 tầng"),
     "cc": lambda i: _R(i["cao"] >= 30, "chiều cao PCCC ≥ 30 m")},

    {"k": "nha_o_sxkd", "t": "Nhà ở riêng lẻ kết hợp SX-KD hàng dễ cháy (< 30% sàn)", "muc": 2,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 500, "≥ 3 tầng hoặc sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 30, "chiều cao PCCC ≥ 30 m")},

    {"k": "chung_cu", "t": "Chung cư, nhà ở tập thể, ký túc xá", "muc": 3,
     "bc": lambda i: _R(i["tang"] >= 5 or i["dt"] >= 700, "≥ 5 tầng hoặc sàn ≥ 700 m²"),
     "cc": lambda i: _R(i["cao"] >= 30, "chiều cao PCCC ≥ 30 m")},

    {"k": "mam_non", "t": "Nhà trẻ, mẫu giáo, mầm non", "muc": 4, "chau": True,
     "bc": lambda i: _R(i["chau"] >= 100 or i["dt"] >= 300, "≥ 100 cháu hoặc sàn ≥ 300 m²"),
     "cc": lambda i: _R(i["tang"] >= 4 and i["dt"] >= 5000, "≥ 4 tầng VÀ sàn ≥ 5.000 m²")},

    {"k": "truong_hoc", "t": "Trường tiểu học/THCS/THPT/ĐH/CĐ/dạy nghề; bảo trợ XH", "muc": 5,
     "bc": lambda i: _R(i["tang"] >= 5 or i["dt"] >= 1500, "≥ 5 tầng hoặc sàn ≥ 1.500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25, "chiều cao PCCC ≥ 25 m")},

    {"k": "benh_vien", "t": "Bệnh viện, phòng khám, trạm y tế, điều dưỡng", "muc": 6, "nguoi": True,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 300, "≥ 3 tầng hoặc sàn ≥ 300 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 2000, "≥ 25 m hoặc sàn ≥ 2.000 m²")},

    {"k": "duong_lao", "t": "Nhà dưỡng lão", "muc": 7, "nguoi": True,
     "bc": lambda i: _R(True, "không phụ thuộc diện tích"),
     "cc": lambda i: _R(i["dt"] >= 500, "sàn ≥ 500 m²")},

    {"k": "the_thao", "t": "Nhà thi đấu, tập luyện thể thao", "muc": 8, "nguoi": True,
     "bc": lambda i: _R(i["dt"] >= 500 or i["nguoi"] >= 200, "sàn ≥ 500 m² hoặc khán đài ≥ 200 chỗ"),
     "cc": lambda i: _R(i["cao"] >= 25, "chiều cao PCCC ≥ 25 m")},

    {"k": "nha_hat", "t": "Nhà hát, rạp chiếu phim, rạp xiếc", "muc": 9, "nguoi": True,
     "bc": lambda i: _R(i["dt"] >= 500 or i["nguoi"] >= 200, "sàn ≥ 500 m² hoặc ≥ 200 chỗ"),
     "cc": lambda i: _R(i["cao"] >= 25, "chiều cao PCCC ≥ 25 m")},

    {"k": "thu_vien", "t": "Thư viện", "muc": 10,
     "bc": lambda i: _R(i["dt"] >= 300, "sàn ≥ 300 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "bao_tang", "t": "Bảo tàng, nhà triển lãm, nhà trưng bày", "muc": 11,
     "bc": lambda i: (_R(True, "có tầng hầm → không phụ thuộc diện tích") if i["ham"] > 0
                     else _R(True, "≥ 3 tầng → không phụ thuộc diện tích") if i["tang"] >= 3
                     else _R(i["dt"] >= 500, "1-2 tầng: sàn ≥ 500 m²")),
     "cc": lambda i: (_R(i["dt"] >= 200, "tầng hầm: sàn ≥ 200 m²") if i["ham"] > 0
                     else _R(i["dt"] >= 500, "≥ 3 tầng: sàn ≥ 500 m²") if i["tang"] >= 3
                     else _R(i["dt"] >= 1000, "1-2 tầng: sàn ≥ 1.000 m²"))},

    {"k": "nha_van_hoa", "t": "Nhà văn hóa, trung tâm hội nghị, nhà đa năng", "muc": 12,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 500, "≥ 3 tầng hoặc sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "karaoke", "t": "Karaoke, vũ trường", "muc": 13, "nguoi": True,
     "bc": lambda i: _R(True, "không phụ thuộc diện tích"),
     "cc": lambda i: (_R(True, "tầng hầm hoặc ≥ 3 tầng → không phụ thuộc diện tích")
                     if (i["ham"] > 0 or i["tang"] >= 3)
                     else _R(i["dt"] >= 500, "1-2 tầng: sàn ≥ 500 m²"))},

    {"k": "ton_giao", "t": "Cơ sở tôn giáo, tín ngưỡng; di tích cấp tỉnh+", "muc": 14,
     "bc": lambda i: _R(i["tang"] >= 4, "≥ 4 tầng"),
     "cc": lambda i: _R(i["cao"] >= 25, "chiều cao PCCC ≥ 25 m")},

    {"k": "cho_tttm", "t": "Chợ, trung tâm thương mại, siêu thị", "muc": 15,
     "bc": lambda i: _R(True, "không phụ thuộc diện tích"),
     "cc": lambda i: (_R(i["dt"] >= 200, "tầng hầm: sàn ≥ 200 m²") if i["ham"] > 0
                     else _R(True, "≥ 3 tầng → không phụ thuộc diện tích") if i["tang"] >= 3
                     else _R(i["dt"] >= 3500, "1-2 tầng: sàn ≥ 3.500 m²"))},

    {"k": "nha_hang", "t": "Nhà hàng/ăn uống; thủy cung; vui chơi giải trí; biểu diễn", "muc": 16,
     "bc": lambda i: _R(i["dt"] >= 500, "sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "cua_hang", "t": "Cửa hàng điện máy/bách hóa/tiện ích/hàng dễ cháy", "muc": 17,
     "bc": lambda i: (_R(True, "tầng hầm → không phụ thuộc diện tích") if i["ham"] > 0
                     else _R(i["tang"] >= 3 or i["dt"] >= 300, "trên mặt đất: ≥ 3 tầng hoặc sàn ≥ 300 m²")),
     "cc": lambda i: (_R(i["dt"] >= 200, "tầng hầm: sàn ≥ 200 m²") if i["ham"] > 0
                     else _R(i["cao"] >= 25 or i["dt"] >= 3500, "≥ 25 m hoặc sàn ≥ 3.500 m²"))},

    {"k": "kd_chat_long", "t": "Nhà kinh doanh chất lỏng cháy & dễ cháy", "muc": 18,
     "bc": lambda i: _R(True, "không phụ thuộc diện tích"),
     "cc": lambda i: _R(True, "không phụ thuộc diện tích")},

    {"k": "khach_san", "t": "Khách sạn, nhà khách, nhà nghỉ, lưu trú", "muc": 19,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 700, "≥ 3 tầng hoặc sàn ≥ 700 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "buu_dien", "t": "Bưu điện, bưu cục, bưu chính viễn thông", "muc": 20,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 500, "≥ 3 tầng hoặc sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "van_phong", "t": "Trụ sở, văn phòng làm việc; nghiên cứu chuyên ngành", "muc": 21,
     "bc": lambda i: _R(i["tang"] >= 5 or i["dt"] >= 500, "≥ 5 tầng hoặc sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "nha_hon_hop", "t": "Nhà hỗn hợp, chung cư sử dụng hỗn hợp", "muc": 22,
     "bc": lambda i: _R(i["tang"] >= 3 or i["dt"] >= 500, "≥ 3 tầng hoặc sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 5000, "≥ 25 m hoặc sàn ≥ 5.000 m²")},

    {"k": "nha_ga", "t": "Nhà ga (hàng không/đường sắt/cáp treo); nhà dịch vụ cảng-bến", "muc": 23,
     "bc": lambda i: _R(i["dt"] >= 500, "sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["cao"] >= 25 or i["dt"] >= 10000, "≥ 25 m hoặc sàn ≥ 10.000 m²")},

    {"k": "nha_de_xe", "t": "Nhà để xe ô tô, xe máy", "muc": 24,
     "bc": lambda i: (_R(True, "dạng kín tầng hầm hoặc ≥ 2 tầng") if (i["ham"] > 0 or i["tang"] >= 2)
                     else _R(False, "1 tầng trên mặt đất: xem chú thích bậc chịu lửa")),
     "cc": lambda i: (_R(True, "dạng kín tầng hầm hoặc ≥ 2 tầng") if (i["ham"] > 0 or i["tang"] >= 2)
                     else _R(i["dt"] >= 3600, "1 tầng: tùy bậc chịu lửa (mặc định ≥ 3.600 m²)"))},

    {"k": "nong_san", "t": "Nhà chế biến, lưu trữ nông sản dạng hạt", "muc": 25, "nguoi": True,
     "bc": lambda i: _R(i["dt"] >= 500, "sàn ≥ 500 m²"),
     "cc": lambda i: _R(i["dt"] >= 3000, "sàn ≥ 3.000 m²")},

    {"k": "kho_bc", "t": "Nhà kho hạng C giá đỡ cao > 5,5 m; kho B,C ≥ 2 tầng", "muc": 26,
     "bc": lambda i: _R(True, "không phụ thuộc diện tích"),
     "cc": lambda i: _R(True, "không phụ thuộc diện tích")},
]


def get_cong_nang(k: str) -> dict:
    """Tra cứu 1 công năng theo mã. Trả None nếu không có."""
    for cn in CONG_NANG_LIST:
        if cn["k"] == k:
            return cn
    return None


# =====================================================================
# NGHỊ ĐỊNH 105/2025/NĐ-CP — Phân loại Phụ lục I/II
# Phụ lục I: 34 mục cơ sở thuộc diện quản lý PCCC
# Phụ lục II: 47 mục cơ sở có nguy hiểm cháy nổ (Nhóm 1 / Nhóm 2)
# =====================================================================

# Mapping 26 công năng app (QCVN 10:2025) → Phụ lục I/II NĐ 105
# Cấu trúc:
#   "cn_k": {
#       "pl1_muc": int,                  # mục trong PL I
#       "pl1_in": lambda i → bool,        # có thuộc PL I không
#       "pl2_muc": int,                  # mục trong PL II (nếu có)
#       "pl2_nhom1": lambda i → bool,    # Nhóm 1 nếu True
#       "pl2_nhom2": lambda i → bool,    # Nhóm 2 nếu True
#       "ten_pl1": str,                  # tên mục trong PL I
#       "ten_pl2": str,                  # tên mục trong PL II
#   }
_PL_ND105 = {
    "nha_o_kd": {
        "pl1_muc": 32, "ten_pl1": "Nhà ở kết hợp SX, KD",
        "pl1_in": lambda i: i.get("dt_kd", i["dt"] * 0.3) >= 50,
        "pl2_muc": 46, "ten_pl2": "Nhà ở kết hợp SX, KD",
        "pl2_nhom1": lambda i: False,  # PL II mục 46 chỉ có Nhóm 2
        "pl2_nhom2": lambda i: i.get("dt_kd", i["dt"] * 0.3) >= 200,
    },
    "nha_o_sxkd": {
        "pl1_muc": 32, "ten_pl1": "Nhà ở kết hợp SX, KD",
        "pl1_in": lambda i: i.get("dt_kd", i["dt"] * 0.3) >= 50,
        "pl2_muc": 46, "ten_pl2": "Nhà ở kết hợp SX, KD",
        "pl2_nhom1": lambda i: False,
        "pl2_nhom2": lambda i: i.get("dt_kd", i["dt"] * 0.3) >= 200,
    },
    "chung_cu": {
        "pl1_muc": 1, "ten_pl1": "Nhà chung cư, nhà ở tập thể",
        "pl1_in": lambda i: True,
        "pl2_muc": 1, "ten_pl2": "Nhà chung cư, nhà ở tập thể",
        "pl2_nhom1": lambda i: i["tang"] >= 7 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (5 <= i["tang"] <= 6) or (1000 <= i["dt"] < 3000),
    },
    "mam_non": {
        "pl1_muc": 2, "ten_pl1": "Nhà trẻ, mẫu giáo, mầm non",
        "pl1_in": lambda i: True,
        "pl2_muc": 2, "ten_pl2": "Nhà trẻ, mẫu giáo, mầm non",
        "pl2_nhom1": lambda i: i.get("chau", 0) >= 150 or i["dt"] >= 2000,
        "pl2_nhom2": lambda i: (50 <= i.get("chau", 0) < 150) or (500 <= i["dt"] < 2000),
    },
    "truong_hoc": {
        "pl1_muc": 2, "ten_pl1": "Trường tiểu học/THCS/THPT/ĐH/CĐ/dạy nghề",
        "pl1_in": lambda i: True,
        "pl2_muc": 3, "ten_pl2": "Trường tiểu học/THCS/THPT/ĐH/CĐ + CS nghiên cứu",
        "pl2_nhom1": lambda i: i["tang"] >= 5 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 5) or (1500 <= i["dt"] < 3000),
    },
    "benh_vien": {
        "pl1_muc": 4, "ten_pl1": "Bệnh viện, phòng khám, trạm y tế",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 50,
        "pl2_muc": 5, "ten_pl2": "Phòng khám, trạm y tế, dưỡng lão",
        "pl2_nhom1": lambda i: (i.get("nguoi", 0) >= 250  # BV ≥ 250 giường
                                or i["tang"] >= 5 or i["dt"] >= 2000),
        "pl2_nhom2": lambda i: ((3 <= i["tang"] < 5) or (300 <= i["dt"] < 2000)),
    },
    "duong_lao": {
        "pl1_muc": 31, "ten_pl1": "Cơ sở trợ giúp xã hội",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 100,
        "pl2_muc": 45, "ten_pl2": "Cơ sở trợ giúp xã hội",
        "pl2_nhom1": lambda i: i["tang"] >= 3 or i["dt"] >= 300,
        "pl2_nhom2": lambda i: False,
    },
    "the_thao": {
        "pl1_muc": 5, "ten_pl1": "Sân vận động, nhà thi đấu, thể thao",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 50,
        "pl2_muc": 7, "ten_pl2": "Nhà thi đấu, bể bơi, sân thi đấu",
        "pl2_nhom1": lambda i: i.get("nguoi", 0) >= 5000 or i["dt"] >= 5000,
        "pl2_nhom2": lambda i: ((1000 <= i.get("nguoi", 0) < 5000)
                                or (1000 <= i["dt"] < 5000)),
    },
    "nha_hat": {
        "pl1_muc": 6, "ten_pl1": "Nhà hát, rạp chiếu phim, rạp xiếc",
        "pl1_in": lambda i: True,
        "pl2_muc": 8, "ten_pl2": "Nhà hát, rạp chiếu phim, rạp xiếc",
        "pl2_nhom1": lambda i: i.get("nguoi", 0) >= 300,
        "pl2_nhom2": lambda i: i.get("nguoi", 0) > 0 and i.get("nguoi", 0) < 300,
    },
    "thu_vien": {
        "pl1_muc": 7, "ten_pl1": "TT hội nghị, bảo tàng, thư viện, nhà văn hoá",
        "pl1_in": lambda i: i.get("nguoi", 0) >= 100,
        "pl2_muc": 9, "ten_pl2": "TT hội nghị, bảo tàng, thư viện, nhà trưng bày",
        "pl2_nhom1": lambda i: i["tang"] >= 5 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 5) or (500 <= i["dt"] < 3000),
    },
    "bao_tang": {
        "pl1_muc": 7, "ten_pl1": "Bảo tàng, nhà trưng bày, nhà triển lãm",
        "pl1_in": lambda i: i.get("nguoi", 0) >= 100,
        "pl2_muc": 9, "ten_pl2": "Bảo tàng, nhà trưng bày, nhà triển lãm",
        "pl2_nhom1": lambda i: i["tang"] >= 5 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 5) or (500 <= i["dt"] < 3000),
    },
    "nha_van_hoa": {
        "pl1_muc": 7, "ten_pl1": "TT hội nghị, nhà văn hoá, nhà đa năng",
        "pl1_in": lambda i: i.get("nguoi", 0) >= 100,
        "pl2_muc": 9, "ten_pl2": "TT hội nghị, nhà văn hoá",
        "pl2_nhom1": lambda i: i["tang"] >= 5 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 5) or (500 <= i["dt"] < 3000),
    },
    "karaoke": {
        "pl1_muc": 8, "ten_pl1": "Thủy cung, karaoke, vũ trường, vui chơi giải trí",
        "pl1_in": lambda i: i["dt"] >= 50,
        "pl2_muc": 10, "ten_pl2": "Thủy cung, karaoke, vũ trường",
        "pl2_nhom1": lambda i: i["tang"] >= 4 or i["dt"] >= 1000,
        "pl2_nhom2": lambda i: (2 <= i["tang"] < 4) or (300 <= i["dt"] < 1000),
    },
    "ton_giao": {
        "pl1_muc": 9, "ten_pl1": "Cơ sở tôn giáo, tín ngưỡng; di tích cấp tỉnh+",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 100,
        "pl2_muc": 11, "ten_pl2": "Cơ sở tôn giáo, tín ngưỡng",
        "pl2_nhom1": lambda i: i["dt"] >= 3000,
        "pl2_nhom2": lambda i: 500 <= i["dt"] < 3000,
    },
    "cho_tttm": {
        "pl1_muc": 10, "ten_pl1": "Chợ, trung tâm thương mại, siêu thị",
        "pl1_in": lambda i: True,
        "pl2_muc": 13, "ten_pl2": "Chợ, trung tâm thương mại, siêu thị",
        "pl2_nhom1": lambda i: i["dt"] >= 2000,
        "pl2_nhom2": lambda i: 300 <= i["dt"] < 2000,
    },
    "nha_hang": {
        "pl1_muc": 11, "ten_pl1": "Cơ sở KD ăn uống, dịch vụ khác",
        "pl1_in": lambda i: i["dt"] >= 100,
        "pl2_muc": 14, "ten_pl2": "Cơ sở KD ăn uống, dịch vụ khác",
        "pl2_nhom1": lambda i: i["dt"] >= 3000,
        "pl2_nhom2": lambda i: 300 <= i["dt"] < 3000,
    },
    "cua_hang": {
        "pl1_muc": 12, "ten_pl1": "Cửa hàng kinh doanh hàng dễ cháy",
        "pl1_in": lambda i: i["dt"] >= 30,  # hàng dễ cháy → ngưỡng 30m²
        "pl2_muc": 15, "ten_pl2": "Cơ sở KD hàng hoá dễ cháy",
        "pl2_nhom1": lambda i: i["dt"] >= 3000,
        "pl2_nhom2": lambda i: 200 <= i["dt"] < 3000,
    },
    "kd_chat_long": {
        "pl1_muc": 13, "ten_pl1": "KD khí đốt; cửa hàng xăng dầu",
        "pl1_in": lambda i: True,
        "pl2_muc": 18, "ten_pl2": "Cửa hàng xăng dầu",
        "pl2_nhom1": lambda i: True,  # cửa hàng xăng dầu: mọi quy mô
        "pl2_nhom2": lambda i: False,
    },
    "khach_san": {
        "pl1_muc": 14, "ten_pl1": "Khách sạn, nhà nghỉ, nhà khách, lưu trú",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 50,
        "pl2_muc": 19, "ten_pl2": "Khách sạn, nhà nghỉ, nhà khách, lưu trú",
        "pl2_nhom1": lambda i: i["tang"] >= 7 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 7) or (500 <= i["dt"] < 3000),
    },
    "buu_dien": {
        "pl1_muc": 15, "ten_pl1": "Bưu điện, bưu cục, viễn thông",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 100,
        "pl2_muc": 20, "ten_pl2": "Bưu điện, bưu cục, viễn thông",
        "pl2_nhom1": lambda i: i["tang"] >= 7 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 7) or (500 <= i["dt"] < 3000),
    },
    "van_phong": {
        "pl1_muc": 16, "ten_pl1": "Trụ sở, văn phòng làm việc",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 100,
        "pl2_muc": 21, "ten_pl2": "Trụ sở, văn phòng làm việc",
        "pl2_nhom1": lambda i: i["tang"] >= 7 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 7) or (500 <= i["dt"] < 3000),
    },
    "nha_hon_hop": {
        "pl1_muc": 17, "ten_pl1": "Nhà đa năng, nhà hỗn hợp",
        "pl1_in": lambda i: i["tang"] >= 2 or i["dt"] >= 100,
        "pl2_muc": 22, "ten_pl2": "Nhà đa năng, nhà hỗn hợp",
        "pl2_nhom1": lambda i: i["tang"] >= 7 or i["dt"] >= 3000,
        "pl2_nhom2": lambda i: (3 <= i["tang"] < 7) or (500 <= i["dt"] < 3000),
    },
    "nha_ga": {
        "pl1_muc": 25, "ten_pl1": "Nhà ga hành khách / hàng hoá",
        "pl1_in": lambda i: i["dt"] >= 500,
        "pl2_muc": 35, "ten_pl2": "Nhà ga hàng không / đường sắt",
        "pl2_nhom1": lambda i: True,  # nhà ga: mọi quy mô (mục 35 PL II)
        "pl2_nhom2": lambda i: False,
    },
    "nha_de_xe": {
        "pl1_muc": 23, "ten_pl1": "Nhà để xe ô tô, xe máy",
        "pl1_in": lambda i: i["dt"] >= 100,
        "pl2_muc": 33, "ten_pl2": "Nhà để xe ô tô, xe máy",
        "pl2_nhom1": lambda i: i["dt"] >= 2000,
        "pl2_nhom2": lambda i: 500 <= i["dt"] < 2000,
    },
    "nong_san": {
        "pl1_muc": 22, "ten_pl1": "Kho chứa hàng (hạng D, E)",
        "pl1_in": lambda i: (i["dt"] * (i.get("cao") or 3.5) >= 2500) or i["dt"] >= 500,
        "pl2_muc": 32, "ten_pl2": "Kho chứa hàng (hạng D, E)",
        "pl2_nhom1": lambda i: False,
        "pl2_nhom2": lambda i: (i["dt"] * (i.get("cao") or 3.5) >= 5000) or i["dt"] >= 1000,
    },
    "kho_bc": {
        "pl1_muc": 22, "ten_pl1": "Kho chứa hàng (hạng A, B, C)",
        "pl1_in": lambda i: (i["dt"] * (i.get("cao") or 3.5) >= 2500) or i["dt"] >= 500,
        "pl2_muc": 30, "ten_pl2": "Kho chứa hàng nguy hiểm cháy nổ A, B, C",
        "pl2_nhom1": lambda i: i["dt"] >= 2000,
        "pl2_nhom2": lambda i: 200 <= i["dt"] < 2000,
    },
}


def tra_phu_luc_nd105(cn_k: str, i: dict) -> dict:
    """Phân loại cơ sở theo Nghị định 105/2025/NĐ-CP.

    Args:
        cn_k: mã công năng (chung_cu, khach_san, nha_hat...)
        i: dict input gồm dt, cao, tang, ham, nguoi, chau...

    Returns: dict {
        thuoc_pl1: bool,
        thuoc_pl2: bool,
        nhom_pl2: 1 / 2 / None,
        pl1_muc, pl1_ten_muc, pl1_ly_do,
        pl2_muc, pl2_ten_muc, pl2_ly_do,
        tan_suat_tu_kiem_tra: "6 tháng/lần" / "1 năm/lần",
        tan_suat_co_quan_kiem_tra: "1 năm/lần" / "2 năm/lần" / "Không định kỳ",
        co_quan_kiem_tra: "Công an / UBND xã / Cơ quan xây dựng",
        bao_hiem_chay_no_bat_buoc: bool,
        nguon: str (citation),
    }
    """
    m = _PL_ND105.get(cn_k)
    if not m:
        # Fallback: không có mapping → giả định thuộc PL I, không thuộc PL II
        return {
            "thuoc_pl1": True,
            "thuoc_pl2": False,
            "nhom_pl2": None,
            "pl1_muc": None, "pl1_ten_muc": "(chưa map)", "pl1_ly_do": "công năng chưa có mapping NĐ 105",
            "pl2_muc": None, "pl2_ten_muc": "-", "pl2_ly_do": "-",
            "tan_suat_tu_kiem_tra": "1 năm/lần",
            "tan_suat_co_quan_kiem_tra": "Không định kỳ",
            "co_quan_kiem_tra": "UBND cấp xã hoặc cơ quan có thẩm quyền",
            "bao_hiem_chay_no_bat_buoc": False,
            "nguon": "NĐ 105/2025/NĐ-CP — fallback (cần kiểm tra thủ công)",
        }

    # Đánh giá PL I
    thuoc_pl1 = bool(m["pl1_in"](i))
    pl1_ly_do = m["ten_pl1"] if thuoc_pl1 else "không đạt ngưỡng PL I"

    # Đánh giá PL II
    is_nhom1 = bool(m["pl2_nhom1"](i))
    is_nhom2 = bool(m["pl2_nhom2"](i))
    if is_nhom1:
        nhom_pl2 = 1
        thuoc_pl2 = True
        pl2_ly_do = f"Nhóm 1: {m['ten_pl2']}"
    elif is_nhom2:
        nhom_pl2 = 2
        thuoc_pl2 = True
        pl2_ly_do = f"Nhóm 2: {m['ten_pl2']}"
    else:
        nhom_pl2 = None
        thuoc_pl2 = False
        pl2_ly_do = "không đạt ngưỡng PL II"

    # Tần suất kiểm tra (Điều 13, 14 NĐ 105)
    if thuoc_pl2:
        tan_suat_tu_kt = "6 tháng/lần"
        if nhom_pl2 == 1:
            tan_suat_cq_kt = "1 năm/lần"
        else:
            tan_suat_cq_kt = "2 năm/lần"
        cq_kt = "Công an theo phân cấp HOẶC cơ quan chuyên môn về xây dựng"
        bao_hiem = True  # PL II → bắt buộc bảo hiểm cháy nổ
    elif thuoc_pl1:
        tan_suat_tu_kt = "1 năm/lần"
        tan_suat_cq_kt = "Theo yêu cầu (không định kỳ bắt buộc)"
        cq_kt = "UBND cấp xã hoặc cơ quan Công an theo phân cấp"
        bao_hiem = False
    else:
        tan_suat_tu_kt = "Không bắt buộc"
        tan_suat_cq_kt = "Không bắt buộc"
        cq_kt = "-"
        bao_hiem = False

    return {
        "thuoc_pl1": thuoc_pl1,
        "thuoc_pl2": thuoc_pl2,
        "nhom_pl2": nhom_pl2,
        "pl1_muc": m["pl1_muc"], "pl1_ten_muc": m["ten_pl1"], "pl1_ly_do": pl1_ly_do,
        "pl2_muc": m["pl2_muc"], "pl2_ten_muc": m["ten_pl2"], "pl2_ly_do": pl2_ly_do,
        "tan_suat_tu_kiem_tra": tan_suat_tu_kt,
        "tan_suat_co_quan_kiem_tra": tan_suat_cq_kt,
        "co_quan_kiem_tra": cq_kt,
        "bao_hiem_chay_no_bat_buoc": bao_hiem,
        "nguon": (f"NĐ 105/2025/NĐ-CP "
                  f"(PL I mục {m['pl1_muc']}, PL II mục {m['pl2_muc']}, "
                  f"Điều 13 + 14)"),
    }


# =====================================================================
# NĐ 105/2025 Điều 4 — 14 tài liệu trong hồ sơ PCCC của cơ sở
# =====================================================================

# Link tải mẫu chính thức từ Thư viện Pháp luật / cổng chính phủ
_LINKS_MAU = {
    "PC01": "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/bieu-mau/85219/tai-ve-phu-luc-nghi-dinh-105-2025-nd-cp-ve-phong-chay-chua-chay-cuu-nan-cuu-ho",
    "PC02": "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/bieu-mau/85219/tai-ve-phu-luc-nghi-dinh-105-2025-nd-cp-ve-phong-chay-chua-chay-cuu-nan-cuu-ho",
    "PC04": "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/bieu-mau/85219/tai-ve-phu-luc-nghi-dinh-105-2025-nd-cp-ve-phong-chay-chua-chay-cuu-nan-cuu-ho",
    "PC06": "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/bieu-mau/85219/tai-ve-phu-luc-nghi-dinh-105-2025-nd-cp-ve-phong-chay-chua-chay-cuu-nan-cuu-ho",
    "ND105_TOAN_VAN": "https://vanban.chinhphu.vn/?pageid=27160&docid=213702",
}


def links_mau_pccc() -> dict:
    """Trả dict tên_mẫu → URL tải mẫu chính thức."""
    return dict(_LINKS_MAU)


def danh_sach_ho_so_pccc(phan_loai: dict = None) -> list:
    """Trả danh sách 14 tài liệu hồ sơ PCCC theo Điều 4 NĐ 105/2025.

    Args:
        phan_loai: dict kết quả từ tra_phu_luc_nd105 (optional)
                   - dùng để đánh dấu mục nào BẮT BUỘC, mục nào tùy chọn

    Returns: list[dict {so, ten, mau, bat_buoc, ghi_chu, luu_5_nam}]
    """
    if phan_loai is None:
        phan_loai = {}
    thuoc_pl1 = phan_loai.get("thuoc_pl1", True)
    thuoc_pl2 = phan_loai.get("thuoc_pl2", False)
    bh = phan_loai.get("bao_hiem_chay_no_bat_buoc", False)

    return [
        {
            "so": 1,
            "ten": "Phiếu thông tin cơ sở",
            "mau": "PC01",
            "bat_buoc": True,
            "ghi_chu": "Khai báo lần đầu + cập nhật khi có thay đổi",
            "luu_5_nam": False,
        },
        {
            "so": 2,
            "ten": "Nội quy phòng cháy, chữa cháy, cứu nạn, cứu hộ",
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": "Niêm yết tại nơi dễ thấy trong cơ sở",
            "luu_5_nam": False,
        },
        {
            "so": 3,
            "ten": "Văn bản thẩm duyệt thiết kế PCCC + chấp thuận nghiệm thu",
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": ("Đối với công trình thuộc diện thẩm duyệt. "
                        "Tham khảo Phụ lục III NĐ 105"),
            "luu_5_nam": False,
        },
        {
            "so": 4,
            "ten": ("Quyết định thành lập Đội PCCC + Phân công người PCCC "
                    "+ Thông báo kết quả huấn luyện nghiệp vụ"),
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": "Huấn luyện nghiệp vụ cho người thực hiện PCCC",
            "luu_5_nam": False,
        },
        {
            "so": 5,
            "ten": "Phương án chữa cháy, cứu nạn, cứu hộ",
            "mau": "PC06",
            "bat_buoc": True,
            "ghi_chu": "Diễn tập tối thiểu 1 lần/năm",
            "luu_5_nam": False,
        },
        {
            "so": 6,
            "ten": "Sổ theo dõi phương tiện PCCC",
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": "Theo quy định Bộ Công an. Cập nhật khi bảo dưỡng/kiểm định",
            "luu_5_nam": False,
        },
        {
            "so": 7,
            "ten": "Biên bản tự kiểm tra PCCC",
            "mau": "PC02",
            "bat_buoc": True,
            "ghi_chu": ("Tự kiểm tra: " + phan_loai.get("tan_suat_tu_kiem_tra", "1 năm/lần")),
            "luu_5_nam": True,
        },
        {
            "so": 8,
            "ten": "Báo cáo kết quả thực hiện công tác PCCC",
            "mau": "PC04",
            "bat_buoc": True,
            "ghi_chu": "Gửi trước 15/6 và 15/12 hàng năm",
            "luu_5_nam": True,
        },
        {
            "so": 9,
            "ten": "Giấy Chứng nhận bảo hiểm cháy nổ bắt buộc",
            "mau": None,
            "bat_buoc": bh,  # chỉ bắt buộc nếu thuộc PL II
            "ghi_chu": ("BẮT BUỘC với cơ sở thuộc Phụ lục II NĐ 105/2025"
                        if bh else "Không bắt buộc (chỉ thuộc PL I)"),
            "luu_5_nam": True,
        },
        {
            "so": 10,
            "ten": "Bản vẽ hoàn công hệ thống, hạng mục liên quan đến PCCC",
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": "Đối với công trình thuộc diện thẩm định thiết kế PCCC",
            "luu_5_nam": False,
        },
        {
            "so": 11,
            "ten": "Thông báo xác minh, giải quyết vụ cháy của cơ quan Công an",
            "mau": None,
            "bat_buoc": False,
            "ghi_chu": "Nếu có vụ cháy xảy ra",
            "luu_5_nam": True,
        },
        {
            "so": 12,
            "ten": "Biên bản kiểm tra của UBND xã / Công an / Cơ quan xây dựng",
            "mau": None,
            "bat_buoc": True,
            "ghi_chu": ("Cơ quan kiểm tra: " + phan_loai.get("co_quan_kiem_tra", "-")),
            "luu_5_nam": False,
        },
        {
            "so": 13,
            "ten": ("Biên bản vi phạm hành chính / QĐ xử phạt / QĐ đình chỉ-phục hồi"
                    " / Kiến nghị PCCC"),
            "mau": None,
            "bat_buoc": False,
            "ghi_chu": "Nếu có vi phạm hoặc kiến nghị",
            "luu_5_nam": True,
        },
        {
            "so": 14,
            "ten": "Văn bản phân công người thực hiện kiểm tra PCCC tại cơ sở",
            "mau": None,
            "bat_buoc": False,
            "ghi_chu": "Nếu có (đối với cơ sở quy mô lớn)",
            "luu_5_nam": False,
        },
    ]


# =====================================================================
# Điều kiện CHO PHÉP dùng thiết bị BÁO CHÁY ĐỘC LẬP thay hệ thống tự động
# (QCVN 10, Bảng A.1 — chú thích về quy mô nhỏ)
# =====================================================================
DOC_LAP_COND = {
    "nha_o_kd":     lambda i: True,
    "nha_o_sxkd":   lambda i: i["tang"] < 5 and i["dt"] < 500,
    "chung_cu":     lambda i: i["tang"] < 5 and i["dt"] < 1500,
    "mam_non":      lambda i: i["dt"] < 500,
    "truong_hoc":   lambda i: i["dt"] < 700,
    "duong_lao":    lambda i: i["tang"] < 3 and i["dt"] < 300,
    "the_thao":     lambda i: i["dt"] < 1500,
    "nha_hat":      lambda i: i["dt"] < 1500,
    "thu_vien":     lambda i: i["dt"] < 500,
    "nha_hang":     lambda i: i["tang"] < 3 and i["dt"] < 1500,
    "cua_hang":     lambda i: i["tang"] < 5 and i["dt"] < 500,
    "khach_san":    lambda i: i["tang"] < 5 and i["dt"] < 1500,
    "van_phong":    lambda i: i["tang"] < 5 and i["dt"] < 1500,
    "nha_hon_hop":  lambda i: i["tang"] < 5 and i["dt"] < 500,
    "nha_ga":       lambda i: i["tang"] < 3 and i["dt"] < 500,
}


def cho_phep_doc_lap(k: str, i: dict) -> bool:
    """Có được phép dùng thiết bị báo cháy độc lập thay hệ thống tự động?"""
    f = DOC_LAP_COND.get(k)
    return bool(f(i)) if f else False


# =====================================================================
# HỆ THỐNG BỔ TRỢ — họng nước (B.1), loa (G.1), phá dỡ (E.1), mặt nạ (F.1)
# =====================================================================
def he_thong_bo_tro(cn: dict, i: dict) -> list:
    """Trả danh sách hệ thống bổ trợ bắt buộc. Mỗi item: dict {ht, dk, can, nhom}."""
    out = []
    k = cn["k"]

    # --- Họng nước trong nhà (Bảng B.1) ---
    hn = None
    if k in ("chung_cu", "khach_san"):
        if i["tang"] >= 5 or i["dt"] >= 1500:
            hn = "≥ 5 tầng hoặc sàn ≥ 1.500 m²"
    elif k == "mam_non":
        if i["chau"] >= 100 or i["tang"] >= 3 or i["dt"] >= 1000:
            hn = "≥ 100 cháu hoặc ≥ 3 tầng hoặc sàn ≥ 1.000 m²"
    elif k in ("van_phong", "buu_dien", "nha_hang", "nha_ga"):
        if i["tang"] >= 6 or i["dt"] >= 1500:
            hn = "≥ 6 tầng hoặc sàn ≥ 1.500 m²"
    elif k == "nha_hat":
        if i["nguoi"] >= 300 or i["dt"] >= 1000:
            hn = "≥ 300 chỗ hoặc sàn ≥ 1.000 m²"
    elif k == "truong_hoc":
        if i["tang"] >= 3 or i["dt"] >= 600:
            hn = "≥ 3 tầng hoặc sàn ≥ 600 m²"
    elif k in ("bao_tang", "the_thao", "ton_giao"):
        if i["tang"] >= 6 or i["dt"] >= 1500:
            hn = "≥ 6 tầng hoặc sàn ≥ 1.500 m²"
    elif k == "cho_tttm":
        hn = "không phụ thuộc diện tích"
    elif k in ("thu_vien", "nha_van_hoa"):
        if i["dt"] >= 1500:
            hn = "sàn ≥ 1.500 m²"
    if hn:
        out.append({"ht": "Hệ thống họng nước chữa cháy trong nhà",
                    "dk": hn, "can": "QCVN 10, Phụ lục B (Bảng B.1)", "nhom": "hong_nuoc"})

    # --- Loa thông báo & hướng dẫn thoát nạn (Bảng G.1) ---
    loa = None
    cong_cong = {"chung_cu", "mam_non", "truong_hoc", "benh_vien", "duong_lao",
                 "the_thao", "nha_hat", "thu_vien", "bao_tang", "nha_van_hoa",
                 "karaoke", "ton_giao", "cho_tttm", "nha_hang", "cua_hang",
                 "khach_san", "buu_dien", "van_phong", "nha_hon_hop"}
    if k == "nha_ga":
        loa = "nhà ga hành khách — không phụ thuộc quy mô (mục 6)"
    elif k == "nha_de_xe":
        if i["dt"] >= 18000:
            loa = "nhà để xe kín, tổng diện tích sàn ≥ 18.000 m² (mục 3)"
    elif k == "nong_san":
        if i["dt"] >= 18000 and i["nguoi"] >= 300:
            loa = "nhà sản xuất ≥ 18.000 m² và ≥ 300 người/tầng (mục 4)"
    elif k in ("karaoke", "nha_hat", "benh_vien", "duong_lao") and i["nguoi"] >= 50:
        loa = "≥ 50 người trên 1 tầng (mục 2)"
    elif k in cong_cong and (i["tang"] > 10 or i["ham"] >= 2):
        loa = "cao > 10 tầng hoặc ≥ 2 tầng hầm (mục 1)"
    if loa:
        out.append({"ht": "Hệ thống loa thông báo & hướng dẫn thoát nạn",
                    "dk": loa, "can": "QCVN 10, Phụ lục G (Bảng G.1)", "nhom": "loa"})

    # --- Mặt nạ lọc độc (Bảng F.1) — khách sạn ≥ 3 tầng ---
    if k == "khach_san" and i["tang"] >= 3:
        out.append({"ht": "Mặt nạ lọc độc (01 chiếc/người mỗi tầng)",
                    "dk": "khách sạn/lưu trú ≥ 3 tầng",
                    "can": "QCVN 10, Phụ lục F (Bảng F.1)", "nhom": "mat_na"})

    # --- Dụng cụ phá dỡ thô sơ (Bảng E.1) ---
    if k in ("chung_cu", "khach_san", "van_phong", "truong_hoc",
             "nha_ga", "karaoke", "nha_hat", "cho_tttm"):
        out.append({"ht": "Bộ dụng cụ phá dỡ thô sơ (rìu, xà beng, búa, kìm…)",
                    "dk": "không phụ thuộc quy mô (01 bộ)",
                    "can": "QCVN 10, Phụ lục E (Bảng E.1)", "nhom": "pha_do"})

    return out


# =====================================================================
# ƯỚC TÍNH SỐ LƯỢNG SƠ BỘ (sales chỉnh lại sau)
# =====================================================================
def uoc_sl(nhom: str, i: dict) -> int:
    """Ước tính sơ bộ số lượng thiết bị theo nhóm và đầu vào công trình."""
    dt = i.get("dt", 0)
    if nhom == "bao_chay":
        return max(1, ceil(dt / 30))            # 1 đầu báo / 30 m²
    if nhom == "bao_chay_doc_lap":
        return max(1, ceil(dt / 60))
    if nhom == "truyen_tin":
        return 1
    if nhom == "chua_chay":
        # Phân theo nhóm nguy cơ (TCVN 7336 Bảng 1)
        cn_k = i.get("cong_nang_k", "")
        _, dt_per_sprk, _, _ = chon_nhom_nguy_co_sprinkler(cn_k)
        # Nếu có rooms data → tính theo từng phòng (chính xác hơn)
        rooms = i.get("rooms_data") or []
        if rooms and any(r.get("dt", 0) > 0 for r in rooms):
            return sum(max(1, ceil(r["dt"] / dt_per_sprk))
                       for r in rooms if r.get("dt", 0) > 0)
        return max(1, ceil(dt / dt_per_sprk))
    if nhom == "hong_nuoc":
        return max(1, ceil(dt / 400))           # 1 họng / 400 m²
    if nhom == "binh":
        per = i.get("binhPerFloor") or 100
        floors = max(1, (i.get("tang") or 0) + (i.get("ham") or 0))
        per_floor = max(1, ceil((dt / floors) / per))
        base = per_floor * floors
        reserve = (i.get("binhReserve") or 0)
        return base + ceil(base * reserve / 100)
    if nhom == "den":
        return max(2, ceil(dt / 100))
    if nhom == "loa":
        return max(2, ceil(dt / 80))
    if nhom == "mat_na":
        return max(4, ceil(i.get("nguoi") or 10))
    if nhom == "pha_do":
        return 1
    if nhom == "nhan_cong":
        return 1
    return 1


# =====================================================================
# PHÂN LOẠI SẢN PHẨM TỪ TÊN (free-text → nhom/loai)
# =====================================================================
def classify_nhom(ten: str) -> dict:
    """
    Ánh xạ tên sản phẩm (free-text) → {nhom, loai}.
    Dùng khi nạp bảng giá từ DB gia_tong_hop (không có cột nhom/loai).
    """
    s = (ten or "").lower()

    def has(*kws):
        return any(kw in s for kw in kws)

    if has("nội quy", "tiêu lệnh"):
        return {"nhom": "noi_quy", "loai": None}
    # Cửa ngăn cháy / cửa chống cháy (QCVN 06:2022/BXD)
    if has("cửa ngăn cháy", "cửa chống cháy") or "ei 30" in s or "ei 60" in s or "ei 90" in s:
        if "ei 90" in s:
            return {"nhom": "cua_ngan_chay", "loai": "ei_90"}
        if "ei 60" in s:
            return {"nhom": "cua_ngan_chay", "loai": "ei_60"}
        if "ei 30" in s:
            return {"nhom": "cua_ngan_chay", "loai": "ei_30"}
        return {"nhom": "cua_ngan_chay", "loai": None}
    if has("mặt nạ"):
        return {"nhom": "mat_na", "loai": None}
    if has("phá dỡ", "rìu", "xà beng", "kìm cộng lực"):
        return {"nhom": "pha_do", "loai": None}
    if has("thiết bị truyền tin"):
        return {"nhom": "truyen_tin", "loai": "truyen_tin"}

    # Đèn EXIT / đèn chiếu sáng sự cố
    if (has("exit")
        or ("đèn" in s and has("sự cố", "thoát", "chỉ dẫn", "chỉ lối"))
        or has("chỉ dẫn thoát")):
        if has("exit", "chỉ dẫn", "chỉ lối") or ("thoát" in s and "sự cố" not in s):
            return {"nhom": "den", "loai": "den_exit"}
        return {"nhom": "den", "loai": "den_sc"}

    # Báo cháy độc lập — CHỈ áp dụng cho ĐẦU BÁO độc lập, không cho
    # chuông/đèn/nút ấn (kể cả khi tên có chữ "độc lập")
    if has("độc lập") and "đầu báo" in s:
        loai = "doc_lap_nhiet" if "nhiệt" in s else "doc_lap_khoi"
        return {"nhom": "bao_chay_doc_lap", "loai": loai}

    # Hệ thống báo cháy tự động
    if has("đầu báo", "trung tâm báo cháy", "tủ trung tâm",
           "tủ báo cháy", "chuông", "nút ấn", "nút nhấn", "tổ hợp chuông"):
        if "đầu báo nhiệt" in s:
            return {"nhom": "bao_chay", "loai": "dau_bao_nhiet"}
        if "đầu báo" in s:
            return {"nhom": "bao_chay", "loai": "dau_bao_khoi"}
        if has("trung tâm", "tủ báo cháy"):
            return {"nhom": "bao_chay", "loai": "trung_tam"}
        if "tổ hợp" in s:
            return {"nhom": "bao_chay", "loai": "chuong_den"}
        return {"nhom": "bao_chay", "loai": None}

    if has("sprinkler", "đầu phun"):
        # Phân biệt hướng lên (upright) vs hướng xuống (pendant)
        if has("upright", "quay lên", "hướng lên", "hướng lên trên"):
            return {"nhom": "chua_chay", "loai": "sprinkler_up"}
        if has("pendant", "quay xuống", "hướng xuống", "hướng xuống dưới"):
            return {"nhom": "chua_chay", "loai": "sprinkler_down"}
        return {"nhom": "chua_chay", "loai": "sprinkler_down"}  # default pendant
    # Tủ điện bơm sprinkler / chữa cháy
    if "tủ điện" in s and ("sprinkler" in s or ("bơm" in s and "chữa cháy" in s)):
        return {"nhom": "chua_chay", "loai": "tu_dien_bom_sprk"}
    # Cụm bơm sprinkler
    if has("cụm bơm") and ("sprinkler" in s or "chữa cháy" in s):
        return {"nhom": "chua_chay", "loai": "cum_bom_sprk"}
    # Van báo động (alarm valve)
    if has("van báo động", "alarm valve"):
        return {"nhom": "chua_chay", "loai": "van_bao_dong"}
    # Ống thép DN cho sprinkler
    if has("ống thép") and "sprinkler" in s:
        return {"nhom": "chua_chay", "loai": "ong_thep_sprk"}
    if "bơm" in s and "chữa cháy" in s:
        return {"nhom": "chua_chay", "loai": "bom"}
    if has("chữa cháy khí", "chữa cháy tự động", "fm200"):
        return {"nhom": "chua_chay", "loai": None}

    # 10 loại SP của hệ thống chữa cháy bằng nước
    if "tủ điện" in s and "bơm" in s:
        return {"nhom": "hong_nuoc", "loai": "tu_dien_bom"}
    if "cụm bơm" in s or ("bơm" in s and "chữa cháy" in s and "cụm" in s):
        return {"nhom": "hong_nuoc", "loai": "cum_bom"}
    if has("trụ chữa cháy", "trụ nước"):
        return {"nhom": "hong_nuoc", "loai": "tru_ngoai"}
    if has("họng tiếp nước"):
        return {"nhom": "hong_nuoc", "loai": "hong_tiep_nuoc"}
    # Ống mềm Daejin (drop pipe cho sprinkler) — KHÔNG phải phụ kiện họng nước
    # Tên SP có thể chứa "phụ kiện" làm match nhầm → loại trừ trước
    if has("ống mềm") and (
            "daejin" in s or "drop" in s or "d20" in s or "d25" in s):
        return {"nhom": "chua_chay", "loai": "ong_mem_sprk"}
    if has("phụ kiện", "cút", "tê", "mặt bích"):
        if "ống" in s or "chữa cháy" in s:
            return {"nhom": "hong_nuoc", "loai": "phu_kien_ong"}
    # === Phụ kiện ren / nối — loại trừ TRƯỚC để không match nhầm thành ống thép ===
    # "Bầu giảm ren", "côn ren", "rắc co", "tê ren", "cút ren", "măng xông",
    # "khớp nối", "nipple", "nối ren", "lơ ren" — đều là phụ kiện, KHÔNG phải ống.
    if has("bầu giảm", "côn ren", "tê ren", "cút ren", "rắc co",
           "măng xông", "khớp nối", "nipple", "nối ren", "lơ ren",
           "khớp xoay", "khớp mềm", "khớp giảm chấn", "elbow", "tee "):
        return {"nhom": "hong_nuoc", "loai": "phu_kien_ong"}

    # === Ống thép tráng kẽm / mạ kẽm — phân loại theo DN ===
    # BẮT BUỘC có chữ "ống" trong tên. Material: "thép" hoặc "tráng kẽm" hoặc "mạ kẽm".
    if has("ống") and has("thép", "tráng kẽm", "mạ kẽm"):
        for dn in ("dn25", "dn32", "dn40", "dn50", "dn65", "dn80",
                   "dn100", "dn125", "dn150"):
            if dn in s:
                return {"nhom": "hong_nuoc", "loai": f"ong_thep_{dn}"}
        # Match D50/D65 (không có DN prefix)
        for d, dn in [("d25", "dn25"), ("d32", "dn32"), ("d40", "dn40"),
                      ("d50", "dn50"), ("d65", "dn65"), ("d80", "dn80"),
                      ("d100", "dn100"), ("d125", "dn125"), ("d150", "dn150")]:
            if d in s:
                return {"nhom": "hong_nuoc", "loai": f"ong_thep_{dn}"}
        return {"nhom": "hong_nuoc", "loai": "ong_thep"}  # fallback
    if has("tủ chữa cháy", "hộp đựng họng", "hộp chữa cháy"):
        return {"nhom": "hong_nuoc", "loai": "tu_chua_chay"}
    if has("cuộn vòi"):
        # Phân DN50/DN65 theo tên SP
        if "d50" in s or "dn50" in s or "d 50" in s:
            return {"nhom": "hong_nuoc", "loai": "cuon_voi_dn50"}
        if "d65" in s or "dn65" in s or "d 65" in s:
            return {"nhom": "hong_nuoc", "loai": "cuon_voi_dn65"}
        return {"nhom": "hong_nuoc", "loai": "cuon_voi_dn65"}  # default
    if has("lăng phun"):
        if "d50" in s or "dn50" in s:
            return {"nhom": "hong_nuoc", "loai": "lang_phun_dn50"}
        if "d65" in s or "dn65" in s:
            return {"nhom": "hong_nuoc", "loai": "lang_phun_dn65"}
        return {"nhom": "hong_nuoc", "loai": "lang_phun_dn65"}  # default
    if has("van") and ("dn65" in s or "dn50" in s or "họng" in s):
        if "dn50" in s:
            return {"nhom": "hong_nuoc", "loai": "van_dn50"}
        return {"nhom": "hong_nuoc", "loai": "van_dn65"}
    # Fallback: bất kỳ SP liên quan đến họng nước
    if has("họng", "vòi chữa", "khớp nối"):
        return {"nhom": "hong_nuoc", "loai": None}

    if has("bình chữa cháy", "bình bột", "bình khí", "bình cầu", "xe đẩy chữa"):
        loai = None
        if "abc" in s and ("4kg" in s or "4 kg" in s):
            loai = "binh_abc"
        return {"nhom": "binh", "loai": loai}

    if has("loa", "âm thanh thông báo"):
        return {"nhom": "loa", "loai": None}

    if has("nhân công", "lắp đặt"):
        return {"nhom": "nhan_cong", "loai": None}

    return {"nhom": "phu_kien", "loai": None}


# =====================================================================
# DANH SÁCH CÔNG NĂNG PHÒNG (TCVN 7568-14:2025)
# =====================================================================
# Mỗi item: k (mã), t (tên), d (loại đầu báo mặc định: 'khoi' | 'nhiet')
ROOM_FUNCS = [
    {"k": "phong_ngu",    "t": "Phòng ngủ / phòng ở",                "d": "khoi"},
    {"k": "van_phong",    "t": "Văn phòng / phòng làm việc",         "d": "khoi"},
    {"k": "hanh_lang",    "t": "Hành lang / sảnh / lối đi",          "d": "khoi"},
    {"k": "phong_hop",    "t": "Phòng họp / hội trường / lớp học",   "d": "khoi"},
    {"k": "phong_khach",  "t": "Phòng khách / phòng chờ",            "d": "khoi"},
    {"k": "phong_benh",   "t": "Phòng bệnh / điều trị",              "d": "khoi"},
    {"k": "phong_an",     "t": "Phòng ăn / khu phục vụ",             "d": "khoi"},
    {"k": "ban_hang",     "t": "Khu bán hàng / trưng bày",           "d": "khoi"},
    {"k": "kho",          "t": "Kho hàng (thường)",                   "d": "khoi"},
    {"k": "phong_dien",   "t": "Phòng kỹ thuật điện / máy chủ",      "d": "khoi"},
    {"k": "bep",          "t": "Bếp / nhà bếp",                       "d": "nhiet"},
    {"k": "gara",         "t": "Gara / nhà để xe",                    "d": "nhiet"},
    {"k": "phong_may",    "t": "Phòng máy phát / nồi hơi",            "d": "nhiet"},
    {"k": "hoi_nuoc",     "t": "Khu nhiều hơi nước (giặt, tắm hơi)",  "d": "nhiet"},
    {"k": "bui",          "t": "Khu nhiều bụi (xưởng gỗ, xay xát)",   "d": "nhiet"},
]


def def_loai_dau_bao(func_k: str) -> str:
    """Loại đầu báo mặc định (khoi/nhiet) theo công năng phòng."""
    for f in ROOM_FUNCS:
        if f["k"] == func_k:
            return f["d"]
    return "khoi"


def default_room_func(cn_k: str) -> str:
    """Công năng phòng mặc định khi sinh hàng loạt từ công năng tòa nhà."""
    if cn_k in ("chung_cu", "nha_o_kd", "nha_o_sxkd", "khach_san",
                "benh_vien", "duong_lao", "nha_hon_hop"):
        return "phong_ngu"
    if cn_k in ("cho_tttm", "cua_hang", "nha_hang", "kd_chat_long"):
        return "ban_hang"
    if cn_k in ("kho_bc", "nong_san"):
        return "kho"
    if cn_k == "nha_de_xe":
        return "gara"
    return "van_phong"


def sl_phong(room: dict, dt_khoi: float = 60, dt_nhiet: float = 20) -> int:
    """Số đầu báo cần cho 1 phòng (theo diện tích bảo vệ)."""
    cov = dt_nhiet if room.get("loai") == "nhiet" else dt_khoi
    return max(1, ceil((room.get("dt") or 0) / cov))


def room_totals(rooms: list, dt_khoi: float = 60, dt_nhiet: float = 20) -> dict:
    """Tổng đầu báo khói/nhiệt từ danh sách phòng."""
    khoi = 0
    nhiet = 0
    for r in rooms:
        s = sl_phong(r, dt_khoi, dt_nhiet)
        if r.get("loai") == "nhiet":
            nhiet += s
        else:
            khoi += s
    return {"khoi": khoi, "nhiet": nhiet}


# =====================================================================
# ĐỘNG CƠ CHÍNH: PHÂN TÍCH YÊU CẦU PCCC
# =====================================================================

def _thuoc_qcvn06_an_toan_chay(cn_k: str, i: dict):
    """Theo QCVN 06:2022/BXD mục 1.1.2.a — phạm vi áp dụng đối với nhà ở.

    Nhà ở riêng lẻ KHÔNG thuộc phạm vi QCVN 06 (không bắt buộc đèn EXIT,
    chiếu sáng sự cố, cửa ngăn cháy theo QCVN 06) NẾU đồng thời:
      - dưới 7 tầng nổi
      - không quá 1 tầng hầm
      - phần SX-KD chiếm < 30% tổng diện tích sàn (đã thoả mãn khi chọn
        công năng nha_o_kd / nha_o_sxkd)

    Các công năng khác (chung cư, công cộng, SX, kho...) đều thuộc QCVN 06.
    Trả về (bool, lý do).
    """
    tang = int(i.get("tang") or 0)
    ham = int(i.get("ham") or 0)
    if cn_k in ("nha_o_kd", "nha_o_sxkd"):
        if tang >= 7:
            return True, "Nhà ở riêng lẻ ≥ 7 tầng → thuộc QCVN 06:2022 (1.1.2.a)"
        if ham > 1:
            return True, "Nhà ở riêng lẻ có > 1 tầng hầm → thuộc QCVN 06:2022 (1.1.2.a)"
        return False, ("Nhà ở riêng lẻ < 7 tầng, ≤ 1 hầm, KD ≤ 30% sàn → "
                       "KHÔNG thuộc phạm vi QCVN 06:2022 (điều 1.1.2.a)")
    return True, "Thuộc phạm vi QCVN 06:2022"


def phan_tich(cn_k: str, i: dict) -> dict:
    """
    Trả {cn, items, bcState} — danh sách hệ thống/thiết bị cần trang bị.

    bcState: 'tu_dong' | 'doc_lap' | 'khong'
        - tu_dong : phải lắp hệ thống báo cháy tự động
        - doc_lap : quy mô nhỏ, được dùng thiết bị báo cháy độc lập thay thế
        - khong   : không yêu cầu

    Mỗi item trong items: dict {ht, req, dk, can, nhom, mode (optional)}
    """
    cn = get_cong_nang(cn_k)
    if cn is None:
        raise ValueError(f"Không có công năng: {cn_k}")

    bc = cn["bc"](i)
    cc = cn["cc"](i)

    items = []

    # --- Báo cháy: tự động / độc lập / khuyến nghị độc lập / không ---
    if not bc["req"]:
        # Dưới ngưỡng yêu cầu hệ thống tự động — kiểm tra xem có thuộc diện
        # "cho phép trang bị thiết bị báo cháy độc lập" (chú thích Bảng A.1)
        # → đưa ra KHUYẾN NGHỊ (không bắt buộc) tối thiểu báo cháy độc lập
        if cho_phep_doc_lap(cn_k, i):
            bc_state = "khuyen_nghi"
            items.append({
                "ht": "Thiết bị báo cháy độc lập (KHUYẾN NGHỊ — không bắt buộc)",
                "req": False, "mode": "khuyen_nghi",
                "dk": (f"công trình dưới ngưỡng bắt buộc ({bc['basis']}) "
                       "nhưng thuộc diện 'cho phép trang bị thiết bị báo cháy "
                       "độc lập' theo chú thích Bảng A.1"),
                "can": (f"QCVN 10:2025/BCA, Bảng A.1 (mục {cn['muc']}) — "
                        "chú thích cho phép trang bị thiết bị báo cháy độc lập"),
                "nhom": "bao_chay_doc_lap"})
        else:
            bc_state = "khong"
            items.append({"ht": "Hệ thống báo cháy tự động", "req": False,
                          "dk": bc["basis"],
                          "can": f"QCVN 10, Bảng A.1 (mục {cn['muc']})",
                          "nhom": "bao_chay"})
    elif cho_phep_doc_lap(cn_k, i):
        bc_state = "doc_lap"
        items.append({"ht": "Thiết bị báo cháy độc lập (được phép thay hệ thống tự động)",
                      "req": True, "mode": "doc_lap",
                      "dk": bc["basis"] + " — quy mô nhỏ: được phép dùng thiết bị báo cháy độc lập thay cho hệ thống tự động",
                      "can": f"QCVN 10, Bảng A.1 (mục {cn['muc']})",
                      "nhom": "bao_chay_doc_lap"})
    else:
        bc_state = "tu_dong"
        items.append({"ht": "Hệ thống báo cháy tự động", "req": True,
                      "dk": bc["basis"],
                      "can": f"QCVN 10, Bảng A.1 (mục {cn['muc']})",
                      "nhom": "bao_chay"})

    # --- Truyền tin báo cháy: bắt buộc khi cơ sở thuộc Phụ lục I NĐ 105 ---
    try:
        _pl_check = tra_phu_luc_nd105(cn_k, i)
        truyen_tin_bat_buoc = bool(_pl_check.get("thuoc_pl1"))
    except Exception:
        truyen_tin_bat_buoc = (bc_state != "khong")

    # LOGIC MỚI: nếu bắt buộc truyền tin mà chưa có báo cháy gì
    # → ép lên báo cháy ĐỘC LẬP (vì truyền tin cần đầu vào tín hiệu)
    if truyen_tin_bat_buoc and bc_state in ("khong", "khuyen_nghi"):
        bc_state = "doc_lap"
        # Loại bỏ item bao_chay/bao_chay_doc_lap cũ rồi append item mới
        items = [x for x in items
                 if x["nhom"] not in ("bao_chay", "bao_chay_doc_lap")]
        items.append({
            "ht": "Thiết bị báo cháy độc lập "
                  "(bắt buộc do yêu cầu truyền tin)",
            "req": True, "mode": "doc_lap",
            "dk": "Cơ sở thuộc Phụ lục I NĐ 105/2025 → bắt buộc thiết bị "
                  "truyền tin báo cháy → cần báo cháy độc lập tối thiểu "
                  "để cấp đầu vào tín hiệu cho truyền tin",
            "can": "NĐ 105/2025/NĐ-CP Điều 27 + QCVN 10:2025/BCA "
                   f"Bảng A.1 (mục {cn['muc']})",
            "nhom": "bao_chay_doc_lap"})

    if truyen_tin_bat_buoc:
        items.append({"ht": "Thiết bị truyền tin báo cháy (kết nối CSDL PCCC)",
                      "req": True,
                      "dk": "bắt buộc với cơ sở thuộc diện quản lý PCCC "
                            "(Phụ lục I) · hoàn thành chậm nhất 01/7/2027",
                      "can": "NĐ 105/2025/NĐ-CP, Điều 27",
                      "nhom": "truyen_tin"})

    # --- Chữa cháy tự động ---
    items.append({"ht": "Hệ thống chữa cháy tự động (Sprinkler/khí…)",
                  "req": cc["req"], "dk": cc["basis"],
                  "can": f"QCVN 10, Bảng A.1 (mục {cn['muc']})",
                  "nhom": "chua_chay"})

    # --- Hệ thống bổ trợ (B.1, E.1, F.1, G.1) ---
    bo_tro_list = he_thong_bo_tro(cn, i)
    has_hong_nuoc = any(x["nhom"] == "hong_nuoc" for x in bo_tro_list)
    for x in bo_tro_list:
        items.append({"ht": x["ht"], "req": True,
                      "dk": x["dk"], "can": x["can"], "nhom": x["nhom"]})

    # Quy tắc bổ sung: công trình có hệ thống chữa cháy tự động
    # → BẮT BUỘC có hệ thống họng nước chữa cháy trong nhà
    if cc["req"] and not has_hong_nuoc:
        items.append({"ht": "Hệ thống họng nước chữa cháy trong nhà",
                      "req": True,
                      "dk": "đi kèm hệ thống chữa cháy tự động",
                      "can": "QCVN 10, Phụ lục B (đi kèm chữa cháy tự động)",
                      "nhom": "hong_nuoc"})

    # --- Luôn khuyến nghị ---
    items.append({"ht": "Bình chữa cháy bột ABC 4kg", "req": True,
                  "dk": "1 bình / 100 m² mỗi tầng + 10% dự phòng (tạm tính; số lượng chỉnh được ở tab Báo giá)",
                  "can": "Định mức công ty (tham khảo QCVN 10 mục 2.6 · TCVN 7435-1)",
                  "nhom": "binh"})

    den_req, den_ly_do = _thuoc_qcvn06_an_toan_chay(cn_k, i)
    items.append({"ht": "Đèn chỉ dẫn thoát nạn (EXIT) & đèn chiếu sáng sự cố",
                  "req": den_req,
                  "dk": ("mặc định 1 đèn EXIT + 1 đèn chiếu sáng sự cố mỗi tầng · "
                         "nhập tab \"Thoát nạn & chiếu sáng\" để tính chính xác"
                         if den_req else den_ly_do),
                  "can": "TCVN 13456:2022; QCVN 06:2022/BXD (điều 1.1.2)",
                  "nhom": "den"})

    items.append({"ht": "Bộ nội quy - tiêu lệnh PCCC", "req": True,
                  "dk": "mỗi tầng 01 bộ, niêm yết nơi dễ thấy (gần bình chữa cháy, lối/cầu thang thoát nạn)",
                  "can": "NĐ 105/2025, Điều 3; TCVN 3890:2023",
                  "nhom": "noi_quy"})

    # Cửa ngăn cháy (QCVN 06:2022/BXD) — chỉ bắt buộc khi thuộc phạm vi QCVN 06
    cnc = tinh_cua_ngan_chay(cn, i)
    cnc_req, cnc_ly_do = _thuoc_qcvn06_an_toan_chay(cn_k, i)
    if cnc["sl_total"] > 0 and cnc_req:
        ei_label = cnc["loai_ei"].upper().replace("_", " ")
        items.append({"ht": "Hệ thống cửa ngăn cháy",
                      "req": True,
                      "dk": f"loại {ei_label} (ước tính ~{cnc['sl_total']} bộ): {cnc['basis']}",
                      "can": "QCVN 06:2022/BXD (mục 3.2.11, Bảng 1, Bảng 2, Bảng A.1)",
                      "nhom": "cua_ngan_chay",
                      "ei_loai": cnc["loai_ei"],
                      "sl_estimate": cnc["sl_total"]})
    elif cnc["sl_total"] > 0 and not cnc_req:
        # Vẫn liệt kê dưới dạng KHÔNG bắt buộc — user có thể chọn "Muốn trang bị"
        ei_label = cnc["loai_ei"].upper().replace("_", " ")
        items.append({"ht": "Hệ thống cửa ngăn cháy",
                      "req": False,
                      "dk": cnc_ly_do,
                      "can": "QCVN 06:2022/BXD (mục 1.1.2.a — phạm vi)",
                      "nhom": "cua_ngan_chay",
                      "ei_loai": cnc["loai_ei"],
                      "sl_estimate": cnc["sl_total"]})

    return {"cn": cn, "i": i, "items": items, "bcState": bc_state}


# =====================================================================
# BUILD SLOTS BÁO GIÁ (mỗi dòng = 1 thiết bị cần báo)
# =====================================================================
def build_slots(items: list, i: dict, totals: dict = None) -> list:
    """
    Sinh danh sách slot báo giá từ phân tích yêu cầu.

    Mỗi slot: dict {label, nhom, loai, sl, parent_ht}
    `parent_ht` = tên hệ thống cha (vd "Hệ thống báo cháy tự động") để gom nhóm
    trong UI báo giá.
    `totals` (tùy chọn) = kết quả room_totals() để override số đầu báo
        theo dữ liệu phòng cụ thể.
    """
    if totals is None:
        totals = {"khoi": 0, "nhiet": 0}
    floors = max(1, (i.get("tang") or 0) + (i.get("ham") or 0))
    slots = []
    current_ht = [""]  # closure-shared parent ht

    def add(label, nhom, loai, sl):
        if sl > 0:
            slots.append({"label": label, "nhom": nhom, "loai": loai, "sl": sl,
                          "parent_ht": current_ht[0]})

    # 3 nhóm gộp chung tiêu đề "Phương tiện chữa cháy ban đầu"
    PT_CC_BAN_DAU = {"binh", "pha_do", "noi_quy"}

    for x in items:
        if not x["req"]:
            continue
        if x["nhom"] in PT_CC_BAN_DAU:
            current_ht[0] = "Phương tiện chữa cháy ban đầu"
        else:
            current_ht[0] = x.get("ht", "")
        nhom = x["nhom"]

        if nhom == "bao_chay":
            add("Đầu báo khói", "bao_chay", "dau_bao_khoi",
                totals["khoi"] or uoc_sl("bao_chay", i))
            if totals["nhiet"] > 0:
                add("Đầu báo nhiệt", "bao_chay", "dau_bao_nhiet", totals["nhiet"])
            add("Tổ hợp chuông đèn, nút ấn", "bao_chay", "chuong_den", floors)
            add("Tủ trung tâm báo cháy", "bao_chay", "trung_tam", 1)

        elif nhom == "bao_chay_doc_lap":
            add("Đầu báo khói độc lập", "bao_chay_doc_lap", "doc_lap_khoi",
                totals["khoi"] or uoc_sl("bao_chay_doc_lap", i))
            if totals["nhiet"] > 0:
                add("Đầu báo nhiệt độc lập", "bao_chay_doc_lap", "doc_lap_nhiet",
                    totals["nhiet"])
            # Mỗi tầng 1 bộ Tổ hợp chuông đèn nút ấn (kể cả khi dùng độc lập)
            add("Tổ hợp chuông đèn, nút ấn", "bao_chay_doc_lap",
                "chuong_den", floors)

        elif nhom == "truyen_tin":
            add("Thiết bị truyền tin báo cháy", "truyen_tin", None, 1)

        elif nhom == "chua_chay":
            # Sinh chi tiết SP cho hệ Sprinkler theo TCVN 7336
            cn_k_local = i.get("cong_nang_k", "")
            n_sprk = uoc_sl("chua_chay", i)
            tang_noi = int(i.get("tang") or 1)
            tang_ham = int(i.get("ham") or 0)
            D_local = float(i.get("dai") or 0)
            R_local = float(i.get("rong") or 0)
            cao_local = float(i.get("cao") or 0)
            for s in build_sprinkler_slots(
                    n_sprk, i.get("dt") or 0,
                    cn_k_local, tang_noi, tang_ham,
                    D=D_local, R=R_local, cao_pccc=cao_local,
                    sprk_per_nhanh=int(i.get("sprk_per_nhanh") or 5)):
                if s["sl"] > 0:
                    s["parent_ht"] = current_ht[0]
                    slots.append(s)

        elif nhom == "hong_nuoc":
            # Sinh chi tiết 10 SP cho hệ thống chữa cháy bằng nước
            D = i.get("dai") or 0
            R = i.get("rong") or 0
            n_hong_per_floor = i.get("hong_per_floor")
            he_so_hong = i.get("he_so_hong_per_diem") or 1
            # Nếu chưa có info hình học → fallback theo uoc_sl
            if D > 0 and R > 0 and n_hong_per_floor:
                n_hong = n_hong_per_floor * he_so_hong * floors
            else:
                n_hong = uoc_sl("hong_nuoc", i)
            has_sprk = any(x["nhom"] == "chua_chay" and x["req"] for x in items)
            # Chọn DN cho cuộn vòi + van + lăng phun
            cao_pccc = float(i.get("cao") or 0)
            he_so = int(i.get("he_so_hong_per_diem") or 1)
            cn_k = i.get("cong_nang_k", "")
            q_per_jet = float(i.get("q_per_jet") or 2.5)
            dn, _ = chon_dn_hong(cao_pccc, he_so, cn_k, q_per_jet)
            # H.2.18: bố trí họng kép chỉ áp dụng cho nhà ở (chung cư/KTX)
            is_nha_o = cn_k == "chung_cu"
            hl_dai = float(i.get("hanh_lang_dai") or 0)
            for s in build_hong_nuoc_slots(n_hong, floors, D, R, has_sprk, dn,
                                           is_nha_o=is_nha_o,
                                           hanh_lang_dai=hl_dai,
                                           he_so_hong_per_diem=he_so,
                                           cao_pccc=cao_pccc):
                if s["sl"] > 0:
                    s["parent_ht"] = current_ht[0]
                    slots.append(s)

        elif nhom == "binh":
            add("Bình chữa cháy ABC 4kg", "binh", "binh_abc", uoc_sl("binh", i))

        elif nhom == "den":
            add("Đèn chỉ dẫn thoát nạn (EXIT)", "den", "den_exit", max(floors, 1))
            add("Đèn chiếu sáng sự cố", "den", "den_sc", max(floors, 1))

        elif nhom == "loa":
            add("Loa thông báo & hướng dẫn thoát nạn", "loa", None, uoc_sl("loa", i))

        elif nhom == "mat_na":
            add("Mặt nạ lọc độc", "mat_na", None, uoc_sl("mat_na", i))

        elif nhom == "pha_do":
            add("Bộ dụng cụ phá dỡ thô sơ", "pha_do", None, 1)

        elif nhom == "cua_ngan_chay":
            ei = x.get("ei_loai") or "ei_30"
            label = f"Cửa ngăn cháy {ei.upper().replace('_', ' ')}"
            sl = int(x.get("sl_estimate") or 0)
            add(label, "cua_ngan_chay", ei, sl)

    # Phần luôn có — gộp vào "Phương tiện chữa cháy ban đầu"
    current_ht[0] = "Phương tiện chữa cháy ban đầu"
    add("Bộ nội quy - tiêu lệnh PCCC", "noi_quy", None, floors)

    # =================================================================
    # CỤM BƠM CHỮA CHÁY — tính chung cho cả họng + sprinkler
    # TCVN 7336:2021 B.3.8: Q_bơm = Q_họng + Q_sprk
    # =================================================================
    has_hong = any(x["nhom"] == "hong_nuoc" and x["req"] for x in items)
    has_sprk_cc = any(x["nhom"] == "chua_chay" and x["req"] for x in items)
    if has_hong or has_sprk_cc:
        q_hong_ls = 0.0
        dn_hong_str = "dn50"
        if has_hong:
            he_so = int(i.get("he_so_hong_per_diem") or 1)
            q_per_jet = float(i.get("q_per_jet") or 2.5)
            q_hong_ls = he_so * q_per_jet
            cao_pccc_local = float(i.get("cao") or 0)
            cn_k_local2 = i.get("cong_nang_k", "")
            dn_h, _ = chon_dn_hong(cao_pccc_local, he_so,
                                   cn_k_local2, q_per_jet)
            dn_hong_str = dn_h
        q_sprk_ls = 0.0
        nhom_sprk = "1"
        if has_sprk_cc:
            cn_k_local3 = i.get("cong_nang_k", "")
            sprk_info = tinh_sprinkler(
                float(i.get("dt") or 0), cn_k_local3, rooms=None)
            q_sprk_ls = float(sprk_info["luu_luong"])
            nhom_sprk = sprk_info["nhom"]
        # Chọn DN trục đứng cho tính ma sát (Bảng IV.1.2)
        dn_truc_str = "dn100"
        try:
            if has_sprk_cc:
                n_sprk_tmp = int(sprk_info.get("n_sprk", 0))
                if n_sprk_tmp > 0:
                    dn_truc_code, _ = dn_ong_sprinkler(n_sprk_tmp, ap_cao=True)
                    dn_truc_str = dn_truc_code
            elif has_hong:
                dn_truc_str = dn_ong_truc_chinh(dn_hong_str)
        except Exception:
            dn_truc_str = "dn100"
        bom = tinh_cum_bom(
            q_hong_ls=q_hong_ls, q_sprk_ls=q_sprk_ls,
            cao_pccc=float(i.get("cao") or 0),
            dai_nha=float(i.get("dai") or 0),
            dn_hong=dn_hong_str, nhom_sprk=nhom_sprk,
            has_van_av=has_sprk_cc,
            dn_truc_chinh=dn_truc_str)
        nhom_bom = "hong_nuoc" if has_hong else "chua_chay"
        parent_bom = ("Hệ thống cấp nước chữa cháy"
                      if has_hong else "Hệ thống chữa cháy tự động")

        # =================================================================
        # TRẠM BƠM CHỮA CHÁY (TCVN 7336 mục 5.8) — 3 bơm + 1 tủ điện
        #   Bơm chính: điện liền/rời trục (Q,H,N từ tinh_cum_bom)
        #   Bơm dự phòng: bắt buộc theo 5.8.2, cùng Q-H với chính
        #                  Mặc định DIESEL (5.8.4); user có thể đổi sang điện
        #   Bơm bù áp (jockey): CHỈ khi có sprinkler — duy trì áp đường ống
        # =================================================================
        Q_chinh = bom["Q_m3h"]
        H_chinh = bom["H_m"]
        N_chinh = bom["N_dv_kw"]
        loai_bom_dp = (i.get("loai_bom_dp") or "diesel").lower()

        # 1. Bơm chính
        label_chinh = (f"Bơm chữa cháy CHÍNH (điện) ≥ Q {Q_chinh:.0f} m³/h, "
                       f"H {H_chinh:.0f} m, N {N_chinh} kW")
        slots.append({
            "label": label_chinh,
            "nhom": nhom_bom, "loai": "cum_bom_chinh",
            "sl": 1, "parent_ht": parent_bom,
            "fixed": True, "fixed_ten": label_chinh,
            "fixed_gia": 1, "fixed_dv": "Bơm",
            "bom_info": bom,
            "bom_role": "chinh",
        })

        # 2. Bơm dự phòng (bắt buộc theo TCVN 7336 5.8.2)
        if loai_bom_dp == "diesel":
            label_dp = (f"Bơm chữa cháy DỰ PHÒNG (diesel) ≥ Q {Q_chinh:.0f} m³/h, "
                        f"H {H_chinh:.0f} m, N {N_chinh*1.2:.0f} kW")
            label_dp_dv = "Bơm"
        else:
            label_dp = (f"Bơm chữa cháy DỰ PHÒNG (điện) ≥ Q {Q_chinh:.0f} m³/h, "
                        f"H {H_chinh:.0f} m, N {N_chinh} kW")
            label_dp_dv = "Bơm"
        slots.append({
            "label": label_dp,
            "nhom": nhom_bom, "loai": "cum_bom_dp",
            "sl": 1, "parent_ht": parent_bom,
            "fixed": True, "fixed_ten": label_dp,
            "fixed_gia": 1, "fixed_dv": label_dp_dv,
            "bom_info": bom,
            "bom_role": "dp",
            "loai_bom_dp": loai_bom_dp,
        })

        # 3. Bơm bù áp (jockey) — CHỈ khi có sprinkler
        if has_sprk_cc:
            Q_jockey = 1.5  # m³/h (chuẩn quốc tế)
            H_jockey = H_chinh + 5  # +5m để duy trì áp
            label_ja = (f"Bơm bù áp (jockey) ≥ Q {Q_jockey} m³/h, "
                        f"H {H_jockey:.0f} m")
            slots.append({
                "label": label_ja,
                "nhom": nhom_bom, "loai": "cum_bom_bu_ap",
                "sl": 1, "parent_ht": parent_bom,
                "fixed": True, "fixed_ten": label_ja,
                "fixed_gia": 1, "fixed_dv": "Bơm",
                "bom_info": {"Q_m3h": Q_jockey, "H_m": H_jockey,
                             "N_dv_kw": 2.2},
                "bom_role": "bu_ap",
            })

        # 4. Tủ điện điều khiển trạm bơm
        slots.append({
            "label": "Tủ điện điều khiển trạm bơm chữa cháy",
            "nhom": nhom_bom, "loai": "tu_dien_bom",
            "sl": 1, "parent_ht": parent_bom,
            "fixed": True,
            "fixed_ten": "Tủ điện điều khiển trạm bơm chữa cháy",
            "fixed_gia": 1, "fixed_dv": "Tủ",
        })

    return slots


# =====================================================================
# SELF-TEST nhanh — chạy `python pccc_rules.py` để kiểm tra
# =====================================================================
# =====================================================================
# CỬA NGĂN CHÁY (QCVN 06:2022/BXD)
# =====================================================================
def tinh_cua_ngan_chay(cn: dict, i: dict) -> dict:
    """Ước tính tổng số cửa ngăn cháy + loại EI theo QCVN 06:2022/BXD.
    Trả dict {sl_total, loai_ei, basis, detail}."""
    floors = max(1, (i.get("tang") or 0) + (i.get("ham") or 0))
    so_phong = int(i.get("so_phong") or 0)
    so_cau_thang = int(i.get("so_cau_thang") or 1)  # mặc định 1 cầu thang
    cao = float(i.get("cao") or 0)
    ham = int(i.get("ham") or 0)

    # (a) Cửa buồng thang bộ — 1 cửa/tầng/buồng thang
    n_thang = floors * so_cau_thang
    # (b) Cửa khoang đệm — chỉ nhà cao ≥ 28m hoặc có tầng hầm
    has_dem = cao >= 28 or ham > 0
    n_dem = n_thang if has_dem else 0
    # (c) Cửa căn hộ ra hành lang — chỉ chung cư
    n_can_ho = so_phong if cn["k"] == "chung_cu" else 0
    # (d) Cửa phòng kỹ thuật (cố định 2 bộ)
    n_kt = 2
    # (e) Cửa tầng hầm
    n_ham = ham

    total = n_thang + n_dem + n_can_ho + n_kt + n_ham

    # Loại EI: EI 60 cho cao tầng / công năng nguy hiểm; còn lại EI 30
    need_ei60 = (cao >= 28
                 or cn["k"] in ("karaoke", "kd_chat_long", "kho_bc",
                                "benh_vien", "duong_lao")
                 or ham > 0)
    loai_ei = "ei_60" if need_ei60 else "ei_30"

    basis_parts = []
    if n_thang > 0:
        basis_parts.append(f"buồng thang: {floors}×{so_cau_thang}={n_thang}")
    if n_dem > 0:
        basis_parts.append(f"khoang đệm: {n_dem}")
    if n_can_ho > 0:
        basis_parts.append(f"cửa căn hộ: {n_can_ho}")
    if n_kt > 0:
        basis_parts.append(f"phòng kỹ thuật: {n_kt}")
    if n_ham > 0:
        basis_parts.append(f"tầng hầm: {n_ham}")

    return {
        "sl_total": total,
        "loai_ei": loai_ei,
        "basis": "; ".join(basis_parts),
        "detail": {"thang": n_thang, "dem": n_dem, "can_ho": n_can_ho,
                   "ky_thuat": n_kt, "ham": n_ham},
    }


# =====================================================================
# TÍNH SỐ HỌNG NƯỚC CHỮA CHÁY TRONG NHÀ (TCVN 2622:1995)
# Nguyên tắc: 1 họng phủ nửa đường tròn bán kính r=25m (vòi 20m + lăng 5m)
# =====================================================================
def tinh_so_hong_nuoc(D: float, R: float, floors: int = 1,
                      he_so_hong_per_diem: int = 1, r: float = 25.0) -> dict:
    """Tính số họng nước chữa cháy trong nhà theo hình học.

    Args:
        D: chiều dài nhà (m)
        R: chiều rộng nhà (m)
        floors: tổng số tầng (nổi + hầm)
        he_so_hong_per_diem: 1 hoặc 2 (theo Bảng 14 TCVN 2622)
        r: bán kính phủ 1 họng (m), mặc định 25

    Returns: dict {n_per_floor, total, case, formula, basis, warnings}
    """
    from math import sqrt, ceil
    warnings = []
    case = ""
    formula = ""

    if D <= 0 or R <= 0:
        return {"n_per_floor": 0, "total": 0, "case": "thiếu_dữ_liệu",
                "formula": "Cần D, R > 0", "basis": "",
                "warnings": ["Chưa nhập đủ chiều dài/chiều rộng nhà"]}

    # Để chuẩn hóa: D = cạnh dài hơn, R = cạnh ngắn hơn
    if R > D:
        D, R = R, D

    if R <= r:
        # TH1: nhà hẹp — 1 dãy họng dọc 1 tường dài
        case = "hẹp"
        # Kiểm tra trước: nếu 1 họng đặt giữa tường đã phủ được toàn nhà → 1 họng đủ
        # Điểm xa nhất từ họng giữa: √((D/2)² + R²)
        max_dist_1_hong = sqrt((D / 2) ** 2 + R * R)
        if max_dist_1_hong <= r:
            n_per_floor = 1
            formula = (f"R={R:.1f}m ≤ 25m và √((D/2)²+R²)={max_dist_1_hong:.1f}m ≤ 25m "
                       f"→ 1 họng đặt giữa tường đủ phủ toàn nhà")
        else:
            # Cần nhiều họng dọc tường
            d = 2 * sqrt(r * r - R * R) if R < r else 1.0
            if d < 1:
                d = 1.0
            n_per_floor = ceil(D / d)
            # Cộng thêm 1 nếu D > d (để phủ cạnh cuối)
            if D > d:
                n_per_floor += 1
            formula = (f"R={R:.1f}m ≤ 25m, D={D:.1f}m > vùng phủ 1 họng. "
                       f"d = 2√(25²-{R:.1f}²) = {d:.1f}m. "
                       f"n = ⌈{D:.1f}/{d:.1f}⌉" 
                       + (f" + 1 = {n_per_floor}" if D > d else f" = {n_per_floor}"))
    else:
        # R > r → cần > 1 dãy. Công thức 2 dãy đối diện: d = √(4r² - R²)
        # Khả thi khi R < 2r VÀ d ≥ 5m. Ngoài đó → fallback area-based.
        D_MIN = 5.0  # ngưỡng thực tế tối thiểu giữa 2 họng cùng dãy
        if R < 2 * r:
            d = 2 * sqrt(r * r - (R / 2) ** 2)  # = √(4r² - R²)
        else:
            d = 0  # R ≥ 2r → 2 dãy không phủ được toán học

        if d >= D_MIN:
            # TH2: 2 dãy đối diện khả thi
            case = "rộng_vừa"
            n_per_row = ceil(D / d) + 1
            n_per_floor = 2 * n_per_row
            formula = (f"R={R:.1f}m (r < R < 2r) → 2 dãy đối diện. "
                       f"d = √(4r²-R²) = √(2500-{R*R:.0f}) = {d:.1f}m. "
                       f"n = 2 × (⌈{D:.1f}/{d:.1f}⌉ + 1) = {n_per_floor}")
        else:
            # TH3: cần ≥ 3 dãy (hoặc dùng DN65 r=28m). Tính sơ bộ theo DT.
            case = "rộng_lớn"
            area_per_hong = 3.1416 * r * r * 0.6  # ~60% hình tròn (kể overlap)
            n_per_floor = max(1, ceil((D * R) / area_per_hong))
            ly_do = (f"R={R:.1f}m ≥ 2r=50m"
                     if R >= 2 * r
                     else f"R={R:.1f}m → d_2dãy={d:.1f}m < 5m")
            formula = (f"{ly_do} → 2 dãy không khả thi. "
                       f"Tính theo DT: 1 họng ~{area_per_hong:.0f}m² → "
                       f"n = ⌈{D*R:.0f}/{area_per_hong:.0f}⌉ = {n_per_floor}")
            warnings.append(
                f"⚠ R={R:.1f}m → 2 dãy họng (DN50, r=25m) không đủ phủ. "
                f"Thực tế cần ≥ 3 dãy, hoặc dùng DN65 (r=28m), hoặc luận chứng "
                f"riêng. App tính sơ bộ theo diện tích.")

    total = n_per_floor * he_so_hong_per_diem * max(1, floors)
    basis = (f"Tầng: {n_per_floor} họng/tầng × {he_so_hong_per_diem} họng/điểm "
             f"(Bảng 14 TCVN 2622) × {floors} tầng = {total} họng")

    return {
        "n_per_floor": n_per_floor,
        "total": total,
        "case": case,
        "formula": formula,
        "basis": basis,
        "warnings": warnings,
    }


# Các tham số phụ trợ cho hệ thống cấp nước CC
BAC_CHIU_LUA = ["I", "II", "III", "IV", "V"]
HANG_SX = ["A", "B", "C", "D", "E", "F"]

# Công năng được coi là nhà sản xuất / kho (cần khai báo hạng SX)
CN_SAN_XUAT_KHO = {"nong_san", "kho_bc", "kd_chat_long",
                   "nha_o_sxkd", "cua_hang"}


def auto_hl_dai(cn_k: str, D: float, so_phong_total: int, floors: int) -> float:
    """Tự tính chiều dài hành lang chung theo công năng.

    Override cases:
      - nha_de_xe → 0 (không có hành lang)
      - mam_non → D (nhiều lớp song song theo chiều dài)
    Rule chung:
      - chung_cu HOẶC ≤ 4 phòng/tầng → D/3 (nhà ở / ít phòng)
      - còn lại → D (nhà công cộng / nhiều phòng / SX / kho)
    """
    from math import ceil
    if cn_k == "nha_de_xe":
        return 0.0
    if cn_k == "mam_non":
        return float(D)
    floors = max(1, int(floors))
    so_phong_per_floor = ceil(max(0, int(so_phong_total)) / floors)
    if cn_k == "chung_cu" or so_phong_per_floor <= 4:
        return float(D) / 3.0
    return float(D)


def tra_bang_h6(bac_chiu_lua: str, hang_nguy_hiem: str,
                cap_nhc_kc: str, khoi_tich: float) -> dict:
    """Tra Bảng H.6 QCVN 10:2025/BCA cho **nhà sản xuất + nhà kho**.

    Khác với Bảng H.5 (cho nhà ở + công cộng), Bảng H.6 tra theo tổ hợp:
        (bậc chịu lửa) × (hạng nguy hiểm cháy) × (cấp NHC kết cấu) × KT
    với 2 ngưỡng KT: ≤ 150 (×1000m³) và > 150 (×1000m³).

    Args:
        bac_chiu_lua: "I", "II", "III", "IV", "V"
        hang_nguy_hiem: "A", "B", "C", "D", "E"
        cap_nhc_kc: "S0", "S1", "S2", "S3" (mặc định "S0" nếu không xác định)
        khoi_tich: m³ (sẽ chia 1000 so với ngưỡng bảng)

    Returns: {he_so, q_per_jet, basis, ghi_chu, source}
    """
    bcl = (bac_chiu_lua or "").upper().strip()
    h = (hang_nguy_hiem or "").upper().strip()
    cap = (cap_nhc_kc or "S0").upper().strip()
    kt_kilo = khoi_tich / 1000.0  # đổi sang nghìn m³

    # 10 dòng Bảng H.6 — mỗi dòng: (set bậc, set hạng, set cấp NHC hoặc None,
    # (he_so, q) cho ≤150, (he_so, q) cho >150)
    rules = [
        ({"I", "II"},   {"A", "B", "C"}, {"S0", "S1"},        (2, 2.5), (3, 2.5)),
        ({"I", "II"},   {"D", "E"},      None,                (1, 2.5), (1, 2.5)),
        ({"III"},       {"A", "B", "C"}, {"S0"},              (2, 2.5), (3, 2.5)),
        ({"III"},       {"D", "E"},      {"S0", "S1"},        (1, 2.5), (2, 2.5)),
        ({"IV"},        {"A", "B"},      {"S0"},              (2, 2.5), (3, 2.5)),
        ({"IV"},        {"C"},           {"S0", "S1"},        (2, 2.5), (2, 5.0)),
        ({"IV"},        {"C"},           {"S2", "S3"},        (3, 2.5), (4, 2.5)),
        ({"IV"},        {"D", "E"},      None,                (1, 2.5), (2, 2.5)),
        ({"V"},         {"C"},           None,                (2, 2.5), (2, 5.0)),
        ({"V"},         {"D", "E"},      None,                (1, 2.5), (2, 2.5)),
    ]

    for bcl_set, h_set, cap_set, le150, gt150 in rules:
        if bcl in bcl_set and h in h_set:
            if cap_set is None or cap in cap_set:
                he_so, q = gt150 if kt_kilo > 150 else le150
                cap_str = f", cấp NHC kết cấu {cap}" if cap_set else ""
                kt_str = (f"KT≈{kt_kilo:.1f} nghìn m³"
                          if kt_kilo > 0 else "KT chưa rõ")
                nguong = "> 150" if kt_kilo > 150 else "≤ 150"
                basis = (f"QCVN 10:2025 Bảng H.6: nhà SX/kho bậc {bcl}, "
                         f"hạng {h}{cap_str}, {kt_str} ({nguong} nghìn m³) → "
                         f"{he_so} tia × {q:g} L/s")
                ghi_chu = []
                if q >= 5.0:
                    ghi_chu.append(
                        "⚠ Lưu lượng tia ≥ 5 L/s → BẮT BUỘC cuộn vòi DN65.")
                if he_so >= 2:
                    ghi_chu.append(
                        "⚠ QCVN 10:2025 H.2.18: ≥ 2 tia/điểm trong nhà SX "
                        "phải bố trí từ 02 tủ chữa cháy CẠNH NHAU "
                        "(hoặc dùng họng kép nếu số tia tính toán ≥ 3).")
                return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                        "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.6"}

    # Không khớp rule nào → fallback
    return {"he_so": 1, "q_per_jet": 2.5,
            "basis": (f"QCVN 10:2025 Bảng H.6: tổ hợp ({bcl}, {h}, {cap}) "
                      f"chưa khớp dòng nào trong bảng → dùng tối thiểu 1×2.5 L/s"),
            "ghi_chu": [
                "⚠ Kiểm tra lại Bậc chịu lửa + Hạng nguy hiểm cháy + Cấp NHC kết cấu. "
                "Nếu là nhà kho cao tầng / hàng nguy hiểm đặc biệt, cần luận chứng "
                "kỹ thuật riêng theo CHÚ THÍCH Bảng H.6."],
            "source": "QCVN 10:2025 Bảng H.6 (fallback)"}


def goi_y_he_so_hong_per_diem(cn_k: str, D: float, R: float,
                              cao_pccc: float = 3.5,
                              tang_total: int = 1, nguoi: int = 0,
                              hanh_lang_dai: float = 0,
                              v_khoang_chay: float = 0,
                              bac_chiu_lua: str = "II",
                              hang_nguy_hiem: str = "C",
                              cap_nhc_kc: str = "S0",
                              cao_tb: float = None) -> dict:
    """Gợi ý số họng/điểm + lưu lượng tia phun theo **QCVN 10:2025/BCA Bảng H.5**.

    QCVN 10:2025/BCA (hiệu lực 30/12/2025) là quy chuẩn mới nhất do BCA ban
    hành, kế thừa và CẬP NHẬT Bảng 11 QCVN 06:2022/BXD. Khác biệt chính so
    với QCVN 06:2022:
      - Mục 1 (chung cư): bỏ ngưỡng "≥ 5 tầng", chỉ giữ "≤ 16" và "> 16-25"
      - Mục 2 (hành chính): bỏ ngưỡng "≥ 6 tầng"
      - Mục 4 (KTX/công cộng): bỏ ngưỡng "≥ 5.000m³"
      - Mục 5 (phụ trợ CN): bỏ ngưỡng "≥ 5.000m³"
      - Thêm chú thích cho hầm đường bộ và nhà để xe dạng kín

    Args:
        cn_k: mã công năng (chung_cu, nha_hat, van_phong, khach_san...)
        D, R: dài × rộng nhà (m)
        cao_tb: chiều cao tầng (m) — dùng tính khối tích
        tang_total: tổng số tầng (nổi + hầm)
        nguoi: số chỗ ngồi (cho rạp hát/CLB/phòng nghe nhìn)
        hanh_lang_dai: chiều dài hành lang chung (m) — quan trọng cho chung cư
        v_khoang_chay: thể tích khoang cháy (m³) — cho nhà để xe dạng kín

    Returns: {he_so, q_per_jet, basis, ghi_chu, source}
    """
    # Khối tích = DT × chiều cao TỔNG. cao_pccc là chiều cao thực toàn nhà
    # (kể cả nhà 1 tầng cao 11m như nhà kho/xưởng).
    # Backward-compat: nếu caller vẫn truyền cao_tb (= chiều cao/tầng), fallback
    # về công thức cũ.
    if D > 0 and R > 0:
        if cao_tb is not None and cao_tb > 0:
            khoi_tich = D * R * cao_tb * tang_total  # legacy: H = cao_tb × số tầng
        else:
            khoi_tich = D * R * cao_pccc  # cao_pccc là chiều cao TỔNG toàn nhà
    else:
        khoi_tich = 0
    ghi_chu = []

    # === Mục 1 Bảng H.5: Nhà chung cư, nhà ở tập thể ===
    if cn_k == "chung_cu":
        if tang_total <= 16:
            he_so = 2 if hanh_lang_dai > 10 else 1
            q = 2.5
            hl_note = (f"hành lang chung {hanh_lang_dai:.0f}m > 10m"
                       if hanh_lang_dai > 10
                       else f"hành lang chung ≤ 10m")
            basis = (f"QCVN 10:2025 Bảng H.5 mục 1: chung cư ≤ 16 tầng, "
                     f"{hl_note} → {he_so} họng/điểm × 2,5 L/s")
        else:  # > 16 đến 25 tầng
            he_so = 3 if hanh_lang_dai > 10 else 2
            q = 2.5
            hl_note = (f"hành lang {hanh_lang_dai:.0f}m > 10m"
                       if hanh_lang_dai > 10 else "hành lang ≤ 10m")
            basis = (f"QCVN 10:2025 Bảng H.5 mục 1: chung cư > 16 tầng "
                     f"({hl_note}) → {he_so} họng/điểm × 2,5 L/s")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 mục 1"}

    # === Mục 2 Bảng H.5: Nhà hành chính (VP, nghiên cứu chuyên ngành) ===
    if cn_k in ("van_phong", "buu_dien"):
        if tang_total <= 10:
            he_so = 2 if khoi_tich > 25000 else 1
        else:
            he_so = 3 if khoi_tich > 25000 else 2
        q = 2.5
        basis = (f"QCVN 10:2025 Bảng H.5 mục 2: nhà hành chính "
                 f"({tang_total} tầng, KT≈{khoi_tich:,.0f}m³) → "
                 f"{he_so} họng/điểm × 2,5 L/s")
        if he_so >= 2:
            ghi_chu.append(
                "⚠ QCVN 10:2025 H.2.18: ≥ 2 tia/điểm trong nhà công cộng "
                "phải bố trí từ 02 tủ chữa cháy CẠNH NHAU (không dùng họng kép).")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 mục 2"}

    # === Mục 3 Bảng H.5: Phòng CLB có sân khấu, nhà hát, rạp chiếu phim,
    # phòng có thiết bị nghe nhìn ===
    # LUÔN 2 họng/điểm; lưu lượng theo số chỗ
    if cn_k == "nha_hat":
        he_so = 2
        q = 5.0 if nguoi > 300 else 2.5
        nguoi_str = f"{nguoi} chỗ" if nguoi > 0 else "chưa khai số chỗ"
        nguoi_ck = ("> 300 chỗ → mỗi tia 5,0 L/s" if nguoi > 300
                    else "≤ 300 chỗ → mỗi tia 2,5 L/s")
        basis = (f"QCVN 10:2025 Bảng H.5 mục 3: phòng CLB có sân khấu / "
                 f"nhà hát / rạp chiếu phim ({nguoi_str}) → "
                 f"LUÔN 2 họng/điểm × {q:g} L/s ({nguoi_ck})")
        ghi_chu.append(
            "⚠ QCVN 10:2025 H.2.18: 2 tia phun/điểm cho nhà công cộng "
            "PHẢI bố trí từ 02 tủ chữa cháy CẠNH NHAU (02 họng khác nhau, "
            "không họng kép).")
        if q >= 5.0:
            ghi_chu.append(
                "⚠ Lưu lượng tia 5 L/s (> 4 L/s) → BẮT BUỘC cuộn vòi DN65 "
                "(QCVN 10:2025 H.2.7 chú thích 2 + mục 2.4.4).")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 mục 3"}

    # === Mục 4 Bảng H.5: KTX & nhà công cộng khác ===
    # (KS, BV, trường, TV, BT, RẠP XIẾC, chợ, ga, mầm non, karaoke, vũ trường,
    #  nhà hàng, nhà ở riêng lẻ kết hợp KD, nhà hỗn hợp, ...)
    cn_muc_4 = {"khach_san", "benh_vien", "truong_hoc", "thu_vien",
                "bao_tang", "nha_ga", "cho_tttm", "cua_hang",
                "the_thao", "karaoke", "mam_non", "vu_truong",
                "nha_hang", "nha_de_xe", "rap_xiec", "nha_hon_hop"}
    if cn_k in cn_muc_4:
        if tang_total <= 10:
            he_so = 2 if khoi_tich > 25000 else 1
        else:  # > 10 tầng
            he_so = 3 if khoi_tich > 25000 else 2
        q = 2.5
        basis = (f"QCVN 10:2025 Bảng H.5 mục 4: nhà công cộng "
                 f"({tang_total} tầng, KT≈{khoi_tich:,.0f}m³) → "
                 f"{he_so} họng/điểm × 2,5 L/s")
        # CHÚ THÍCH 2 Bảng H.5: nhà để xe ô tô dạng kín
        if cn_k == "nha_de_xe" and v_khoang_chay > 0:
            if v_khoang_chay > 5000:
                ghi_chu.append(
                    f"⚠ CHÚ THÍCH 2 Bảng H.5: nhà để xe dạng kín, "
                    f"V khoang cháy {v_khoang_chay:,.0f}m³ > 5.000m³ → "
                    f"2 lăng phun + 5 L/s/tia (override Bảng H.5).")
                q = 5.0
            elif v_khoang_chay >= 500:
                ghi_chu.append(
                    f"⚠ CHÚ THÍCH 2 Bảng H.5: nhà để xe dạng kín, "
                    f"V khoang cháy {v_khoang_chay:,.0f}m³ (500-5.000m³) → "
                    f"2 lăng phun + 2,5 L/s/tia.")
        if he_so >= 2:
            ghi_chu.append(
                "⚠ QCVN 10:2025 H.2.18: ≥ 2 tia/điểm trong nhà công cộng "
                "phải bố trí từ 02 tủ chữa cháy CẠNH NHAU (không dùng họng kép).")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 mục 4"}

    # === Bảng H.6: Nhà sản xuất + nhà kho (route sang tra_bang_h6) ===
    # cn_k: kho_bc (kho hạng C), nong_san (kho nông sản), nha_xuong (xưởng SX)
    if cn_k in ("kho_bc", "nong_san", "nha_xuong"):
        h6 = tra_bang_h6(bac_chiu_lua, hang_nguy_hiem, cap_nhc_kc, khoi_tich)
        return h6

    # === Mục 5 Bảng H.5: Nhà hành chính – phụ trợ CỦA công trình công nghiệp ===
    # (Đây là phần VĂN PHÒNG/HÀNH CHÍNH NẰM TRONG khu công nghiệp, không phải
    # nhà SX/kho — nhà SX/kho dùng Bảng H.6 ở trên)
    if cn_k in ("phu_tro_cn",):
        he_so = 2 if khoi_tich > 25000 else 1
        q = 2.5
        basis = (f"QCVN 10:2025 Bảng H.5 mục 5: nhà hành chính - phụ trợ CN "
                 f"(KT≈{khoi_tich:,.0f}m³) → {he_so} họng/điểm × 2,5 L/s")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 mục 5"}

    # === CHÚ THÍCH 1 Bảng H.5: hầm đường bộ ===
    if cn_k in ("ham_duong_bo",):
        he_so, q = 1, 5.0
        basis = ("QCVN 10:2025 Bảng H.5 CHÚ THÍCH 1: hầm đường bộ → "
                 "1 tia phun × 5 L/s cho 1 điểm cháy")
        ghi_chu.append(
            "⚠ Lưu lượng 5 L/s (> 4 L/s) → BẮT BUỘC cuộn vòi DN65.")
        return {"he_so": he_so, "q_per_jet": q, "basis": basis,
                "ghi_chu": ghi_chu, "source": "QCVN 10:2025 Bảng H.5 CHÚ THÍCH 1"}

    # === Fallback: TCVN 2622 Bảng 14 cho công năng chưa map riêng ===
    if khoi_tich > 25000:
        he_so, q = 2, 2.5
        basis = (f"TCVN 2622 Bảng 14 (fallback): nhà công cộng KT > 25.000m³ "
                 f"({khoi_tich:,.0f}m³) → 2 họng/điểm × 2,5 L/s")
    else:
        he_so, q = 1, 2.5
        basis = "TCVN 2622 Bảng 14 (fallback): 1 họng/điểm × 2,5 L/s"
    if D > 0 and R > 0 and D <= 25 and R <= 25:
        ghi_chu.append(
            "⚠ Nhà D, R ≤ 25m vẫn phải bố trí họng MỖI TẦNG. "
            "TCVN 2622 Điều 10.17-10.18 không cho phép dùng họng tầng trên "
            "cho tầng dưới.")
    return {"he_so": he_so, "q_per_jet": q, "basis": basis,
            "ghi_chu": ghi_chu, "source": "TCVN 2622 Bảng 14 (fallback)"}


# =====================================================================
# 10 SP CHO HỆ THỐNG HỌNG NƯỚC CHỮA CHÁY (TCVN 2622)
# =====================================================================
def tinh_chieu_dai_ong_truc_chinh(D: float, R: float, cao_pccc: float,
                                   floors: int, n_hong: int,
                                   he_so_hong_per_diem: int,
                                   is_nha_o: bool, hanh_lang_dai: float,
                                   has_sprinkler: bool) -> dict:
    """Ước tính chiều dài ống trục chính cho hệ thống họng nước chữa cháy.

    Giả định bố trí:
      - Bể nước + máy bơm đặt tại 1 góc nhà
      - Khoảng cách từ bể đến trục đứng gần nhất ≈ 2D/3
      - Trục đứng dài = chiều cao PCCC (nhà nhiều tầng), hoặc 1.2m (nhà 1 tầng,
        vì họng đặt ở 1.2m theo H.2.12)
      - Họng kép cho phép theo H.2.11: nhà ở+HL≤10m+≥2 tia, hoặc nhà SX/CC+≥3 tia
      - Cần ≥ 2 trục + mạng vòng khi: n_hong ≥ 12 HOẶC có sprinkler

    Returns: dict {
      n_truc, cho_phep_hong_kep,
      L_ngang, L_truc, L_vong, L_total,
      H_truc_dung,
      ghi_chu (list các dòng giải thích cách tính)
    }
    """
    from math import ceil
    gc = []

    # === 1. Quyết định họng kép + số trục đứng (H.2.11) ===
    cho_phep_hong_kep = False
    if he_so_hong_per_diem >= 2:
        if is_nha_o and hanh_lang_dai <= 10:
            cho_phep_hong_kep = True
            gc.append(
                f"• Nhà ở + hành lang chung {hanh_lang_dai:.0f}m ≤ 10m + "
                f"{he_so_hong_per_diem} tia/điểm → CHO PHÉP họng kép (H.2.11 đoạn 2).")
        elif (not is_nha_o) and he_so_hong_per_diem >= 3:
            cho_phep_hong_kep = True
            gc.append(
                f"• Nhà SX/công cộng + {he_so_hong_per_diem} tia/điểm (≥ 3) → "
                f"CHO PHÉP họng kép (H.2.11 đoạn 1).")
        else:
            ly_do = ("nhà công cộng/SX có 2 tia/điểm" if not is_nha_o
                     else f"hành lang {hanh_lang_dai:.0f}m > 10m")
            gc.append(
                f"• {ly_do} → KHÔNG cho phép họng kép, mỗi tia phải từ 1 trục "
                f"đứng riêng (H.2.11 đoạn 3).")

    # Số trục đứng cơ bản
    if cho_phep_hong_kep:
        # Họng kép = 2 tia trên 1 trục. ceil(n_tia/2) trục là đủ.
        n_truc = max(1, ceil(he_so_hong_per_diem / 2))
        gc.append(
            f"• Có họng kép: số trục đứng = ⌈{he_so_hong_per_diem}/2⌉ = {n_truc}.")
    else:
        n_truc = max(1, he_so_hong_per_diem)
        gc.append(f"• Không họng kép: số trục = {he_so_hong_per_diem} (= số tia/điểm).")

    # Điều chỉnh cho mạng vòng (H.2.16)
    can_mach_vong = (n_hong >= 12) or has_sprinkler
    if can_mach_vong:
        if n_truc < 2:
            n_truc = 2
            gc.append(
                f"• {'Có sprinkler' if has_sprinkler else f'n_hong={n_hong} ≥ 12'}"
                f" → BẮT BUỘC ≥ 2 trục + mạng vòng (H.2.16). "
                f"Tăng số trục lên 2.")
        else:
            gc.append(
                f"• {'Có sprinkler' if has_sprinkler else f'n_hong={n_hong} ≥ 12'}"
                f" → cần mạng vòng (H.2.16). Số trục hiện tại {n_truc} đủ.")

    # === 2. Chiều cao trục đứng ===
    if floors == 1:
        H_truc = 1.2
        gc.append(
            f"• Nhà 1 tầng → trục đứng chỉ cao 1,2m (chỉ đến cao độ họng, "
            f"không cần lên đến chiều cao PCCC = {cao_pccc:.1f}m).")
    else:
        H_truc = cao_pccc
        gc.append(
            f"• Nhà {floors} tầng → trục đứng cao = chiều cao PCCC = {cao_pccc:.1f}m.")

    # === 3. Chiều dài ống ngang bể → các trục đứng (L₁) ===
    # Giả định: trục 1 cách bể 2D/3, các trục tiếp theo cách nhau D/2
    if n_truc == 1:
        L_ngang = 2 * D / 3
        gc.append(f"• L_ngang = 2D/3 = 2×{D:.0f}/3 = {L_ngang:.1f}m (1 trục).")
    elif n_truc == 2:
        L_ngang = D  # 2 trục cùng cạnh dài: trục 1 ở 2D/3, trục 2 ở D
        gc.append(f"• L_ngang = D = {D:.0f}m (2 trục cùng cạnh dài).")
    else:
        L_ngang = 2 * D / 3 + (n_truc - 1) * D / 2
        gc.append(
            f"• L_ngang = 2D/3 + (N-1)×D/2 = "
            f"{2*D/3:.1f} + {(n_truc-1)*D/2:.1f} = {L_ngang:.1f}m ({n_truc} trục).")

    # === 4. Tổng chiều dài các trục đứng (L₂) ===
    L_truc = n_truc * H_truc
    gc.append(f"• L_truc = {n_truc} × {H_truc:.1f}m = {L_truc:.1f}m.")

    # === 5. Mạng vòng (L₃) ===
    if can_mach_vong:
        L_vong = D
        gc.append(
            f"• L_vong = D = {D:.0f}m (đoạn nối giữa các trục ở tầng trệt, "
            f"tạo mạng vòng kín).")
    else:
        L_vong = 0
        gc.append(f"• Không yêu cầu mạng vòng (n_hong < 12 và không có sprinkler).")

    # === 6. Tổng ===
    L_total = L_ngang + L_truc + L_vong
    gc.append(
        f"• <b>Tổng L_trục_chính = L_ngang + L_trục + L_vong = "
        f"{L_ngang:.1f} + {L_truc:.1f} + {L_vong:.1f} = {L_total:.1f}m</b>")

    return {
        "n_truc": n_truc,
        "cho_phep_hong_kep": cho_phep_hong_kep,
        "can_mach_vong": can_mach_vong,
        "L_ngang": L_ngang,
        "L_truc": L_truc,
        "L_vong": L_vong,
        "L_total": L_total,
        "H_truc_dung": H_truc,
        "ghi_chu": gc,
    }


def dn_ong_truc_chinh(dn_hong: str) -> str:
    """Chọn DN ống trục chính theo DN họng:
    - Họng DN50 → ống trục chính DN65
    - Họng DN65 → ống trục chính DN80
    """
    return "dn80" if dn_hong == "dn65" else "dn65"


def build_hong_nuoc_slots(n_hong: int, floors: int, D: float, R: float,
                          has_sprinkler: bool = False, dn: str = "dn65",
                          is_nha_o: bool = False, hanh_lang_dai: float = 0,
                          he_so_hong_per_diem: int = 1,
                          cao_pccc: float = 0) -> list:
    """Sinh 10 slots vật tư cho hệ thống chữa cháy bằng nước trong nhà.

    Args:
        n_hong: tổng số họng nước (đã tính bằng tinh_so_hong_nuoc)
        floors: tổng số tầng
        D, R: dài × rộng nhà (m)
        has_sprinkler: có sprinkler kèm không (TCVN 10.16: ≥ 2 ống dẫn)
        is_nha_o: True nếu là nhà ở/chung cư/KTX (cn_k == "chung_cu")
        hanh_lang_dai: chiều dài hành lang chung (m)
        he_so_hong_per_diem: số tia/điểm (1, 2 hoặc 3)

    QCVN 10:2025 H.2.18:
      - Nhà ở + HL ≤ 10m + 2 tia/điểm → cho phép HỌNG KÉP (1 tủ + 1 ống đứng,
        2 cuộn vòi, 2 lăng phun trên cùng vị trí)
      - Nhà ở + HL > 10m + 2 tia/điểm → BẮT BUỘC 2 tủ riêng + 2 ống đứng
      - Nhà công cộng/SX + ≥ 2 tia/điểm → BẮT BUỘC 2 tủ riêng (luôn)
    """
    from math import ceil
    slots = []
    n_hong = max(1, int(n_hong))  # = số đầu ra/họng (số tia tổng)
    floors = max(1, int(floors))

    # === Chuẩn hóa BoQ: MỖI HỌNG (đầu ra) cần 1 bộ thiết bị đầy đủ ===
    # (Họng kép vẫn áp dụng ở logic số trục đứng — nhưng BoQ chuẩn 1 tủ/họng)
    cho_phep_hong_kep = (is_nha_o and hanh_lang_dai <= 10
                        and he_so_hong_per_diem >= 2)
    dn_upper = "DN50" if dn == "dn50" else "DN65"

    # 1. Van góc DN50/DN65 — 1 cái/họng
    slots.append({"label": f"Van góc {dn_upper}",
                  "nhom": "hong_nuoc", "loai": f"van_{dn}", "sl": n_hong})

    # 2. Lăng phun DN50/DN65 — 1 cái/họng
    slots.append({"label": f"Lăng phun chữa cháy {dn_upper}",
                  "nhom": "hong_nuoc", "loai": f"lang_phun_{dn}", "sl": n_hong})

    # 3. Cuộn vòi chữa cháy D50/D65 - 16bar - 20m — 1 cuộn/họng
    d_voi = "D50" if dn == "dn50" else "D65"
    slots.append({"label": f"Cuộn vòi chữa cháy {d_voi}-16bar-20m",
                  "nhom": "hong_nuoc", "loai": f"cuon_voi_{dn}",
                  "sl": n_hong})

    # 4. Tủ chữa cháy vách tường 500×600×180 — 1 tủ/họng
    slots.append({"label": "Tủ chữa cháy vách tường 500×600×180",
                  "nhom": "hong_nuoc", "loai": "tu_chua_chay", "sl": n_hong})

    # 5. Ống nhánh DN50/DN65 đến họng — 3m/họng (cùng DN với họng)
    slots.append({"label": f"Ống thép {dn_upper} nhánh đến họng (m)",
                  "nhom": "hong_nuoc", "loai": f"ong_thep_{dn}",
                  "sl": n_hong * 3})

    # 5. Ống thép trục chính — dùng công thức tinh_chieu_dai_ong_truc_chinh
    chu_vi = 2 * (D + R) if D > 0 and R > 0 else 100
    if cao_pccc > 0 and D > 0:
        kq_ong = tinh_chieu_dai_ong_truc_chinh(
            D=D, R=R, cao_pccc=cao_pccc, floors=floors,
            n_hong=n_hong,
            he_so_hong_per_diem=he_so_hong_per_diem,
            is_nha_o=is_nha_o, hanh_lang_dai=hanh_lang_dai,
            has_sprinkler=has_sprinkler)
        n_ong = int(ceil(kq_ong["L_total"]))
    else:
        # Fallback nếu thiếu data
        n_ong = max(50, int(ceil(n_hong * 5)))
    # DN ống trục chính lớn hơn DN họng 1 cấp
    # (Họng DN50 → trục DN65 ; Họng DN65 → trục DN80)
    dn_truc_code = "dn80" if dn == "dn65" else "dn65"
    dn_truc = dn_truc_code.upper()
    slots.append({"label": f"Ống thép {dn_truc} trục chính (m)",
                  "nhom": "hong_nuoc", "loai": f"ong_thep_{dn_truc_code}",
                  "sl": n_ong})

    # 6. Phụ kiện + Vật tư phụ + Giá đỡ — 3 dòng MẶC ĐỊNH (KHÔNG tra catalog)
    # Sales tự điều chỉnh giá cho từng công trình.
    slots.append({
        "label": "Giá đỡ", "nhom": "hong_nuoc", "loai": "fixed_gia_do",
        "sl": 1,
        "fixed": True,
        "fixed_ten": "Giá đỡ",
        "fixed_gia": 3_000_000,
        "fixed_dv": "Hệ",
    })
    slots.append({
        "label": "Phụ kiện (côn, kép, măng xông, cút ren, tyren, quang treo,…)",
        "nhom": "hong_nuoc", "loai": "fixed_phu_kien",
        "sl": 1,
        "fixed": True,
        "fixed_ten": "Phụ kiện (côn, kép, măng xông, cút ren, tyren, quang treo,…)",
        "fixed_gia": 3_000_000,
        "fixed_dv": "Bộ",
    })
    slots.append({
        "label": "Vật tư phụ (Que hàn, đá cắt, nở sắt, sơn đỏ, sơn chống rỉ,…)",
        "nhom": "hong_nuoc", "loai": "fixed_vat_tu",
        "sl": 1,
        "fixed": True,
        "fixed_ten": "Vật tư phụ (Que hàn, đá cắt, nở sắt, sơn đỏ, sơn chống rỉ,…)",
        "fixed_gia": 3_000_000,
        "fixed_dv": "Bộ",
    })

    # 7. Họng tiếp nước cho xe chữa cháy — 1 bộ (hoặc 2 nếu nhà lớn)
    n_hong_tn = 2 if n_hong > 12 else 1
    slots.append({"label": "Họng tiếp nước cho xe CC (2-4 cửa DN65)",
                  "nhom": "hong_nuoc", "loai": "hong_tiep_nuoc", "sl": n_hong_tn})

    # 8. Trụ chữa cháy ngoài nhà — chu vi ÷ 150m
    n_tru = max(1, int(ceil(chu_vi / 150)))
    slots.append({"label": "Trụ chữa cháy ngoài nhà DN100",
                  "nhom": "hong_nuoc", "loai": "tru_ngoai", "sl": n_tru})

    # 9-10. Cụm bơm + tủ điện — thêm trong build_slots() để tính chung
    #       cho cả họng + sprinkler (TCVN 7336 B.3.8)

    return slots


def chon_dn_hong(cao_pccc: float, he_so_hong_per_diem: int,
                 cong_nang_k: str, q_per_jet: float = 2.5) -> tuple:
    """Chọn đường kính cuộn vòi + van + lăng phun: DN50 hay DN65.
    Trả (dn, basis).

    Căn cứ duy nhất (QCVN 10:2025 H.2.7 CHÚ THÍCH 2 + QCVN 06:2022 CT Bảng 13):
      "Để nhận tia nước đặc lưu lượng đến 4 L/s thì sử dụng DN 50,
       đối với lưu lượng lớn hơn phải sử dụng DN 65."
    → Ngưỡng DN dựa trên **LƯU LƯỢNG MỖI TIA**, KHÔNG phải tổng cộng.
    → 2 tia × 2.5 L/s vẫn dùng DN50 (mỗi tia 2.5 ≤ 4).

    Thêm: QCVN 10:2025 mục 2.4.4 — nhà > 28m phải có đường ống khô DN65.
    """
    # 1. BẮT BUỘC DN65: nhà cao > 28m (mục 2.4.4)
    if cao_pccc > 28:
        return "dn65", "QCVN 10:2025 mục 2.4.4: nhà cao > 28m → DN65 bắt buộc"

    # 2. BẮT BUỘC DN65: lưu lượng MỖI TIA > 4 L/s
    if q_per_jet > 4.0:
        return "dn65", (f"QCVN 10:2025 H.2.7 CHÚ THÍCH 2: lưu lượng tia "
                       f"{q_per_jet:g} L/s > 4 L/s → DN65 bắt buộc")

    # 3. KHUYẾN NGHỊ DN65: công năng nguy hiểm cháy cao (không bắt buộc)
    nguy_hiem_cao = {"kho_bc", "kd_chat_long", "nong_san", "nha_de_xe",
                     "karaoke", "cho_tttm"}
    if cong_nang_k in nguy_hiem_cao:
        return "dn65", (f"Khuyến nghị: công năng '{cong_nang_k}' nguy hiểm "
                       f"cháy cao → ưu tiên DN65 cho an toàn (không bắt buộc).")

    # 4. Mặc định DN50 (kể cả khi ≥ 2 họng/điểm, miễn mỗi tia ≤ 4 L/s)
    return "dn50", (f"QCVN 10:2025 H.2.7: lưu lượng tia {q_per_jet:g} L/s "
                   f"≤ 4 L/s, nhà ≤ 28m → DN50 đủ "
                   f"(số tia/điểm không ảnh hưởng đến DN — chỉ lưu lượng mỗi tia mới quyết định).")


# =====================================================================
# SPRINKLER (TCVN 7336:2021) - tính số đầu phun theo nhóm nguy cơ
# =====================================================================
def chon_nhom_nguy_co_sprinkler(cong_nang_k: str) -> tuple:
    """Phân nhóm nguy cơ cháy theo TCVN 7336 Phụ lục A.
    Trả (nhóm, dt_per_sprinkler, cuong_do_phun_l_s_m2, thoi_gian_phun_phut)."""
    # Nhóm 4.1 (nguy hiểm cao): kho hạng B/C, chất lỏng cháy
    if cong_nang_k in ("kho_bc", "kd_chat_long"):
        return ("4.1", 9, 0.3, 60)
    # Nhóm 3 (TB): cửa hàng có hàng dễ cháy, karaoke, kho thường, SX
    if cong_nang_k in ("karaoke", "nong_san", "nha_de_xe"):
        return ("3", 12, 0.24, 60)
    # Nhóm 2 (TB thấp): cửa hàng, TTTM, nhà hàng, nhà hát, bảo tàng
    if cong_nang_k in ("cua_hang", "cho_tttm", "nha_hang", "nha_hat",
                       "nha_van_hoa", "bao_tang", "thu_vien"):
        return ("2", 12, 0.12, 60)
    # Nhóm 1 (ít nguy hiểm) — mặc định
    return ("1", 12, 0.08, 30)


def tinh_sprinkler(dt_can_bao_ve: float, cong_nang_k: str,
                   rooms: list = None) -> dict:
    """Tính số đầu phun + lưu lượng + bể nước theo TCVN 7336.

    Số đầu phun tính theo **Grid 1D (giả định phòng vuông)**:
        Bước 1: L_max = khoảng cách tối đa giữa sprk (Bảng 1 TCVN 7336)
                - Nhóm 1, 2, 3 → 4m
                - Nhóm 4.1, 4.2 → 3m
        Bước 2: cạnh phòng giả định = √dt_phòng
        Bước 3: n_1d = ⌈cạnh / L_max⌉
        Bước 4: n_sprk_phòng = n_1d²
        Bước 5: n_total = Σ n_sprk_phòng

    Ưu điểm so với cách cũ ⌈dt/12⌉ (hoặc /9):
      - Phản ánh đúng bố trí lưới chữ nhật của TCVN 7336
      - Nhóm nguy hiểm cao (L=3m) ra số sprk nhiều hơn đúng yêu cầu
    """
    from math import ceil, sqrt
    nhom, dt_per_sprk, cd_phun, t_phun = chon_nhom_nguy_co_sprinkler(cong_nang_k)

    # L_max giữa sprk theo nhóm (Bảng 1 TCVN 7336)
    L_max = 3.0 if nhom in ("4.1", "4.2") else 4.0

    rooms_with_dt = [r for r in (rooms or []) if r.get("dt", 0) > 0]
    if rooms_with_dt:
        # Per phòng: Grid 1D (cạnh = √dt)
        n_per_room = []
        for r in rooms_with_dt:
            canh = sqrt(r["dt"])
            n_1d = max(1, ceil(canh / L_max))
            n_per_room.append(n_1d * n_1d)
        n_sprk = sum(n_per_room)
        cong_thuc = (f"Σ ⌈√dt_phòng / {L_max:g}m⌉² trên "
                     f"{len(rooms_with_dt)} phòng = {n_sprk} đầu phun "
                     f"(Grid 1D, L_max nhóm {nhom} = {L_max:g}m)")
    else:
        # Fallback: Grid 1D toàn nhà (giả định 1 phòng = cả DT)
        canh = sqrt(dt_can_bao_ve)
        n_1d = max(1, ceil(canh / L_max))
        n_sprk = n_1d * n_1d
        cong_thuc = (f"⌈√{dt_can_bao_ve:.0f} / {L_max:g}m⌉² = "
                     f"⌈{canh:.1f}/{L_max:g}⌉² = {n_1d}² = {n_sprk} đầu phun "
                     f"(Grid 1D, L_max nhóm {nhom} = {L_max:g}m)")

    # Lưu lượng = cường độ × diện tích tính toán tối thiểu
    # Theo Bảng 1: nhóm 1 = 10 l/s, nhóm 2 = 30 l/s, nhóm 3 = 60 l/s, nhóm 4.1 = 110 l/s
    luu_luong_table = {"1": 10, "2": 30, "3": 60, "4.1": 110, "4.2": 65}
    luu_luong = luu_luong_table.get(nhom, 30)

    # Bể nước = lưu lượng × thời gian (đổi l/s × phút → m³)
    # 1 l/s × 60 phút = 60 lít/phút × 60 phút = 3.600 lít = 3,6 m³ → l/s × phút × 0,06
    the_tich_be = round(luu_luong * t_phun * 0.06, 1)

    return {
        "nhom": nhom,
        "dt_per_sprk": dt_per_sprk,
        "n_sprk": n_sprk,
        "cd_phun": cd_phun,
        "luu_luong": luu_luong,
        "t_phun": t_phun,
        "the_tich_be": the_tich_be,
        "cong_thuc": cong_thuc,
        "basis": (f"Nhóm {nhom} (TCVN 7336 Bảng 1) → 1 đầu phun / {dt_per_sprk}m². "
                  f"{cong_thuc}. "
                  f"Lưu lượng: {luu_luong} l/s, thời gian: {t_phun} phút, "
                  f"bể dự trữ tối thiểu: {the_tich_be} m³"),
    }





# =====================================================================
# Bảng IV.1.2 — Đặc tính riêng K_t của ống thép GOST 3262-75 (ống nước,
# tương đương ống thép tráng kẽm dùng phổ biến tại VN)
# K_t có đơn vị l⁶/s² → H_ms = (Q²/K_t) × L với Q [L/s], L [m] → H [m]
# Nguồn: Sổ tay thiết kế VNIIPO 2002 + TCVN 7336:2021 Bảng B.2
# =====================================================================
_KT_ONG_THEP = {
    "dn15": 0.18, "dn20": 0.926, "dn25": 3.65, "dn32": 16.5,
    "dn40": 34.5, "dn50": 135, "dn65": 517, "dn80": 1262,
    "dn90": 2725, "dn100": 5205, "dn125": 16940, "dn150": 43000,
}


def _kt_lookup(dn_code: str) -> float:
    """Tra K_t theo mã DN; nếu không có dùng DN gần nhất trên."""
    if dn_code in _KT_ONG_THEP:
        return _KT_ONG_THEP[dn_code]
    return 5205.0  # fallback DN100


def _h_ma_sat_chinh_xac(Q_ls: float, L_m: float, dn_code: str) -> float:
    """H_ms = (Q²/K_t) × L  — Sổ tay VNIIPO 2002 mục IV.1.5-1.6."""
    if Q_ls <= 0 or L_m <= 0:
        return 0.0
    Kt = _kt_lookup(dn_code)
    return (Q_ls * Q_ls / Kt) * L_m


def tinh_cum_bom(q_hong_ls: float = 0.0,
                 q_sprk_ls: float = 0.0,
                 cao_pccc: float = 0.0,
                 dai_nha: float = 0.0,
                 dn_hong: str = "dn50",
                 nhom_sprk: str = "1",
                 has_van_av: bool = False,
                 dn_truc_chinh: str = "dn100") -> dict:
    """Tính Q và H của cụm bơm chữa cháy chung (sprk + họng).

    CĂN CỨ:
      - TCVN 7336:2021 mục B.3.8 (Q tổng) + B.3.9 (cấu thành H) + B.3.13 (cục bộ 20%)
      - Sổ tay thiết kế VNIIPO 2002, Phần IV mục 1.4 + 3 (công thức IV.1.4,
        IV.1.5, IV.1.6, IV.3.1)
      - TCVN 2622:1995 (áp đầu vòi họng DN50 = 21m, DN65 = 28m)

    Công thức cột áp (sổ tay IV.1.4):
        P = P_o + P_z + P_m + P_s + P_yy + P_n
      P_o  — áp đầu phun chủ đạo
      P_z  — chênh cao hình học (cao_PCCC + bể chìm 3m)
      P_m  — tổn thất tuyến tính ống (Bảng IV.1.2: H = Q²/K_t × L)
      P_s  — tổn thất cục bộ = 0.2 × P_m (mục IV.1.3)
      P_yy — tổn thất van báo động Alarm Valve sprinkler (3-5m)
      P_n  — tổn thất nội bộ trong cụm bơm (5-7m)

    Công suất động cơ (sổ tay IV.3.1):
        N_dv (kW) = K × Q × H × ρ × g / (1000 × η_bơm × η_truyền)
                  ≈ K × Q_m³h × H_m / (367 × η_bơm × η_truyền)
        K=1.15, η_bơm=0.65, η_truyền=1.0 (trục trực tiếp)
    """
    # ----- Q (L/s + m³/h) -----
    Q_breakdown = []
    if q_hong_ls > 0:
        Q_breakdown.append(("Họng nước trong nhà", q_hong_ls))
    if q_sprk_ls > 0:
        Q_breakdown.append(("Sprinkler (Bảng 1 TCVN 7336)", q_sprk_ls))
    Q_ls = q_hong_ls + q_sprk_ls
    Q_m3h = round(Q_ls * 3.6, 1)

    # ----- H (m) -----
    H_breakdown = []

    # P_z: chênh cao + bể chìm 3m
    H_be_chim = 3.0
    P_z = cao_pccc + H_be_chim
    H_breakdown.append(
        (f"P_z chênh cao (PCCC {cao_pccc:.0f}m + bể chìm 3m)", P_z))

    # P_o: áp đầu phun chủ đạo
    H_dau_hong = 21.0 if (dn_hong or "dn50").lower() == "dn50" else 28.0
    H_dau_sprk = 5.0 if nhom_sprk in ("1", "2") else 10.0
    if q_hong_ls > 0 and q_sprk_ls > 0:
        P_o = max(H_dau_hong, H_dau_sprk)
        lbl_po = (f"P_o áp đầu phun (max họng {H_dau_hong:.0f}m, "
                  f"sprk {H_dau_sprk:.0f}m)")
    elif q_hong_ls > 0:
        P_o = H_dau_hong
        lbl_po = f"P_o áp đầu vòi họng {dn_hong.upper()} (TCVN 2622)"
    else:
        P_o = H_dau_sprk
        lbl_po = f"P_o áp đầu sprinkler nhóm {nhom_sprk} (TCVN 7336 Bảng 1)"
    H_breakdown.append((lbl_po, P_o))

    # P_m: tổn thất ma sát ống — Bảng IV.1.2 chính xác
    # L_tổng = trục đứng (cao) + đoạn ngang bơm-trục (≈ dai_nha)
    #          + đoạn ngang xa nhất 1 tầng (≈ dai_nha / 2)
    L_ms = cao_pccc + dai_nha + dai_nha / 2
    P_m = _h_ma_sat_chinh_xac(Q_ls, L_ms, dn_truc_chinh)
    H_breakdown.append(
        (f"P_m ma sát ống {dn_truc_chinh.upper()} ({L_ms:.0f}m, "
         f"K_t={_kt_lookup(dn_truc_chinh):.0f})", P_m))

    # P_s: tổn thất cục bộ = 0.2 × P_m
    P_s = 0.2 * P_m
    H_breakdown.append(("P_s cục bộ (0.2 × P_m, IV.1.3)", P_s))

    # P_yy: tổn thất Alarm Valve sprinkler — chỉ có khi có sprk
    if has_van_av:
        P_yy = 4.0
        H_breakdown.append(("P_yy van báo động Alarm Valve sprk", P_yy))
    else:
        P_yy = 0.0

    # P_n: tổn thất nội bộ cụm bơm
    P_n = 6.0
    H_breakdown.append(("P_n nội bộ cụm bơm", P_n))

    # Tổng (theo sổ tay không có dự phòng riêng vì K=1.15 đã có ở N_dv)
    H_m = round(P_o + P_z + P_m + P_s + P_yy + P_n, 1)

    # ----- N_dv: công suất động cơ — sổ tay IV.3.1 -----
    # N_dv (kW) = K × Q_m³h × H_m / (367 × η_b × η_t)
    # với 367 = 1000 × η_g × const. Quy về: Q_m³/h × H_m / 367 = công suất nước (kW)
    K_du_phong = 1.15
    eta_bom = 0.65
    eta_truyen = 1.0
    N_nuoc = Q_m3h * H_m / 367.0  # kW thuần — chuyển động chất lỏng
    N_dv = round(K_du_phong * N_nuoc / (eta_bom * eta_truyen), 1)

    # ----- HTML thuyết minh -----
    lines = []
    lines.append("<div style='font-size:12px;'>")
    lines.append("<b>Lưu lượng cụm bơm Q</b> (TCVN 7336 B.3.8 = sổ tay VNIIPO):<br>")
    for lbl, v in Q_breakdown:
        lines.append(f"&nbsp;&nbsp;• {lbl}: {v:.1f} L/s<br>")
    lines.append(f"<b>&nbsp;&nbsp;Σ Q = {Q_ls:.1f} L/s "
                 f"= {Q_m3h:.0f} m³/h</b><br><br>")

    lines.append("<b>Cột áp cụm bơm H</b> (sổ tay VNIIPO 2002 mục IV.1.4):<br>")
    lines.append("&nbsp;&nbsp;<i>P = P_o + P_z + P_m + P_s + P_yy + P_n</i><br>")
    for lbl, v in H_breakdown:
        lines.append(f"&nbsp;&nbsp;• {lbl}: {v:.1f} m<br>")
    lines.append(f"<b>&nbsp;&nbsp;Σ H = {H_m:.1f} m</b><br><br>")

    lines.append("<b>Công suất động cơ điện</b> "
                 "(sổ tay VNIIPO 2002 mục IV.3.1):<br>")
    lines.append(f"&nbsp;&nbsp;N_dv = K × Q × H / (367 × η) "
                 f"= 1.15 × {Q_m3h:.0f} × {H_m:.0f} / (367 × 0.65) "
                 f"≈ <b>{N_dv} kW</b><br>")
    lines.append("&nbsp;&nbsp;<i>(K=1.15 dự phòng, η_bơm=0.65, η_truyền=1.0)</i><br><br>")

    lines.append("<b>Khuyến nghị:</b> Cụm bơm có "
                 f"<b>Q ≥ {Q_ls:.1f} L/s ({Q_m3h:.0f} m³/h)</b>, "
                 f"<b>H ≥ {H_m:.0f} m</b>, "
                 f"<b>động cơ ≥ {N_dv} kW</b>.<br>")
    lines.append("Sales chọn model thực tế (Pentax / Ebara / Wilo / Grundfos…) "
                 "qua nút <b>'Đổi model'</b> với Q-H-N ≥ giá trị trên.")
    lines.append("</div>")

    return {
        "Q_ls": round(Q_ls, 2),
        "Q_m3h": Q_m3h,
        "H_m": H_m,
        "N_dv_kw": N_dv,
        "Q_breakdown": Q_breakdown,
        "H_breakdown": H_breakdown,
        "thuyet_minh": "".join(lines),
        "label_bom": (f"Cụm bơm chữa cháy ≥ Q {Q_m3h:.0f} m³/h, "
                      f"H {H_m:.0f} m, N {N_dv} kW "
                      f"(chính + dự bị + jockey)"),
    }


# =====================================================================
# TCVN 7336:2021 — Bảng B.3: DN ống sprinkler theo số đầu phun downstream
# =====================================================================
# Mapping: (max_sprk, DN_code, DN_label)
_BANG_B3_AP_CAO = [   # P ≥ 0.5 MPa (mặc định)
    (3,   "dn25", "DN25"), (5,   "dn32", "DN32"),
    (9,   "dn40", "DN40"), (18,  "dn50", "DN50"),
    # Theo TCVN 7336 Bảng B.3 là DN70, nhưng thực tế thi công VN dùng DN65
    # (ống thép tráng kẽm DN65 phổ biến, DN70 hiếm).
    (28,  "dn65", "DN65"), (46,  "dn80", "DN80"),
    (80,  "dn100", "DN100"), (150, "dn125", "DN125"),
]


def dn_ong_sprinkler(n_sprk_downstream: int, ap_cao: bool = True) -> tuple:
    """Tra Bảng B.3 TCVN 7336:2021. Trả (dn_code, dn_label).
    n_sprk_downstream = số sprinkler ở phía sau đoạn ống (bao gồm đoạn này).
    """
    for max_n, dn_code, dn_label in _BANG_B3_AP_CAO:
        if n_sprk_downstream <= max_n:
            return dn_code, dn_label
    return "dn150", "DN150"  # > 150 sprk


def tinh_chieu_dai_ong_sprinkler(n_sprk_total: int, dt_per_sprk: int,
                                  D: float, R: float, cao_pccc: float,
                                  floors: int,
                                  sprk_per_nhanh: int = 5) -> dict:
    """Tính chiều dài + DN ống cho hệ sprinkler theo TCVN 7336 Bảng B.3.

    Cấu trúc hệ:
      - Trục đứng: từ bơm lên các tầng, DN tra theo n_sprk_total
      - Ống phân phối ngang/tầng: chạy theo dài nhà D, DN theo n_sprk/tầng
      - Ống nhánh: vuông góc ống phân phối, mỗi nhánh có sprk_per_nhanh đầu phun
        DN tăng dần dọc nhánh theo Bảng B.3 (1-3 sprk: DN25; 4-5: DN32; v.v.)

    Returns: dict {L_per_dn, L_phan_phoi, L_truc, dn_phan_phoi, dn_truc,
                   n_zone, n_sprk_per_floor, n_nhanh_per_floor, sprk_per_nhanh,
                   L_sprk, ghi_chu}
    """
    from math import sqrt, ceil
    gc = []
    n_sprk_total = max(1, int(n_sprk_total))
    floors = max(1, int(floors))
    nb = max(1, int(sprk_per_nhanh))

    # 1. Khoảng cách sprk + bố trí mỗi tầng
    L_sprk = sqrt(dt_per_sprk)
    n_sprk_per_floor = ceil(n_sprk_total / floors)
    nf = ceil(n_sprk_per_floor / nb)
    lb = (nb - 1) * L_sprk if nb > 1 else L_sprk

    gc.append(f"<b>📐 Bố trí mỗi tầng:</b>")
    gc.append(f"• 1 đầu phun phủ {dt_per_sprk}m² → khoảng cách giữa sprk "
              f"L = √{dt_per_sprk} = <b>{L_sprk:.2f}m</b>")
    gc.append(f"• Số sprk/tầng = ⌈{n_sprk_total}/{floors}⌉ = <b>{n_sprk_per_floor}</b>")
    gc.append(f"• Mỗi nhánh {nb} sprk → dài nhánh = ({nb}−1) × {L_sprk:.2f} "
              f"= <b>{lb:.1f}m</b>")
    gc.append(f"• Số nhánh/tầng = ⌈{n_sprk_per_floor}/{nb}⌉ = <b>{nf}</b>")

    # 2. Phân đoạn DN trên 1 nhánh (Bảng B.3)
    # Đoạn (k+1) từ đầu nhánh có (k+1) sprk downstream
    from collections import Counter
    dn_per_seg = []
    for k in range(nb):
        n_d = k + 1
        dn_code, _ = dn_ong_sprinkler(n_d, ap_cao=True)
        dn_per_seg.append(dn_code)
    dn_count = Counter(dn_per_seg)

    gc.append(f"<b>📏 Phân đoạn DN trên 1 nhánh (Bảng B.3 TCVN 7336, P≥0,5 MPa):</b>")
    L_per_dn = {}   # dict dn_code -> tổng m
    for dn_code, c in sorted(dn_count.items()):
        L_nhanh_dn = floors * nf * c * L_sprk
        L_per_dn[dn_code] = L_nhanh_dn
        gc.append(
            f"• {dn_code.upper()}: {c} đoạn/nhánh × {L_sprk:.2f}m × "
            f"{nf} nhánh × {floors} tầng = <b>{L_nhanh_dn:.1f}m</b>")

    # 3. Ống phân phối ngang/tầng — TAPER DN tăng dần từ cuối → trục đứng
    # Mỗi tầng có 1 ống ngang dài D, chia thành nf đoạn (giữa các nhánh).
    # Đoạn k (đếm từ cuối ống ngang): cấp cho k nhánh = k × nb sprk downstream.
    # DN đoạn k tra Bảng B.3 theo (k × nb) → tăng dần về phía trục đứng.
    from collections import defaultdict
    L_pp_per_dn = defaultdict(float)
    seg_len = D / nf if nf > 0 else D
    pp_seg_count = defaultdict(int)  # đếm số đoạn theo DN (cho ghi chú)
    for k in range(1, nf + 1):
        n_downstream = k * nb
        dn_code, _ = dn_ong_sprinkler(n_downstream, ap_cao=True)
        L_pp_per_dn[dn_code] += seg_len * floors
        pp_seg_count[dn_code] += 1

    gc.append(f"<b>📏 Ống phân phối ngang mỗi tầng (TAPER tăng DN từ cuối → trục):</b>")
    gc.append(f"• Mỗi tầng có 1 ống ngang dài {D:.0f}m, chia "
              f"{nf} đoạn × {seg_len:.2f}m (= khoảng cách giữa các nhánh)")
    gc.append(f"• Đoạn k (k=1 ở cuối) cấp cho k×{nb} sprk → DN theo Bảng B.3:")
    for dn_code in sorted(L_pp_per_dn.keys(),
                          key=lambda x: int(x.replace("dn", ""))):
        c = pp_seg_count[dn_code]
        L = L_pp_per_dn[dn_code]
        gc.append(f"  - {dn_code.upper()}: {c} đoạn × {seg_len:.2f}m × "
                  f"{floors} tầng = <b>{L:.1f}m</b>")

    # 4. Trục đứng — từ trạm bơm (đặt 1 góc nhà) lên trục đứng + đi lên các tầng
    # Gồm: đoạn ngang từ bơm đến chân trục đứng (≈ D) + đoạn đứng (cao PCCC)
    dn_truc_code, dn_truc_label = dn_ong_sprinkler(n_sprk_total, ap_cao=True)
    L_truc_doan_ngang = D  # đoạn nối từ bơm/bể nước đến chân trục đứng
    L_truc_doan_dung = cao_pccc
    L_truc = L_truc_doan_ngang + L_truc_doan_dung
    gc.append(f"<b>📏 Trục đứng (riser) + đoạn nối tới bơm:</b>")
    gc.append(f"• DN theo {n_sprk_total} sprk tổng (Bảng B.3) = "
              f"<b>{dn_truc_label}</b>")
    gc.append(f"• Đoạn ngang nối bơm → chân trục: {L_truc_doan_ngang:.0f}m "
              f"(= chiều dài nhà D)")
    gc.append(f"• Đoạn đứng từ chân trục lên đỉnh: {L_truc_doan_dung:.0f}m "
              f"(= cao PCCC)")
    gc.append(f"• <b>Tổng L_trục = {L_truc:.0f}m</b>")

    # 5. Số zone (cụm van điều khiển) — max 800 sprk/zone (TCVN 7336)
    n_zone = max(1, ceil(n_sprk_total / 800))
    gc.append(f"<b>🔧 Cụm van điều khiển:</b> ⌈{n_sprk_total}/800⌉ = "
              f"<b>{n_zone} cụm</b> (max 800 sprk/zone — TCVN 7336)")

    # Tổng chiều dài ống phân phối ngang (cho hiển thị)
    L_phan_phoi_total = sum(L_pp_per_dn.values())

    return {
        "L_per_dn": L_per_dn,           # ống nhánh per DN
        "L_pp_per_dn": dict(L_pp_per_dn),  # ống phân phối ngang per DN (taper)
        "L_phan_phoi": L_phan_phoi_total,
        "L_truc": L_truc,
        "dn_truc": dn_truc_code,
        "dn_truc_label": dn_truc_label,
        "n_zone": n_zone,
        "n_sprk_per_floor": n_sprk_per_floor,
        "n_nhanh_per_floor": nf,
        "sprk_per_nhanh": nb,
        "L_sprk": L_sprk,
        "lb": lb,
        "ghi_chu": gc,
    }


# =====================================================================
# Chi tiết SP cho hệ thống Sprinkler (theo TCVN 7336)
# =====================================================================
def build_sprinkler_slots(n_sprk: int, dt: float, cn_k: str,
                          tang_noi: int = 1, tang_ham: int = 0,
                          D: float = 0, R: float = 0, cao_pccc: float = 0,
                          sprk_per_nhanh: int = 5) -> list:
    """Sinh các slot SP cho hệ thống sprinkler. Tầng hầm dùng upright,
    tầng nổi dùng pendant."""
    from math import ceil
    slots = []
    n_sprk = max(1, int(n_sprk))

    # 1. Đầu phun Sprinkler
    floors_total = max(1, tang_noi + tang_ham)
    if tang_ham > 0 and floors_total > 0:
        n_upright = max(1, int(round(n_sprk * tang_ham / floors_total)))
        n_pendant = max(0, n_sprk - n_upright)
        if n_pendant > 0:
            slots.append({"label": "Đầu phun Sprinkler hướng xuống (Pendant) — tầng nổi",
                          "nhom": "chua_chay", "loai": "sprinkler_down",
                          "sl": n_pendant})
        slots.append({"label": "Đầu phun Sprinkler hướng lên (Upright) — tầng hầm",
                      "nhom": "chua_chay", "loai": "sprinkler_up",
                      "sl": n_upright})
    else:
        slots.append({"label": "Đầu phun Sprinkler hướng xuống (Pendant)",
                      "nhom": "chua_chay", "loai": "sprinkler_down",
                      "sl": n_sprk})

    # 2. Tính DN + chiều dài ống theo TCVN 7336 Bảng B.3
    floors = max(1, tang_noi + tang_ham)
    nhom, dt_per_sprk, _, _ = chon_nhom_nguy_co_sprinkler(cn_k)
    if D > 0 and cao_pccc > 0:
        kq_ong = tinh_chieu_dai_ong_sprinkler(
            n_sprk_total=n_sprk, dt_per_sprk=dt_per_sprk,
            D=D, R=R, cao_pccc=cao_pccc, floors=floors,
            sprk_per_nhanh=sprk_per_nhanh)
        # Gộp ống nhánh + ống phân phối ngang (taper) theo DN — 1 dòng/DN
        from collections import defaultdict
        L_total_per_dn = defaultdict(float)
        for dn_code, L in kq_ong["L_per_dn"].items():
            L_total_per_dn[dn_code] += L
        for dn_code, L in kq_ong.get("L_pp_per_dn", {}).items():
            L_total_per_dn[dn_code] += L
        # Dùng loai chung "ong_thep_dnXX" (nhom=hong_nuoc) để match SP "Ống thép
        # tráng kẽm DNxx" có sẵn trong bảng giá Fsales (dùng chung cho cả sprinkler
        # và họng nước — cùng 1 SP vật tư).
        for dn_code in sorted(L_total_per_dn.keys(),
                              key=lambda x: int(x.replace("dn", ""))):
            L = L_total_per_dn[dn_code]
            slots.append({
                "label": f"Ống thép {dn_code.upper()} sprinkler "
                         f"(nhánh + phân phối) (m)",
                "nhom": "hong_nuoc", "loai": f"ong_thep_{dn_code}",
                "sl": int(ceil(L)),
            })
        slots.append({
            "label": f"Ống thép {kq_ong['dn_truc_label']} trục đứng + "
                     f"ngang đến bơm sprinkler (m)",
            "nhom": "hong_nuoc",
            "loai": f"ong_thep_{kq_ong['dn_truc']}",
            "sl": int(ceil(kq_ong["L_truc"])),
        })
        n_zone = kq_ong["n_zone"]
    else:
        n_ong = max(50, int(ceil(n_sprk * 2)))
        slots.append({"label": "Ống thép DN65 mạng phân phối sprinkler (m)",
                      "nhom": "chua_chay", "loai": "ong_sprk_dn65",
                      "sl": n_ong})
        n_zone = max(1, ceil(n_sprk / 800))

    # 3. Van báo động (alarm valve)
    slots.append({"label": "Van báo động Alarm Valve DN100/DN150",
                  "nhom": "chua_chay", "loai": "van_bao_dong", "sl": n_zone})

    # 4-5. Cụm bơm + tủ điện — thêm trong build_slots() để tính chung
    #      cho cả họng + sprinkler (TCVN 7336 B.3.8)

    # 6. 3 dòng ước tính
    slots.append({
        "label": "Giá đỡ ống sprinkler",
        "nhom": "chua_chay", "loai": "fixed_gia_do_sprk",
        "sl": 1, "fixed": True,
        "fixed_ten": "Giá đỡ ống sprinkler",
        "fixed_gia": 3_000_000, "fixed_dv": "Hệ",
    })
    slots.append({
        "label": "Phụ kiện sprinkler (côn, kép, măng xông, cút ren, tyren, quang treo,…)",
        "nhom": "chua_chay", "loai": "fixed_phu_kien_sprk",
        "sl": 1, "fixed": True,
        "fixed_ten": "Phụ kiện sprinkler (côn, kép, măng xông, cút ren, tyren, quang treo,…)",
        "fixed_gia": 3_000_000, "fixed_dv": "Bộ",
    })
    slots.append({
        "label": "Vật tư phụ sprinkler (Que hàn, đá cắt, nở sắt, sơn đỏ, sơn chống rỉ,…)",
        "nhom": "chua_chay", "loai": "fixed_vat_tu_sprk",
        "sl": 1, "fixed": True,
        "fixed_ten": "Vật tư phụ sprinkler (Que hàn, đá cắt, nở sắt, sơn đỏ, sơn chống rỉ,…)",
        "fixed_gia": 3_000_000, "fixed_dv": "Bộ",
    })

    return slots


# =====================================================================
# NHÓM HỆ THỐNG BÁO CHÁY
# =====================================================================

def normalize_model(s: str) -> str:
    if not s:
        return ""
    out = str(s).upper()
    for ch in "()[]{}":
        out = out.replace(ch, "")
    for ch in ("-", "_", " ", "\t", "\n"):
        out = out.replace(ch, "")
    return out




# =====================================================================
# GỢI Ý BƠM TỪ bom_catalog.json (Affetti + các hãng khác nếu có)
# =====================================================================
_BOM_CATALOG_CACHE = None


def _load_bom_catalog():
    """Load bom_catalog.json (cached)."""
    global _BOM_CATALOG_CACHE
    if _BOM_CATALOG_CACHE is not None:
        return _BOM_CATALOG_CACHE
    import json, os, sys
    try:
        here = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        here = os.getcwd()
    p = os.path.join(here, "bom_catalog.json")
    if not os.path.exists(p):
        _BOM_CATALOG_CACHE = {}
        return _BOM_CATALOG_CACHE
    try:
        with open(p, encoding="utf-8") as f:
            _BOM_CATALOG_CACHE = json.load(f) or {}
    except Exception:
        _BOM_CATALOG_CACHE = {}
    return _BOM_CATALOG_CACHE


def goi_y_bom(q_m3h: float, h_m: float, n_kw_min: float = 0,
              loai_bom: str = "lien_truc_2900",
              top_n: int = 3, exclude_bu_ap: bool = True) -> list:
    """Gợi ý top N bơm thỏa Q-H-N từ bom_catalog.json.

    Tham số:
      q_m3h      — Lưu lượng cần thiết (m³/h)
      h_m        — Cột áp cần thiết (m)
      n_kw_min   — Công suất tối thiểu (kW) — chỉ filter nếu > 0
      loai_bom   — Nhóm bơm ưu tiên: 'lien_truc_2900' / 'roi_truc_2900'
                   / 'diesel_3000' / 'bu_ap' / 'da_tang'.
                   Đặt 'auto' để tự chọn theo công suất (≤37kW: liền trục,
                   >37kW: rời trục).
      top_n      — Số lượng gợi ý trả về (mặc định 3, sort theo giá tăng)
      exclude_bu_ap — Loại bơm bù áp ra khỏi gợi ý chính (mặc định True)

    Trả: list dict [{model, kw, q_min, q_max, h_min, h_max, gia, loai, hang}]
    """
    cat = _load_bom_catalog()
    if not cat:
        return []
    hang = cat.get("_meta", {}).get("hang", "")

    # Auto-chọn nhóm theo công suất
    if loai_bom == "auto":
        if n_kw_min and n_kw_min > 37:
            loai_bom = "roi_truc_2900"
        else:
            loai_bom = "lien_truc_2900"

    candidates = []
    for key, items in cat.items():
        if not isinstance(items, list):
            continue
        if exclude_bu_ap and key == "bu_ap":
            continue
        for x in items:
            # Filter Q-H-N
            if x["q_max"] < q_m3h:
                continue
            if x["h_max"] < h_m:
                continue
            if n_kw_min and x.get("kw") and x["kw"] < n_kw_min:
                continue
            x2 = dict(x)
            x2["loai"] = key
            x2["hang"] = hang
            x2["uu_tien"] = 1 if key == loai_bom else 2
            candidates.append(x2)

    # Sort: ưu tiên loai_bom đúng, sau đó giá thấp
    candidates.sort(key=lambda x: (x["uu_tien"], x["gia"]))
    return candidates[:top_n]


_BAO_CHAY_GROUPS_RAW = {
    "co_day": [
        "FCP-2", "FCP-4", "FCP-5", "FCP-8",
        "FSP-10", "FSP-15", "FSP-16", "FSP-20", "FSP-24", "FSP-32", "FSP-40",
        "FSS-001", "FSH-001", "FSH-002", "FSBL-001", "FSL-001", "FSM-001",
        "Fcom1", "Fcom3",
    ],
    "khong_day": [
        "WCP1", "(WCP-1)", "WSD1", "(WSD-1)", "WHD1", "(WHD-1)",
        "WSHD1", "(WSHD-1)", "WMCP1", "(WMCP-1)", "WBL1", "(WBL-1)",
        "FSMBL-001", "RSA", "WBM", "WBM-1", "WBM-2", "Fcom1",
    ],
    "cuc_bo": [
        "FS-SS-001", "FS-SS-002", "FS-SH-001", "FS-SH-002",
        "FS-SSH-002", "FSMBL-002", "Fcom2",
    ],
}

BAO_CHAY_GROUPS = {
    g: {normalize_model(m) for m in lst}
    for g, lst in _BAO_CHAY_GROUPS_RAW.items()
}

BAO_CHAY_GROUP_LABELS = {
    "khong_day": "Không dây (mặc định)",
    "co_day": "Có dây",
    "cuc_bo": "Cục bộ",
}


def bao_chay_groups_of(model: str) -> set:
    m = normalize_model(model)
    if not m:
        return set()
    return {g for g, codes in BAO_CHAY_GROUPS.items() if m in codes}


def is_in_bao_chay_group(model: str, group: str) -> bool:
    m = normalize_model(model)
    return m in BAO_CHAY_GROUPS.get(group, set())


def truyen_tin_model_of(group: str) -> str:
    return "Fcom2" if group == "cuc_bo" else "Fcom1"


DEFAULT_TRUNG_TAM_BY_GROUP = {
    "co_day": "FCP-4",
    "khong_day": "WCP-1",
}


def default_trung_tam_model(group: str) -> str:
    return DEFAULT_TRUNG_TAM_BY_GROUP.get(group, "")
