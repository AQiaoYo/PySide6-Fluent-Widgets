# coding: utf-8
""" 按钮组件模块

提供 PushButton、ToolButton、RadioButton 及其变体，
支持主题色、透明、下拉、分离式等样式
"""
from typing import Union

from PySide6.QtCore import Signal, QUrl, Qt, QRectF, QSize, QPoint, Property, QRect
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QColor, QPainterPath
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QRadioButton, QToolButton, QApplication, QWidget, QSizePolicy

from ...common.animation import TranslateYAnimation
from ...common.icon import FluentIconBase, drawIcon, isDarkTheme, Theme, toQIcon, Icon
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont, getFont
from ...common.style_sheet import FluentStyleSheet, themeColor, ThemeColor
from ...common.color import autoFallbackThemeColor
from ...common.overload import singledispatchmethod
from .menu import RoundMenu, MenuAnimationType


class PushButton(QPushButton):
    """标准推送按钮，用于触发常见的界面操作
    
    适用于提交表单、确认对话框、执行命令等常规交互场景，支持文本和图标组合展示
    
    构造函数重载:
        * PushButton(parent: QWidget = None)
        * PushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * PushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """ 初始化按钮

        Args:
            parent: 父部件，默认为 None
        """
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.isPressed = False
        self.isHover = False
        self.setIconSize(QSize(16, 16))
        self.setIcon(None)
        setFont(self)
        self._postInit()

    @__init__.register
    def _(self, text: str, parent: QWidget = None, icon: Union[QIcon, str, FluentIconBase] = None):
        self.__init__(parent=parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def _postInit(self):
        pass

    def setIcon(self, icon: Union[QIcon, str, FluentIconBase]):
        """ 设置按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase、str 或 None
        """
        if icon is None or (isinstance(icon, QIcon) and icon.isNull()):
            self.setProperty('hasIcon', False)
        else:
            self.setProperty('hasIcon', True)

        self.setStyle(QApplication.style())
        self._icon = icon or QIcon()
        self.update()

    def icon(self):
        """ 获取按钮图标

        Returns:
            QIcon 图标实例
        """
        return toQIcon(self._icon)

    def setProperty(self, name: str, value) -> bool:
        """ 设置属性

        当 name 为 'icon' 时，自动调用 setIcon 处理

        Args:
            name: 属性名
            value: 属性值

        Returns:
            设置是否成功
        """
        if name != 'icon':
            return super().setProperty(name, value)

        self.setIcon(value)
        return True

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        """ 绘制按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase 或 str
            painter: QPainter 绘图对象
            rect: 绘制区域
            state: 图标状态，默认为 QIcon.Off
        """
        drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.icon().isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.3628)
        elif self.isPressed:
            painter.setOpacity(0.786)

        w, h = self.iconSize().width(), self.iconSize().height()
        y = (self.height() - h) / 2
        mw = self.minimumSizeHint().width()
        if mw > 0:
            x = 12 + (self.width() - mw) // 2
        else:
            x = 12

        if self.isRightToLeft():
            x = self.width() - w - x

        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))


class PrimaryPushButton(PushButton):
    """主题色推送按钮，用于强调当前界面的主要操作
    
    通常在一个操作区域中只使用一个，以视觉高亮引导用户完成核心任务，如保存、提交或继续
    
    构造函数重载:
        * PrimaryPushButton(parent: QWidget = None)
        * PrimaryPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * PrimaryPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            # reverse 图标 颜色
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.icon(theme)
        elif not self.isEnabled():
            painter.setOpacity(0.786 if isDarkTheme() else 0.9)
            if isinstance(icon, FluentIconBase):
                icon = icon.icon(Theme.DARK)

        PushButton._drawIcon(self, icon, painter, rect, state)


class TransparentPushButton(PushButton):
    """透明背景推送按钮，用于次要或低频操作
    
    在需要减少视觉干扰的界面中使用，悬浮或点击时才会显现明显的背景反馈，适合工具栏或列表内的辅助操作
    
    构造函数重载:
        * TransparentPushButton(parent: QWidget = None)
        * TransparentPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * TransparentPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """


