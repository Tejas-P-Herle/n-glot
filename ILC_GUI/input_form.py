
import os
from urllib.parse import urlparse
from PyQt5.QtWidgets import (QWidget, QFormLayout, QLineEdit, QLabel,
                             QPushButton, QToolButton, QFileDialog)
from PyQt5 import QtCore
from ILC_GUI.error_label import ErrorLabel
from ILC_GUI.input_widget_row import InputWidgetRow
from ILC_GUI.file_validator import FileValidator


class InputForm(QWidget):
    input_success: bool = False

    def __init__(self, parent):
        """Initiate new Input Field"""

        super().__init__(parent)
        self.parent = parent
        self.error_state = 1

        flo = QFormLayout()

        input_file_path_err = ErrorLabel()

        self.lang_from = QLineEdit()
        lang_from_row = InputWidgetRow(self.lang_from, text="Language From: ")
        lang_from_row.set_row_hidden(True)
        InputWidgetRow(QLabel("Language From: "), self.lang_from)

        self.input_file_validator = FileValidator(
            self.lang_from, input_file_path_err, self.parent.app.validator)
        self.input_file_path_edit, row = self.get_new_row(
            "Input File: ", self.input_file_validator)

        flo.addRow(row)
        flo.addRow(InputWidgetRow(*input_file_path_err.get_widgets()))
        flo.addRow(lang_from_row)

        output_file_path_err = ErrorLabel()
        self.lang_to = QLineEdit()
        lang_to_row = InputWidgetRow(self.lang_to, text="Language To: ")
        lang_to_row.set_row_hidden(True)

        self.output_file_validator = FileValidator(
            self.lang_to, output_file_path_err, self.parent.app.validator,
            FileValidator.CHECK_PATH)
        self.output_file_path_edit, row = self.get_new_row(
            "Output File: ", self.output_file_validator)

        flo.addRow(row)
        flo.addRow(InputWidgetRow(*output_file_path_err.get_widgets()))
        flo.addRow(lang_to_row)

        self.start_btn = QPushButton("Start", parent)
        self.cancel_btn = QPushButton("Cancel", parent)
        flo.addRow(InputWidgetRow(self.cancel_btn, (self.start_btn, 12)))

        self.start_btn.clicked.connect(self.start_conv)
        self.cancel_btn.clicked.connect(self.parent.quit_app)

        self.setLayout(flo)
        self.setWindowTitle("ILC File Input")

    def start_conv(self):
        """Start Conversion"""

        found_errors = False
        if self.input_file_validator.error_no == 1:
            self.input_file_validator.error_label.show_err_msg(
                "Error: Input File Path cannot be left Blank")
            found_errors = True
        if self.output_file_validator.error_no == 1:
            self.output_file_validator.error_label.show_err_msg(
                "Error: Output File Path cannot be left Blank")
            found_errors = True
        found_errors = (found_errors
                        or self.input_file_validator.error_no != 0
                        or self.output_file_validator.error_no != 0)
        if found_errors:
            return
        self.lang_from = self.parent.app.validator.recognize_language(
            self.input_file_path_edit.text())
        self.lang_to = self.parent.app.validator.recognize_language(
            self.output_file_path_edit.text())

        self.input_success = True
        self.parent.quit_app()

    def get_new_row(self, label_text, validator=None):
        """Creates new LineEdit object"""

        line_edit = QLineEdit()
        if validator is not None:
            line_edit.textChanged.connect(lambda t: validator.validate(t))
        # line_edit.setAlignment(Qt.AlignRight)
        # input_file_path.setFont(QFont("Arial", 20))

        browse_btn = QToolButton()
        browse_btn.setGeometry(QtCore.QRect(210, 10, 25, 19))
        browse_btn.setObjectName("browse_btn")
        browse_btn.clicked.connect(lambda: self.open_browser(line_edit))

        translate = QtCore.QCoreApplication.translate
        browse_btn.setText(translate("TestQFileDialog", "..."))

        return line_edit, InputWidgetRow(line_edit, browse_btn,
                                         text=label_text)

    def open_browser(self, line_edit):
        input_file_path, _ = QFileDialog.getOpenFileUrl(self, "Open File")
        p = urlparse(input_file_path.toLocalFile())
        final_path = os.path.abspath(os.path.join(p.netloc, p.path))
        line_edit.setText(final_path)
