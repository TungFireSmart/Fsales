from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import misc

class WorkerSignals(QObject):
    success = pyqtSignal(tuple)
    failure = pyqtSignal(str)

class SQLLoginWorker(QRunnable):
    def __init__(self, phone, password):
        super().__init__()
        self.phone = phone
        self.password = password
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = misc.sql_one("SELECT * FROM user WHERE phone_number = %s", (self.phone,))
            if result and result[1] == self.password:
                self.signals.success.emit((result[2], result[0], result[3]))
            else:
                self.signals.failure.emit("❌ Số điện thoại hoặc mật khẩu không đúng.")
        except Exception as e:
            self.signals.failure.emit("❌ Không kết nối được đến máy chủ. Vui lòng kiểm tra mạng.")
