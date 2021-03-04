# -*- coding: utf-8 -*-
from datetime import datetime
import os
import sys

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWidgets import QApplication, QMainWindow
from pyqtgraph import GraphicsLayoutWidget, DateAxisItem

RESULTS_DIR = '/home/robocomp/robocomp/components/melex-rodao/files/results/'


class VelocityPlotWidget(pg.GraphicsLayoutWidget):
    def __init__(self, file_dir):
        super(VelocityPlotWidget, self).__init__(show=True)
        self.df1 = pd.read_csv(os.path.join(file_dir, 'velocity.csv'),
                          delimiter=';', skiprows=0, low_memory=False)
        self.df2 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_velocity.csv'),
                          delimiter=';', skiprows=0, low_memory=False)
        self.plot1 = self.addPlot(row=1, col=0)
        self.data1 = self.df1['prom_velocity'].to_numpy()
        self.data2 = self.df2['Velocity'].to_numpy()
        self.label = pg.LabelItem(justify='right')
        self.addItem(self.label,row=0, col=0)

        self.plot1.plot(self.df1['Time'], self.data1, pen="r")
        self.plot1.plot(self.df2['Time'], self.data2, pen="g")
        axis = pg.DateAxisItem()
        self.plot1.setAxisItems({'bottom': axis})

        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)
        self.region.setRegion([self.df1['Time'][0], self.df1['Time'].iloc[-1]])


        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot1.addItem(self.vLine, ignoreBounds=True)
        self.plot1.addItem(self.hLine, ignoreBounds=True)

        self.proxy = pg.SignalProxy(self.plot1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)


    def mouseMoved(self, evt):
        vb = self.plot1.vb
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.plot1.sceneBoundingRect().contains(pos):
            mousePoint = vb.mapSceneToView(pos)
            xpoint = mousePoint.x()

            nearest1 = self.find_nearest(self.df1['Time'], xpoint)
            index1 = self.df1.index[self.df1['Time'] == nearest1].tolist()[0]

            nearest2 = self.find_nearest(self.df2['Time'], xpoint)
            index2 = self.df2.index[self.df2['Time'] == nearest2].tolist()[0]

            datetime_ = datetime.fromtimestamp(mousePoint.x()).strftime("%H:%M:%S")

            self.label.setText(
                "<span style='font-size: 12pt'>x=%s,   <span style='color: red'>Calculated=%0.1f</span>,   "
                "<span style='color: green'>Carla=%0.1f</span>" % (
                    datetime_, self.data1[index1], self.data2[index2]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())



    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]


class MelexStatistics(QMainWindow):
    def __init__(self):
        super(MelexStatistics, self).__init__()
        self.docks = {}
        dialog = QtWidgets.QFileDialog(caption="Select result directory", directory=RESULTS_DIR)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.exec_()
        for dirpath, dnames, fnames in os.walk(dialog.selectedFiles()[0]):
            for f in fnames:
                if "carlaBridge_velocity" in f:
                    self.create_velocity_dock(dirpath, f)



    def create_velocity_dock(self, dirpath, f):
        dock = QtWidgets.QDockWidget("Velocity")
        plot_widget = VelocityPlotWidget(dirpath)
        dock.setWidget(plot_widget)
        dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
        self.docks[f] = dock
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock)


if __name__ == '__main__':

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MelexStatistics()
    window.show()
    app.exec_()
