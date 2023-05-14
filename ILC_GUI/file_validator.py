import os
from PyQt5.QtWidgets import QLineEdit


class FileValidator:
    BLANK_INPUT = 1
    MISSING_EXTENSION = 2
    UNKNOWN_LANGUAGE = 3
    FILE_NOT_FOUND_ERROR = 4
    DIR_NOT_FOUND_ERROR = 4

    CHECK_NONE = 0
    CHECK_PATH = 1
    CHECK_ALL = 2

    def __init__(self, lang_edit: QLineEdit, error_label,
                 validator, check_exists=CHECK_ALL):
        """Initiate new FileValidator"""

        self.lang_edit = lang_edit
        self.error_no = self.BLANK_INPUT
        self.error_label = error_label
        self.validator = validator
        self.check_exists = check_exists

    def validate(self, filepath):
        """Validate file path"""

        if self.check_exists & self.CHECK_ALL and not os.path.isfile(filepath):
            self.error_no = self.FILE_NOT_FOUND_ERROR
            self.error_label.show_err_msg("Error: File Doesn't Exist")
            return

        dir_ = os.path.split(filepath)[0]
        if self.check_exists & self.CHECK_PATH and not os.path.isdir(dir_):
            self.error_no = self.DIR_NOT_FOUND_ERROR
            self.error_label.show_err_msg(
                "Error: Parent Directory Doesn't Exist")
            return

        recognized_language = self.validator.recognize_language(filepath)
        if recognized_language == self.MISSING_EXTENSION:
            self.error_no = self.MISSING_EXTENSION
            self.error_label.show_err_msg("Error: Filename Missing Extension")
        elif recognized_language == self.UNKNOWN_LANGUAGE:
            self.error_no = self.UNKNOWN_LANGUAGE
            self.error_label.show_err_msg("Error: Unknown Language Extension")
        else:
            self.lang_edit.setText(recognized_language)
            self.error_no = 0
            self.error_label.set_hidden(True)
