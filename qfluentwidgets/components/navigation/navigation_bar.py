# coding: utf-8
"""导航栏组件"""

from typing import Dict, Union

from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, Property, QRectF, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout

from ...common.config import isDarkTheme
from ...common.font import setFont
from ...common.style_sheet import themeColor
from ...common.color import autoFallbackThemeColor
from ...common.icon import drawIcon, FluentIconBase, toQIcon
from ...common.icon import FluentIcon as FIF
from ...common.router import qrouter
from ...common.style_sheet import FluentStyleSheet
from ..widgets.scroll_area import ScrollArea
from .navigation_widget import NavigationPushButton, NavigationWidget, NavigationIndicator
from .navigation_types import RouteKeyError, NavigationItemPosition


class IconSlideAnimation(QPropertyAnimation):
    """图标滑动动画"""

    def __init__(self, parent=None):
        """初始化动画

        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self._offset = 0
        self.maxOffset = 6
        self.setTargetObject(self)
        self.setPropertyName(b"offset")

    def getOffset(self):
        """获取偏移量"""
        return self._offset

    def setOffset(self, value: float):
        """设置偏移量

        Args:
            value: 偏移量值
        """
        self._offset = value
        self.parent().update()

    def slideDown(self):
        """向下滑动"""
        self.setEndValue(self.maxOffset)
        self.setDuration(100)
        self.start()

    def slideUp(self):
        """向上滑动"""
        self.setEndValue(0)
        self.setDuration(100)
        self.start()

    offset = Property(float, getOffset, setOffset)



class NavigationBarPushButton(NavigationPushButton):
    """导航栏按钮"""

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, selectedIcon=None, parent=None):
        """初始化按钮

        Args:
            icon: 图标
            text: 文本
            isSelectable: 是否可选中
            selectedIcon: 选中时的图标
            parent: 父对象
        """
        super().__init__(icon, text, isSelectable, parent)
        self.iconAni = IconSlideAnimation(self)
        self._selectedIcon = selectedIcon
        self._isSelectedTextVisible = True
        self.lightSelectedColor = QColor()
        self.darkSelectedColor = QColor()

        self.setFixedSize(64, 58)
        setFont(self, 11)

    def setSelectedColor(self, light, dark):
        """设置选中颜色

        Args:
            light: 浅色模式下的颜色
            dark: 深色模式下的颜色
        """
        self.lightSelectedColor = QColor(light)
        self.darkSelectedColor = QColor(dark)
        self.update()

    def selectedIcon(self):
        """获取选中图标"""
        if self._selectedIcon:
            return toQIcon(self._selectedIcon)

        return QIcon()

    def setSelectedIcon(self, icon: Union[str, QIcon, FIF]):
        """设置选中图标

        Args:
            icon: 图标
        """
        self._selectedIcon = icon
        self.update()

    def setSelectedTextVisible(self, isVisible):
        """设置选中时文本是否可见

        Args:
            isVisible: 是否可见
        """
        self._isSelectedTextVisible = isVisible
        self.update()

    def indicatorRect(self):
        """获取指示器几何区域"""
        return QRectF(0, 16, 4, 24)

    def paintEvent(self, e):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        self._drawBackground(painter)
        self._drawIcon(painter)
        self._drawText(painter)

    def _drawBackground(self, painter: QPainter):
        """绘制背景"""
        if self.isSelected or self.isAboutSelected:
            painter.setBrush(QColor(255, 255, 255, 42) if isDarkTheme() else Qt.white)
            painter.drawRoundedRect(self.rect(), 5, 5)

            # 绘制指示器
            if not self.isAboutSelected:
                painter.setBrush(autoFallbackThemeColor(self.lightSelectedColor, self.darkSelectedColor))
                if not self.isPressed:
                    painter.drawRoundedRect(0, 16, 4, 24, 2, 2)
                else:
                    painter.drawRoundedRect(0, 19, 4, 18, 2, 2)
        elif self.isPressed or self.isEnter:
            c = 255 if isDarkTheme() else 0
            alpha = 9 if self.isEnter else 6
            painter.setBrush(QColor(c, c, c, alpha))
            painter.drawRoundedRect(self.rect(), 5, 5)

    def _drawIcon(self, painter: QPainter):
        """绘制图标"""
        if (self.isPressed or not self.isEnter) and not (self.isSelected or self.isAboutSelected):
            painter.setOpacity(0.6)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        if self._isSelectedTextVisible:
            rect = QRectF(22, 13, 20, 20)
        else:
            rect = QRectF(22, 13 + self.iconAni.offset, 20, 20)

        selectedIcon = self._selectedIcon or self._icon

        if isinstance(selectedIcon, FluentIconBase) and (self.isSelected or self.isAboutSelected):
            color = autoFallbackThemeColor(self.lightSelectedColor, self.darkSelectedColor)
            selectedIcon.render(painter, rect, fill=color.name())
        elif self.isSelected or self.isAboutSelected:
            drawIcon(selectedIcon, painter, rect)
        else:
            drawIcon(self._icon, painter, rect)

    def _drawText(self, painter: QPainter):
        """绘制文本"""
        if self.isSelected and not self._isSelectedTextVisible:
            return

        if self.isSelected or self.isAboutSelected:
            painter.setPen(autoFallbackThemeColor(self.lightSelectedColor, self.darkSelectedColor))
        else:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)

        painter.setFont(self.font())
        rect = QRect(0, 32, self.width(), 26)
        painter.drawText(rect, Qt.AlignCenter, self.text())

    def setSelected(self, isSelected: bool):
        """设置选中状态

        Args:
            isSelected: 是否选中
        """
        if isSelected == self.isSelected:
            return

        self.isSelected = isSelected
        self.isAboutSelected = False

        if isSelected:
            self.iconAni.slideDown()
        else:
            self.iconAni.slideUp()


class NavigationBar(QWidget):
    """导航栏"""

    def __init__(self, parent=None):
        """初始化导航栏

        Args:
            parent: 父对象
        """
        super().__init__(parent=parent)
        self.indicator = NavigationIndicator(self)
        self._isIndicatorAnimationEnabled = True
        self._isSelectedTextVisible = True

        self.lightSelectedColor = QColor()
        self.darkSelectedColor = QColor()

        self.scrollArea = ScrollArea(self)
        self.scrollWidget = QWidget()

        self.vBoxLayout = QVBoxLayout(self)
        self.topLayout = QVBoxLayout()
        self.bottomLayout = QVBoxLayout()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)

        self.items = {}   # type: Dict[str, NavigationWidget]
        self.history = qrouter
        self._currentRouteKey = None

        self.__initWidget()

    def __initWidget(self):
        """初始化组件"""
        self.resize(48, self.height())
        self.setAttribute(Qt.WA_StyledBackground)
        self.window().installEventFilter(self)

        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.horizontalScrollBar().setEnabled(False)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)

        self.scrollWidget.setObjectName('scrollWidget')
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()

        self.indicator.aniFinished.connect(self._onIndicatorAniFinished)

    def __initLayout(self):
        """初始化布局"""
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.topLayout.setContentsMargins(4, 0, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea)
        self.vBoxLayout.addLayout(self.bottomLayout, 0)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

    def widget(self, routeKey: str):
        """根据路由键获取部件

        Args:
            routeKey: 路由键

        Returns:
            NavigationWidget: 导航部件

        Raises:
            RouteKeyError: 路由键非法时抛出
        """
        if routeKey not in self.items:
            raise RouteKeyError(f"`{routeKey}` is illegal.")

        return self.items[routeKey]

    def addItem(self, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                selectable=True, selectedIcon=None, position=NavigationItemPosition.TOP):
        """添加导航项

        Args:
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            selectedIcon: 导航项在选中状态下的图标
            position: 导航项的插入位置

        Returns:
            NavigationBarPushButton: 导航按钮
        """
        return self.insertItem(-1, routeKey, icon, text, onClick, selectable, selectedIcon, position)

    def addWidget(self, routeKey: str, widget: NavigationWidget, onClick=None, position=NavigationItemPosition.TOP):
        """添加自定义导航部件

        Args:
            routeKey: 导航项的唯一标识
            widget: 要添加的自定义部件
            onClick: 连接到点击信号的槽函数
            position: 部件的插入位置
        """
        self.insertWidget(-1, routeKey, widget, onClick, position)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                   selectable=True, selectedIcon=None, position=NavigationItemPosition.TOP):
        """插入导航项

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            selectedIcon: 导航项在选中状态下的图标
            position: 导航项的插入位置

        Returns:
            NavigationBarPushButton: 导航按钮
        """
        if routeKey in self.items:
            return

        w = NavigationBarPushButton(icon, text, selectable, selectedIcon, self)
        w.setSelectedColor(self.lightSelectedColor, self.darkSelectedColor)
        w.setSelectedTextVisible(self.isSelectedTextVisible())
        self.insertWidget(index, routeKey, w, onClick, position)
        return w

    def insertWidget(self, index: int, routeKey: str, widget: NavigationWidget, onClick=None,
                     position=NavigationItemPosition.TOP):
        """插入自定义导航部件

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            widget: 要插入的自定义部件
            onClick: 连接到点击信号的槽函数
            position: 部件的插入位置
        """
        if routeKey in self.items:
            return

        self._registerWidget(routeKey, widget, onClick)
        self._insertWidgetToLayout(index, widget, position)

    def _registerWidget(self, routeKey: str, widget: NavigationWidget, onClick):
        """注册部件

        Args:
            routeKey: 路由键
            widget: 导航部件
            onClick: 点击时触发的回调函数
        """
        widget.clicked.connect(self._onWidgetClicked)

        if onClick is not None:
            widget.clicked.connect(onClick)

        widget.setProperty('routeKey', routeKey)
        self.items[routeKey] = widget

    def _insertWidgetToLayout(self, index: int, widget: NavigationWidget, position: NavigationItemPosition):
        """将部件插入到布局

        Args:
            index: 插入位置
            widget: 导航部件
            position: 插入位置类型
        """
        if position == NavigationItemPosition.TOP:
            widget.setParent(self)
            self.topLayout.insertWidget(
                index, widget, 0, Qt.AlignTop | Qt.AlignHCenter)
        elif position == NavigationItemPosition.SCROLL:
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(
                index, widget, 0, Qt.AlignTop | Qt.AlignHCenter)
        else:
            widget.setParent(self)
            self.bottomLayout.insertWidget(
                index, widget, 0, Qt.AlignBottom | Qt.AlignHCenter)

        widget.show()

    def removeWidget(self, routeKey: str):
        """移除导航部件

        Args:
            routeKey: 导航项的唯一标识
        """
        if routeKey not in self.items:
            return

        widget = self.items.pop(routeKey)
        widget.deleteLater()
        self.history.remove(routeKey)

    def currentItem(self):
        """获取当前选中的导航项"""
        return self.widget(self._currentRouteKey) if self._currentRouteKey else None

    def setCurrentItem(self, routeKey: str):
        """设置当前选中项

        Args:
            routeKey: 导航项的唯一标识
        """
        if routeKey not in self.items or routeKey == self._currentRouteKey:
            return

        self._stopIndicatorAnimation()

        prevItem = self.currentItem()
        self._currentRouteKey = routeKey

        # 如果未启用指示器动画, 或没有上一个选中项, 则直接更新选中状态.
        if not self.isIndicatorAnimationEnabled() or prevItem is None:
            for k, widget in self.items.items():
                widget.setSelected(k == routeKey)

            return

        # 计算动画的起始和结束几何区域.
        newItem = self.currentItem()
        preIndicatorRect = self._getIndicatorRect(prevItem)
        newIndicatorRect = self._getIndicatorRect(newItem)

        # 开始动画
        prevItem.setSelected(False)
        newItem.setAboutSelected(True)
        self.indicator.raise_()
        self.indicator.setIndicatorColor(newItem.lightIndicatorColor, newItem.darkIndicatorColor)
        self.indicator.startAnimation(preIndicatorRect, newIndicatorRect)

    def setFont(self, font: QFont):
        """设置导航项字体

        Args:
            font: 字体
        """
        super().setFont(font)

        for widget in self.buttons():
            widget.setFont(font)

    def setSelectedTextVisible(self, isVisible: bool):
        """设置选中按钮时是否显示文本

        Args:
            isVisible: 是否显示
        """
        if isVisible == self._isSelectedTextVisible:
            return

        self._isSelectedTextVisible = isVisible
        for widget in self.buttons():
            widget.setSelectedTextVisible(isVisible)

    def isSelectedTextVisible(self):
        """获取选中按钮时是否显示文本"""
        return self._isSelectedTextVisible

    def setSelectedColor(self, light, dark):
        """设置所有项的选中色

        Args:
            light: 浅色模式下的颜色
            dark: 深色模式下的颜色
        """
        self.lightSelectedColor = QColor(light)
        self.darkSelectedColor = QColor(dark)
        for button in self.buttons():
            button.setSelectedColor(self.lightSelectedColor, self.darkSelectedColor)

    def buttons(self):
        """获取所有导航按钮"""
        return [i for i in self.items.values() if isinstance(i, NavigationPushButton)]

    def isIndicatorAnimationEnabled(self):
        """获取是否启用指示器动画"""
        return self._isIndicatorAnimationEnabled

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        """设置是否启用指示器动画

        Args:
            isEnabled: 是否启用
        """
        self._isIndicatorAnimationEnabled = isEnabled

    def _onWidgetClicked(self):
        """处理部件点击事件"""
        widget = self.sender()  # type: NavigationWidget
        if widget.isSelectable:
            self.setCurrentItem(widget.property('routeKey'))

    def _getIndicatorRect(self, item: NavigationWidget):
        """获取指示器几何区域

        Args:
            item: 导航部件

        Returns:
            QRect: 指示器区域
        """
        if not item:
            return QRect()

        pos = item.mapTo(self, QPoint(0, 0))
        rect = item.indicatorRect()
        return rect.translated(pos)

    def _stopIndicatorAnimation(self):
        """停止指示器动画"""
        if not self.isIndicatorAnimationEnabled():
            return

        self.indicator.stopAnimation()
        self._onIndicatorAniFinished()

    def _onIndicatorAniFinished(self):
        """指示器动画结束回调"""
        item = self.currentItem()
        if not item:
            return

        item.setAboutSelected(False)
        item.setSelected(True)
        self.indicator.hide()