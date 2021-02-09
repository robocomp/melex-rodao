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
import pygame
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from numpy import random
import re
import random
import time

try:
    # sys.path.append(glob.glob('/home/robocomp/robocomp/components/melex-rodao/files/carla/carla-*%d.%d-%s.egg' % (
    # sys.path.append(glob.glob('/home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
    sys.path.append(glob.glob('/home/robolab/carla_build/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    6

import carla
from CameraManager import CameraManager

client = carla.Client('localhost', 2000)
client.set_timeout(30.0)
print('Loading world...')
# world = client.load_world('CampusV3')
world = client.get_world()
print('Done')

print(f' Client version {client.get_client_version()}')
print(f' Server version {client.get_server_version()}')

carla_map = world.get_map()
blueprint_library = world.get_blueprint_library()


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map, blueprint_library

        self.Period = 0
        self.world = world
        self.carla_map = carla_map
        self.blueprint_library = blueprint_library


        self.server_fps = 0
        self._server_clock = pygame.time.Clock()
        self.world.on_tick(self.on_world_tick)

        self.camera_manager = CameraManager(self.world, self.blueprint_library, self.camerargbdsimplepub_proxy)
        # Connect to the callback to get server fps
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

        self.destroy()
        cv2.destroyAllWindows()

    def setParams(self, params):
        return True

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        print('Server FPS', int(self.server_fps))

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.vehicle.get_world().set_weather(preset[0])

    def destroy(self):
        for sensor in self.camera_manager.sensor_list:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.vehicle is not None:
            self.vehicle.destroy()

    @QtCore.Slot()
    def compute(self):
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

# ===================================================================
# ===================================================================

######################
# From the RoboCompCameraRGBDSimplePub you can publish calling this methods:
# self.camerargbdsimplepub_proxy.pushRGBD(...)
