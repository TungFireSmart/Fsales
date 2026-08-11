# -*- coding: utf-8 -*-
"""
Kiểm tra trước khi build & phát hành. CHỈ ĐỌC, không sửa gì.

Lý do tồn tại: repo không có test tự động (điểm mù số 2 trong CLAUDE.md), nên mọi
"sửa xong rồi" đều là niềm tin. Script này bắt được lớp lỗi rẻ tiền nhất mà lại
hay gây phải phát hành lại: import gãy, hàm bị gọi nhưng không tồn tại, số phiên
bản lệch giữa version.py và file .iss, và chốt chặn cũ vô tình bị dựng lại.

Nó KHÔNG thay được việc mở app bấm thử.

Chạy:
    .venv\\Scripts\\python.exe kiem_tra_truoc_phat_hanh.py
"""
import ast
import glob
import importlib
import os
import re
import sys

loi = []
canh_bao = []


def dat(ok, mo_ta, chi_tiet='', nghiem_trong=True):
    if ok:
        print(f'  ✅ {mo_ta}')
        return True
    print(f'  {"❌" if nghiem_trong else "⚠️ "} {mo_ta}')
    if chi_tiet:
        for d in str(chi_tiet).splitlines():
            print(f'       {d}')
    (loi if nghiem_trong else canh_bao).append(mo_ta)
    return False


# ─────────────────────────────────────────────────────────────────────────
print('\n[1/5] Import toàn bộ module (bắt ImportError / lỗi lúc nạp)')

MODULE_BO_QUA = {'kiem_tra_truoc_phat_hanh', 'chan_doan_check_busy', 'run_sql_file', 'hinhanh_rc'}
for f in sorted(glob.glob('*.py')):
    ten = os.path.splitext(f)[0]
    if ten in MODULE_BO_QUA:
        continue
    try:
        importlib.import_module(ten)
        print(f'  ✅ {ten}')
    except Exception as e:
        dat(False, f'{ten} — {type(e).__name__}: {e}')


# ─────────────────────────────────────────────────────────────────────────
print('\n[2/5] Mọi self.X() được gọi đều phải có thật')

