from PyQt5.QtWidgets import QWidget, QLabel, QFormLayout


class ConvComplete(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        title = QLabel("Conversion Complete")
        msg = QLabel(
            "The Converted Source Code has been printed to the terminal")
        flo = QFormLayout(self)
        flo.addRow(title)
        flo.addRow(msg)
