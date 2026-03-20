# coding: utf-8
from typing import Union
from PySide6.QtCore import QPoint, Qt, QRect, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPainterPath, QIcon, QImage
from PySide6.QtWidgets import QWidget

from ...common.style_sheet import isDarkTheme
from ...common.icon import FluentIconBase
from ..widgets.flyout import FlyoutAnimationType, FlyoutViewBase, FlyoutView, Flyout, FlyoutAnimationManager
from .acrylic_widget import AcrylicWidget


class AcrylicFlyoutViewBase(AcrylicWidget, FlyoutViewBase):
    """ 亚克力 浮出层 视图 base """

    def acrylicClipPath(self):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 8, 8)
        return path

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        self._drawAcrylic(painter)

        # 绘制边框
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self.borderColor())
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)


class AcrylicFlyoutView(AcrylicWidget, FlyoutView):
    """ 亚克力 浮出层 视图 """

    def acrylicClipPath(self):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 8, 8)
        return path

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        self._drawAcrylic(painter)

        # 绘制边框
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self.borderColor())
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)


class AcrylicFlyout(Flyout):
    """ 亚克力 浮出层 """

    @classmethod
    def create(cls, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
               image: Union[str, QPixmap, QImage] = None, isClosable=False, target: Union[QWidget, QPoint] = None,
               parent=None, aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True):
        """ 创建and 显示 浮出层 using default 视图

        参数
        ----------
        title: str
            标题 的 教学提示

        content: str
            内容 的 教学提示

        icon: InfoBarIcon | FluentIconBase | QIcon | str
            图标 的 教学提示

        image: str | QPixmap | QImage
            图像 的 教学提示

        isClosable: bool
            是否 到 显示 关闭 按钮

        target: QWidget | QPoint
            目标 部件 或 位置 到 显示 浮出层

        parent: QWidget
            父部件 窗口

        aniType: FlyoutAnimationType
            浮出层 动画 type

        isDeleteOnClose: bool
            是否 delete 浮出层 automatically 当 浮出层 is closed
        """
        view = AcrylicFlyoutView(title, content, icon, image, isClosable)
        w = cls.make(view, target, parent, aniType, isDeleteOnClose)
        view.closed.connect(w.close)
        return w

    def exec(self, pos: QPoint, aniType=FlyoutAnimationType.PULL_UP):
        """ 显示日历视图 """
        self.aniManager = FlyoutAnimationManager.make(aniType, self)

        if isinstance(self.view, AcrylicWidget):
            pos = self.aniManager._adjustPosition(pos)
            self.view.acrylicBrush.grabImage(QRect(pos, self.layout().sizeHint()))

        self.show()
        self.aniManager.exec(pos)