class ToggleButton(PushButton):
    """状态切换按钮，用于在两种互斥状态之间切换
    
    适用于需要开启/关闭某项功能或切换视图模式的场景，点击后按钮会保持选中或取消选中的视觉状态
    
    构造函数重载:
        * ToggleButton(parent: QWidget = None)
        * ToggleButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * ToggleButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def _postInit(self):
        self.setCheckable(True)
        self.setChecked(False)

    def _drawIcon(self, icon, painter, rect):
        if not self.isChecked():
            return PushButton._drawIcon(self, icon, painter, rect)

        PrimaryPushButton._drawIcon(self, icon, painter, rect, QIcon.On)


TogglePushButton = ToggleButton


class TransparentTogglePushButton(TogglePushButton):
    """透明背景的状态切换按钮，用于轻量级的开关切换
    
    在需要保持界面简洁的同时提供状态切换能力，常用于工具栏、侧边栏或卡片内的功能启停控制
    
    构造函数重载:
        * TransparentTogglePushButton(parent: QWidget = None)
        * TransparentTogglePushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * TransparentTogglePushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """


class HyperlinkButton(PushButton):
    """超链接样式按钮，用于打开外部链接或执行页面跳转
    
    以文本链接形式呈现，通常带有下划线或主题色高亮，适合在提示信息、关于页面或登录界面中引导用户访问相关资源
    
    构造函数重载:
        * HyperlinkButton(parent: QWidget = None)
        * HyperlinkButton(url: str, text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * HyperlinkButton(icon: QIcon | FluentIconBase, url: str, text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化控件
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent)
        self._url = QUrl()
        FluentStyleSheet.BUTTON.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        setFont(self)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, url: str, text: str, parent: QWidget = None, icon: Union[QIcon, FluentIconBase, str] = None):
        self.__init__(parent)
        self.setText(text)
        self.url.setUrl(url)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, url: str, text: str, parent: QWidget = None):
        self.__init__(url, text, parent, icon)

    def getUrl(self):
        """ 获取超链接 URL

        Returns:
            QUrl URL 实例
        """
        return self._url

    def setUrl(self, url: Union[str, QUrl]):
        """ 设置超链接 URL

        Args:
            url: URL 字符串或 QUrl 实例
        """
        self._url = QUrl(url)

    def _onClicked(self):
        if self.getUrl().isValid():
            QDesktopServices.openUrl(self.getUrl())

    def _drawIcon(self, icon, painter, rect, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            icon = icon.icon(color=themeColor())
        elif not self.isEnabled():
            painter.setOpacity(0.3628 if isDarkTheme() else 0.36)

        drawIcon(icon, painter, rect, state)

    url = Property(QUrl, getUrl, setUrl)


class RadioButton(QRadioButton):
    """单选按钮，用于在一组互斥选项中选择其中一项
    
    通常与 QButtonGroup 配合使用，确保同一组内只有一个按钮被选中，适用于性别选择、支付方式或分类筛选等场景
    
    构造函数重载:
        * RadioButton(parent: QWidget = None)
        * RadioButton(text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化单选按钮
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent)
        self._lightTextColor = QColor(0, 0, 0)
        self._darkTextColor = QColor(255, 255, 255)
        self.lightIndicatorColor = QColor()
        self.darkIndicatorColor = QColor()
        self.indicatorPos = QPoint(11, 12)
        self.isHover = False

        FluentStyleSheet.BUTTON.apply(self)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self._postInit()

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def _postInit(self):
        pass

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self._drawIndicator(painter)
        self._drawText(painter)

    def _drawText(self, painter: QPainter):
        if not self.isEnabled():
            painter.setOpacity(0.36)

        painter.setFont(self.font())
        painter.setPen(self.textColor())
        painter.drawText(QRect(29, 0, self.width(), self.height()), Qt.AlignVCenter, self.text())

    def _drawIndicator(self, painter: QPainter):
        if self.isChecked():
            if self.isEnabled():
                borderColor = autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor)
            else:
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

            filledColor = Qt.black if isDarkTheme() else Qt.white

            if self.isHover and not self.isDown():
                self._drawCircle(painter, self.indicatorPos, 10, 4, borderColor, filledColor)
            else:
                self._drawCircle(painter, self.indicatorPos, 10, 5, borderColor, filledColor)

        else:
            if self.isEnabled():
                if not self.isDown():
                    borderColor = QColor(255, 255, 255, 153) if isDarkTheme() else QColor(0, 0, 0, 153)
                else:
                    borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

                if self.isDown():
                    filledColor = Qt.black if isDarkTheme() else Qt.white
                elif self.isHover:
                    filledColor = QColor(255, 255, 255, 11) if isDarkTheme() else QColor(0, 0, 0, 15)
                else:
                    filledColor = QColor(0, 0, 0, 26) if isDarkTheme() else QColor(0, 0, 0, 6)
            else:
                filledColor = Qt.transparent
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 55)

            self._drawCircle(painter, self.indicatorPos, 10, 1, borderColor, filledColor)

            if self.isEnabled() and self.isDown():
                borderColor = QColor(255, 255, 255, 40) if isDarkTheme() else QColor(0, 0, 0, 24)
                self._drawCircle(painter, self.indicatorPos, 9, 4, borderColor, Qt.transparent)

    def _drawCircle(self, painter: QPainter, center: QPoint, radius, thickness, borderColor, filledColor):
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)

        # outer circle (边框)
        outerRect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        path.addEllipse(outerRect)

        # inner center (filled)
        ir = radius - thickness
        innerRect = QRectF(center.x() - ir, center.y() - ir, 2 * ir, 2 * ir)
        innerPath = QPainterPath()
        innerPath.addEllipse(innerRect)

        path = path.subtracted(innerPath)

        # 绘制outer ring
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, borderColor)

        # fill inner circle
        painter.fillPath(innerPath, filledColor)

    def textColor(self):
        return self.darkTextColor if isDarkTheme() else self.lightTextColor

    def getLightTextColor(self) -> QColor:
        return self._lightTextColor

    def getDarkTextColor(self) -> QColor:
        return self._darkTextColor

    def setLightTextColor(self, color: QColor):
        """ 设置亮色主题下的文本颜色

        Args:
            color: 文本颜色
        """
        self._lightTextColor = QColor(color)
        self.update()

    def setDarkTextColor(self, color: QColor):
        """ 设置暗色主题下的文本颜色

        Args:
            color: 文本颜色
        """
        self._darkTextColor = QColor(color)
        self.update()

    def setIndicatorColor(self, light, dark):
        """ 设置单选指示器颜色

        Args:
            light: 亮色主题下的指示器颜色
            dark: 暗色主题下的指示器颜色
        """
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()

    def setTextColor(self, light, dark):
        """ 设置文本颜色（亮色/暗色主题）

        Args:
            light: 亮色主题下的文本颜色
            dark: 暗色主题下的文本颜色
        """
        self.setLightTextColor(light)
        self.setDarkTextColor(dark)

    lightTextColor = Property(QColor, getLightTextColor, setLightTextColor)
    darkTextColor = Property(QColor, getDarkTextColor, setDarkTextColor)


class ToolButton(QToolButton):
    """工具按钮，用于在工具栏中执行快捷操作
    
    仅显示图标或简短文本，占用空间较小，适合在窗口标题栏、侧边工具栏或富文本编辑器的格式栏中密集排列
    
    构造函数重载:
        * ToolButton(parent: QWidget = None)
        * ToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化工具按钮
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent)
        FluentStyleSheet.BUTTON.apply(self)
        self.isPressed = False
        self.isHover = False
        self.setIconSize(QSize(16, 16))
        self.setIcon(QIcon())
        setFont(self)
        self._postInit()

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    def _postInit(self):
        pass

    def setIcon(self, icon: Union[QIcon, str, FluentIconBase]):
        """ 设置按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase 或 str
        """
        self._icon = icon
        self.update()

    def icon(self):
        """ 获取按钮图标

        Returns:
            QIcon 图标实例
        """
        return toQIcon(self._icon)

    def setProperty(self, name: str, value) -> bool:
        """ 设置属性

        当 name 为 'icon' 时，自动调用 setIcon 处理

        Args:
            name: 属性名
            value: 属性值

        Returns:
            设置是否成功
        """
        if name != 'icon':
            return super().setProperty(name, value)

        self.setIcon(value)
        return True

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        """ 绘制按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase 或 str
            painter: QPainter 绘图对象
            rect: 绘制区域
            state: 图标状态，默认为 QIcon.Off
        """
        drawIcon(icon, painter, rect, state)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._icon is None:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.43)
        elif self.isPressed:
            painter.setOpacity(0.63)

        w, h = self.iconSize().width(), self.iconSize().height()
        y = (self.height() - h) / 2
        x = (self.width() - w) / 2
        self._drawIcon(self._icon, painter, QRectF(x, y, w, h))


