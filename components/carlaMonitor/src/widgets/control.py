from PySide2.QtGui import QPixmap

from src.widgets.lightwidget import LightState
from .uiloader import CustomUiLoader
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtWidgets import QWidget

import pathlib
FILE_PATH = pathlib.Path(__file__).parent.absolute()

class ControlWidget(QWidget):
    def __init__(self, parent=None):
        super(ControlWidget, self).__init__()

        CustomUiLoader().loadUi(FILE_PATH / '../resources/uis/monitor.ui', self)
        map_widget = QWebEngineView()
        self.map_layout.addWidget(map_widget)
        map_widget.page().load('https://www.openstreetmap.org/export/embed.html?bbox=-6.346299648284912%2C39.47831158636391%2C-6.337727308273315%2C39.482013191562885&amp;layer=mapnik')
        self.camera1_image.setPixmap(QPixmap(str(FILE_PATH / "../resources/images/camera1.png")))
        self.camera2_image.setPixmap(QPixmap(str(FILE_PATH / "../resources/images/camera2.png")))
        self.state_light1 = LightState("Estado")
        self.state1_layout.addWidget(self.state_light1)
        self.state_light2 = LightState("Estado")
        self.state2_layout.addWidget(self.state_light2)

        self.gps_state_light = LightState("GPS")

        self.imu_state_light = LightState("IMU")

        self.ve_camera_state_light = LightState("Cámara VE")


        self.state_panel.addWidget(self.ve_camera_state_light)
        self.state_panel.addWidget(self.gps_state_light)
        self.state_panel.addWidget(self.imu_state_light)
        self.gps_state_light.turn_on()




if __name__ == '__main__':
    import sys
    from PySide2.QtCore import QCoreApplication, Qt
    from PySide2.QtWidgets import QApplication

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = ControlWidget()
    window.show()
    app.exec_()
