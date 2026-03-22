import misc


# =========================================================
#  TIỆN ÍCH CHUNG
# =========================================================

def _iso_week_condition(date_col: str) -> str:
    """
    Điều kiện SQL cho TUẦN ISO (Thứ 2 → CN)
    YEARWEEK(col, 1) = YEARWEEK(CURDATE(), 1)
    """
    return f"YEARWEEK({date_col}, 1) = YEARWEEK(CURDATE(), 1)"


# =========================================================
#  BÁO GIÁ
# =========================================================

def quotes_this_week():
    """
    Danh sách báo giá tạo trong tuần ISO hiện tại
    """
    return misc.sql_all(
        f"""
        SELECT so_bg, lead_id, sotien, user, ngaythang
        FROM ds_bao_gia
        WHERE {_iso_week_condition("ngaythang")}
        ORDER BY ngaythang DESC
        """
    )


def quotes_this_week_count():
    """
    Số lượng báo giá trong tuần ISO
    """
    return misc.sql_one(
        f"""
        SELECT COUNT(*)
        FROM ds_bao_gia
        WHERE {_iso_week_condition("ngaythang")}
        """
    )[0]


def big_quotes_unclosed(min_value=100_000_000):
    """
    Báo giá lớn chưa chốt
    """
    return misc.sql_all(
        """
        SELECT so_bg, lead_id, sotien, user, ngaythang
        FROM ds_bao_gia
        WHERE sotien >= %s
          AND thanh_cong != 'T'
        ORDER BY sotien DESC
        """,
        (min_value,)
    )


# =========================================================
#  KHÁCH HÀNG / LEAD
# =========================================================

def new_potential_customers_this_week():
    """
    Khách hàng tiềm năng mới trong tuần ISO
    Định nghĩa:
    - Có ít nhất 1 báo giá HOẶC
    - Có đơn hàng hoàn thành
    """
    return misc.sql_all(
        f"""
        SELECT DISTINCT
            l.lead_id,
            l.name,
            l.company,
            l.phu_trach
        FROM sale_lead l
        LEFT JOIN ds_bao_gia bg ON bg.lead_id = l.lead_id
        LEFT JOIN ds_don_hang dh ON dh.lead_id = l.lead_id
        WHERE {_iso_week_condition("l.time_create")}
          AND (bg.so_bg IS NOT NULL OR dh.da_hoan_thanh = 'T')
        ORDER BY l.time_create DESC
        """
    )


def overdue_leads(days=3, limit=20):
    """
    Lead quá hạn (quá X ngày)
    """
    return misc.sql_all(
        """
        SELECT
            lead_id,
            name,
            company,
            phu_trach,
            DATEDIFF(NOW(), time_create) AS overdue_days,
            status
        FROM sale_lead
        WHERE status NOT IN ('Đã giao hàng', 'Done - Thất bại')
          AND time_create < DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY overdue_days DESC
        LIMIT %s
        """,
        (days, limit)
    )


# =========================================================
#  TỒN KHO
# =========================================================

def inventory_total_value():
    """
    Tổng giá trị tồn kho = SUM(số lượng * giá đầu vào)
    """
    return misc.sql_one(
        """
        SELECT SUM(so_luong * gia_dau_vao)
        FROM ton_kho
        """
    )[0] or 0


# =========================================================
#  SALE / HIỆU SUẤT
# =========================================================

def top_sales_by_quotes_this_week(limit=5):
    """
    Sale tạo nhiều báo giá nhất trong tuần ISO
    """
    return misc.sql_all(
        f"""
        SELECT user, COUNT(*) AS total_quotes
        FROM ds_bao_gia
        WHERE {_iso_week_condition("ngaythang")}
        GROUP BY user
        ORDER BY total_quotes DESC
        LIMIT %s
        """,
        (limit,)
    )
