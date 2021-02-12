#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2021 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#
import time
from threading import Lock
from PySide2.QtGui import QPixmap, qRgb
import cv2
import numpy as np
from PySide2.QtGui import QImage

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel
from src.widgets.control import ControlWidget


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.mutex = Lock()
        self.start = time.time()
        self.contFPS = 0
        self.start_stop = time.time()
        self.data_received = {}

        self.init_ui()

        self.cameras_widget_dict = {
            5: [self.main_widget.camera1_image, self.main_widget.camera1_switch, self.main_widget.state_light1],
            7: [self.main_widget.camera2_image, self.main_widget.camera2_switch, self.main_widget.state_light2],
        }

        self.is_sensor_active = {
            5: True,
            7: True,
        }

        self.Period = 0
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def init_ui(self):
        self.main_widget = ControlWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.camera1_switch.stateChanged.connect(self.change_camera_state)
        self.main_widget.camera2_switch.stateChanged.connect(self.change_camera_state)

    def change_camera_state(self):
        print('change_camera_state')
        for id, [_, switch, led] in self.cameras_widget_dict.items():
            if switch.isChecked():
                if not self.is_sensor_active[id]:
                    self.adminbridge_proxy.activateSensor(id)
                    self.is_sensor_active[id] = True
                    led.turn_on()
            else:
                if self.is_sensor_active[id]:
                    self.adminbridge_proxy.stopSensor(id)
                    self.is_sensor_active[id] = False
                    led.turn_off()

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        self.mutex.acquire()
        for camera_ID, camera_data in self.data_received.items():
            if camera_data is None:
                continue

            if self.is_sensor_active[camera_ID]:
                array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
                array = np.reshape(array, (camera_data.height, camera_data.width, 4))
                qImg = QImage(array, array.shape[1], array.shape[0], array.strides[0], QImage.Format_ARGB32)

            else:
                qImg = QImage(camera_data.width, camera_data.height, QImage.Format_ARGB32)
                qImg.fill(qRgb(0,0,0))

            self.cameras_widget_dict[camera_ID][0].setPixmap(QPixmap(qImg))
            self.cameras_widget_dict[camera_ID][1].setText('Cámara ' + str(camera_ID))

        self.mutex.release()

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        self.mutex.acquire()
        if im.cameraID != 0 and im.cameraID != 1:
            self.data_received[im.cameraID] = im
        self.mutex.release()

    # ===================================================================
    # ===================================================================

    ######################
    # From the RoboCompAdminBridge you can call this methods:
    # self.adminbridge_proxy.activateSensor(...)
    # self.adminbridge_proxy.stopSensor(...)
