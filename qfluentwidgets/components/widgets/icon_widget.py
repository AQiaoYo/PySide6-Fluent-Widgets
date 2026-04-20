# coding: utf-8
"""提供图标显示控件

该模块包含 IconWidget 类，用于在界面中展示图标资源，支持 QIcon、字符串路径以及 FluentIconBase 对象作为图标源，适用于工具栏、导航栏等需要展示图标的场景
"""

from typing import Union

from PySide6.QtCore import Property
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QWidget

from ...common.icon import FluentIconBase, drawIcon, toQIcon
from ...common.overload import singledispatchmethod


class IconWidget(QWidget):
    """用于显示图标的控件
    
    可用于按钮、工具栏、列表项等需要展示图标的场景，支持 QIcon、字符串路径以及 FluentIconBase 对象作为图标输入并响应鼠标交互状态变化
    
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