from PyQt5.QtWidgets import QLabel


class ErrorLabel:
    def __init__(self, parent=None, padding=3):
        """Create new Error Label"""

        self.padding_label = QLabel(parent=parent)
        self.err_msg_label = QLabel(parent=parent)
        self.err_msg_label.setStyleSheet("QLabel { color: #D00 }")
        self.padding = padding

        self.set_hidden(True)

    def set_hidden(self, hidden):
        """Set hidden state of padding_label and err_msg_label"""

        self.padding_label.setHidden(hidden)
        self.err_msg_label.setHidden(hidden)

    def show_err_msg(self, err_msg, show=True):
        """Set Error Message to given message"""

        self.err_msg_label.setText(err_msg)
        if show:
            self.set_hidden(False)

    def get_widgets(self):
        """Returns widgets in ErrorLabel"""

        return (self.padding_label, 1), (self.err_msg_label, self.padding)
