"""
Demonstrates some customized mouse interaction by drawing a crosshair that follows
the mouse.
"""
import os
from datetime import time, datetime

import numpy as np
import pandas as pd
import pyqtgraph as pg
from matplotlib import pyplot as plt
from pyqtgraph import DateAxisItem
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


# generate layout
app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('Velocity')
label = pg.LabelItem(justify='right')
win.addItem(label)
p1 = win.addPlot(row=1, col=0)
# p2 = win.addPlot(row=2, col=0)

region = pg.LinearRegionItem()
region.setZValue(10)
# Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this
# item when doing auto-range calculations.
# p2.addItem(region, ignoreBounds=True)

# pg.dbg()
p1.setAutoVisible(y=False)

# create numpy arrays
dir = '/home/robocomp/robocomp/components/melex-rodao/files/results/pruebaCampusV4'
# Read last directory
directory = '/home/robocomp/robocomp/components/melex-rodao/files/results/'
dir = max([os.path.join(directory, d) for d in os.listdir(directory)], key=os.path.getmtime)
df1 = pd.read_csv(os.path.join(dir, 'responsetime.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

#To milliseconds
df1[["CommunicationTime", "ServerResponseTime", "TotalTime"]] = df1[
    ["CommunicationTime", "ServerResponseTime", "TotalTime"]].apply(lambda x: x * 1000)

print(len(df1))

df1['datetime'] = pd.to_datetime(df1['Time'], unit='ns')
df2 = df1.groupby(pd.Grouper(key='datetime', freq='1ns')).mean()
print(len(df1))

df2.to_csv('groupby.csv')


data1_original = df1['TotalTime'].to_numpy()
data2_original = df1['CommunicationTime'].to_numpy()
data3_original = df1['ServerResponseTime'].to_numpy()

data1 = df2['TotalTime'].to_numpy()
data2 = df2['CommunicationTime'].to_numpy()
data3 = df2['ServerResponseTime'].to_numpy()


# bg1 = pg.BarGraphItem(x=df1['Time'], height=data1, width=1, brush='r', pen='r')
bg3 = pg.BarGraphItem(x=df2['Time'], y0=0, y1=data3, width=1, brush='b', pen='b')  # Server
bg2 = pg.BarGraphItem(x=df2['Time'], y0=data3, height=data2, width=1, brush='g', pen='g')  # Comm
# p1.addItem(bg1)
p1.addItem(bg2)
p1.addItem(bg3)

axis = DateAxisItem()
p1.setAxisItems({'bottom': axis})
region.setRegion([df1['Time'][0], df1['Time'].iloc[-1]])


def update():
    region.setZValue(10)
    minX, maxX = region.getRegion()

    p1.setXRange(minX, maxX, padding=0)
    axX = p1.getAxis('bottom')
    print('x axis range: {}'.format(axX.range))


region.sigRegionChanged.connect(update)


def updateRegion(window, viewRange):
    rgn = viewRange[0]
    region.setRegion(rgn)


p1.sigRangeChanged.connect(updateRegion)

# cross hair
vLine = pg.InfiniteLine(angle=90, movable=False)
hLine = pg.InfiniteLine(angle=0, movable=False)
p1.addItem(vLine, ignoreBounds=True)
p1.addItem(hLine, ignoreBounds=True)

vb = p1.vb


def mouseMoved(evt):
    pos = evt[0]  ## using signal proxy turns original arguments into a tuple
    if p1.sceneBoundingRect().contains(pos):
        mousePoint = vb.mapSceneToView(pos)
        xpoint = mousePoint.x()
        print(xpoint)
        nearest1 = find_nearest(df1['Time'], xpoint)
        print(nearest1, '\n')
        index1 = df1.index[df1['Time'] == nearest1].tolist()[0]

        datetime_ = datetime.fromtimestamp(mousePoint.x()).strftime("%H:%M:%S")

        label.setText(
            "<span style='font-size: 12pt'>x=%s,   <span style='color: red'>Total=%0.2f ms</span> ,   "
            "<span style='color: green'>Communication=%0.2f ms</span> , <span style='color: blue'>Server=%0.2f "
            "ms</span>  " % (
                datetime_, data1_original[index1], data2_original[index1], data3_original[index1]))
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())


proxy = pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
