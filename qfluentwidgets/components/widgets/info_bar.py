# coding: utf-8
from enum import Enum
import sys
from typing import Union
import weakref

from PySide6.QtCore import (Qt, QEvent, QSize, QRectF, QObject, QPropertyAnimation,
                          QEasingCurve, QTimer, Signal, QParallelAnimationGroup, QPoint)
from PySide6.QtGui import QPainter, QIcon, QColor
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect, QApplication)

from ...common.auto_wrap import TextWrap
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.icon import FluentIconBase, Theme, isDarkTheme, writeSvg, drawSvgIcon, drawIcon
from ...common.icon import FluentIcon as FIF
from .button import TransparentToolButton



class InfoBarIcon(FluentIconBase, Enum):
    """ 信息栏 图标 """

    INFORMATION = "Info"
    SUCCESS = "Success"
    WARNING = "Warning"
    ERROR = "Error"

    def path(self, theme=Theme.AUTO):
        if theme == Theme.AUTO:
            color = "dark" if isDarkTheme() else "light"
        else:
            color = theme.value.lower()

        return f':/qfluentwidgets/images/info_bar/{self.value}_{color}.svg'


class InfoBarPosition(Enum):
    """ 信息栏位置 """
    TOP = 0
    BOTTOM = 1
    TOP_LEFT = 2
    TOP_RIGHT = 3
    BOTTOM_LEFT = 4
    BOTTOM_RIGHT = 5
    NONE = 6


