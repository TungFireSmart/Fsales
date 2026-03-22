
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
import misc

class LoginWorkerSignals(QObject):
    success = pyqtSignal(int)   # user_power
    error = pyqtSignal(str)


class LoginWorker(QRunnable):
    def __init__(self, user_phone):
        super().__init__()
        self.user_phone = user_phone
        self.signals = LoginWorkerSignals()

    def run(self):
        try:
            result = misc.sql_one(
                "SELECT * FROM user WHERE phone_number = %s",
                (self.user_phone,)
            )
            if not result:
                self.signals.error.emit("Không tìm thấy user trong DB")
                return

            user_power = int(result[3])
            self.signals.success.emit(user_power)

        except Exception as e:
            # ⚠️ BẮT LỖI PYTHON (không bắt được segfault, nhưng giảm rủi ro)
            self.signals.error.emit(str(e))
