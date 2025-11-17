
import os

from .CommonChart import CommonChart

from qgis.utils import iface


import qgis.PyQt as PyQt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMenu,QAction,QApplication,QDockWidget


def classFactory(iface):
    return CommonPlugin(iface)
    QgsOptionsWidgetFactory

class CommonPlugin:
    def __init__(self, iface=None):
        self.DocksArray = []

    def initGui(self):
        self.Action = QAction('Open new CommonChart')
        self.Action.triggered.connect(self.NewDash)
        self.Action.setIcon(QIcon(os.path.dirname(os.path.abspath(__file__))+'/icon.png'))
        #iface.addPluginToDatabaseMenu('Common Chart',self.Action)
        iface.addToolBarIcon(self.Action)
        
    def NewDash(self,B):
        Docki = CommonDock(self.DocksArray)
        Dash = CommonChart()
        Docki.setWidget(Dash)
        ##Check if QgsProject.instance() has layers
        if Dash.UI['Layers'].count() > 0:
            Dash.LayerSet()
        else:
            Docki.setWindowTitle('Common Chart')

        iface.addDockWidget(Qt.RightDockWidgetArea,Docki)
        self.DocksArray.append(Docki)
        
    def unload(self):
        #iface.removeDatabaseToolBarIcon('Common Chart',self.Action)
        iface.removeToolBarIcon(self.Action)
        for D in iface.mainWindow().findChildren(QDockWidget):
            if type(D) == CommonDock:
                D.setParent(None)
                D.deleteLater()

        self.Action.deleteLater()
        del self.DocksArray
        


class CommonDock(QDockWidget):
    def __init__(self,Storage):
        super(CommonDock,self).__init__()
        self.Storage=Storage

    def closeEvent(self, event):
        self.setParent(None)
        self.Storage.remove(self)
        event.accept()

## QGis Python console commands to help work with live docks
#[i.windowTitle() for i in iface.mainWindow().findChildren(QDockWidget)] ## See all open docks
#iface.mainWindow().findChildren(QDockWidget)[0].findfindChildren(QDialog)[0] ## Get the CommonChart instance for the dock
#iface.mainWindow().findChildren(QDockWidget)[0].findfindChildren(QDialog)[0].ShowLayer ##Virtual layer