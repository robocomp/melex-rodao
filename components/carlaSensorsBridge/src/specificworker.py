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
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from numpy import random
import pygame
from Hud import HUD
from carlaWorld import World
from DualControl import DualControl
try:
    sys.path.append(glob.glob('/home/robocomp/carla/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:6

import carla




client = carla.Client('localhost', 2000)
client.set_timeout(15.0)
# world = client.load_world('CampusV3')
# world = client.load_world('CampusVersionDos')
world = client.get_world()

carla_map = world.get_map()
blueprint_library = world.get_blueprint_library()


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map

        self.Period = 0
        self.pygame_width = 1280
        self.pygame_height = 720

        pygame.init()
        pygame.font.init()
        self.display = pygame.display.set_mode(
            (self.pygame_width, self.pygame_height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.world = None

        hud = HUD(carla_map, self.pygame_width, self.pygame_height)
        self.world = World(world, carla_map, hud)
        self.controller = DualControl(self.world)


        self.clock = pygame.time.Clock()

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

        self.world.destroy()

        cv2.destroyAllWindows()

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        # print('SpecificWorker.compute...')
        self.clock.tick_busy_loop(60)
        if self.controller.parse_events(self.world, self.clock):
            return
        self.world.tick(self.clock)
        self.world.render(self.display)
        pygame.display.flip()

        try:
            for i in range(0, len(self.world.camera_manager.sensor_list)):
                # print('------------- RGB -------------')
                cm_timestamp, cm_frame, cm_sensor_name, cm_sensor_data = self.world.camera_manager.cm_queue.get()
                self.world.camera_manager.show_img(cm_sensor_data, cm_sensor_name)

                # print( f'TimeStamp: {cm_timestamp}   Frame: {cm_frame}   Sensor: {cm_sensor_name}     Shape:{cm_sensor_data.shape}')

                # print('\n')
                pass

        except Empty:
            print('No data found')


        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)


