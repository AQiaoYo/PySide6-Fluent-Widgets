# coding: utf-8
from typing import TYPE_CHECKING, Union
import sys

from PySide6.QtCore import Qt, QSize, QRect, QRectF
from PySide6.QtGui import QIcon, QPainter, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication

from ..common.config import qconfig
from ..common.icon import FluentIconBase, toQIcon, drawIcon
from ..common.router import qrouter
from ..common.style_sheet import FluentStyleSheet, isDarkTheme, setTheme, Theme
from ..common.animation import BackgroundAnimationWidget
from ..components.widgets.frameless_window import FramelessWindow
from ..components.navigation.navigation_types import NavigationItemPosition
from .stacked_widget import StackedWidget

from qframelesswindow import TitleBar, TitleBarBase, TitleBarButton

if TYPE_CHECKING:
    from ..components.navigation import NavigationBar, NavigationBarPushButton, NavigationInterface, NavigationTreeWidget


class FluentWidget(BackgroundAnimationWidget, FramelessWindow):
    """ Fluent 部件 """

    def __init__(self, parent=None):
        self._isMicaEnabled = False
        self._lightBackgroundColor = QColor(240, 244, 249)
        self._darkBackgroundColor = QColor(32, 32, 32)
        super().__init__(parent=parent)

        # 在 Win11 上默认启用 Mica 效果.
        self.setMicaEffectEnabled(True)

        # 在 macOS 上显示系统标题栏按钮.
        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)

        # 初始化标题栏.
        self.setTitleBar(FluentWidgetTitleBar(self))

        qconfig.themeChangedFinished.connect(self._onThemeChangedFinished)

    def setCustomBackgroundColor(self, light, dark):
        """设置自定义背景色
        
        Args:
            light (QColor | Qt.GlobalColor | str): 亮色主题下使用的背景色
            dark (QColor | Qt.GlobalColor | str): 暗色主题下使用的背景色
        """
        self._lightBackgroundColor = QColor(light)
        self._darkBackgroundColor = QColor(dark)
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        if not self.isMicaEffectEnabled():
            return self._darkBackgroundColor if isDarkTheme() else self._lightBackgroundColor

        return QColor(0, 0, 0, 0)

    def _onThemeChangedFinished(self):
        if self.isMicaEffectEnabled():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.backgroundColor)
        painter.drawRect(self.rect())

    def showEvent(self, e):
        super().showEvent(e)
        # 窗口初始化完成后重新应用 Mica 效果.
        if self.isMicaEffectEnabled():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())

    def setMicaEffectEnabled(self, isEnabled: bool):
        """设置是否启用 Mica 效果，仅在 Win11 上可用
        
        Args:
            isEnabled (bool): 是否启用 Mica 效果
        """
        if sys.platform != 'win32' or sys.getwindowsversion().build < 22000:
            return

        self._isMicaEnabled = isEnabled

        if isEnabled:
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())
        else:
            self.windowEffect.removeBackgroundEffect(self.winId())

        self.setBackgroundColor(self._normalBackgroundColor())

    def isMicaEffectEnabled(self):
        return self._isMicaEnabled

    def systemTitleBarRect(self, size: QSize) -> QRect:
        """返回系统标题栏区域，仅适用于 macOS
        
        Args:
            size (QSize): 原始系统标题栏区域
        
        Returns:
            系统标题栏区域
        """
        return QRect(0, 0 if self.isFullScreen() else 2, 75, size.height())

    def setTitleBar(self, titleBar):
        super().setTitleBar(titleBar)

        # 在 macOS 上隐藏自绘标题栏按钮,避免与系统按钮重复.
        if sys.platform == "darwin" and self.isSystemButtonVisible() and isinstance(titleBar, TitleBarBase):
            titleBar.minBtn.hide()
            titleBar.maxBtn.hide()
            titleBar.closeBtn.hide()


