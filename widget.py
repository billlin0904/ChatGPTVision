# widget.py

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QApplication
from qfluentwidgets import SubtitleLabel, ImageLabel, BodyLabel, PushButton, setFont, IndeterminateProgressBar
from window_capture import WindowCapture
from chatgpt_service import ChatGPTService

class Widget(QFrame):
    showWindow = pyqtSignal(bool)
    sendImage = pyqtSignal(QPixmap)
    textToVoice = pyqtSignal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.captureWindowBtn = PushButton(self.tr('Capture window'), self)
        self.captureWindowBtn.clicked.connect(lambda: self.doCaptureWindow())
        self.imageLabel = ImageLabel(self)
        self.imageLabel.setBorderRadius(8, 8, 0, 0)
        self.responseBodyLabel = BodyLabel(self)
        #self.responseBodyLabel.setMaximumHeight(300)
        #self.responseBodyLabel.setMaximumWidth(640)
        self.waitResponseProcessRing = IndeterminateProgressBar(self)
        self.waitResponseProcessRing.hide()
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.imageLabel, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.responseBodyLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.waitResponseProcessRing, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.captureWindowBtn, 0, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))
        self.conversation_history = []
        self.window_capture = WindowCapture(self.onCaptureCompleted)
        self.window_capture.hide()

        # 初始化 ChatGPTService 並移動到 QThread 中
        self.chatgpt_service = ChatGPTService()
        #self.sendImage.connect(self.chatgpt_service.sendImage)  # 連接信號到槽
        #self.textToVoice.connect(self.chatgpt_service.textToVoice) 
        
        self.thread = QThread()
        self.chatgpt_service.moveToThread(self.thread)
        self.thread.start()

        # 連接 ChatGPTService 的信號到顯示方法
        self.chatgpt_service.responseReady.connect(self.displayChatGPTResponse)
        self.chatgpt_service.textToVoiceReady.connect(self.playVoiceResponse)

    def doCaptureWindow(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.window_capture.show()
        self.window_capture.update_full_screen_pixmap()        
        self.responseBodyLabel.hide()
        self.waitResponseProcessRing.show()
        self.waitResponseProcessRing.start()

    def onCaptureCompleted(self, captured_pixmap):        
        if captured_pixmap is None:
            self.waitResponseProcessRing.stop()
            self.waitResponseProcessRing.hide()
            self.showWindow.emit(True)
            self.window_capture.close()
            return
        scaled_screenshot = captured_pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.imageLabel.setImage(scaled_screenshot)
        self.sendImage.emit(captured_pixmap)  # 發送圖片信號
        self.showWindow.emit(True)        
        self.window_capture.hide()
        self.textToVoice.emit(self.responseBodyLabel.text()) 
        
    def playVoiceResponse(self, audio_data: bytes):
        pass

    def displayChatGPTResponse(self, response):
        self.waitResponseProcessRing.stop()
        self.waitResponseProcessRing.hide()
        self.responseBodyLabel.show()
        self.responseBodyLabel.setText(response)