class TransparentToolButton(ToolButton):
    """透明背景工具按钮，用于工具栏中的次要或辅助操作
    
    在没有选中或悬浮时与背景融为一体，可减少工具栏的视觉重量，适合在需要突出内容而非控件的创意或媒体应用中使用
    
    构造函数重载:
        * TransparentToolButton(parent: QWidget = None)
        * TransparentToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """


class PrimaryToolButton(ToolButton):
    """主题色工具按钮，用于强调工具栏中的核心功能
    
    通过主题色背景突出当前最重要的工具操作，如保存、刷新或新建，通常在一个功能区域中少量使用以避免视觉混乱
    
    构造函数重载:
        * PrimaryToolButton(parent: QWidget = None)
        * PrimaryToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        if isinstance(icon, FluentIconBase) and self.isEnabled():
            # reverse 图标 颜色
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.icon(theme)
        elif isinstance(icon, Icon) and self.isEnabled():
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.fluentIcon.icon(theme)
        elif not self.isEnabled():
            painter.setOpacity(0.786 if isDarkTheme() else 0.9)
            if isinstance(icon, FluentIconBase):
                icon = icon.icon(Theme.DARK)

        return drawIcon(icon, painter, rect, state)


class ToggleToolButton(ToolButton):
    """状态切换工具按钮，用于工具栏中的功能开关
    
    在需要开启/关闭某个编辑模式、视图选项或面板显示时使用，选中状态会保持高亮以明确告知用户当前功能是否启用
    
    构造函数重载:
        * ToggleToolButton(parent: QWidget = None)
        * ToggleToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def _postInit(self):
        self.setCheckable(True)
        self.setChecked(False)

    def _drawIcon(self, icon, painter, rect):
        if not self.isChecked():
            return ToolButton._drawIcon(self, icon, painter, rect)

        PrimaryToolButton._drawIcon(self, icon, painter, rect, QIcon.On)


