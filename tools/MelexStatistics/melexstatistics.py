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

web_colors = ["Red", "Yellow", "Cyan", "Blue", "Magenta"]
qt_colors = ["r", "y", "g", "b", "m"]


class AbstractPlotWidget(pg.GraphicsLayoutWidget):
    def __init__(self):
        super(AbstractPlotWidget, self).__init__(show=True)
        self.plots = {}
        self._current_color = 0
        self.x_axis_name = ""
        self.plot_area = self.addPlot(row=1, col=0)
        self.label = pg.LabelItem(justify='right')
        self.addItem(self.label, row=0, col=0)
        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot_area.addItem(self.vLine, ignoreBounds=True)
        self.plot_area.addItem(self.hLine, ignoreBounds=True)

        self.proxy = pg.SignalProxy(self.plot_area.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        axis = pg.DateAxisItem()
        self.plot_area.setAxisItems({'bottom': axis})

        self.proxy = pg.SignalProxy(self.plot_area.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

    def mouseMoved(self, evt):
        vb = self.plot_area.vb
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.plot_area.sceneBoundingRect().contains(pos):
            mousePoint = vb.mapSceneToView(pos)
            xpoint = mousePoint.x()
            data_frames_string = ""
            for plot_index, [plot_name, plot_values] in enumerate(self.plots.items()):
                next_color = web_colors[plot_index % len(web_colors)]
                nearest = self.find_nearest(plot_values.xData, xpoint)
                index = np.where(plot_values.xData == nearest)[0][0]
                data_frames_string += f", <span style='color: {next_color}'>{plot_name}={plot_values.yData[index]:02.02f}</span>"

            datetime_ = datetime.fromtimestamp(mousePoint.x()).strftime("%H:%M:%S")

            self.label.setText(
                f"<span style='font-size: 12pt'>x={datetime_}{data_frames_string}")
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]

    def plot(self, x_axis_name, x_axis_data, y_axis_name, y_axis_data):
        self.plots[y_axis_name] = self.plot_area.plot(x_axis_data, y_axis_data, pen=qt_colors[self._current_color])
        self._current_color += 1
        self.x_axis_name = x_axis_name


class FPSPlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(FPSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_fps.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        self.data1 = self.df1['FPS'].to_numpy()

        self.plot('time', self.df1['Time'], 'fps', self.data1)


class ResponseTimePlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir, *args):
        super(ResponseTimePlotWidget, self).__init__()
        df1 = pd.read_csv(os.path.join(file_dir, 'responsetime.csv'),
                          delimiter=';', skiprows=0, low_memory=False)

        df1[["CommunicationTime", "ServerResponseTime", "TotalTime"]] = df1[
            ["CommunicationTime", "ServerResponseTime", "TotalTime"]].apply(lambda x: x * 1000)

        data1 = df1['TotalTime'].to_numpy()
        data2 = df1['CommunicationTime'].to_numpy()
        data3 = df1['ServerResponseTime'].to_numpy()

        self.plot('time', df1['Time'], 'TotalTime', data1)
        self.plot('time', df1['Time'], 'CommunicationTime', data2)  # Communication_time
        self.plot('time', df1['Time'], 'ServerResponseTime', data3)  # Server Response


class VelocityPlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir, *args):
        super(VelocityPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'velocity.csv'),
                               delimiter=';', skiprows=0, low_memory=False)
        self.df2 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_velocity.csv'),
                               delimiter=';', skiprows=0, low_memory=False)
        self.data1 = self.df1['prom_velocity'].to_numpy()
        self.data2 = self.df2['Velocity'].to_numpy()

        self.plot('Time', self.df1['Time'], 'prom_velocity', self.data1)
        self.plot('Time', self.df2['Time'], 'Velocity', self.data2)


dock_type = {
    "carlaBridge_velocity.csv":
        {"name": "Velocity",
         "type": VelocityPlotWidget
         },
    "responsetime.csv":
        {"name": "ResponseTime",
         "type": ResponseTimePlotWidget
         },
    "carlaBridge_fps.csv":
        {"name": "ResponseTime",
         "type": FPSPlotWidget
         }
}


class MelexStatistics(QMainWindow):
    def __init__(self):
        super(MelexStatistics, self).__init__()
        self.docks = {}

        # dialog = QtWidgets.QFileDialog(caption="Select result directory", directory=RESULTS_DIR)
        # dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        # dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        # dialog.exec_()
        # for dirpath, dnames, fnames in os.walk(dialog.selectedFiles()[0]):
        for dirpath, dnames, fnames in os.walk(
                "/home/robolab/robocomp/components/melex-rodao/files/results/pruebaCampusV4"):
            for f in fnames:
                self.create_dock(dirpath, f)

    def create_dock(self, dirpath, f):

        if f in dock_type:
            current_type = dock_type[f]
            dock = QtWidgets.QDockWidget(current_type["name"])
            plot_widget = current_type["type"](dirpath)
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
