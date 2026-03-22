from PyQt6.QtWidgets import QMainWindow, QMessageBox
from win_ai_manager_chat import Ui_ui_ai_manager_chat

# import AI manager (sẽ viết ngay bên dưới)
from AI.ai_manager import ask_ai_manager


class AiManagerChatWindow(QMainWindow):
    def __init__(self, parent=None, user=None, user_power=0):
        super().__init__(parent)

        self.ui = Ui_ui_ai_manager_chat()
        self.ui.setupUi(self)

        self.user = user
        self.user_power = user_power

        self.setWindowTitle("🤖 AI Trợ lý Quản lý")

        # 🔒 Chỉ cho quản lý dùng
        if self.user_power < 40:
            QMessageBox.warning(
                self,
                "Không có quyền",
                "AI Chat chỉ dành cho quản lý."
            )
            self.close()
            return

        # Gắn sự kiện Enter
        self.ui.lineEdit.returnPressed.connect(self.ask_ai)

        # Gợi ý ban đầu
        self.ui.textBrowser.setText(
            "💡 Gợi ý câu hỏi:\n"
            "- Hôm nay có bao nhiêu lead mới?\n"
            "- Lead nào đang bị bỏ quên?\n"
            "- Ai đang xử lý nhiều lead nhất?\n"
            "- Có báo giá lớn nào chưa chốt?"
        )

        self.ui.textEdit.append("🤖 AI sẵn sàng hỗ trợ quản lý.")

    def ask_ai(self):
        question = self.ui.lineEdit.text().strip()
        if not question:
            return

        # Hiển thị câu hỏi
        self.ui.textEdit.append(f"\n👤 Bạn: {question}")

        try:
            answer = ask_ai_manager(question)
        except Exception as e:
            answer = f"❌ Lỗi AI: {e}"

        # Hiển thị câu trả lời
        self.ui.textEdit.append(f"🤖 AI: {answer}")

        self.ui.lineEdit.clear()
