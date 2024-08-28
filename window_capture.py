# coding:utf-8
# window_capture.py

from PyQt5.QtCore import Qt, QRect, QBuffer, QIODevice
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QWidget

class WindowCapture(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.update_full_screen_pixmap()
        #self.setWindowOpacity(0.1)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)   
        self.setWindowFlag(Qt.FramelessWindowHint)     
        self.selecting = False
        self.start_point = None
        self.end_point = None
        self.callback = callback
        self.showFullScreen()
        self.show()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selecting = False
            self.start_point = None
            self.end_point = None
            self.full_screen_pixmap = None
            self.callback(self.full_screen_pixmap)
            QApplication.setOverrideCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.start_point = event.pos()

    def update_full_screen_pixmap(self):
        mouse_pos = QCursor.pos()
        screen = QApplication.screenAt(mouse_pos)
        if screen:
            self.full_screen_pixmap = screen.grabWindow(0)
        else:
            self.full_screen_pixmap = QPixmap(QApplication.primaryScreen().grabWindow(0))

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
        painter.fillRect(self.rect(), QBrush(QColor(255, 255, 255, 1)))
        painter.end()
            
        if self.selecting and self.start_point and self.end_point:                    
            painter.begin(self)
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.fillRect(rect, QColor(255, 255, 255, 150))
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.end()
            
    def get_capture_selected_area(self):
        rect = QRect(self.start_point, self.end_point).normalized()
        pic_real_size = self.full_screen_pixmap.size()
        win_size = self.size()
        real_rect_x = int(rect.x() * pic_real_size.width() / win_size.width())
        real_rect_y = int(rect.y() * pic_real_size.height() / win_size.height())
        real_rect_w = int(rect.width() * pic_real_size.width() / win_size.width())
        real_rect_h = int(rect.height() * pic_real_size.height() / win_size.height())

        img_rect = QRect(real_rect_x, real_rect_y, real_rect_w, real_rect_h)
        captured_pixmap = self.full_screen_pixmap.copy(img_rect)
        return captured_pixmap, img_rect

    def capture_selected_area(self):        
        image, _ = self.get_capture_selected_area()
        self.callback(image)
        QApplication.setOverrideCursor(Qt.ArrowCursor)

