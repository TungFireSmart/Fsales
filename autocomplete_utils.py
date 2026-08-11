from PyQt6.QtWidgets import QLineEdit, QTableWidgetItem, QCompleter
from PyQt6.QtCore import Qt, QTimer


class SafeAutoCompletingLineEdit(QLineEdit):
    """
    Editor autocomplete AN TOÀN:
    - Không override focusOutEvent
    - Commit 1 lần duy nhất
    - QTimer là child → không use-after-delete
    """
    def __init__(self, row, col, table_widget, update_callback):
        super().__init__(table_widget)
        self.row = row
        self.col = col
        self.table_widget = table_widget
        self.update_callback = update_callback
        self._committed = False

        self._commit_timer = QTimer(self)
        self._commit_timer.setSingleShot(True)
        self._commit_timer.timeout.connect(self._safe_commit)

        self.textEdited.connect(self._on_text_edited)
        self.editingFinished.connect(self._on_editing_finished)

    def _on_text_edited(self, text):
        if self.completer():
            self.completer().setCompletionPrefix(text)
            self.completer().complete()
        self._commit_timer.stop()

    def _on_editing_finished(self):
        if self._committed:
            return
        self._commit_timer.start(250)

    def _safe_commit(self):
        if self._committed:
            return
        self._committed = True

        text = self.text().strip()

        if text:
            try:
                self.update_callback(self.row, self.col, text, self.table_widget)
            except Exception as e:
                print("Autocomplete commit error:", e)

        self._cleanup()

    def _cleanup(self):
        if self._commit_timer.isActive():
            self._commit_timer.stop()

        if self.table_widget.cellWidget(self.row, self.col) is self:
            self.table_widget.removeCellWidget(self.row, self.col)

        self.deleteLater()
        self.table_widget.viewport().update()


def setup_autocomplete_for_table_row(table, row, model_to_name, name_to_model):
    """
    Setup autocomplete RAM-ONLY, KHÔNG SQL
    """

    def update_callback(row, col, text, table_widget):
        if col == 1:  # Model → Tên
            name = model_to_name.get(text.lower(), "")
            table_widget.setItem(row, 0, QTableWidgetItem(name))
            table_widget.setItem(row, 1, QTableWidgetItem(text))
        else:  # Tên → Model
            model = name_to_model.get(text.lower(), "")
            table_widget.setItem(row, 0, QTableWidgetItem(text))
            table_widget.setItem(row, 1, QTableWidgetItem(model))

    # Completer cho model
    completer_model = QCompleter(list(model_to_name.keys()))
    completer_model.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer_model.setFilterMode(Qt.MatchFlag.MatchContains)

    # Completer cho tên
    completer_name = QCompleter(list(name_to_model.keys()))
    completer_name.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer_name.setFilterMode(Qt.MatchFlag.MatchContains)

    # Cột 0: Tên sản phẩm
    name_edit = SafeAutoCompletingLineEdit(row, 0, table, update_callback)
    name_edit.setCompleter(completer_name)
    table.setItem(row, 0, QTableWidgetItem(""))
    table.setCellWidget(row, 0, name_edit)
    name_edit.setFocus()
    name_edit.selectAll()

    # Cột 1: Model
    model_edit = SafeAutoCompletingLineEdit(row, 1, table, update_callback)
    model_edit.setCompleter(completer_model)
    table.setItem(row, 1, QTableWidgetItem(""))
    table.setCellWidget(row, 1, model_edit)
