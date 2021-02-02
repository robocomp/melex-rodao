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

from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication
from genericworker import *
from multiprocessing import SimpleQueue
import numpy as np
import cv2

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewerser
# import librobocomp_innermodel

class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 0
        self.data_queue = SimpleQueue()
        self.contFPS = 0
        self.start = time.time()

        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        #try:
        #	self.innermodel = InnerModel(params["InnerModelPath"])
        #except:
        #	traceback.print_exc()
        #	print("Error reading config params")
        return True

    def show_img(self, im):
        array = np.frombuffer(im.image, dtype=np.dtype("uint8"))
        array = np.reshape(array, (im.height, im.width, 4))
        array = array[:, :, :3]
        window_name = "camera"+str(im.cameraID)
        cv2.imshow(window_name, array)
        cv2.waitKey(1)

    @QtCore.Slot()
    def compute(self):
        pass
        # print('compute')
        try:
            self.show_img(self.data_queue.get())
        except Exception as e:
            print(e)
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)


    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to pushRGBD method from CameraRGBDSimplePub interface
    #
    def CameraRGBDSimplePub_pushRGBD(self, im, dep):
        if time.time() - self.start > 1:
            print("FPS:", self.contFPS)
            self.start = time.time()
            self.contFPS = 0
        self.contFPS += 1

        self.data_queue.put((im))

    # ===================================================================
    # ===================================================================



