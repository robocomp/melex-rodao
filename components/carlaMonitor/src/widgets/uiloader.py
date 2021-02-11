from PySide2 import  QtCore, QtUiTools

from src.widgets.lightwidget import LightState


class CustomUiLoader(QtUiTools.QUiLoader):
    _baseinstance = None
    def __init__(self):
        super(CustomUiLoader, self).__init__()
        self.registerCustomWidget(LightState)

    def createWidget(self, classname, parent=None, name=''):
        if parent is None and self._baseinstance is not None:
            widget = self._baseinstance
        else:
            widget = super(CustomUiLoader, self).createWidget(classname, parent, name)
            if self._baseinstance is not None:
                setattr(self._baseinstance, name, widget)
        return widget

    def loadUi(self, uifile, baseinstance=None):
        self._baseinstance = baseinstance
        widget = self.load(str(uifile))
        QtCore.QMetaObject.connectSlotsByName(widget)
        return widget