import os
from PyQt6.QtCore import Qt, QTimer
import misc
from PyQt6.QtCore import QThreadPool
from login_worker import LoginWorker


def check_saved_login(main):
    if not os.path.exists('login.txt'):
        return

    try:
        with open('login.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) >= 3:
                main.user_phone = lines[0].strip()
                main.user = lines[2].strip()
                main.logged_in = True

                # 🚀 ĐẨY DB LOGIN SANG THREAD
                worker = LoginWorker(main.user_phone)

                worker.signals.success.connect(
                    lambda power: on_login_success(main, power)
                )
                worker.signals.error.connect(
                    lambda msg: on_login_error(main, msg)
                )

                # ⚠️ PHẢI giữ tham chiếu (sửa 6/8/2026).
                # `worker` là biến cục bộ: hết hàm này là Python có thể thu hồi
                # nó cùng với `worker.signals`, trong khi luồng nền VẪN đang
                # chạy → đối tượng QObject bị huỷ giữa chừng, và lần emit tiếp
                # theo ném "wrapped C/C++ object ... has been deleted".
                main._login_worker = worker

                QThreadPool.globalInstance().start(worker)

    except Exception as e:
        print("Lỗi khi đọc login.txt:", e)


def on_login_success(main, user_power):
    # Cửa sổ có thể đã đóng trong lúc chờ DB → thao tác lên nó sẽ ném
    # RuntimeError. Lúc đó chẳng còn gì để làm, bỏ qua là đúng.
    try:
        main.user_power = user_power
        # ⚠️ POST LOGIN PHẢI CHẠY TRONG MAIN THREAD
        QTimer.singleShot(0, main.post_login_setup)
    except RuntimeError:
        pass


def on_login_error(main, message):
    print("❌ Auto login thất bại:", message)
    try:
        main.logged_in = False
    except RuntimeError:
        pass


def finish_login_from_db(self):
    try:
        # 🔒 DB call sau khi Qt đã chạy ổn
        result = misc.sql_one(
            "SELECT * FROM user WHERE phone_number = %s",
            (self.user_phone,)
        )
        self.user_power = int(result[3])

        self.post_login_setup()

    except Exception as e:
        print("❌ Lỗi finish_login_from_db:", e)
        self.uic.label_noti.setText("Lỗi kết nối CSDL khi auto-login.")

def handle_login(main):
    try:
        # Lấy text từ QTextEdit
        user_text = main.uic.text_user.toPlainText()
        pass_text = main.uic.text_password.toPlainText()
        # 👉 Nếu nhấn Enter ở ô USER thì chuyển focus sang PASSWORD
        if '\n' in user_text and '\n' not in pass_text:
            user = user_text.strip()

            main.uic.text_user.blockSignals(True)
            main.uic.text_user.setPlainText(user)
            main.uic.text_user.blockSignals(False)

            main.uic.text_password.setFocus()
            return

        # 🚫 CHỈ xử lý khi nhấn Enter
        if '\n' not in user_text and '\n' not in pass_text:
            return

        # Làm sạch text (loại bỏ xuống dòng)
        user = user_text.strip()
        password = pass_text.strip()

        # Reset QTextEdit để tránh trigger lặp
        main.uic.text_user.blockSignals(True)
        main.uic.text_password.blockSignals(True)

        main.uic.text_user.setPlainText(user)
        main.uic.text_password.setPlainText(password)

        main.uic.text_user.blockSignals(False)
        main.uic.text_password.blockSignals(False)

        # Kiểm tra dữ liệu
        if not user or not password:
            return

        # Truy vấn DB
        result = misc.sql_all(
            "SELECT * FROM user WHERE phone_number = %s",
            (user,)
        )

        if result and password == result[0][1]:
            main.user = result[0][2]
            main.user_phone = result[0][0]
            main.user_power = int(result[0][3])
            main.logged_in = True

            # Lưu login.txt
            with open('login.txt', 'w', encoding='utf-8') as f:
                f.write(main.user_phone + '\n')
                f.write(password + '\n')
                f.write(main.user + '\n')

            # ⚠️ Post-login chạy SAU event loop
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, main.post_login_setup)

        else:
            main.uic.label_noti.setStyleSheet("color: red")
            main.uic.label_noti.setText("❌ Số điện thoại hoặc mật khẩu không đúng!")

    except Exception as e:
        print("Lỗi handle_login:", e)
        main.uic.label_noti.setText("⚠️ Lỗi khi đăng nhập.")

def handle_logout(main):
    """Xử lý đăng xuất người dùng"""
    main.logged_in = False
    main.user = None
    main.user_phone = None
    main.user_power = 0

    main.uic.text_user.show()
    main.uic.text_password.show()
    main.uic.text_user.setPlainText('')
    main.uic.text_password.setPlainText('')
    main.uic.label_username.setText('')
    main.uic.tableWidget.clear()
    main.uic.label_so_co_hoi.setText('')
    main.uic.label_doanh_so.setText('')
    main.uic.label_noti.setText('')

    main.uic.but_crm.setEnabled(False)
    main.uic.but_mydesk.setEnabled(False)
    main.uic.but_co_hoi_moi.setEnabled(False)
    main.uic.but_tao_co_hoi.setEnabled(False)
    main.uic.but_quan_ly_kho.setEnabled(False)
    main.uic.but_sua_bang_gia.setEnabled(False)

    try:
        os.remove('login.txt')
    except:
        pass


