from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QColor

class ColorSelector(QWidget):

    def __init__(self, colors, callback):

        super().__init__()

        layout = QHBoxLayout()

        for c in colors:

            btn = QPushButton()
            btn.setFixedSize(40,40)

            qcolor = QColor(int(c[0]), int(c[1]), int(c[2]))
            btn.setStyleSheet(f"background-color:{qcolor.name()}")

            btn.clicked.connect(lambda _, col=c: callback(col))

            layout.addWidget(btn)

        self.setLayout(layout)