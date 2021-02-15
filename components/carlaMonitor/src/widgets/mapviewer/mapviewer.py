import os
import functools
from PySide2 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebChannel
from PySide2.QtCore import Slot


class MapViewer(QtWidgets.QWidget):
    def __init__(self):
        super(MapViewer, self).__init__()
        # self.setFixedSize(800, 500)
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        label = self.label = QtWidgets.QLabel()
        sp = QtWidgets.QSizePolicy()
        sp.setVerticalStretch(0)
        label.setSizePolicy(sp)
        vbox.addWidget(label)
        view = self.view = QtWebEngineWidgets.QWebEngineView()
        channel = self.channel = QtWebChannel.QWebChannel()

        channel.registerObject("MapViewer", self)
        view.page().setWebChannel(channel)

        file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "assets/map.html",
        )
        self.view.setUrl(QtCore.QUrl.fromLocalFile(file))

        vbox.addWidget(view)

        button = QtWidgets.QPushButton("Go to Paris")
        panToParis = functools.partial(self.panMap, 2.3272, 48.8620)
        button.clicked.connect(panToParis)
        vbox.addWidget(button)

    @Slot(float, float)
    def onMapMove(self, lat, lng):
        self.label.setText("Lng: {:.5f}, Lat: {:.5f}".format(lng, lat))


    def panMap(self, lat, lng):
        page = self.view.page()
        page.runJavaScript("map.panTo(L.latLng({}, {}));".format(lat, lng))
        # page.runJavaScript("var marker = L.marker(map.getCenter()).addTo(map); marker.bindPopup(\"Car is here!\").openPopup();")
        page.runJavaScript(f"var newLatLng = new L.LatLng({lat}, {lng});marker.setLatLng(newLatLng);")
    def update_map_position(self, lat, lng):
        self.panMap(lat, lng)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MapViewer()
    w.show()
    sys.exit(app.exec_())


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
