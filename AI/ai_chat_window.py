from PyQt6.QtWidgets import QMainWindow
from win_ai_manager_chat import Ui_ui_ai_manager_chat
from AI.ai_controller import ask_ai_safe, ask_ai_with_handler
from AI.openclaw_bridge_client import ask_openclaw_bridge, fetch_openclaw_history


class AIChatWindow(QMainWindow):
    def __init__(self, parent=None, user_power=0):
        super().__init__(parent)

        self.ui = Ui_ui_ai_manager_chat()
        self.ui.setupUi(self)

        self.setWindowTitle("🌿 Chat với Anna")
        self.ui.textEdit.setReadOnly(True)

        # 🔒 Chỉ quản lý mới dùng
        if user_power < 40:
            self.ui.textEdit.setText("❌ Bạn không có quyền dùng AI quản lý.")
            self.ui.lineEdit.setDisabled(True)
            return

        parent_user = getattr(parent, 'user', '') if parent else ''
        parent_phone = getattr(parent, 'user_phone', '') if parent else ''

        # Ưu tiên định danh ổn định theo phone/user_id để tránh lẫn ngữ cảnh giữa các user trùng tên
        if parent_phone:
            self._user_name = f"phone:{str(parent_phone).strip()}"
        elif parent_user:
            self._user_name = f"name:{str(parent_user).strip()}"
        else:
            self._user_name = 'fsales-user'

        self._load_history()
        self.ui.lineEdit.returnPressed.connect(self.on_ask)

    def _load_history(self):
        self.ui.textEdit.clear()
        rows = fetch_openclaw_history(self._user_name, limit=50)

        if not rows:
            self.ui.textEdit.append("🌿 Anna sẵn sàng. Anh/chị cứ đặt câu hỏi.")
            return

        for item in rows:
            role = item.get("role")
            text = item.get("text", "")
            if role == "user":
                self.ui.textEdit.append(f"👤 Bạn: {text}")
            else:
                self.ui.textEdit.append(f"🌿 Anna: {text}")

    def on_ask(self):
        question = self.ui.lineEdit.text().strip()
        if not question:
            return

        self.ui.textEdit.append(f"\n👤 Bạn: {question}")
        self.ui.lineEdit.clear()

        # 👉 Ưu tiên gọi OpenClaw bridge (Anna thật)
        def _bridge_handler(q: str):
            return ask_openclaw_bridge(q, self._user_name)

        try:
            ask_ai_with_handler(question, self.on_ai_answer, _bridge_handler)
        except Exception:
            # Fallback cũ nếu bridge lỗi khởi tạo
            ask_ai_safe(question, self.on_ai_answer)

    def on_ai_answer(self, answer):
        self.ui.textEdit.append(f"🌿 Anna: {answer}")
