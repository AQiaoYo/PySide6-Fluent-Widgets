# coding: utf-8
"""提供导航面板相关的组件，包括导航面板、导航项、布局管理器以及工具提示过滤器。通常用于构建具有层级结构的应用侧边导航栏，支持展开/收起、最小化等交互模式"""

from typing import Dict, Union

from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QSize, QEvent, QEasingCurve, Signal, QPoint, QRectF
from PySide6.QtGui import QResizeEvent, QIcon, QColor, QPainterPath
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication, QHBoxLayout

from .navigation_widget import (NavigationTreeWidgetBase, NavigationToolButton, NavigationWidget, NavigationSeparator,
                                NavigationTreeWidget, NavigationFlyoutMenu, NavigationItemHeader, NavigationIndicator)
from .navigation_types import NavigationDisplayMode, NavigationItemPosition, RouteKeyError
from ..widgets.scroll_area import ScrollArea
from ..widgets.tool_tip import ToolTipFilter
from ..widgets.scroll_bar import ScrollBarHandleDisplayMode
from ...common.router import qrouter
from ...common.style_sheet import FluentStyleSheet, isDarkTheme
from ...common.icon import FluentIconBase
from ...common.icon import FluentIcon as FIF

class NavigationToolTipFilter(ToolTipFilter):
    """Navigation 工具提示事件过滤器，用于在导航栏处于最小化或紧凑模式时，为图标项提供悬浮提示功能。当用户将鼠标悬停在仅显示图标的导航项上时，自动展示该项的完整标题提示"""

    def _canShowToolTip(self) -> bool:
        isVisible = super()._canShowToolTip()
        parent = self.parent()  # type: NavigationWidget
        return isVisible and parent.isCompacted


class NavigationItem:
    """Navigation 单项数据载体，用于描述导航栏中的一个节点。包含路由标识、层级关系以及关联的显示组件，支持构建扁平或层级化的导航结构。可通过 routeKey 唯一标识并在不同导航状态间保持对应关系"""

    def __init__(self, routeKey: str, parentRouteKey: str, widget: NavigationWidget):
        """初始化 NavigationItem 实例
        
        Args:
            routeKey (str): 当前项的唯一路由标识，用于在导航切换时定位目标页面
            parentRouteKey (str | None): 父级项的路由标识，若为顶层项可传入 None
            widget (QWidget): 与当前项绑定的显示组件，通常为 NavigationPushButton 或类似控件
        """
        self.routeKey = routeKey
        self.parentRouteKey = parentRouteKey
        self.widget = widget


