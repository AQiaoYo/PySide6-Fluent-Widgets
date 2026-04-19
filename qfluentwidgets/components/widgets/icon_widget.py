# coding: utf-8
"""图标控件"""

from typing import Union

from PySide6.QtCore import Property
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QWidget

from ...common.icon import FluentIconBase, drawIcon, toQIcon
from ...common.overload import singledispatchmethod


class IconWidget(QWidget):
    """图标控件

    构造函数重载:
        * IconWidget(parent=None)
        * IconWidget(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化图标控件

        Args:
            parent: 父控件，默认为 None
        """
        super().__init__(parent)
        self.setIcon(QIcon())

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        """初始化图标控件

        Args:
            icon: 图标
            parent: 父控件，默认为 None
        """
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        """初始化图标控件

        Args:
            icon: 图标
            parent: 父控件，默认为 None
        """
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        """初始化图标控件

        Args:
            icon: 图标
            parent: 父控件，默认为 None
        """
        self.__init__(parent)
        self.setIcon(icon)

    def getIcon(self):
        """获取图标

        Returns:
            图标
        """
        return toQIcon(self._icon)

    def setIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        """设置图标

        Args:
            icon: 图标
        """
        self._icon = icon
        self.update()

    def paintEvent(self, e):
        """绘制图标

        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())

    icon = Property(QIcon, getIcon, setIcon)