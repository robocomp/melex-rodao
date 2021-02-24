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
import time
from threading import Lock

import cv2
import numpy as np
import yaml
from PySide2.QtCore import QTimer
from PySide2.QtGui import QImage
from PySide2.QtGui import QPixmap, qRgb
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Signal

from SaveResults import SaveResults
from genericworker import *
from widgets.control import ControlWidget


class SpecificWorker(GenericWorker):
    save_signal = Signal(str, object)

    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.mutex = Lock()

        self.results = SaveResults()
        self.save_signal.connect(self.results.save_data)

        self.images_received = {}

        self.latitude = 0
        self.longitude = 0
        self.altitude = 0
        self.gps_data_received = False

        self.accelerometer = 0
        self.gyroscope = 0
        self.compass = 0
        self.imu_data_received = False

        yaml_file = open('/home/robolab/robocomp/components/melex-rodao/etc/cameras.yml')
        self.pose_cameras_dict = yaml.load(yaml_file)

        self.car_cameras_dist = {}

        self.init_ui()

        self.cameras_widget_dict = {
            'widget1': [self.main_widget.camera1_image, self.main_widget.camera1_switch, self.main_widget.state_light1],
            'widget2': [self.main_widget.camera2_image, self.main_widget.camera2_switch, self.main_widget.state_light2],

        }
        # This relates the index of cameras widgets with
        self.current_cams_ids = dict.fromkeys(self.cameras_widget_dict.keys())
        self.current_cams_ids['vehicle'] = 0
        num_cams = 13
        self.is_sensor_active = {}
        for n in range(num_cams):
            self.is_sensor_active[n] = False

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
            'widget1': self.timers["camera1_timer"],
            'widget2': self.timers["camera2_timer"],
        }

    def init_ui(self):
        self.main_widget = ControlWidget()
        self.setCentralWidget(self.main_widget)
        self.main_widget.camera1_switch.stateChanged.connect(self.change_camera_state)
        self.main_widget.camera2_switch.stateChanged.connect(self.change_camera_state)
        self.main_widget.update_map_position((self.latitude, self.longitude))

    # TODO ¿Hay que pasar por aqui cada vez que se cambie automáticamente de cámara?
    def change_camera_state(self):
        for widget_name, (_, switch, _) in self.cameras_widget_dict.items():
            camID = self.current_cams_ids[widget_name]
            if switch.isChecked():
                if not self.is_sensor_active[camID]:
                    self.adminbridge_proxy.activateSensor(camID)
                    self.is_sensor_active[camID] = True
            else:
                if self.is_sensor_active[camID]:
                    self.adminbridge_proxy.stopSensor(camID)
                    self.is_sensor_active[camID] = False

    def admin_sensor_state_lights(self):
        if self.imu_data_received:
            self.main_widget.imu_state_light.turn_on()
            self.timers['imu_timer'].start(self.sensor_downtime)
            self.imu_data_received = False

        if self.gps_data_received:
            self.main_widget.gps_state_light.turn_on()
            self.timers['gps_timer'].start(self.sensor_downtime)
            self.gps_data_received = False

        for widget, camID in self.current_cams_ids.items():
            if camID in self.camera_data_received.keys() and self.camera_data_received[camID]:
                if camID == 0:
                    self.main_widget.ve_camera_state_light.turn_on()
                    self.timers['ve_camera_timer'].start(self.sensor_downtime)
                else:
                    self.cameras_widget_dict[widget][2].turn_on()
                    self.camera_timer_dict[widget].start(self.sensor_downtime)
                self.camera_data_received[camID] = False

    def compute_coord_distance(self, cameraID, lat1, lon1):
        R = 6373.0
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(self.latitude)
        lon2 = math.radians(self.longitude)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        self.car_cameras_dist[cameraID] = distance

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

        nearest_camera_ids = self.get_nearest_cameras()
        self.admin_cameras(nearest_camera_ids)

        for widget_name, (camera_widget, camera_label, _) in sorted(self.cameras_widget_dict.items()):
            for cam_id in nearest_camera_ids:
                if cam_id in self.images_received:
                    if cam_id not in self.current_cams_ids.values():
                        self.current_cams_ids[widget_name] = cam_id
                        self.update_widgets(cam_id, camera_widget, camera_label)
                        break

                    elif self.current_cams_ids[widget_name] == cam_id:
                        self.update_widgets(cam_id, camera_widget, camera_label)
                        break

                    else:
                        continue

        self.admin_sensor_state_lights()
        self.mutex.release()

        return True

    def update_widgets(self, cam_id, camera_widget, camera_label):
        camera_data = self.images_received[cam_id]

        if cam_id in self.is_sensor_active.keys() and self.is_sensor_active[cam_id]:
            array = np.frombuffer(camera_data.image, dtype=np.dtype("uint8"))
            array = np.reshape(array, (camera_data.height, camera_data.width, 4))
            qImg = QImage(array, array.shape[1], array.shape[0], array.strides[0], QImage.Format_ARGB32)
        else:
            qImg = QImage(camera_data.width, camera_data.height, QImage.Format_ARGB32)
            qImg.fill(qRgb(0, 0, 0))

        camera_widget.setPixmap(QPixmap(qImg))
        camera_label.setText(self.pose_cameras_dict[cam_id]['name'])

    def get_nearest_cameras(self):
        for cameraID, pose in self.pose_cameras_dict.items():
            self.compute_coord_distance(cameraID, pose['latitude'], pose['longitude'])
        cameras_sorted = dict(sorted(self.car_cameras_dist.items(), key=lambda item: item[1]))

        ids = [x for x in cameras_sorted.keys()]

        return ids

    def admin_cameras(self, nearest_camera_ids):
        for camID in nearest_camera_ids[:2]:
            if not self.is_sensor_active[camID]:
                self.adminbridge_proxy.activateSensor(camID)
                self.is_sensor_active[camID] = True

        for camID in nearest_camera_ids[2:]:
            if self.is_sensor_active[camID]:
                self.is_sensor_active[camID] = False
                self.adminbridge_proxy.stopSensor(camID)

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        self.mutex.acquire()

        # self.is_sensor_active[im.cameraID] = True
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

        self.save_signal.emit('gnss', [time.time(), self.latitude, self.longitude, self.altitude])

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
        self.save_signal.emit('imu', [time.time(), self.accelerometer, self.gyroscope, self.compass])

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
