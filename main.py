# coding:utf-8

import sys
import platform
from PyQt5.QtCore import Qt, QUrl, QTimer, QBuffer, QIODevice, QRect
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QScreen, QPainter, QColor, QPen
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QMessageBox, QWidget
from qfluentwidgets import (MessageBox, FluentWindow, SubtitleLabel, ImageLabel, BodyLabel, PushButton, NavigationItemPosition, setFont)
from qfluentwidgets import FluentIcon as FIF

import requests
import os
import subprocess
import sys
import openai
import base64

class WindowCapture(QWidget):

    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle('Window Capture')
        self.setWindowOpacity(0.3)  # 將主視窗設置為透明
        self.full_screen_pixmap = QPixmap(QApplication.primaryScreen().grabWindow(0))  # 截取全屏
        self.setGeometry(0, 0, self.full_screen_pixmap.width(), self.full_screen_pixmap.height())  # 設置視窗大小為全屏
        self.showFullScreen()
        QApplication.setOverrideCursor(Qt.CrossCursor)  # 設置滑鼠為十字形
        self.selecting = False
        self.start_point = None
        self.end_point = None
        self.callback = callback  # 保存回調函數
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.start_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.end_point = event.pos()
            self.capture_selected_area()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.full_screen_pixmap)
        if self.selecting and self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point)
            pen = QPen(QColor(255, 0, 0), 2)  # 紅色外框
            painter.setPen(pen)
            painter.drawRect(rect)

    def capture_selected_area(self):
        rect = QRect(self.start_point, self.end_point).normalized()
        captured_pixmap = self.full_screen_pixmap.copy(rect)
        captured_pixmap.save('captured_window.png', 'PNG')
        self.callback(captured_pixmap)  # 調用回調函數，傳遞捕捉到的圖片
        self.close()  # 關閉捕捉視窗

class Widget(QFrame):
    showWindow = pyqtSignal(bool) 

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.vBoxLayout = QVBoxLayout(self)
        
        self.captureImageBtn = PushButton(self.tr('Capture image'), self)
        self.captureImageBtn.clicked.connect(lambda:self.doCapture())
        
        self.captureWindowBtn = PushButton(self.tr('Capture window'), self)
        self.captureWindowBtn.clicked.connect(lambda:self.captureWindow())  # 新增按鈕

        self.imageLabel = ImageLabel(self)
        self.imageLabel.setBorderRadius(8, 8, 0, 0)
        
        self.responseBodyLabel = BodyLabel(self)
        self.responseBodyLabel.setMaximumHeight(300)
        self.responseBodyLabel.setMaximumWidth(640)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.imageLabel, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.responseBodyLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.captureImageBtn, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.captureWindowBtn, 0, Qt.AlignCenter)  # 新增按鈕
        self.setObjectName(text.replace(' ', '-'))
        
    def doCapture(self):
        self.showWindow.emit(False)
        QTimer.singleShot(3000, self.captureScreen)
        
    def captureWindow(self):
        self.window_capture = WindowCapture(self.onCaptureCompleted)  # 創建 WindowCapture 物件，並設置回調函數

    def onCaptureCompleted(self, captured_pixmap):
        """
        當捕捉完成時的回調函數
        """
        scaled_screenshot = captured_pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.imageLabel.setImage(scaled_screenshot)
        self.sendImageToChatGPT(captured_pixmap)
        self.showMessageBox()
        self.showWindow.emit(True)

    def captureScreen(self):
        screen = QApplication.primaryScreen()
        if screen:
            screenshot = screen.grabWindow(0)
            scaled_screenshot = screenshot.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.imageLabel.setImage(scaled_screenshot)
            screenshot.save('screenshot.png', 'png')
            self.sendImageToChatGPT(screenshot)
        self.showWindow.emit(True)
    
    def sendImageToChatGPT(self, pixmap):
        """
        將 QPixmap 圖片轉換為 base64 並以文本形式發送到 OpenAI API 進行分析。
        """
        try:
            image = pixmap.toImage()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            byte_data = buffer.data()
            encoded_image = base64.b64encode(byte_data).decode('utf-8')

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
            }
            
            prompt = "What’s in this image? use traditional chinese response."

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt },
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                        ]
                    }
                ],
                "max_tokens": 300
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    message_content = result['choices'][0]['message']['content']
                    self.displayChatGPTResponse(message_content)
                else:
                    print("Unexpected response format:", result)
                    QMessageBox.warning(self, "API Error", "Unexpected response format.")
            else:
                print(f"Error: {response.status_code}, {response.text}")
                QMessageBox.warning(self, "API Error", f"Failed to get response: {response.text}")
        except Exception as e:
            print(f"發送圖片過程中發生錯誤：{e}")
            QMessageBox.warning(self, "發送錯誤", f"發送圖片過程中發生錯誤：{e}")

    def displayChatGPTResponse(self, response):
        self.responseBodyLabel.setText(response)

    def showMessageBox(self):
        w = MessageBox(
            '截圖完成',
            '截圖已保存為 captured_window.png。',
            self
        )
        w.exec()

class Window(FluentWindow):
    def showOrHidden(self, isShow):
        if isShow:
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()

    def __init__(self):
        super().__init__()
        self.homeInterface = Widget('Capture Image', self)
        self.homeInterface.showWindow.connect(self.showOrHidden)
        self.settingInterface = Widget('Setting Interface', self)
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)
        self.navigationInterface.setAcrylicEnabled(True)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('ChatGPT Vision')

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