class TransparentToggleToolButton(ToggleToolButton):
    """透明背景的状态切换工具按钮，用于轻量级的功能开关
    
    适合在简洁风格的工具栏或浮动面板中使用，在保持界面干净的同时提供可视化的选中状态反馈
    
    构造函数重载:
        * TransparentToggleToolButton(parent: QWidget = None)
        * TransparentToggleToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """


class DropDownButtonBase:
    """下拉按钮基类，为带下拉箭头的按钮提供通用功能
    
    继承此类可快速实现点击后弹出菜单或选项列表的复合按钮，通常与 PushButton 或 ToolButton 组合使用以实现更多命令收纳
    """

    def __init__(self, *args, **kwargs):
        """初始化下拉按钮基类
        
        Args:
            *args: 位置参数，用于兼容子类多样化的构造参数
            **kwargs: 关键字参数，用于兼容子类多样化的构造参数
        """
        super().__init__(*args, **kwargs)
        self._menu = None
        self.arrowAni = TranslateYAnimation(self)

    def setMenu(self, menu: RoundMenu):
        """ 设置下拉菜单

        Args:
            menu: RoundMenu 菜单实例
        """
        self._menu = menu

    def menu(self) -> RoundMenu:
        """ 获取下拉菜单

        Returns:
            RoundMenu 菜单实例，未设置时返回 None
        """
        return self._menu

    def _showMenu(self):
        if not self.menu():
            return

        menu = self.menu()
        menu.view.setMinimumWidth(self.width())
        menu.view.adjustSize()
        menu.adjustSize()

        # 根据可用高度选择动画类型.
        x = -menu.width()//2 + menu.layout().contentsMargins().left() + self.width()//2
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def _hideMenu(self):
        if self.menu():
            self.menu().hide()

    def _drawDropDownIcon(self, painter, rect):
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(self.width()-22, self.height() /
                      2-5+self.arrowAni.y, 10, 10)
        self._drawDropDownIcon(painter, rect)


