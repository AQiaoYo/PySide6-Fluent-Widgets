# coding: utf-8
"""浮出层组件，提供轻量级的弹出式信息提示与交互能力
适用于显示操作确认、消息通知、附加选项等场景，支持多种弹出方向和动画效果
"""

from enum import Enum
import sys
from typing import Union

from PySide6.QtCore import (Qt, QPropertyAnimation, QPoint, QParallelAnimationGroup, QEasingCurve, QMargins,
                          QRectF, QObject, QSize, Signal, QEvent)
from PySide6.QtGui import QPixmap, QPainter, QColor, QCursor, QIcon, QImage, QPainterPath, QBrush, QMovie, QImageReader
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QLabel, QHBoxLayout, QVBoxLayout, QApplication

from ...common.auto_wrap import TextWrap
from ...common.style_sheet import isDarkTheme, FluentStyleSheet
from ...common.icon import FluentIconBase, drawIcon, FluentIcon
from ...common.screen import getCurrentScreenGeometry
from .button import TransparentToolButton
from .label import ImageLabel


class FlyoutAnimationType(Enum):
    """浮出层动画类型枚举
    定义了浮出层显示和隐藏时可使用的动画效果，可根据目标控件相对位置选择合适的动画类型
    """
    PULL_UP = 0
    DROP_DOWN = 1
    SLIDE_LEFT = 2
    SLIDE_RIGHT = 3
    FADE_IN = 4
    NONE = 5


class IconWidget(QWidget):
    """浮出层图标控件
    用于在 FlyoutView 中展示图标，支持 FluentIconBase 与 QIcon，可通过图标直观传达信息类型
    """

    def __init__(self, icon, parent=None):
        """创建图标控件实例
        
        Args:
            icon: 图标，支持 FluentIconBase 与 QIcon 类型
            parent: 父控件，通常为 FlyoutView 实例
        """
        super().__init__(parent=parent)
        self.setFixedSize(36, 54)
        self.icon = icon

    def paintEvent(self, e):
        if not self.icon:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        rect = QRectF(8, (self.height()-20)/2, 20, 20)
        drawIcon(self.icon, painter, rect)


class FlyoutViewBase(QWidget):
    """浮出视图基类
    定义了浮出内容的基本接口与布局规范，自定义浮出视图时应继承此类并实现相关接口
    """

    def __init__(self, parent=None):
        """初始化浮出视图基类
        
        Args:
            parent: 父控件，用于指定该视图的父级容器
        """
        super().__init__(parent=parent)

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        raise NotImplementedError

    def backgroundColor(self):
        return QColor(40, 40, 40) if isDarkTheme() else QColor(248, 248, 248)

    def borderColor(self):
        return QColor(0, 0, 0, 45) if isDarkTheme() else QColor(0, 0, 0, 17)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setBrush(self.backgroundColor())
        painter.setPen(self.borderColor())

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)