class InfoIconWidget(QWidget):
    """ 图标 部件 """

    def __init__(self, icon: InfoBarIcon, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(36, 36)
        self.icon = icon

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        rect = QRectF(10, 10, 15, 15)
        if self.icon != InfoBarIcon.INFORMATION:
            drawIcon(self.icon, painter, rect)
        else:
            drawIcon(self.icon, painter, rect, indexes=[0], fill=themeColor().name())


class InfoBar(QFrame):
    """ Information 栏 """

    closedSignal = Signal()
    _desktopView = None     # type: DesktopInfoBarView

    def __init__(self, icon: Union[InfoBarIcon, FluentIconBase, QIcon, str], title: str, content: str,
                 orient=Qt.Horizontal, isClosable=True, duration=1000, position=InfoBarPosition.TOP_RIGHT,
                 parent=None):
        """
        参数
        ----------
        icon: InfoBarIcon | FluentIconBase | QIcon | str
            图标 的 信息栏

        title: str
            标题 的 信息栏

        content: str
            内容 的 信息栏

        orient: Qt.Orientation
            布局 方向 的 信息栏, use `Qt.Horizontal` 用于 short 内容

        isClosable: bool
            是否 到 显示 关闭 按钮

        duraction: int
            时间 用于 信息栏 到 display 中的 milliseconds. 如果 持续时间 is less than zero,
            信息栏 will never disappear.

        parent: QWidget
            父部件 部件
        """
        super().__init__(parent=parent)
        self.title = title
        self.content = content
        self.orient = orient
        self.icon = icon
        self.duration = duration
        self.isClosable = isClosable
        self.position = position

        self.titleLabel = QLabel(self)
        self.contentLabel = QLabel(self)
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.iconWidget = InfoIconWidget(icon)

        self.hBoxLayout = QHBoxLayout(self)
        self.textLayout = QHBoxLayout() if self.orient == Qt.Horizontal else QVBoxLayout()
        self.widgetLayout = QHBoxLayout() if self.orient == Qt.Horizontal else QVBoxLayout()

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.opacityAni = QPropertyAnimation(
            self.opacityEffect, b'opacity', self)

        self.lightBackgroundColor = None
        self.darkBackgroundColor = None

        self.__initWidget()

    def __initWidget(self):
        self.opacityEffect.setOpacity(1)
        self.setGraphicsEffect(self.opacityEffect)

        self.closeButton.setFixedSize(36, 36)
        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.setVisible(self.isClosable)

        self.__setQss()
        self.__initLayout()

        self.closeButton.clicked.connect(self.close)

    def __initLayout(self):
        self.hBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.hBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.textLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.textLayout.setAlignment(Qt.AlignTop)
        self.textLayout.setContentsMargins(1, 8, 0, 8)

        self.hBoxLayout.setSpacing(0)
        self.textLayout.setSpacing(5)

        # 将图标添加到布局
        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignTop | Qt.AlignLeft)

        # 将标题添加到布局
        self.textLayout.addWidget(self.titleLabel, 1, Qt.AlignTop)
        self.titleLabel.setVisible(bool(self.title))

        # 将内容 标签添加到布局
        if self.orient == Qt.Horizontal:
            self.textLayout.addSpacing(7)

        self.textLayout.addWidget(self.contentLabel, 1, Qt.AlignTop)
        self.contentLabel.setVisible(bool(self.content))
        self.hBoxLayout.addLayout(self.textLayout)

        # 添加 部件 布局
        if self.orient == Qt.Horizontal:
            self.hBoxLayout.addLayout(self.widgetLayout)
            self.widgetLayout.setSpacing(10)
        else:
            self.textLayout.addLayout(self.widgetLayout)

        # 将关闭 按钮添加到布局
        self.hBoxLayout.addSpacing(12)
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignLeft)

        self._adjustText()

    def __setQss(self):
        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')
        if isinstance(self.icon, Enum):
            self.setProperty('type', self.icon.value)

        FluentStyleSheet.INFO_BAR.apply(self)

    def __fadeOut(self):
        """ 淡出 """
        # After compiling 到 executable file by nuitka, RuntimeError will be thrown 如果 we 关闭 InfoBar manually
        try:
            self.opacityAni.setDuration(200)
            self.opacityAni.setStartValue(1)
            self.opacityAni.setEndValue(0)
            self.opacityAni.finished.connect(self.close)
            self.opacityAni.start()
        except RuntimeError:
            pass

    def _adjustText(self):
        w = 900 if not self.parent() else (self.parent().width() - 50)

        # 调整标题
        chars = max(min(w / 10, 120), 30)
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])

        # 调整内容
        chars = max(min(w / 9, 120), 30)
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.adjustSize()

    def addWidget(self, widget: QWidget, stretch=0):
        """ 将部件添加到info 栏 """
        self.widgetLayout.addSpacing(6)
        align = Qt.AlignTop if self.orient == Qt.Vertical else Qt.AlignVCenter
        self.widgetLayout.addWidget(widget, stretch, Qt.AlignLeft | align)

    def setCustomBackgroundColor(self, light, dark):
        """ 设置 自定义 背景色

        参数
        ----------
        亮色, dark: str | Qt.GlobalColor | QColor
            背景色 中的 亮色/暗色主题模式
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                self._adjustText()

        return super().eventFilter(obj, e)

    def closeEvent(self, e):
        self.closedSignal.emit()
        self.deleteLater()
        e.ignore()

    def showEvent(self, e):
        self._adjustText()
        super().showEvent(e)

        if self.duration >= 0:
            QTimer.singleShot(self.duration, self.__fadeOut)

        if self.position != InfoBarPosition.NONE:
            manager = InfoBarManager.make(self.position)
            manager.add(self)

        if self.parent():
            self.parent().installEventFilter(self)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.lightBackgroundColor is None:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if isDarkTheme():
            painter.setBrush(self.darkBackgroundColor)
        else:
            painter.setBrush(self.lightBackgroundColor)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 6, 6)

    @classmethod
    def new(cls, icon, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
            position=InfoBarPosition.TOP_RIGHT, parent=None):
        w = InfoBar(icon, title, content, orient,
                    isClosable, duration, position, parent)
        w.show()
        return w

    @classmethod
    def info(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
             position=InfoBarPosition.TOP_RIGHT, parent=None):
        return cls.new(InfoBarIcon.INFORMATION, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def success(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        return cls.new(InfoBarIcon.SUCCESS, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def warning(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
                position=InfoBarPosition.TOP_RIGHT, parent=None):
        return cls.new(InfoBarIcon.WARNING, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def error(cls, title, content, orient=Qt.Horizontal, isClosable=True, duration=1000,
              position=InfoBarPosition.TOP_RIGHT, parent=None):
        return cls.new(InfoBarIcon.ERROR, title, content, orient, isClosable, duration, position, parent)

    @classmethod
    def desktopView(cls):
        """ 返回 desktop container """
        if not cls._desktopView:
            cls._desktopView = DesktopInfoBarView()
            cls._desktopView.show()

        return cls._desktopView


class InfoBarManager(QObject):
    """ 信息栏 管理器 """

    _instance = None
    managers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InfoBarManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance.__initialized = False

        return cls._instance

    def __init__(self):
        if self.__initialized:
            return

        super().__init__()
        self.spacing = 16
        self.margin = 24
        self.infoBars = weakref.WeakKeyDictionary()
        self.aniGroups = weakref.WeakKeyDictionary()
        self.slideAnis = []
        self.dropAnis = []
        self.__initialized = True

    def add(self, infoBar: InfoBar):
        """ 添加 信息栏 """
        p = infoBar.parent()    # type:QWidget
        if not p:
            return

        if p not in self.infoBars:
            p.installEventFilter(self)
            self.infoBars[p] = []
            self.aniGroups[p] = QParallelAnimationGroup(self)

        if infoBar in self.infoBars[p]:
            return

        # 添加 drop 动画
        if self.infoBars[p]:
            dropAni = QPropertyAnimation(infoBar, b'pos')
            dropAni.setDuration(200)

            self.aniGroups[p].addAnimation(dropAni)
            self.dropAnis.append(dropAni)

            infoBar.setProperty('dropAni', dropAni)

        # 添加 slide 动画
        self.infoBars[p].append(infoBar)
        slideAni = self._createSlideAni(infoBar)
        self.slideAnis.append(slideAni)

        infoBar.setProperty('slideAni', slideAni)
        infoBar.closedSignal.connect(lambda: self.remove(infoBar))

        slideAni.start()

    def remove(self, infoBar: InfoBar):
        """ 移除 信息栏 """
        p = infoBar.parent()
        if p not in self.infoBars:
            return

        if infoBar not in self.infoBars[p]:
            return

        self.infoBars[p].remove(infoBar)

        # 移除 drop 动画
        dropAni = infoBar.property('dropAni')   # type: QPropertyAnimation
        if dropAni:
            self.aniGroups[p].removeAnimation(dropAni)
            self.dropAnis.remove(dropAni)

        # 移除 slider 动画
        slideAni = infoBar.property('slideAni')
        if slideAni:
            self.slideAnis.remove(slideAni)

        # 调整the 位置 的 remaining info bars
        self._updateDropAni(p)
        self.aniGroups[p].start()

    def _createSlideAni(self, infoBar: InfoBar):
        slideAni = QPropertyAnimation(infoBar, b'pos')
        slideAni.setEasingCurve(QEasingCurve.OutQuad)
        slideAni.setDuration(200)

        slideAni.setStartValue(self._slideStartPos(infoBar))
        slideAni.setEndValue(self._pos(infoBar))

        return slideAni

    def _updateDropAni(self, parent):
        for bar in self.infoBars[parent]:
            ani = bar.property('dropAni')
            if not ani:
                continue

            ani.setStartValue(bar.pos())
            ani.setEndValue(self._pos(bar))

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        """ 返回info 栏的位置 """
        raise NotImplementedError

    def _slideStartPos(self, infoBar: InfoBar) -> QPoint:
        """ 返回slide 动画的开始 位置  """
        raise NotImplementedError

    def eventFilter(self, obj, e: QEvent):
        # After compiling 到 executable file, RuntimeError will be thrown 当 closing app
        try:
            if obj not in self.infoBars:
                return False

            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                size = e.size() if e.type() == QEvent.Resize else None
                for bar in self.infoBars[obj]:
                    bar.move(self._pos(bar, size))

            return super().eventFilter(obj, e)
        except:
            return False

    @classmethod
    def register(cls, name):
        """ 注册 菜单 动画 管理器

        参数
        ----------
        name: Any
            name 的 管理器, it should be unique
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def make(cls, position: InfoBarPosition):
        """ 遮罩 信息栏 管理器 根据 display 位置 """
        if position not in cls.managers:
            raise ValueError(f'`{position}` is an invalid animation type.')

        return cls.managers[position]()


