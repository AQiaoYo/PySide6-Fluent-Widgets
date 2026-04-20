# coding: utf-8
from PySide6.QtCore import QEasingCurve, Qt, QPropertyAnimation
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea, QScrollBar

from ...common.smooth_scroll import SmoothScroll, SmoothMode
from .scroll_bar import ScrollBar, SmoothScrollBar, SmoothScrollDelegate


class ScrollArea(QScrollArea):
    """平滑滚动区域
    用于展示超出可视区域的内容，支持垂直与水平双向滚动，适用于长列表、大图片浏览等场景
    提供流畅的滚动体验并支持自定义滚动条样式，可作为复杂布局的容器基类
    """

    def __init__(self, parent=None):
        """初始化滚动区域
        
        Args:
            parent: 父控件，类型为 QWidget，None 表示作为顶级窗口
        """
        super().__init__(parent)
        self.scrollDelagate = SmoothScrollDelegate(self)

    def setSmoothMode(self, mode: SmoothMode, orientation: Qt.Orientation):
        """设置平滑模式
        
        Args:
            mode (SmoothMode): smooth 滚动模式
            orientation (Qt.Orientation): 滚动方向
        """
        if orientation == Qt.Orientation.Vertical:
            self.scrollDelagate.verticalSmoothScroll.setSmoothMode(mode)
        else:
            self.scrollDelagate.horizonSmoothScroll.setSmoothMode(mode)

    def enableTransparentBackground(self):
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        if self.widget():
            self.widget().setStyleSheet("QWidget{background: transparent}")


class SingleDirectionScrollArea(QScrollArea):
    """单方向滚动区域
    限制内容仅在水平或垂直单一方向上滚动，适用于横向时间轴、纵向消息列表等线性布局场景
    自动屏蔽另一方向的滚动事件，避免误触导致页面偏移
    """

    def __init__(self, parent=None, orient=Qt.Vertical):
        """构造函数
        
        Args:
            parent (QWidget): 父部件
            orient (Orientation): 滚动 orientation
        """
        super().__init__(parent)
        self.orient = orient
        self.smoothScroll = SmoothScroll(self, orient)
        self.vScrollBar = SmoothScrollBar(Qt.Vertical, self)
        self.hScrollBar = SmoothScrollBar(Qt.Horizontal, self)

    def setVerticalScrollBarPolicy(self, policy):
        super().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setHorizontalScrollBarPolicy(self, policy):
        super().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hScrollBar.setForceHidden(policy == Qt.ScrollBarAlwaysOff)

    def setSmoothMode(self, mode):
        """设置平滑模式
        
        Args:
            mode (SmoothMode): smooth 滚动模式
        """
        self.smoothScroll.setSmoothMode(mode)

    def keyPressEvent(self, e):
        if e.key() in [Qt.Key_Left, Qt.Key_Right]:
            return

        return super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent):
        if e.angleDelta().x() != 0:
            return

        self.smoothScroll.wheelEvent(e)
        e.setAccepted(True)

    def enableTransparentBackground(self):
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        if self.widget():
            self.widget().setStyleSheet("QWidget{background: transparent}")


class SmoothScrollArea(QScrollArea):
    """平滑滚动区域
    基于动画插值实现丝滑的滚动过渡效果，适用于对交互体验要求较高的内容展示场景
    相比普通滚动区域可有效消除滚轮切换时的生硬感，特别适合长文本阅读与信息流浏览
    """

    def __init__(self, parent=None):
        """初始化平滑滚动区域
        
        Args:
            parent: 父控件，类型为 QWidget，None 表示作为顶级窗口
        """
        super().__init__(parent)
        self.delegate = SmoothScrollDelegate(self, True)

    def setScrollAnimation(self, orient, duration, easing=QEasingCurve.OutCubic):
        """设置滚动动画
        
        Args:
            orient (Orient): 滚动 orientation
            duration (int): 滚动持续时间
            easing (QEasingCurve): 动画类型
        """
        bar = self.delegate.hScrollBar if orient == Qt.Horizontal else self.delegate.vScrollBar
        bar.setScrollAnimation(duration, easing)

    def enableTransparentBackground(self):
        self.setStyleSheet("QScrollArea{border: none; background: transparent}")

        if self.widget():
            self.widget().setStyleSheet("QWidget{background: transparent}")
