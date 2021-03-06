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
from genericworker import *
import traceback

import pygame
from PySide2.QtCore import QTimer, Signal
from PySide2.QtWidgets import QApplication

from DualControl import DualControl
from HUD import HUD
from Logger import Logger
from SensorManager import CameraManager, GNSSSensor, IMUSensor


class SpecificWorker(GenericWorker):
    logger_signal = Signal(str, str, str)

    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)

        self.width = 1280
        self.height = 720

        pygame.init()
        pygame.font.init()

        self.display = pygame.display.set_mode(
            (self.width, self.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.camera_manager = CameraManager(self.width, self.height)
        self.gnss_sensor = GNSSSensor()
        self.imu_sensor = IMUSensor()
        self.hud = HUD(self.width, self.height, self.gnss_sensor, self.imu_sensor)
        self.controller = None
        self.clock = pygame.time.Clock()

        data_to_save = {
            'control': ['Time', 'Throttle', 'Steer', 'Brake', 'Gear', 'Handbrake', 'Reverse', 'Manualgear'],
            'communication': ['Time', 'CommunicationTime']
        }
        self.logger = Logger(self.melexlogger_proxy, 'carlaRemoteControl', data_to_save)
        self.logger_signal.connect(self.logger.publish_to_logger)

        self.Period = 0

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        try:
            wheel_config = params["wheel"]
            self.controller = DualControl(self.camera_manager, self.hud, wheel_config,
                                          self.carlavehiclecontrol_proxy)

        except:
            traceback.print_exc()
            print("Error reading config params")
        return True

    @QtCore.Slot()
    def compute(self):
        self.clock.tick_busy_loop(60)
        if self.controller and self.controller.parse_events(self.clock):
            exit(-1)

        if self.controller.car_moved():
            control, elapsed_time = self.controller.publish_vehicle_control()
            control_array = [control.throttle, control.steer, control.brake, control.gear, control.handbrake,
                             control.reverse,
                             control.manualgear]
            data = ';'.join(map(str, control_array))
            self.logger_signal.emit('control', 'compute', data)
            self.logger_signal.emit('communication', 'compute', str(elapsed_time))

            self.hud.tick(self, self.clock, control)
        self.camera_manager.render(self.display)
        self.hud.render(self.display)
        pygame.display.flip()

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CarCameraRGBD_pushRGBD(self, im, dep):
        self.camera_manager.images_received[im.cameraID] = im

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
        self.imu_sensor.update(imuData.accelerometer, imuData.gyroscope, imuData.compass, imuData.frame,
                               imuData.timestamp)

    # ===================================================================
    # ===================================================================



    ######################
    # From the RoboCompCarlaVehicleControl you can call this methods:
    # self.carlavehiclecontrol_proxy.updateVehicleControl(...)

    ######################
    # From the RoboCompCarlaVehicleControl you can use this types:
    # RoboCompCarlaVehicleControl.VehicleControl

    ######################
    # From the RoboCompMelexLogger you can publish calling this methods:
    # self.melexlogger_proxy.createNamespace(...)
    # self.melexlogger_proxy.sendMessage(...)

    ######################
    # From the RoboCompMelexLogger you can use this types:
    # RoboCompMelexLogger.LogMessage
    # RoboCompMelexLogger.LogNamespace

    ######################
    # From the RoboCompCarlaSensors you can use this types:
    # RoboCompCarlaSensors.IMU
    # RoboCompCarlaSensors.GNSS

