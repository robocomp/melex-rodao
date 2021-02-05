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
import traceback

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from multiprocessing import SimpleQueue
import numpy as np
import cv2
import pygame

from SensorManager import CameraManager, GNSSSensor, IMUSensor
from DualControl import DualControl
from HUD import HUD


# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewerser
# import librobocomp_innermodel

class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 0

        self.contFPS = 0
        self.start = time.time()

        self.width = 1280
        self.height = 720
        self.data_queue = SimpleQueue()

        pygame.init()
        pygame.font.init()

        self.display = pygame.display.set_mode(
            (self.width, self.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.camera_manager = CameraManager(self.width, self.height)
        self.gnss_sensor = GNSSSensor()
        self.imu_sensor = IMUSensor()
        self.hud = HUD(self.width, self.height, self.gnss_sensor, self.imu_sensor)
        self.controller = DualControl(self.camera_manager, self.hud,
                                      self.carlavehiclecontrol_proxy)
        self.clock = pygame.time.Clock()

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        self.clock.tick_busy_loop(60)

        # try:
        #     cm_image, cm_width, cm_height, cm_cameraID = self.data_queue.get()
        #     self.camera_manager.show_img(cm_image, cm_width, cm_height, cm_cameraID)
        # except Exception as e:
        #     print(e)

        if self.controller.parse_events(self.clock):
            exit(-1)

        control = self.controller.publish_vehicle_control()
        self.hud.tick(self, self.clock, control)
        self.camera_manager.render(self.display)
        self.hud.render(self.display)
        pygame.display.flip()

        # self.world.tick(self.clock)

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        # if time.time() - self.start > 1:
        #     print("FPS:", self.contFPS)
        #     self.start = time.time()
        #     self.contFPS = 0
        # self.contFPS += 1

        # self.data_queue.put((im.image, im.width, im.height,im.cameraID))
        # self.data_queue.put(im)
        self.camera_manager.show_img_noqueue(im.image, im.width, im.height, im.cameraID)

    #
    # SUBSCRIPTION to updateSensorGNSS method from CarlaSensors interface
    #
    def CarlaSensors_updateSensorGNSS(self, gnssData):
        self.gnss_sensor.update(gnssData.latitude, gnssData.longitude, gnssData.altitude, gnssData.frame,
                                gnssData.timestamp)

    #
    # SUBSCRIPTION to updateSensorIMU method from CarlaSensors interface
    #
    def CarlaSensors_updateSensorIMU(self, imuData):
        self.imu_sensor.update(imuData.accelerometer, imuData.gyroscope, imuData.compass, imuData.frame, imuData.timestamp)

    # ===================================================================
    # ===================================================================
    ######################
    # From the RoboCompCarlaVehicleControl you can publish calling this methods:
    # self.carlavehiclecontrol_proxy.updateVehicleControl(...)

    ######################
    # From the RoboCompCarlaVehicleControl you can use this types:
    # RoboCompCarlaVehicleControl.VehicleControl
