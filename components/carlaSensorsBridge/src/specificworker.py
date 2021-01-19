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

import glob
import os
import sys
from queue import Empty

import cv2
from CameraManager import CameraManager
from GNSS import GnssSensor
from IMU import IMUSensor
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from numpy import random

try:
    sys.path.append(glob.glob('/home/robocomp/carla/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

client = carla.Client('localhost', 2000)
client.set_timeout(15.0)
world = client.load_world('CampusAvanz')
# world = client.load_world('CampusVersionDos')
# world = client.get_world()

carla_map = world.get_map()
blueprint_library = world.get_blueprint_library()

blueprint = random.choice(blueprint_library.filter('vehicle.*'))
spawn_point = random.choice(carla_map.get_spawn_points())
vehicle = world.spawn_actor(blueprint, spawn_point)
vehicle.set_autopilot(True)



class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map, blueprint_library, vehicle

        self.Period = 50
        self.img_width = 480
        self.img_height = 360

        self.world = world
        self.blueprint_library = blueprint_library
        self.vehicle = vehicle

        self.gnss_sensor = GnssSensor(self.vehicle)
        self.imu_sensor = IMUSensor(self.vehicle)
        self.camera_manager = CameraManager(self.blueprint_library, self.vehicle, self.img_width, self.img_height)

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')
        cv2.destroyAllWindows()
        for sensor in self.sensor_list:
            sensor.destroy()

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        # print('SpecificWorker.compute...')
        try:
            for i in range(0, len(self.camera_manager.sensor_list)):
                print('------------- RGB -------------')
                cm_timestamp, cm_frame, cm_sensor_name, cm_sensor_data = self.camera_manager.cm_queue.get()
                self.camera_manager.show_img(cm_sensor_data, cm_sensor_name)
                print(
                    f'TimeStamp: {cm_timestamp}   Frame: {cm_frame}   Sensor: {cm_sensor_name}     Shape:{cm_sensor_data.shape}')
                print('------------- GNSS -------------')
                gnss_timestamp, gnss_frame, gnss_lat, gnss_lon = self.gnss_sensor.gnss_queue.get()
                print(f'TimeStamp: {gnss_timestamp}   Frame: {gnss_frame}  Latitud: {gnss_lat} Longitud: {gnss_lon}')
                print('------------- IMU -------------')
                imu_timestamp, imu_frame, imu_accelerometer, imu_gyroscope, imu_compass = self.imu_sensor.imu_queue.get()
                print(f'TimeStamp: {imu_timestamp}   Frame:{imu_frame}  Accelerometer: {imu_accelerometer}   '
                      f'Gyroscope:{imu_gyroscope} Compass: {imu_compass} ')

                print('\n')

        except Empty:
            print('No data found')
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)


