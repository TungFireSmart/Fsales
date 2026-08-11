# -*- coding: utf-8 -*-
"""
Soi cờ "bận" (user.check_busy) của nhân viên.

⚠️ Từ 11/8/2026 cờ này KHÔNG còn chặn ai nhận cơ hội mới nữa — luật "một nhân
viên một cơ hội" đã bị bỏ (việc B7). Cờ chỉ còn dùng để *ưu tiên* khi chia việc
tự động trong misc.pick_auto_assign_user(). Script giữ lại để:
  · kiểm tra việc chia lead tự động đang ưu tiên ai;
  · rà lead tồn đọng đã nhận nhưng chưa ai báo giá.

CHỈ ĐỌC — script này không UPDATE/DELETE bất cứ thứ gì.
Dùng đúng credential của app qua misc.py, không tự cấu hình lại kết nối.

Chạy:
    .venv\\Scripts\\python.exe chan_doan_check_busy.py Nga
    .venv\\Scripts\\python.exe chan_doan_check_busy.py            # xem toàn bộ user đang bận
"""
import sys

import misc

# Đúng 6 status mà misc.refresh_user_busy() coi là "còn việc chưa xong".
BUSY_STATUSES = (
    'Đã nhận việc',
    'Đã quá hạn báo giá',
    'Cần cập nhật lại',
    'Đã quá 10 ngày',
    misc.LEAD_STATUS_ANNA_ASSIGNED,
    misc.LEAD_STATUS_ANNA_ASSIGNED_LEGACY,
)

# Danh sách loại trừ trong main.py:456 — lead ở các status này KHÔNG bị
# rule tuổi đời tự đẩy ngược về trạng thái bận.
TERMINAL_STATUSES = (
    'Đã đặt hàng', 'Đã thanh toán', 'Đã giao hàng',
    'Đã trả lại toàn bộ', 'Done - Thất bại',
)


def _in_clause(n):
    return ', '.join(['%s'] * n)


def tim_user(tu_khoa):
    """Tìm user theo tên gần đúng. Trả về list (full_name, check_busy, power)."""
    if tu_khoa:
        return misc.sql_all(
            "SELECT full_name, check_busy, power FROM user WHERE full_name LIKE %s",
            ('%' + tu_khoa + '%',), default=[],
        ) or []
    return misc.sql_all(
        "SELECT full_name, check_busy, power FROM user WHERE check_busy = 1",
        None, default=[],
    ) or []


def dem_busy_thuc_te(full_name):
    """Chạy ĐÚNG câu đếm của misc.refresh_user_busy(), nhưng không ghi cờ."""
    row = misc.sql_one(
        "SELECT COUNT(*) FROM sale_lead l "
        "WHERE l.phu_trach = %s AND l.check_delete != '1' "
        f"AND TRIM(l.status) IN ({_in_clause(len(BUSY_STATUSES))}) "
        "AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id)",
        (full_name,) + BUSY_STATUSES,
        default=(0,),
    )
    return int((row or [0])[0] or 0)


def dem_theo_luat_cu(full_name):
    """Đếm theo luật TRƯỚC 11/8/2026 — để thấy thay đổi đã gỡ được bao nhiêu."""
    row = misc.sql_one(
        "SELECT COUNT(*) FROM sale_lead "
        "WHERE phu_trach = %s AND check_delete != '1' "
        f"AND TRIM(status) IN ({_in_clause(len(BUSY_STATUSES))})",
        (full_name,) + BUSY_STATUSES,
        default=(0,),
    )
    return int((row or [0])[0] or 0)


def lead_dang_giu_co(full_name):
    """Lead thật sự còn khoá theo luật MỚI: đã nhận, chưa có báo giá."""
    return misc.sql_all(
        "SELECT l.lead_id, l.ten_co_hoi, l.status, l.time_create, l.time_nhan_viec, "
        "       TIMESTAMPDIFF(DAY, l.time_create, NOW()) AS so_ngay, "
        "       EXISTS(SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id) AS co_bao_gia, "
        "       EXISTS(SELECT 1 FROM ds_don_hang o WHERE o.lead_id = l.lead_id) AS co_don_hang "
        "FROM sale_lead l "
        "WHERE l.phu_trach = %s AND l.check_delete != '1' "
        f"AND TRIM(l.status) IN ({_in_clause(len(BUSY_STATUSES))}) "
        "AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id) "
        "ORDER BY l.time_create ASC",
        (full_name,) + BUSY_STATUSES,
        default=[],
    ) or []


