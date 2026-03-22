from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QLineEdit, QCompleter

def setup_table_xuat(table, rowcount):
    table.setRowCount(0)
    table.setColumnCount(5)
    table.setRowCount(rowcount)
    table.setHorizontalHeaderLabels(['Tên hàng', 'Model', 'Số lượng', 'Đơn giá', 'Tên kho'])

    table.setColumnWidth(0, 380)
    table.setColumnWidth(1, 100)
    table.setColumnWidth(2, 100)
    table.setColumnWidth(3, 80)
    table.setColumnWidth(4, 100)


def add_row_to_table(table: QTableWidget, row_data: list[str]):
    row = table.rowCount()
    table.insertRow(row)
    for col, value in enumerate(row_data):
        table.setItem(row, col, QTableWidgetItem(value))

def clear_table(table: QTableWidget):
    table.setRowCount(0)

def set_completer(line_edit: QLineEdit, options: list[str]):
    completer = QCompleter(options)
    completer.setCaseSensitivity(False)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    line_edit.setCompleter(completer)

def get_column_values(table: QTableWidget, column: int) -> list[str]:
    return [table.item(row, column).text() for row in range(table.rowCount()) if table.item(row, column)]
