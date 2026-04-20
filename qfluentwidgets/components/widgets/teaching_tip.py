# coding: utf-8
from enum import Enum
from typing import Union

from PySide6.QtCore import Qt, QPoint, QObject, QPointF, QTimer, QPropertyAnimation, QEvent
from PySide6.QtGui import QPainter, QColor, QPainterPath, QIcon, QCursor, QPolygonF, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QHBoxLayout, QApplication, QGraphicsDropShadowEffect

from ...common.icon import FluentIconBase
from ...common.screen import getCurrentScreenGeometry
from ...common.style_sheet import isDarkTheme
from .flyout import FlyoutView, FlyoutViewBase


class TeachingTipTailPosition(Enum):
    """教学提示尾部位置
    用于指定 TeachingTip 气泡框尾部箭头相对于内容区域的方位，
    与 TeachingTipManager 配合使用时决定提示框的弹出方向
    """
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3
    TOP_LEFT = 4
    TOP_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_RIGHT = 7
    LEFT_TOP = 8
    LEFT_BOTTOM = 9
    RIGHT_TOP = 10
    RIGHT_BOTTOM = 11
    NONE = 12


class ImagePosition(Enum):
    """图片在提示框中的显示位置
    用于控制 TeachingTipView 中配图相对于文本内容的布局方式，
    支持设置图片位于文本上方、下方或左右两侧以适应不同内容结构
    """
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3


class TeachingTipView(FlyoutView):
    """教学提示视图
    负责构建提示框的内部布局，支持标题、正文、图标、配图及操作按钮的组合展示，
    可通过 addWidget 等方法向底部按钮区域追加自定义控件以扩展交互能力
    """

    def __init__(self, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
                 image: Union[str, QPixmap, QImage] = None, isClosable=True, tailPosition=TeachingTipTailPosition.BOTTOM,
                 parent=None):
        """Args:
            title (str): 提示标题，显示在内容区顶部
            content (str): 提示正文，支持富文本格式
            icon (QIcon | None): 标题左侧的图标，None 时不显示图标
            image (str | QPixmap | None): 提示配图的路径或像素图，None 时不显示配图
            isClosable (bool): 是否显示关闭按钮，True 时允许用户手动关闭提示
            tailPosition (TeachingTipTailPosition): 尾部箭头方位，影响内容区与气泡边框的间距
            parent (QWidget | None): 父控件
        """
        self.manager = TeachingTipManager.make(tailPosition)
        self.hBoxLayout = QHBoxLayout()
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        super().__init__(title, content, icon, image, isClosable, parent)

    def _adjustImage(self):
        if self.manager.imagePosition() in [ImagePosition.TOP, ImagePosition.BOTTOM]:
            return super()._adjustImage()

        h = self.vBoxLayout.sizeHint().height() - 2
        self.imageLabel.scaledToHeight(h)

    def _addImageToLayout(self):
        self.imageLabel.setHidden(self.imageLabel.isNull())
        pos = self.manager.imagePosition()

        if pos == ImagePosition.TOP:
            self.imageLabel.setBorderRadius(8, 8, 0, 0)
            self.vBoxLayout.insertWidget(0, self.imageLabel)
        elif pos == ImagePosition.BOTTOM:
            self.imageLabel.setBorderRadius(0, 0, 8, 8)
            self.vBoxLayout.addWidget(self.imageLabel)
        elif pos == ImagePosition.LEFT:
            self.vBoxLayout.removeItem(self.vBoxLayout.itemAt(0))
            self.hBoxLayout.addLayout(self.viewLayout)
            self.vBoxLayout.addLayout(self.hBoxLayout)

            self.imageLabel.setBorderRadius(8, 0, 8, 0)
            self.hBoxLayout.insertWidget(0, self.imageLabel)
        elif pos == ImagePosition.RIGHT:
            self.vBoxLayout.removeItem(self.vBoxLayout.itemAt(0))
            self.hBoxLayout.addLayout(self.viewLayout)
            self.vBoxLayout.addLayout(self.hBoxLayout)

            self.imageLabel.setBorderRadius(0, 8, 0, 8)
            self.hBoxLayout.addWidget(self.imageLabel)

    def paintEvent(self, e):
        pass


