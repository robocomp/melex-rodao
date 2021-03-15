# -*- coding: utf-8 -*-
import pathlib
from datetime import datetime
import os
import sys

import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import yaml
from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtCore import QCoreApplication, Qt
from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton
from pyqtgraph import GraphicsLayoutWidget, DateAxisItem
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
import pandas as pd
import geopandas as gpd

FILE_PATH = pathlib.Path(__file__).parent.absolute()
RESULTS_DIR = os.path.join(FILE_PATH, "..", "..", 'files/results/')

web_colors = ["Red", "Yellow", "Cyan", "Blue", "Magenta"]
qt_colors = ["r", "y", "c", "b", "m"]


def set_color(value):
    if value == np.nan:
        value = 0
    if value < 5:
        color = 'greenyellow'
    elif value < 10:
        color = 'yellow'
    elif value < 15:
        color = 'gold'
    elif value < 20:
        color = 'darkorange'
    elif value >= 20:
        color = 'red'
    return color


class GeoDataPlotWidget(Canvas):
    def __init__(self, file_dir):
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        # Read gnss file
        df = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                         delimiter=';', skiprows=0, low_memory=False)

        # Read velocity file generated with velocity.py script
        df2 = pd.read_csv(os.path.join(file_dir, 'velocity.csv'),
                          delimiter=';', skiprows=0, low_memory=False)
        # Merge dataframes
        df_merge_result = pd.merge_ordered(df, df2, on='Time', fill_method="ffill")

        # Create column color depending of the velocity
        df['Color'] = df_merge_result['prom_velocity'].apply(lambda value: set_color(value))

        # Create geodataframe to plot latitude and loingitude
        geometry = gpd.points_from_xy(df['Longitude'], df['Latitude'])
        gdf = gpd.GeoDataFrame(df, geometry=geometry)
        self.fig = Figure()
        ax1 = self.fig.add_subplot(111)
        gdf.plot(ax=ax1, marker='o', color=gdf['Color'], markersize=8)

        CAMPUS_DIR_PATH = os.path.join(FILE_PATH, "..", "..", "files", "campus")
        # Read roads map
        roads = gpd.read_file(os.path.join(CAMPUS_DIR_PATH, 'roads.geojson'))
        roads.plot(ax=ax1)
        # Buildings map
        buildings = gpd.read_file(os.path.join(CAMPUS_DIR_PATH, 'buildings.geojson'))
        buildings.plot(ax=ax1, color='darkslateblue')

        # Read and plot cameras location
        yaml_file = open(os.path.join(FILE_PATH, "..", "..", "etc", 'cameras.yml'))
        pose_cameras_dict = yaml.load(yaml_file, Loader=yaml.FullLoader)

        cam_lat = []
        cam_lon = []
        for pose in pose_cameras_dict.values():
            cam_lat.append(pose['latitude'])
            cam_lon.append(pose['longitude'])

        df2 = pd.DataFrame({'Latitude': cam_lat, 'Longitude': cam_lon})
        geometry2 = gpd.points_from_xy(cam_lon, cam_lat)
        gdf2 = gpd.GeoDataFrame(df2, geometry=geometry2)

        gdf2.plot(ax=ax1, marker='o', color='y', markersize=20)
        self.ax = ax1
        super(GeoDataPlotWidget, self).__init__(self.fig)


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
            try:
                mousePoint = vb.mapSceneToView(pos)
            except np.linalg.LinAlgError:
                print("Plot too small to show values")
                return
            xpoint = mousePoint.x()
            data_frames_string = ""
            stacked_total_showed = False
            for plot_index, [plot_name, plot_values] in enumerate(self.plots.items()):
                next_color = web_colors[plot_index % len(web_colors)]
                if self.type == 'bars':
                    data = plot_values.getData()
                    index, value = self.find_nearest(data[0], xpoint)
                    data_frames_string += f", <span style='color: {next_color}'>{plot_name}={data[1][index]:02.02f}</span>"

                elif self.type == 'stacked_bars':
                    index, value = self.find_nearest(self.stacked_bars_data['time'], xpoint)

                    if not stacked_total_showed:
                        data_frames_string += f", <span style='color: blue'>'TotalTime'={self.stacked_bars_data['TotalTime'][index]:02.02f} ms </span> "
                        stacked_total_showed = True

                    data_frames_string += f", <span style='color: {next_color}'>{plot_name}={self.stacked_bars_data[plot_name][index]:02.02f} ms </span> "


                else:
                    index, value = self.find_nearest(plot_values.xData, xpoint)
                    if index >= len(plot_values.yData):
                        index = len(plot_values.yData) - 1
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
        bg1 = pg.BarGraphItem(x=x_axis_data, height=y_axis_data, width=0.5, brush=color, pen=color)
        # bg1 = pg.BarGraphItem(x=x_axis_data, height=x_axis_data, width=0.5)
        self.plot_area.addItem(bg1)
        self.plots[y_axis_name] = bg1
        self._current_color += 1
        if 'time' in x_axis_name.lower():
            axis = pg.DateAxisItem()
            self.plot_area.setAxisItems({'bottom': axis})

    def plot_stacked_bars(self, x_axis_name, x_axis_data, y_axis_prev_data, y_axis_name, y_axis_data, y_data_to_show):
        self.type = 'stacked_bars'
        color = qt_colors[self._current_color]
        self.x_axis_name = x_axis_name
        bg1 = pg.BarGraphItem(x=x_axis_data, y0=y_axis_prev_data, y1=y_axis_data, width=1, brush=color, pen=color)
        self.plot_area.addItem(bg1)
        self.plots[y_axis_name] = bg1

        self._current_color += 1
        if 'time' in x_axis_name.lower():
            axis = pg.DateAxisItem()
            self.plot_area.setAxisItems({'bottom': axis})

    def plot_hist(self, x_axis_name, x_axis_data, min_x_axis=0.0):
        self.type = 'hist'
        x_axis_data = x_axis_data[~np.isnan(x_axis_data)]
        min_data = min(x_axis_data[x_axis_data > min_x_axis])
        max_data = max(x_axis_data)
        data_bins = max_data - min_data
        y, x = np.histogram(x_axis_data, range=[min_data, max_data], bins='auto')
        self.x_axis_name = x_axis_name
        self.plots[x_axis_name + "_freq"] = self.plot_area.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True,
                                                                brush=qt_colors[self._current_color])
        self._current_color += 1