class FluentWindowBase(FluentWidget):
    """ Fluent 窗口基类 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.stackedWidget = StackedWidget(self)
        self.navigationInterface = None

        # 初始化布局
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        FluentStyleSheet.FLUENT_WINDOW.apply(self.stackedWidget)

    def addSubInterface(self, interface: QWidget, icon: Union[FluentIconBase, QIcon, str], text: str,
                        position=None):
        """添加子界面
        
        Args:
            interface (QWidget): 要添加的子界面
            icon (Union[FluentIconBase, QIcon, str]): 导航项图标
            text (str): 导航项文本
            position: 导航项位置
        """
        raise NotImplementedError

    def removeInterface(self, interface: QWidget, isDelete=False):
        """移除子界面
        
        Args:
            interface (QWidget): 要移除的子界面
            isDelete (bool): 是否一并删除该子界面
        """
        raise NotImplementedError

    def switchTo(self, interface: QWidget):
        self.stackedWidget.setCurrentWidget(interface, popOut=False)

    def _onCurrentInterfaceChanged(self, index: int):
        widget = self.stackedWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

        self._updateStackedBackground()

    def _updateStackedBackground(self):
        isTransparent = self.stackedWidget.currentWidget().property("isStackedTransparent")
        if bool(self.stackedWidget.property("isTransparent")) == isTransparent:
            return

        self.stackedWidget.setProperty("isTransparent", isTransparent)
        self.stackedWidget.setStyle(QApplication.style())

    def systemTitleBarRect(self, size: QSize) -> QRect:
        """返回系统标题栏区域，仅适用于 macOS
        
        Args:
            size (QSize): 原始系统标题栏区域
        
        Returns:
            系统标题栏区域
        """
        return QRect(size.width() - 75, 0 if self.isFullScreen() else 8, 75, size.height())


class FluentTitleBarButton(TitleBarButton):
    """ Fluent 标题栏按钮 """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], parent=None):
        super().__init__(parent)
        self.setIcon(icon)

    def setIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        self._icon = icon
        self.update()

    def icon(self) -> QIcon:
        return toQIcon(self._icon)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        _, bgColor = self._getColors()

        # 绘制背景
        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        # 绘制图标
        iw, ih = self.iconSize().width(), self.iconSize().height()
        x = (self.width() - iw) / 2
        y = (self.height() - ih) / 2
        drawIcon(self._icon, painter, QRectF(x, y, iw, ih))



class FluentTitleBar(TitleBar):
    """ Fluent 标题栏"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # 添加窗口图标.
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertWidget(0, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.window().windowIconChanged.connect(self.setIcon)

        # 添加标题标签.
        from ..components.widgets.label import CaptionLabel

        self.titleLabel = CaptionLabel(self)
        self.hBoxLayout.insertWidget(1, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setAlignment(Qt.AlignTop)
        self.buttonLayout.addWidget(self.minBtn)
        self.buttonLayout.addWidget(self.maxBtn)
        self.buttonLayout.addWidget(self.closeBtn)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addStretch(1)
        self.hBoxLayout.addLayout(self.vBoxLayout, 0)

        FluentStyleSheet.FLUENT_WINDOW.apply(self)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class FluentWindow(FluentWindowBase):
    """ Fluent 窗口 """

    def __init__(self, parent=None):
        super().__init__(parent)
        from ..components.navigation import NavigationInterface

        self.setTitleBar(FluentTitleBar(self))

        self.navigationInterface = NavigationInterface(self, showReturnButton=True)
        self.widgetLayout = QHBoxLayout()

        # 初始化布局
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.setStretchFactor(self.widgetLayout, 1)

        self.widgetLayout.addWidget(self.stackedWidget)
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)

        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)
        self.titleBar.raise_()

    def addSubInterface(self, interface: QWidget, icon: Union[FluentIconBase, QIcon, str], text: str,
                        position=None, parent=None, isTransparent=False) -> 'NavigationTreeWidget':
        """添加子界面
        
        调用此方法前，必须先为 interface 设置 objectName
        
        Args:
            interface (QWidget): 要添加的子界面，调用前必须已设置 objectName
            icon (Union[FluentIconBase, QIcon, str]): 导航项图标
            text (str): 导航项文本
            position (NavigationItemPosition): 导航项位置
            parent (QWidget | str): 父级导航项，QWidget 表示使用父部件的 objectName 作为父级导航项，str 表示直接使用父级路由键
            isTransparent (bool): 是否使用透明背景
        """
        if not interface.objectName():
            raise ValueError("The object name of `interface` can't be empty string.")

        position = position or NavigationItemPosition.TOP

        parentRouteKey = parent
        if parent and isinstance(parent, QWidget):
            parentRouteKey = parent.objectName()
            if not parentRouteKey:
                raise ValueError("The object name of `parent` can't be empty string.")

        interface.setProperty("isStackedTransparent", isTransparent)
        self.stackedWidget.addWidget(interface)

        # 将界面注册到导航树.
        routeKey = interface.objectName()
        item = self.navigationInterface.addItem(
            routeKey=routeKey,
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text,
            parentRouteKey=parentRouteKey
        )

        # 第一个子界面默认作为当前页.
        if self.stackedWidget.count() == 1:
            self.stackedWidget.currentChanged.connect(self._onCurrentInterfaceChanged)
            self.navigationInterface.setCurrentItem(routeKey)
            qrouter.setDefaultRouteKey(self.stackedWidget, routeKey)

        self._updateStackedBackground()

        return item

    def removeInterface(self, interface, isDelete=False):
        self.navigationInterface.removeWidget(interface.objectName())
        self.stackedWidget.removeWidget(interface)
        interface.hide()

        if isDelete:
            interface.deleteLater()

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width()-46, self.titleBar.height())


