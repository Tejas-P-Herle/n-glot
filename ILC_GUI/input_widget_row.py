from PyQt5.QtWidgets import QHBoxLayout, QLabel


class InputWidgetRow(QHBoxLayout):
    def __init__(self, *args, text=None, parent=None):
        super().__init__()

        if text is not None:
            self.label = QLabel(text, parent=parent)
            self.addWidget(self.label, 1)

        for widget in args:
            if not isinstance(widget, tuple):
                widget = (widget,)

            if widget[0] is None:
                widget = (QLabel(),) + widget[1:]
            if len(widget) == 1:
                widget = (widget[0], 3)
            self.addWidget(*widget)

    def set_row_hidden(self, hidden):
        """Set hidden property of full row"""

        for i in range(self.count()):
            self.get_widget(i).setHidden(hidden)

    def get_widget(self, i):
        """Get ith widget in layout"""

        return self.itemAt(i).widget()
