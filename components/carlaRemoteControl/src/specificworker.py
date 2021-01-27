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
import pygame

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *

from Hud import HUD
from carlaWorld import World
from DualControl import DualControl

import carla

try:
    sys.path.append(glob.glob('/home/robocomp/carla/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.load_world('CampusAvanz')
carla_map = world.get_map()

class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        global world, carla_map
        self.Period = 10
        self.width = 1280
        self.height = 720

        pygame.init()
        pygame.font.init()
        self.world = None

        self.display = pygame.display.set_mode(
            (self.width, self.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(carla_map, self.width, self.height)
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

    def setParams(self, params):
        return True


    @QtCore.Slot()
    def compute(self):
        self. clock.tick_busy_loop(60)
        if self.controller.parse_events(self.world, self.clock):
            return
        self.world.tick(self.clock)
        self.world.render(self.display)
        pygame.display.flip()

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)




