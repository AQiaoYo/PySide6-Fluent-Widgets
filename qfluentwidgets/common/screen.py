"""提供与屏幕及显示器相关的辅助工具函数

包含获取屏幕几何信息、DPI 缩放比例以及多显示器环境下窗口定位的常用方法，
主要用于适配不同分辨率与缩放比例下的界面布局，确保组件在各屏幕配置下均能正确显示
"""

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