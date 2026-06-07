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
        return max(1, ceil(dt / 12))            # 1 sprinkler / 12 m²
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

    # Báo cháy độc lập
    if has("độc lập"):
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
        return {"nhom": "chua_chay", "loai": "sprinkler"}
    if "bơm" in s and "chữa cháy" in s:
        return {"nhom": "chua_chay", "loai": "bom"}
    if has("van báo động", "chữa cháy khí", "chữa cháy tự động", "fm200"):
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
    if has("phụ kiện", "cút", "tê", "mặt bích"):
        if "ống" in s or "chữa cháy" in s:
            return {"nhom": "hong_nuoc", "loai": "phu_kien_ong"}
    if has("ống thép") and ("dn65" in s or "dn50" in s or "dn100" in s):
        return {"nhom": "hong_nuoc", "loai": "ong_thep"}
    if has("tủ chữa cháy", "hộp đựng họng", "hộp chữa cháy"):
        return {"nhom": "hong_nuoc", "loai": "tu_chua_chay"}
    if has("cuộn vòi"):
        return {"nhom": "hong_nuoc", "loai": "cuon_voi"}
    if has("lăng phun"):
        return {"nhom": "hong_nuoc", "loai": "lang_phun"}
    if has("van") and ("dn65" in s or "dn50" in s or "họng" in s):
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

    # --- Báo cháy: tự động / độc lập / không ---
    if not bc["req"]:
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

    # --- Truyền tin báo cháy (bắt buộc khi có trang bị báo cháy) ---
    if bc_state != "khong":
        items.append({"ht": "Thiết bị truyền tin báo cháy (kết nối CSDL PCCC)",
                      "req": True,
                      "dk": "bắt buộc với cơ sở thuộc diện quản lý PCCC (Phụ lục I) · hoàn thành chậm nhất 01/7/2027",
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

    items.append({"ht": "Đèn chỉ dẫn thoát nạn (EXIT) & đèn chiếu sáng sự cố", "req": True,
                  "dk": "mặc định 1 đèn EXIT + 1 đèn chiếu sáng sự cố mỗi tầng · nhập tab \"Thoát nạn & chiếu sáng\" để tính chính xác",
                  "can": "TCVN 13456:2022; QCVN 06/BXD",
                  "nhom": "den"})

    items.append({"ht": "Bộ nội quy - tiêu lệnh PCCC", "req": True,
                  "dk": "mỗi tầng 01 bộ, niêm yết nơi dễ thấy (gần bình chữa cháy, lối/cầu thang thoát nạn)",
                  "can": "NĐ 105/2025, Điều 3; TCVN 3890:2023",
                  "nhom": "noi_quy"})

    # Cửa ngăn cháy (QCVN 06:2022/BXD)
    cnc = tinh_cua_ngan_chay(cn, i)
    if cnc["sl_total"] > 0:
        ei_label = cnc["loai_ei"].upper().replace("_", " ")
        items.append({"ht": "Hệ thống cửa ngăn cháy",
                      "req": True,
                      "dk": f"loại {ei_label} (ước tính ~{cnc['sl_total']} bộ): {cnc['basis']}",
                      "can": "QCVN 06:2022/BXD (mục 3.2.11, Bảng 1, Bảng 2, Bảng A.1)",
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

        elif nhom == "truyen_tin":
            add("Thiết bị truyền tin báo cháy", "truyen_tin", None, 1)

        elif nhom == "chua_chay":
            add("Đầu phun Sprinkler", "chua_chay", "sprinkler", uoc_sl("chua_chay", i))
            add("Cụm bơm chữa cháy", "chua_chay", "bom", 1)

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
            for s in build_hong_nuoc_slots(n_hong, floors, D, R, has_sprk):
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
    elif R <= 2 * r:
        # TH2: nhà rộng vừa — 2 dãy họng đối diện, mỗi dãy phủ R/2
        case = "rộng_vừa"
        R_half = R / 2
        if R_half >= r:
            d = 1.0
        else:
            d = 2 * sqrt(r * r - R_half * R_half)
            if d < 1:
                d = 1.0
        n_per_row = ceil(D / d) + 1
        n_per_floor = 2 * n_per_row
        formula = (f"25 < R={R:.1f}m ≤ 50m → 2 dãy. "
                   f"d = 2√(25²-{R_half:.1f}²) = {d:.1f}m. "
                   f"n = 2 × (⌈{D:.1f}/{d:.1f}⌉ + 1) = {n_per_floor}")
    else:
        # TH3: rất rộng — fallback theo diện tích
        case = "rất_rộng"
        area_per_hong = 0.5 * 3.1416 * r * r
        n_per_floor = ceil((D * R) / area_per_hong)
        formula = (f"R={R:.1f}m > 50m → cảnh báo phức tạp. "
                   f"Tạm tính theo DT: n = ⌈{D*R:.0f}/{area_per_hong:.0f}⌉ = {n_per_floor}")
        warnings.append(
            "Nhà quá rộng (R > 50m). Cần khảo sát thực tế, app chỉ tính sơ bộ theo diện tích.")

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


def goi_y_he_so_hong_per_diem(cn_k: str, D: float, R: float, cao_tb: float = 3.5) -> dict:
    """Gợi ý hệ số họng/điểm dựa trên Bảng 14 TCVN 2622 + ngoại lệ Điều 10.17.

    Returns: {he_so, basis, ghi_chu}
    """
    khoi_tich_tang = D * R * cao_tb
    cn_nho_duoc_giam = {"kho_bc", "cua_hang", "nong_san"}  # hạng C/D/E
    ghi_chu = []

    # TCVN 10.17 ngoại lệ: nhà ≤ 1000m³ hạng C/D/E → 1 họng/điểm
    if khoi_tich_tang <= 1000 and cn_k in cn_nho_duoc_giam:
        he_so = 1
        basis = (f"TCVN 2622 Điều 10.17: nhà nhỏ ≤ 1.000m³ (KT={khoi_tich_tang:.0f}m³) "
                 f"hạng sản xuất C/D/E → cho phép mỗi điểm chỉ 1 họng")
        return {"he_so": he_so, "basis": basis, "ghi_chu": ghi_chu}

    # Bảng 14 — các trường hợp cần 2 họng/điểm
    can_2_hong = False
    reasons = []
    # Mục 7: nhà ở 12-16 tầng (cần tang để biết, tạm dùng khối tích lớn)
    # Mục 9, 13, 14: khối tích >25.000m³ với công năng công cộng/kho
    if khoi_tich_tang > 25000:
        if cn_k in ("chung_cu", "khach_san", "benh_vien", "truong_hoc",
                    "thu_vien", "bao_tang", "nha_van_hoa", "nha_ga",
                    "cho_tttm", "cua_hang", "van_phong", "buu_dien"):
            can_2_hong = True
            reasons.append("khối tích > 25.000m³ + công năng công cộng/cửa hàng")
    # Mục 12: nhà hát/rạp/CLB > 800 chỗ — không có biến số_chỗ trực tiếp ở đây
    # Mục 13: nhà sản xuất
    if cn_k in cn_nho_duoc_giam and khoi_tich_tang > 1000:
        can_2_hong = True
        reasons.append("nhà SX/kho hạng C/D/E > 1.000m³")

    if can_2_hong:
        he_so = 2
        basis = "TCVN 2622 Bảng 14: " + "; ".join(reasons)
    else:
        he_so = 1
        basis = "TCVN 2622 Bảng 14: 1 họng/điểm (mặc định cho nhà thường)"

    # Cảnh báo: nhà nhỏ D & R ≤ 25m KHÔNG được dùng họng tầng trên cho tầng dưới
    if D <= 25 and R <= 25:
        ghi_chu.append(
            "⚠ Lưu ý: nhà D, R ≤ 25m vẫn phải có họng MỖI TẦNG. "
            "TCVN 2622 Điều 10.17-10.18 không cho phép dùng họng tầng trên "
            "cho tầng dưới (rủi ro khói, sàn không an toàn).")

    return {"he_so": he_so, "basis": basis, "ghi_chu": ghi_chu}


# =====================================================================
# 10 SP CHO HỆ THỐNG HỌNG NƯỚC CHỮA CHÁY (TCVN 2622)
# =====================================================================
def build_hong_nuoc_slots(n_hong: int, floors: int, D: float, R: float,
                          has_sprinkler: bool = False) -> list:
    """Sinh 10 slots vật tư cho hệ thống chữa cháy bằng nước trong nhà.

    Args:
        n_hong: tổng số họng nước (đã tính bằng tinh_so_hong_nuoc)
        floors: tổng số tầng
        D, R: dài × rộng nhà (m)
        has_sprinkler: có sprinkler kèm không (TCVN 10.16: ≥ 2 ống dẫn)
    """
    from math import ceil
    slots = []
    n_hong = max(1, int(n_hong))
    floors = max(1, int(floors))

    # 1. Van khóa DN65 — 1 cái/họng
    slots.append({"label": "Van khóa DN65 cho họng nước",
                  "nhom": "hong_nuoc", "loai": "van_dn65", "sl": n_hong})

    # 2. Lăng phun DN65 — 1 cái/họng
    slots.append({"label": "Lăng phun chữa cháy DN65",
                  "nhom": "hong_nuoc", "loai": "lang_phun", "sl": n_hong})

    # 3. Cuộn vòi mềm D65-20m — 1 cuộn/họng
    slots.append({"label": "Cuộn vòi chữa cháy D65-20m",
                  "nhom": "hong_nuoc", "loai": "cuon_voi", "sl": n_hong})

    # 4. Tủ chữa cháy (hộp đựng họng) — 1 tủ/họng (có thể gộp 2 họng/tủ tùy thiết kế)
    slots.append({"label": "Tủ chữa cháy / Hộp đựng họng",
                  "nhom": "hong_nuoc", "loai": "tu_chua_chay", "sl": n_hong})

    # 5. Ống thép DN65 — ước tính theo công thức:
    # = ống đứng (cao 3,5m × số tầng × số ống đứng) + ống ngang (chu vi × 0,3)
    # đơn giản hóa: ~ 15m/họng (kinh nghiệm thi công)
    chu_vi = 2 * (D + R) if D > 0 and R > 0 else 100
    ong_dung = floors * 3.5 * (2 if has_sprinkler else 1)  # 2 ống nếu có sprinkler
    ong_ngang = chu_vi * 0.3 * floors  # ước tính
    n_ong = int(ceil(ong_dung + ong_ngang))
    slots.append({"label": "Ống thép DN65 (m)",
                  "nhom": "hong_nuoc", "loai": "ong_thep", "sl": n_ong})

    # 6. Phụ kiện đường ống (cút, tê, mặt bích, gioăng) — gộp 1 dòng
    # Số lượng ước tính = số họng × 4 (mỗi họng cần ~4 phụ kiện)
    slots.append({"label": "Phụ kiện đường ống (cút, tê, mặt bích, gioăng)",
                  "nhom": "hong_nuoc", "loai": "phu_kien_ong", "sl": n_hong * 4})

    # 7. Họng tiếp nước cho xe chữa cháy — 1 bộ (hoặc 2 nếu nhà lớn)
    n_hong_tn = 2 if n_hong > 12 else 1
    slots.append({"label": "Họng tiếp nước cho xe CC (2-4 cửa DN65)",
                  "nhom": "hong_nuoc", "loai": "hong_tiep_nuoc", "sl": n_hong_tn})

    # 8. Trụ chữa cháy ngoài nhà — chu vi ÷ 150m
    n_tru = max(1, int(ceil(chu_vi / 150)))
    slots.append({"label": "Trụ chữa cháy ngoài nhà DN100",
                  "nhom": "hong_nuoc", "loai": "tru_ngoai", "sl": n_tru})

    # 9. Cụm bơm chữa cháy (gộp: chính + dự bị + jockey = 3 bơm)
    slots.append({"label": "Cụm bơm chữa cháy (chính + dự bị + jockey)",
                  "nhom": "hong_nuoc", "loai": "cum_bom", "sl": 1})

    # 10. Tủ điện điều khiển bơm
    slots.append({"label": "Tủ điện điều khiển cụm bơm",
                  "nhom": "hong_nuoc", "loai": "tu_dien_bom", "sl": 1})

    return slots


if __name__ == "__main__":
    cases = [
        ("Nhà ở KD nhỏ", "nha_o_kd",
         {"dt": 200, "cao": 12, "tang": 4, "ham": 0, "nguoi": 0, "chau": 0}),
        ("Chung cư 12 tầng", "chung_cu",
         {"dt": 6000, "cao": 40, "tang": 12, "ham": 1, "nguoi": 0, "chau": 0}),
        ("Karaoke 2 tầng", "karaoke",
         {"dt": 400, "cao": 8, "tang": 2, "ham": 0, "nguoi": 80, "chau": 0}),
        ("Mầm non lớn", "mam_non",
         {"dt": 400, "cao": 10, "tang": 3, "ham": 0, "nguoi": 0, "chau": 120}),
    ]
    for name, k, inp in cases:
        print(f"\n=== {name} ({k}) ===")
        r = phan_tich(k, inp)
        print(f"bcState = {r['bcState']}")
        for it in r["items"]:
            mark = "[BB]" if it["req"] else "[--]"
            print(f"  {mark} {it['ht']}  ({it['nhom']})  — {it['dk']}")

# =====================================================================
# NHÓM HỆ THỐNG BÁO CHÁY (file "Lựa chọn thiết bị báo cháy.xlsx")
# 3 nhóm độc quyền, không trộn lẫn được trong cùng 1 hệ thống
# =====================================================================

def normalize_model(s: str) -> str:
    """Chuẩn hóa model code để so khớp linh hoạt: bỏ ngoặc, dấu cách,
    gạch ngang/dưới, viết hoa. VD '(WSD-1)' -> 'WSD1', 'fs ss 002' -> 'FSSS002'."""
    if not s:
        return ""
    out = str(s).upper()
    for ch in "()[]{}":
        out = out.replace(ch, "")
    for ch in ("-", "_", " ", "\t", "\n"):
        out = out.replace(ch, "")
    return out


# Tập model code cho mỗi nhóm. Dùng tên normalized (xem normalize_model).
_BAO_CHAY_GROUPS_RAW = {
    "co_day": [  # Hệ thống báo cháy tự động CÓ DÂY
        "FCP-2", "FCP-4", "FCP-5", "FCP-8",
        "FSP-10", "FSP-15", "FSP-16", "FSP-20", "FSP-24", "FSP-32", "FSP-40",
        "FSS-001",          # đầu báo khói 24V có dây
        "FSH-001", "FSH-002",  # đầu báo nhiệt có dây
        "FSBL-001",         # còi đèn báo cháy
        "FSL-001",          # đèn báo cháy
        "FSM-001",          # nút ấn báo cháy
        "Fcom1", "Fcom3",   # truyền tin (có dây)
    ],
    "khong_day": [  # Hệ thống báo cháy tự động KHÔNG DÂY (mặc định)
        "WCP1", "(WCP-1)",
        "WSD1", "(WSD-1)",
        "WHD1", "(WHD-1)",
        "WSHD1", "(WSHD-1)",
        "WMCP1", "(WMCP-1)",
        "WBL1", "(WBL-1)",
        "FSMBL-001",        # tổ hợp chuông đèn nút ấn không dây
        "RSA", "WBM", "WBM-1", "WBM-2",
        "Fcom1",            # truyền tin (dùng chung với có dây)
    ],
    "cuc_bo": [  # Thiết bị báo cháy CỤC BỘ (cho công trình quy mô nhỏ)
        "FS-SS-001", "FS-SS-002",   # đầu báo khói cục bộ/độc lập
        "FS-SH-001", "FS-SH-002",   # đầu báo nhiệt cục bộ/độc lập
        "FS-SSH-002",               # khói-nhiệt kết hợp cục bộ
        "FSMBL-002",                # tổ hợp chuông đèn nút ấn cục bộ
        "Fcom2",                    # truyền tin cho thiết bị cục bộ
    ],
}

# Build set normalized cho lookup nhanh
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
    """Trả set tên nhóm mà model thuộc về. Model có thể thuộc nhiều nhóm
    (vd Fcom1 thuộc cả co_day và khong_day)."""
    m = normalize_model(model)
    if not m:
        return set()
    return {g for g, codes in BAO_CHAY_GROUPS.items() if m in codes}


def is_in_bao_chay_group(model: str, group: str) -> bool:
    """Model có thuộc nhóm `group` (co_day/khong_day/cuc_bo) không?"""
    m = normalize_model(model)
    return m in BAO_CHAY_GROUPS.get(group, set())


def truyen_tin_model_of(group: str) -> str:
    """Model thiết bị truyền tin cho nhóm: cục bộ -> Fcom2, còn lại -> Fcom1."""
    return "Fcom2" if group == "cuc_bo" else "Fcom1"

# Tủ trung tâm mặc định cho mỗi nhóm hệ báo cháy (model code dùng nhiều nhất)
DEFAULT_TRUNG_TAM_BY_GROUP = {
    "co_day": "FCP-4",
    "khong_day": "WCP-1",
    # cuc_bo: không có tủ trung tâm
}


def default_trung_tam_model(group: str) -> str:
    """Trả model code tủ trung tâm mặc định cho nhóm, hoặc "" nếu không có."""
    return DEFAULT_TRUNG_TAM_BY_GROUP.get(group, "")
