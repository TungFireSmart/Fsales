import sys
import re
import json

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem
from PyQt6.QtCore import Qt

from UI.gui import Ui_MainWindow
from UI.sua_bang_gia import Ui_Bang_gia
import hinhanh_rc  # đăng ký Qt resource (logo)
from lead_handle import LeadHandle
import crm
import misc
from baocao import Report
from stock_handle import StockHandle
from quotation import Quotato
from login_handle import check_saved_login, handle_login, handle_logout
from price_list_manager import PriceListManager

# Phần AI
from AI.ai_chat_window import AIChatWindow
from greeting_service import generate_greeting



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self)
        self.setWindowTitle(QApplication.translate("MainWindow", "Fsale v2.1.1"))
        self.user = ''
        self.user_phone = ''
        self.logged_in = False

        self.checkLogin = 0
        self._login_lock = False
        check_saved_login(self)

        self.uic.text_user.textChanged.connect(self.login)
        self.uic.text_password.textChanged.connect(self.login)

        self.uic.but_logout.clicked.connect(lambda: handle_logout(self))
        self.uic.but_chat.clicked.connect(self.open_ai_chat)

    def open_ai_chat(self):
        self.ai_chat = AIChatWindow(self, self.user_power)
        self.ai_chat.show()

    def login(self):
        handle_login(self)

    def logout(self):
        handle_logout(self)
        self.uic.text_password.show()
        self.uic.text_user.show()
        self.uic.text_user.textChanged.connect(self.login)
        self.uic.text_password.textChanged.connect(self.login)
        self.uic.but_logout.setEnabled(False)

    def post_login_setup(self):
        self.uic.text_user.hide()
        self.uic.text_password.hide()
        self.uic.but_logout.setEnabled(True)
        self.uic.but_co_hoi_moi.setEnabled(True)
        self.uic.but_tao_co_hoi.setEnabled(True)

        self.uic.label_username.setText(self.user)

        result = misc.sql_one("SELECT * from user where phone_number = %s", (self.user_phone,))
        self.user_power = int(result[3])

        # Phân quyền CRM: chỉ cho phép power >= 40
        self.uic.but_crm.setEnabled(self.user_power >= 40)

        if self.user_power > 40:
            self.uic.but_sua_bang_gia.setEnabled(True)

        self.uic.label_so_co_hoi.setText(misc.header_label(self.user))
        self.uic.label_so_co_hoi.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.uic.label_doanh_so.setText(misc.header_label_doanh_so(self.user))
        self.uic.label_doanh_so.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.show_lead(self.user)
        self.set_combo_user_status(self.user)

        self.uic.but_logout.clicked.connect(self.logout)
        self.uic.but_mydesk.clicked.connect(lambda: self.show_lead(self.user))
        self.uic.but_co_hoi_moi.clicked.connect(lambda: self.show_co_hoi_moi())

        # Quản lý bảng giá
        self.win_banggia = QMainWindow()
        self.uic6 = Ui_Bang_gia()
        self.uic6.setupUi(self.win_banggia)
        self.price_manager = PriceListManager(self.uic6, self.user)
        self.uic.but_sua_bang_gia.clicked.connect(self.sua_bang_gia)

        # Quản lý khách hàng (chỉ user power >= 40)
        try:
            self.uic.but_crm.clicked.disconnect()
        except Exception:
            pass
        if self.user_power >= 40:
            self.uic.but_crm.clicked.connect(lambda: crm.Crm.company_view(self))
            self.uic.but_crm.setToolTip("Mở CRM")
        else:
            self.uic.but_crm.setToolTip("Bạn không có quyền truy cập CRM (yêu cầu power >= 40)")

        # Quản lý kho
        self.uic.but_quan_ly_kho.clicked.connect(lambda: StockHandle.quan_ly_kho(self))
        # self.uic.but_tao_don_hang.clicked.connect(self.show_quotato)

        # Quản lý báo cáo
        self.report_window = Report(self)
        self.uic.but_baocao.clicked.connect(lambda: self.report_window.khoitao(self.user))

        # LeadHandle instance
        self.lead_handler = LeadHandle(self)
        self.lead_handler.user = self.user
        self.lead_handler.user_phone = self.user_phone
        self.uic.but_tao_co_hoi.clicked.connect(self.lead_handler.create_new_lead)

        # Tìm kiếm trên gui main
        self.uic.tex_search.textChanged.connect(self.universal_search)
        self.userName = 'All'
        self.status = 'All'
        self.uic.label_noti.setStyleSheet("color: green")
        self.uic.label_noti.setText(generate_greeting())

        self.uic.text_user.textChanged.disconnect(self.login)
        self.uic.text_password.textChanged.disconnect(self.login)

    def sua_bang_gia(self):
        self.win_banggia.show()

    def set_combo_user_status(self, user):
        try:
            self.uic.combo_user.clear()
            q = 'SELECT power FROM user WHERE full_name = %s'
            result = misc.sql_one(q, (user,))
            if result:
                if int(result[0]) < 40:
                    self.uic.combo_user.addItem(user)
                else:
                    self.uic.combo_user.addItem('All')
                    q = 'SELECT full_name FROM user WHERE power != 0'
                    result1 = misc.sql_all(q, params=None)
                    for item in result1:
                        self.uic.combo_user.addItem(item[0])
                self.uic.combo_user.activated.connect(self.on_combo_box_activated)

        except Exception as e:
            print(e)

    def on_combo_box_activated(self, index):
        self.uic.label_noti.clear()
        self.userName = self.uic.combo_user.itemText(index)

        if len(self.uic.tex_search.toPlainText().strip()) != 10:
            self.show_lead_with_status(self.userName, self.status)
        else:
            self.search_sdt()

    def show_lead_with_status(self, user, status):
        try:
            self.uic.tableWidget.clear()
            self.uic.tableWidget.setColumnCount(4)
            self.uic.tableWidget.setHorizontalHeaderLabels(['Lead', 'Yêu cầu của khách hàng', 'Trạng thái', ' '])
            self.uic.tableWidget.setColumnWidth(0, 60)
            self.uic.tableWidget.setColumnWidth(1, 400)
            self.uic.tableWidget.setColumnWidth(2, 140)
            self.uic.tableWidget.setColumnWidth(3, 100)
            self.uic.tableWidget.verticalHeader().setVisible(False)

            # 🔍 Lấy danh sách theo user và status
            if user == 'All':
                if status == 'All':
                    query = "SELECT * FROM sale_lead WHERE check_delete != '1'"
                    result = misc.sql_all(query)
                else:
                    query = "SELECT * FROM sale_lead WHERE status = %s AND check_delete != '1'"
                    result = misc.sql_all(query, (status,))
            else:
                if status == 'All':
                    query = "SELECT * FROM sale_lead WHERE phu_trach = %s AND check_delete != '1'"
                    result = misc.sql_all(query, (user,))
                else:
                    query = "SELECT * FROM sale_lead WHERE phu_trach = %s AND status = %s AND check_delete != '1'"
                    result = misc.sql_all(query, (user, status))

            result = sorted((result or []), key=lambda x: x[0], reverse=True)
            tasks = self._get_return_request_tasks()

            total_rows = len(tasks) + len(result)
            if total_rows == 0:
                self.uic.label_noti.setText('Không tìm thấy cơ hội nào phù hợp yêu cầu tìm kiếm')
                self.uic.tableWidget.setRowCount(0)
                return

            self.uic.tableWidget.setRowCount(total_rows)
            row_idx = 0

            # Ưu tiên hiển thị item chờ duyệt/chờ thực thi lên đầu
            for t in tasks:
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(t['lead_id'])))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(t['text']))
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(t['status']))

                btn = QPushButton('Duyệt/Từ chối' if t['action'] == 'DUYET_TU_CHOI' else 'Thực thi')
                btn.clicked.connect(lambda _, lid=t['lead_id'], sb=t['so_bg']: self._handle_return_task(lid, sb))
                self.uic.tableWidget.setCellWidget(row_idx, 3, btn)

                self.uic.tableWidget.resizeRowToContents(row_idx)
                if self.uic.tableWidget.rowHeight(row_idx) > 65:
                    self.uic.tableWidget.setRowHeight(row_idx, 65)
                row_idx += 1

            for item in result:
                lead_id, yeu_cau, trang_thai, phu_trach = item[0], item[9], item[10], item[11]
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(lead_id)))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(yeu_cau))
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(f"{trang_thai}\n{phu_trach}"))

                if trang_thai.strip() == '...':
                    but = QPushButton('Nhận việc')
                    but.clicked.connect(lambda _, lid=lead_id: self.nhan_viec_by_id(lid))
                else:
                    but = QPushButton('Cập nhật')
                    but.clicked.connect(lambda _, lid=lead_id: LeadHandle.update_job(self, str(lid)))

                self.uic.tableWidget.setCellWidget(row_idx, 3, but)
                self.uic.tableWidget.resizeRowToContents(row_idx)
                if self.uic.tableWidget.rowHeight(row_idx) > 65:
                    self.uic.tableWidget.setRowHeight(row_idx, 65)
                row_idx += 1

            self.uic.tableWidget.repaint()

        except Exception as e:
            print(f"Lỗi show_lead_with_status: {e}")

    def search_sdt(self):
        self.uic.label_noti.clear()

        raw_text = self.uic.tex_search.toPlainText()
        search_text = re.sub(r"\D", "", raw_text)

        if not search_text:
            return

        # Nếu có Enter thì dọn text về 1 dòng để tránh lặp ký tự xuống dòng
        if '\n' in raw_text:
            self.uic.tex_search.setText(search_text)

        # ✅ Kiểm tra định dạng số điện thoại (phải là 10 chữ số, bắt đầu bằng 0)
        if not re.match(r"^0\d{9}$", search_text):
            self.uic.label_noti.setStyleSheet("color: red")
            self.uic.label_noti.setText("⚠️ Số điện thoại phải có đúng 10 chữ số và bắt đầu bằng số 0.")
            return

        # ✅ Truy vấn dữ liệu tùy theo trạng thái
        if self.status == "All":
            query = "SELECT * FROM sale_lead WHERE check_delete != '1'"
            results = misc.sql_all(query)
        else:
            query = "SELECT * FROM sale_lead WHERE status = %s AND check_delete != '1'"
            results = misc.sql_all(query, (self.status,))

        # ✅ Tìm kiếm trong tất cả các trường
        matched_results = [item for item in results if any(search_text in str(field) for field in item)]

        if matched_results:
            self.show_search_result(matched_results)
        else:
            self.uic.label_noti.setStyleSheet("color: red")
            self.uic.label_noti.setText("❌ Không tìm thấy cơ hội nào có số điện thoại này.")

    def show_search_result(self, results):
        result = sorted(results, key=lambda x: x[0], reverse=True)
        self.uic.tableWidget.clearContents()
        self.uic.tableWidget.setColumnCount(4)
        self.uic.tableWidget.setRowCount(len(result))
        self.uic.tableWidget.setHorizontalHeaderLabels(['Lead', 'Yêu cầu của khách hàng', 'Trạng thái', 'Phụ trách'])
        self.uic.tableWidget.setColumnWidth(0, 40)
        self.uic.tableWidget.setColumnWidth(1, 400)
        self.uic.tableWidget.setColumnWidth(2, 100)
        self.uic.tableWidget.setColumnWidth(3, 90)

        for row in range(len(result)):
            self.uic.tableWidget.setItem(row, 0, QTableWidgetItem(str(result[row][0])))
            self.uic.tableWidget.setItem(row, 1, QTableWidgetItem(result[row][9]))
            txt = str(result[row][10]) + '\n' + str(result[row][11])
            self.uic.tableWidget.setItem(row, 2, QTableWidgetItem(txt))
            self.uic.tableWidget.resizeRowToContents(row)
            # Get the current height of the row
            current_row_height = self.uic.tableWidget.rowHeight(row)
            # Check if current row height exceeds maximum row height
            if current_row_height > 65:
                self.uic.tableWidget.setRowHeight(row, 65)

        for row in range(0, len(result)):
            self.uic.tableWidget.takeItem(row, 3)
            if self.user == result[row][11] or int(self.user_power) > 40:
                but1 = QPushButton('Nhận việc')
                but1.clicked.connect(lambda: self.nhan_viec(result))
                but2 = QPushButton('Cập nhật')
                but2.clicked.connect(lambda: LeadHandle.update_job(self, self.uic.tableWidget.item(
                    self.uic.tableWidget.currentRow(), 0).text()))

                if result[row][10] == '...':
                    self.uic.tableWidget.setCellWidget(row, 3, but1)
                else:
                    self.uic.tableWidget.setCellWidget(row, 3, but2)

    def _not_found(self, keyword="tìm kiếm"):
        self.uic.label_noti.setStyleSheet("color: red")
        self.uic.label_noti.setText(f"❌ Không tìm thấy kết quả theo {keyword.lower()}.")

    def universal_search(self):
        self.uic.label_noti.clear()
        raw_text = self.uic.tex_search.toPlainText()
        search_text = raw_text.strip()

        if not search_text:
            return

        # Kiểm tra SĐT: cho phép nhập kèm dấu cách/chấm/gạch
        phone_digits = re.sub(r"\D", "", search_text)
        if re.match(r"^0\d{9}$", phone_digits):
            if '\n' in raw_text:
                self.uic.tex_search.setText(phone_digits)
            query = "SELECT * FROM sale_lead WHERE check_delete != '1'"
            params = ()
            if self.status != "All":
                query += " AND status = %s"
                params = (self.status,)
            results = misc.sql_all(query, params)
            matched = [r for r in results if phone_digits in str(r)]
            return self.show_search_result(matched) if matched else self._not_found("SĐT")

        # Kiểm tra số báo giá (toàn số, <= 6 chữ số)
        if search_text.isdigit() and len(search_text) <= 6:
            result = misc.sql_one("SELECT lead_id FROM ds_bao_gia WHERE so_bg = %s", (search_text,))
            if result:
                lead_id = result[0]
                leads = misc.sql_all("SELECT * FROM sale_lead WHERE lead_id = %s AND check_delete != '1'", (lead_id,))
                return self.show_search_result(leads) if leads else self._not_found("Số BG")
            else:
                return self._not_found("Số BG")

        # Mặc định tìm theo tên
        results = misc.sql_all("SELECT * FROM sale_lead WHERE name LIKE %s", (f"%{search_text}%",))
        return self.show_search_result(results) if results else self._not_found("Tên KH")

    def _parse_return_request_from_log(self, lich_su_gd):
        if not lich_su_gd:
            return None
        markers = [
            ("RETURN_REQ_EXECUTED|", "EXECUTED"),
            ("RETURN_REQ_REJECTED|", "REJECTED"),
            ("RETURN_REQ_APPROVED|", "APPROVED"),
            ("RETURN_REQ_JSON|", "PENDING_APPROVAL"),
        ]
        lines = str(lich_su_gd).split('@@')
        for line in reversed(lines):
            for mk, state in markers:
                if mk in line:
                    try:
                        payload = json.loads(line.split(mk, 1)[1])
                        payload["state"] = payload.get("state", state)
                        return payload
                    except Exception:
                        return None
        return None

    def _get_return_request_tasks(self):
        out = []
        rows = misc.sql_all(
            "SELECT d.so_bg, d.lead_id, d.lich_su_gd, s.name, s.company "
            "FROM ds_don_hang d LEFT JOIN sale_lead s ON s.lead_id = d.lead_id "
            "WHERE d.lich_su_gd IS NOT NULL AND d.lich_su_gd != ''",
            None,
        ) or []

        for r in rows:
            so_bg, lead_id, lich_su_gd, name, company = r[0], r[1], r[2], r[3], r[4]
            payload = self._parse_return_request_from_log(lich_su_gd)
            if not payload:
                continue

            state = str(payload.get("state", "")).upper()
            power = int(getattr(self, 'user_power', 0) or 0)

            # Manager: chỉ thấy việc chờ duyệt
            if power > 50 and state == "PENDING_APPROVAL":
                out.append({
                    "lead_id": lead_id,
                    "so_bg": so_bg,
                    "text": f"[TRẢ HÀNG - CHỜ DUYỆT] Đơn #{so_bg} | {name or ''} | {company or ''}",
                    "status": "Chờ quản lý duyệt",
                    "action": "DUYET_TU_CHOI",
                })

            # Kế toán: thấy việc chờ thực thi
            if 40 < power <= 50 and state == "APPROVED":
                out.append({
                    "lead_id": lead_id,
                    "so_bg": so_bg,
                    "text": f"[TRẢ HÀNG - CHỜ KẾ TOÁN] Đơn #{so_bg} | {name or ''} | {company or ''}",
                    "status": "Đã duyệt, chờ kế toán",
                    "action": "THUC_THI",
                })

            # Kế toán: nếu đã EXECUTED nhưng có thể dở bước hậu xử lý kho -> cho phép tiếp tục
            if 40 < power <= 50 and state == "EXECUTED":
                px = misc.sql_one("SELECT id FROM xuat_kho WHERE so_bg = %s ORDER BY id DESC LIMIT 1", (so_bg,))
                has_nhap_tra = False
                if px:
                    k = misc.sql_one("SELECT id FROM nhap_kho WHERE ghi_chu LIKE %s ORDER BY id DESC LIMIT 1", (f"%TRA_LAI_PX:{px[0]}%",))
                    has_nhap_tra = bool(k)

                if not has_nhap_tra:
                    out.append({
                        "lead_id": lead_id,
                        "so_bg": so_bg,
                        "text": f"[TRẢ HÀNG - CẦN TIẾP TỤC] Đơn #{so_bg} | {name or ''} | {company or ''}",
                        "status": "Đã thực thi tài chính, chưa nhập kho trả lại",
                        "action": "THUC_THI",
                    })

        return out

    def _handle_return_task(self, lead_id, so_bg):
        try:
            from order_handle import OrderHandle
            self.win_order = self
            OrderHandle.tra_lai_hang(self, int(lead_id), int(so_bg))
        except Exception as e:
            print(f"Lỗi xử lý phiếu trả hàng: {e}")
            self.uic.label_noti.setStyleSheet("color: red")
            self.uic.label_noti.setText(f"Lỗi xử lý phiếu trả hàng: {e}")

    def show_lead(self, user):
        try:
            self.thong_ke()
            self.uic.tableWidget.clear()
            self.uic.tableWidget.verticalHeader().setVisible(False)

            kq = misc.sql_one('SELECT power FROM user WHERE full_name = %s', (self.user,))
            if kq:
                if int(kq[0]) < 40:
                    code = "SELECT * from sale_lead WHERE phu_trach = %s AND check_delete != '1' AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
                    result = misc.sql_all(code, (self.user,))
                else:
                    code = "SELECT * FROM sale_lead WHERE status != ' ...' AND check_delete != '1' AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
                    result = misc.sql_all(code, None)
            else:
                return

            result = result or []
            result = sorted(result, key=lambda x: x[0], reverse=True)

            self.uic.tableWidget.setColumnCount(4)
            self.uic.tableWidget.setHorizontalHeaderLabels(['Lead', 'Yêu cầu của khách hàng', 'Trạng thái', 'Phụ trách'])
            self.uic.tableWidget.setColumnWidth(0, 60)
            self.uic.tableWidget.setColumnWidth(1, 400)
            self.uic.tableWidget.setColumnWidth(2, 140)
            self.uic.tableWidget.setColumnWidth(3, 100)

            tasks = self._get_return_request_tasks()
            total_rows = len(result) + len(tasks)
            self.uic.tableWidget.setRowCount(total_rows)

            row_idx = 0
            # Ưu tiên hiển thị item chờ duyệt/chờ thực thi lên đầu
            for t in tasks:
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(t['lead_id'])))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(t['text']))
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(t['status']))

                if t['action'] == 'DUYET_TU_CHOI':
                    btn = QPushButton('Duyệt/Từ chối')
                else:
                    btn = QPushButton('Thực thi')
                btn.clicked.connect(lambda _, lid=t['lead_id'], sb=t['so_bg']: self._handle_return_task(lid, sb))
                self.uic.tableWidget.setCellWidget(row_idx, 3, btn)

                self.uic.tableWidget.resizeRowToContents(row_idx)
                if self.uic.tableWidget.rowHeight(row_idx) > 65:
                    self.uic.tableWidget.setRowHeight(row_idx, 65)
                row_idx += 1

            for item in result:
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(item[0])))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(item[9]))
                txt = item[10] + '\n' + item[11]
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(txt))

                but2 = QPushButton('Cập nhật')
                but2.clicked.connect(lambda _, lid=item[0]: LeadHandle.update_job(self, str(lid)))
                self.uic.tableWidget.setCellWidget(row_idx, 3, but2)

                self.uic.tableWidget.resizeRowToContents(row_idx)
                if self.uic.tableWidget.rowHeight(row_idx) > 65:
                    self.uic.tableWidget.setRowHeight(row_idx, 65)
                row_idx += 1

            if total_rows == 0:
                self.uic.label_noti.setText('Cơ hội bán hàng!')

            self.uic.tableWidget.repaint()

        except Exception as e:
            print(e)
            print("❌ Lỗi khi show lead!!!")
            return

    def show_co_hoi_moi(self):
        try:
            self.thong_ke()
            self.uic.tableWidget.clear()
            self.uic.tableWidget.verticalHeader().setVisible(False)

            code = "SELECT * FROM sale_lead WHERE status = ' ...' AND check_delete != '1' AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
            result = misc.sql_all(code, None)

            if result:
                # Sort based on sublist[0] in descending order
                result = sorted(result, key=lambda x: x[0], reverse=True)

                self.uic.tableWidget.setColumnCount(4)
                self.uic.tableWidget.setRowCount(len(result))
                self.uic.tableWidget.setHorizontalHeaderLabels(['Lead', 'Yêu cầu của khách hàng', 'Trạng thái', 'Phụ trách'])
                self.uic.tableWidget.setColumnWidth(0, 40)
                self.uic.tableWidget.setColumnWidth(1, 400)
                self.uic.tableWidget.setColumnWidth(2, 100)
                self.uic.tableWidget.setColumnWidth(3, 90)

                for row in range(len(result)):
                    self.uic.tableWidget.setItem(row, 0, QTableWidgetItem(str(result[row][0])))

                    self.uic.tableWidget.setItem(row, 1, QTableWidgetItem(result[row][9]))
                    txt = result[row][10] + '\n' + result[row][11]
                    self.uic.tableWidget.setItem(row, 2, QTableWidgetItem(txt))

                    self.uic.tableWidget.resizeRowToContents(row)
                    # Get the current height of the row
                    current_row_height = self.uic.tableWidget.rowHeight(row)

                    # Check if current row height exceeds maximum row height
                    if current_row_height > 65:
                        self.uic.tableWidget.setRowHeight(row, 65)

                for row in range(0, len(result)):
                    but1 = QPushButton('Nhận việc')
                    but1.clicked.connect(lambda: self.nhan_viec(result))

                    self.uic.tableWidget.setCellWidget(row, 3, but1)
                self.uic.tableWidget.repaint()
            else:
                self.uic.label_noti.setText('Cơ hội bán hàng!')

        except Exception as e:
            print(e)
            print("❌ Lỗi khi show cơ hội mới!!!")
            return

    def nhan_viec(self, result):
        lead_id = result[self.uic.tableWidget.currentRow()][0]

        code = "SELECT check_busy FROM user WHERE full_name = %s"
        kq = misc.sql_one(code, (self.user,))

        if kq[0] == 0:
            misc.sql_commit("UPDATE user SET check_busy = 1 WHERE full_name = %s", (self.user,))
            misc.sql_commit("UPDATE sale_lead SET phu_trach = %s, status = 'Đang xử lý', time_nhan_viec = NOW() "
                          "WHERE lead_id = %s", (self.user, lead_id,))

            self.show_lead(self.user)

            kq = misc.sql_one("SELECT ten_co_hoi FROM sale_lead WHERE lead_id = %s", (lead_id,))[0]

            misc.send_to_telegram(self.user + ' nhận xử lý cơ hội: ' + kq + ' số ' + str(lead_id) + '.')

        else:
            self.uic.label_noti.setText('❌ Không được nhận cơ hội mới do vẫn còn cơ hội cũ chưa xử lý')

    def thong_ke(self):
        try:
            code = "SELECT * FROM ds_don_hang WHERE nguoi_tao = %s AND da_hoan_thanh = 'T'"
            result = misc.sql_all(code, (self.user,))

            txt = 'Đã chốt ' + str(len(result)) + ' đơn hàng, tổng giá trị ' + "{:,}".format(sum(item[2] for item in result)) + ' VNĐ.'
            self.uic.label_doanh_so.setText(txt)

        except Exception as e:
            print(e)
            self.uic.label_noti.setText('Lỗi server! Try again!')

    def show_quotato(self):
        self.win_quotato = Quotato()
        self.win_quotato.user = self.user
        self.win_quotato.user_phone = self.user_phone
        self.win_quotato.tao_don_hang_khong_co_bao_gia()


if __name__ == "__main__":
    from PyQt6.QtCore import QTimer

    app = QApplication(sys.argv)

    win = MainWindow()
    QTimer.singleShot(0, win.show)

    print("🌀 Entering event loop")
    sys.exit(app.exec())