class MSFluentTitleBar(FluentTitleBar):

    def __init__(self, parent):
        super().__init__(parent)
        self.hBoxLayout.insertSpacing(0, 20)
        self.hBoxLayout.insertSpacing(2, 2)


class FluentWidgetTitleBar(FluentTitleBar):

    def __init__(self, parent):
        super().__init__(parent)

        if sys.platform == "darwin":
            self.iconLabel.hide()
            self.titleLabel.hide()
            self.setFixedHeight(28)
        else:
            self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
            self.setFixedHeight(self.buttonLayout.sizeHint().height())

        for button in self.findChildren(TitleBarButton):
            FluentStyleSheet.FLUENT_WINDOW.apply(button)



class MSFluentWindow(FluentWindowBase):
    """ Microsoft Store 风格的 Fluent 窗口 """

    def __init__(self, parent=None):
        super().__init__(parent)
        from ..components.navigation import NavigationBar

        self.setTitleBar(MSFluentTitleBar(self))

        self.navigationInterface = NavigationBar(self)

        # 初始化布局
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackedWidget, 1)

        self.titleBar.raise_()
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

    def addSubInterface(self, interface: QWidget, icon: Union[FluentIconBase, QIcon, str], text: str,
                        selectedIcon=None, position=None, isTransparent=False) -> 'NavigationBarPushButton':
        """添加子界面
        
        调用此方法前，必须先为 interface 设置 objectName
        
        Args:
            interface (QWidget): 要添加的子界面，调用前必须已设置 objectName
            icon (Union[FluentIconBase, QIcon, str]): 导航项图标
            text (str): 导航项文本
            selectedIcon (str | QIcon | FluentIconBase): 导航项选中状态下的图标
            position (NavigationItemPosition): 导航项位置
            isTransparent: 是否使用透明背景
        """
        if not interface.objectName():
            raise ValueError("The object name of `interface` can't be empty string.")

        position = position or NavigationItemPosition.TOP

        interface.setProperty("isStackedTransparent", isTransparent)
        self.stackedWidget.addWidget(interface)

        # 将界面注册到导航栏.
        routeKey = interface.objectName()
        item = self.navigationInterface.addItem(
            routeKey=routeKey,
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            selectedIcon=selectedIcon,
            position=position
        )

        if self.stackedWidget.count() == 1:
            self.stackedWidget.currentChanged.connect(self._onCurrentInterfaceChanged)
            self.navigationInterface.setCurrentItem(routeKey)
            qrouter.setDefaultRouteKey(self.stackedWidget, routeKey)

        self._updateStackedBackground()

        return item

    def removeInterface(self, interface, isDelete=False):
        self.navigationInterface.removeWidget(interface.objectName())
        self.stackedWidget.removeWidget(interface)
        interface.hide()

        if isDelete:
            interface.deleteLater()


class SplitTitleBar(TitleBar):

    def __init__(self, parent):
        super().__init__(parent)
        # 添加窗口图标.
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 12)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # 添加标题标签.
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        FluentStyleSheet.FLUENT_WINDOW.apply(self)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class SplitFluentWindow(FluentWindow):
    """分栏风格的 Fluent 窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitleBar(SplitTitleBar(self))

        if sys.platform == "darwin":
            self.titleBar.setFixedHeight(48)

        self.widgetLayout.setContentsMargins(0, 0, 0, 0)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)


class FluentBackgroundTheme:
    """Fluent 背景主题"""
    DEFAULT = (QColor(243, 243, 243), QColor(32, 32, 32))   # 亮色, 暗色
    DEFAULT_BLUE = (QColor(240, 244, 249), QColor(25, 33, 42))
