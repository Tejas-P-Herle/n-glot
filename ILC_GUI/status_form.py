from PyQt5.QtWidgets import QWidget, QProgressBar, QFormLayout, QLabel
from PyQt5.QtCore import QThread, QObject, pyqtSignal


class Task(QObject):
    update = pyqtSignal(int, str)
    finished = pyqtSignal()
    resp = None

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        """Run new task"""

        self.resp = self.task()
        self.finished.emit()


class StatusForm(QWidget):
    task = None
    thread = None

    def __init__(self, parent):
        """Initiate new Status Form"""

        super().__init__()

        flo = QFormLayout(self)
        self.progress_message = QLabel()
        self.progress_bar = QProgressBar()
        flo.addRow(self.progress_message)
        flo.addRow(self.progress_bar)

        # self.progress.connect(self.reportProgress)

    def start(self, task):
        """Start task and show Status"""

        self.thread = QThread()
        self.task = Task(task)
        self.task.moveToThread(self.thread)
        self.thread.started.connect(self.show)
        self.thread.started.connect(self.task.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.task.finished.connect(self.thread.quit)
        self.task.finished.connect(self.task.deleteLater)
        self.task.update.connect(self.update_progress_bar)
        self.thread.start()

    def update_progress_bar(self, value, msg):
        """Update Progress Bar"""

        self.progress_bar.setValue(value)
        self.progress_message.setText(" ".join(msg.lower().split("_")).title())
