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
import csv
from datetime import datetime

from PySide2.QtCore import QTimer, Signal
from PySide2.QtWidgets import QApplication
from genericworker import *


# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# sys.path.append('/opt/robocomp/lib')
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel

class SpecificWorker(GenericWorker):
    save_signal = Signal(str, object)

    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.headers_dict = {}
        self.save_signal.connect(self.save_data)

        # Create directory to store the results
        results_directory = '/home/robocomp/robocomp/components/melex-rodao/files/results'
        if not os.path.isdir(results_directory):
            os.mkdir(results_directory)
        date = datetime.strftime(datetime.now(), "%y%m%d_%H%M")  # %S
        self.directory = os.path.join(results_directory, "test_" + date)

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

        self.Period = 2000
        if startup_check:
            self.startup_check()
        else:
            self.timer.start(self.Period)

    def save_data(self, namespace, data_list):

        file_name = namespace + '.csv'
        file_dir = os.path.join(self.directory, file_name)

        if not os.path.isfile(file_dir):
            if namespace in self.headers_dict.keys():
                with open(file_dir, 'w') as csvFile:
                    writer = csv.writer(csvFile, delimiter=';')
                    writer.writerow(
                        self.headers_dict[namespace])
                csvFile.close()
        with open(file_dir, 'a') as csvFile:
            writer = csv.writer(csvFile, delimiter=';')
            writer.writerow(data_list)
        csvFile.close()

    def __del__(self):
        print('SpecificWorker destructor')

    def setParams(self, params):
        return True

    @QtCore.Slot()
    def compute(self):
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component SubscribesTo ================
    # ===================================================================

    #
    # SUBSCRIPTION to createNamespace method from MelexLogger interface
    #
    def MelexLogger_createNamespace(self, logn):
        filename = logn.sender + '_' + logn.namespace
        headers = logn.headers
        print(filename, headers)
        self.headers_dict[filename] = headers

    #
    # SUBSCRIPTION to sendMessage method from MelexLogger interface
    #
    def MelexLogger_sendMessage(self, m):
        filename = m.sender + '_' + m.namespace
        data = m.message.split(';')
        data.insert(0, m.timeStamp)
        self.save_signal.emit(filename, data)

    # ===================================================================
    # ===================================================================

    ######################
    # From the RoboCompMelexLogger you can use this types:
    # RoboCompMelexLogger.LogMessage
    # RoboCompMelexLogger.LogNamespace