class TeachTipBubble(QWidget):
    """教学提示气泡
    承载 TeachingTipView 的圆角气泡窗口，负责绘制背景、边框和尾部箭头，
    通常不应直接使用，而是通过 TeachingTip 或 PopupTeachingTip 进行创建与管理
    """

    def __init__(self, view: FlyoutViewBase, tailPosition=TeachingTipTailPosition.BOTTOM, parent=None):
        """Args:
            view (TeachingTipView): 气泡内部需要展示的教学提示视图
            tailPosition (TeachingTipTailPosition): 尾部箭头方位，决定气泡形状与留白
            parent (QWidget | None): 父控件
        """
        super().__init__(parent=parent)
        self.manager = TeachingTipManager.make(tailPosition)
        self.hBoxLayout = QHBoxLayout(self)
        self.view = view

        self.manager.doLayout(self)
        self.hBoxLayout.addWidget(self.view)

    def setView(self, view: QWidget):
        self.hBoxLayout.removeWidget(self.view)
        self.view.deleteLater()
        self.view = view
        self.hBoxLayout.addWidget(view)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setBrush(
            QColor(40, 40, 40) if isDarkTheme() else QColor(248, 248, 248))
        painter.setPen(
            QColor(23, 23, 23) if isDarkTheme() else QColor(0, 0, 0, 17))

        self.manager.draw(self, painter)


