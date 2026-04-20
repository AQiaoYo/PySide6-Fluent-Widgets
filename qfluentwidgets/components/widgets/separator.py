# coding: utf-8
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QWidget

from ...common.style_sheet import isDarkTheme


class HorizontalSeparator(QWidget):
    """水平方向的分隔符控件
    
     适用于在垂直布局中插入水平分割线，对不同功能区块或相邻组件进行视觉分隔，提升界面的层次感与可读性
    """

    def __init__(self, parent=None):
        """初始化水平分隔符
        
         Args:
             parent (QWidget, optional): 父级控件，默认为 None。传入父控件时，分隔符将嵌入对应布局并随父控件一起显示
        """
        super().__init__(parent=parent)
        self.setFixedHeight(3)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 51))
        else:
            painter.setPen(QColor(0, 0, 0, 22))

        painter.drawLine(0, 1, self.width(), 1)


class VerticalSeparator(QWidget):
    """垂直方向的分隔符控件
    
     适用于在水平布局中插入垂直分割线，对不同功能区块或相邻组件进行视觉分隔，提升界面的层次感与可读性
    """

    def __init__(self, parent=None):
        """初始化垂直分隔符
        
         Args:
             parent (QWidget, optional): 父级控件，默认为 None。传入父控件时，分隔符将嵌入对应布局并随父控件一起显示
        """
        super().__init__(parent=parent)
        self.setFixedWidth(3)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 51))
        else:
            painter.setPen(QColor(0, 0, 0, 22))

        painter.drawLine(1, 0, 1, self.height())