class GNSS3DPlotWidget(gl.GLViewWidget):
    def __init__(self, file_dir):
        super(GNSSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        data1 = self.df1['Latitude'].to_numpy()
        data2 = self.df1['Longitude'].to_numpy()
        data3 = self.df1['Longitude'].to_numpy()

        self.plot3D('Longitude', data1, 'Latitud', data2, "altitude", data3)

    def plot3D(self, x_axis_name, x_axis_data, y_axis_name, y_axis_data, z_axis_name, z_axis_data):
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
            plt = gl.GLLinePlotItem(pos=np.vstack([x_axis_data[i], y_axis_data[i], z_axis_data[i]]).transpose(),
                                    antialias=True)
            self.addItem(plt)


class GNSSPlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(GNSSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_gnss.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        long = self.df1['Longitude'].to_numpy()
        lat = self.df1['Latitude'].to_numpy()

        self.plot('Long', lat, 'Lat', long)


class FPSPlotHistogramWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(FPSPlotHistogramWidget, self).__init__()
        df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_fps.csv'),
                          delimiter=';', skiprows=0, low_memory=False)

        data1 = df1['FPS'].to_numpy()

        self.plot_hist("FPS", data1, 5)
        # self.plot('time', self.df1['Time'], 'fps', self.data1)


class FPSPlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(FPSPlotWidget, self).__init__()
        self.df1 = pd.read_csv(os.path.join(file_dir, 'carlaBridge_fps.csv'),
                               delimiter=';', skiprows=0, low_memory=False)

        self.data1 = self.df1['FPS'].to_numpy()

        self.plot('time', self.df1['Time'], 'fps', self.data1)


class ResponseTimePlotHistogramWidget(AbstractPlotWidget):
    def __init__(self, file_dir):
        super(ResponseTimePlotHistogramWidget, self).__init__()
        df1 = pd.read_csv(os.path.join(file_dir, 'responsetime.csv'),
                          delimiter=';', skiprows=0, low_memory=False)

        data1 = df1['TotalTime'].to_numpy()
        data2 = df1['CommunicationTime'].to_numpy()
        data3 = df1['ServerResponseTime'].to_numpy()

        self.plot_hist("TotalTime", data1, 0.0)
        self.plot_hist("CommunicationTime", data2, 0.0)
        self.plot_hist("ServerResponseTime", data3, 0.0)
        # self.plot('time', self.df1['Time'], 'fps', self.data1)


class ResponseTimePlotWidget(AbstractPlotWidget):
    def __init__(self, file_dir, *args):
        super(ResponseTimePlotWidget, self).__init__()
        df1 = pd.read_csv(os.path.join(file_dir, 'responsetime.csv'),
                          delimiter=';', skiprows=0, low_memory=False)

        df1[["CommunicationTime", "ServerResponseTime", "TotalTime"]] = df1[
            ["CommunicationTime", "ServerResponseTime", "TotalTime"]].apply(lambda x: x * 1000)

        # df1['datetime'] = pd.to_datetime(df1['Time'], unit='ns')
        df1['datetime'] = df1['Time'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S.%f'))
        df1['datetime'] = df1['datetime'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f'))
        df2 = df1.groupby(pd.Grouper(key='datetime', freq='1s')).mean()

        data1_original = df1['TotalTime'].to_numpy()
        data2_original = df1['CommunicationTime'].to_numpy()
        data3_original = df1['ServerResponseTime'].to_numpy()

        data2 = df2['CommunicationTime'].to_numpy()
        data3 = df2['ServerResponseTime'].to_numpy()

        self.plot_stacked_bars('time', df2['Time'], 0, 'ServerResponseTime', data3, data3_original)
        self.plot_stacked_bars('time', df2['Time'], data3, 'CommunicationTime', data2, data2_original)

        self.stacked_bars_data = {'time': df1['Time'],
                                  'TotalTime': data1_original,
                                  'ServerResponseTime': data2_original,
                                  'CommunicationTime': data3_original
                                  }

        # self.plot_bars('time', df1['Time'], 'TotalTime', data1)
        # self.plot_bars('time', df1['Time'], 'CommunicationTime', data2)  # Communication_time
        # self.plot_bars('time', df1['Time'], 'ServerResponseTime', data3)  # Server Response


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
         "widgets": VelocityPlotWidget
         },
    "responsetime.csv":
        {"name": "ResponseTime",
         "widgets": [ResponseTimePlotWidget, ResponseTimePlotHistogramWidget]
         },
    "carlaBridge_fps.csv":
        {"name": "FPS",
         "widgets": [FPSPlotWidget, FPSPlotHistogramWidget]
         },
    "carlaBridge_gnss.csv":
        {"name": "GNSS",
         "widgets": GeoDataPlotWidget
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
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        open_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open statistics')
        open_action.triggered.connect(self.open_statistics)

        self.statusBar()

        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu('&File')
        fileMenu.addAction(open_action)
        fileMenu.addAction(exit_action)

    def open_statistics(self):
        dialog = QtWidgets.QFileDialog(caption="Select result directory", directory=RESULTS_DIR)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.exec_()
        self.view_menu = self.menubar.addMenu('&View')
        for dirpath, dnames, fnames in os.walk(dialog.selectedFiles()[0]):
            for f in fnames:
                self.create_dock(dirpath, f)

    def create_dock(self, dirpath, f):
        if f in dock_type:
            current_type = dock_type[f]
            widgets = current_type["widgets"]
            if not isinstance(widgets, list):
                widgets = [widgets]
            previous_dock = None
            for w_index, widget in enumerate(widgets):
                dock_name = current_type["name"]
                if len(widgets) > 1:
                    dock_name += f" {w_index}"
                dock = QtWidgets.QDockWidget(dock_name)
                view_action = dock.toggleViewAction()
                view_action.setStatusTip(f'Show/Hide {dock_name}')
                self.view_menu.addAction(view_action)
                plot_widget = widget(dirpath)
                dock.setWidget(plot_widget)
                dock.setAllowedAreas(Qt.AllDockWidgetAreas)
                self.docks[f] = dock
                self.addDockWidget(dock_positions[self._current_dock_pos % len(dock_positions)], dock)
                if previous_dock:
                    self.tabifyDockWidget(previous_dock, dock)
                previous_dock = dock
            self._current_dock_pos += 1


if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    window = MelexStatistics()
    window.showMaximized()
    app.exec_()