@InfoBarManager.register(InfoBarPosition.TOP)
class TopInfoBarManager(InfoBarManager):
    """ Top 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        x = (infoBar.parent().width() - infoBar.width()) // 2
        y = self.margin
        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


@InfoBarManager.register(InfoBarPosition.TOP_RIGHT)
class TopRightInfoBarManager(InfoBarManager):
    """ Top right 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        x = parentSize.width() - infoBar.width() - self.margin
        y = self.margin
        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        return QPoint(infoBar.parent().width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM_RIGHT)
class BottomRightInfoBarManager(InfoBarManager):
    """ Bottom right 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        x = parentSize.width() - infoBar.width() - self.margin
        y = parentSize.height() - infoBar.height() - self.margin

        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        return QPoint(infoBar.parent().width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.TOP_LEFT)
class TopLeftInfoBarManager(InfoBarManager):
    """ Top left 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize=None) -> QPoint:
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        y = self.margin
        index = self.infoBars[p].index(infoBar)

        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(self.margin, y)

    def _slideStartPos(self, infoBar: InfoBar):
        return QPoint(-infoBar.width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM_LEFT)
class BottomLeftInfoBarManager(InfoBarManager):
    """ Bottom left 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize: QSize = None) -> QPoint:
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        y = parentSize.height() - infoBar.height() - self.margin
        index = self.infoBars[p].index(infoBar)

        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(self.margin, y)

    def _slideStartPos(self, infoBar: InfoBar):
        return QPoint(-infoBar.width(), self._pos(infoBar).y())


@InfoBarManager.register(InfoBarPosition.BOTTOM)
class BottomInfoBarManager(InfoBarManager):
    """ Bottom 位置 信息栏 管理器 """

    def _pos(self, infoBar: InfoBar, parentSize: QSize = None) -> QPoint:
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        x = (parentSize.width() - infoBar.width()) // 2
        y = parentSize.height() - infoBar.height() - self.margin
        index = self.infoBars[p].index(infoBar)

        for bar in self.infoBars[p][0:index]:
            y -= (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() + 16)


class DesktopInfoBarView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        if sys.platform == "win32":
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().availableGeometry())
