# -*- coding: utf-8 -*-
from datetime import datetime
import os
import sys

import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.opengl as gl
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
        self.type = None
        self.label = pg.LabelItem(justify='right')
        self.addItem(self.label)
        self.plot_area = self.addPlot(row=1, col=0)
        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot_area.addItem(self.vLine, ignoreBounds=True)
        self.plot_area.addItem(self.hLine, ignoreBounds=True)
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
                if self.type == 'bars':
                    data = plot_values.getData()
                    index, value = self.find_nearest(data[0], xpoint)
                    data_frames_string += f", <span style='color: {next_color}'>{plot_name}={data[1][index]:02.02f}</span>"
                else:
                    index, value = self.find_nearest(plot_values.xData, xpoint)
                    data_frames_string += f", <span style='color: {next_color}'>{plot_name}={plot_values.yData[index]:02.02f}</span>"

            if 'time' in self.x_axis_name.lower():
                x_axis_string = datetime.fromtimestamp(mousePoint.x()).strftime("%H:%M:%S")
            else:
                x_axis_string = f"{mousePoint.x():02.02f}"

            self.label.setText(
                f"<span style='font-size: 12pt'>{self.x_axis_name}={x_axis_string}{data_frames_string}")
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx, array[idx]

    def plot(self, x_axis_name, x_axis_data, y_axis_name, y_axis_data):
        self.plots[y_axis_name] = self.plot_area.plot(x_axis_data, y_axis_data, pen=qt_colors[self._current_color])
        self._current_color += 1
        self.x_axis_name = x_axis_name
        if 'time' in x_axis_name.lower():
            axis = pg.DateAxisItem()
            self.plot_area.setAxisItems({'bottom': axis})

    def plot_bars(self, x_axis_name, x_axis_data, y_axis_name, y_axis_data):
        self.type = 'bars'
        color = qt_colors[self._current_color]
        self.x_axis_name = x_axis_name
        bg1 = pg.BarGraphItem(x=x_axis_data, height=y_axis_data, width=1, brush=color, pen=color)
        # bg1 = pg.BarGraphItem(x=x_axis_data, height=x_axis_data, width=0.5)
        self.plot_area.addItem(bg1)
        self.plots[y_axis_name] = bg1
        self._current_color += 1
        if 'time' in x_axis_name.lower():
            axis = pg.DateAxisItem()
            self.plot_area.setAxisItems({'bottom': axis})



class GNSS3DPlotWidget(gl.GLViewWidget):
    def __init__(self, file_dir):
        super(GNSSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        data1 = self.df1['Latitude'].to_numpy()
        data2 = self.df1['Longitude'].to_numpy()
        data3 = self.df1['Longitude'].to_numpy()

        self.plot3D('Longitude', data1, 'Latitud', data2, "altitude", data3)

    def plot3D(self,  x_axis_name, x_axis_data, y_axis_name, y_axis_data, z_axis_name, z_axis_data):
        self.opts['distance'] = 40
        # self.show()
        # self.setWindowTitle('pyqtgraph example: GLLinePlotItem')
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-100, 0, 0)
        self.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -100, 0)
        self.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, -100)
        self.addItem(gz)
        for i in range(len(x_axis_data)):
            # pts = np.vstack([x_axis_data[i], y_axis_data[i], z_axis_data[i]]).transpose()
            plt = gl.GLLinePlotItem(pos=np.vstack([x_axis_data[i], y_axis_data[i], z_axis_data[i]]).transpose(), antialias=True)
            self.addItem(plt)


class GNSSPlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(GNSSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        long= self.df1['Longitude'].to_numpy()
        lat = self.df1['Latitude'].to_numpy()

        self.plot('Long', lat, 'Lat', long)


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

        self.plot_bars('time', df1['Time'], 'TotalTime', data1)
        self.plot_bars('time', df1['Time'], 'CommunicationTime', data2)  # Communication_time
        self.plot_bars('time', df1['Time'], 'ServerResponseTime', data3)  # Server Response


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
        {"name": "FPS",
         "type": FPSPlotWidget
         },
    "carlaBridge_gnss.csv":
        {"name": "GNSS",
         "type": GNSSPlotWidget
         }
}

dock_positions = [
    QtCore.Qt.BottomDockWidgetArea,
    QtCore.Qt.LeftDockWidgetArea,
    QtCore.Qt.RightDockWidgetArea,
    QtCore.Qt.TopDockWidgetArea
]

class MelexStatistics(QMainWindow):
    def __init__(self):
        super(MelexStatistics, self).__init__()
        self.setWindowTitle("Melex Statistics")
        self.docks = {}
        self._current_dock_pos = 0

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
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            self._current_dock_pos += 1
            self.docks[f] = dock
            self.addDockWidget(dock_positions[self._current_dock_pos % len(dock_positions)], dock)


if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MelexStatistics()
    window.show()
    app.exec_()
