from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QApplication
from qfluentwidgets import SubtitleLabel, ImageLabel, LineEdit, PlainTextEdit, IndeterminateProgressBar, ToolButton, setFont
from window_capture import WindowCapture
from chatgpt_service import ChatGPTService
from qfluentwidgets import FluentIcon as FIF

class SettingFrame(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))

class AskGptFrame(QFrame):
    showWindow = pyqtSignal(bool)
    sendImage = pyqtSignal(QPixmap, str)
    textToVoice = pyqtSignal(str)
    sendText = pyqtSignal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout()  # 新增的水平布局

        # 設置主要視窗部件
        self.imageLabel = ImageLabel(self)
        self.imageLabel.setBorderRadius(2, 2, 2, 2)
        self.responseBodyLabel = PlainTextEdit(self)
        self.responseBodyLabel.setReadOnly(True)
        self.responseBodyLabel.hide()
        self.waitResponseProcessRing = IndeterminateProgressBar(self)
        self.waitResponseProcessRing.hide()

        # 設置字體和佈局
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.label, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.imageLabel, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.responseBodyLabel, 1, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.waitResponseProcessRing, 0, Qt.AlignCenter)

        # 新增的功能按鈕和輸入框
        self.captureWindowBtn = ToolButton(FIF.CUT, self)
        self.pasteTextBtn = ToolButton(FIF.CLIPPING_TOOL, self)
        self.inputText = LineEdit(self)
        self.inputText.setText("TLDR: and use traditional chinese response.")
        self.sendBtn = ToolButton(FIF.SEND, self)

        # 連接按鈕信號到槽函數
        self.captureWindowBtn.clicked.connect(lambda: self.captureWindow())
        self.pasteTextBtn.clicked.connect(lambda: self.pasteText())
        self.sendBtn.clicked.connect(lambda: self.sendTextMessage())

        # 添加按鈕和輸入框到水平布局
        self.hBoxLayout.addWidget(self.captureWindowBtn)
        self.hBoxLayout.addWidget(self.pasteTextBtn)
        self.hBoxLayout.addWidget(self.inputText, 1)  # 伸展以填充空間
        self.hBoxLayout.addWidget(self.sendBtn)

        # 添加水平布局到主垂直布局
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.setObjectName(text.replace(' ', '-'))
        
        # 其餘初始化操作
        self.window_capture = WindowCapture(self.onCaptureCompleted)
        self.window_capture.hide()
        self.chatgpt_service = ChatGPTService()
        self.sendImage.connect(self.chatgpt_service.sendImage)
        self.textToVoice.connect(self.chatgpt_service.textToVoice)
        
        self.thread = QThread()
        self.chatgpt_service.moveToThread(self.thread)
        self.thread.start()
        self.chatgpt_service.responseReady.connect(self.displayChatGPTResponse)
        
        self.waitResponseProcessRing.setMinimumWidth(self.responseBodyLabel.width())

    def captureWindow(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.showWindow.emit(False)
        QTimer.singleShot(500, lambda: self.doCaptureWindow())
        
    def doCaptureWindow(self):
        self.window_capture.update_full_screen_pixmap()
        self.window_capture.show()
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
        self.responseBodyLabel.setMinimumWidth(scaled_screenshot.width())
        self.waitResponseProcessRing.setMinimumWidth(self.responseBodyLabel.width())
        self.imageLabel.setImage(scaled_screenshot)
        self.sendImage.emit(captured_pixmap, self.inputText.text())        
        self.showWindow.emit(True)        
        self.window_capture.hide()
        
    def textToImage(self, text: str):
        # 創建底色為白色的圖片
        width, height = 640, 480
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor('white'))

        # 使用 QPainter 繪製文字
        painter = QPainter(pixmap)
        painter.setPen(QColor('black'))
        
        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)

        # 設定文字區域和對齊方式
        text_rect = pixmap.rect()  # 文字區域為整個圖片區域
        flags = Qt.AlignLeft | Qt.TextWordWrap  # 居中對齊，並啟用單詞換行

        # 使用 drawText 方法繪製文字
        painter.drawText(text_rect, flags, text)
        painter.end()

        return pixmap

    def pasteText(self):
        clipboard = QApplication.clipboard()
        #self.inputText.setText(clipboard.text())
        image = self.textToImage(clipboard.text())
        self.imageLabel.setImage(image)
        self.sendImage.emit(image, self.inputText.text())
        self.waitResponseProcessRing.show()
        self.waitResponseProcessRing.start()
        self.responseBodyLabel.setMinimumWidth(image.width())
        self.waitResponseProcessRing.setMinimumWidth(self.responseBodyLabel.width())

    def sendTextMessage(self):
        message = self.inputText.text()
        if message:
            self.sendText.emit(message)  # 發送輸入的文本
            self.inputText.clear()  # 清空輸入框

    def displayChatGPTResponse(self, response):
        self.waitResponseProcessRing.stop()
        self.waitResponseProcessRing.hide()
        self.responseBodyLabel.show()
        self.responseBodyLabel.setPlainText(response)
        self.textToVoice.emit(response)
