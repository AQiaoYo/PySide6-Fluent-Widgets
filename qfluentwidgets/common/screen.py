from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication


def getCurrentScreen():
    """ 获取 当前 屏幕 """
    cursorPos = QCursor.pos()

    for s in QApplication.screens():
        if s.geometry().contains(cursorPos):
            return s

    return None


def getCurrentScreenGeometry(avaliable=True):
    """ 获取 当前 屏幕 几何区域 """
    screen = getCurrentScreen() or QApplication.primaryScreen()

    # this should not happen
    if not screen:
        return QRect(0, 0, 1920, 1080)

    return screen.availableGeometry() if avaliable else screen.geometry()