from datetime import datetime, timedelta

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QStyledItemDelegate, QLineEdit, \
    QPushButton

import misc
import stock_ui_utils
from UI.nhap_xuat_kho import Ui_NhapXuat
from quotation import Quotato
from UI.report import Ui_Report
from UI.win_bao_gia import Ui_Win_bao_gia


class DigitCommaDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)

        # Allow digits and commas, e.g., "1", "2,000", "123,456"
        regex = QRegularExpression(r"^\d{1,3}(,\d{3})*$|^\d*$")
        validator = QRegularExpressionValidator(regex, editor)
        editor.setValidator(validator)

        return editor


class Report(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_power = None
        self.user = None
        self.win_baocao = None
        self.uic13 = None

    def khoitao(self, user):

        self.user = user
        self.win_baocao = QMainWindow()
        self.uic13 = Ui_Report()
        self.uic13.setupUi(self.win_baocao)
        self.win_baocao.show()

        self.setWindowTitle(QApplication.translate("Bao cao ket qua kinh doanh theo ky".encode('utf-8').decode('utf-8'), "Fsale v3.04.2025"))

        # Tạo list user
        kq = misc.sql_one("SELECT power FROM user WHERE full_name = %s", (self.user, ))
        self.user_power = kq[0]

        if int(self.user_power) > 40:

            kq = [ele[0] for ele in misc.sql_all("SELECT full_name FROM user WHERE power > 0", None)]
            self.uic13.comboBox.addItems(kq)
            self.uic13.comboBox.addItems(['Tổng thể cả công ty'])
            self.uic13.comboBox.setCurrentText('Tổng thể cả công ty')
        else:
            self.uic13.comboBox.addItems([self.user])

        # Get the current date
        today = datetime.today()

        # Determine the first day of the current month
        first_day_this_month = today.replace(day=1)

        # Determine the last day of the last month by subtracting one day from the first day of this month
        last_day_last_month = first_day_this_month - timedelta(days=1)

        # Determine the first day of the last month by replacing the day with 1
        first_day_last_month = last_day_last_month.replace(day=1)

        self.uic13.date_from.setDate(first_day_last_month)
        self.uic13.date_to.setDate(last_day_last_month)

        self.uic13.label_user.setText(self.user)

        self.uic13.tableWidget.setRowCount(6)  # tạo số row
        self.uic13.tableWidget.setColumnCount(7)  # tạo số column
        self.uic13.tableWidget.setColumnWidth(0, 80)
        self.uic13.tableWidget.setColumnWidth(1, 80)
        self.uic13.tableWidget.setColumnWidth(2, 120)
        self.uic13.tableWidget.setColumnWidth(3, 120)
        self.uic13.tableWidget.setColumnWidth(4, 120)
        self.uic13.tableWidget.setColumnWidth(5, 120)
        self.uic13.tableWidget.setColumnWidth(6, 170)

        header = ['Số BG', 'Lead', 'Doanh số', 'Nợ phải thu', 'Profit', 'Ngày giao hàng', 'Người giao hàng']
        self.uic13.tableWidget.setHorizontalHeaderLabels(header)
        self.uic13.tableWidget.repaint()

        self.uic13.comboBox.currentTextChanged.connect(lambda: Report.baocaothang(self, self.uic13.comboBox.currentText()))
        self.uic13.pushButton.clicked.connect(lambda: Report.baocaothang(self, self.uic13.comboBox.currentText()))

        Report.baocaothang(self, self.uic13.comboBox.currentText())
        # Report.thong_ke_cong_no(self, self.uic13.comboBox.currentText())

    def thong_ke_cong_no(self, user, kq):
        self.uic13.tableWidget_3.setRowCount(len(kq))  # tạo số row
        self.uic13.tableWidget_3.setColumnCount(11)  # tạo số column
        self.uic13.tableWidget_3.setColumnWidth(0, 75)
        self.uic13.tableWidget_3.setColumnWidth(1, 80)
        self.uic13.tableWidget_3.setColumnWidth(2, 60)
        self.uic13.tableWidget_3.setColumnWidth(3, 80)
        self.uic13.tableWidget_3.setColumnWidth(4, 80)
        self.uic13.tableWidget_3.setColumnWidth(5, 80)
        self.uic13.tableWidget_3.setColumnWidth(6, 110)
        self.uic13.tableWidget_3.setColumnWidth(7, 80)
        self.uic13.tableWidget_3.setColumnWidth(8, 80)
        self.uic13.tableWidget_3.setColumnWidth(9, 80)

        header = ['Số BG', 'Doanh số', 'VAT', 'Đã TT', 'Phải thu', 'Ngày bán', 'Chịu trách nhiệm', 'Thu tiền', ' ', 'LSTT', 'Xem phiếu xuất']
        self.uic13.tableWidget_3.setHorizontalHeaderLabels(header)
        self.uic13.tableWidget_3.repaint()

        # Column 7 (index 7) is "Thu tiền" and gets digit+comma validator
        self.uic13.tableWidget_3.setItemDelegateForColumn(7, DigitCommaDelegate())

        kq = sorted(kq, key=lambda x: x[0])
        for row in range(self.uic13.tableWidget_3.rowCount()):
            for col in range(11):
                item = QTableWidgetItem()
                if col == 0:
                    so_bg = str(kq[row][col])
                    item.setText(so_bg)

                    but1 = QPushButton(so_bg)
                    but1.clicked.connect(lambda _, bg=so_bg: Report.xem_lai_bao_gia(self, bg))

                    self.uic13.tableWidget_3.setCellWidget(row, 0, but1)

                elif col in [1, 2, 3]:
                    if kq[row][col] != '':
                        temp = str(kq[row][col+1]).replace(",", "")
                        item.setText("{:,}".format(round(int(temp), 0)))
                elif col == 4:
                    cong_no = int(kq[row][2]) + int(kq[row][3]) - int(kq[row][4])
                    item.setText(("{:,}".format(cong_no)))

                elif col == 5:
                    value = kq[row][6]
                    if isinstance(value, (int, float)):
                        # Nếu nó là int (timestamp dạng seconds), thì convert
                        value = datetime.fromtimestamp(value)
                    elif isinstance(value, str):
                        try:
                            # Nếu nó là string dạng ngày, parse ra datetime
                            value = datetime.strptime(value, "%Y-%m-%d")
                        except:
                            value = None

                    if value:
                        item.setText(value.strftime("%d/%m/%Y"))
                    else:
                        item.setText("")
                elif col == 6:
                    if user != 'Tổng thể cả công ty':
                        item.setText(user)

                self.uic13.tableWidget_3.setItem(row, col, item)
            # self.uic13.tableWidget_3.resizeRowToContents(row)
            self.uic13.tableWidget_3.setRowHeight(row, 45)
        self.uic13.tableWidget_3.repaint()

        self.uic13.tableWidget_3.itemChanged.connect(lambda: Report.on_cell_changed(self))
        if self.uic13.tableWidget_3.rowCount() > 0:
            self.uic13.tableWidget_3.cellClicked.connect(lambda: Report.on_row_focus(self, None))

    def xem_lai_bao_gia(self, so_bg=None):
        if so_bg is None:
            row = self.uic13.tableWidget_3.currentRow()
            if row < 0:
                return
            so_bg = self.uic13.tableWidget_3.item(row, 0).text()

        try:
            self.sub_win1 = QMainWindow()
            self.uic5 = Ui_Win_bao_gia()
            self.uic5.setupUi(self.sub_win1)
            self.sub_win1.show()
        except:
            pass

        # Tìm thông tin báo giá theo số báo giá
        kq = misc.sql_one("SELECT * from ds_bao_gia WHERE so_bg = %s", (so_bg,))

        if kq[16] == 'T':
            self.uic5.checkBox.setChecked(True)
        else:
            self.uic5.checkBox.setChecked(False)

        self.uic5.checkBox.repaint()

        goods = kq[3].split('@')
        data = []
        for item in goods:
            data.append(item.split('|'))

        if kq[4] == 'T':
            self.uic5.but_luu_file.setDisabled(True)
            self.uic5.label_noti.setStyleSheet("color: red")
            self.uic5.label_noti.setText('Báo giá này đã xuất hàng, không sửa được nữa.')
            tex = misc.sql_one("SELECT lich_su_gd FROM ds_don_hang WHERE so_bg = %s", (so_bg,))[0]
            if tex:
                self.uic5.text_ghi_chu.setText('Lịch sử thanh toán:' + tex)
            else:
                self.uic5.text_ghi_chu.setText('Lịch sử thanh toán:')

        lead_id = str(kq[1])
        Quotato.show_bg(self, lead_id, so_bg, data)

    def on_cell_changed(self):
        if self.uic13.tableWidget_3.currentColumn() == 7:
            row = self.uic13.tableWidget_3.currentRow()
            text = self.uic13.tableWidget_3.item(row, 7).text().replace(",", "")
            if len(text) > 3:
                but1 = QPushButton('Xác nhận')
                but1.clicked.connect(lambda: Report.xac_nhan_thu_tien(self))
                self.uic13.tableWidget_3.setCellWidget(row, 8, but1)
                self.uic13.tableWidget_3.blockSignals(True)
                self.uic13.tableWidget_3.setItem(row, 7, QTableWidgetItem("{:,}".format(int(text))))
                self.uic13.tableWidget_3.blockSignals(False)

    def on_row_focus(self, so_bg=None):
        # 🧹 Duyệt qua toàn bộ dòng, xóa widget ở cột 9 và 10
        for r in range(self.uic13.tableWidget_3.rowCount()):
            for col in [9, 10]:
                old_widget = self.uic13.tableWidget_3.cellWidget(r, col)
                if old_widget:
                    self.uic13.tableWidget_3.removeCellWidget(r, col)
                    old_widget.setParent(None)
                    old_widget.deleteLater()
                    self.uic13.tableWidget_3.setItem(r, col, QTableWidgetItem(""))  # Cho trống luôn

        # Sau đó, ở dòng hiện tại, thêm 2 nút mới
        row = self.uic13.tableWidget_3.currentRow()

        but2 = QPushButton('Xem LSTT')
        but2.clicked.connect(lambda: Report.xem_lai_bao_gia(self))
        self.uic13.tableWidget_3.setCellWidget(row, 9, but2)

        but3 = QPushButton('Phiếu xuất')
        but3.clicked.connect(lambda: Report.xem_lai_phieu_xuat(self))
        self.uic13.tableWidget_3.setCellWidget(row, 10, but3)

    def xem_lai_phieu_xuat(self):
        row = self.uic13.tableWidget_3.currentRow()
        so_bg = self.uic13.tableWidget_3.item(row, 0).text()
        sophieu = misc.sql_one("SELECT id FROM xuat_kho WHERE so_bg = %s", (so_bg,))[0]

        try:
            self.win_stock = QMainWindow()
            self.uic7 = Ui_NhapXuat()
            self.uic7.setupUi(self.win_stock)
            self.win_stock.show()
        except:
            pass
        # Disable tất cả các nút
        [btn.hide() for btn in self.findChildren(QPushButton)]
        self.uic7.label.setStyleSheet("color: red")
        self.uic7.label.setText("Xem lại phiếu xuất kho - không thể sửa")

        kq = misc.sql_one("SELECT * from xuat_kho WHERE id = %s", (sophieu,))

        hanghoa = [ele.split('|') for ele in kq[2].split('@@')]

        # Ghi nội dung biến tb - tức là nội dung phiếu xuất - lên màn hình
        stock_ui_utils.setup_table_xuat(self.uic7.tableWidget, len(kq))

        for row in range(len(hanghoa)):
            self.uic7.tableWidget.setItem(row, 0, QTableWidgetItem(str(hanghoa[row][0])))
            self.uic7.tableWidget.setItem(row, 1, QTableWidgetItem(str(hanghoa[row][1])))
            self.uic7.tableWidget.setItem(row, 2, QTableWidgetItem(str(hanghoa[row][2])))
            self.uic7.tableWidget.setItem(row, 3, QTableWidgetItem("{:,}".format(int(hanghoa[row][3]))))
            self.uic7.tableWidget.setItem(row, 4, QTableWidgetItem(str(hanghoa[row][4])))

        self.uic7.tableWidget.repaint()

        tong_tien = sum(int(item[3]) for item in hanghoa)
        self.uic7.text_gia_tri.setText("{:,}".format(tong_tien))

        con_no = self.uic13.tableWidget_3.item(row, 3).text()
        self.uic7.text_cong_no.setText(con_no)

        self.uic7.text_noi_dung_xuat.setText(kq[8])
        self.uic7.text_lead.setText(str(kq[7]))
        self.uic7.text_so_bg.setText(str(kq[6]))
        self.uic7.text_nguoi_nhan_hang.setText(kq[9])
        self.uic7.text_dia_chi.setText(kq[10])
        self.uic7.text_sdt.setText(kq[11])

    def xac_nhan_thu_tien(self):
        try:
            row = self.uic13.tableWidget_3.currentRow()
            if row < 0:
                self.uic13.label_noti.setText("⚠️ Vui lòng chọn một đơn hàng trước khi xác nhận thu tiền.")
                return

            def get_int_col(col):
                text = self.uic13.tableWidget_3.item(row, col).text().replace(",", "").strip()
                return int(text) if text.isdigit() else 0

            so_bg = self.uic13.tableWidget_3.item(row, 0).text().strip()
            thu_them = get_int_col(7)
            da_thanh_toan = get_int_col(3)
            tong_tien = get_int_col(1)

            da_thanh_toan_moi = da_thanh_toan + thu_them
            phai_thu_moi = tong_tien - da_thanh_toan_moi

            # Cập nhật cơ sở dữ liệu
            misc.sql_commit("UPDATE ds_don_hang SET da_thanh_toan = %s, phai_thu = %s WHERE so_bg = %s",
                            (da_thanh_toan_moi, phai_thu_moi, so_bg))

            Report.ghi_lich_su_thanh_toan_cua_don_hang(self, so_bg, thu_them)

            # ✅ Remove button
            self.uic13.tableWidget_3.removeCellWidget(row, 8)

            # Gửi thông báo telegram
            misc.send_to_telegram(f"💰 {self.user} xác nhận thu {thu_them:,} VNĐ cho đơn hàng số {so_bg}.")

            # Refresh lại thống kê
            Report.baocaothang(self, self.uic13.comboBox.currentText())

            self.uic13.label_noti.setStyleSheet("color: green")
            self.uic13.label_noti.setText(f"✅ Đã cập nhật thu tiền cho đơn hàng số {so_bg}.")

        except Exception as e:
            print(e)
            self.uic13.label_noti.setStyleSheet("color: red")
            self.uic13.label_noti.setText("❌ Lỗi trong quá trình xác nhận thu tiền.")

    def ghi_lich_su_thanh_toan_cua_don_hang(self, so_bg, thu_them):
        gio = datetime.now()
        lsgd = misc.sql_one("SELECT lich_su_gd FROM ds_don_hang WHERE so_bg = %s", (so_bg,))[0]
        if lsgd:
            lsgd = lsgd + '@@' + f"{thu_them}|{so_bg}|{gio}|{self.user}"
        else:
            lsgd = f"{thu_them}|{so_bg}|{gio}|{self.user}"
        misc.sql_commit("UPDATE ds_don_hang SET lich_su_gd = %s WHERE so_bg = %s", (lsgd, so_bg,))
        print(self.user, ' xác nhận thu tiền từ đơn hàng số bg ', so_bg, '. Số tiền là: ', thu_them, ' vào lúc: ', gio)

    def baocaothang(self, user):

        fromdate = self.uic13.date_from.date().toString("yyyy-MM-dd")
        todate = self.uic13.date_to.date().toString("yyyy-MM-dd")

        if user == 'Tổng thể cả công ty':

            code1 = ("SELECT so_bg FROM xuat_kho WHERE ngay_thang BETWEEN %s AND %s")
            kq1 = [ele[0] for ele in misc.sql_all(code1, (fromdate, todate,))]

            if kq1:
                placeholders = ','.join(['%s'] * len(kq1))
                query = (
                    f"SELECT so_bg, lead_id, tien_hang, vat, da_thanh_toan, profit, ngay_hen_giao_hang, nguoi_cai_dat "
                    f"FROM ds_don_hang WHERE so_bg IN ({placeholders})")
                kq = [list(row) for row in misc.sql_all(query, tuple(kq1))]
            else:
                kq = []

        else:
            code1 = ("SELECT so_bg FROM xuat_kho WHERE ngay_thang BETWEEN %s AND %s")
            kq1 = [ele[0] for ele in misc.sql_all(code1, (fromdate, todate,))]

            if kq1:
                placeholders = ','.join(['%s'] * len(kq1))
                query = (
                    f"SELECT so_bg, lead_id, tien_hang, vat, da_thanh_toan, profit, ngay_hen_giao_hang, nguoi_cai_dat "
                    f"FROM ds_don_hang WHERE so_bg IN ({placeholders}) AND nguoi_tao = %s")
                params = tuple(kq1) + (user,)  # ✅ gộp lại thành 1 tuple
                kq = [list(row) for row in misc.sql_all(query, params)]
            else:
                kq = []

        self.uic13.tableWidget.setRowCount(len(kq))  # tạo số row
        self.uic13.tableWidget.setColumnCount(8)  # tạo số column
        self.uic13.tableWidget.setColumnWidth(0, 60)
        self.uic13.tableWidget.setColumnWidth(1, 60)
        self.uic13.tableWidget.setColumnWidth(2, 80)
        self.uic13.tableWidget.setColumnWidth(3, 60)
        self.uic13.tableWidget.setColumnWidth(4, 90)
        self.uic13.tableWidget.setColumnWidth(5, 80)
        self.uic13.tableWidget.setColumnWidth(6, 100)
        self.uic13.tableWidget.setColumnWidth(7, 170)

        header = ['Số BG', 'Lead', 'Doanh số', 'vat', 'Đã thanh toán', 'Nợ phải thu', 'Ngày giao hàng', 'Người giao hàng']
        self.uic13.tableWidget.setHorizontalHeaderLabels(header)
        self.uic13.tableWidget.repaint()

        kq = sorted(kq, key=lambda x: x[5])

        for row in range(self.uic13.tableWidget.rowCount()):
            for col in range(8):
                item = QTableWidgetItem()
                if col in [2, 3, 4]:
                    if kq[row][col] != '':
                        temp = str(kq[row][col]).replace(",", "")
                        item.setText("{:,}".format(round(int(temp), 0)))
                elif col == 5:
                    cong_no = int(kq[row][2]) + int(kq[row][3]) - int(kq[row][4])
                    item.setText(("{:,}".format(cong_no)))

                elif col == 6:
                    value = kq[row][6]
                    if isinstance(value, (int, float)):
                        # Nếu nó là int (timestamp dạng seconds), thì convert
                        value = datetime.fromtimestamp(value)
                    elif isinstance(value, str):
                        try:
                            # Nếu nó là string dạng ngày, parse ra datetime
                            value = datetime.strptime(value, "%Y-%m-%d")
                        except:
                            value = None

                    if value:
                        item.setText(value.strftime("%d/%m/%Y"))
                    else:
                        item.setText("")
                elif col == 7:
                    if kq[row][7] == 'Tổng thể cả công ty':
                        pass
                    else:
                        item.setText(str(kq[row][7]))
                else:
                    item.setText(str(kq[row][col]))
                self.uic13.tableWidget.setItem(row, col, item)
            self.uic13.tableWidget.resizeRowToContents(row)
        self.uic13.tableWidget.repaint()

        Report.kpi(self, user, kq)
        Report.thong_ke_cong_no(self, self.uic13.comboBox.currentText(), kq)

    def kpi(self, user, kq):
        doanhso = sum(int(ele[2]) for ele in kq)
        # nợ phải thu = doanh số + VAT - đã thanh toán
        phaithu = sum(int(ele[2]) + int(ele[3]) - int(ele[4]) for ele in kq)
        profit = sum(int(ele[5]) for ele in kq)

        self.uic13.clb_doanh_so.setText('Doanh số:   ' + str("{:,}".format(doanhso)) + ' đ')
        self.uic13.clb_phai_thu.setText('Phải thu:   ' + str("{:,}".format(phaithu)) + ' đ')

        if int(self.user_power) > 40:
            self.uic13.clb_profit.setText('Profit:   ' + str("{:,}".format(profit)) + ' đ')
        else:
            self.uic13.clb_profit.hide()

        fromdate = self.uic13.date_from.date().addDays(-1).toString("yyyy-MM-dd")
        todate = self.uic13.date_to.date().addDays(1).toString("yyyy-MM-dd")

        code = "SELECT lead_id FROM sale_lead WHERE nguoi_tao_lead = %s AND time_create > %s AND time_create < %s"
        kq = misc.sql_all(code, (user, fromdate, todate,))

        code = "SELECT so_bg FROM ds_don_hang WHERE nguoi_tao = %s AND ngay_hen_giao_hang > %s AND ngay_hen_giao_hang < %s AND da_hoan_thanh = 'T'"
        kq1 = misc.sql_all(code, (user, fromdate, todate,))

        self.uic13.clb_don_lead.setText('Đơn/lead:   ' + str(len(kq1)) + '/' + str(len(kq)))
        if len(kq) > 0:
            self.uic13.clb_ti_le_thanh_cong.setText('Thành công:   ' + str(round(len(kq1)/len(kq)*100)) + '%')
        else:
            self.uic13.clb_ti_le_thanh_cong.setText('Thành công:   0%')

        ds_kd = ['Lê Văn Việt', 'Nguyễn Hải Hà', 'Phí Ngọc Tùng', 'Dương Lê Hiệp']
        ds_ctv = ['Nguyễn Xuân Thủy', 'Mai Anh Đức', 'Nguyễn T M Huệ', 'Nguyễn Thanh Vương']
        ds_ke_toan = ['Nguyễn Ngọc Linh']

        if user in ds_kd:
            Report.bonus(self, user)
        elif user in ds_ctv:
            Report.commission(self, user)
        elif user in ds_ke_toan:
            Report.bonus_ketoan(self, user)

    def bonus_ketoan(self, user):
        ds_ctv = ['Nguyễn Xuân Thủy', 'Mai Anh Đức', 'Nguyễn T M Huệ', 'Nguyễn Thanh Vương']

        fromdate = self.uic13.date_from.date().addDays(-1).toString("yyyy-MM-dd")
        todate = self.uic13.date_to.date().addDays(1).toString("yyyy-MM-dd")

        code = ("SELECT so_bg, lead_id, tien_hang, vat, da_thanh_toan, profit, ngay_hen_giao_hang, nguoi_tao, "
                "nguoi_tao_lead, nguoi_tu_van, nguoi_cai_dat, phai_thu FROM ds_don_hang "
                "WHERE ngay_hen_thanh_toan > %s AND ngay_hen_thanh_toan < %s AND da_hoan_thanh = 'T'")
        kq = [list(ele) for ele in misc.sql_all(code, (fromdate, todate,))]

        ds = []
        for item in kq:
            bonus = 0
            # if item[8] not in ds_ctv:

            if user == item[8]:  # Nếu là người tạo lead thì bonus = 2% doanh số
                bonus = bonus + int(item[2]) * 0.02
            if user == item[9]:  # Nếu là người tư vấn thì bonus = 1% doanh số
                bonus = bonus + int(item[2]) * 0.01
            if user == item[10]:  # Nếu là người cài đặt và giao hàng thì bonus = 0.5% doanh số
                bonus = bonus + int(item[2]) * 0.005

            bonus = bonus + int(item[2]) * 0.005  # Bonus của kế toán là 0.5% giá trị đơn hàng
            item.append(bonus)
            ds.append(item)

        bonus = 0
        for item in ds:
            bonus += item[12]
        self.uic13.clb_bonus.setText('Bonus: ' + "{:,}".format(round(bonus), 0))

        self.uic13.tableWidget_2.setRowCount(len(ds))  # tạo số row
        self.uic13.tableWidget_2.setColumnCount(7)  # tạo số column
        self.uic13.tableWidget_2.setColumnWidth(0, 80)
        self.uic13.tableWidget_2.setColumnWidth(1, 80)
        self.uic13.tableWidget_2.setColumnWidth(2, 120)
        self.uic13.tableWidget_2.setColumnWidth(3, 120)
        self.uic13.tableWidget_2.setColumnWidth(4, 120)
        self.uic13.tableWidget_2.setColumnWidth(5, 120)
        self.uic13.tableWidget_2.setColumnWidth(6, 120)

        header = ['Số BG', 'Ngày tháng', 'Doanh số', '2% tạo lead', '1% báo giá', '0.5% cài đặt', 'Bonus']
        self.uic13.tableWidget_2.setHorizontalHeaderLabels(header)
        for row in range(self.uic13.tableWidget_2.rowCount()):
            doanhso = int(ds[row][2])
            for col in range(7):
                item = QTableWidgetItem()
                if col == 0:
                    item.setText(str(ds[row][0]))
                elif col == 1:
                    item.setText(ds[row][6].strftime("%d/%m/%Y"))
                elif col == 2:
                    item.setText("{:,}".format(round(int(ds[row][2]), 0)))
                elif col == 3:
                    if user == ds[row][8]:
                        item.setText("{:,}".format(round(doanhso * 0.02), 0))
                    else:
                        item.setText(str(ds[row][8]))
                elif col == 4:
                    if user == ds[row][9]:
                        item.setText("{:,}".format(round(doanhso * 0.01), 0))
                    else:
                        item.setText(str(ds[row][9]))
                elif col == 5:
                    if user == ds[row][10]:
                        item.setText("{:,}".format(round(doanhso * 0.005), 0))
                    else:
                        item.setText(str(ds[row][10]))
                elif col == 6:
                    item.setText("{:,}".format(round(int(ds[row][12]), 0)))
                self.uic13.tableWidget_2.setItem(row, col, item)
        self.uic13.tableWidget_2.insertRow(len(ds) + 1)

    def commission(self, user):
        fromdate = self.uic13.date_from.date().toString("yyyy-MM-dd")
        todate = self.uic13.date_to.date().toString("yyyy-MM-dd")

        code1 = "SELECT so_bg FROM xuat_kho WHERE ngay_thang BETWEEN %s AND %s"
        kq1 = [ele[0] for ele in misc.sql_all(code1, (fromdate, todate))]

        if kq1:
            placeholders = ','.join(['%s'] * len(kq1))
            query_dh = (
                f"SELECT so_bg, lead_id, tien_hang, vat, da_thanh_toan, profit, ngay_hen_giao_hang, nguoi_tao, nguoi_tao_lead, nguoi_tu_van, nguoi_cai_dat, phai_thu "
                f"FROM ds_don_hang WHERE so_bg IN ({placeholders})")
            ds = [list(row) for row in misc.sql_all(query_dh, tuple(kq1))]

            query_bg = f"SELECT so_bg, noi_dung FROM ds_bao_gia WHERE so_bg IN ({placeholders})"
            kq_bg = misc.sql_all(query_bg, tuple(kq1))
            noi_dung_dict = {str(row[0]): row[1] for row in kq_bg}

            query_gia = "SELECT model, gia_cap_2 FROM gia_tong_hop"
            model_price_map = {row[0]: row[1] for row in misc.sql_all(query_gia)}
        else:
            ds = []
            noi_dung_dict = {}
            model_price_map = {}

        new_ds = []
        com = 0
        pro = 0

        for item in ds:
            if user == item[7]:
                noi_dung = noi_dung_dict.get(str(item[0]), '')
                nd = [ele.split('|') for ele in noi_dung.split('@') if ele]
                ban_c2 = 0
                for e in nd:
                    model = e[1]
                    soluong = int(e[4])
                    gia_c2 = int(model_price_map.get(model, 0))
                    ban_c2 += gia_c2 * soluong

                item.append(ban_c2)
                profit = int(item[5]) - (int(item[2]) - int(item[12]))
                item.append(profit)
                com += int(item[2]) - int(item[12])
                pro += profit
                new_ds.append(item)

        ds = new_ds

        self.uic13.clb_bonus.setText('Commission: ' + "{:,}".format(com) + 'đ')
        self.uic13.clb_profit.setText('Profit: ' + "{:,}".format(pro) + 'đ')

        self.uic13.tableWidget_2.setRowCount(len(ds))
        self.uic13.tableWidget_2.setColumnCount(7)
        self.uic13.tableWidget_2.setHorizontalHeaderLabels(
            ['Số BG', 'Ngày tháng', 'Doanh số', 'Nợ chưa thu', 'Giá đại lý C2', 'Commission', 'Profit']
        )
        for row in range(len(ds)):
            values = [
                str(ds[row][0]),
                ds[row][6].strftime("%d/%m/%Y"),
                "{:,}".format(int(ds[row][2])),
                "{:,}".format(int(ds[row][11])),
                "{:,}".format(int(ds[row][12])),
                "{:,}".format(int(ds[row][2]) - int(ds[row][12])),
                "{:,}".format(int(ds[row][13])),
            ]
            for col, value in enumerate(values):
                self.uic13.tableWidget_2.setItem(row, col, QTableWidgetItem(value))

    def bonus(self, user):
        self.uic13.tableWidget_2.clear()
        # Tính thưởng theo doanh số hàng thực xuất khỏi kho
        # Chưa trừ đi hàng trả lại, sẽ trừ sau
        # ds_kd = ['Lê Văn Việt', 'Nguyễn Hải Hà', 'Phí Ngọc Tùng', 'Dương Lê Hiệp']
        ds_ctv = ['Nguyễn Xuân Thủy', 'Mai Anh Đức', 'Nguyễn T M Huệ', 'Nguyễn Thanh Vương']

        fromdate = self.uic13.date_from.date().toString("yyyy-MM-dd")
        todate = self.uic13.date_to.date().toString("yyyy-MM-dd")

        code1 = ("SELECT so_bg FROM xuat_kho WHERE ngay_thang BETWEEN %s AND %s")
        kq1 = [ele[0] for ele in misc.sql_all(code1, (fromdate, todate,))]

        if kq1:
            placeholders = ','.join(['%s'] * len(kq1))
            query = (
                f"SELECT so_bg, lead_id, tien_hang, vat, da_thanh_toan, profit, ngay_hen_giao_hang, nguoi_tao, nguoi_tao_lead, nguoi_tu_van, nguoi_cai_dat, phai_thu "
                f"FROM ds_don_hang WHERE so_bg IN ({placeholders})")
            kq = [list(row) for row in misc.sql_all(query, tuple(kq1))]
        else:
            kq = []

        ds = []
        for item in kq:
            bonus = 0
            if user in [item[7], item[8], item[9], item[10]] and item[8] not in ds_ctv:

                if user == item[8]:  # Nếu là người tạo lead thì bonus = 2% doanh số
                    bonus = bonus + int(item[2])*0.02
                if user == item[9]:  # Nếu là người tư vấn thì bonus = 1% doanh số
                    bonus = bonus + int(item[2]) * 0.01
                if user == item[10]:  # Nếu là người cài đặt và giao hàng thì bonus = 0.5% doanh số
                    bonus = bonus + int(item[2]) * 0.005
                item.append(bonus)
                ds.append(item)

        bonus = 0
        for item in ds:
            bonus += item[12]
        self.uic13.clb_bonus.setText('Bonus: ' + "{:,}".format(round(bonus), 0) + 'đ')

        self.uic13.tableWidget_2.setRowCount(len(ds))  # tạo số row
        self.uic13.tableWidget_2.setColumnCount(7)  # tạo số column
        self.uic13.tableWidget_2.setColumnWidth(0, 80)
        self.uic13.tableWidget_2.setColumnWidth(1, 80)
        self.uic13.tableWidget_2.setColumnWidth(2, 120)
        self.uic13.tableWidget_2.setColumnWidth(3, 120)
        self.uic13.tableWidget_2.setColumnWidth(4, 120)
        self.uic13.tableWidget_2.setColumnWidth(5, 120)
        self.uic13.tableWidget_2.setColumnWidth(6, 120)

        header = ['Số BG', 'Ngày tháng', 'Doanh số', '2% tạo lead', '1% báo giá', '0.5% cài đặt', 'Bonus']
        self.uic13.tableWidget_2.setHorizontalHeaderLabels(header)
        for row in range(self.uic13.tableWidget_2.rowCount()):
            doanhso = int(ds[row][2])
            for col in range(7):
                item = QTableWidgetItem()
                if col == 0:
                    item.setText(str(ds[row][0]))
                elif col == 1:
                    item.setText(ds[row][6].strftime("%d/%m/%Y"))
                elif col == 2:
                    item.setText("{:,}".format(round(int(ds[row][2]), 0)))
                elif col == 3:
                    if user == ds[row][8]:
                        item.setText("{:,}".format(round(doanhso*0.02), 0))
                    else:
                        item.setText(str(ds[row][8]))
                elif col == 4:
                    if user == ds[row][9]:
                        item.setText("{:,}".format(round(doanhso * 0.01), 0))
                    else:
                        item.setText(str(ds[row][9]))
                elif col == 5:
                    if user == ds[row][10]:
                        item.setText("{:,}".format(round(doanhso * 0.005), 0))
                    else:
                        item.setText(str(ds[row][10]))
                elif col == 6:
                    item.setText("{:,}".format(round(int(ds[row][12]), 0)))
                self.uic13.tableWidget_2.setItem(row, col, item)
        self.uic13.tableWidget_2.insertRow(len(ds) + 1)