class DropDownPushButton(DropDownButtonBase, PushButton):
    """带下拉箭头的推送按钮，用于执行主操作并展开相关选项
    
    主按钮区域响应最常见的命令，下拉箭头区域展示更多同组操作，适合保存为、分享或格式设置等具有多种变体的场景
    
    构造函数重载:
        * DropDownPushButton(parent: QWidget = None)
        * DropDownPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * DropDownPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def mouseReleaseEvent(self, e):
        PushButton.mouseReleaseEvent(self, e)
        self._showMenu()

    def paintEvent(self, e):
        PushButton.paintEvent(self, e)
        DropDownButtonBase.paintEvent(self, e)


class TransparentDropDownPushButton(DropDownPushButton):
    """透明背景的带下拉箭头推送按钮，用于次要的分组操作
    
    在需要保持界面简洁的同时提供多级命令入口，点击下拉箭头可展开与当前上下文相关的附加选项
    
    构造函数重载:
        * TransparentDropDownPushButton(parent: QWidget = None)
        * TransparentDropDownPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * TransparentDropDownPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """


class DropDownToolButton(DropDownButtonBase, ToolButton):
    """带下拉箭头的工具按钮，用于工具栏中的复合快捷操作
    
    图标区域执行默认命令，下拉箭头展开同类命令列表，适合在有限空间内提供一组相关的编辑或视图控制功能
    
    构造函数重载:
        * DropDownToolButton(parent: QWidget = None)
        * DropDownToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def mouseReleaseEvent(self, e):
        ToolButton.mouseReleaseEvent(self, e)
        self._showMenu()

    def _drawIcon(self, icon, painter, rect: QRectF):
        rect.moveLeft(12)
        return super()._drawIcon(icon, painter, rect)

    def paintEvent(self, e):
        ToolButton.paintEvent(self, e)
        DropDownButtonBase.paintEvent(self, e)


class TransparentDropDownToolButton(DropDownToolButton):
    """透明背景的带下拉箭头工具按钮，用于轻量级的复合工具操作
    
    在简洁风格的工具栏中提供默认操作与附加选项的分离入口，悬浮时显现背景以提示可交互性
    
    构造函数重载:
        * TransparentDropDownToolButton(parent: QWidget = None)
        * TransparentDropDownToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """


class PrimaryDropDownButtonBase(DropDownButtonBase):
    """主题色下拉按钮基类，为主题色样式的下拉按钮提供通用实现
    
    继承此类可构建带有下拉箭头的高强调度按钮，常用于需要突出展示主要命令组的应用栏或对话框底部
    """

    def _drawDropDownIcon(self, painter, rect):
        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
        FIF.ARROW_DOWN.render(painter, rect, theme)


class PrimaryDropDownPushButton(PrimaryDropDownButtonBase, PrimaryPushButton):
    """主题色带下拉箭头推送按钮，用于强调最重要的分组操作
    
    通过主题色突出主命令入口，下拉区域收纳同类变体命令，适合新建、导出等高频且有多选项的核心业务流程
    
    构造函数重载:
        * PrimaryDropDownPushButton(parent: QWidget = None)
        * PrimaryDropDownPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * PrimaryDropDownPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def mouseReleaseEvent(self, e):
        PrimaryPushButton.mouseReleaseEvent(self, e)
        self._showMenu()

    def paintEvent(self, e):
        PrimaryPushButton.paintEvent(self, e)
        PrimaryDropDownButtonBase.paintEvent(self, e)


class PrimaryDropDownToolButton(PrimaryDropDownButtonBase, PrimaryToolButton):
    """主题色带下拉箭头工具按钮，用于强调工具栏中的核心复合操作
    
    在工具栏中以主题色图标突出最常用命令，下拉箭头提供相关选项，适合主题切换、缩放级别或样式库选择等场景
    
    构造函数重载:
        * PrimaryDropDownToolButton(parent: QWidget = None)
        * PrimaryDropDownToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def mouseReleaseEvent(self, e):
        PrimaryToolButton.mouseReleaseEvent(self, e)
        self._showMenu()

    def _drawIcon(self, icon, painter, rect: QRectF):
        rect.moveLeft(12)
        return super()._drawIcon(icon, painter, rect)

    def paintEvent(self, e):
        PrimaryToolButton.paintEvent(self, e)
        PrimaryDropDownButtonBase.paintEvent(self, e)