def quet_ham_thieu(duong_dan):
    cay = ast.parse(open(duong_dan, encoding='utf-8').read())
    thieu = []
    for cls in [n for n in ast.walk(cay) if isinstance(n, ast.ClassDef)]:
        co = {n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for n in ast.walk(cls):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self'):
                ten = n.func.attr
                # Bỏ qua method kế thừa từ Qt: chỉ soi tên "kiểu nghiệp vụ"
                if ten in co or '_' not in ten or ten.startswith('__'):
                    continue
                thieu.append((cls.name, ten, n.lineno))
    return thieu

# Chỉ kiểm main.py — nơi đã từng có nhan_viec_by_id gọi mà không định nghĩa (B6).
tat_ca_ham = set()
for f in glob.glob('*.py'):
    try:
        for n in ast.walk(ast.parse(open(f, encoding='utf-8').read())):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tat_ca_ham.add(n.name)
    except Exception:
        pass

nghi_ngo = [(c, t, l) for (c, t, l) in quet_ham_thieu('main.py') if t not in tat_ca_ham]
dat(not nghi_ngo, 'main.py không còn self.X() gọi vào hàm không tồn tại',
    '\n'.join(f'main.py:{l}  {c}.{t}()' for c, t, l in nghi_ngo))


# ─────────────────────────────────────────────────────────────────────────
print('\n[3/5] Luật "một nhân viên một cơ hội" phải ở trạng thái ĐÃ BỎ (B7)')

src_main = open('main.py', encoding='utf-8').read()

# Bỏ chú thích để không bắt nhầm phần giải thích lịch sử
src_khong_chu_thich = '\n'.join(
    d for d in src_main.splitlines() if not d.lstrip().startswith('#')
)

dat('nhan_viec_by_id' in tat_ca_ham, 'nhan_viec_by_id() đã được định nghĩa')
dat('SELECT check_busy' not in src_khong_chu_thich,
    'main.py không còn đọc thẳng cột check_busy để quyết định')
dat('cơ hội cũ chưa xử lý' not in src_khong_chu_thich,
    'Không còn câu chặn "vẫn còn cơ hội cũ chưa xử lý"')

src_misc = open('misc.py', encoding='utf-8').read()
dat('NOT EXISTS (SELECT 1 FROM ds_bao_gia' in src_misc,
    'refresh_user_busy() đã loại lead đã có báo giá (B1)')

# ── Màn hình "Cơ hội mới" phải ở trạng thái ĐÃ TẮT (B10) ───────────────
# Nút này từng được bật lại ở 4 chỗ khác nhau, nên kiểm cả 4.
dat('_tat_nut_co_hoi_moi' in tat_ca_ham, 'Có hàm _tat_nut_co_hoi_moi()')
dat(not re.search(r'but_co_hoi_moi\.setEnabled\(True\)', src_khong_chu_thich),
    'Không còn chỗ nào setEnabled(True) cho but_co_hoi_moi')
dat("'but_co_hoi_moi'" not in src_khong_chu_thich,
    'but_co_hoi_moi đã ra khỏi danh sách bật lại của _set_main_loading_lock')
dat(not re.search(r'but_co_hoi_moi\.clicked\.connect', src_khong_chu_thich),
    'but_co_hoi_moi không còn nối vào show_co_hoi_moi()')
dat(not re.search(r'self\.show_co_hoi_moi\s*\(', src_khong_chu_thich),
    'Không còn đường nào gọi show_co_hoi_moi()')


# ─────────────────────────────────────────────────────────────────────────
print('\n[4/5] Số phiên bản phải khớp nhau')

from version import APP_VERSION
print(f'  · version.py  APP_VERSION = {APP_VERSION}')

iss = f'release/FsalesInstaller-{APP_VERSION}.iss'
if dat(os.path.exists(iss), f'Có file {iss}'):
    noi_dung = open(iss, encoding='utf-8-sig').read()
    m = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', noi_dung)
    dat(m and m.group(1) == APP_VERSION,
        f'AppVersion trong .iss khớp {APP_VERSION}',
        f'tìm thấy: {m.group(1) if m else "không có"}')
    dat('B210A5E9-4E37-4D65-A91F-56F3B05B7E09' in noi_dung,
        'AppId giữ nguyên (đổi AppId ⇒ cài thành bản thứ hai)')

# Số mới phải lớn hơn mọi số đã phát hành
da_phat = []
for f in glob.glob('release/FsalesInstaller-*.iss'):
    m = re.search(r'FsalesInstaller-(\d+(?:\.\d+)*)\.iss', f)
    if m:
        da_phat.append(tuple(int(x) for x in m.group(1).split('.')))
hien_tai = tuple(int(x) for x in APP_VERSION.split('.'))
cao_hon = [v for v in da_phat if v > hien_tai]
dat(not cao_hon, f'{APP_VERSION} là số cao nhất trong release/',
    'cao hơn: ' + ', '.join('.'.join(map(str, v)) for v in cao_hon))


# ─────────────────────────────────────────────────────────────────────────
print('\n[5/5] Kết nối CSDL + ảnh hưởng thực tế của thay đổi')

try:
    import misc
    if misc.LOI_CONFIG:
        dat(False, 'Đọc được cấu hình CSDL', misc.LOI_CONFIG)
    else:
        users = misc.sql_all(
            'SELECT full_name FROM user WHERE power != 0', None, default=[]) or []
        if dat(bool(users), 'Kết nối được CSDL sản xuất'):
            print(f'\n  {"Nhân viên":<28} {"luật cũ":>8} {"luật mới":>9}  gỡ được')
            print(f'  {"-"*28} {"-"*8} {"-"*9}  {"-"*8}')
            tong_cu = tong_moi = 0
            for (ten,) in users:
                cu = misc.sql_one(
                    "SELECT COUNT(*) FROM sale_lead WHERE phu_trach = %s AND check_delete != '1' "
                    "AND TRIM(status) IN (%s,%s,%s,%s,%s,%s)",
                    (ten, 'Đã nhận việc', 'Đã quá hạn báo giá', 'Cần cập nhật lại',
                     'Đã quá 10 ngày', misc.LEAD_STATUS_ANNA_ASSIGNED,
                     misc.LEAD_STATUS_ANNA_ASSIGNED_LEGACY), default=(0,))[0] or 0
                moi = misc.sql_one(
                    "SELECT COUNT(*) FROM sale_lead l WHERE l.phu_trach = %s AND l.check_delete != '1' "
                    "AND TRIM(l.status) IN (%s,%s,%s,%s,%s,%s) "
                    "AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id)",
                    (ten, 'Đã nhận việc', 'Đã quá hạn báo giá', 'Cần cập nhật lại',
                     'Đã quá 10 ngày', misc.LEAD_STATUS_ANNA_ASSIGNED,
                     misc.LEAD_STATUS_ANNA_ASSIGNED_LEGACY), default=(0,))[0] or 0
                tong_cu += cu
                tong_moi += moi
                if cu or moi:
                    print(f'  {ten[:28]:<28} {cu:>8} {moi:>9}  {cu - moi:>8}')
            print(f'  {"-"*28} {"-"*8} {"-"*9}  {"-"*8}')
            print(f'  {"TỔNG":<28} {tong_cu:>8} {tong_moi:>9}  {tong_cu - tong_moi:>8}')
            print('\n  Ghi chú: sau khi bỏ B7, cột "luật mới" KHÔNG còn chặn ai nhận việc —')
            print('  nó chỉ là số lead tồn đọng chưa báo giá, dùng để ưu tiên chia việc.')
except Exception as e:
    dat(False, f'Kiểm tra CSDL — {type(e).__name__}: {e}', nghiem_trong=False)


# ─────────────────────────────────────────────────────────────────────────
print('\n' + '=' * 62)
if loi:
    print(f'❌ {len(loi)} lỗi phải sửa TRƯỚC khi build:')
    for x in loi:
        print(f'   · {x}')
else:
    print('✅ Qua hết các kiểm tra tự động.')
if canh_bao:
    print(f'\n⚠️  {len(canh_bao)} cảnh báo:')
    for x in canh_bao:
        print(f'   · {x}')

print('\n🔴 CHƯA XONG: script này không thay được việc mở app bấm thử.')
print('   Tối thiểu phải thử tay: đăng nhập · bấm "Nhận việc" ở cả màn hình')
print('   "Cơ hội mới" lẫn danh sách lead · mở một báo giá · mở một đơn hàng.')
sys.exit(1 if loi else 0)
