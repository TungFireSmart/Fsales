from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from AI.ai_logic import answer_manager_question


class AIWorkerSignals(QObject):
    finished = pyqtSignal(str)


class AIWorker(QRunnable):
    def __init__(self, question, callback, handler=None):
        super().__init__()
        self.question = question
        self.signals = AIWorkerSignals()
        self.signals.finished.connect(callback)
        self.handler = handler or answer_manager_question

    def run(self):
        try:
            answer = self.handler(self.question)
        except Exception as e:
            answer = f"Lỗi AI: {e}"

        self.signals.finished.emit(answer)
