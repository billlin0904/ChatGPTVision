# window.py

from PyQt5.QtGui import QIcon
from qfluentwidgets import FluentWindow, MessageBox, NavigationItemPosition
from widget import AskGptFrame, SettingFrame
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import QApplication
import sys

class Window(FluentWindow):
    def showOrHidden(self, isShow):
        if isShow:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()

    def showMessageBox(self):
        w = MessageBox(
            '截圖完成',
            '截圖已保存為 captured_window.png。',
            self
        )
        w.exec()

    def __init__(self):
        super().__init__()
        self.homeInterface = AskGptFrame('Ask GPT', self)
        self.homeInterface.showWindow.connect(self.showOrHidden)
        self.settingInterface = SettingFrame('Setting', self)
        self.initNavigation()
        self.initWindow()        

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Ask GTP')
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
        self.navigationInterface.setAcrylicEnabled(True)

    def initWindow(self):
        self.resize(640, 480)
        self.setWindowIcon(QIcon('./assets/icons/horus.ico'))
        self.setWindowTitle('Horus')
        
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
    
