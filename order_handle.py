import datetime
import re
import json
from PyQt6 import QtCore
from PyQt6.QtCore import QDate, Qt, QUrl
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QComboBox,
    QPushButton,
)

import file_handle
import misc
from stock_handle import StockHandle
from UI.don_hang import Ui_Don_hang
from UI.don_cho_thue import Ui_Don_hang_cho_thue
from ui_theme import apply_ui_v2


class ReturnGoodsDialog(QDialog):
    def __init__(self, so_bg, items, customer_info=None, prev_return_by_model=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Trả lại hàng - Đơn #{so_bg}")
        self.resize(980, 560)
        self.items = items
        self.prev_return_by_model = prev_return_by_model or {}
        self.customer_info = customer_info or {}

        layout = QVBoxLayout(self)

        title = QLabel("Phiếu yêu cầu trả lại hàng")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #111827;")
        layout.addWidget(title)

        customer_name = self.customer_info.get('name', '')
        company_name = self.customer_info.get('company', '')
        phone = self.customer_info.get('sdt', '')

        layout.addWidget(QLabel(f"Tên khách hàng: {customer_name}"))
        layout.addWidget(QLabel(f"Tên công ty: {company_name}"))
        layout.addWidget(QLabel(f"Số điện thoại liên hệ: {phone}"))

        layout.addWidget(QLabel("Chi tiết đơn hàng (readonly) - chỉ nhập cột 'SL trả lại'"))
        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Tên sản phẩm", "Model", "SL đã bán", "Đơn giá", "VAT%", "Đã trả trước", "Còn có thể trả", "SL trả lại"
        ])
        self.table.setRowCount(len(items))

        for r, it in enumerate(items):
            sold = int(it.get("qty", 0))
            model = it.get("model", "")
            prev = int(self.prev_return_by_model.get(model, 0))
            remain = max(0, sold - prev)

            readonly_values = [
                it.get("name", ""),
                model,
                str(sold),
                "{:,}".format(int(it.get("price", 0))),
                str(int(it.get("vat_rate", 0))),
                str(prev),
                str(remain),
            ]
            for c, v in enumerate(readonly_values):
                item = QTableWidgetItem(v)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(r, c, item)

            edit_item = QTableWidgetItem("0")
            edit_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 7, edit_item)

        self.table.setColumnWidth(0, 260)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 90)
        layout.addWidget(self.table)

        layout.addWidget(QLabel("Lý do trả lại hàng (bắt buộc):"))
        self.reason = QTextEdit(self)
        self.reason.setPlaceholderText("Ví dụ: Khách đổi model / hàng lỗi / giao thừa số lượng...")
        layout.addWidget(self.reason)

        vat_row = QHBoxLayout()
        vat_row.addWidget(QLabel("Phương án xử lý hóa đơn VAT:"))
        self.vat_combo = QComboBox(self)
        self.vat_combo.addItems(["Không xử lý hóa đơn", "Cần xuất hóa đơn giảm trừ"])
        vat_row.addWidget(self.vat_combo)
        vat_row.addStretch()
        layout.addLayout(vat_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Hủy", self)
        btn_ok = QPushButton("Xác nhận trả lại hàng", self)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._on_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _on_ok(self):
        if not self.reason.toPlainText().strip():
            QMessageBox.warning(self, "Thiếu dữ liệu", "Vui lòng nhập lý do trả lại hàng.")
            return

        has_qty = False
        for r in range(self.table.rowCount()):
            try:
                remain = int((self.table.item(r, 6).text() or "0").replace(",", ""))
                ret_qty = int((self.table.item(r, 7).text() or "0").replace(",", ""))
            except Exception:
                QMessageBox.warning(self, "Lỗi dữ liệu", f"Số lượng trả lại không hợp lệ tại dòng {r+1}.")
                return

            if ret_qty < 0:
                QMessageBox.warning(self, "Lỗi dữ liệu", f"Số lượng trả lại không được âm (dòng {r+1}).")
                return
            if ret_qty > remain:
                QMessageBox.warning(self, "Vượt giới hạn", f"SL trả lại vượt mức cho phép tại dòng {r+1}.")
                return
            if ret_qty > 0:
                has_qty = True

        if not has_qty:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Cần nhập ít nhất 1 sản phẩm có SL trả lại > 0.")
            return

        self.accept()

    def get_result(self):
        rows = []
        for r in range(self.table.rowCount()):
            ret_qty = int((self.table.item(r, 7).text() or "0").replace(",", ""))
            if ret_qty <= 0:
                continue
            rows.append({
                "name": self.table.item(r, 0).text(),
                "model": self.table.item(r, 1).text(),
                "qty_sold": int((self.table.item(r, 2).text() or "0").replace(",", "")),
                "price": int((self.table.item(r, 3).text() or "0").replace(",", "")),
                "vat_rate": int((self.table.item(r, 4).text() or "0").replace(",", "")),
                "qty_return": ret_qty,
            })

        return {
            "rows": rows,
            "reason": self.reason.toPlainText().strip(),
            "vat_option": self.vat_combo.currentText().strip(),
        }


class ReturnRequestReviewDialog(QDialog):
    def __init__(self, so_bg, payload, title, confirm_text, show_reject=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(980, 560)
        self._decision = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Phiếu yêu cầu trả lại hàng - Đơn #{so_bg}"))

        ci = payload.get("customer_info", {}) or {}
        layout.addWidget(QLabel(f"Tên khách hàng: {ci.get('name', '')}"))
        layout.addWidget(QLabel(f"Tên công ty: {ci.get('company', '')}"))
        layout.addWidget(QLabel(f"Số điện thoại liên hệ: {ci.get('sdt', '')}"))
        layout.addWidget(QLabel(f"Lý do: {payload.get('reason', '')}"))
        layout.addWidget(QLabel(f"Phương án VAT: {payload.get('vat_option', '')}"))

        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Tên sản phẩm", "Model", "SL đã bán", "Đơn giá", "VAT%", "Đã trả trước", "Còn có thể trả", "SL trả lại"
        ])

        snapshot = payload.get("all_items_snapshot", []) or []
        if not snapshot:
            # fallback cho phiếu cũ
            for it in payload.get("rows", []):
                snapshot.append({
                    "name": it.get("name", ""),
                    "model": it.get("model", ""),
                    "qty": int(it.get("qty_sold", it.get("qty_return", 0)) or 0),
                    "price": int(it.get("price", 0) or 0),
                    "vat_rate": int(it.get("vat_rate", 0) or 0),
                    "prev_return": 0,
                    "remain": int(it.get("qty_return", 0) or 0),
                    "qty_return": int(it.get("qty_return", 0) or 0),
                })

        self.table.setRowCount(len(snapshot))
        for r, it in enumerate(snapshot):
            vals = [
                str(it.get("name", "")),
                str(it.get("model", "")),
                str(int(it.get("qty", 0) or 0)),
                "{:,}".format(int(it.get("price", 0) or 0)),
                str(int(it.get("vat_rate", 0) or 0)),
                str(int(it.get("prev_return", 0) or 0)),
                str(int(it.get("remain", 0) or 0)),
                str(int(it.get("qty_return", 0) or 0)),
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(r, c, item)

        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 90)
        layout.addWidget(self.table)

        tien_hang = int(payload.get('tien_hang_tra', 0) or 0)
        vat_option = str(payload.get('vat_option', '') or '')
        tien_vat_tra = int(payload.get('tien_vat_tra', 0) or 0)
        if 'tien_vat_ap_dung' in payload:
            tien_vat = int(payload.get('tien_vat_ap_dung', 0) or 0)
        else:
            tien_vat = tien_vat_tra if vat_option == 'Cần xuất hóa đơn giảm trừ' else 0
        tong = int(payload.get('so_tien_tra', tien_hang + tien_vat) or 0)
        # Chuẩn hóa hiển thị theo logic VAT hiện hành
        tong = tien_hang + tien_vat
        layout.addWidget(QLabel(f"Tiền hàng giảm trừ dự kiến: {tien_hang:,} VND"))
        layout.addWidget(QLabel(f"VAT giảm trừ dự kiến: {tien_vat:,} VND"))
        layout.addWidget(QLabel(f"Tổng giảm trừ dự kiến: {tong:,} VND"))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Đóng", self)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        if show_reject:
            btn_reject = QPushButton("Từ chối", self)
            btn_reject.clicked.connect(self._on_reject)
            btn_row.addWidget(btn_reject)

        btn_confirm = QPushButton(confirm_text, self)
        btn_confirm.clicked.connect(self._on_approve)
        btn_row.addWidget(btn_confirm)
        layout.addLayout(btn_row)

    def _on_approve(self):
        self._decision = "APPROVED"
        self.accept()

    def _on_reject(self):
        self._decision = "REJECTED"
        self.accept()

    def decision(self):
        return self._decision