class SplitDropButton(ToolButton):
    """分离式按钮的下拉箭头部件，用于触发下拉菜单弹出
    
    作为 SplitPushButton 或 SplitToolButton 的附属组件，单独响应下拉箭头区域的点击事件以展开选项列表，通常不独立使用
    """

    def _postInit(self):
        self.arrowAni = TranslateYAnimation(self)
        self.setIcon(FIF.ARROW_DOWN)
        self.setIconSize(QSize(10, 10))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

    def _drawIcon(self, icon, painter, rect):
        rect.translate(0, self.arrowAni.y)

        if self.isPressed:
            painter.setOpacity(0.5)
        elif self.isHover:
            painter.setOpacity(1)
        else:
            painter.setOpacity(0.63)

        super()._drawIcon(icon, painter, rect)


class PrimarySplitDropButton(PrimaryToolButton):
    """主题色分离式按钮的下拉箭头部件，用于触发下拉菜单弹出
    
    以主题色样式呈现，配合 PrimarySplitPushButton 等控件使用，负责处理下拉区域的点击与菜单展示逻辑
    """

    def _postInit(self):
        self.arrowAni = TranslateYAnimation(self)
        self.setIcon(FIF.ARROW_DOWN)
        self.setIconSize(QSize(10, 10))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

    def _drawIcon(self, icon, painter, rect):
        rect.translate(0, self.arrowAni.y)

        if self.isPressed:
            painter.setOpacity(0.7)
        elif self.isHover:
            painter.setOpacity(0.9)
        else:
            painter.setOpacity(1)

        if isinstance(icon, FluentIconBase):
            icon = icon.icon(Theme.DARK if not isDarkTheme() else Theme.LIGHT)

        super()._drawIcon(icon, painter, rect)