class FlyoutView(FlyoutViewBase):
    """标准浮出视图
    内置标题、内容文本、图标和可选的关闭按钮，适用于大多数信息提示与轻量级交互场景
    """

    closed = Signal()

    def __init__(self, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
                 image: Union[str, QPixmap, QImage] = None, isClosable=False, parent=None):
        """初始化标准浮出视图
        
        Args:
            title: 标题文本，显示在浮出层顶部
            content: 内容文本，显示在标题下方，支持富文本格式
            icon: 图标实例，显示在左侧，传 None 时不显示图标
            image: 图片实例，显示在内容下方，传 None 时不显示图片
            isClosable: 是否显示关闭按钮，为 True 时允许用户手动关闭浮出层
            parent: 父控件，用于指定该视图的父级容器
        """
        super().__init__(parent=parent)
        """浮出视图构造函数

        Args:
            title (str): 浮出卡片标题
            content (str): 浮出卡片内容
            icon (Union[FluentIconBase, QIcon, str], optional): 浮出卡片图标
            image (Union[str, QPixmap, QImage], optional): 浮出卡片图片
            isClosable (bool, optional): 是否显示关闭按钮
            parent (QWidget, optional): 父部件
        """
        self.icon = icon
        self.title = title
        self.image = image
        self.content = content
        self.isClosable = isClosable

        self.vBoxLayout = QVBoxLayout(self)
        self.viewLayout = QHBoxLayout()
        self.widgetLayout = QVBoxLayout()

        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content, self)
        self.iconWidget = IconWidget(icon, self)
        self.imageLabel = ImageLabel(self)
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE, self)

        self.__initWidgets()

    def __initWidgets(self):
        self.imageLabel.setImage(self.image)

        self.closeButton.setFixedSize(32, 32)
        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setVisible(self.isClosable)
        self.titleLabel.setVisible(bool(self.title))
        self.contentLabel.setVisible(bool(self.content))
        self.iconWidget.setHidden(self.icon is None)

        self.closeButton.clicked.connect(self.closed)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.TEACHING_TIP.apply(self)

        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(1, 1, 1, 1)
        self.widgetLayout.setContentsMargins(0, 8, 0, 8)
        self.viewLayout.setSpacing(4)
        self.widgetLayout.setSpacing(0)
        self.vBoxLayout.setSpacing(0)

        # 添加 图标 部件
        if not self.title or not self.content:
            self.iconWidget.setFixedHeight(36)

        self.vBoxLayout.addLayout(self.viewLayout)
        self.viewLayout.addWidget(self.iconWidget, 0, Qt.AlignTop)

        # 添加 文本
        self._adjustText()
        self.widgetLayout.addWidget(self.titleLabel)
        self.widgetLayout.addWidget(self.contentLabel)
        self.viewLayout.addLayout(self.widgetLayout)

        # 添加 关闭 按钮
        self.closeButton.setVisible(self.isClosable)
        self.viewLayout.addWidget(
            self.closeButton, 0, Qt.AlignRight | Qt.AlignTop)

        # 调整内容 margins
        margins = QMargins(6, 5, 6, 5)
        margins.setLeft(20 if not self.icon else 5)
        margins.setRight(20 if not self.isClosable else 6)
        self.viewLayout.setContentsMargins(margins)

        # 添加 图像
        self._adjustImage()
        self._addImageToLayout()

    def addWidget(self, widget: QWidget, stretch=0, align=Qt.AlignLeft):
        """将部件添加到视图

        Args:
            widget (QWidget): 要添加的部件
            stretch (int, optional): 拉伸因子，默认为 0
            align (Qt.AlignmentFlag, optional): 对齐方式，默认为 Qt.AlignLeft
        """
        self.widgetLayout.addSpacing(8)
        self.widgetLayout.addWidget(widget, stretch, align)

    def _addImageToLayout(self):
        self.imageLabel.setBorderRadius(8, 8, 0, 0)
        self.imageLabel.setHidden(self.imageLabel.isNull())
        self.vBoxLayout.insertWidget(0, self.imageLabel)

    def _adjustText(self):
        w = min(900, QApplication.screenAt(
            QCursor.pos()).geometry().width() - 200)

        # 调整标题
        chars = max(min(w / 10, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])

        # 调整内容
        chars = max(min(w / 9, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])

    def _adjustImage(self):
        w = self.vBoxLayout.sizeHint().width() - 2
        self.imageLabel.scaledToWidth(w)

    def showEvent(self, e):
        super().showEvent(e)
        self._adjustImage()
        self.adjustSize()


