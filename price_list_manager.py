from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import QTableWidgetItem, QStyledItemDelegate, QStyle
import misc
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from openpyxl import Workbook


class CustomDelegate(QStyledItemDelegate):
    def __init__(self, selected_color_hex):
        super().__init__()
        self.selected_color = QColor(selected_color_hex)

    def paint(self, painter, option, index):
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            painter.fillRect(option.rect, QBrush(self.selected_color))
            painter.setPen(QColor('black'))
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignLeft, index.data())
            painter.restore()
        else:
            super().paint(painter, option, index)


class PriceListManager:
    def __init__(self, ui, user):
        self.uic6 = ui
        self.user = user

        self.show_bang_gia()
        self.uic6.text_search.returnPressed.connect(self.tim_kiem_san_pham)
        self.uic6.but_excel.clicked.connect(self.export_to_excel)

    def export_to_excel(self):
        try:
            # Mở hộp thoại chọn đường dẫn lưu file
            file_path, _ = QFileDialog.getSaveFileName(
                self.uic6.tableWidget,
                "Lưu file Excel",
                "bang_gia.xlsx",
                "Excel Files (*.xlsx)"
            )

            if not file_path:
                return  # Người dùng bấm Cancel

            wb = Workbook()
            ws = wb.active
            ws.title = "Bảng giá tổng hợp"

            # Ghi tiêu đề cột
            headers = [self.uic6.tableWidget.horizontalHeaderItem(i).text() for i in
                       range(self.uic6.tableWidget.columnCount())]
            ws.append(headers)

            # Ghi dữ liệu từ bảng
            for row in range(self.uic6.tableWidget.rowCount()):
                row_data = []
                for col in range(self.uic6.tableWidget.columnCount()):
                    item = self.uic6.tableWidget.item(row, col)
                    row_data.append(item.text() if item else "")
                ws.append(row_data)

            # Lưu file
            wb.save(file_path)
            QMessageBox.information(self.uic6.tableWidget, "✅ Thành công", f"Đã lưu file Excel:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self.uic6.tableWidget, "❌ Lỗi", f"Không thể lưu file Excel:\n{e}")

    def show_bang_gia(self):

        q = "SELECT * from gia_tong_hop"
        data = misc.sql_all(q, None)
        self.uic6.tableWidget.setItemDelegate(CustomDelegate("#e6fff5"))  # Yellow color in hex
        self.uic6.tableWidget.setRowCount(len(data))  # tạo số row
        self.uic6.tableWidget.setColumnCount(10)  # tạo số column
        self.uic6.tableWidget.setColumnWidth(0, 300)
        self.uic6.tableWidget.setColumnWidth(1, 90)
        self.uic6.tableWidget.setColumnWidth(2, 90)
        self.uic6.tableWidget.setColumnWidth(3, 70)
        self.uic6.tableWidget.setColumnWidth(4, 30)
        self.uic6.tableWidget.setColumnWidth(5, 90)
        self.uic6.tableWidget.setColumnWidth(6, 90)
        self.uic6.tableWidget.setColumnWidth(7, 90)
        self.uic6.tableWidget.setColumnWidth(8, 30)
        self.uic6.tableWidget.setColumnWidth(9, 90)

        header = ['Mô tả sản phẩm', 'Model', 'Nhãn hiệu', 'Xuất xứ', 'ĐV', 'Giá cấp 1', 'Giá cấp 2', 'Giá bán lẻ',
                  'VAT', 'Giá vốn']
        self.uic6.tableWidget.setHorizontalHeaderLabels(header)

        for row in range(len(data)):
            indices_to_remove = {0}  # Using a set for faster lookups

            data[row] = [item for index, item in enumerate(data[row]) if index not in indices_to_remove]

            for col in range(10):
                item = QTableWidgetItem()
                item.setText(str(data[row][col]))
                self.uic6.tableWidget.setItem(row, col, item)

        # ✅ Kết nối lại
        self.uic6.tableWidget.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        try:
            item_model = self.uic6.tableWidget.item(row, 1)
            item_value = self.uic6.tableWidget.item(row, col)
            header_item = self.uic6.tableWidget.horizontalHeaderItem(col)

            if not item_model or not item_value or not header_item:
                return

            model = item_model.text().strip()
            new_value = item_value.text().strip()
            header = header_item.text().strip()

            if not model:
                self.uic6.label.setText("⚠️ Model không được để trống!")
                self.uic6.label.setStyleSheet("color: red")
                return

            column_mapping = {
                "Mô tả sản phẩm": "ten_san_pham",
                "Model": "model",
                "Nhãn hiệu": "nhan_hieu",
                "Xuất xứ": "xuat_xu",
                "ĐV": "don_vi",
                "Giá cấp 1": "gia_cap_1",
                "Giá cấp 2": "gia_cap_2",
                "Giá bán lẻ": "gia_ban_le",
                "VAT": "vat",
                "Giá vốn": "gia_dau_vao",
            }

            if header not in column_mapping:
                return

            db_col = column_mapping[header]

            numeric_cols = {"gia_cap_1", "gia_cap_2", "gia_ban_le", "vat", "gia_dau_vao"}
            if db_col in numeric_cols:
                if new_value == "":
                    self.uic6.label.setText(f"⚠️ '{header}' không được để trống!")
                    self.uic6.label.setStyleSheet("color: red")
                    return
                try:
                    save_value = int(str(new_value).replace(",", "").replace(".", ""))
                except ValueError:
                    self.uic6.label.setText(f"⚠️ '{header}' phải là số hợp lệ!")
                    self.uic6.label.setStyleSheet("color: red")
                    return
            else:
                save_value = new_value

            confirm = QMessageBox.question(
                self.uic6.tableWidget,
                "Xác nhận lưu",
                f"💾 Bạn có muốn lưu thay đổi cột '{header}' thành: {new_value} ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                sql = f"UPDATE gia_tong_hop SET {db_col} = %s WHERE model = %s"
                misc.sql_commit(sql, (save_value, model))
                self.uic6.label.setText(f"✅ Đã lưu thay đổi '{header}' cho model {model}")
                self.uic6.label.setStyleSheet("color: green")
            else:
                self.uic6.label.setText("❌ Đã hủy lưu thay đổi.")
                self.uic6.label.setStyleSheet("color: gray")

        except Exception as e:
            self.uic6.label.setText(f"❌ Lỗi khi cập nhật: {e}")
            self.uic6.label.setStyleSheet("color: red")

    def tim_kiem_san_pham(self):

        # 🚫 Tạm ngắt kết nối
        self.uic6.tableWidget.cellChanged.disconnect(self.on_cell_changed)

        keyword = self.uic6.text_search.text().strip().lower()

        # Nếu người dùng nhấn Enter để xuống dòng, loại bỏ ký tự xuống dòng
        self.uic6.text_search.setText(keyword)

        if not keyword:
            self.uic6.label.setText("❗ Vui lòng nhập tên sản phẩm hoặc model để tìm kiếm.")
            self.uic6.label.setStyleSheet("color: orange")
            return

        query = """
            SELECT * FROM gia_tong_hop 
            WHERE LOWER(ten_san_pham) LIKE %s OR LOWER(model) LIKE %s
        """
        like_pattern = f"%{keyword}%"
        result = misc.sql_all(query, (like_pattern, like_pattern))

        if not result:
            self.uic6.label.setText("❌ Không tìm thấy sản phẩm phù hợp.")
            self.uic6.label.setStyleSheet("color: red")
            self.uic6.tableWidget.clearContents()
            self.uic6.tableWidget.setRowCount(0)
            return

        self.uic6.label.setText(f"🔍 Tìm thấy {len(result)} kết quả.")
        self.uic6.label.setStyleSheet("color: green")

        self.refresh_price_table(result)

        # ✅ Kết nối lại
        self.uic6.tableWidget.cellChanged.connect(self.on_cell_changed)

    def refresh_price_table(self, data):
        self.uic6.tableWidget.setRowCount(len(data))
        self.uic6.tableWidget.setColumnCount(10)

        column_widths = [300, 90, 90, 70, 30, 90, 90, 90, 30, 90]
        for i, width in enumerate(column_widths):
            self.uic6.tableWidget.setColumnWidth(i, width)

        headers = ['Mô tả sản phẩm', 'Model', 'Nhãn hiệu', 'Xuất xứ', 'ĐV', 'Giá cấp 1', 'Giá cấp 2', 'Giá bán lẻ', 'VAT', 'Giá vốn']
        self.uic6.tableWidget.setHorizontalHeaderLabels(headers)

        for row in range(len(data)):
            cleaned_data = [item for i, item in enumerate(data[row]) if i != 0]
            for col in range(10):
                item = QTableWidgetItem(str(cleaned_data[col]))
                self.uic6.tableWidget.setItem(row, col, item)

        self.uic6.tableWidget.repaint()
