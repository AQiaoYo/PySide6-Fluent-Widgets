"""提供屏幕相关功能的工具函数"""

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication


def getCurrentScreen():
    """获取鼠标指针当前所在的屏幕

    Returns:
        QScreen | None: 鼠标所在的屏幕，未找到时返回 None
    """
    cursorPos = QCursor.pos()

    for s in QApplication.screens():
        if s.geometry().contains(cursorPos):
            return s

    return None


def getCurrentScreenGeometry(avaliable=True):
    """获取当前屏幕的几何区域

    Args:
        avaliable: 是否返回可用区域（排除任务栏等），默认为 True

    Returns:
        QRect: 屏幕的几何区域，未获取到屏幕时返回默认的 QRect(0, 0, 1920, 1080)
    """
    screen = getCurrentScreen() or QApplication.primaryScreen()

    # this should not happen
    if not screen:
        return QRect(0, 0, 1920, 1080)

    return screen.availableGeometry() if avaliable else screen.geometry()