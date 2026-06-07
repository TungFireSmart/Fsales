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
    ORIGINAL_MODEL_ROLE = Qt.ItemDataRole.UserRole

    # header, db column, width, is numeric
    PRICE_COLUMNS = [
        ("Mô tả sản phẩm", "ten_san_pham", 300, False),
        ("Model", "model", 90, False),
        ("Nhãn hiệu", "nhan_hieu", 90, False),
        ("Xuất xứ", "xuat_xu", 70, False),
        ("ĐV", "don_vi", 30, False),
        ("Giá cấp 1", "gia_cap_1", 90, True),
        ("Giá cấp 2", "gia_cap_2", 90, True),
        ("Giá bán lẻ", "gia_ban_le", 90, True),
        ("VAT", "vat", 30, True),
        ("Giá vốn", "gia_dau_vao", 90, True),
        ("Đơn giá nhân công", "nhan_cong", 130, True),
    ]

    def __init__(self, ui, user):
        self.uic6 = ui
        self.user = user

        self.show_bang_gia()
        self.uic6.text_search.returnPressed.connect(self.tim_kiem_san_pham)
        self.uic6.but_excel.clicked.connect(self.export_to_excel)
        self.uic6.but_xoadong.clicked.connect(self.xoa_dong_hien_tai)

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

    def _select_columns_sql(self):
        return ", ".join(db_col for _, db_col, _, _ in self.PRICE_COLUMNS)

    def _setup_price_table(self, row_count):
        self.uic6.tableWidget.setItemDelegate(CustomDelegate("#e6fff5"))
        self.uic6.tableWidget.setRowCount(row_count)
        self.uic6.tableWidget.setColumnCount(len(self.PRICE_COLUMNS))

        for col, (_, _, width, _) in enumerate(self.PRICE_COLUMNS):
            self.uic6.tableWidget.setColumnWidth(col, width)

        self.uic6.tableWidget.setHorizontalHeaderLabels([header for header, _, _, _ in self.PRICE_COLUMNS])

    def _populate_price_table(self, data):
        table = self.uic6.tableWidget
        table.blockSignals(True)
        try:
            self._setup_price_table(len(data))

            for row, row_data in enumerate(data):
                original_model = str(row_data[1]).strip() if row_data[1] is not None else ""
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem("" if value is None else str(value))
                    item.setData(self.ORIGINAL_MODEL_ROLE, original_model)
                    table.setItem(row, col, item)
        finally:
            table.blockSignals(False)

        table.repaint()

    def show_bang_gia(self):
        q = f"SELECT {self._select_columns_sql()} FROM gia_tong_hop"
        data = misc.sql_all(q, None)
        self._populate_price_table(data)
        self.uic6.tableWidget.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        try:
            item_model = self.uic6.tableWidget.item(row, 1)
            item_value = self.uic6.tableWidget.item(row, col)
            header_item = self.uic6.tableWidget.horizontalHeaderItem(col)

            if not item_model or not item_value or not header_item:
                return

            model = item_model.text().strip()
            original_model = item_model.data(self.ORIGINAL_MODEL_ROLE) or model
            original_model = str(original_model).strip()
            new_value = item_value.text().strip()
            header = header_item.text().strip()

            if not model:
                self.uic6.label.setText("⚠️ Model không được để trống!")
                self.uic6.label.setStyleSheet("color: red")
                return

            column_mapping = {header: db_col for header, db_col, _, _ in self.PRICE_COLUMNS}

            if header not in column_mapping:
                return

            db_col = column_mapping[header]

            numeric_cols = {db_col for _, db_col, _, is_numeric in self.PRICE_COLUMNS if is_numeric}
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
                misc.sql_commit(sql, (save_value, original_model))

                if db_col == "model":
                    self._set_original_model_for_row(row, model)
                    status_model = f"{original_model} → {model}"
                else:
                    status_model = original_model

                self.uic6.label.setText(f"✅ Đã lưu thay đổi '{header}' cho model {status_model}")
                self.uic6.label.setStyleSheet("color: green")
            else:
                self.uic6.label.setText("❌ Đã hủy lưu thay đổi.")
                self.uic6.label.setStyleSheet("color: gray")

        except Exception as e:
            self.uic6.label.setText(f"❌ Lỗi khi cập nhật: {e}")
            self.uic6.label.setStyleSheet("color: red")

    def _set_original_model_for_row(self, row, model):
        table = self.uic6.tableWidget
        table.blockSignals(True)
        try:
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    item.setData(self.ORIGINAL_MODEL_ROLE, model)
        finally:
            table.blockSignals(False)

    def xoa_dong_hien_tai(self):
        table = self.uic6.tableWidget
        row = table.currentRow()

        if row < 0:
            self.uic6.label.setText("⚠️ Vui lòng chọn dòng cần xóa.")
            self.uic6.label.setStyleSheet("color: orange")
            return

        item_model = table.item(row, 1)
        if not item_model:
            self.uic6.label.setText("⚠️ Không xác định được model của dòng cần xóa.")
            self.uic6.label.setStyleSheet("color: red")
            return

        model = item_model.data(self.ORIGINAL_MODEL_ROLE) or item_model.text().strip()
        model = str(model).strip()
        if not model:
            self.uic6.label.setText("⚠️ Model không được để trống!")
            self.uic6.label.setStyleSheet("color: red")
            return

        confirm = QMessageBox.question(
            table,
            "Xác nhận xóa",
            f"🗑️ Bạn có chắc muốn xóa sản phẩm model '{model}' khỏi bảng giá?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            self.uic6.label.setText("❌ Đã hủy xóa dòng.")
            self.uic6.label.setStyleSheet("color: gray")
            return

        try:
            misc.sql_commit("DELETE FROM gia_tong_hop WHERE model = %s", (model,))
            table.blockSignals(True)
            try:
                table.removeRow(row)
            finally:
                table.blockSignals(False)
            self.uic6.label.setText(f"✅ Đã xóa sản phẩm model {model}")
            self.uic6.label.setStyleSheet("color: green")
        except Exception as e:
            self.uic6.label.setText(f"❌ Lỗi khi xóa dòng: {e}")
            self.uic6.label.setStyleSheet("color: red")

    def tim_kiem_san_pham(self):
        keyword = self.uic6.text_search.text().strip().lower()

        # Nếu người dùng nhấn Enter để xuống dòng, loại bỏ ký tự xuống dòng
        self.uic6.text_search.setText(keyword)

        if not keyword:
            self.uic6.label.setText("❗ Vui lòng nhập tên sản phẩm hoặc model để tìm kiếm.")
            self.uic6.label.setStyleSheet("color: orange")
            return

        query = f"""
            SELECT {self._select_columns_sql()} FROM gia_tong_hop
            WHERE LOWER(ten_san_pham) LIKE %s OR LOWER(model) LIKE %s
        """
        like_pattern = f"%{keyword}%"
        result = misc.sql_all(query, (like_pattern, like_pattern))

        if not result:
            self.uic6.label.setText("❌ Không tìm thấy sản phẩm phù hợp.")
            self.uic6.label.setStyleSheet("color: red")
            self.uic6.tableWidget.blockSignals(True)
            try:
                self.uic6.tableWidget.clearContents()
                self.uic6.tableWidget.setRowCount(0)
            finally:
                self.uic6.tableWidget.blockSignals(False)
            return

        self.uic6.label.setText(f"🔍 Tìm thấy {len(result)} kết quả.")
        self.uic6.label.setStyleSheet("color: green")

        self.refresh_price_table(result)

    def refresh_price_table(self, data):
        self._populate_price_table(data)
