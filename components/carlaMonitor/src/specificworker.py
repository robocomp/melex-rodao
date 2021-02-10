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
import pygame
from SensorManager import CameraManager
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *

from threading import Lock

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel

class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.mutex = Lock()

        self.pygame_width = 1280
        self.pygame_height = 720

        # pygame.init()
        # pygame.font.init()
        #
        # self.display = pygame.display.set_mode(
        #     (self.pygame_width, self.pygame_height),
        #     pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.camera_manager = CameraManager(self.mutex)

        self.Period = 0
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
        # self.camera_manager.render(self.display)
        self.camera_manager.render()
        # pygame.display.flip()

        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)


    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        print('Received image from camera ', im.cameraID)
        self.mutex.acquire()
        if im.cameraID != 5 and im.cameraID != 7:
            self.camera_manager.images_received[im.cameraID] = im
        self.mutex.release()

    # ===================================================================
    # ===================================================================



