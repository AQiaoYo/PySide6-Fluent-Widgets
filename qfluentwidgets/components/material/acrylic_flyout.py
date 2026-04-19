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
    """亚克力浮出层视图基类"""

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
    """亚克力浮出层视图"""

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
    """亚克力浮出层"""

    @classmethod
    def create(cls, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
               image: Union[str, QPixmap, QImage] = None, isClosable=False, target: Union[QWidget, QPoint] = None,
               parent=None, aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True):
        """使用默认视图创建并显示浮出层
        
        Args:
            title: 提示标题
            content: 提示内容
            icon: 图标
            image: 图片
            isClosable (bool): 是否显示关闭按钮
            target: 目标控件或位置
            parent (QWidget): 父控件
            aniType (FlyoutAnimationType): 动画类型
            isDeleteOnClose (bool): 关闭时是否自动删除
        """
        view = AcrylicFlyoutView(title, content, icon, image, isClosable)
        w = cls.make(view, target, parent, aniType, isDeleteOnClose)
        view.closed.connect(w.close)
        return w

    def exec(self, pos: QPoint, aniType=FlyoutAnimationType.PULL_UP):
        """在指定位置显示浮出层
        
        Args:
            pos: 显示位置
            aniType (FlyoutAnimationType): 动画类型
        """
        self.aniManager = FlyoutAnimationManager.make(aniType, self)

        if isinstance(self.view, AcrylicWidget):
            pos = self.aniManager._adjustPosition(pos)
            self.view.acrylicBrush.grabImage(QRect(pos, self.layout().sizeHint()))

        self.show()
        self.aniManager.exec(pos)
