from openpyxl.drawing.image import Image
import os
import sys
import re
import unicodedata
import time
import mysql.connector
import requests
import datetime
import openpyxl
from PyQt6.QtWidgets import QFileDialog
import mysql.connector

db_config = {
    'host': 'db.fs.rsa.vn',
    'port': 3118,
    'user': 'firesmart',
    'password': '123@123a',
    'database': 'fs_mrb',
    'connection_timeout': 3  # ⏱ Giới hạn timeout 3 giây
}

def _connect():
    return mysql.connector.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        connection_timeout=db_config.get("connection_timeout", 5),

        # 🔥 BẮT BUỘC
        use_pure=True
    )

def sql_all(query, params=None):
    while True:
        try:
            db = _connect()
            cur = db.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            db.close()
            return rows
        except Exception as e:
            print("sql_all error:", e)
            time.sleep(0.5)


def sql_one(query, params=None):
    while True:
        try:
            db = _connect()
            cur = db.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            cur.close()
            db.close()
            return row
        except Exception as e:
            print("sql_one error:", e)
            time.sleep(0.5)

def sql_commit(query, params=None, max_retry=3):
    retry = 0
    while True:
        try:
            db = _connect()
            cur = db.cursor()
            cur.execute(query, params)
            db.commit()
            cur.close()
            db.close()
            return
        except Exception as e:
            msg = str(e)
            if "1062" in msg or "Duplicate entry" in msg:
                print("sql_commit integrity error:", e)
                raise

            retry += 1
            print(f"sql_commit error (retry {retry}/{max_retry}):", e)
            if retry >= max_retry:
                raise
            time.sleep(0.5)


