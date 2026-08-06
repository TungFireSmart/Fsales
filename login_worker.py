"""
Đăng nhập chạy ở luồng nền, để truy vấn DB không làm đơ giao diện.

SỬA 6/8/2026 — lỗi:
    RuntimeError: wrapped C/C++ object of type LoginWorkerSignals has been deleted

NGUYÊN NHÂN
-----------
`LoginWorkerSignals` là một QObject. Khi cửa sổ chính đóng — hoặc khi
`MainWindow.__init__` ném lỗi giữa chừng — Qt huỷ đối tượng ở tầng C++,
nhưng luồng nền VẪN đang chạy và vẫn cố `emit`. Emit lên một QObject đã
chết ⇒ RuntimeError.

Bản cũ còn làm lỗi nhân đôi: lệnh `emit` nằm ngay trong `try`, nên khi
`success.emit` hỏng thì rơi xuống `except` và gọi tiếp `error.emit` —
cũng hỏng nốt ⇒ hai traceback chồng lên nhau, đúng như đã gặp.

CÁCH SỬA
--------
Bọc mọi lần emit trong `_phat()`. Cửa sổ đã đóng thì không còn ai nghe,
im lặng bỏ qua mới là đúng — đây không phải lỗi cần báo.
"""

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

    def _phat(self, tin_hieu, gia_tri):
        """
        Emit an toàn. Trả False nếu bên nhận đã bị Qt huỷ.

        RuntimeError ở đây KHÔNG phải sự cố — nó chỉ có nghĩa là cửa sổ đã
        đóng trước khi truy vấn xong. Ném nó lên chỉ làm bẩn log và khiến
        người đọc tưởng đăng nhập bị hỏng.
        """
        try:
            tin_hieu.emit(gia_tri)
            return True
        except RuntimeError:
            return False

    def run(self):
        try:
            # Chỉ lấy đúng cột cần thay vì SELECT * rồi đọc result[3]:
            # nhanh hơn, và không vỡ nếu thứ tự cột trong bảng thay đổi.
            result = misc.sql_one(
                "SELECT power FROM user WHERE phone_number = %s",
                (self.user_phone,)
            )
            if not result:
                self._phat(self.signals.error, "Không tìm thấy user trong DB")
                return

            self._phat(self.signals.success, int(result[0]))

        except Exception as e:
            # Lỗi thật (mất mạng, sai SQL…) — báo lên nếu còn ai nghe.
            self._phat(self.signals.error, str(e))