class TeachingTip(QWidget):
    """非弹出式教学提示
    直接嵌入到界面布局中的提示组件，不依赖目标控件定位，
    适用于需要常驻显示或跟随界面滚动的引导场景，与 PopupTeachingTip 的临时弹出特性形成互补
    """

    def __init__(self, view: FlyoutViewBase, target: QWidget, duration=1000,
                 tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose=True):
        """初始化并显示教学提示
        
        Args:
            view: 教学提示视图
            target: 目标部件
            duration: 教学提示显示时长，单位为毫秒。如果时长小于 0，教学提示将不会自动消失
            tailPosition: 气泡尾巴的位置
            parent: 父部件
            isDeleteOnClose: 浮出层关闭后是否自动删除
        """
        super().__init__(parent=parent)
        self.target = target
        self.duration = duration
        self.isDeleteOnClose = isDeleteOnClose
        self.manager = TeachingTipManager.make(tailPosition)

        self.hBoxLayout = QHBoxLayout(self)
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity', self)

        self.bubble = TeachTipBubble(view, tailPosition, self)

        self.hBoxLayout.setContentsMargins(15, 8, 15, 20)
        self.hBoxLayout.addWidget(self.bubble)
        self.setShadowEffect()

        # 设置 style
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

        if parent and parent.window():
            parent.window().installEventFilter(self)

    def setShadowEffect(self, blurRadius=35, offset=(0, 8)):
        """添加阴影效果
        
        Args:
            blurRadius: 模糊半径
            offset: 阴影偏移量
        """
        color = QColor(0, 0, 0, 80 if isDarkTheme() else 30)
        self.shadowEffect = QGraphicsDropShadowEffect(self.bubble)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.bubble.setGraphicsEffect(None)
        self.bubble.setGraphicsEffect(self.shadowEffect)

    def _fadeOut(self):
        """ 淡出 """
        self.opacityAni.setDuration(167)
        self.opacityAni.setStartValue(1)
        self.opacityAni.setEndValue(0)
        self.opacityAni.finished.connect(self.close)
        self.opacityAni.start()

    def showEvent(self, e):
        if self.duration >= 0:
            QTimer.singleShot(self.duration, self._fadeOut)

        self.move(self.manager.position(self))
        self.adjustSize()
        self.opacityAni.setDuration(167)
        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()
        super().showEvent(e)

    def closeEvent(self, e):
        if self.isDeleteOnClose:
            self.deleteLater()

        super().closeEvent(e)

    def eventFilter(self, obj, e: QEvent):
        if self.parent() and obj is self.parent().window():
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange, QEvent.Move]:
                self.move(self.manager.position(self))

        return super().eventFilter(obj, e)

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        """向教学提示中添加部件
        
        Args:
            widget: 要添加的部件
            stretch: 拉伸因子
            align: 对齐方式
        """
        self.view.addSpacing(8)
        self.view.addWidget(widget, stretch, align)

    @property
    def view(self):
        return self.bubble.view

    def setView(self, view):
        self.bubble.setView(view)

    @classmethod
    def make(cls, view: FlyoutViewBase, target: QWidget, duration=1000, tailPosition=TeachingTipTailPosition.BOTTOM,
             parent=None, isDeleteOnClose=True):
        """创建教学提示
        
        Args:
            view: 教学提示视图
            target: 目标部件
            duration: 教学提示显示时长，单位为毫秒。如果时长小于 0，教学提示将不会自动消失
            tailPosition: 气泡尾巴的位置
            parent: 父部件
            isDeleteOnClose: 浮出层关闭后是否自动删除
        """
        w = cls(view, target, duration, tailPosition, parent, isDeleteOnClose)
        w.show()
        return w

    @classmethod
    def create(cls, target: QWidget, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
               image: Union[str, QPixmap, QImage] = None, isClosable=True, duration=1000,
               tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose=True):
        """创建教学提示
        
        Args:
            target: 要显示提示的目标部件
            title: 教学提示标题
            content: 教学提示内容
            icon: 教学提示图标
            image: 教学提示图片
            isClosable: 是否显示关闭按钮
            duration: 教学提示显示时长，单位为毫秒。如果时长小于 0，教学提示将不会自动消失
            tailPosition: 气泡尾巴的位置
            parent: 父部件
            isDeleteOnClose: 浮出层关闭后是否自动删除
        """
        view = TeachingTipView(title, content, icon, image, isClosable, tailPosition)
        w = cls.make(view, target, duration, tailPosition, parent, isDeleteOnClose)
        view.closed.connect(w.close)
        return w


class PopupTeachingTip(TeachingTip):
    """弹出式教学提示
    以气泡形式附着在目标控件旁边的临时提示，支持自动关闭计时，
    适用于新手引导、功能介绍等需要精准指向目标区域且无需常驻的场景
    """

    def __init__(self, view: FlyoutViewBase, target: QWidget, duration=1000,
                 tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose=True):
        """Args:
            view (TeachingTipView): 教学提示视图，定义气泡内部展示内容
            target (QWidget): 气泡箭头指向的目标控件
            duration (int): 自动关闭延迟，单位毫秒，-1 表示不自动关闭
            tailPosition (TeachingTipTailPosition): 尾部箭头方位，影响气泡弹出位置
            parent (QWidget | None): 父控件
            isDeleteOnClose (bool): 关闭时是否销毁实例，True 可避免内存泄漏
        """
        super().__init__(view, target, duration, tailPosition, parent, isDeleteOnClose)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)


