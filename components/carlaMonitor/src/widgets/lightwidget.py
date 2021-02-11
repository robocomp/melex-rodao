from PySide2.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QIcon
from PySide2.QtWidgets import QRadioButton, QWidget, QLabel, QHBoxLayout
from PySide2.QtCore import Qt, QPointF, QSize

import pathlib
FILE_PATH = pathlib.Path(__file__).parent.absolute()

class LightState(QWidget):
    def __init__(self, text="estado", colour_on=QColor("lightgreen"), colour_off=QColor("red")):
        super(LightState, self).__init__()
        self.light = LightWidget(colour_on, colour_off)
        self.label = QLabel(text)
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignVCenter)
        self.layout.addWidget(self.light)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def turn_off(self):
        self.light.turn_off()

    def turn_on(self):
        self.light.turn_on()

class LightWidget(QWidget):
    def __init__(self, colour_on=QColor("lightgreen"), colour_off=QColor("red")):
        super(LightWidget, self).__init__()
        self.on_colour = colour_on
        self.off_colour = colour_off
        self.is_on = False
        sp = self.sizePolicy()
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.setMinimumWidth(20)
        self.setMinimumHeight(20)

    def is_on(self):
        return self.is_on

    def set_on(self, on):
        if self.is_on == on:
            return
        self.is_on = on
        self.update()

    def turn_off(self):
        self.set_on(False)

    def turn_on(self):
        self.set_on(True)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        the_size = min(self.width(), self.height())

        gradient = QRadialGradient(QPointF(2*the_size/3,the_size/3), the_size)
        if self.is_on:
            painter.drawPixmap(0, 0, the_size, the_size,
                               QIcon(str(FILE_PATH / "../resources/images/greenlight.svg")).pixmap(QSize(the_size, the_size)))
        else:
            painter.drawPixmap(0, 0, the_size, the_size,
                               QIcon(str(FILE_PATH / "../resources/images/redlight.svg")).pixmap(QSize(the_size, the_size)))



        # INNER Gradient
        # lgradien = QLinearGradient(the_size/2, 0, the_size/3, the_size)
        # lgradien.setColorAt(0.0, QColor(255, 255, 255, 200))
        # lgradien.setColorAt(.5, QColor(255, 255, 255, 0))
        # painter.setBrush(lgradien)
        # painter.setPen(Qt.NoPen)
        # painter.drawEllipse(0, 2, the_size, the_size/3)

        painter.end()






if __name__ == '__main__':
    import sys
    from PySide2.QtCore import  QCoreApplication, Qt
    from PySide2.QtWidgets import QApplication
    # QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = LightState("patata", QColor("lightgreen"), QColor("red"))
    window.turn_on()
    window.show()
    app.exec_()

