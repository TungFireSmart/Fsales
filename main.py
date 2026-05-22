import sys
import re
import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

from UI.gui import Ui_MainWindow
from UI.sua_bang_gia import Ui_Bang_gia
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
from ui_theme import apply_ui_v2
from auto_update import AutoUpdater


LEAD_STATUS_ENUM = [
    'Mới',
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
]

def load_global_stylesheet(app: QApplication):
    """Load global QSS for a cleaner, more consistent UI."""
    try:
        # Guard: avoid Qt warning "QFont::setPointSize <= 0 (-1)"
        f = app.font()
        if f.pointSize() <= 0:
            f.setPointSize(10)
            app.setFont(f)

        qss_path = Path(__file__).resolve().parent / "styles" / "app.qss"
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
            return True
    except Exception as e:
        print(f"Không thể nạp app.qss: {e}")
    return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self)
        self.app_version = '3.0.20'
        self.setWindowTitle(QApplication.translate("MainWindow", f"Fsale v{self.app_version}"))
        apply_ui_v2(self)
        self._set_version_label()
        self.user = ''
        self.user_phone = ''
        self.logged_in = False

        self.checkLogin = 0
        self._login_lock = False
        check_saved_login(self)

        # Nút cập nhật thủ công (hiện sau đăng nhập)
        self.but_check_update = QPushButton('Kiểm tra cập nhật', self.uic.centralwidget)
        self.but_check_update.setGeometry(800, 510, 145, 31)
        self.but_check_update.setVisible(False)
        self.but_force_update = QPushButton('Cập nhật ngay', self.uic.centralwidget)
        self.but_force_update.setGeometry(800, 545, 145, 31)
        self.but_force_update.setVisible(False)
        self.but_check_update.clicked.connect(self.check_update_manual)
        self.but_force_update.clicked.connect(self.force_update_now)

        self.uic.text_user.textChanged.connect(self.login)
        self.uic.text_password.textChanged.connect(self.login)

        self.uic.but_logout.clicked.connect(lambda: handle_logout(self))
        self.uic.but_chat.clicked.connect(self.open_ai_chat)

        # Auto-update check shortly after startup (non-blocking UX)
        QTimer.singleShot(1500, self.check_auto_update)

        # Chống chạy normalize status quá dày (gây chậm lúc mở app)
        self._last_lead_status_refresh_ms = 0

        # Cache tác vụ trả hàng để tránh quét log đơn hàng liên tục
        self._return_tasks_cache = []
        self._return_tasks_cache_ms = 0

    def _set_version_label(self):
        try:
            if hasattr(self.uic, 'label_version'):
                self.uic.label_version.setText(f"v{self.app_version}")
        except Exception:
            pass

    def _lead_status_color(self, status_text: str):
        status = (status_text or '').strip().split('\n')[0]
        color_map = {
            'Mới': ('#64748B', '#F1F5F9'),
            'Đã nhận việc': ('#2563EB', '#DBEAFE'),
            'Đã quá hạn báo giá': ('#F59E0B', '#FEF3C7'),
            'Cần cập nhật lại': ('#EA580C', '#FFEDD5'),
            'Đã quá 10 ngày': ('#DC2626', '#FEE2E2'),
            'Đã báo giá': ('#0EA5E9', '#E0F2FE'),
            'Đã đặt hàng': ('#16A34A', '#DCFCE7'),
            'Đã thanh toán': ('#15803D', '#DCFCE7'),
            'Đã giao hàng': ('#059669', '#D1FAE5'),
            'Đã trả lại toàn bộ': ('#7C3AED', '#EDE9FE'),
            'Done - Thất bại': ('#991B1B', '#FEE2E2'),
        }
        return color_map.get(status, ('#374151', '#F3F4F6'))

    def _apply_status_style_item(self, item: QTableWidgetItem):
        try:
            fg, bg = self._lead_status_color(item.text())
            item.setForeground(QBrush(QColor(fg)))
            item.setBackground(QBrush(QColor(bg)))
        except Exception:
            pass

    def open_ai_chat(self):
        self.ai_chat = AIChatWindow(self, self.user_power)
        self.ai_chat.show()

    def _run_update(self, info: dict):
        app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
        updater = AutoUpdater(str(app_dir), self.app_version)
        self.setEnabled(False)
        QApplication.processEvents()
        try:
            installer = updater.download_installer(info['installer_url'])
            updater.launch_installer(installer)
            QApplication.quit()
        except Exception as e:
            self.setEnabled(True)
            QMessageBox.warning(self, 'Cập nhật FSales', f'Không thể chạy bộ cài cập nhật: {e}')

    def check_update_manual(self):
        try:
            app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
            updater = AutoUpdater(str(app_dir), self.app_version)
            info = updater.check()
            if not info:
                QMessageBox.information(self, 'Cập nhật FSales', f'Bạn đang ở phiên bản mới nhất ({self.app_version}).')
                return
            msg = f"Đã có phiên bản mới {info['version']} (hiện tại {self.app_version}).\n\nBạn có muốn cập nhật ngay không?"
            answer = QMessageBox.question(self, 'Cập nhật FSales', msg)
            if answer == QMessageBox.StandardButton.Yes:
                self._run_update(info)
        except Exception as e:
            QMessageBox.warning(self, 'Cập nhật FSales', f'Không thể kiểm tra cập nhật: {e}')

    def force_update_now(self):
        try:
            app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
            updater = AutoUpdater(str(app_dir), self.app_version)
            info = updater.get_manifest_info()
            if not info:
                QMessageBox.warning(self, 'Cập nhật FSales', 'Không tải được manifest cập nhật.')
                return
            msg = f"Cưỡng bức cập nhật theo manifest hiện tại ({info['version']}).\n\nTiếp tục?"
            answer = QMessageBox.question(self, 'Cập nhật FSales', msg)
            if answer == QMessageBox.StandardButton.Yes:
                self._run_update(info)
        except Exception as e:
            QMessageBox.warning(self, 'Cập nhật FSales', f'Cập nhật cưỡng bức thất bại: {e}')

    def check_auto_update(self):
        try:
            app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
            updater = AutoUpdater(str(app_dir), self.app_version)
            info = updater.check()
            if not info:
                return

            msg = f"Đã có phiên bản mới {info['version']} (hiện tại {self.app_version}).\n\nBạn có muốn cập nhật ngay không?"

            answer = QMessageBox.question(self, 'Cập nhật FSales', msg)
            if answer != QMessageBox.StandardButton.Yes:
                return

            self._run_update(info)
        except Exception as e:
            # silent-safe: avoid interrupting sales workflow
            print(f'Auto update check skipped: {e}')

    def _apply_main_table_zebra(self):
        tb = self.uic.tableWidget
        tb.setAlternatingRowColors(True)

    def login(self):
        handle_login(self)

    def logout(self):
        handle_logout(self)
        self.uic.text_password.show()
        self.uic.text_user.show()
        self.uic.text_user.textChanged.connect(self.login)
        self.uic.text_password.textChanged.connect(self.login)
        self.uic.but_logout.setEnabled(False)
        self.but_check_update.setVisible(False)
        self.but_force_update.setVisible(False)

    def post_login_setup(self):
        self.uic.text_user.hide()
        self.uic.text_password.hide()
        self.uic.but_logout.setEnabled(True)
        self.uic.but_co_hoi_moi.setEnabled(True)
        self.uic.but_tao_co_hoi.setEnabled(True)

        self.uic.label_username.setText(self.user)

        # đảm bảo schema audit sẵn sàng
        try:
            misc.ensure_audit_schema()
        except Exception as e:
            print(f"init audit schema error: {e}")

        # Giới hạn hiển thị nút "Cơ hội mới" theo user
        blocked_new_lead_users = {'Vương', 'Huệ', 'Đức'}
        display_name = str(self.user or '').strip()
        hide_new_lead_btn = any(k in display_name for k in blocked_new_lead_users)
        self.uic.but_co_hoi_moi.setVisible(not hide_new_lead_btn)
        self.uic.but_co_hoi_moi.setEnabled(not hide_new_lead_btn)

        result = misc.sql_one("SELECT * from user where phone_number = %s", (self.user_phone,))
        self.user_power = int(result[3])

        # Phân quyền CRM: chỉ hiển thị khi power > 40
        self.uic.but_crm.setVisible(self.user_power > 40)
        self.uic.but_crm.setEnabled(self.user_power > 40)

        # Nút update thủ công chỉ hiện sau khi đăng nhập
        self.but_check_update.setVisible(True)
        # Bỏ nút "Cập nhật ngay" khỏi main GUI theo yêu cầu owner
        self.but_force_update.setVisible(False)

        # Chỉ power > 40 mới thấy và dùng được Quản lý kho + Sửa bảng giá
        # Nút Reports giữ nguyên cho mọi user (đã giới hạn dữ liệu theo quyền ở màn report)
        is_manager = self.user_power > 40
        self.uic.but_sua_bang_gia.setVisible(is_manager)
        self.uic.but_quan_ly_kho.setVisible(is_manager)
        self.uic.but_sua_bang_gia.setEnabled(is_manager)
        self.uic.but_quan_ly_kho.setEnabled(is_manager)

        self.uic.label_so_co_hoi.setText(misc.header_label(self.user))
        self.uic.label_so_co_hoi.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.uic.label_doanh_so.setText(misc.header_label_doanh_so(self.user))
        self.uic.label_doanh_so.setAlignment(Qt.AlignmentFlag.AlignRight)

        self._apply_main_table_zebra()
        # Ưu tiên hiển thị danh sách nhanh, dời normalize nặng sang nền sau khi vào app
        from time import time as _time
        self._last_lead_status_refresh_ms = int(_time() * 1000)
        self.show_lead(self.user)
        QTimer.singleShot(2500, lambda: (self._normalize_and_refresh_lead_statuses(force=True), self.show_lead(self.user)))
        self.set_combo_user_status(self.user)

        self.uic.but_logout.clicked.connect(self.logout)
        self.uic.but_mydesk.clicked.connect(lambda: self.show_lead(self.user))
        self.uic.but_co_hoi_moi.clicked.connect(lambda: self.show_co_hoi_moi())

        # Quản lý bảng giá
        self.win_banggia = QMainWindow()
        self.uic6 = Ui_Bang_gia()
        self.uic6.setupUi(self.win_banggia)
        apply_ui_v2(self.win_banggia)
        self.price_manager = PriceListManager(self.uic6, self.user)
        self.uic.but_sua_bang_gia.clicked.connect(self.sua_bang_gia)

        # Quản lý khách hàng (chỉ user power > 40)
        try:
            self.uic.but_crm.clicked.disconnect()
        except Exception:
            pass
        if self.user_power > 40:
            self.crm_handler = crm.Crm(self)
            self.crm_handler.user = self.user
            self.crm_handler.user_phone = self.user_phone
            # dùng cùng lead handler để mở nhanh màn tạo lead từ CRM
            self.crm_handler.lead_handler = self.lead_handler if hasattr(self, 'lead_handler') else None
            self.uic.but_crm.clicked.connect(self.crm_handler.company_view)
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
        if hasattr(self, 'crm_handler') and self.crm_handler:
            self.crm_handler.lead_handler = self.lead_handler

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

    def _normalize_and_refresh_lead_statuses(self, min_interval_ms: int = 300000, force: bool = False):
        """Chuẩn hóa status lead về enum duy nhất + tự động gắn trạng thái theo tuổi lead."""
        try:
            now_ms = int(QApplication.instance().property("_now_ms") or 0)
            if now_ms <= 0:
                from time import time as _time
                now_ms = int(_time() * 1000)

            if not force and (now_ms - int(getattr(self, '_last_lead_status_refresh_ms', 0) or 0) < int(min_interval_ms or 0)):
                return
            # 1) Normalize legacy statuses
            normalize_sql = [
                "UPDATE sale_lead SET status='Mới' WHERE status IS NULL OR TRIM(status) IN ('', '...', ' ...', 'waiting', 'new', 'Mới')",
                "UPDATE sale_lead SET status='Đã nhận việc' WHERE TRIM(status) IN ('Đang xử lý', 'Dang xử lý', 'Dang xu ly', 'Da nhan viec', 'Đã giao việc từ Anna', 'Da giao viec tu Anna', 'Da nhận việc')",
                "UPDATE sale_lead SET status='Đã báo giá' WHERE TRIM(status) IN ('Da bao gia', 'Da báo giá')",
                "UPDATE sale_lead SET status='Đã đặt hàng' WHERE TRIM(status) IN ('Da dat hang')",
                "UPDATE sale_lead SET status='Đã thanh toán' WHERE TRIM(status) IN ('Da thanh toan')",
                "UPDATE sale_lead SET status='Đã giao hàng' WHERE TRIM(status) IN ('Da giao hang')",
                "UPDATE sale_lead SET status='Đã trả lại toàn bộ' WHERE TRIM(status) IN ('Da tra lai toan bo')",
                "UPDATE sale_lead SET status='Done - Thất bại' WHERE TRIM(status) IN ('Done - That bai')",
            ]
            for q in normalize_sql:
                misc.sql_commit(q)
            misc.refresh_busy_for_all_users_with_open_leads()

            # 2) Auto-release lead Anna đã giao việc quá 1 giờ (nếu chưa có BG/ĐH)
            to_release = misc.sql_all(
                "SELECT l.lead_id, l.phu_trach, l.status FROM sale_lead l "
                "WHERE l.nguoi_tao_lead='Anna' "
                "AND l.status='Anna đã giao việc' "
                "AND TIMESTAMPDIFF(HOUR, l.time_create, NOW()) >= 1 "
                "AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id) "
                "AND NOT EXISTS (SELECT 1 FROM ds_don_hang o WHERE o.lead_id = l.lead_id)",
                None
            ) or []

            misc.sql_commit(
                "UPDATE sale_lead l "
                "SET l.status='Mới', l.phu_trach='', l.time_nhan_viec=NULL "
                "WHERE l.nguoi_tao_lead='Anna' "
                "AND l.status='Anna đã giao việc' "
                "AND TIMESTAMPDIFF(HOUR, l.time_create, NOW()) >= 1 "
                "AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id) "
                "AND NOT EXISTS (SELECT 1 FROM ds_don_hang o WHERE o.lead_id = l.lead_id)"
            )
            for lid, old_owner, old_status in to_release:
                misc.audit_log('system', 'AUTO_RELEASE', 'status', old_status, 'Mới', lid)
                misc.audit_log('system', 'UPDATE_OWNER', 'phu_trach', old_owner, '', lid)

            # 3) Auto-state from age (theo rule nghiệp vụ mới)
            base_filter = "status NOT IN ('Đã đặt hàng','Đã thanh toán','Đã giao hàng','Đã trả lại toàn bộ','Done - Thất bại')"

            # >10 ngày và chưa có đơn hàng theo lead
            misc.sql_commit(
                f"UPDATE sale_lead l SET l.status='Đã quá 10 ngày' "
                f"WHERE {base_filter} AND TIMESTAMPDIFF(DAY, l.time_create, NOW()) >= 10 "
                f"AND NOT EXISTS (SELECT 1 FROM ds_don_hang o WHERE o.lead_id = l.lead_id)"
            )

            # >3 ngày và chưa có đơn hàng theo lead
            misc.sql_commit(
                f"UPDATE sale_lead l SET l.status='Cần cập nhật lại' "
                f"WHERE {base_filter} AND TIMESTAMPDIFF(DAY, l.time_create, NOW()) >= 3 AND TIMESTAMPDIFF(DAY, l.time_create, NOW()) < 10 "
                f"AND NOT EXISTS (SELECT 1 FROM ds_don_hang o WHERE o.lead_id = l.lead_id)"
            )

            # >4 giờ và chưa có báo giá theo lead
            misc.sql_commit(
                f"UPDATE sale_lead l SET l.status='Đã quá hạn báo giá' "
                f"WHERE {base_filter} AND TIMESTAMPDIFF(HOUR, l.time_create, NOW()) >= 4 AND TIMESTAMPDIFF(DAY, l.time_create, NOW()) < 3 "
                f"AND NOT EXISTS (SELECT 1 FROM ds_bao_gia q WHERE q.lead_id = l.lead_id)"
            )

            self._last_lead_status_refresh_ms = now_ms
        except Exception as e:
            print(f"Lỗi normalize lead status: {e}")

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
            self._normalize_and_refresh_lead_statuses()
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
                self._apply_status_style_item(self.uic.tableWidget.item(row_idx, 2))

                btn = QPushButton('Duyệt/Từ chối' if t['action'] == 'DUYET_TU_CHOI' else 'Thực thi')
                btn.clicked.connect(lambda _, lid=t['lead_id'], sb=t['so_bg']: self._handle_return_task(lid, sb))
                self.uic.tableWidget.setCellWidget(row_idx, 3, btn)

                self.uic.tableWidget.resizeRowToContents(row_idx)
                if self.uic.tableWidget.rowHeight(row_idx) > 65:
                    self.uic.tableWidget.setRowHeight(row_idx, 65)
                row_idx += 1

            for item in result:
                lead_id, name, sdt, ten_co_hoi, trang_thai, phu_trach = item[0], item[1], item[2], item[9], item[10], item[11]
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(lead_id)))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(self._lead_display_text(name, sdt, ten_co_hoi)))
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(f"{trang_thai}\n{phu_trach}"))
                self._apply_status_style_item(self.uic.tableWidget.item(row_idx, 2))

                if trang_thai.strip() == 'Mới':
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
            self.uic.tableWidget.setItem(row, 1, QTableWidgetItem(self._lead_display_text(result[row][1], result[row][2], result[row][9])))
            txt = str(result[row][10]) + '\n' + str(result[row][11])
            self.uic.tableWidget.setItem(row, 2, QTableWidgetItem(txt))
            self._apply_status_style_item(self.uic.tableWidget.item(row, 2))
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

                if result[row][10] == 'Mới':
                    self.uic.tableWidget.setCellWidget(row, 3, but1)
                else:
                    self.uic.tableWidget.setCellWidget(row, 3, but2)

    def _lead_display_text(self, name, sdt, ten_co_hoi):
        line1 = f"{str(name or '').strip()} - {str(sdt or '').strip()}".strip(' -')
        line2 = str(ten_co_hoi or '').strip()
        if not line1:
            line1 = '(chưa có tên/SĐT liên hệ)'
        if not line2:
            line2 = '(chưa có tên cơ hội)'
        return f"{line1}\n{line2}"

    def _not_found(self, keyword="tìm kiếm"):
        self.uic.label_noti.setStyleSheet("color: red")
        self.uic.label_noti.setText(f"❌ Không tìm thấy kết quả theo {keyword.lower()}.")

    def universal_search(self):
        self.uic.label_noti.clear()
        raw_text = self.uic.tex_search.toPlainText()
        search_text = raw_text.strip()

        if not search_text:
            return

        try:
            user_power = int(getattr(self, 'user_power', 0) or 0)
        except Exception:
            user_power = 0

        # Giới hạn phạm vi theo combo_user nếu power < 40
        allowed_assignees = []
        if user_power < 40:
            for i in range(self.uic.combo_user.count()):
                name = self.uic.combo_user.itemText(i).strip()
                if name and name != 'All':
                    allowed_assignees.append(name)
            if not allowed_assignees and getattr(self, 'user', None):
                allowed_assignees = [self.user]

        where_parts = ["check_delete != '1'"]
        params = []

        if self.status != "All":
            where_parts.append("status = %s")
            params.append(self.status)

        if user_power < 40 and allowed_assignees:
            placeholders = ",".join(["%s"] * len(allowed_assignees))
            where_parts.append(f"phu_trach IN ({placeholders})")
            params.extend(allowed_assignees)

        base_where = " AND ".join(where_parts)

        # 1) Tìm theo SĐT (10 số)
        phone_digits = re.sub(r"\D", "", search_text)
        if re.match(r"^0\d{9}$", phone_digits):
            if '\n' in raw_text:
                self.uic.tex_search.setText(phone_digits)
            query = f"SELECT * FROM sale_lead WHERE {base_where} AND sdt = %s"
            results = misc.sql_all(query, tuple(params + [phone_digits]))
            return self.show_search_result(results) if results else self._not_found("SĐT")

        # 2) Tìm theo số báo giá
        if search_text.isdigit() and len(search_text) <= 6:
            result = misc.sql_one("SELECT lead_id FROM ds_bao_gia WHERE so_bg = %s", (search_text,))
            if result:
                lead_id = result[0]
                query = f"SELECT * FROM sale_lead WHERE {base_where} AND lead_id = %s"
                leads = misc.sql_all(query, tuple(params + [lead_id]))
                return self.show_search_result(leads) if leads else self._not_found("Số BG")
            return self._not_found("Số BG")

        # 3) Mở rộng tìm theo: lead_id, tên cơ hội (ten_co_hoi), tên người liên hệ (name)
        query = (
            f"SELECT * FROM sale_lead WHERE {base_where} "
            "AND (CAST(lead_id AS CHAR) LIKE %s OR ten_co_hoi LIKE %s OR name LIKE %s)"
        )
        kw = f"%{search_text}%"
        results = misc.sql_all(query, tuple(params + [kw, kw, kw]))
        return self.show_search_result(results) if results else self._not_found("Lead/Tên cơ hội/Tên liên hệ")

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
        power = int(getattr(self, 'user_power', 0) or 0)

        # Sales thường (<=40) không có flow duyệt/thực thi trả hàng -> bỏ qua sớm
        if power <= 40:
            return out

        from time import time as _time
        now_ms = int(_time() * 1000)
        # Cache 30s để giảm tải SQL + parse log
        if now_ms - int(getattr(self, '_return_tasks_cache_ms', 0) or 0) < 30000:
            return list(getattr(self, '_return_tasks_cache', []) or [])

        rows = misc.sql_all(
            "SELECT d.so_bg, d.lead_id, d.lich_su_gd, s.name, s.company "
            "FROM ds_don_hang d LEFT JOIN sale_lead s ON s.lead_id = d.lead_id "
            "WHERE d.lich_su_gd IS NOT NULL AND d.lich_su_gd != '' "
            "AND (d.lich_su_gd LIKE '%RETURN_REQ_JSON|%' OR d.lich_su_gd LIKE '%RETURN_REQ_APPROVED|%' "
            "OR d.lich_su_gd LIKE '%RETURN_REQ_EXECUTED|%' OR d.lich_su_gd LIKE '%RETURN_REQ_REJECTED|%') "
            "ORDER BY d.so_bg DESC LIMIT 300",
            None,
        ) or []

        for r in rows:
            so_bg, lead_id, lich_su_gd, name, company = r[0], r[1], r[2], r[3], r[4]
            payload = self._parse_return_request_from_log(lich_su_gd)
            if not payload:
                continue

            state = str(payload.get("state", "")).upper()

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

        self._return_tasks_cache = list(out)
        self._return_tasks_cache_ms = now_ms
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

    def _set_main_loading_lock(self, locked: bool, text: str = ""):
        try:
            self.uic.tableWidget.setEnabled(not locked)
            for n in [
                'but_mydesk', 'but_co_hoi_moi', 'but_tao_co_hoi', 'but_crm',
                'but_sua_bang_gia', 'but_quan_ly_kho', 'but_baocao', 'tex_search'
            ]:
                if hasattr(self.uic, n):
                    getattr(self.uic, n).setEnabled(not locked)
            if hasattr(self, 'but_check_update'):
                self.but_check_update.setEnabled(not locked)
            if hasattr(self, 'but_force_update'):
                self.but_force_update.setEnabled(not locked)
            if locked:
                self.uic.label_noti.setStyleSheet("color: #2563EB")
                self.uic.label_noti.setText(text or "Loading ... ... ...")
            else:
                self.uic.label_noti.setStyleSheet("color: green")
        except Exception:
            pass

    def _render_lead_chunk(self):
        st = getattr(self, '_lead_lazy_state', None)
        if not st:
            return

        rows = st['rows']
        idx = st['idx']
        total = len(rows)
        chunk = st.get('chunk', 50)
        end = min(idx + chunk, total)

        for row_idx in range(idx, end):
            r = rows[row_idx]
            if r['kind'] == 'task':
                t = r['data']
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(t['lead_id'])))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(t['text']))
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(t['status']))
                self._apply_status_style_item(self.uic.tableWidget.item(row_idx, 2))
                btn = QPushButton('Duyệt/Từ chối' if t['action'] == 'DUYET_TU_CHOI' else 'Thực thi')
                btn.clicked.connect(lambda _, lid=t['lead_id'], sb=t['so_bg']: self._handle_return_task(lid, sb))
                self.uic.tableWidget.setCellWidget(row_idx, 3, btn)
            else:
                lead_id, ten_lh, sdt_lh, ten_co_hoi, trang_thai, phu_trach = r['data']
                self.uic.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(lead_id)))
                self.uic.tableWidget.setItem(row_idx, 1, QTableWidgetItem(self._lead_display_text(ten_lh, sdt_lh, ten_co_hoi)))
                txt = str(trang_thai or '') + '\n' + str(phu_trach or '')
                self.uic.tableWidget.setItem(row_idx, 2, QTableWidgetItem(txt))
                self._apply_status_style_item(self.uic.tableWidget.item(row_idx, 2))
                but2 = QPushButton('Cập nhật')
                but2.clicked.connect(lambda _, lid=lead_id: LeadHandle.update_job(self, str(lid)))
                self.uic.tableWidget.setCellWidget(row_idx, 3, but2)

        st['idx'] = end
        if total > 0:
            self.uic.label_noti.setText("Loading ... ... ...")

        if end < total:
            QTimer.singleShot(0, self._render_lead_chunk)
            return

        self._set_main_loading_lock(False)
        if total == 0:
            self.uic.label_noti.setText('Cơ hội bán hàng!')
        else:
            self.uic.label_noti.setText(generate_greeting())
        self.uic.tableWidget.repaint()
        self._lead_lazy_state = None

    def show_lead(self, user):
        try:
            self._normalize_and_refresh_lead_statuses()
            self.thong_ke()
            self.uic.tableWidget.clear()
            self.uic.tableWidget.verticalHeader().setVisible(False)

            kq = misc.sql_one('SELECT power FROM user WHERE full_name = %s', (self.user,))
            if not kq:
                return

            if int(kq[0]) < 40:
                code = (
                    "SELECT lead_id, name, sdt, ten_co_hoi, status, phu_trach "
                    "FROM sale_lead WHERE phu_trach = %s AND check_delete != '1' "
                    "AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY) "
                    "ORDER BY lead_id DESC LIMIT 500"
                )
                result = misc.sql_all(code, (self.user,))
            else:
                code = (
                    "SELECT lead_id, name, sdt, ten_co_hoi, status, phu_trach "
                    "FROM sale_lead WHERE status != 'Mới' AND check_delete != '1' "
                    "AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY) "
                    "ORDER BY lead_id DESC LIMIT 500"
                )
                result = misc.sql_all(code, None)

            result = result or []

            self.uic.tableWidget.setColumnCount(4)
            self.uic.tableWidget.setHorizontalHeaderLabels(['Lead', 'Yêu cầu của khách hàng', 'Trạng thái', 'Phụ trách'])
            self.uic.tableWidget.setColumnWidth(0, 60)
            self.uic.tableWidget.setColumnWidth(1, 400)
            self.uic.tableWidget.setColumnWidth(2, 140)
            self.uic.tableWidget.setColumnWidth(3, 100)
            self.uic.tableWidget.verticalHeader().setDefaultSectionSize(48)

            tasks = self._get_return_request_tasks()
            merged_rows = ([{'kind': 'task', 'data': t} for t in tasks] +
                           [{'kind': 'lead', 'data': item} for item in result])

            total_rows = len(merged_rows)
            self.uic.tableWidget.setRowCount(total_rows)

            self._lead_lazy_state = {
                'rows': merged_rows,
                'idx': 0,
                'chunk': 50,
            }
            self._set_main_loading_lock(True, "Loading ... ... ...")
            QTimer.singleShot(0, self._render_lead_chunk)

        except Exception as e:
            self._set_main_loading_lock(False)
            print(e)
            print("❌ Lỗi khi show lead!!!")
            return

    def show_co_hoi_moi(self):
        try:
            self._normalize_and_refresh_lead_statuses()
            self.thong_ke()
            self.uic.tableWidget.clear()
            self.uic.tableWidget.verticalHeader().setVisible(False)

            code = "SELECT * FROM sale_lead WHERE status = 'Mới' AND check_delete != '1' AND time_create >= DATE_SUB(NOW(), INTERVAL 90 DAY)"
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

                    self.uic.tableWidget.setItem(row, 1, QTableWidgetItem(self._lead_display_text(result[row][1], result[row][2], result[row][9])))
                    txt = result[row][10] + '\n' + result[row][11]
                    self.uic.tableWidget.setItem(row, 2, QTableWidgetItem(txt))
                    self._apply_status_style_item(self.uic.tableWidget.item(row, 2))

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
            old = misc.sql_one("SELECT phu_trach, status FROM sale_lead WHERE lead_id = %s", (lead_id,))
            old_owner = old[0] if old else ''
            old_status = old[1] if old else ''

            misc.sql_commit("UPDATE sale_lead SET phu_trach = %s, status = 'Đã nhận việc', time_nhan_viec = NOW() "
                          "WHERE lead_id = %s", (self.user, lead_id,))

            misc.refresh_user_busy(old_owner)
            misc.refresh_user_busy(self.user)

            misc.audit_log(self.user, 'UPDATE_OWNER', 'phu_trach', old_owner, self.user, lead_id)
            misc.audit_log(self.user, 'UPDATE_STATUS', 'status', old_status, 'Đã nhận việc', lead_id)

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
    load_global_stylesheet(app)

    win = MainWindow()
    QTimer.singleShot(0, win.show)

    print("Entering event loop")
    sys.exit(app.exec())