class NavigationPanel(QFrame):
    """应用侧边导航面板，负责管理 NavigationItem 的生命周期、布局排列以及交互行为。支持展开、收起、最小化等多种显示模式，适用于需要多级菜单或单级导航的桌面应用场景。可通过信号与槽机制与路由框架配合实现页面切换"""

    displayModeChanged = Signal(NavigationDisplayMode)

    def __init__(self, parent=None, isMinimalEnabled=False):
        """初始化 NavigationPanel 实例
        
        Args:
            parent (QWidget | None): 父级控件实例，决定导航面板的层级归属和位置关系
            isMinimalEnabled (bool): 是否启用最小化显示模式，为 True 时导航栏可收缩为仅显示图标的窄栏
        """
        super().__init__(parent=parent)
        self._parent = parent   # type: QWidget
        self._isMenuButtonVisible = True
        self._isReturnButtonVisible = False
        self._isCollapsible = True
        self._isAcrylicEnabled = False

        self._isIndicatorAnimationEnabled = True
        self._isUpdateIndicatorPosOnCollapseFinished = False

        self.indicator = NavigationIndicator(self)

        self.acrylicBrush = None

        self.scrollArea = ScrollArea(self)
        self.scrollWidget = QWidget()

        self.menuButton = NavigationToolButton(FIF.MENU, self)
        self.returnButton = NavigationToolButton(FIF.RETURN, self)

        self.vBoxLayout = NavigationItemLayout(self)
        self.topLayout = NavigationItemLayout()
        self.bottomLayout = NavigationItemLayout()
        self.scrollLayout = NavigationItemLayout(self.scrollWidget)

        self.items = {}   # type: Dict[str, NavigationItem]
        self.history = qrouter
        self._currentRouteKey = None

        self.expandAni = QPropertyAnimation(self, b'geometry', self)
        self.expandWidth = 322
        self.minimumExpandWidth = 1008

        self.isMinimalEnabled = isMinimalEnabled
        if isMinimalEnabled:
            self.displayMode = NavigationDisplayMode.MINIMAL
        else:
            self.displayMode = NavigationDisplayMode.COMPACT

        self.__initWidget()

    def __initWidget(self):
        self.resize(48, self.height())
        self.setAttribute(Qt.WA_StyledBackground)
        self.window().installEventFilter(self)

        self.returnButton.hide()
        self.returnButton.setDisabled(True)

        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.horizontalScrollBar().setEnabled(False)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.scrollDelagate.vScrollBar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)

        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
        self.expandAni.setDuration(150)

        self.menuButton.clicked.connect(self.toggle)
        self.expandAni.finished.connect(self._onExpandAniFinished)
        self.history.emptyChanged.connect(self.returnButton.setDisabled)
        self.returnButton.clicked.connect(self.history.pop)
        self.indicator.aniFinished.connect(self._onIndicatorAniFinished)

        # 添加 工具提示
        self.returnButton.installEventFilter(ToolTipFilter(self.returnButton, 1000))
        self.returnButton.setToolTip(self.tr('Back'))

        self.menuButton.installEventFilter(ToolTipFilter(self.menuButton, 1000))
        self.menuButton.setToolTip(self.tr('Open Navigation'))

        self.scrollWidget.setObjectName('scrollWidget')
        self.setProperty('menu', False)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self)
        FluentStyleSheet.NAVIGATION_INTERFACE.apply(self.scrollWidget)
        self.__initLayout()

    def __initLayout(self):
        self.vBoxLayout.setContentsMargins(0, 5, 0, 5)
        self.topLayout.setContentsMargins(4, 0, 4, 0)
        self.bottomLayout.setContentsMargins(4, 0, 4, 0)
        self.scrollLayout.setContentsMargins(4, 0, 4, 0)
        self.vBoxLayout.setSpacing(4)
        self.topLayout.setSpacing(4)
        self.bottomLayout.setSpacing(4)
        self.scrollLayout.setSpacing(4)

        self.vBoxLayout.addLayout(self.topLayout, 0)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addLayout(self.bottomLayout, 0)

        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.topLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.bottomLayout.setAlignment(Qt.AlignBottom)

        self.topLayout.addWidget(self.returnButton, 0, Qt.AlignTop)
        self.topLayout.addWidget(self.menuButton, 0, Qt.AlignTop)

    def _updateAcrylicColor(self):
        brush = self._ensureAcrylicBrush()
        if isDarkTheme():
            tintColor = QColor(32, 32, 32, 200)
            luminosityColor = QColor(0, 0, 0, 0)
        else:
            tintColor = QColor(255, 255, 255, 180)
            luminosityColor = QColor(255, 255, 255, 0)

        brush.tintColor = tintColor
        brush.luminosityColor = luminosityColor

    def _ensureAcrylicBrush(self):
        if self.acrylicBrush is None:
            from ..widgets.acrylic_label import AcrylicBrush

            self.acrylicBrush = AcrylicBrush(self, 30)

        return self.acrylicBrush

    def isIndicatorAnimationEnabled(self):
        return self._isIndicatorAnimationEnabled

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        self._isIndicatorAnimationEnabled = isEnabled

    def isUpdateIndicatorPosOnCollapseFinished(self):
        return self._isUpdateIndicatorPosOnCollapseFinished

    def setUpdateIndicatorPosOnCollapseFinished(self, update: bool):
        self._isUpdateIndicatorPosOnCollapseFinished = update

    def widget(self, routeKey: str):
        if routeKey not in self.items:
            raise RouteKeyError(f"`{routeKey}` is illegal.")

        return self.items[routeKey].widget

    def addItem(self, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None, selectable=True,
                position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey: str = None):
        """添加导航项

        Args:
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            position: 导航项的插入位置
            tooltip: 导航项提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidget

        Returns:
            添加的导航树部件
        """
        return self.insertItem(-1, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)

    def addWidget(self, routeKey: str, widget: NavigationWidget, onClick=None, position=NavigationItemPosition.TOP,
                  tooltip: str = None, parentRouteKey: str = None):
        """添加自定义导航部件

        Args:
            routeKey: 导航项的唯一标识
            widget: 要添加的自定义部件
            onClick: 连接到点击信号的槽函数
            position: 部件的插入位置
            tooltip: 部件提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidget
        """
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip, parentRouteKey)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                   selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey=None):
        """插入导航树项

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            position: 导航项的插入位置
            tooltip: 导航项提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidget

        Returns:
            插入的导航树部件
        """
        if routeKey in self.items:
            return

        w = NavigationTreeWidget(icon, text, selectable, self)
        self.insertWidget(index, routeKey, w, onClick, position, tooltip, parentRouteKey)
        return w

    def insertWidget(self, index: int, routeKey: str, widget: NavigationWidget, onClick=None,
                     position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey: str = None):
        """插入自定义导航部件

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            widget: 要插入的自定义部件
            onClick: 连接到点击信号的槽函数
            position: 部件的插入位置
            tooltip: 部件提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidget
        """
        if routeKey in self.items:
            return

        self._registerWidget(routeKey, parentRouteKey, widget, onClick, tooltip)
        if parentRouteKey:
            self.widget(parentRouteKey).insertChild(index, widget)
        else:
            self._insertWidgetToLayout(index, widget, position)

    def addSeparator(self, position=NavigationItemPosition.TOP):
        """添加分隔符

        Args:
            position: 分隔符的插入区域
        """
        self.insertSeparator(-1, position)

    def insertSeparator(self, index: int, position=NavigationItemPosition.TOP):
        """插入分隔符

        Args:
            index: 插入位置
            position: 分隔符的插入区域
        """
        separator = NavigationSeparator(self)
        self._insertWidgetToLayout(index, separator, position)

    def addItemHeader(self, text: str, position=NavigationItemPosition.TOP):
        """添加导航分组标题

        Args:
            text: 标题文本
            position: 标题的插入位置

        Returns:
            创建的标题部件
        """
        return self.insertItemHeader(-1, text, position)

    def insertItemHeader(self, index: int, text: str, position=NavigationItemPosition.TOP):
        """插入导航分组标题

        Args:
            index: 插入位置
            text: 标题文本
            position: 标题的插入位置

        Returns:
            创建的标题部件
        """
        header = NavigationItemHeader(text, self)
        self._insertWidgetToLayout(index, header, position)

        # 根据当前显示模式设置紧凑状态.
        isCompacted = self.displayMode not in [NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU]
        header.setCompacted(isCompacted)

        return header

    def _registerWidget(self, routeKey: str, parentRouteKey: str, widget: NavigationWidget, onClick, tooltip: str):
        """注册导航部件

        Args:
            routeKey: 导航项的唯一标识
            parentRouteKey: 父级导航项的路由键
            widget: 导航部件
            onClick: 点击回调函数
            tooltip: 提示文本
        """
        widget.clicked.connect(self._onWidgetClicked)

        if onClick is not None:
            widget.clicked.connect(onClick)

        widget.setProperty('routeKey', routeKey)
        widget.setProperty('parentRouteKey', parentRouteKey)
        self.items[routeKey] = NavigationItem(routeKey, parentRouteKey, widget)

        if self.displayMode in [NavigationDisplayMode.EXPAND, NavigationDisplayMode.MENU]:
            widget.setCompacted(False)

        if tooltip:
            widget.setToolTip(tooltip)
            widget.installEventFilter(NavigationToolTipFilter(widget, 1000))

    def _insertWidgetToLayout(self, index: int, widget: NavigationWidget, position: NavigationItemPosition):
        """将部件插入布局

        Args:
            index: 插入位置
            widget: 导航部件
            position: 插入的区域位置
        """
        if position == NavigationItemPosition.TOP:
            widget.setParent(self)
            self.topLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        elif position == NavigationItemPosition.SCROLL:
            widget.setParent(self.scrollWidget)
            self.scrollLayout.insertWidget(index, widget, 0, Qt.AlignTop)
        else:
            widget.setParent(self)
            self.bottomLayout.insertWidget(index, widget, 0, Qt.AlignBottom)

        widget.show()

    def removeWidget(self, routeKey: str):
        """移除导航部件

        Args:
            routeKey: 导航项的唯一标识
        """
        if routeKey not in self.items:
            return

        if self._currentRouteKey == routeKey:
            self._currentRouteKey = None

        item = self.items.pop(routeKey)

        if item.parentRouteKey is not None:
            self.widget(item.parentRouteKey).removeChild(item.widget)

        if isinstance(item.widget, NavigationTreeWidgetBase):
            for child in item.widget.findChildren(NavigationWidget, options=Qt.FindChildrenRecursively):
                key = child.property('routeKey')
                if key is None:
                    continue

                self.items.pop(key)
                child.deleteLater()
                self.history.remove(key)

        item.widget.deleteLater()
        self.history.remove(routeKey)

    def setMenuButtonVisible(self, isVisible: bool):
        """设置菜单按钮是否可见

        Args:
            isVisible: 是否可见
        """
        self._isMenuButtonVisible = isVisible
        self.menuButton.setVisible(isVisible)

    def setReturnButtonVisible(self, isVisible: bool):
        """设置返回按钮是否可见

        Args:
            isVisible: 是否可见
        """
        self._isReturnButtonVisible = isVisible
        self.returnButton.setVisible(isVisible)

    def setCollapsible(self, on: bool):
        self._isCollapsible = on
        if not on and self.displayMode != NavigationDisplayMode.EXPAND:
            self.expand(False)

    def setExpandWidth(self, width: int):
        """设置导航面板的展开宽度

        Args:
            width: 展开宽度
        """
        if width <= 42:
            return

        self.expandWidth = width
        NavigationWidget.EXPAND_WIDTH = width - 10

    def setMinimumExpandWidth(self, width: int):
        """设置允许面板展开的最小窗口宽度

        Args:
            width: 最小窗口宽度
        """
        self.minimumExpandWidth = width

    def setAcrylicEnabled(self, isEnabled: bool):
        if isEnabled == self.isAcrylicEnabled():
            return

        self._isAcrylicEnabled = isEnabled
        self.setProperty("transparent", self._canDrawAcrylic())
        self.setStyle(QApplication.style())
        self.update()

    def isAcrylicEnabled(self):
        """判断是否启用了亚克力效果

        Returns:
            是否启用亚克力效果
        """
        return self._isAcrylicEnabled

    def expand(self, useAni=True):
        """展开导航面板

        Args:
            useAni: 是否使用动画
        """
        self._stopIndicatorAnimation()
        self._setWidgetCompacted(False)
        self._restoreTreeExpandState(useAni)
        self.expandAni.setProperty('expand', True)
        self.menuButton.setToolTip(self.tr('Close Navigation'))

        # 根据窗口宽度判断显示模式.
        # https://learn.microsoft.com/en-us/windows/apps/design/controls/navigationview#default
        expandWidth = self.minimumExpandWidth + self.expandWidth - 322
        if (self.window().width() >= expandWidth and not self.isMinimalEnabled) or not self._isCollapsible:
            self.displayMode = NavigationDisplayMode.EXPAND
        else:
            self.setProperty('menu', True)
            self.setStyle(QApplication.style())
            self.displayMode = NavigationDisplayMode.MENU

            # 捕获亚克力背景图像.
            if self._canDrawAcrylic():
                self._ensureAcrylicBrush().grabImage(
                    QRect(self.mapToGlobal(QPoint()), QSize(self.expandWidth, self.height())))

            if not self._parent.isWindow():
                pos = self.parent().pos()
                self.setParent(self.window())
                self.move(pos)

            self.show()

        if useAni:
            self.displayModeChanged.emit(self.displayMode)
            self.expandAni.setStartValue(
                QRect(self.pos(), QSize(48, self.height())))
            self.expandAni.setEndValue(
                QRect(self.pos(), QSize(self.expandWidth, self.height())))
            self.expandAni.start()
        else:
            self.resize(self.expandWidth, self.height())
            self._onExpandAniFinished()

    def collapse(self):
        """折叠导航面板"""
        # 如果当前选中项不是根节点, 则停止指示器动画.
        if self.currentItem() and self.currentItem().property('parentRouteKey'):
            self._stopIndicatorAnimation()

        if self.expandAni.state() == QPropertyAnimation.Running:
            return

        for item in self.items.values():
            w = item.widget
            if isinstance(w, NavigationTreeWidgetBase) and w.isRoot():
                w.saveExpandState()
                w.setExpanded(False)

        self.expandAni.setStartValue(
            QRect(self.pos(), QSize(self.width(), self.height())))
        self.expandAni.setEndValue(
            QRect(self.pos(), QSize(48, self.height())))
        self.expandAni.setProperty('expand', False)
        self.expandAni.start()

        self.menuButton.setToolTip(self.tr('Open Navigation'))

    def _stopIndicatorAnimation(self):
        self.indicator.stopAnimation()
        self._onIndicatorAniFinished()

    def _restoreTreeExpandState(self, useAni=True):
        for item in self.items.values():
            w = item.widget
            if isinstance(w, NavigationTreeWidgetBase) and w.isRoot():
                w.restoreExpandState(useAni)

    def toggle(self):
        """切换导航面板的展开状态"""
        if self.displayMode in [NavigationDisplayMode.COMPACT, NavigationDisplayMode.MINIMAL]:
            self.expand()
        else:
            self.collapse()

    def setCurrentItem(self, routeKey: str):
        """设置当前选中项

        Args:
            routeKey: 导航项的唯一标识
        """
        if routeKey not in self.items or routeKey == self._currentRouteKey:
            return

        prevItem = self.currentItem()
        self._currentRouteKey = routeKey

        # 查找需要参与指示器动画的目标项.
        newItem = self.currentItem()
        newIndicatorItem = self._findIndicatorItem(newItem)
        prevIndicatorItem = self._findIndicatorItem(prevItem)

        # 如果未启用指示器动画, 或无法取得有效的前后项, 则直接更新选中状态.
        if not (self.isIndicatorAnimationEnabled() and prevItem and prevIndicatorItem and newIndicatorItem):
            for k, item in self.items.items():
                item.widget.setSelected(k == routeKey)

            return

        # 计算动画的起始和结束几何区域.
        preIndicatorRect = self._getIndicatorRect(prevIndicatorItem)
        newIndicatorRect = self._getIndicatorRect(newIndicatorItem)

        # 开始动画
        prevItem.setSelected(False)
        prevIndicatorItem.setSelected(False)
        newIndicatorItem.setAboutSelected(True)
        self.indicator.setIndicatorColor(newItem.lightIndicatorColor, newItem.darkIndicatorColor)
        self.indicator.startAnimation(preIndicatorRect, newIndicatorRect)

    def currentItem(self):
        return self.widget(self._currentRouteKey) if self._currentRouteKey else None

    def _findIndicatorItem(self, item: NavigationWidget):
        parent = item
        while parent:
            if isinstance(parent, NavigationWidget) and parent.isVisible():
                break

            parent = parent.parent()

        return parent

    def _getIndicatorRect(self, item: NavigationWidget):
        if not item:
            return QRect()

        pos = item.mapTo(self, QPoint(0, 0))
        rect = item.indicatorRect()
        return rect.translated(pos)

    def _onIndicatorAniFinished(self):
        item = self.currentItem()
        if not item:
            return

        item.setSelected(True)
        
        indicatorItem = self._findIndicatorItem(item)
        if indicatorItem:
            indicatorItem.setAboutSelected(False)

        self.indicator.hide()

    def _onWidgetClicked(self):
        widget = self.sender()  # type: NavigationWidget
        if not widget.isSelectable:
            return self._showFlyoutNavigationMenu(widget)

        self.setCurrentItem(widget.property('routeKey'))

        isLeaf = not isinstance(widget, NavigationTreeWidgetBase) or widget.isLeaf()
        if self.displayMode == NavigationDisplayMode.MENU and isLeaf:
            self.collapse()
        elif self.isCollapsed():
            self._showFlyoutNavigationMenu(widget)

    def _showFlyoutNavigationMenu(self, widget: NavigationTreeWidget):
        """显示导航浮出菜单

        Args:
            widget: 导航树部件
        """
        if not (self.isCollapsed() and isinstance(widget, NavigationTreeWidget)):
            return

        if not widget.isRoot() or widget.isLeaf():
            return

        from ..widgets.flyout import Flyout, FlyoutAnimationType, FlyoutViewBase, SlideRightFlyoutAnimationManager

        layout = QHBoxLayout()

        if self._canDrawAcrylic():
            from ..material.acrylic_flyout import AcrylicFlyout, AcrylicFlyoutViewBase

            view = AcrylicFlyoutViewBase()
            view.setLayout(layout)
            flyout = AcrylicFlyout(view, self.window())
        else:
            view = FlyoutViewBase()
            view.setLayout(layout)
            flyout = Flyout(view, self.window())

        # 将导航菜单添加到浮出层.
        menu = NavigationFlyoutMenu(widget, view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(menu)

        # 执行浮出层动画.
        flyout.resize(flyout.sizeHint())
        pos = SlideRightFlyoutAnimationManager(flyout).position(widget)
        flyout.exec(pos, FlyoutAnimationType.SLIDE_RIGHT)

        menu.expanded.connect(lambda: self._adjustFlyoutMenuSize(flyout, widget, menu))

    def _adjustFlyoutMenuSize(self, flyout, widget: NavigationTreeWidget, menu: NavigationFlyoutMenu):
        flyout.view.setFixedSize(menu.size())
        flyout.setFixedSize(flyout.layout().sizeHint())

        manager = flyout.aniManager
        pos = manager.position(widget)

        rect = self.window().geometry()
        w, h = flyout.sizeHint().width() + 5, flyout.sizeHint().height()
        x = max(rect.left(), min(pos.x(), rect.right() - w))
        y = max(rect.top() + 42, min(pos.y() - 4, rect.bottom() - h + 5))
        flyout.move(x, y)

    def isCollapsed(self):
        return self.displayMode == NavigationDisplayMode.COMPACT

    def eventFilter(self, obj, e: QEvent):
        if obj is not self.window() or not self._isCollapsible:
            return super().eventFilter(obj, e)

        if e.type() == QEvent.MouseButtonRelease:
            if not self.geometry().contains(e.pos()) and self.displayMode == NavigationDisplayMode.MENU:
                self.collapse()
        elif e.type() == QEvent.Resize:
            w = QResizeEvent(e).size().width()
            if w < self.minimumExpandWidth and self.displayMode == NavigationDisplayMode.EXPAND:
                self.collapse()
            elif w >= self.minimumExpandWidth and self.displayMode == NavigationDisplayMode.COMPACT and \
                    not self._isMenuButtonVisible:
                self.expand()

        return super().eventFilter(obj, e)

    def _onExpandAniFinished(self):
        if not self.expandAni.property('expand'):
            if self.isMinimalEnabled:
                self.displayMode = NavigationDisplayMode.MINIMAL
            else:
                self.displayMode = NavigationDisplayMode.COMPACT

            self.displayModeChanged.emit(self.displayMode)

        if self.displayMode == NavigationDisplayMode.MINIMAL:
            self.hide()
            self.setProperty('menu', False)
            self.setStyle(QApplication.style())
        elif self.displayMode == NavigationDisplayMode.COMPACT:
            self.setProperty('menu', False)
            self.setStyle(QApplication.style())

            self._setWidgetCompacted(True)

            if self.isUpdateIndicatorPosOnCollapseFinished():
                self._stopIndicatorAnimation()

            if not self._parent.isWindow():
                self.setParent(self._parent)
                self.move(0, 0)
                self.show()

    def _setWidgetCompacted(self, isCompacted: bool):
        """设置导航部件是否为紧凑模式

        Args:
            isCompacted: 是否为紧凑模式
        """
        for item in self.findChildren(NavigationWidget):
            item.setCompacted(isCompacted)

    def layoutMinHeight(self):
        th = self.topLayout.minimumSize().height()
        bh = self.bottomLayout.minimumSize().height()
        sh = sum(w.height() for w in self.findChildren(NavigationSeparator))
        spacing = self.topLayout.count() * self.topLayout.spacing()
        spacing += self.bottomLayout.count() * self.bottomLayout.spacing()
        return 36 + th + bh + sh + spacing

    def _canDrawAcrylic(self):
        return self.isAcrylicEnabled() and self._ensureAcrylicBrush().isAvailable()

    def paintEvent(self, e):
        if not self._canDrawAcrylic() or self.displayMode != NavigationDisplayMode.MENU:
            return super().paintEvent(e)

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRoundedRect(0, 1, self.width() - 1, self.height() - 1, 7, 7)
        path.addRect(0, 1, 8, self.height() - 1)
        brush = self._ensureAcrylicBrush()
        brush.setClipPath(path)

        self._updateAcrylicColor()
        brush.paint()

        super().paintEvent(e)



class NavigationItemLayout(QVBoxLayout):
    """专为导航项设计的垂直布局管理器，负责自动调整各导航按钮的间距、边距以及尺寸策略。可与 NavigationPanel 协同工作，确保在面板展开或最小化切换时保持一致的视觉排列"""

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        for i in range(self.count()):
            item = self.itemAt(i)
            if isinstance(item.widget(), NavigationSeparator):
                geo = item.geometry()
                item.widget().setGeometry(0, geo.y(), geo.width(), geo.height())