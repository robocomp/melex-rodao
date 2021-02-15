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
import random
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

        self.images_received = {}

        self.latitude = 39.47978558137163
        self.longitude = -6.3421153169747795
        self.altitude = 0
        self.gps_data_received = False

        self.accelerometer = 0
        self.gyroscope = 0
        self.compass = 0
        self.imu_data_received = False

        self.init_ui()

        self.cameras_widget_dict = {
            0: [None, None, self.main_widget.ve_camera_state_light],
            5: [self.main_widget.camera1_image, self.main_widget.camera1_switch, self.main_widget.state_light1],
            7: [self.main_widget.camera2_image, self.main_widget.camera2_switch, self.main_widget.state_light2],
        }

        self.is_sensor_active = {
            5: True,
            7: True,
        }

        self.camera_timer_dict = {}
        self.camera_data_received = {}

        self.sensor_downtime = 1000
        self.Period = 0
        if startup_check:
            self.startup_check()
        else:
            self.initialize_sensor_timers()

            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def initialize_sensor_timers(self):
        self.stimer = QTimer()
        self.stimer.timeout.connect(lambda: self.main_widget.update_map_position((self.latitude, self.longitude)))
        self.stimer.start(self.sensor_downtime)

        self.imu_timer = QTimer()
        self.imu_timer.timeout.connect(lambda: self.main_widget.imu_state_light.turn_off())
        self.imu_timer.start(self.sensor_downtime)

        self.gps_timer = QTimer()
        self.gps_timer.timeout.connect(lambda: self.main_widget.gps_state_light.turn_off())
        self.gps_timer.start(self.sensor_downtime)

        self.camera1_timer = QTimer()
        self.camera1_timer.timeout.connect(lambda: self.main_widget.state_light1.turn_off())
        self.camera1_timer.start(self.sensor_downtime)

        self.camera2_timer = QTimer()
        self.camera2_timer.timeout.connect(lambda: self.main_widget.state_light2.turn_off())
        self.camera2_timer.start(self.sensor_downtime)

        self.ve_camera_timer = QTimer()
        self.ve_camera_timer.timeout.connect(lambda: self.main_widget.ve_camera_state_light.turn_off())
        self.ve_camera_timer.start(self.sensor_downtime)

        self.camera_timer_dict = {
            0: self.ve_camera_timer,
            5: self.camera1_timer,
            7: self.camera2_timer,
        }

    def init_ui(self):
        self.main_widget = ControlWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.camera1_switch.stateChanged.connect(self.change_camera_state)
        self.main_widget.camera2_switch.stateChanged.connect(self.change_camera_state)
        self.main_widget.update_map_position((self.latitude, self.longitude))

    def change_camera_state(self):
        for id, [_, switch, _] in self.cameras_widget_dict.items():
            if switch is None:
                continue
            elif switch.isChecked():
                if not self.is_sensor_active[id]:
                    self.adminbridge_proxy.activateSensor(id)
                    self.is_sensor_active[id] = True
            else:
                if self.is_sensor_active[id]:
                    self.adminbridge_proxy.stopSensor(id)
                    self.is_sensor_active[id] = False

    def admin_sensor_state_lights(self):
        if self.imu_data_received:
            self.main_widget.imu_state_light.turn_on()
            self.imu_timer.start(self.sensor_downtime)
            self.imu_data_received = False

        if self.gps_data_received:
            self.main_widget.gps_state_light.turn_on()
            self.gps_timer.start(self.sensor_downtime)
            self.gps_data_received = False

        for id, data_received in self.camera_data_received.items():
            if data_received:
                self.cameras_widget_dict[id][2].turn_on()
                self.camera_timer_dict[id].start(self.sensor_downtime)
                self.camera_data_received[id] = False


    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        return True



    @QtCore.Slot()
    def compute(self):
        self.mutex.acquire()

        self.admin_sensor_state_lights()

        for camera_ID, camera_data in self.images_received.items():
            if camera_data is None:
                continue

            if self.is_sensor_active[camera_ID]:
                array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
                array = np.reshape(array, (camera_data.height, camera_data.width, 4))
                qImg = QImage(array, array.shape[1], array.shape[0], array.strides[0], QImage.Format_ARGB32)

            else:
                qImg = QImage(camera_data.width, camera_data.height, QImage.Format_ARGB32)
                qImg.fill(qRgb(0, 0, 0))

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

        self.camera_data_received[im.cameraID] = True

        if im.cameraID != 0:
            self.images_received[im.cameraID] = im
        self.mutex.release()

    #
    # SUBSCRIPTION to updateSensorGNSS method from CarlaSensors interface
    #
    def CarlaSensors_updateSensorGNSS(self, gnssData):
        self.mutex.acquire()

        self.latitude = gnssData.latitude
        self.longitude = gnssData.longitude
        self.altitude = gnssData.altitude

        self.gps_data_received = True

        self.mutex.release()

    #
    # SUBSCRIPTION to updateSensorIMU method from CarlaSensors interface
    #
    def CarlaSensors_updateSensorIMU(self, imuData):
        self.mutex.acquire()

        self.accelerometer = imuData.accelerometer
        self.gyroscope = imuData.gyroscope
        self.compass = imuData.compass
        self.imu_data_received = True

        self.mutex.release()

    # ===================================================================
    # ===================================================================

    ######################
    # From the RoboCompAdminBridge you can call this methods:
    # self.adminbridge_proxy.activateSensor(...)
    # self.adminbridge_proxy.stopSensor(...)

    ######################
    # From the RoboCompCarlaSensors you can use this types:
    # RoboCompCarlaSensors.IMU
    # RoboCompCarlaSensors.GNSS
