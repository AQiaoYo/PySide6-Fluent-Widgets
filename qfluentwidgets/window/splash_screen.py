# coding: utf-8
"""提供启动画面功能的模块"""

from typing import Union
import sys

from PySide6.QtCore import Qt, QSize, QRectF, QEvent
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsDropShadowEffect

from ..common.icon import FluentIconBase, drawIcon, toQIcon
from ..common.style_sheet import isDarkTheme, FluentStyleSheet
from ..components.widgets import IconWidget
from qframelesswindow import TitleBar



class SplashScreen(QWidget):
    """启动画面

    应用程序加载期间显示的居中图标窗口，支持阴影效果和自定义标题栏
    """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], parent=None, enableShadow=True):
        """初始化启动画面

        Args:
            icon: 图标，可以是图片路径、QIcon 或 FluentIconBase
            parent: 父窗口，默认为 None
            enableShadow: 是否启用图标阴影效果，默认为 True
        """
        super().__init__(parent=parent)
        self._icon = icon
        self._iconSize = QSize(96, 96)

        self.titleBar = TitleBar(self)
        self.iconWidget = IconWidget(icon, self)
        self.shadowEffect = QGraphicsDropShadowEffect(self)

        self.iconWidget.setFixedSize(self._iconSize)
        self.shadowEffect.setColor(QColor(0, 0, 0, 50))
        self.shadowEffect.setBlurRadius(15)
        self.shadowEffect.setOffset(0, 4)

        FluentStyleSheet.FLUENT_WINDOW.apply(self.titleBar)

        if enableShadow:
            self.iconWidget.setGraphicsEffect(self.shadowEffect)

        if parent:
            parent.installEventFilter(self)

        if sys.platform == "darwin":
            self.titleBar.hide()

    def setIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        """设置图标

        Args:
            icon: 图标，可以是图片路径、QIcon 或 FluentIconBase
        """
        self._icon = icon
        self.update()

    def icon(self):
        """获取图标

        Returns:
            转换后的 QIcon 对象
        """
        return toQIcon(self._icon)

    def setIconSize(self, size: QSize):
        """设置图标大小

        Args:
            size: 图标尺寸
        """
        self._iconSize = size
        self.iconWidget.setFixedSize(size)
        self.update()

    def iconSize(self):
        """获取图标大小

        Returns:
            当前图标尺寸
        """
        return self._iconSize

    def setTitleBar(self, titleBar: QWidget):
        """设置标题栏

        Args:
            titleBar: 自定义标题栏控件
        """
        self.titleBar.deleteLater()
        self.titleBar = titleBar
        titleBar.setParent(self)
        titleBar.raise_()
        self.titleBar.resize(self.width(), self.titleBar.height())

    def eventFilter(self, obj, e: QEvent):
        """过滤父窗口事件

        Args:
            obj: 事件发送对象
            e: 事件对象

        Returns:
            是否拦截该事件
        """
        if obj is self.parent():
            if e.type() == QEvent.Resize:
                self.resize(e.size())
            elif e.type() == QEvent.ChildAdded:
                self.raise_()

        return super().eventFilter(obj, e)

    def resizeEvent(self, e):
        """处理尺寸调整事件

        Args:
            e: 尺寸调整事件
        """
        iw, ih = self.iconSize().width(), self.iconSize().height()
        self.iconWidget.move(self.width()//2 - iw//2, self.height()//2 - ih//2)
        self.titleBar.resize(self.width(), self.titleBar.height())

    def finish(self):
        """关闭启动画面"""
        self.close()

    def paintEvent(self, e):
        """绘制背景和图标

        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        # 绘制背景
        c = 32 if isDarkTheme() else 255
        painter.setBrush(QColor(c, c, c))
        painter.drawRect(self.rect())