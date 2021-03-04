"""
Demonstrates some customized mouse interaction by drawing a crosshair that follows
the mouse.
"""
import os
from datetime import time, datetime

import numpy as np
import pandas as pd
import pyqtgraph as pg
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
df1 = pd.read_csv(os.path.join(dir, 'carlaBridge_fps.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

print(df1.head())
df1 = df1[df1['FPS'] != 0]  # Remove columns with FPS 0 --- bridge not working yet
print(df1.head())
data1 = df1['FPS'].to_numpy()
p1.plot(df1['Time'], data1, pen="r")

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
            "<span style='font-size: 12pt'>x=%s,   <span style='color: red'>FPS=%0.1f</span>" % (
                datetime_, data1[index1]))
        vLine.setPos(mousePoint.x())
        hLine.setPos(mousePoint.y())


proxy = pg.SignalProxy(p1.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)
# p1.scene().sigMouseMoved.connect(mouseMoved)

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
