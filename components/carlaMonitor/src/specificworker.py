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
import math
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

        self.cameras_GNSS_localization = {
            # id : [(latitude, longitude), dist_to_car]
            1: [(39.47951795840331, -6.343213688035427), 0],
            2: [(39.4794451943053, -6.3425991738366045), 0],
            3: [(39.479349972033106, -6.341949744036231), 0],
            4: [(39.47914156049626, -6.3412211722981695), 0],
            5: [(39.4797560132987, -6.339405446028102), 0],
            6: [(39.4797560132987, -6.339619710987503), 0],
            7: [(39.48029769743266, -6.342937854949663), 0],
            8: [(39.48029051094454, -6.343020488491904), 0],
            9: [(39.480330934969174, -6.343118252109651), 0],
            10: [(39.47996532127118, -6.344649882084023), 0],
            11: [(39.48011893315282, -6.344228567462022), 0],
            12: [(39.480092882041475, -6.344149425535433), 0],
            13: [(39.480092882041475, -6.34414942553543), 0]
        }

        self.init_ui()

        # self.cameras_widget_dict = [
        #     0: [None, None, self.main_widget.ve_camera_state_light],
        #     5: [self.main_widget.camera1_image, self.main_widget.camera1_switch, self.main_widget.state_light1],
        #     7: [self.main_widget.camera2_image, self.main_widget.camera2_switch, self.main_widget.state_light2],
        # ]

        self.cameras_widget_array = [
            [self.main_widget.camera1_image, self.main_widget.camera1_switch, self.main_widget.state_light1],
            [self.main_widget.camera2_image, self.main_widget.camera2_switch, self.main_widget.state_light2],
        ]

        self.is_sensor_active = {}
        self.timers = {}
        self.camera_timer_dict = {}
        self.camera_data_received = {}

        self.sensor_downtime = 1000
        self.Period = 1000 / 24
        if startup_check:
            self.startup_check()
        else:
            self.initialize_sensor_timers()

            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def initialize_sensor_timers(self):
        timeout_lambdas = {
            "stimer": lambda: self.main_widget.update_map_position((self.latitude, self.longitude)),
            "imu_timer": lambda: self.main_widget.imu_state_light.turn_off(),
            "gps_timer": lambda: self.main_widget.gps_state_light.turn_off(),
            "camera1_timer": lambda: self.main_widget.state_light1.turn_off(),
            "camera2_timer": lambda: self.main_widget.state_light2.turn_off(),
            "ve_camera_timer": lambda: self.main_widget.ve_camera_state_light.turn_off(),
        }
        for timer_name, timer_lambda in timeout_lambdas.items():
            self.timers[timer_name] = QTimer()
            self.timers[timer_name].timeout.connect(timer_lambda)
            self.timers[timer_name].start(self.sensor_downtime)

        self.camera_timer_dict = {
            0: self.timers["ve_camera_timer"],
            5: self.timers["camera1_timer"],
            7: self.timers["camera2_timer"],
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

        # for id, data_received in self.camera_data_received.items():
        #     if data_received:
        #         self.cameras_widget_dict[id][2].turn_on()
        #         self.camera_timer_dict[id].start(self.sensor_downtime)
        #         self.camera_data_received[id] = False

    def compute_coord_distance(self, cameraID, camera_pose):
        R = 6373.0
        lat1, lon1 = camera_pose
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(self.latitude)
        lon2 = math.radians(self.longitude)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        self.cameras_GNSS_localization[cameraID][1] = distance

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        return True

    def show_img_opencv(self, data):
        array = np.frombuffer(data.image, dtype=np.dtype("uint8"))
        array = np.reshape(array, (data.height, data.width, 4))
        array = array[:, :, :3]

        window_name = "camera" + str(data.cameraID)
        cv2.imshow(window_name, array)
        cv2.waitKey(1)

    @QtCore.Slot()
    def compute(self):
        self.mutex.acquire()

        self.admin_sensor_state_lights()

        nearest_camera_ids = self.get_nearest_cameras()

        for camera_widget,camera_label,_ in self.cameras_widget_array:
            for cam_id in nearest_camera_ids:
                if cam_id in self.images_received:
                    camera_data = self.images_received[cam_id]
                    if cam_id in self.is_sensor_active and self.is_sensor_active[cam_id]:
                            array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
                            array = np.reshape(array, (camera_data.height, camera_data.width, 4))
                            qImg = QImage(array, array.shape[1], array.shape[0], array.strides[0], QImage.Format_ARGB32)
                    else:
                        qImg = QImage(camera_data.width, camera_data.height, QImage.Format_ARGB32)
                        qImg.fill(qRgb(0, 0, 0))

                    if cam_id not in self.current_cams_ids:
                        camera_widget.setPixmap(QPixmap(qImg))
                        camera_label.setText('Cámara ' + str(cam_id))

        for camera_ID, camera_data in self.images_received.items():
            self.show_img_opencv(camera_data)

            # if camera_data is None:
            #     continue
            #
            # if self.is_sensor_active[camera_ID]:
            #     array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
            #     array = np.reshape(array, (camera_data.height, camera_data.width, 4))
            #     qImg = QImage(array, array.shape[1], array.shape[0], array.strides[0], QImage.Format_ARGB32)
            #
            # else:
            #     qImg = QImage(camera_data.width, camera_data.height, QImage.Format_ARGB32)
            #     qImg.fill(qRgb(0, 0, 0))
            #
            # # self.cameras_widget_dict[camera_ID][0].setPixmap(QPixmap(qImg))
            # # self.cameras_widget_dict[camera_ID][1].setText('Cámara ' + str(camera_ID))

        self.mutex.release()

        return True

    def get_nearest_cameras(self):
        for cameraID, pose in self.cameras_GNSS_localization.items():
            self.compute_coord_distance(cameraID, pose[0])
        cameras_sorted = sorted(self.cameras_GNSS_localization.items(), key=lambda x: x[1][1])

        ids = [x[0] for x in cameras_sorted]

        return ids

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        self.mutex.acquire()

        self.is_sensor_active[im.cameraID] = True
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