class TeachingTipManager(QObject):
    """教学提示位置管理器
    负责根据目标控件的几何信息与尾部方位，计算气泡应弹出的屏幕坐标，
    子类通过重写 position 方法实现不同的定位策略，通常与 PopupTeachingTip 配合使用以完成精准定位
    """

    def __init__(self):
        """初始化教学提示位置管理器
        Args:
            无
        """
        super().__init__()

    def doLayout(self, tip: TeachTipBubble):
        """管理 tip 的布局
        
        Args:
            tip: 教学提示气泡
        """
        tip.hBoxLayout.setContentsMargins(0, 0, 0, 0)

    def imagePosition(self):
        return ImagePosition.TOP

    def position(self, tip: TeachingTip) -> QPoint:
        pos = self._pos(tip)
        x, y = pos.x(), pos.y()

        rect = getCurrentScreenGeometry()
        x = max(rect.left(), min(pos.x(), rect.right() - tip.width() - 4))
        y = max(rect.top(), min(pos.y(), rect.bottom() - tip.height() - 4))

        return QPoint(x, y)

    def draw(self, tip: TeachTipBubble, painter: QPainter):
        """绘制气泡外形
        
        Args:
            tip: 教学提示气泡
            painter: 画笔
        """
        rect = tip.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)

    def _pos(self, tip: TeachingTip):
        """返回 tip 的位置
        
        Args:
            tip: 教学提示
        
        Returns:
            tip 的位置
        """
        return tip.pos()

    @staticmethod
    def make(position: TeachingTipTailPosition):
        """根据显示位置创建教学提示尾部管理器
        
        Args:
            position: 尾部位置
        """
        managers = {
            TeachingTipTailPosition.TOP: TopTailTeachingTipManager,
            TeachingTipTailPosition.BOTTOM: BottomTailTeachingTipManager,
            TeachingTipTailPosition.LEFT: LeftTailTeachingTipManager,
            TeachingTipTailPosition.RIGHT: RightTailTeachingTipManager,
            TeachingTipTailPosition.TOP_RIGHT: TopRightTailTeachingTipManager,
            TeachingTipTailPosition.BOTTOM_RIGHT: BottomRightTailTeachingTipManager,
            TeachingTipTailPosition.TOP_LEFT: TopLeftTailTeachingTipManager,
            TeachingTipTailPosition.BOTTOM_LEFT: BottomLeftTailTeachingTipManager,
            TeachingTipTailPosition.LEFT_TOP: LeftTopTailTeachingTipManager,
            TeachingTipTailPosition.LEFT_BOTTOM: LeftBottomTailTeachingTipManager,
            TeachingTipTailPosition.RIGHT_TOP: RightTopTailTeachingTipManager,
            TeachingTipTailPosition.RIGHT_BOTTOM: RightBottomTailTeachingTipManager,
            TeachingTipTailPosition.NONE: TeachingTipManager,
        }

        if position not in managers:
            raise ValueError(
                f'`{position}` is an invalid teaching tip position.')

        return managers[position]()


class TopTailTeachingTipManager(TeachingTipManager):
    """顶部尾部教学提示管理器
    气泡尾部箭头位于目标控件上方，提示框整体显示在目标下方，
    适用于目标控件上方空间不足，需要在下方展示引导信息的场景
    """

    def doLayout(self, tip):
        tip.hBoxLayout.setContentsMargins(0, 8, 0, 0)

    def imagePosition(self):
        return ImagePosition.BOTTOM

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pt = tip.hBoxLayout.contentsMargins().top()

        path = QPainterPath()
        path.addRoundedRect(1, pt, w - 2, h - pt - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w/2 - 7, pt), QPointF(w/2, 1), QPointF(w/2 + 7, pt)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() + target.width()//2 - tip.sizeHint().width()//2
        y = pos.y() - tip.layout().contentsMargins().top()
        return QPoint(x, y)


class BottomTailTeachingTipManager(TeachingTipManager):
    """底部尾部教学提示管理器
    气泡尾部箭头位于目标控件下方，提示框整体显示在目标上方，
    适用于目标控件下方空间不足，需要在上方展示引导信息的场景
    """

    def doLayout(self, tip):
        tip.hBoxLayout.setContentsMargins(0, 0, 0, 8)

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pb = tip.hBoxLayout.contentsMargins().bottom()

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - 2, h - pb - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w/2 - 7, h - pb), QPointF(w/2, h - 1), QPointF(w/2 + 7, h - pb)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint())
        x = pos.x() + target.width()//2 - tip.sizeHint().width()//2
        y = pos.y() - tip.sizeHint().height() + tip.layout().contentsMargins().bottom()
        return QPoint(x, y)