class SplitWidgetBase(QWidget):
    """分离式部件基类，提供主按钮与下拉箭头分离布局的通用实现
    
    继承此类可将默认操作与下拉选项物理分离，让用户直接点击主区域执行最常用命令，或通过下拉箭头选择其他变体，适合保存为、发送等具有明确主次之分的场景
    """

    dropDownClicked = Signal()

    def __init__(self, parent=None):
        """初始化分离式部件基类
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent=parent)
        self.flyout = None  # type: QWidget
        self.dropButton = SplitDropButton(self)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.dropButton)

        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def setWidget(self, widget: QWidget):
        """ 设置左侧主按钮部件

        Args:
            widget: 要设置的部件
        """
        self.hBoxLayout.insertWidget(0, widget, 1, Qt.AlignLeft)

    def setDropButton(self, button):
        """ 设置下拉按钮

        Args:
            button: 下拉按钮实例
        """
        self.hBoxLayout.removeWidget(self.dropButton)
        self.dropButton.deleteLater()

        self.dropButton = button
        self.dropButton.clicked.connect(self.dropDownClicked)
        self.dropButton.clicked.connect(self.showFlyout)
        self.hBoxLayout.addWidget(button)

    def setDropIcon(self, icon: Union[str, QIcon, FluentIconBase]):
        """ 设置下拉按钮的图标

        Args:
            icon: 图标，可为 str、QIcon 或 FluentIconBase
        """
        self.dropButton.setIcon(icon)
        self.dropButton.removeEventFilter(self.dropButton.arrowAni)

    def setDropIconSize(self, size: QSize):
        """ 设置下拉按钮的图标大小

        Args:
            size: 图标尺寸
        """
        self.dropButton.setIconSize(size)

    def setFlyout(self, flyout):
        """ 设置点击下拉按钮时弹出的部件

        Args:
            flyout: 点击下拉按钮时弹出的部件，需提供 exec(pos: QPoint) 方法
        """
        self.flyout = flyout

    def showFlyout(self):
        """ 显示浮出层

        若未设置 flyout 则直接返回
        """
        if not self.flyout:
            return

        w = self.flyout

        if isinstance(w, RoundMenu):
            w.view.setMinimumWidth(self.width())
            w.view.adjustSize()
            w.adjustSize()

        dx = w.layout().contentsMargins().left() if isinstance(w, RoundMenu) else 0
        x = -w.width()//2 + dx + self.width()//2
        y = self.height()
        w.exec(self.mapToGlobal(QPoint(x, y)))


class SplitPushButton(SplitWidgetBase):
    """分离式推送按钮，将主操作与下拉选项分离为两个可点击区域
    
    左侧主按钮直接执行默认命令，右侧下拉箭头展开相关选项列表，适合在表单或对话框中提供高频主操作与低频选项的快捷入口
    
    构造函数重载:
        * SplitPushButton(parent: QWidget = None)
        * SplitPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
    """

    clicked = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化分离式推送按钮
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent=parent)
        self.button = PushButton(self)
        self.button.setObjectName('splitPushButton')
        self.button.clicked.connect(self.clicked)
        self.setWidget(self.button)
        self._postInit()

    @__init__.register
    def _(self, text: str, parent: QWidget = None, icon: Union[QIcon, str, FluentIconBase] = None):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QWidget = None):
        self.__init__(text, parent, icon)

    def _postInit(self):
        pass

    def text(self):
        """ 获取按钮文本

        Returns:
            str 当前文本
        """
        return self.button.text()

    def setText(self, text: str):
        """ 设置按钮文本

        Args:
            text: 文本内容
        """
        self.button.setText(text)
        self.adjustSize()

    def icon(self):
        """ 获取按钮图标

        Returns:
            QIcon 图标实例
        """
        return self.button.icon()

    def setIcon(self, icon: Union[QIcon, FluentIconBase, str]):
        """ 设置按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase 或 str
        """
        self.button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """ 设置图标大小

        Args:
            size: 图标尺寸
        """
        self.button.setIconSize(size)

    text_ = Property(str, text, setText)
    icon_ = Property(QIcon, icon, setIcon)


class PrimarySplitPushButton(SplitPushButton):
    """主题色分离式推送按钮，以高强调度呈现主次分明的操作入口
    
    左侧主题色按钮执行最核心的默认命令，右侧下拉箭头提供相关变体，适用于保存、发布、打印等业务流程中的主行动点
    
    构造函数重载:
        * PrimarySplitPushButton(parent: QWidget = None)
        * PrimarySplitPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * PrimarySplitPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def _postInit(self):
        self.setDropButton(PrimarySplitDropButton(self))

        self.hBoxLayout.removeWidget(self.button)
        self.button.deleteLater()

        self.button = PrimaryPushButton(self)
        self.button.setObjectName('primarySplitPushButton')
        self.button.clicked.connect(self.clicked)
        self.setWidget(self.button)


class SplitToolButton(SplitWidgetBase):
    """分离式工具按钮，用于工具栏中主次分明的快捷操作
    
    图标区域直接执行默认命令，下拉箭头展开同组命令选项，适合在紧凑的工具栏中提供多样化的格式或视图控制
    
    构造函数重载:
        * SplitToolButton(parent: QWidget = None)
        * SplitToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    clicked = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化分离式工具按钮
        
        Args:
            parent (QWidget): 父级窗口部件，None 表示无父控件
        """
        super().__init__(parent=parent)
        self.button = ToolButton(self)
        self.button.setObjectName('splitToolButton')
        self.button.clicked.connect(self.clicked)
        self.setWidget(self.button)
        self._postInit()

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: str, parent: QWidget = None):
        self.__init__(parent)
        self.setIcon(icon)

    def _postInit(self):
        pass

    def icon(self):
        """ 获取按钮图标

        Returns:
            QIcon 图标实例
        """
        return self.button.icon()

    def setIcon(self, icon: Union[QIcon, FluentIconBase, str]):
        """ 设置按钮图标

        Args:
            icon: 图标，可为 QIcon、FluentIconBase 或 str
        """
        self.button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """ 设置图标大小

        Args:
            size: 图标尺寸
        """
        self.button.setIconSize(size)

    icon_ = Property(QIcon, icon, setIcon)


