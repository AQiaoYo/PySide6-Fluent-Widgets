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
    """支持 Fluent 设计系统的自定义部件基类，提供主题感知背景和亚克力/云母材质渲染能力
    
    通常作为需要跟随系统主题自动切换背景色的可视化组件的基类使用，一般由框架内部派生，不建议直接实例化
    """

    def __init__(self, parent=None):
        """初始化 Fluent 部件
        
        Args:
            parent: 父部件，默认为 None。指定父部件时该部件将随父部件一同销毁并内嵌显示
        """
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
    """所有 Fluent 风格窗口的抽象基类，封装了导航视图、堆叠窗口和自定义标题栏的通用交互逻辑
    
    继承该类可快速构建具有 Fluent 设计特征的自定义主窗口，建议优先使用 FluentWindow、MSFluentWindow 或 SplitFluentWindow 等具体子类
    """

    def __init__(self, parent=None):
        """初始化窗口基类
        
        Args:
            parent: 父窗口，默认为 None。作为主窗口时不应指定父部件
        """
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
    """Fluent 风格标题栏上的窗口控制按钮，用于实现最小化、最大化/还原和关闭操作
    
    按钮内置悬浮高亮和按下反馈动画，仅作为 FluentTitleBar 及其子类的内部组件使用
    """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], parent=None):
        """初始化标题栏按钮
        
        Args:
            icon: 按钮显示的图标，类型为 QIcon
            parent: 父部件，通常为标题栏实例
        """
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
    """Fluent 风格窗口的标准标题栏，包含窗口标题、图标以及最小化、最大化和关闭按钮
    
    支持响应式布局与按钮自定义，适用于 FluentWindow 等标准单栏窗口
    """

    def __init__(self, parent):
        """初始化标题栏
        
        Args:
            parent: 父窗口，默认为 None。必须为有效窗口以便标题栏控制按钮能正确操作窗口状态
        """
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
    """标准 Fluent 风格的主窗口，集成左侧可折叠导航栏、堆叠内容区和自定义标题栏
    
    适用于需要多页面导航的桌面应用程序，通过 addSubInterface 方法添加子界面并自动生成导航项
    """

    def __init__(self, parent=None):
        """初始化主窗口
        
        Args:
            parent: 父窗口，默认为 None。作为主窗口使用时通常不指定父部件
        """
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
    """Microsoft Store 风格的标题栏，在标准标题栏基础上集成返回按钮与更紧凑的布局
    
    适用于 MSFluentWindow，用于构建具有层级导航回退能力的现代应用界面
    """

    def __init__(self, parent):
        """初始化 Microsoft Store 风格标题栏
        
        Args:
            parent: 父窗口，默认为 None
        """
        super().__init__(parent)
        self.hBoxLayout.insertSpacing(0, 20)
        self.hBoxLayout.insertSpacing(2, 2)


class FluentWidgetTitleBar(FluentTitleBar):
    """用于内嵌部件或对话框场景的标题栏，提供标题文本展示和关闭控制功能
    
    适用于需要在非顶层窗口（如卡片、弹窗）中模拟标题栏的自定义容器
    """

    def __init__(self, parent):
        """初始化部件标题栏
        
        Args:
            parent: 父部件，默认为 None
        """
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
    """Microsoft Store 风格的 Fluent 主窗口，采用左侧导航与顶部返回按钮的组合布局
    
    适用于具有明确层级结构、需要频繁向前向后导航的现代桌面应用，视觉上更接近微软官方商店的设计语言
    """

    def __init__(self, parent=None):
        """初始化主窗口
        
        Args:
            parent: 父窗口，默认为 None。作为主窗口使用时通常不指定父部件
        """
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
    """分栏式 Fluent 窗口的专用标题栏，支持在标题区域整合导航指示器与窗口控制按钮
    
    通常与 SplitFluentWindow 配合使用，为左右分栏布局提供统一的顶部视觉控制区域
    """

    def __init__(self, parent):
        """初始化分栏标题栏
        
        Args:
            parent: 父窗口，默认为 None
        """
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
    """分栏式 Fluent 风格主窗口，具有可折叠的左侧导航栏与右侧内容区，类似 Windows 11 文件资源管理器布局
    
    适用于需要同时展示导航树与详细内容的场景，如文件管理器、设置中心或邮件客户端
    """

    def __init__(self, parent=None):
        """初始化主窗口
        
        Args:
            parent: 父窗口，默认为 None。作为主窗口使用时通常不指定父部件
        """
        super().__init__(parent)
        self.setTitleBar(SplitTitleBar(self))

        if sys.platform == "darwin":
            self.titleBar.setFixedHeight(48)

        self.widgetLayout.setContentsMargins(0, 0, 0, 0)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)


class FluentBackgroundTheme:
    """Fluent 窗口背景主题枚举，定义自动、亮色、深色以及亚克力、云母等材质背景选项
    
    用于控制 FluentWindowBase 系列窗口的背景渲染效果，可在构造时传入或通过主题切换接口动态调整
    """
    DEFAULT = (QColor(243, 243, 243), QColor(32, 32, 32))   # 亮色, 暗色
    DEFAULT_BLUE = (QColor(240, 244, 249), QColor(25, 33, 42))