class LeftTailTeachingTipManager(TeachingTipManager):
    """左侧尾部教学提示管理器
    气泡尾部箭头位于目标控件左侧，提示框整体显示在目标右侧，
    适用于目标控件左侧有遮挡或需要在右侧展示引导信息的场景
    """

    def doLayout(self, tip):
        tip.hBoxLayout.setContentsMargins(8, 0, 0, 0)

    def imagePosition(self):
        return ImagePosition.RIGHT

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pl = 8

        path = QPainterPath()
        path.addRoundedRect(pl, 1, w - pl - 2, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(pl, h/2 - 7), QPointF(1, h/2), QPointF(pl, h/2 + 7)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(target.width(), 0))
        x = pos.x() - m.left()
        y = pos.y() - tip.view.sizeHint().height()//2 + target.height()//2 - m.top()
        return QPoint(x, y)


class RightTailTeachingTipManager(TeachingTipManager):
    """右侧尾部教学提示管理器
    气泡尾部箭头位于目标控件右侧，提示框整体显示在目标左侧，
    适用于目标控件右侧有遮挡或需要在左侧展示引导信息的场景
    """

    def doLayout(self, tip):
        tip.hBoxLayout.setContentsMargins(0, 0, 8, 0)

    def imagePosition(self):
        return ImagePosition.LEFT

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pr = 8

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - pr - 1, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w - pr, h/2 - 7), QPointF(w - 1, h/2), QPointF(w - pr, h/2 + 7)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(0, 0))
        x = pos.x() - tip.sizeHint().width() + m.right()
        y = pos.y() - tip.view.sizeHint().height()//2 + target.height()//2 - m.top()
        return QPoint(x, y)


class TopLeftTailTeachingTipManager(TopTailTeachingTipManager):
    """顶部左侧尾部教学提示管理器
    气泡尾部箭头位于目标控件顶部的左侧区域，提示框向下展开，
    适用于需要在目标控件下方偏左位置精准定位提示的场景
    """

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pt = tip.hBoxLayout.contentsMargins().top()

        path = QPainterPath()
        path.addRoundedRect(1, pt, w - 2, h - pt - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(20, pt), QPointF(27, 1), QPointF(34, pt)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() - tip.layout().contentsMargins().left()
        y = pos.y() - tip.layout().contentsMargins().top()
        return QPoint(x, y)


class TopRightTailTeachingTipManager(TopTailTeachingTipManager):
    """顶部右侧尾部教学提示管理器
    气泡尾部箭头位于目标控件顶部的右侧区域，提示框向下展开，
    适用于需要在目标控件下方偏右位置精准定位提示的场景
    """

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pt = tip.hBoxLayout.contentsMargins().top()

        path = QPainterPath()
        path.addRoundedRect(1, pt, w - 2, h - pt - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w - 20, pt), QPointF(w - 27, 1), QPointF(w - 34, pt)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint(target.width(), target.height()))
        x = pos.x() - tip.sizeHint().width() + tip.layout().contentsMargins().left()
        y = pos.y() - tip.layout().contentsMargins().top()
        return QPoint(x, y)


class BottomLeftTailTeachingTipManager(BottomTailTeachingTipManager):
    """底部左侧尾部教学提示管理器
    气泡尾部箭头位于目标控件底部的左侧区域，提示框向上展开，
    适用于需要在目标控件上方偏左位置精准定位提示的场景
    """

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pb = tip.hBoxLayout.contentsMargins().bottom()

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - 2, h - pb - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(20, h - pb), QPointF(27, h - 1), QPointF(34, h - pb)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint())
        x = pos.x() - tip.layout().contentsMargins().left()
        y = pos.y() - tip.sizeHint().height() + tip.layout().contentsMargins().bottom()
        return QPoint(x, y)