class PrimarySplitToolButton(SplitToolButton):
    """主题色分离式工具按钮，用于强调工具栏中的核心复合功能
    
    以主题色突出默认命令的优先级，下拉区域收纳相关选项，适合在应用栏中提供设置、视图模式或缩放控制等关键入口
    
    构造函数重载:
        * PrimarySplitToolButton(parent: QWidget = None)
        * PrimarySplitToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def _postInit(self):
        self.setDropButton(PrimarySplitDropButton(self))

        self.hBoxLayout.removeWidget(self.button)
        self.button.deleteLater()

        self.button = PrimaryToolButton(self)
        self.button.setObjectName('primarySplitToolButton')
        self.button.clicked.connect(self.clicked)
        self.setWidget(self.button)


class PillButtonBase:
    """Pill 按钮基类，为圆角胶囊形态的按钮提供通用实现
    
    继承此类可实现具有大圆角风格的标签式按钮，常用于导航栏、分类筛选或状态标签等需要柔和视觉风格的场景
    """

    def __init__(self, *args, **kwargs):
        """初始化 Pill 按钮基类
        
        Args:
            *args: 位置参数，用于兼容子类多样化的构造参数
            **kwargs: 关键字参数，用于兼容子类多样化的构造参数
        """
        super().__init__(*args, **kwargs)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        isDark = isDarkTheme()

        if not self.isChecked():
            rect = self.rect().adjusted(1, 1, -1, -1)
            borderColor = QColor(255, 255, 255, 18) if isDark else QColor(0, 0, 0, 15)

            if not self.isEnabled():
                bgColor = QColor(255, 255, 255, 11) if isDark else QColor(249, 249, 249, 75)
            elif self.isPressed or self.isHover:
                bgColor = QColor(255, 255, 255, 21) if isDark else QColor(249, 249, 249, 128)
            else:
                bgColor = QColor(255, 255, 255, 15) if isDark else QColor(243, 243, 243, 194)

        else:
            if not self.isEnabled():
                bgColor = QColor(255, 255, 255, 40) if isDark else QColor(0, 0, 0, 55)
            elif self.isPressed:
                bgColor = ThemeColor.DARK_2.color() if isDark else ThemeColor.LIGHT_3.color()
            elif self.isHover:
                bgColor = ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color()
            else:
                bgColor = themeColor()

            borderColor = Qt.transparent
            rect = self.rect()

        painter.setPen(borderColor)
        painter.setBrush(bgColor)

        r = rect.height() / 2
        painter.drawRoundedRect(rect, r, r)


class PillPushButton(TogglePushButton, PillButtonBase):
    """胶囊形推送按钮，以圆润的 Pill 外观呈现标准操作
    
    适合在需要柔和现代感的界面中使用，如移动端适配窗口、卡片式布局或顶部导航栏中的操作入口，视觉上比直角按钮更友好
    
    构造函数重载:
        * PillPushButton(parent: QWidget = None)
        * PillPushButton(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * PillPushButton(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    def paintEvent(self, e):
        PillButtonBase.paintEvent(self, e)
        TogglePushButton.paintEvent(self, e)


class PillToolButton(ToggleToolButton, PillButtonBase):
    """胶囊形工具按钮，以圆润的 Pill 外观呈现图标操作
    
    在需要统一柔和风格的工具栏或导航栏中使用，兼具工具按钮的紧凑性与 Pill 形状的亲和力，适合作为视图切换或筛选条件
    
    构造函数重载:
        * PillToolButton(parent: QWidget = None)
        * PillToolButton(icon: QIcon | str | FluentIconBase, parent: QWidget = None)
    """

    def paintEvent(self, e):
        PillButtonBase.paintEvent(self, e)
        ToggleToolButton.paintEvent(self, e)
