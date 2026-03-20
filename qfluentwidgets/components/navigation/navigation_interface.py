# coding: utf-8
from typing import Union

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QResizeEvent, QIcon, QPixmap
from PySide6.QtWidgets import QWidget

from .navigation_types import NavigationItemPosition, NavigationDisplayMode
from .navigation_widget import NavigationTreeWidget, NavigationUserCard, NavigationWidget
from ...common.style_sheet import FluentStyleSheet
from ...common.icon import FluentIconBase


class NavigationInterface(QWidget):
    """ 导航界面 """

    displayModeChanged = Signal(NavigationDisplayMode)

    def __init__(self, parent=None, showMenuButton=True, showReturnButton=False, collapsible=True):
        """
        参数
        ----------
        parent: 部件
            父部件 部件

        showMenuButton: bool
            是否 到 显示 菜单 按钮

        showReturnButton: bool
            是否 到 显示 返回 按钮

        collapsible: bool
            Is 导航界面 collapsible
        """
        super().__init__(parent=parent)
        from .navigation_panel import NavigationPanel

        self.panel = NavigationPanel(self)
        self.panel.setMenuButtonVisible(showMenuButton and collapsible)
        self.panel.setReturnButtonVisible(showReturnButton)
        self.panel.setCollapsible(collapsible)
        self.panel.installEventFilter(self)
        self.panel.displayModeChanged.connect(self.displayModeChanged)

        self.resize(48, self.height())
        self.setMinimumWidth(48)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def addItem(self, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str, onClick=None,
                selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None,
                parentRouteKey: str = None) -> NavigationTreeWidget:
        """ 添加 navigation 项

        参数
        ----------
        routKey: str
            unique name 的 项

        icon: str | QIcon | FluentIconBase
            图标 的 navigation 项

        text: str
            文本 的 navigation 项

        onClick: callable
            槽函数 connected 到 项 clicked 信号

        selectable: bool
            是否 项 is selectable

        position: NavigationItemPosition
            where 按钮 is added

        tooltip: str
            tooltip 的 项

        parentRouteKey: str
            路由键 的 父部件 项, 父部件 项 should be `NavigationTreeWidgetBase`
        """
        return self.insertItem(-1, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)

    def addWidget(self, routeKey: str, widget: NavigationWidget, onClick=None, position=NavigationItemPosition.TOP,
                  tooltip: str = None, parentRouteKey: str = None):
        """ 添加 自定义 部件

        参数
        ----------
        routKey: str
            unique name 的 项

        widget: NavigationWidget
            自定义 部件 到 be added

        onClick: callable
            槽函数 connected 到 项 clicked 信号

        position: NavigationItemPosition
            where 部件 is added

        tooltip: str
            tooltip 的 部件

        parentRouteKey: str
            路由键 的 父部件 项, 父部件 项 should be `NavigationTreeWidgetBase`
        """
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip, parentRouteKey)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str,
                   onClick=None, selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None,
                   parentRouteKey: str = None) -> NavigationTreeWidget:
        """ 插入 navigation 项

        参数
        ----------
        index: int
            插入 位置

        routKey: str
            unique name 的 项

        icon: str | QIcon | FluentIconBase
            图标 的 navigation 项

        text: str
            文本 的 navigation 项

        onClick: callable
            槽函数 connected 到 项 clicked 信号

        selectable: bool
            是否 项 is selectable

        position: NavigationItemPosition
            where 项 is added

        tooltip: str
            tooltip 的 项

        parentRouteKey: str
            路由键 的 父部件 项, 父部件 项 should be `NavigationTreeWidgetBase`
        """
        w = self.panel.insertItem(index, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())
        return w

    def insertWidget(self, index: int, routeKey: str, widget: NavigationWidget, onClick=None,
                     position=NavigationItemPosition.TOP, tooltip: str = None, parentRouteKey: str = None):
        """ 插入 自定义 部件

        参数
        ----------
        index: int
            插入 位置

        routKey: str
            unique name 的 项

        widget: NavigationWidget
            自定义 部件 到 be added

        onClick: callable
            槽函数 connected 到 项 clicked 信号

        position: NavigationItemPosition
            where 部件 is added

        tooltip: str
            tooltip 的 部件

        parentRouteKey: str
            路由键 的 父部件 项, 父部件 项 should be `NavigationTreeWidgetBase`
        """
        self.panel.insertWidget(index, routeKey, widget, onClick, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def addSeparator(self, position=NavigationItemPosition.TOP):
        """ 添加 分隔符

        参数
        ----------
        position: NavigationPostion
            where 到 添加 分隔符
        """
        self.insertSeparator(-1, position)

    def addItemHeader(self, text: str, position=NavigationItemPosition.TOP):
        """ 添加 项 header 用于 grouping navigation 项

        参数
        ----------
        text: str
            header 文本 到 display

        position: NavigationItemPosition
            where header is added

        返回
        -------
        NavigationItemHeader
            created header 部件
        """
        return self.panel.addItemHeader(text, position)

    def insertItemHeader(self, index: int, text: str, position=NavigationItemPosition.TOP):
        """ 插入 项 header 用于 grouping navigation 项

        参数
        ----------
        index: int
            插入 位置

        text: str
            header 文本 到 display

        position: NavigationItemPosition
            where header is added

        返回
        -------
        NavigationItemHeader
            created header 部件
        """
        return self.panel.insertItemHeader(index, text, position)

    def addUserCard(self, routeKey: str, avatar: Union[str, QIcon, FluentIconBase] = None,
                    title: str = '', subtitle: str = '', onClick=None,
                    position=NavigationItemPosition.TOP, aboveMenuButton: bool = False):
        """ 将user card添加到navigation 面板

        参数
        ----------
        routeKey: str
            unique name 的 user card

        avatar: str | QIcon | FluentIconBase
            avatar 图像 或 图标

        title: str
            user name 或 标题 文本

        subtitle: str
            subtitle 文本 (e.g., email, 状态)

        onClick: callable
            槽函数 connected 到 card clicked 信号

        position: NavigationItemPosition
            where card is added

        aboveMenuButton: bool
            是否 到 place card above 菜单 按钮 (expand/collapse 按钮)

        返回
        -------
        NavigationUserCard
            created user card 部件
        """
        card = NavigationUserCard(self)

        if avatar:
            if isinstance(avatar, FluentIconBase):
                card.setAvatarIcon(avatar)
            else:
                card.setAvatar(avatar)

        card.setTitle(title)
        card.setSubtitle(subtitle)

        # 计算插入 索引 如果 placing above 菜单 按钮
        index = -1
        if aboveMenuButton and position == NavigationItemPosition.TOP:
            # find 菜单 按钮 索引 中的 top 布局
            layout = self.panel.topLayout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() == self.panel.menuButton:
                    index = i
                    break

        if index >= 0:
            self.panel.insertWidget(index, routeKey, card, onClick, position)
        else:
            self.addWidget(routeKey, card, onClick, position)

        return card

    def insertSeparator(self, index: int, position=NavigationItemPosition.TOP):
        """ 添加 分隔符

        参数
        ----------
        index: int
            插入 位置

        position: NavigationPostion
            where 到 添加 分隔符
        """
        self.panel.insertSeparator(index, position)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def removeWidget(self, routeKey: str):
        """ 移除 部件

        参数
        ----------
        routKey: str
            unique name 的 项
        """
        self.panel.removeWidget(routeKey)

    def setCurrentItem(self, name: str):
        """ 设置 当前 选中项

        参数
        ----------
        name: str
            unique name 的 项
        """
        self.panel.setCurrentItem(name)

    def expand(self, useAni=True):
        """ 展开导航面板 """
        self.panel.expand(useAni)

    def toggle(self):
        """ 切换导航面板 """
        self.panel.toggle()

    def setExpandWidth(self, width: int):
        """ 设置 maximum 宽度 """
        self.panel.setExpandWidth(width)

    def setMinimumExpandWidth(self, width: int):
        """ 设置 最小窗口宽度 that allows 面板 到 be expanded """
        self.panel.setMinimumExpandWidth(width)

    def setMenuButtonVisible(self, isVisible: bool):
        """ 设置 是否 菜单 按钮 is 可见 """
        self.panel.setMenuButtonVisible(isVisible)

    def setReturnButtonVisible(self, isVisible: bool):
        """ 设置 是否 返回 按钮 is 可见 """
        self.panel.setReturnButtonVisible(isVisible)

    def setCollapsible(self, collapsible: bool):
        self.panel.setCollapsible(collapsible)

    def isAcrylicEnabled(self):
        return self.panel.isAcrylicEnabled()

    def setAcrylicEnabled(self, isEnabled: bool):
        """ 设置 是否 亚克力 背景 effect is 已启用 """
        self.panel.setAcrylicEnabled(isEnabled)

    def isIndicatorAnimationEnabled(self):
        return self.panel.isIndicatorAnimationEnabled()

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        """ 设置 是否 指示器 sliding 动画 is 已启用 """
        self.panel.setIndicatorAnimationEnabled(isEnabled)

    def isUpdateIndicatorPosOnCollapseFinished(self):
        return self.panel.isUpdateIndicatorPosOnCollapseFinished()

    def setUpdateIndicatorPosOnCollapseFinished(self, update: bool):
        """ 设置 是否 到 更新 指示器 位置 当 collapese finished """
        self.panel.setUpdateIndicatorPosOnCollapseFinished(update)

    def widget(self, routeKey: str):
        return self.panel.widget(routeKey)

    def eventFilter(self, obj, e: QEvent):
        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        if self.panel.displayMode != NavigationDisplayMode.MENU:
            event = QResizeEvent(e)
            if event.oldSize().width() != event.size().width():
                self.setFixedWidth(event.size().width())

        return super().eventFilter(obj, e)

    def resizeEvent(self, e: QResizeEvent):
        if e.oldSize().height() != self.height():
            self.panel.setFixedHeight(self.height())