class BottomRightTailTeachingTipManager(BottomTailTeachingTipManager):
    """底部右侧尾部教学提示管理器
    气泡尾部箭头位于目标控件底部的右侧区域，提示框向上展开，
    适用于需要在目标控件上方偏右位置精准定位提示的场景
    """

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pb = tip.hBoxLayout.contentsMargins().bottom()

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - 2, h - pb - 1, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w - 20, h - pb), QPointF(w - 27, h - 1), QPointF(w - 34, h - pb)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        pos = target.mapToGlobal(QPoint(target.width(), 0))
        x = pos.x() - tip.sizeHint().width() + tip.layout().contentsMargins().left()
        y = pos.y() - tip.sizeHint().height() + tip.layout().contentsMargins().bottom()
        return QPoint(x, y)


class LeftTopTailTeachingTipManager(LeftTailTeachingTipManager):
    """左侧顶部尾部教学提示管理器
    气泡尾部箭头位于目标控件左侧的顶部区域，提示框向右展开，
    适用于需要在目标控件右侧偏上位置精准定位提示的场景
    """

    def imagePosition(self):
        return ImagePosition.BOTTOM

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pl = 8

        path = QPainterPath()
        path.addRoundedRect(pl, 1, w - pl - 2, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(pl, 10), QPointF(1, 17), QPointF(pl, 24)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(target.width(), 0))
        x = pos.x() - m.left()
        y = pos.y() - m.top()
        return QPoint(x, y)


class LeftBottomTailTeachingTipManager(LeftTailTeachingTipManager):
    """左侧底部尾部教学提示管理器
    气泡尾部箭头位于目标控件左侧的底部区域，提示框向右展开，
    适用于需要在目标控件右侧偏下位置精准定位提示的场景
    """

    def imagePosition(self):
        return ImagePosition.TOP

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pl = 9

        path = QPainterPath()
        path.addRoundedRect(pl, 1, w - pl - 1, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(pl, h - 10), QPointF(1, h - 17), QPointF(pl, h - 24)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(target.width(), target.height()))
        x = pos.x() - m.left()
        y = pos.y() - tip.sizeHint().height() + m.bottom()
        return QPoint(x, y)


class RightTopTailTeachingTipManager(RightTailTeachingTipManager):
    """右侧顶部尾部教学提示管理器
    气泡尾部箭头位于目标控件右侧的顶部区域，提示框向左展开，
    适用于需要在目标控件左侧偏上位置精准定位提示的场景
    """

    def imagePosition(self):
        return ImagePosition.BOTTOM

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pr = 8

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - pr - 1, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w - pr, 10), QPointF(w - 1, 17), QPointF(w - pr, 24)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(0, 0))
        x = pos.x() - tip.sizeHint().width() + m.right()
        y = pos.y() - m.top()
        return QPoint(x, y)


class RightBottomTailTeachingTipManager(RightTailTeachingTipManager):
    """右侧底部尾部教学提示管理器
    气泡尾部箭头位于目标控件右侧的底部区域，提示框向左展开，
    适用于需要在目标控件左侧偏下位置精准定位提示的场景
    """

    def imagePosition(self):
        return ImagePosition.TOP

    def draw(self, tip, painter):
        w, h = tip.width(), tip.height()
        pr = 8

        path = QPainterPath()
        path.addRoundedRect(1, 1, w - pr - 1, h - 2, 8, 8)
        path.addPolygon(
            QPolygonF([QPointF(w - pr, h-10), QPointF(w - 1, h-17), QPointF(w - pr, h-24)]))

        painter.drawPath(path.simplified())

    def _pos(self, tip: TeachingTip):
        target = tip.target
        m = tip.layout().contentsMargins()
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() - tip.sizeHint().width() + m.right()
        y = pos.y() - tip.sizeHint().height() + m.bottom()
        return QPoint(x, y)
