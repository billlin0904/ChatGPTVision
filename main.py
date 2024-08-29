# coding:utf-8

# main.py

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from window import Window

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_NativeWindows, True)
    
    w = Window()
    w.show()
    sys.exit(app.exec_())
