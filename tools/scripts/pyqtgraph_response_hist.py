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
df1 = pd.read_csv(os.path.join(dir, 'responsetime.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df1[["CommunicationTime", "ServerResponseTime", "TotalTime"]] = df1[
    ["CommunicationTime", "ServerResponseTime", "TotalTime"]].apply(lambda x: x * 1000)

# print (len(df1))
# df1 = df1.groupby(['TotalTime']).mean()
# print (len(df1))
# df1.to_csv('groupby.csv')

data1 = df1['TotalTime'].to_numpy()
data2 = df1['CommunicationTime'].to_numpy()
data3 = df1['ServerResponseTime'].to_numpy()

# bg1 = pg.BarGraphItem(x=df1['Time'], height=data1, width=0.1, brush='r')
# y,x = np.histogram(data1, bins=np.linspace(-3, 8, 40))

## Using stepMode="center" causes the plot to draw two lines for each sample.
## notice that len(x) == len(y)+1
# p1.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0,0,255,150))
bg1 = pg.BarGraphItem(x=df1['Time'], height=data1, width=0.3, brush='r', pen='r')
bg2 = pg.BarGraphItem(x=df1['Time'], height=data2, width=0.3, brush='g',pen='g')
bg3 = pg.BarGraphItem(x=df1['Time'], height=data3, width=0.3, brush='b',pen='b')
p1.addItem(bg1)
p1.addItem(bg3)
p1.addItem(bg2)

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

        nearest1 = find_nearest(df1['Time'], xpoint)
        index1 = df1.index[df1['Time'] == nearest1].tolist()[0]

        datetime_ = datetime.fromtimestamp(mousePoint.x()).strftime("%H:%M:%S")

        label.setText(
            "<span style='font-size: 12pt'>x=%s,   <span style='color: red'>Total=%0.2f ms</span> ,   "
            "<span style='color: green'>Communication=%0.2f ms</span> , <span style='color: blue'>Server=%0.2f "
            "ms</span>  " % (
                datetime_, data1[index1], data2[index1], data3[index1]))
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())


proxy = pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)



def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
