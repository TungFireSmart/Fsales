import re
from datetime import datetime, timedelta
import pytz
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from PyQt6.QtCore import QUrl
from UI.lead_update import Ui_LeadUpdate

import file_handle
import quotation
import misc
from UI.new_lead import Ui_NewLead


class LeadHandle(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = None
        self.user_phone = None
        self.win_newlead = None
        self.uic3 = None

    def update_job(self, lead_id):
        self.win_update_lead = QMainWindow()
        self.uic4 = Ui_LeadUpdate()
        self.uic4.setupUi(self.win_update_lead)
        self.win_update_lead.show()

        result = misc.sql_one("SELECT * from sale_lead WHERE lead_id = %s", (lead_id,))

        self.uic4.label_username.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.uic4.label_username.setText(self.user)

        status_list = ['Đã nhận việc', 'Đã báo giá', 'Đã giao hàng', 'Done - Thất bại']
        self.uic4.comboBox.addItems(status_list)
        self.uic4.comboBox.setCurrentText(result[10])

        self.uic4.label_lead_id.setText(lead_id)
        self.uic4.txt_ten_cong_ty.setText(result[4])
        self.uic4.txt_ten_khach_hang.setText(result[1])
        self.uic4.txt_so_dt.setText(result[2])
        self.uic4.txt_yeu_cau.setText(result[9])
        self.uic4.txt_dia_chi.setText(result[12])
        self.uic4.txt_mst.setText(result[8])

        # Hiển thị file đã upload
        old_files = result[18]
        if old_files:
            ds_file = old_files.split('@@')

            for f in ds_file:
                name, fid, *_ = f.split('|')
                self.uic4.txt_file.append(
                    f'<a href="{fid}">📎 {name}</a> &nbsp; ----------- &nbsp; '
                    f'<a href="delete:{fid}">🗑️ Xóa file</a><br>'
                )

        self.uic4.but_upload.clicked.connect(lambda: file_handle.handle_upload(lead_id, self.uic4))
        self.uic4.txt_file.anchorClicked.connect(
            lambda url: file_handle.handle_download_or_delete(url, lead_id, self.uic4))

        self.uic4.txt_file.setOpenLinks(False)  # 🚫 Prevent navigation

        self.uic4.but_bo_qua_co_hoi.clicked.connect(lambda: LeadHandle.refuse_lead(self, result[0]))
        self.uic4.but_xoa_lead.clicked.connect(lambda: LeadHandle.delete_lead(self, result[0]))

        self.uic4.but_baogia.clicked.connect(lambda: LeadHandle.show_quotato_from_lead(self, lead_id))

        self.uic4.but_sua_tt.clicked.connect(lambda: LeadHandle.sua_tt_kh(self))

    def sua_tt_kh(self):
        tenkhachhang = self.uic4.txt_ten_khach_hang.toPlainText().strip()
        tencongty = self.uic4.txt_ten_cong_ty.toPlainText().strip()
        sdt = self.uic4.txt_so_dt.toPlainText().strip().replace(".", "")
        mst = self.uic4.txt_mst.toPlainText().strip()
        address = self.uic4.txt_dia_chi.toPlainText().strip()
        leadid = self.uic4.label_lead_id.text()
        yeucau = self.uic4.txt_yeu_cau.toPlainText().strip()

        # Update thông tin trong bảng sale_lead
        update_query = """
            UPDATE sale_lead
            SET company = %s, name = %s, sdt = %s, mst = %s, address = %s, yc = %s
            WHERE lead_id = %s
        """
        misc.sql_commit(update_query, (tencongty, tenkhachhang, sdt, mst, address, yeucau, leadid))

        self.uic4.label_noti.setText('Update thành công thông tin khách hàng!')
        self.uic4.label_noti.repaint()

        # ttkh = [ten_khach, sdt, cong_ty, mst, phu_trach, lead_id, diachi]
        ttkh = [tenkhachhang, sdt, tencongty, mst, self.user, leadid, address]

        LeadHandle.luu_thong_tin_kh(self, ttkh)

    def refuse_lead(self, lead_id):

        kq = misc.sql_one("SELECT status FROM sale_lead WHERE lead_id = %s AND phu_trach = %s ", (lead_id, self.user,))

        if kq:

            misc.sql_commit("UPDATE sale_lead SET phu_trach = 'waiting', status = ' ...', time_nhan_viec = NOW() WHERE lead_id = %s", (lead_id,))
            # misc.sql_commit("UPDATE sale_lead SET status = ' ...' WHERE lead_id = %s", (lead_id,))
            # misc.sql_commit("UPDATE sale_lead SET time_nhan_viec = NOW() WHERE lead_id = '{}'", (lead_id,))

            misc.sql_commit("UPDATE user SET check_busy = 0 WHERE full_name = %s", (self.user,))

            txt = self.user + 'từ chối cơ hội, cơ hội số ' + str(lead_id) + ' được chuyển thành cơ hộ mới.'
            misc.send_to_telegram(txt)

            self.uic4.label_noti.setText('Đã từ bỏ cơ hội này. Hãy tắt cửa sổ hiện tại')
            self.win_update_lead.close()
            self.show_lead(self.user)
        return

    def delete_lead(self, lead_id):

        kq = misc.sql_one("SELECT nguoi_tao_lead, time_create FROM sale_lead WHERE lead_id = %s", (lead_id,))

        if kq:
            timestamp_from_db = kq[1]
            # Chuyển đổi giá trị timestamp từ cơ sở dữ liệu thành đối tượng datetime
            timestamp_from_db = timestamp_from_db.replace(tzinfo=pytz.utc)

            # Lấy thời gian UTC hiện tại từ Python
            current_time_utc = datetime.now(pytz.utc)
            time_difference = current_time_utc - timestamp_from_db

            # So sánh khoảng thời gian với 2 ngày
            if time_difference < timedelta(days=2):

                misc.sql_commit("UPDATE sale_lead SET check_delete = '1' WHERE lead_id = %s", (lead_id,))

                txt = self.user + 'đã xóa cơ hội số ' + str(lead_id) + '.'
                misc.send_to_telegram(txt)
                LeadHandle.check_busy(self)
                self.uic4.label_noti.setText('Đã xóa cơ hội này. Hãy tắt cửa sổ hiện tại')
                self.uic4.but_baogia.setEnabled(False)
                self.uic4.but_bo_qua_co_hoi.setEnabled(False)
                self.uic4.but_donhang.setEnabled(False)
                self.uic4.but_upload.setEnabled(False)
                self.win_update_lead.close()
                self.show_lead(self.user)
            else:
                self.uic4.label_noti.setText('Đã quá thời gian cho phép xóa, không thể xóa cơ hội này')
        return
        # USER chỉ được xóa những lead do chính mình tạo ra trong 2 ngày gần nhất
        # Khi xóa lead bắn thông tin lên telegram và ghi vào table sale_lead trên db

    def check_busy(self):

        kq = misc.sql_all("SELECT lead_id FROM sale_lead WHERE status = 'Đang xử lý' AND phu_trach = %s AND check_delete != '1'",
            (self.user,))

        if not kq:
            misc.sql_commit("UPDATE user SET check_busy = 0 WHERE full_name = %s", (self.user,))

        else:
            misc.sql_commit("UPDATE user SET check_busy = 1 WHERE full_name = %s", (self.user,))

    def create_new_lead(self):
        self.win_newlead = QMainWindow()
        self.uic3 = Ui_NewLead()
        self.uic3.setupUi(self.win_newlead)
        self.setWindowTitle(QApplication.translate("Lead update", "Fsale v3.04.2025"))

        self.win_newlead.show()

        self.uic3.label_username.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.uic3.label_username.setText(self.user)
        self.uic3.but_upload.setEnabled(False)

        # Setcombo tên user để giao việc

        result = misc.sql_all("SELECT * FROM user WHERE power != '0'", None)
        # Get the maximum value of 'lead_id' from the table
        max_id = misc.sql_one("SELECT MAX(lead_id) FROM sale_lead", None)[0]
        lead_id = str(int(max_id) + 1)

        self.uic3.label_noti.setText('Bạn đang tạo cơ hội bán hàng thứ ' + lead_id)

        ds = []
        for item in result:
            ds.append(item[2])
        ds.append(' ...')
        self.uic3.comboBox.addItems(sorted(ds))
        self.uic3.comboBox.setCurrentText(self.user)

        self.uic3.but_tao_lead.clicked.connect(lambda: LeadHandle.tao_lead(self, lead_id))
        self.uic3.txt_mst.textChanged.connect(lambda: LeadHandle.check_tt_kh(self))
        self.uic3.txt_so_dt.textChanged.connect(lambda: LeadHandle.check_tt_kh(self))

        self.uic3.txt_file.anchorClicked.connect(
            lambda url: file_handle.handle_download_or_delete(url, lead_id, self.uic3))
        self.uic3.txt_file.setOpenLinks(False)  # 🚫 Prevent navigation

    def check_tt_kh(self):
        sdt = re.sub(r'\D', '', self.uic3.txt_so_dt.toPlainText())
        mst = re.sub(r'\D', '', self.uic3.txt_mst.toPlainText())

        if sdt != '' and len(sdt.strip()) == 10:
            self.uic3.txt_file.clear()
            kq_sdt = misc.sql_all("SELECT * from ds_ca_nhan WHERE dien_thoai = %s", (sdt,))
            if kq_sdt:
                self.uic3.txt_ten_khach_hang.setText(kq_sdt[0][0])
                kq_lead = misc.sql_all("SELECT * from sale_lead WHERE sdt = %s", (sdt,))

                if kq_lead:
                    self.uic3.txt_file.append('Đã từng có ' + str(len(kq_lead)) + ' cơ hội bán hàng')
                    kq_tc = misc.sql_all("SELECT * from sale_lead WHERE sdt = %s AND dat_hang = 'T'", (sdt,))
                    self.uic3.txt_file.append('và có ' + str(len(kq_tc)) + ' đơn hàng thành công.\n')
                    nlh = ", ".join(set([ele[13] for ele in kq_tc]))
                    self.uic3.txt_file.append('Người đã từng liên hệ: ' + nlh + '.')

                    self.uic3.txt_file.repaint()

        if mst != '':

            kq_mst = misc.sql_all("SELECT * from ds_cong_ty WHERE mst = %s", (mst,))
            if kq_mst:
                self.uic3.txt_ten_cong_ty.setText(str(kq_mst[0][0]))
                # self.uic3.txt_email.setText(kq_mst[0][7])
                if kq_mst[0][2] != '':
                    self.uic3.txt_file.append(f'Công ty {kq_mst[0][0]} đã từng có lịch sử giao dịch.  Hãy nhấn nút phía dưới để xem chi tiết.')
                    self.uic3.txt_file.repaint()
                    self.uic3.but_lich_su.setEnabled(True)

    def tao_lead(self, lead_id):
        ten_lead = self.uic3.txt_ten_lead.toPlainText()
        ten_khach = self.uic3.txt_ten_khach_hang.toPlainText()
        cong_ty = self.uic3.txt_ten_cong_ty.toPlainText() or ' '
        diachi = self.uic3.txt_dia_chi.toPlainText()
        sdt = re.sub(r'\D', '', self.uic3.txt_so_dt.toPlainText())
        mst = self.uic3.txt_mst.toPlainText()
        yeu_cau = self.uic3.txt_yeu_cau.toPlainText().strip()
        phu_trach = self.uic3.comboBox.currentText()

        self.uic3.label_noti.setStyleSheet("color: red")

        if len(sdt) != 10:
            self.uic3.label_noti.setText('📱 Số điện thoại phải gồm đúng 10 chữ số!')
        elif len(ten_khach.split()) < 2:
            self.uic3.label_noti.setText('👤 Vui lòng nhập đầy đủ họ tên người liên hệ!')
        elif len(yeu_cau.split()) < 10:
            self.uic3.label_noti.setText('📝 Nội dung yêu cầu của khách hàng còn quá ngắn!')
        elif len(ten_lead.split()) < 2:
            self.uic3.label_noti.setText('📌 Cần ghi rõ tên cơ hội (ít nhất 2 từ).')
        else:
            sql = (
                "INSERT INTO sale_lead (lead_id, name, sdt, company, mst, yc, status, phu_trach, nguoi_tao_lead, ten_co_hoi, address) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

            status = 'waiting' if phu_trach == ' ...' else 'Đã nhận việc'
            val = (lead_id, ten_khach, sdt, cong_ty, mst, yeu_cau, status, phu_trach, self.user, ten_lead, diachi)
            misc.sql_commit(sql, val)

            # Gửi tin nhắn Telegram
            if phu_trach == ' ...':
                misc.send_to_telegram(f"📥 {self.user} đã tạo mới một cơ hội bán hàng số {lead_id}")
            elif phu_trach == self.user:
                misc.send_to_telegram(f"🧑‍💼 {self.user} đã tạo mới một cơ hội bán hàng số {lead_id} và tự xử lý")
            else:
                misc.send_to_telegram(
                    f"📤 {self.user} đã tạo mới một cơ hội bán hàng số {lead_id} và giao cho {phu_trach} xử lý")

            # Lưu lịch sử và cập nhật giao diện
            lead_id = str(int(misc.sql_one("SELECT MAX(lead_id) FROM sale_lead")[0]) + 1)
            ttkh = [ten_khach, sdt, cong_ty, mst, phu_trach, lead_id, diachi]

            LeadHandle.luu_thong_tin_kh(self, ttkh)

            self.uic3.label_noti.setStyleSheet("color: green")
            self.uic3.label_noti.setText('✅ Đã tạo xong cơ hội bán hàng và ghi lên hệ thống!')

            self.uic3.but_upload.setEnabled(True)
            self.uic3.but_upload.clicked.connect(lambda: LeadHandle.upload_file(self, lead_id, self.uic3))
            self.uic3.but_tao_lead.hide()
            self.uic3.but_sua_lead.clicked.connect(lambda: LeadHandle.sua_lead(self, lead_id))

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
                LeadHandle.refresh_file_list(self, lead_id, uic)

            return

        # 📥 Handle normal download
        file_id = url_str

        html = uic.txt_file.toHtml()


        pattern = rf'<a href="{re.escape(file_id)}".*?>(?:<span.*?>)?(.*?)(?:</span>)?</a>'
        match = re.search(pattern, html)
        file_name = match.group(1) if match else "downloaded_file"

        print(f"📥 Đang tải file với ID: {file_id}, Tên file: {file_name}")
        file_handle.download_file(file_id, suggested_filename=file_name)

    def sua_lead(self, lead_id):
        try:
            ten_lead = self.uic3.txt_ten_lead.toPlainText()
            ten_khach = self.uic3.txt_ten_khach_hang.toPlainText()
            cong_ty = self.uic3.txt_ten_cong_ty.toPlainText()
            diachi = self.uic3.txt_dia_chi.toPlainText()

            if cong_ty == '':
                cong_ty = ' '
            sdt = re.sub(r'\D', '', self.uic3.txt_so_dt.toPlainText())
            mst = self.uic3.txt_mst.toPlainText()
            yeu_cau = self.uic3.txt_yeu_cau.toPlainText().strip()
            phu_trach = self.uic3.comboBox.currentText()

            self.uic3.label_noti.setStyleSheet("color: red")

            # Kiểm tra tính hợp lệ của data nhập vào - SẼ LÀM SAU

            if len(sdt) == 10:
                if len(ten_khach.split()) >= 2:
                    if len(yeu_cau.split()) >= 10:
                        if len(ten_lead.split()) >= 2:
                            # ghi data đã kiểm tra vào table sale_lead
                            sql = ("UPDATE sale_lead SET name = %s, sdt = %s, company = %s, mst = %s, yc = %s, status = %s,"
                                   " phu_trach = %s, nguoi_tao_lead = %s, ten_co_hoi = %s, address = %s")

                            if phu_trach == ' ...':
                                val = (ten_khach, sdt, cong_ty, mst, yeu_cau, 'waiting', phu_trach, self.user, ten_lead, diachi)
                                misc.send_to_telegram(self.user + ' đã sửa thông tin lead ' + str(lead_id))
                            else:
                                val = (lead_id, ten_khach, sdt, cong_ty, mst, yeu_cau, 'Đã nhận việc', phu_trach, self.user, ten_lead, diachi)
                                if phu_trach != self.user:
                                    misc.send_to_telegram(self.user + ' đã sửa thông tin lead ' + str(lead_id) + '.')
                                else:
                                    misc.send_to_telegram(self.user + ' đã sửa thông tin lead ' + str(lead_id) + '.')

                            misc.sql_commit(sql, val)

                            # Ghi lịch sử tạo lead của user
                            ttkh = [ten_khach, sdt, cong_ty, mst, phu_trach, lead_id, diachi]

                            LeadHandle.luu_thong_tin_kh(self, ttkh)
                            self.uic3.label_noti.setText('Đã sửa thông tin và ghi lên hệ thống!')

                        else:
                            self.uic3.label_noti.setText('Cần ghi rõ tên cơ hội')
                    else:
                        self.uic3.label_noti.setText('Cần ghi rõ nội dung khách hàng yêu cầu')
                else:
                    self.uic3.label_noti.setText('Vui lòng xem lại tên người liên hệ')
            else:
                self.uic3.label_noti.setText('Số điện thoại phải là 10 chữ số')
        except Exception as e:
            print(e)

    def luu_thong_tin_kh(self, ttkh):
        # ttkh = [ten_khach, sdt, cong_ty, mst, phu_trach, lead_id, diachi]
        tenkhach = ttkh[0]
        sdt = ttkh[1]
        tencongty = ttkh[2]
        mst = ttkh[3]
        nguoiphutrach = ttkh[4]
        leadid = ttkh[5]
        diachi = ttkh[6]

        kq = misc.sql_one("SELECT * from ds_ca_nhan WHERE dien_thoai = %s", (sdt,))

        if kq:
            # Combine the existing lead with the new lead
            new_lead = kq[2] + '|' + ttkh[5]
            # Update the existing record
            misc.sql_commit(
                "UPDATE ds_ca_nhan SET ten = %s, leads = %s, ten_cong_ty = %s, mst_cong_ty = %s, address = %s WHERE dien_thoai = %s",
                (tenkhach, new_lead, tencongty, mst, diachi, sdt,)
            )
        else:
            # Insert a new record
            misc.sql_commit(
                "INSERT INTO ds_ca_nhan (ten, dien_thoai, leads, ten_cong_ty, mst_cong_ty, address) VALUES (%s, %s, %s, %s, %s, %s)",
                (tenkhach, sdt, leadid, tencongty, mst, diachi,)
            )

        # Nếu có mã số thuế, ghi thông tin công ty vào bảng ds_cong_ty
        if mst.strip() != '':

            kq = misc.sql_one("SELECT * from ds_cong_ty WHERE mst = %s", (mst,))
            if kq is None:   # Nếu không có mã số thuế trong cơ sở dữ liệu
                # Lưu ý:  cell nguoi_lien_he là text (ten_nguoi_lien_he|số điện thoại), mỗi người 1 dòng
                # ttkh = [ten_khach, sdt, cong_ty, mst, phu_trach, lead_id, diachi]
                misc.sql_commit("INSERT into ds_cong_ty (ten_cong_ty, dia_chi, mst, leads, nguoi_lien_he, sdt_nguoi_lh, phu_trach) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s)", (tencongty, diachi, mst, leadid, tenkhach, sdt, nguoiphutrach,))

            else:
                kq = misc.sql_one("SELECT * from ds_cong_ty WHERE mst = %s", (mst,))
                new_lead_id = kq[2] + '|' + leadid

                misc.sql_commit("UPDATE ds_cong_ty SET leads = %s, ten_cong_ty = %s, nguoi_lien_he = %s, sdt_nguoi_lh = %s, dia_chi = %s "
                                "WHERE mst = %s", (new_lead_id, tencongty, ttkh[0], ttkh[1], diachi, mst,))

    def show_quotato_from_lead(self, lead_id):
        self.win_quotato = quotation.Quotato()
        self.win_quotato.user = self.user
        self.win_quotato.user_phone = self.user_phone
        self.win_quotato.before_make_quotation(lead_id)


