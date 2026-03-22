from datetime import datetime
from PyQt6.QtWidgets import QTableWidgetItem
import misc

class QuotationDisplay:
    @staticmethod
    def show_bao_gia_cu(data, index, uick):
        if index == 0:
            uic = uick.tableWidget
        elif index == 1:
            uic = uick.tableWidget_2
        elif index == 2:
            uic = uick.tableWidget_3
        else:
            uic = uick.tableWidget_4

        uic.clear()
        uic.setRowCount(len(data))
        uic.setColumnCount(8)
        uic.setColumnWidth(0, 400)
        uic.setColumnWidth(1, 80)
        uic.setColumnWidth(2, 80)
        uic.setColumnWidth(3, 50)
        uic.setColumnWidth(4, 60)
        uic.setColumnWidth(5, 90)
        uic.setColumnWidth(6, 90)
        uic.setColumnWidth(7, 90)

        header = ['Mô tả sản phẩm', 'Model', 'Nhãn hiệu', 'ĐV tính', 'Số lượng', 'Đơn giá', 'Thuế', 'Nhân công']
        uic.setHorizontalHeaderLabels(header)
        uic.repaint()

        for row in range(uic.rowCount()):
            if len(data[row]) == 6:
                data[row].append("")
            if len(data[row]) == 7:
                data[row].append("")

            for col in range(8):
                item = QTableWidgetItem()
                if col == 5:
                    if data[row][col] != '':
                        temp = str(data[row][col]).replace(",", "")
                        item.setText("{:,}".format(round(int(temp), 0)))
                else:
                    item.setText(str(data[row][col]))
                uic.setItem(row, col, item)
            uic.resizeRowToContents(row)
        uic.repaint()

class QuotationSaver:
    @staticmethod
    def sum_save(parent, so_bg, uick):
        try:
            nhap_tay = 'T' if uick.checkBox.isChecked() else 'F'

            uic = uick.tableWidget
            noi_dung_bao_gia = []

            # Giá áp dụng
            gia_index_map = {
                'Giá bán lẻ': 8,
                'Giá cấp 1': 6,
                'Giá cấp 2': 7,
                'Giá thuê theo ngày': 12,
                'Giá thuê theo tháng': 13,
                'Giá thuê theo năm': 14
            }
            gia_ap_dung = uick.comboBox.currentText()
            col_index = gia_index_map.get(gia_ap_dung, 8)

            for row in range(uic.rowCount()):
                col_list = []
                for col in range(8):
                    try:
                        tex = uic.item(row, col).text().strip()
                        if tex is None:
                            tex = ''
                        if col == 5 or col == 4:
                            tex = int(tex.replace(",", "")) if tex else 0
                    except:
                        tex = 0
                    col_list.append(tex)

                kq = misc.sql_one("Select * from gia_tong_hop where model = %s", (col_list[1],))

                if kq is not None:
                    col_list[2] = kq[3]
                    col_list[3] = kq[5]
                    if col_list[6] in ['0', '', 0]:
                        col_list[6] = kq[9]
                    col_list[7] = kq[11]

                    if not uick.checkBox.isChecked():
                        col_list[0] = kq[1]

                    if nhap_tay == 'T' and col_list[5] == 0:
                        col_list[5] = int(kq[col_index])
                    elif nhap_tay == 'F':
                        col_list[5] = int(kq[col_index])

                    misc.sql_commit("UPDATE ds_bao_gia SET ghi_chu = %s WHERE so_bg = %s", (gia_ap_dung, so_bg))

                col_list.append('')
                col_list[4] = int(col_list[4]) if isinstance(col_list[4], int) or str(col_list[4]).isdigit() else 0

                if col_list[4] > 0:
                    noi_dung_bao_gia.append(col_list)

            sum8 = sum(int(ele[4]) * int(ele[5]) for ele in noi_dung_bao_gia if ele[1] != 'NhanCong' and int(ele[6]) == 8)
            sum10 = sum(int(ele[4]) * int(ele[5]) for ele in noi_dung_bao_gia if ele[1] != 'NhanCong' and int(ele[6]) == 10)
            sum0 = sum8 + sum10

            try:
                nc = sum(int(ele[4]) * int(ele[7]) for ele in noi_dung_bao_gia if ele[1] != 'NhanCong' and ele[7] is not None)
            except:
                nc = 0

            if gia_ap_dung in ['Giá thuê theo ngày', 'Giá thuê theo tháng', 'Giá thuê theo năm']:
                nc = nc / 2

            for i in range(len(noi_dung_bao_gia)):
                if noi_dung_bao_gia[i][1] == 'NhanCong' and nhap_tay == 'F':
                    noi_dung_bao_gia[i][4] = 1
                    noi_dung_bao_gia[i][5] = nc

            # LUÔN TÍNH VAT
            # ===== TÍNH TOÁN CHUẨN =====
            vat8_value = sum8 * 0.08
            vat10_value = sum10 * 0.1

            tong_tien_hang = sum0
            tong_vat = vat8_value + vat10_value
            tong_thanh_toan = tong_tien_hang + tong_vat

            # ===== HIỂN THỊ RA 3 LABEL =====
            uick.label_showtienhang.setText("{:,}".format(round(tong_tien_hang)))
            uick.label_showvat.setText("{:,}".format(round(tong_vat)))
            uick.label_showtongcong.setText("{:,}".format(round(tong_thanh_toan)))

            uick.label_showtienhang.repaint()
            uick.label_showvat.repaint()
            uick.label_showtongcong.repaint()

            noi_dung = []
            for row in noi_dung_bao_gia:
                row.pop()
                if row[0] != '':
                    text = '|'.join(str(item) for item in row)
                    noi_dung.append(text)

            noi_dung_bg = '@'.join(noi_dung)

            lead_id = uick.label_lead_id.text()
            ngaythang = datetime.now().strftime("%d/%m/%y")
            dienthoai = uick.text_sdt.toPlainText()
            tieu_de = uick.text_noi_dung.toPlainText()

            query = """UPDATE ds_bao_gia SET lead_id = %s, ngaythang = %s, noi_dung = %s, tieu_de = %s, user = %s, dien_thoai = %s, sum8 = %s, sum10 = %s, sotien = %s, sum0 = %s, gia_nhap_tay = %s WHERE so_bg = %s"""
            data = (lead_id, ngaythang, noi_dung_bg, tieu_de, parent.user, dienthoai, sum8, sum10, tong_thanh_toan, sum0, nhap_tay, so_bg)
            misc.sql_commit(query, data)

            uick.but_excel.setEnabled(True)
            QuotationDisplay.show_bao_gia_cu(noi_dung_bao_gia, uick.tabWidget.currentIndex(), uick)

        except Exception as e:
            print(e)
