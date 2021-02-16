from PySide2.QtGui import QPixmap

from src.widgets.lightwidget import LightState
from src.widgets.mapviewer.mapviewer import MapViewer
from .uiloader import CustomUiLoader
from PySide2.QtWidgets import QWidget

import pathlib

FILE_PATH = pathlib.Path(__file__).parent.absolute()


class ControlWidget(QWidget):
    def __init__(self, parent=None):
        super(ControlWidget, self).__init__()

        CustomUiLoader().loadUi(FILE_PATH / '../resources/uis/monitor.ui', self)
        self.map_widget = MapViewer()
        self.map_layout.addWidget(self.map_widget)

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
        self.camera1_switch.setChecked(True)
        self.camera2_switch.setChecked(True)

    def update_map_position(self, coords):
        self.map_widget.update_map_position(coords[0], coords[1])


if __name__ == '__main__':
    import sys
    from PySide2.QtCore import QCoreApplication, Qt
    from PySide2.QtWidgets import QApplication

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = ControlWidget()
    window.show()
    app.exec_()