class Flyout(QWidget):
    """浮出层容器控件
    负责承载 FlyoutView 并附加到目标控件旁，自动计算显示位置并播放动画
    构造函数重载:
        make: 基于目标控件创建浮出层并自动定位
        show: 基于全局坐标创建浮出层并显示
    """

    closed = Signal()

    def __init__(self, view: FlyoutViewBase, parent=None, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """初始化浮出层容器
        
        Args:
            view: 浮出视图实例，必须是 FlyoutViewBase 的子类实例
            parent: 父窗口或控件，用于确定浮出层的显示层级
            isDeleteOnClose: 关闭时是否自动删除实例，为 True 可避免内存泄漏，适用于一次性浮出层
            isMacInputMethodEnabled: 是否启用 Mac 输入法支持，仅在 macOS 平台下生效
        """
        super().__init__(parent=parent)
        self.view = view
        self.hBoxLayout = QHBoxLayout(self)
        self.aniManager = None  # type: FlyoutAnimationManager
        self.isDeleteOnClose = isDeleteOnClose
        self.isMacInputMethodEnabled = isMacInputMethodEnabled

        self.hBoxLayout.setContentsMargins(15, 8, 15, 20)
        self.hBoxLayout.addWidget(self.view)
        self.setShadowEffect()

        self.setAttribute(Qt.WA_TranslucentBackground)

        if sys.platform != "darwin" or not isMacInputMethodEnabled:
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                                Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched, event):
        if sys.platform == "darwin" and self.isMacInputMethodEnabled:
            if self.isVisible() and event.type() == QEvent.MouseButtonPress:
                if not self.rect().contains(self.mapFromGlobal(event.globalPos())):
                    self.close()

        return super().eventFilter(watched, event)

    def setShadowEffect(self, blurRadius=35, offset=(0, 8)):
        """设置阴影效果

        Args:
            blurRadius (int, optional): 模糊半径，默认为 35
            offset (tuple, optional): 阴影偏移量，默认为 (0, 8)
        """
        color = QColor(0, 0, 0, 80 if isDarkTheme() else 30)
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def closeEvent(self, e):
        if self.isDeleteOnClose:
            self.deleteLater()

        super().closeEvent(e)
        self.closed.emit()

    def showEvent(self, e):
        # 修复 #780
        self.activateWindow()
        super().showEvent(e)

    def exec(self, pos: QPoint, aniType=FlyoutAnimationType.PULL_UP):
        """显示浮出层

        Args:
            pos (QPoint): 显示位置
            aniType (FlyoutAnimationType, optional): 动画类型，默认为 FlyoutAnimationType.PULL_UP
        """
        self.aniManager = FlyoutAnimationManager.make(aniType, self)
        self.show()
        self.aniManager.exec(pos)

    @classmethod
    def make(cls, view: FlyoutViewBase, target: Union[QWidget, QPoint] = None, parent=None,
             aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """创建并显示浮出层

        Args:
            view (FlyoutViewBase): 浮出层视图
            target (Union[QWidget, QPoint], optional): 目标部件或显示位置
            parent (QWidget, optional): 父窗口
            aniType (FlyoutAnimationType, optional): 动画类型，默认为 FlyoutAnimationType.PULL_UP
            isDeleteOnClose (bool, optional): 关闭时是否自动删除，默认为 True
            isMacInputMethodEnabled (bool, optional): 是否启用 Mac 输入法兼容模式，默认为 False

        Returns:
            Flyout: 浮出层实例
        """
        w = cls(view, parent, isDeleteOnClose, isMacInputMethodEnabled)

        if target is None:
            return w

        # 显示浮出层 first so that we can 获取 correct 大小
        w.show()

        # move 浮出层 到 top 的 目标
        if isinstance(target, QWidget):
            target = FlyoutAnimationManager.make(aniType, w).position(target)

        w.exec(target, aniType)
        return w

    @classmethod
    def create(cls, title: str, content: str, icon: Union[FluentIconBase, QIcon, str] = None,
               image: Union[str, QPixmap, QImage] = None, isClosable=False, target: Union[QWidget, QPoint] = None,
               parent=None, aniType=FlyoutAnimationType.PULL_UP, isDeleteOnClose=True, isMacInputMethodEnabled=False):
        """使用默认视图创建并显示浮出层

        Args:
            title (str): 浮出层标题
            content (str): 浮出层内容
            icon (Union[FluentIconBase, QIcon, str], optional): 浮出层图标
            image (Union[str, QPixmap, QImage], optional): 浮出层图片
            isClosable (bool, optional): 是否显示关闭按钮
            target (Union[QWidget, QPoint], optional): 目标部件或显示位置
            parent (QWidget, optional): 父窗口
            aniType (FlyoutAnimationType, optional): 动画类型，默认为 FlyoutAnimationType.PULL_UP
            isDeleteOnClose (bool, optional): 关闭时是否自动删除，默认为 True
            isMacInputMethodEnabled (bool, optional): 是否启用 Mac 输入法兼容模式，默认为 False

        Returns:
            Flyout: 浮出层实例
        """
        view = FlyoutView(title, content, icon, image, isClosable)
        w = cls.make(view, target, parent, aniType, isDeleteOnClose, isMacInputMethodEnabled)
        view.closed.connect(w.close)
        return w

    def fadeOut(self):
        self.fadeOutAni = QPropertyAnimation(self, b'windowOpacity', self)
        self.fadeOutAni.finished.connect(self.close)
        self.fadeOutAni.setStartValue(1)
        self.fadeOutAni.setEndValue(0)
        self.fadeOutAni.setDuration(120)
        self.fadeOutAni.start()


class FlyoutAnimationManager(QObject):
    """浮出层动画管理器基类
    负责根据目标控件位置自动选择并执行合适的动画类型，管理浮出层的显示和隐藏动画流程
    """

    managers = {}

    def __init__(self, flyout: Flyout):
        """初始化动画管理器
        
        Args:
            flyout: 浮出层实例，必须是 Flyout 类型，动画将应用在该实例上
        """
        super().__init__()
        self.flyout = flyout
        self.aniGroup = QParallelAnimationGroup(self)
        self.slideAni = QPropertyAnimation(flyout, b'pos', self)
        self.opacityAni = QPropertyAnimation(flyout, b'windowOpacity', self)

        self.slideAni.setDuration(187)
        self.opacityAni.setDuration(187)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)

        self.slideAni.setEasingCurve(QEasingCurve.OutQuad)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)
        self.aniGroup.addAnimation(self.slideAni)
        self.aniGroup.addAnimation(self.opacityAni)

    @classmethod
    def register(cls, name):
        """注册浮出层动画管理器

        Args:
            name: 管理器名称，必须唯一

        Returns:
            function: 装饰器函数
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    def exec(self, pos: QPoint):
        """开始动画

        Args:
            pos (QPoint): 动画起始位置
        """
        raise NotImplementedError

    def _adjustPosition(self, pos):
        rect = getCurrentScreenGeometry()
        w, h = self.flyout.sizeHint().width() + 5, self.flyout.sizeHint().height()
        x = max(rect.left(), min(pos.x(), rect.right() - w))
        y = max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5))
        return QPoint(x, y)

    def position(self, target: QWidget):
        """获取相对于目标的左上角位置

        Args:
            target (QWidget): 目标部件

        Returns:
            QPoint: 左上角位置
        """
        raise NotImplementedError

    @classmethod
    def make(cls, aniType: FlyoutAnimationType, flyout: Flyout) -> "FlyoutAnimationManager":
        """创建动画管理器

        Args:
            aniType (FlyoutAnimationType): 动画类型
            flyout (Flyout): 浮出层实例

        Returns:
            FlyoutAnimationManager: 动画管理器实例

        Raises:
            ValueError: 动画类型无效时抛出
        """
        if aniType not in cls.managers:
            raise ValueError(f'`{aniType}` is an invalid animation type.')

        return cls.managers[aniType](flyout)


@FlyoutAnimationManager.register(FlyoutAnimationType.PULL_UP)
class PullUpFlyoutAnimationManager(FlyoutAnimationManager):
    """向上弹出动画管理器
    当目标控件位于触发点下方时，浮出层从下方向上滑入显示，适用于底部触发场景
    """

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint())
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        y = pos.y() - w.sizeHint().height() + w.layout().contentsMargins().bottom()
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        pos = self._adjustPosition(pos)
        self.slideAni.setStartValue(pos+QPoint(0, 8))
        self.slideAni.setEndValue(pos)
        self.aniGroup.start()


@FlyoutAnimationManager.register(FlyoutAnimationType.DROP_DOWN)
class DropDownFlyoutAnimationManager(FlyoutAnimationManager):
    """向下弹出动画管理器
    当目标控件位于触发点上方时，浮出层从上方向下滑入显示，适用于顶部触发场景
    """

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        y = pos.y() - w.layout().contentsMargins().top() + 8
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        pos = self._adjustPosition(pos)
        self.slideAni.setStartValue(pos-QPoint(0, 8))
        self.slideAni.setEndValue(pos)
        self.aniGroup.start()


@FlyoutAnimationManager.register(FlyoutAnimationType.SLIDE_LEFT)
class SlideLeftFlyoutAnimationManager(FlyoutAnimationManager):
    """向左滑入动画管理器
    当目标控件位于触发点右侧时，浮出层从右侧向左滑入显示，适用于右侧触发场景
    """

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint(0, 0))
        x = pos.x() - w.sizeHint().width() + 8
        y = pos.y() - w.sizeHint().height()//2 + target.height()//2 + \
            w.layout().contentsMargins().top()
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        pos = self._adjustPosition(pos)
        self.slideAni.setStartValue(pos+QPoint(8, 0))
        self.slideAni.setEndValue(pos)
        self.aniGroup.start()


@FlyoutAnimationManager.register(FlyoutAnimationType.SLIDE_RIGHT)
class SlideRightFlyoutAnimationManager(FlyoutAnimationManager):
    """向右滑入动画管理器
    当目标控件位于触发点左侧时，浮出层从左侧向右滑入显示，适用于左侧触发场景
    """

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint(0, 0))
        x = pos.x() + target.width() - 8
        y = pos.y() - w.sizeHint().height()//2 + target.height()//2 + \
            w.layout().contentsMargins().top()
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        pos = self._adjustPosition(pos)
        self.slideAni.setStartValue(pos-QPoint(8, 0))
        self.slideAni.setEndValue(pos)
        self.aniGroup.start()


@FlyoutAnimationManager.register(FlyoutAnimationType.FADE_IN)
class FadeInFlyoutAnimationManager(FlyoutAnimationManager):
    """淡入动画管理器
    浮出层以透明度渐变的方式显示和隐藏，不依赖具体方位，适用于所有触发位置
    """

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint())
        x = pos.x() + target.width()//2 - w.sizeHint().width()//2
        y = pos.y() - w.sizeHint().height() + w.layout().contentsMargins().bottom()
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        self.flyout.move(self._adjustPosition(pos))
        self.aniGroup.removeAnimation(self.slideAni)
        self.aniGroup.start()



@FlyoutAnimationManager.register(FlyoutAnimationType.NONE)
class DummyFlyoutAnimationManager(FlyoutAnimationManager):
    """无动画管理器
    直接显示和隐藏浮出层而不播放任何过渡动画，适用于性能敏感或需要即时响应的场景
    """

    def exec(self, pos: QPoint):
        """执行显示

        Args:
            pos (QPoint): 显示位置
        """
        self.flyout.move(self._adjustPosition(pos))

    def position(self, target: QWidget):
        """获取相对于目标的左上角位置

        Args:
            target (QWidget): 目标部件

        Returns:
            QPoint: 左上角位置
        """
        m = self.flyout.hBoxLayout.contentsMargins()
        return target.mapToGlobal(QPoint(-m.left(), -self.flyout.sizeHint().height()+m.bottom()-8))