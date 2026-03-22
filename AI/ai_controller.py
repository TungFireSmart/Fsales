from PyQt6.QtCore import QThreadPool
from AI.ai_worker import AIWorker


def ask_ai_safe(question, callback):
    worker = AIWorker(question, callback)
    QThreadPool.globalInstance().start(worker)


def ask_ai_with_handler(question, callback, handler):
    worker = AIWorker(question, callback, handler=handler)
    QThreadPool.globalInstance().start(worker)