def kiem_tra_lech_ten(full_name):
    """
    Cờ bận đếm theo sale_lead.phu_trach = user.full_name.
    Nếu hai bên lệch nhau khoảng trắng / dấu tiếng Việt tổ hợp thì đếm sai.
    """
    rows = misc.sql_all(
        "SELECT DISTINCT phu_trach FROM sale_lead "
        "WHERE phu_trach IS NOT NULL AND TRIM(phu_trach) != '' AND phu_trach != 'waiting' "
        "AND phu_trach LIKE %s",
        ('%' + full_name.strip()[-6:] + '%',), default=[],
    ) or []
    return [r[0] for r in rows if r[0] != full_name]


def bao_cao(full_name, co_cache, power):
    print('=' * 74)
    print(f'NHÂN VIÊN: {full_name!r}   power={power}')
    print(f'  user.check_busy (cờ app đang đọc) = {co_cache}')

    cu = dem_theo_luat_cu(full_name)
    thuc_te = dem_busy_thuc_te(full_name)
    print(f'  Đếm theo luật CŨ (trước 11/8/2026)  = {cu}')
    print(f'  Đếm theo luật MỚI (chưa có báo giá) = {thuc_te}')
    if cu != thuc_te:
        print(f'  ✅ Thay đổi 11/8/2026 gỡ được {cu - thuc_te} lead khỏi cờ bận.')

    if int(co_cache or 0) == 1 and thuc_te == 0:
        print('  ⚠️  CỜ BỊ TREO: không còn lead bận nào nhưng cờ vẫn = 1.')
        print('      → nguyên nhân 2 hoặc 3 (cờ cache lệch), KHÔNG phải do lead nào cả.')
    elif int(co_cache or 0) == 0 and thuc_te > 0:
        print('  ⚠️  Cờ = 0 nhưng thực tế còn lead bận — cờ chưa được refresh.')

    leads = lead_dang_giu_co(full_name)
    if not leads:
        print('  → Không còn lead nào giữ cờ.')
    else:
        print(f'\n  {len(leads)} LEAD ĐÃ NHẬN NHƯNG CHƯA BÁO GIÁ (cũ nhất trước):\n')
        for (lid, ten, st, tao, nhan, ngay, bg, dh) in leads:
            ten = (ten or '')[:44]
            print(f'  ── lead #{lid}  [{st}]')
            print(f'     tên      : {ten}')
            print(f'     tạo lúc  : {tao}   (đã {ngay} ngày)')
            print(f'     nhận lúc : {nhan}')
            print(f'     báo giá  : {"CÓ" if bg else "không"}    đơn hàng: {"CÓ" if dh else "không"}')
            if bg and not dh:
                print('     💡 Đã báo giá nhưng chưa thành đơn → đúng cái bẫy ở main.py:456')
                print("        ('Đã báo giá' không nằm trong base_filter nên bị đẩy ngược về trạng thái bận)")
            if st == 'Đã quá 10 ngày':
                print('     🔒 Status này KHÔNG có đường thoát tự động — khoá vĩnh viễn.')
            print()

    lech = kiem_tra_lech_ten(full_name)
    if lech:
        print('  ⚠️  Có bản ghi sale_lead.phu_trach viết khác user.full_name:')
        for x in lech:
            print(f'        {x!r}')
        print('      → lead của những tên này KHÔNG được đếm, cờ có thể sai cả hai chiều.')
    print()


def main():
    tu_khoa = sys.argv[1] if len(sys.argv) > 1 else ''

    if misc.LOI_CONFIG:
        print('Không đọc được cấu hình CSDL:', misc.LOI_CONFIG)
        return 1

    users = tim_user(tu_khoa)
    if not users:
        print(f'Không tìm thấy user nào khớp {tu_khoa!r}.')
        print('Thử liệt kê toàn bộ:')
        for r in (misc.sql_all('SELECT full_name FROM user WHERE power != 0', None, default=[]) or []):
            print('   ', repr(r[0]))
        return 1

    for full_name, co_cache, power in users:
        bao_cao(full_name, co_cache, power)

    print('Script này CHỈ ĐỌC.')
    print('Từ 11/8/2026 cờ bận KHÔNG chặn ai nhận cơ hội mới nữa (việc B7).')
    print('Lead liệt kê ở trên chỉ là việc tồn đọng chưa báo giá — dọn khi rảnh,')
    print('bằng cách mở lead trong app → combo trạng thái → "Done - Thất bại".')
    return 0


if __name__ == '__main__':
    sys.exit(main())