class OrderHandle(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.win_order = QMainWindow()
        self.uic6 = Ui_Don_hang()
        self.uic6.setupUi(self.win_order)
        apply_ui_v2(self.win_order)
        self.win_order.show()
        self.setWindowTitle(QApplication.translate("Thong tin don hang", "Fsale v2.1.1"))
        self.user_power = None
        self.user = None

    def combo_ky_tt_changed(self, tien_hang):
        value = self.uic13.combo_ky_tt.currentText()
        today = QtCore.QDate.currentDate()
        if value == "T.toán 3 tháng":
            self.uic13.text_tienhang.setText("{:,}".format(tien_hang*3))
            self.uic13.date_thanhtoan.setDate(today.addMonths(3))

            vat = round(tien_hang*0.08)
            if self.uic13.check_congty.isChecked():
                self.uic13.label_VAT1.setText("{:,}".format(round(vat)))
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 3 + tien_hang * 6 + vat)))
            else:
                self.uic13.label_VAT1.setText('0')
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 3 + tien_hang * 6)))

        elif value == "T.toán 6 tháng":
            self.uic13.text_tienhang.setText("{:,}".format(tien_hang*6))
            self.uic13.date_thanhtoan.setDate(today.addMonths(6))
            vat = round(tien_hang * 0.08)
            if self.uic13.check_congty.isChecked():
                self.uic13.label_VAT1.setText("{:,}".format(round(vat)))
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 6 + tien_hang * 6 + vat)))
            else:
                self.uic13.label_VAT1.setText('0')
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 6 + tien_hang * 6)))

        elif value == "T.toán 9 tháng":
            self.uic13.text_tienhang.setText("{:,}".format(tien_hang*9))
            self.uic13.date_thanhtoan.setDate(today.addMonths(9))
            vat = round(tien_hang * 0.08)
            if self.uic13.check_congty.isChecked():
                self.uic13.label_VAT1.setText("{:,}".format(round(vat)))
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 9 + tien_hang * 6 + vat)))
            else:
                self.uic13.label_VAT1.setText('0')
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 9 + tien_hang * 6)))

        else:
            self.uic13.text_tienhang.setText("{:,}".format(tien_hang*12))
            self.uic13.date_thanhtoan.setDate(today.addMonths(12))
            vat = round(tien_hang * 0.08)
            if self.uic13.check_congty.isChecked():
                self.uic13.label_VAT1.setText("{:,}".format(round(vat)))
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 12 + tien_hang * 6 + vat)))
            else:
                self.uic13.label_VAT1.setText('0')
                self.uic13.text_tongcong.setText("{:,}".format(round(tien_hang * 12 + tien_hang * 6)))

        tong_cong = int(self.uic13.text_tongcong.toPlainText().replace(",", ""))
        da_thanh_toan = int(self.uic13.text_da_thanhtoan.toPlainText().replace(",", ""))

        phai_thu = tong_cong - da_thanh_toan
        self.uic13.text_phaithu.setText("{:,}".format(round(phai_thu)))

    def tao_don_cho_thue(self,so_bg, user, user_power, ttkh, uick):
        self.win_cho_thue = QMainWindow()
        self.uic13 = Ui_Don_hang_cho_thue()
        self.uic13.setupUi(self.win_cho_thue)
        apply_ui_v2(self.win_cho_thue)
        # Vô hiệu hóa checkbox công ty / cá nhân (LUÔN TÍNH VAT)
        self.uic13.check_congty.setChecked(True)
        self.uic13.check_congty.setDisabled(True)
        self.uic13.check_canhan.setDisabled(True)

        self.win_cho_thue.show()

        self.uic13.label_username.setText(self.user)
        self.uic13.but_xuatkho.setEnabled(False)
        self.uic13.check_giaohang.setCheckable(False)
        self.uic13.check_hoanthanh.setCheckable(False)

        if len(ttkh[5]) < 9:
            self.uic13.check_congty.setDisabled(True)
            self.uic13.check_canhan.setCheckState(Qt.CheckState.Checked)
            self.uic13.check_canhan.setDisabled(True)

        # Set the QDateEdit to today's date
        today = QtCore.QDate.currentDate()
        self.uic13.date_giaohang.setDate(today)
        self.uic13.date_thanhtoan.setDate(today.addMonths(3))

        # Điền thông tin khách hàng
        self.uic13.text_ghichu.setText(ttkh[4])
        self.uic13.label_tencongty.setText(ttkh[0])
        self.uic13.label_nguoidaidien.setText('Người liên hệ: ' + ttkh[1])
        self.uic13.label_sdt.setText('Điện thoại: ' + ttkh[2])
        self.uic13.label_so_donhang.setText('Đơn hàng số: ' + str(so_bg))
        self.uic13.label_mst.setText('Mã số thuế: ' + ttkh[5])
        kq = [ele for ele in misc.sql_one("SELECT address FROM sale_lead WHERE lead_id = %s", (ttkh[3],))]
        if kq[0] is None:
            kq[0] = ''
        self.uic13.label_diachi.setText('Địa chỉ: ' + kq[0])

        # Lấy thông tin về hàng hóa
        kq = misc.sql_one("SELECT * FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))
        hanghoa = [item.split('|') for item in kq[3].split('@')]
        try:
            sum8 = sum(int(item[4]) * int(item[5]) for item in hanghoa if int(item[6]) == 8)
        except Exception as e:
            sum8 = 0
            print(e)
        try:
            sum10 = sum(int(item[4]) * int(item[5]) for item in hanghoa if int(item[6]) == 10)
        except Exception as e:
            sum10 = 0
            print(e)

        # Tính giá trị tiền hàng theo giá thuê
        tien_hang = round(sum8 + sum10)
        self.uic13.text_tienhang.setText("{:,}".format(tien_hang*3))
        if tien_hang <= 0:
            self.uic13.text_ghichu.setText('Đơn hàng có giá trị 0 đồng, không thể tạo đơn.')
            self.uic13.text_ghichu.repaint()
            return

        # Tiền cọc bằng 6 tháng tiền thuê
        self.uic13.text_tien_datcoc.setText("{:,}".format(round(tien_hang*6)))

        # Điền VAT và cộng tổng giá trị đơn hàng, đồng thời điền vào số tiền phải thu
        vat = round(sum8 * 0.08 + sum10 * 0.1)

        self.uic13.label_VAT1.setText("{:,}".format(round(vat)))
        tong = round(tien_hang * 3 + tien_hang * 6 + vat)

        self.uic13.text_tongcong.setText("{:,}".format(tong))
        self.uic13.text_phaithu.setText("{:,}".format(tong))

        self.uic13.text_da_thanhtoan.textChanged.connect(
            lambda: OrderHandle.tinhtien(self, self.uic13))
        self.uic13.but_save_data.clicked.connect(lambda: OrderHandle.save_don_cho_thue(self, so_bg))
        self.uic13.but_xuatkho.clicked.connect(lambda: StockHandle.xuat_kho_thue(self, so_bg))

        # Connect both checkboxes to the same handler
        self.uic13.check_congty.stateChanged.connect(lambda: OrderHandle.handle_checkbox_change(self, self.uic13))
        self.uic13.check_canhan.stateChanged.connect(lambda: OrderHandle.handle_checkbox_change(self, self.uic13))

        self.uic13.combo_ky_tt.addItems(["T.toán 3 tháng", "T.toán 6 tháng", "T.toán 9 tháng", "T.toán theo năm"])
        self.uic13.combo_ky_tt.currentTextChanged.connect(lambda: OrderHandle.combo_ky_tt_changed(self, tien_hang))

        kq = misc.sql_one("SELECT * from ds_don_thue WHERE so_bg = %s", (so_bg,))

        if kq:
            print('đơn hàng cũ')
            # Nếu là đơn hàng cũ thì ghi lại các thông số: công ty/cá nhân, số tiền đã thanh toán trước, kỳ thanh toán
            kq = misc.sql_one("SELECT tk_cong_ty, da_thanh_toan, ky_han_thue FROM ds_don_thue WHERE so_bg = %s", (so_bg,))
            if kq[0] == 'T':
                self.uic13.check_congty.setChecked(True)
            if kq[1] != '0':
                self.uic13.text_da_thanhtoan.setText("{:,}".format(int(kq[1])))
            self.uic13.combo_ky_tt.setCurrentText(kq[2])

    def save_don_cho_thue(self, so_bg):
        lead_id = misc.sql_one("SELECT lead_id FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))[0]
        tien_thue_dinh_ky = self.uic13.text_tienhang.toPlainText().replace(',', '')
        vat = self.uic13.label_VAT1.text().replace(',', '')
        gia_tri_goc = OrderHandle.tinh_tien_coc_thue(self, so_bg)
        tien_dat_coc = self.uic13.text_tien_datcoc.toPlainText().replace(',', '')
        try:
            da_thanh_toan = int(self.uic13.text_da_thanhtoan.toPlainText().replace(',', ''))
        except:
            da_thanh_toan = 0

        ngay_ban_giao = '-'.join(map(str, self.uic13.date_giaohang.date().getDate()))
        next_payment_date = '-'.join(map(str, self.uic13.date_thanhtoan.date().getDate()))

        ky_han_thue = self.uic13.combo_ky_tt.currentText()
        tkcn = 'F'
        tkct = 'T'
        if self.uic13.check_canhan.isChecked():
            tkcn = 'T'
            tkct = 'F'

        nguoi_tao_lead = misc.sql_one("SELECT nguoi_tao_lead FROM sale_lead WHERE lead_id = %s", (lead_id,))[0]
        nguoi_tu_van = misc.sql_one("SELECT user FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))[0]

        if misc.sql_one("SELECT so_bg FROM ds_don_thue WHERE so_bg = %s", (so_bg,)) is None:
            misc.sql_commit("INSERT INTO ds_don_thue SET so_bg = %s, lead_id = %s, tien_thue_dinh_ky = %s, vat = %s, gia_tri_goc = %s, tien_dat_coc = %s, da_thanh_toan = %s, ngay_ban_giao = %s, next_payment_date = %s, ky_han_thue = %s, tk_ca_nhan = %s, tk_cong_ty = %s, nguoi_tao_don = %s, nguoi_tao_lead = %s, nguoi_tu_van = %s",
                            (so_bg, lead_id, tien_thue_dinh_ky, vat, gia_tri_goc, tien_dat_coc, da_thanh_toan, ngay_ban_giao, next_payment_date, ky_han_thue, tkcn, tkct, self.user, nguoi_tao_lead, nguoi_tu_van,))
            self.uic13.label_noti.setStyleSheet("color: blue")
            self.uic13.label_noti.setText('Đã ghi đơn hàng vào danh sách.')
        else:
            misc.sql_commit("UPDATE ds_don_thue SET tien_thue_dinh_ky = %s, vat = %s, gia_tri_goc = %s, tien_dat_coc = %s, da_thanh_toan = %s, ngay_ban_giao = %s, next_payment_date = %s, ky_han_thue = %s, tk_ca_nhan = %s, tk_cong_ty = %s, nguoi_tao_don = %s, nguoi_tu_van = %s WHERE so_bg = %s",
                            (tien_thue_dinh_ky, vat, gia_tri_goc, tien_dat_coc, da_thanh_toan, ngay_ban_giao, next_payment_date, ky_han_thue, tkcn, tkct, self.user, nguoi_tu_van, so_bg,))
            self.uic13.label_noti.setStyleSheet("color: blue")
            self.uic13.label_noti.setText('Đã update thông tin đơn hàng.')

        self.uic13.but_xuatkho.setEnabled(True)

    def tinh_tien_coc_thue(self, so_bg):
        kq = misc.sql_one("SELECT noi_dung FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))[0].split('@')
        tongtien = 0

        for ele in kq:
            item = ele.split('|')
            dongia = misc.sql_one("SELECT gia_ban_le FROM gia_tong_hop WHERE model = %s", (item[1],))[0]
            tien = int(item[4])*int(dongia)/100*30
            tongtien = tongtien + tien

        return tongtien

    def tao_don_hang(self, so_bg, lead_id, uick):
        nc = 0
        ttkh = misc.sql_one("SELECT company, name, sdt, mst, address, yc FROM sale_lead WHERE lead_id = %s", (lead_id,))

        if uick.comboBox.currentText() in ['Giá thuê theo ngày', 'Giá thuê theo tháng', 'Giá thuê theo năm']:
            OrderHandle.tao_don_cho_thue(self, so_bg, ttkh, uick)
        else:
            try:
                self.sub_win1.close()
            except:
                pass

            self.win_order = QMainWindow()
            self.uic6 = Ui_Don_hang()
            self.uic6.setupUi(self.win_order)
            apply_ui_v2(self.win_order)
            # Vô hiệu hóa checkbox công ty / cá nhân (LUÔN TÍNH VAT)
            self.uic6.check_congty.setChecked(True)
            self.uic6.check_congty.setDisabled(True)
            self.uic6.check_canhan.setDisabled(True)

            self.win_order.show()
            self.setWindowTitle(QApplication.translate("Thong tin don hang", "Fsale v2.1.1"))

            self.uic6.label_username.setText(self.user)

            self.uic6.but_xuatkho.setEnabled(False)
            self.uic6.check_giaohang.setCheckable(False)
            self.uic6.check_hoanthanh.setCheckable(False)

            if len(ttkh[5]) < 9:
                self.uic6.check_congty.setDisabled(True)
                self.uic6.check_canhan.setCheckState(Qt.CheckState.Checked)

            # try:
            # Ghi thông tin khách hàng

            self.uic6.label_tencongty.setText(ttkh[0])
            self.uic6.label_nguoidaidien.setText('Người liên hệ: ' + ttkh[1])
            self.uic6.label_sdt.setText('Điện thoại: ' + ttkh[2])
            self.uic6.label_mst.setText('Mã số thuế: ' + ttkh[3])
            self.uic6.label_diachi.setText('Địa chỉ: ' + ttkh[4])
            self.uic6.label_mo_ta_lead.setText(ttkh[5])
            self.uic6.label_so_donhang.setText('Đơn hàng số: ' + str(so_bg))

            # Ghi ngày giao hàng dự kiến - chính là hôm nay
            today = QtCore.QDate.currentDate()
            self.uic6.date_giaohang.setDate(today)
            self.uic6.date_thanhtoan.setDate(today)

            # Nếu là đơn hàng mới
            # Lấy giá trị hàng hóa và giá trị tiền nhân công
            kq = misc.sql_one("SELECT * FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))
            hanghoa = [item.split('|') for item in kq[3].split('@')]
            try:
                sum8 = sum(int(item[4]) * int(item[5]) for item in hanghoa if int(item[6]) == 8 and item[1] != 'NhanCong')
            except Exception as e:
                sum8 = 0
                print(e)
            try:
                sum10 = sum(int(item[4]) * int(item[5]) for item in hanghoa if int(item[6]) == 10 and item[1] != 'NhanCong')
            except Exception as e:
                sum10 = 0
                print(e)

            for item in hanghoa:
                if item[1] == 'NhanCong':
                    nc = sum(int(item[4]) * int(item[5]) for item in hanghoa if item[1] == 'NhanCong')

            self.uic6.text_nc.setText("{:,}".format(nc))

            tien_hang = round(sum8 + sum10)
            if tien_hang <= 0:
                self.uic6.text_ghichu.setText('Đơn hàng có giá trị 0 đồng, không thể tạo đơn.')
                self.uic6.text_ghichu.repaint()
                return

            self.uic6.text_tienhang.setText("{:,}".format(round(sum8 + sum10)))

            vat = round(sum8 * 0.08 + sum10 * 0.1)

            self.uic6.label_VAT1.setText("{:,}".format(round(vat)))
            self.uic6.text_tongcong.setText("{:,}".format(round(tien_hang + vat + nc)))

            self.uic6.text_phaithu.setText("{:,}".format(int(self.uic6.text_tongcong.toPlainText().strip().replace(",", ""))))

            self.uic6.text_da_thanhtoan.textChanged.connect(lambda: OrderHandle.tinhtien(self, self.uic6))
            self.uic6.but_save_data.clicked.connect(lambda: OrderHandle.save_data(self, str(lead_id), str(so_bg)))
            self.uic6.but_xuatkho.clicked.connect(lambda: OrderHandle.xuat_kho(self, lead_id, so_bg))
            if hasattr(self.uic6, 'but_tra_lai_hang'):
                self.uic6.but_tra_lai_hang.clicked.connect(lambda: OrderHandle.tra_lai_hang(self, int(lead_id), int(so_bg)))

            # Phần xử lý file
            self.uic6.but_upload.clicked.connect(lambda: file_handle.handle_upload(lead_id, self.uic6))
            self.uic6.txt_file.anchorClicked.connect(
                lambda url: file_handle.handle_download_or_delete(url, lead_id, self.uic6))

            self.uic6.txt_file.setOpenLinks(False)  # 🚫 Prevent navigation

            # Connect both checkboxes to the same handler
            self.uic6.check_congty.stateChanged.connect(lambda: OrderHandle.handle_checkbox_change(self, self.uic6))
            self.uic6.check_canhan.stateChanged.connect(lambda: OrderHandle.handle_checkbox_change(self, self.uic6))

            kq = misc.sql_one("SELECT da_thanh_toan, tk_cong_ty, da_hoan_thanh from ds_don_hang WHERE so_bg = %s", (so_bg,))
            if kq:
                if kq[0] != '0':
                    self.uic6.text_da_thanhtoan.setText(str(kq[0]))

                if kq[1] == 'T':
                    self.uic6.check_congty.setChecked(True)

                if kq[2] == 'T':
                    self.uic6.label_mo_ta_lead.setStyleSheet('color: red')
                    self.uic6.label_mo_ta_lead.setText("Đơn hàng này không sửa được nữa vì đã xuất hàng.")
                    self.uic6.but_save_data.hide()
                    self.uic6.check_hoanthanh.setChecked(True)

            # Hiển thị file đã upload
            old_files = misc.sql_one("SELECT file FROM sale_lead WHERE lead_id = %s", (lead_id,))
            if old_files and old_files[0]:
                ds_file = old_files[0].split('@@')

                for f in ds_file:
                    name, fid, *_ = f.split('|')
                    self.uic6.txt_file.append(
                        f'<a href="{fid}">📎 {name}</a> &nbsp; ----------- &nbsp; '
                        f'<a href="delete:{fid}">🗑️ Xóa file</a><br>'
                    )

    def upload_file(self, lead_id, uic):
        uic.txt_file.append('<span style="color:green;">⏳ Đang tải file lên Google Drive...</span>')

        uploaded = file_handle.upload_file()
        if not uploaded:
            return

        file = str(lead_id) + '|' + uploaded

        old_files = misc.sql_one("SELECT file FROM sale_lead WHERE lead_id = %s", (lead_id,))
        if old_files and old_files[0]:
            file = old_files[0] + '@@' + uploaded
            misc.sql_commit("UPDATE sale_lead SET file = %s WHERE lead_id = %s", (file, lead_id))
            ds_file = file.split('@@')
        else:
            misc.sql_commit("UPDATE sale_lead SET file = %s WHERE lead_id = %s", (file, lead_id))
            ds_file = [uploaded]

        uic.txt_file.clear()
        for f in ds_file:
            name, fid, *_ = f.split('|')
            uic.txt_file.append(
                f'<a href="{fid}">📎 {name}</a> &nbsp; ----------- &nbsp; '
                f'<a href="delete:{fid}">🗑️ Xóa file</a><br>'
            )

    def refresh_file_list(self, lead_id, uic):
        uic.txt_file.clear()

        result = misc.sql_one("SELECT file FROM sale_lead WHERE lead_id = %s", (lead_id,))
        if result and result[0]:
            ds_file = result[0].split('@@')
            for f in ds_file:
                try:
                    name, fid, *_ = f.split('|')
                    uic.txt_file.append(
                        f'<a href="{fid}">📎 {name}</a> &nbsp; ----------- &nbsp; '
                        f'<a href="delete:{fid}">🗑️ Xóa file</a><br>'
                    )
                except Exception as e:
                    print(f"Lỗi khi xử lý file: {f} – {e}")

    def handle_file_download(self, url: QUrl, lead_id, uic):
        url_str = url.toString()

        # 🔥 Handle delete link
        if url_str.startswith("delete:"):
            file_id = url_str.replace("delete:", "")
            # lead_id = self.uic4.label_lead_id.text() if hasattr(self, "uic4") else self.uic3.label_lead_id.text()
            # uic = self.uic4 if hasattr(self, "uic4") else self.uic3

            confirm = QMessageBox.question(
                uic.txt_file,
                "Xác nhận xóa",
                "Bạn có chắc muốn xóa file này khỏi Google Drive?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                file_handle.delete_file_from_drive(file_id)
                file_handle.remove_file_from_sale_lead(lead_id, file_id)
                OrderHandle.refresh_file_list(self, lead_id, uic)

            return

        # 📥 Handle normal download
        file_id = url_str

        html = uic.txt_file.toHtml()


        pattern = rf'<a href="{re.escape(file_id)}".*?>(?:<span.*?>)?(.*?)(?:</span>)?</a>'
        match = re.search(pattern, html)
        file_name = match.group(1) if match else "downloaded_file"

        print(f"📥 Đang tải file với ID: {file_id}, Tên file: {file_name}")
        file_handle.download_file(file_id, suggested_filename=file_name)

    def tinhtien(self, uic):
        tongcong = int(uic.text_tongcong.toPlainText().strip().replace(',', ''))
        # Lấy số tiền tổng giá trị đơn hàng --> trừ đi số tiền đã đặt cọc  --> ra số tiền phải thu --> điền vào ô phải thu
        if uic.text_da_thanhtoan.toPlainText().strip().replace(',', '').isdigit():
            if uic.text_da_thanhtoan.toPlainText().strip().replace(',', '') == '':
                coc = 0
            else:
                coc = int(uic.text_da_thanhtoan.toPlainText().strip().replace(',', ''))

            uic.text_phaithu.setText("{:,}".format(round(tongcong-coc)))
            uic.text_phaithu.repaint()

        else:
            uic.text_phaithu.setText("{:,}".format(round(tongcong)))
            uic.text_phaithu.repaint()

    def save_data(self, lead_id, so_bg):
        tien_hang = int(self.uic6.text_tienhang.toPlainText().replace(",", ""))
        vat = int(self.uic6.label_VAT1.text().replace(",", ""))
        try:
            temp = "{:,.0f}".format(int(self.uic6.text_da_thanhtoan.toPlainText().strip().replace(",", "")))
            self.uic6.text_da_thanhtoan.setText(str(temp))
            pass
        except Exception as e:
            print(e)
            self.uic6.text_da_thanhtoan.setText('0')

        if self.uic6.text_da_thanhtoan.toPlainText().strip() == '':
            self.uic6.text_da_thanhtoan.setText('0')
            self.uic6.text_da_thanhtoan.setFocus(True)
        da_thanh_toan = round(int(self.uic6.text_da_thanhtoan.toPlainText().strip().replace(',', '')))

        phai_thu = round(tien_hang + vat - da_thanh_toan)

        self.uic6.date_giaohang = QDate.currentDate()  # Replace with your actual QDateEdit widget
        self.uic6.date_thanhtoan = QDate.currentDate()  # Replace with your actual QDateEdit widget

        # Convert QDate to string in 'dd-MM-yyyy' format
        ngay_hen_giao_hang_str = self.uic6.date_giaohang.toString("dd-MM-yyyy")
        ngay_hen_thanh_toan_str = self.uic6.date_thanhtoan.toString("dd-MM-yyyy")
        # Convert the date strings to datetime objects
        ngay_hen_giao_hang = datetime.datetime.strptime(ngay_hen_giao_hang_str, '%d-%m-%Y')
        ngay_hen_thanh_toan = datetime.datetime.strptime(ngay_hen_thanh_toan_str, '%d-%m-%Y')

        ghi_chu = self.uic6.text_ghichu.toPlainText().strip()

        if self.uic6.check_canhan.isChecked():
            tk_canhan = 'T'
        else:
            tk_canhan = 'F'

        if self.uic6.check_congty.isChecked():
            tk_congty = 'T'
        else:
            tk_congty = 'F'

        querry = "SELECT nguoi_tao_lead FROM sale_lead WHERE lead_id = %s"
        nguoi_tao_lead = misc.sql_one(querry, (lead_id,))[0]

        querry = "SELECT user FROM ds_bao_gia WHERE so_bg = %s"
        nguoi_tu_van = misc.sql_one(querry, (so_bg,))[0]

        kq = misc.sql_one("Select * from ds_don_hang where so_bg = %s", (so_bg,))

        lich_su_gd = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '|' + self.user + '|' + str(da_thanh_toan)

        if kq:
            code = ("UPDATE ds_don_hang SET lead_id = %s, tien_hang = %s, vat = %s, da_thanh_toan = %s,"
                    " ngay_hen_giao_hang = %s, ngay_hen_thanh_toan = %s, tk_ca_nhan = %s, tk_cong_ty = %s, "
                    "ghi_chu = %s, da_giao_hang = 'F', da_hoan_thanh = 'F', tien_do = ' ', nguoi_tao = %s, "
                    "nguoi_tao_lead = %s, nguoi_tu_van = %s, lich_su_gd = %s, phai_thu = %s WHERE so_bg = %s")
            param = (lead_id, tien_hang, vat, da_thanh_toan, ngay_hen_giao_hang.date(), ngay_hen_thanh_toan.date(), tk_canhan, tk_congty, ghi_chu, self.user,
                     nguoi_tao_lead, nguoi_tu_van, lich_su_gd, phai_thu, so_bg,)
            misc.sql_commit(code, param)

        else:
            # thiếu người cài đặt
            code = "INSERT INTO ds_don_hang VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
            param = (so_bg, lead_id, tien_hang, vat, da_thanh_toan, 0, ngay_hen_giao_hang.date(), ngay_hen_thanh_toan.date(),
                     tk_canhan, tk_congty, ghi_chu, 'F', 'F', ' ', self.user, nguoi_tao_lead, nguoi_tu_van, '', phai_thu, lich_su_gd,)

            misc.sql_commit(code, param)

        misc.sql_commit("UPDATE ds_bao_gia SET dat_hang = 'T' WHERE so_bg = %s", (so_bg,))

        old_status_row = misc.sql_one("SELECT status FROM sale_lead WHERE lead_id = %s", (lead_id,))
        old_status = old_status_row[0] if old_status_row else ''
        misc.sql_commit("UPDATE sale_lead SET dat_hang = 'T', status = 'Đã đặt hàng' WHERE lead_id = %s", (lead_id,))
        misc.refresh_busy_for_lead(lead_id)
        misc.audit_log(self.user, 'CREATE_ORDER', 'so_bg', '-', so_bg, lead_id)
        misc.audit_log(self.user, 'UPDATE_STATUS', 'status', old_status, 'Đã đặt hàng', lead_id)

        if int(phai_thu) <= 0:
            misc.sql_commit("UPDATE ds_bao_gia SET thanh_toan = 'T' WHERE so_bg = %s", (so_bg,))
            old_paid = misc.sql_one("SELECT status FROM sale_lead WHERE lead_id = %s", (lead_id,))
            old_paid_status = old_paid[0] if old_paid else ''
            misc.sql_commit("UPDATE sale_lead SET status = 'Đã thanh toán' WHERE lead_id = %s", (lead_id,))
            misc.refresh_busy_for_lead(lead_id)
            misc.audit_log(self.user, 'UPDATE_STATUS', 'status', old_paid_status, 'Đã thanh toán', lead_id)

        self.uic6.label_mo_ta_lead.setStyleSheet('color: red')
        self.uic6.label_mo_ta_lead.setText('Đã tạo đơn hàng, tiếp tục tạo phiếu xuất kho?')
        self.uic6.label_mo_ta_lead.repaint()
        self.uic6.but_xuatkho.setEnabled(True)

        misc.send_to_telegram(f"{self.user} đã chốt đơn hàng số {so_bg}, trị giá {'{:,}'.format(tien_hang)} đ, vat = {'{:,}'.format(vat)} đ.")

    def xuat_kho(self, lead_id, so_bg):
        StockHandle.tao_phieu_xuat_tu_don_hang(self, lead_id, so_bg)
        try:
            self.win_order.close()
        except:
            pass

    def _load_quote_items(self, so_bg):
        q = misc.sql_one("SELECT noi_dung FROM ds_bao_gia WHERE so_bg = %s", (so_bg,))
        if not q or not q[0]:
            return []

        items = []
        for raw in str(q[0]).split('@'):
            cols = raw.split('|')
            if len(cols) < 7:
                continue
            try:
                items.append({
                    "name": cols[0],
                    "model": cols[1],
                    "qty": int(cols[4]),
                    "price": int(str(cols[5]).replace(',', '')),
                    "vat_rate": int(cols[6]),
                })
            except Exception:
                continue
        return items

    def _load_prev_return_by_model(self, so_bg):
        px = misc.sql_one("SELECT id FROM xuat_kho WHERE so_bg = %s ORDER BY id DESC LIMIT 1", (so_bg,))
        if not px:
            return {}, None

        so_px = str(px[0])
        rows = misc.sql_all("SELECT noi_dung FROM nhap_kho WHERE ghi_chu LIKE %s", (f"%TRA_LAI_PX:{so_px}%",)) or []

        out = {}
        for r in rows:
            for line in str(r[0] or '').split('@@'):
                c = line.split('|')
                if len(c) < 3:
                    continue
                model = c[1].strip()
                try:
                    qty = int(str(c[2]).replace(',', '').strip() or '0')
                except Exception:
                    qty = 0
                out[model] = out.get(model, 0) + qty

        return out, so_px

    def _append_order_log(self, so_bg, note_text):
        row = misc.sql_one("SELECT ghi_chu, lich_su_gd FROM ds_don_hang WHERE so_bg = %s", (so_bg,))
        if not row:
            return
        ghi_cu = (row[0] or "").strip()
        ls_cu = (row[1] or "").strip()
        ghi_moi = f"{ghi_cu}\n{note_text}".strip()
        ls_moi = f"{ls_cu}@@{note_text}".strip('@')
        misc.sql_commit("UPDATE ds_don_hang SET ghi_chu=%s, lich_su_gd=%s WHERE so_bg=%s", (ghi_moi, ls_moi, so_bg))

    def _get_latest_return_request(self, so_bg, state=None):
        row = misc.sql_one("SELECT lich_su_gd FROM ds_don_hang WHERE so_bg = %s", (so_bg,))
        if not row or not row[0]:
            return None
        lines = str(row[0]).split('@@')
        markers = ["RETURN_REQ_JSON|", "RETURN_REQ_APPROVED|", "RETURN_REQ_REJECTED|", "RETURN_REQ_EXECUTED|"]

        for line in reversed(lines):
            for mk in markers:
                if mk in line:
                    try:
                        payload = json.loads(line.split(mk, 1)[1])
                    except Exception:
                        payload = None
                    if not payload:
                        continue
                    if state and str(payload.get("state", "")).upper() != str(state).upper():
                        continue
                    return payload
        return None

    def _save_return_request(self, so_bg, payload):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload["created_at"] = now
        payload["created_by"] = self.user
        payload["state"] = "PENDING_APPROVAL"
        note = f"[{now}] RETURN_REQ_JSON|{json.dumps(payload, ensure_ascii=False)}"
        OrderHandle._append_order_log(self, so_bg, note)

    def _apply_return_request(self, lead_id, so_bg, row, payload):
        da_thanh_toan = int(row[0] or 0)
        phai_thu = int(row[1] or 0)
        ly_do = payload.get("reason", "")
        vat_option = payload.get("vat_option", "")
        item_log = payload.get("item_log", "")

        tien_hang_tra = int(payload.get("tien_hang_tra", 0) or 0)
        tien_vat_tra = int(payload.get("tien_vat_tra", 0) or 0)
        if "tien_vat_ap_dung" in payload:
            tien_vat_ap_dung = int(payload.get("tien_vat_ap_dung", 0) or 0)
        else:
            tien_vat_ap_dung = tien_vat_tra if vat_option == "Cần xuất hóa đơn giảm trừ" else 0

        so_tien_tra = tien_hang_tra + tien_vat_ap_dung

        tong_gia_tri_hien_tai = max(0, da_thanh_toan + phai_thu)
        phai_thu_moi = phai_thu - so_tien_tra
        tien_hoan = 0
        da_thanh_toan_moi = da_thanh_toan
        is_full_return = so_tien_tra >= tong_gia_tri_hien_tai and tong_gia_tri_hien_tai > 0

        if phai_thu_moi < 0:
            tien_hoan = abs(phai_thu_moi)
            phai_thu_moi = 0
            da_thanh_toan_moi = max(0, da_thanh_toan - tien_hoan)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note = (
            f"[{now}] RETURN_APPLIED | tong={so_tien_tra} | hoan={tien_hoan} | vat_option={vat_option} "
            f"| items={item_log} | ly_do={ly_do} | approved_by={self.user}"
        )
        OrderHandle._append_order_log(self, so_bg, note)

        misc.sql_commit(
            "UPDATE ds_don_hang SET da_thanh_toan=%s, phai_thu=%s WHERE so_bg=%s",
            (da_thanh_toan_moi, phai_thu_moi, so_bg)
        )

        if is_full_return:
            misc.sql_commit("UPDATE ds_bao_gia SET dat_hang = 'F', thanh_toan = 'F' WHERE so_bg = %s", (so_bg,))
            misc.sql_commit("UPDATE ds_don_hang SET da_giao_hang = 'F', da_hoan_thanh = 'T', tien_do = 'TRA_HET' WHERE so_bg = %s", (so_bg,))
            misc.sql_commit("UPDATE sale_lead SET dat_hang = 'F', status = 'Da tra lai toan bo' WHERE lead_id = %s", (lead_id,))
        elif phai_thu_moi <= 0:
            misc.sql_commit("UPDATE ds_bao_gia SET thanh_toan = 'T' WHERE so_bg = %s", (so_bg,))
            misc.sql_commit("UPDATE sale_lead SET status = 'Đã thanh toán' WHERE lead_id = %s", (lead_id,))
        else:
            misc.sql_commit("UPDATE ds_bao_gia SET thanh_toan = 'F' WHERE so_bg = %s", (so_bg,))
            misc.sql_commit("UPDATE sale_lead SET status = 'Đã đặt hàng' WHERE lead_id = %s", (lead_id,))

        misc.refresh_busy_for_lead(lead_id)

        return da_thanh_toan_moi, phai_thu_moi, tien_hoan, is_full_return

    def tra_lai_hang(self, lead_id, so_bg):
        row = misc.sql_one(
            "SELECT da_thanh_toan, phai_thu, ghi_chu, lich_su_gd FROM ds_don_hang WHERE so_bg = %s",
            (so_bg,)
        )
        if not row:
            QMessageBox.warning(self.win_order, "Thiếu dữ liệu", f"Không tìm thấy đơn hàng #{so_bg}.")
            return

        try:
            da_thanh_toan = int(row[0] or 0)
            phai_thu = int(row[1] or 0)
        except Exception:
            QMessageBox.warning(self.win_order, "Lỗi dữ liệu", "Dữ liệu thanh toán của đơn hàng không hợp lệ.")
            return

        user_power = int(getattr(self, 'user_power', 0) or 0)

        # 1) SALES SCREEN: chỉ gửi duyệt
        if user_power <= 40:
            quote_items = OrderHandle._load_quote_items(self, so_bg)
            if not quote_items:
                QMessageBox.warning(self.win_order, "Thiếu dữ liệu", "Không đọc được chi tiết hàng hóa từ báo giá.")
                return

            prev_return_by_model, _so_px = OrderHandle._load_prev_return_by_model(self, so_bg)
            customer = misc.sql_one("SELECT name, company, sdt FROM sale_lead WHERE lead_id = %s", (lead_id,))
            customer_info = {
                "name": customer[0] if customer else "",
                "company": customer[1] if customer else "",
                "sdt": customer[2] if customer else "",
            }

            dlg = ReturnGoodsDialog(
                so_bg=so_bg,
                items=quote_items,
                customer_info=customer_info,
                prev_return_by_model=prev_return_by_model,
                parent=self.win_order,
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return

            result = dlg.get_result()
            rows = result["rows"]
            ly_do = result["reason"]
            vat_option = result["vat_option"]
            tien_hang_tra = sum(int(r["qty_return"]) * int(r["price"]) for r in rows)
            tien_vat_tra = sum(int(r["qty_return"]) * int(r["price"]) * int(r["vat_rate"]) // 100 for r in rows)
            tinh_vat_giam_tru = (vat_option == "Cần xuất hóa đơn giảm trừ")
            tien_vat_ap_dung = tien_vat_tra if tinh_vat_giam_tru else 0
            so_tien_tra = tien_hang_tra + tien_vat_ap_dung
            item_log = '; '.join([f"{x['model']}:{x['qty_return']}" for x in rows])

            return_map = {x['model']: int(x['qty_return']) for x in rows}
            snapshot = []
            for it in quote_items:
                model = it.get("model", "")
                qty = int(it.get("qty", 0) or 0)
                prev = int(prev_return_by_model.get(model, 0) or 0)
                snapshot.append({
                    "name": it.get("name", ""),
                    "model": model,
                    "qty": qty,
                    "price": int(it.get("price", 0) or 0),
                    "vat_rate": int(it.get("vat_rate", 0) or 0),
                    "prev_return": prev,
                    "remain": max(0, qty - prev),
                    "qty_return": int(return_map.get(model, 0) or 0),
                })

            payload = {
                "so_bg": int(so_bg), "lead_id": int(lead_id), "rows": rows,
                "reason": ly_do, "vat_option": vat_option,
                "tien_hang_tra": int(tien_hang_tra),
                "tien_vat_tra": int(tien_vat_tra),
                "tien_vat_ap_dung": int(tien_vat_ap_dung),
                "so_tien_tra": int(so_tien_tra), "item_log": item_log,
                "customer_info": customer_info,
                "all_items_snapshot": snapshot,
            }
            OrderHandle._save_return_request(self, so_bg, payload)
            QMessageBox.information(self.win_order, "Đã gửi duyệt", "Đã gửi Phiếu yêu cầu trả lại hàng cho quản lý duyệt.")
            return

        # 2) MANAGER SCREEN: chỉ duyệt/từ chối
        if user_power > 50:
            pending = OrderHandle._get_latest_return_request(self, so_bg, state="PENDING_APPROVAL")
            if not pending:
                QMessageBox.information(self.win_order, "Không có phiếu chờ duyệt", "Hiện không có Phiếu yêu cầu trả lại hàng ở trạng thái chờ duyệt.")
                return

            if not pending.get("all_items_snapshot"):
                quote_items = OrderHandle._load_quote_items(self, so_bg)
                prev_return_by_model, _ = OrderHandle._load_prev_return_by_model(self, so_bg)
                return_map = {x.get('model', ''): int(x.get('qty_return', 0) or 0) for x in pending.get('rows', [])}
                pending["all_items_snapshot"] = []
                for it in quote_items:
                    model = it.get("model", "")
                    qty = int(it.get("qty", 0) or 0)
                    prev = int(prev_return_by_model.get(model, 0) or 0)
                    pending["all_items_snapshot"].append({
                        "name": it.get("name", ""),
                        "model": model,
                        "qty": qty,
                        "price": int(it.get("price", 0) or 0),
                        "vat_rate": int(it.get("vat_rate", 0) or 0),
                        "prev_return": prev,
                        "remain": max(0, qty - prev),
                        "qty_return": int(return_map.get(model, 0) or 0),
                    })

            if not pending.get("customer_info"):
                customer = misc.sql_one("SELECT name, company, sdt FROM sale_lead WHERE lead_id = %s", (lead_id,))
                pending["customer_info"] = {
                    "name": customer[0] if customer else "",
                    "company": customer[1] if customer else "",
                    "sdt": customer[2] if customer else "",
                }

            dlg = ReturnRequestReviewDialog(
                so_bg=so_bg,
                payload=pending,
                title="Duyệt Phiếu yêu cầu trả lại hàng",
                confirm_text="Duyệt",
                show_reject=True,
                parent=self.win_order,
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return

            decision = dlg.decision()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pending["state"] = "APPROVED" if decision == "APPROVED" else "REJECTED"
            pending["approved_by"] = self.user
            pending["approved_at"] = now
            marker = "RETURN_REQ_APPROVED|" if decision == "APPROVED" else "RETURN_REQ_REJECTED|"
            OrderHandle._append_order_log(self, so_bg, f"[{now}] {marker}{json.dumps(pending, ensure_ascii=False)}")

            if decision == "APPROVED":
                QMessageBox.information(self.win_order, "Đã duyệt", "Phiếu đã được duyệt. Kế toán có thể thực thi bước nhập kho/hoàn tiền/thuế.")
            else:
                QMessageBox.information(self.win_order, "Đã từ chối", "Phiếu yêu cầu trả lại hàng đã bị từ chối.")
            return

        # 3) ACCOUNTING SCREEN: chỉ thực thi sau duyệt (power 41..50)
        executed = OrderHandle._get_latest_return_request(self, so_bg, state="EXECUTED")
        if executed:
            # Cho phép tiếp tục công việc dở dang (ví dụ lỗi ở bước mở/lưu phiếu nhập kho)
            reopen = QMessageBox.question(
                self.win_order,
                "Phiếu đã thực thi",
                "Phiếu này đã thực thi tài chính trước đó.\n"
                "Bạn có muốn tiếp tục bước hậu xử lý (mở lại phiếu nhập kho trả lại) không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reopen == QMessageBox.StandardButton.Yes:
                return_map = {x.get('model', ''): int(x.get('qty_return', 0) or 0) for x in executed.get('rows', [])}
                OrderHandle.mo_phieu_nhap_tra_lai_hang(
                    self,
                    so_bg,
                    executed.get('reason', ''),
                    executed.get('vat_option', ''),
                    return_map,
                )
            return

        approved = OrderHandle._get_latest_return_request(self, so_bg, state="APPROVED")
        if not approved:
            QMessageBox.warning(self.win_order, "Chưa đủ điều kiện", "Chưa có phiếu trả lại hàng đã được duyệt bởi quản lý.")
            return

        if not approved.get("all_items_snapshot"):
            quote_items = OrderHandle._load_quote_items(self, so_bg)
            prev_return_by_model, _ = OrderHandle._load_prev_return_by_model(self, so_bg)
            return_map = {x.get('model', ''): int(x.get('qty_return', 0) or 0) for x in approved.get('rows', [])}
            approved["all_items_snapshot"] = []
            for it in quote_items:
                model = it.get("model", "")
                qty = int(it.get("qty", 0) or 0)
                prev = int(prev_return_by_model.get(model, 0) or 0)
                approved["all_items_snapshot"].append({
                    "name": it.get("name", ""),
                    "model": model,
                    "qty": qty,
                    "price": int(it.get("price", 0) or 0),
                    "vat_rate": int(it.get("vat_rate", 0) or 0),
                    "prev_return": prev,
                    "remain": max(0, qty - prev),
                    "qty_return": int(return_map.get(model, 0) or 0),
                })

        if not approved.get("customer_info"):
            customer = misc.sql_one("SELECT name, company, sdt FROM sale_lead WHERE lead_id = %s", (lead_id,))
            approved["customer_info"] = {
                "name": customer[0] if customer else "",
                "company": customer[1] if customer else "",
                "sdt": customer[2] if customer else "",
            }

        review = ReturnRequestReviewDialog(
            so_bg=so_bg,
            payload=approved,
            title="Thực thi Phiếu trả lại hàng (Kế toán)",
            confirm_text="Thực thi",
            show_reject=False,
            parent=self.win_order,
        )
        if review.exec() != QDialog.DialogCode.Accepted:
            return

        da_thanh_toan_moi, phai_thu_moi, tien_hoan, is_full_return = OrderHandle._apply_return_request(self, lead_id, so_bg, row, approved)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        approved["state"] = "EXECUTED"
        approved["executed_by"] = self.user
        approved["executed_at"] = now
        OrderHandle._append_order_log(self, so_bg, f"[{now}] RETURN_REQ_EXECUTED|{json.dumps(approved, ensure_ascii=False)}")

        if hasattr(self, 'uic6') and hasattr(self.uic6, 'text_da_thanhtoan'):
            self.uic6.text_da_thanhtoan.setText("{:,}".format(da_thanh_toan_moi))
            self.uic6.text_phaithu.setText("{:,}".format(phai_thu_moi))
            self.uic6.label_mo_ta_lead.setStyleSheet('color: #b45309')
            self.uic6.label_mo_ta_lead.setText("Đã thực thi phiếu trả lại hàng.")
            self.uic6.label_mo_ta_lead.repaint()

        QMessageBox.information(
            self.win_order,
            "Đã thực thi",
            f"Kế toán đã thực thi phiếu trả hàng.\nPhải thu mới: {phai_thu_moi:,} VND\nHoàn tiền dự kiến: {tien_hoan:,} VND"
        )

        open_stock_form = QMessageBox.question(
            self.win_order,
            "Nhập kho trả lại",
            "Mở luôn phiếu nhập kho trả lại từ phiếu xuất của đơn này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if open_stock_form == QMessageBox.StandardButton.Yes:
            return_map = {x['model']: int(x['qty_return']) for x in approved.get('rows', [])}
            OrderHandle.mo_phieu_nhap_tra_lai_hang(self, so_bg, approved.get('reason', ''), approved.get('vat_option', ''), return_map)

    def mo_phieu_nhap_tra_lai_hang(self, so_bg, ly_do='', vat_option='', return_map=None):
        return_map = return_map or {}
        try:
            StockHandle.tao_phieu_nhap(self)
        except Exception as e:
            QMessageBox.warning(self.win_order, "Lỗi mở phiếu nhập", f"Không mở được form nhập kho: {e}")
            return

        try:
            # Bật chế độ nhập lại từ phiếu xuất
            self.uic8.checkBox.setChecked(True)

            # Ưu tiên phiếu xuất mới nhất theo số báo giá
            px = misc.sql_one("SELECT id FROM xuat_kho WHERE so_bg = %s ORDER BY id DESC LIMIT 1", (so_bg,))
            if not px:
                QMessageBox.warning(self.win_order, "Thiếu phiếu xuất", f"Không tìm thấy phiếu xuất kho cho đơn #{so_bg}.")
                return

            so_px = str(px[0])
            idx = self.uic8.combo_so_px.findText(so_px)
            if idx >= 0:
                self.uic8.combo_so_px.setCurrentIndex(idx)
            else:
                self.uic8.combo_so_px.addItem(so_px)
                self.uic8.combo_so_px.setCurrentText(so_px)

            # Đánh dấu đây là phiếu nhập do trả lại hàng
            if hasattr(self.uic8, 'check_tra_lai'):
                self.uic8.check_tra_lai.setChecked(True)

            reason_text = f"Trả lại hàng đơn #{so_bg}"
            if ly_do:
                reason_text += f": {ly_do}"
            if vat_option:
                reason_text += f" | VAT: {vat_option}"
            self.uic8.text_nguyen_nhan.setText(reason_text)

            # Điền sẵn số lượng nhập lại theo các dòng đã chọn ở màn hình trả hàng
            for r in range(self.uic8.tableWidget.rowCount()):
                model_item = self.uic8.tableWidget.item(r, 1)
                qty_item = self.uic8.tableWidget.item(r, 4)
                if not model_item or not qty_item:
                    continue
                model = model_item.text().strip()
                qty = int(return_map.get(model, 0) or 0)
                qty_item.setText(str(qty))

            if hasattr(self.uic8, 'label_noti'):
                self.uic8.label_noti.setStyleSheet('color: #0f766e')
                self.uic8.label_noti.setText(f"Đã nạp sẵn dữ liệu trả lại hàng cho đơn #{so_bg}.")
        except Exception as e:
            QMessageBox.warning(self.win_order, "Lỗi chuẩn bị dữ liệu", f"Không thể nạp sẵn phiếu nhập trả lại: {e}")

    def handle_checkbox_change(self, uic):
        # Ensure only one checkbox is selected at a time
        if uic.check_congty.isChecked():
            uic.check_canhan.setCheckState(Qt.CheckState.Unchecked)
            vat_included = True
        else:
            # Default behavior if no checkbox is selected (optional)
            uic.check_canhan.setCheckState(Qt.CheckState.Checked)
            uic.check_congty.setCheckState(Qt.CheckState.Unchecked)
            vat_included = False

        uic.check_congty.repaint()
        uic.check_canhan.repaint()

        OrderHandle.update_labels(self, vat_included, uic)

    def update_labels(self, vat_included, uic):

        tien_hang = int(uic.text_tienhang.toPlainText().strip().replace(",", ""))

        try:
            tien_coc = int(uic.text_tien_datcoc.toPlainText().strip().replace(",", ""))
        except:
            tien_coc = 0

        try:
            nc = int(uic.text_nc.toPlainText().strip().replace(",", ""))
        except:
            nc = 0

        vat = round(tien_hang * 0.08)

        uic.label_VAT1.setText("{:,}".format(round(vat)))
        uic.text_tongcong.setText("{:,}".format(round(tien_hang + vat + nc + tien_coc)))

        OrderHandle.tinhtien(self, uic)