def ensure_audit_schema():
    sql_commit(
        """
        CREATE TABLE IF NOT EXISTS sale_lead_audit_log (
            id BIGINT NOT NULL AUTO_INCREMENT,
            lead_id BIGINT NULL,
            log_line TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_lead_id (lead_id),
            KEY idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        None,
    )


def audit_log(actor, action, field, old_value, new_value, lead_id=None):
    try:
        ensure_audit_schema()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old_txt = "(trống)" if old_value is None or str(old_value).strip() == "" else str(old_value)
        new_txt = "(trống)" if new_value is None or str(new_value).strip() == "" else str(new_value)
        line = f"[{ts}] {actor} | {action} | {field}: {old_txt} -> {new_txt}"
        sql_commit("INSERT INTO sale_lead_audit_log (lead_id, log_line) VALUES (%s, %s)", (lead_id, line))
    except Exception as e:
        print(f"audit_log error: {e}")


LEAD_TITLE_PLACEHOLDER_ANNA = 'Anna chờ sales đặt tên lead này'
LEAD_STATUS_ANNA_ASSIGNED = 'Anna đã giao việc'
LEAD_READY_STATUS = {
    'Đã nhận việc',
    'Đã quá hạn báo giá',
    'Cần cập nhật lại',
    'Đã quá 10 ngày',
    'Đã báo giá',
    'Đã đặt hàng',
    'Đã thanh toán',
    'Đã giao hàng',
    'Đã trả lại toàn bộ',
    'Done - Thất bại',
}


def check_lead_ready_for_workflow(lead_id):
    row = sql_one("SELECT ten_co_hoi, status FROM sale_lead WHERE lead_id = %s", (lead_id,))
    if not row:
        return False, f"Không tìm thấy lead #{lead_id}"

    ten_co_hoi = (row[0] or '').strip()
    status = (row[1] or '').strip()

    if ten_co_hoi == LEAD_TITLE_PLACEHOLDER_ANNA:
        return False, "Lead chưa được đặt tên cơ hội. Vui lòng đổi tên trước khi thao tác tiếp."

    if status == LEAD_STATUS_ANNA_ASSIGNED:
        return False, "Lead đang ở trạng thái 'Anna đã giao việc'. Vui lòng chuyển sang 'Đã nhận việc' (hoặc trạng thái sau đó) để tiếp tục."

    if status not in LEAD_READY_STATUS:
        return False, "Lead chưa sẵn sàng xử lý. Vui lòng cập nhật trạng thái sang 'Đã nhận việc' (hoặc trạng thái sau đó)."

    return True, "OK"


def tao_bao_gia(lead_id, user):

    now = datetime.datetime.now()

    # Xóa báo giá cũ không có nội dung
    kq = sql_all("SELECT * FROM ds_bao_gia WHERE noi_dung IS NULL", None)
    for item in kq:
        item_date = datetime.datetime.strptime(item[2], '%d/%m/%y').date()
        if item_date < now.date():
            sql_commit("DELETE FROM ds_bao_gia WHERE so_bg = %s", (item[0],))

    # Tạo số báo giá mới
    kq = sql_one("SELECT MAX(so_bg) FROM ds_bao_gia")
    sobaogia = 1 if kq[0] is None else int(kq[0]) + 1

    lead_id = int(lead_id)

    ok, msg = check_lead_ready_for_workflow(lead_id)
    if not ok:
        raise ValueError(msg)

    d = now.strftime("%d/%m/%y")

    sql_commit(
        "INSERT INTO ds_bao_gia (so_bg, lead_id, ngaythang, sotien, user, tieu_de) VALUES (%s, %s, %s, %s, %s, %s)",
        (sobaogia, lead_id, d, 0, user, 'Cần đổi tên của báo giá này!')
    )
    audit_log(user, 'CREATE_QUOTE', 'so_bg', '-', sobaogia, lead_id)

    return 'Thông tin hợp lệ – báo giá đã được tạo', sobaogia


def send_to_telegram(message):

    apiToken = '6469906602:AAEuTZ3y0tOMug8qX8DKoRdOLZN1bycb-WA'
    chatID = '-928385747'
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message})
    except Exception as e:
        print(e)


def get_resource_path(relative_path):
    """
    Dùng được cả khi chạy Python thường và khi build PyInstaller (.exe)
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def insert_logo_by_company(sheet, cty):
    """
    Chèn logo vào sheet theo combo công ty
    """
    LOGO_MAP = {
        "BG PCCC.vn": "assets/logo_pccc.png",
        "BG Infutech": "assets/logo_infutech.png",
        "BG Bach Khoa": "assets/logo_bach_khoa.png",
    }

    logo_rel_path = LOGO_MAP.get(cty)

    if not logo_rel_path:
        print(f"⚠️ Không tìm thấy logo cho công ty: {cty}")
        return

    logo_path = get_resource_path(logo_rel_path)

    if not os.path.exists(logo_path):
        print(f"❌ File logo không tồn tại: {logo_path}")
        return

    img = Image(logo_path)

    # 🎯 Chỉnh kích thước chuẩn cho báo giá
    img.width = 180
    img.height = 70

    # 🎯 Vị trí đặt logo (bạn có thể đổi)
    sheet.add_image(img, "A1")


def save_excel(so_bg, user, phone, cty, thue=None):

    # Get lead_id
    kq = sql_one("SELECT lead_id, tieu_de FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))
    lead_id = str(kq[0])
    tieu_de = kq[1]
    # Step 1: Get address
    ttkh = sql_one("SELECT company, name, address, sdt, mst FROM sale_lead WHERE lead_id = %s", (lead_id,)) or ''

    # Step 2: Get quote data
    kq = sql_one("SELECT so_bg, ngaythang, sotien, noi_dung, ghi_chu, user, dien_thoai, sum8, sum10, sum0 FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))
    goods = [item.split('|') for item in kq[3].split('@')]

    # Step 3: Select template
    if thue == 'Thue':
        template_path = get_resource_path('bao_gia_thue.xlsx')
    else:
        if cty == 'BG PCCC.vn':
            template_path = get_resource_path('bao_gia_mau.xlsx')
        elif cty == 'BG Infutech':
            template_path = get_resource_path('bao_gia_mau_infutech.xlsx')
        else:
            template_path = get_resource_path('bao_gia_mau_bach_khoa.xlsx')

    if not os.path.exists(template_path):
        return f"Không tìm thấy file mẫu báo giá: {template_path}"

    workbook = openpyxl.load_workbook(template_path)

    sheet = workbook['Quotation']
    #insert_logo_by_company(sheet, cty)

    now_str = datetime.datetime.now().strftime('%d-%m-%Y')

    # Step 4: Fill general info
    sheet.cell(row=5, column=2).value = f'Kính gửi: {ttkh[0]}'
    sheet.cell(row=6, column=2).value = f'Anh/Chị: {ttkh[1]}'
    sheet.cell(row=7, column=2).value = f'Địa chỉ: {ttkh[2]}'
    sheet.cell(row=8, column=2).value = f'Điện thoại: {ttkh[3]}'
    sheet.cell(row=5, column=9).value = now_str
    sheet.cell(row=6, column=9).value = f'BG-{so_bg}-{lead_id}'
    sheet.cell(row=9, column=2).value = f"V/v: {tieu_de}"

    # Step 5: Fill goods list
    for i, item in enumerate(goods):
        try:
            stt = str(i + 1)
            tax_marker = item[6] if len(item) > 6 else '0'
            prefix = {'0': '', '8': '.', '10': '..'}.get(tax_marker, '...')
            item.insert(0, f'{stt}{prefix}')
            total = int(item[5]) * int(item[6].replace(',', ''))
            item.append(str(total))

            for col in range(2, 9):
                cell = sheet.cell(row=12 + i, column=col)
                cell.value = int(item[col - 2]) if col == 8 else item[col - 2]
                if col == 8:
                    cell.number_format = "#,##0"
        except Exception as e:
            print("Lỗi khi điền dữ liệu hàng hoá:", e)

    # Step 6: Delete extra rows
    sheet.delete_rows(13 + len(goods), 80 - len(goods))

    # Step 7: Tính thuế, tổng tiền
    sheet.cell(row=13 + len(goods), column=9).value = f'=SUM(I12:I{11 + len(goods)})'

    # LUÔN TÍNH VAT – an toàn kiểu dữ liệu
    sum8 = float(kq[7] or 0)
    sum10 = float(kq[8] or 0)

    sheet.cell(row=14 + len(goods), column=9).value = round(sum8 * 0.08)
    sheet.cell(row=15 + len(goods), column=9).value = round(sum10 * 0.1)

    if thue == 'Thue':
        sheet.cell(row=15 + len(goods), column=9).value = sum(int(item[5]) for item in goods) * 100000
    sheet.cell(row=16 + len(goods), column=9).value = f'=SUM(I{13 + len(goods)}:I{15 + len(goods)})'

    # Step 8: Tên người làm, sĐT
    sheet.cell(row=22 + len(goods), column=8).value = user
    sheet.cell(row=23 + len(goods), column=8).value = phone

    # Step 9: Save file
    # Step 9: Save file
    #root = Tk()
    #root.withdraw()


    def clean_filename(name):

        # Chuẩn hóa unicode
        name = unicodedata.normalize('NFKD', name)

        # Loại bỏ ký tự không phải ASCII in được
        name = ''.join(c for c in name if c.isprintable())

        # Thay mọi khoảng trắng đặc biệt bằng space thường
        name = re.sub(r'\s+', ' ', name)

        # Loại bỏ ký tự Windows cấm
        name = re.sub(r'[\\/*?:"<>|]', "", name)

        # Cắt khoảng trắng đầu/cuối
        name = name.strip()

        # Giới hạn độ dài
        return name[:120]

    raw_name = f"BG {so_bg} - {ttkh[1]} - {tieu_de}"
    safe_name = clean_filename(raw_name)

    default_file_name = f"{safe_name}.xlsx"

    # Ask the user to select a location to save the modified file
    #file_save_path = filedialog.asksaveasfilename(
     #   initialfile=default_file_name,
      #  defaultextension=".xlsx",
       # filetypes=[("Excel Files", "*.xlsx")]
    #)

    file_save_path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Excel File",
        default_file_name,
        "Excel Files (*.xlsx)"
    )

    if not file_save_path:
        return 'Chưa SAVE file excel.'

    try:
        workbook.save(file_save_path)
        tenfile = file_save_path.split('/')[-1]
        return "Đã SAVE file:   " + tenfile
    except Exception as e:
        print(e)
        return 'Chưa save file, kiểm tra xem có file nào trùng tên đang mở không!'

    # Check if the user canceled the save dialog
    if not file_save_path:
        tex = 'Chưa SAVE file excel.'
    else:
        try:
            # Save the modified workbook to the selected location
            workbook.save(file_save_path)

            # Find the last occurrence of '/'
            last_slash = file_save_path.rfind('/')

            # Extract substring from last slash to the end
            if last_slash != -1:  # Check if '/' is found
                tenfile = file_save_path[last_slash + 1:]  # +1 to exclude the slash itself
            else:
                tenfile = file_save_path  # If '/' is not found, return the original string

            tex = "Đã SAVE file:   " + tenfile

            check = 1
        except Exception as e:
            print(e)
            check = 0
            tex = 'Chưa save file, kiểm tra xem có file nào trùng tên đang mở không!'
    # Close the tkinter root window
    root.destroy()
    return tex


def header_label(user):
    db = _connect()
    cur = db.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM sale_lead
        WHERE YEAR(time_create) = YEAR(CURDATE())
        AND MONTH(time_create) = MONTH(CURDATE())
        AND nguoi_tao_lead = %s
    """, (user,))
    result = cur.fetchone()[0]
    cur.close()
    db.close()
    return f"Tháng này bạn đã tạo ra {result} cơ hội."


def header_label_doanh_so(user):
    # Ghi lịch sử tạo lead của user
    result = sql_all("SELECT * FROM ds_don_hang WHERE nguoi_tao = %s", (user,))
    txt = 'Đã chốt ' + str(len(result)) + ' đơn hàng, tổng giá trị ' + "{:,}".format(
        sum(item[2] for item in result)) + ' VNĐ.'

    return txt


def save_price_list(price_list):
    saved = False
    while not saved:
        try:
            for e in price_list:
                code = ("UPDATE gia_tong_hop SET ten_san_pham = %s, nhan_hieu = %s, xuat_xu = %s, don_vi = %s, "
                        "gia_cap_1 = %s, gia_cap_2 = %s, gia_ban_le = %s, vat = %s, gia_dau_vao = %s WHERE model = %s")
                val = (e[0], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[1])
                sql_commit(code, val)
                time.sleep(0.05)
                print('Đã lưu đến sản phẩm: ', e[0])
            saved = True
        except Exception as e1:
            saved = False
            time.sleep(0.5)
            print(e1)
