from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar
from ILC_GUI.input_form import InputForm
from ILC_GUI.status_form import StatusForm
from ILC_GUI.conv_complete import ConvComplete
import sys


class ILCApp(QApplication):

    def __init__(self, validator):
        super().__init__(sys.argv)
        self.validator = validator
        self.main_window = MainWindow(self)

    def get_inputs(self):
        """Get Filepath inputs loop"""

        self.main_window.show()
        return self.main_window.get_inputs()

    def get_progress_bar(self):
        """Get Progress bar"""

        return self.main_window.get_progress_bar()


class MainWindow(QMainWindow):

    progress_bar = None

    def __init__(self, app: ILCApp):
        super().__init__()

        self.app = app
        self.setWindowTitle("ILC")
        self.setGeometry(100, 100, 500, 400)
        self.show()

    def build_input_form(self):
        """Build Input form"""

        input_form = InputForm(self)
        self.setCentralWidget(input_form)
        return input_form

    def get_inputs(self):
        """Get input values"""

        input_form = self.build_input_form()
        self.app.exec_()
        if input_form.input_success:
            return (input_form.input_file_path_edit.text(),
                    input_form.output_file_path_edit.text(),
                    input_form.lang_from, input_form.lang_to)

    def get_progress_bar(self):
        """Get Progress bar handler"""

        if self.progress_bar is None:
            self.progress_bar = QProgressBar(self)
        return self.progress_bar

    def build_status_window(self):
        """Build status window"""

        status_form = StatusForm(self)
        self.setCentralWidget(status_form)
        return status_form

    def show_progress(self, task, status_win):
        """Show Progress of Conversion"""

        self.show()
        status_win.start(task)
        self.app.exec_()
        return status_win.task.resp

    def show_complete_window(self):
        """Show Conversion Complete window"""

        conv_complete_wid = ConvComplete(self)
        self.setCentralWidget(conv_complete_wid)
        self.show()
        self.app.exec_()

    def quit_app(self):
        """Quit Application"""

        self.app.quit()
