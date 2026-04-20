# coding: utf-8
"""导航界面组件

该模块提供 NavigationInterface 类及相关辅助接口，用于构建侧栏导航体系
适用于需要多页面管理与层级切换的桌面应用，支持导航项分组、面板折叠与 Acrylic 材质效果
"""

from typing import Union

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QResizeEvent, QIcon, QPixmap
from PySide6.QtWidgets import QWidget

from .navigation_types import NavigationItemPosition, NavigationDisplayMode
from .navigation_widget import NavigationTreeWidget, NavigationUserCard, NavigationWidget
from ...common.style_sheet import FluentStyleSheet
from ...common.icon import FluentIconBase


class NavigationInterface(QWidget):
    """导航界面
    
    提供侧栏导航功能，管理导航项的添加、移除与页面切换逻辑
    作为主窗口的核心导航容器，适用于具有多模块或分级页面的 Fluent Design 应用
    支持通过 addItem() 注册导航按钮，配合 NavigationItemPosition 实现顶部、滚动区与底部分层固定，并可通过 setCurrentItem() 控制页面显隐
    """

    displayModeChanged = Signal(NavigationDisplayMode)

    def __init__(self, parent=None, showMenuButton=True, showReturnButton=False, collapsible=True):
        """初始化导航界面

        Args:
            parent: 父部件
            showMenuButton: 是否显示菜单按钮
            showReturnButton: 是否显示返回按钮
            collapsible: 导航界面是否可折叠
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
        """添加导航项

        Args:
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            position: 导航项的插入位置
            tooltip: 导航项提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidgetBase

        Returns:
            创建出的 NavigationTreeWidget
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
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidgetBase
        """
        self.insertWidget(-1, routeKey, widget, onClick, position, tooltip, parentRouteKey)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], text: str,
                   onClick=None, selectable=True, position=NavigationItemPosition.TOP, tooltip: str = None,
                   parentRouteKey: str = None) -> NavigationTreeWidget:
        """插入导航项

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            icon: 导航项图标
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            selectable: 导航项是否可选中
            position: 导航项的插入位置
            tooltip: 导航项提示文本
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidgetBase

        Returns:
            创建出的 NavigationTreeWidget
        """
        w = self.panel.insertItem(index, routeKey, icon, text, onClick, selectable, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())
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
            parentRouteKey: 父级导航项的路由键，其对应项应为 NavigationTreeWidgetBase
        """
        self.panel.insertWidget(index, routeKey, widget, onClick, position, tooltip, parentRouteKey)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def addSeparator(self, position=NavigationItemPosition.TOP):
        """添加分隔符

        Args:
            position: 分隔符的插入区域
        """
        self.insertSeparator(-1, position)

    def addItemHeader(self, text: str, position=NavigationItemPosition.TOP):
        """添加导航分组标题

        Args:
            text: 要显示的标题文本
            position: 标题的插入位置

        Returns:
            创建出的 NavigationItemHeader
        """
        return self.panel.addItemHeader(text, position)

    def insertItemHeader(self, index: int, text: str, position=NavigationItemPosition.TOP):
        """插入导航分组标题

        Args:
            index: 插入位置
            text: 要显示的标题文本
            position: 标题的插入位置

        Returns:
            创建出的 NavigationItemHeader
        """
        return self.panel.insertItemHeader(index, text, position)

    def addUserCard(self, routeKey: str, avatar: Union[str, QIcon, FluentIconBase] = None,
                    title: str = '', subtitle: str = '', onClick=None,
                    position=NavigationItemPosition.TOP, aboveMenuButton: bool = False):
        """向导航面板添加用户卡片

        Args:
            routeKey: 用户卡片的唯一标识
            avatar: 头像图像或图标
            title: 用户名或标题文本
            subtitle: 副标题文本，例如邮箱或状态
            onClick: 连接到卡片点击信号的槽函数
            position: 卡片的插入位置
            aboveMenuButton: 是否将卡片放在菜单按钮上方

        Returns:
            创建出的 NavigationUserCard
        """
        card = NavigationUserCard(self)

        if avatar:
            if isinstance(avatar, FluentIconBase):
                card.setAvatarIcon(avatar)
            else:
                card.setAvatar(avatar)

        card.setTitle(title)
        card.setSubtitle(subtitle)

        # 如果需要放在菜单按钮上方, 则计算插入位置.
        index = -1
        if aboveMenuButton and position == NavigationItemPosition.TOP:
            # 在顶部布局中查找菜单按钮的位置.
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
        """插入分隔符

        Args:
            index: 插入位置
            position: 分隔符的插入区域
        """
        self.panel.insertSeparator(index, position)
        self.setMinimumHeight(self.panel.layoutMinHeight())

    def removeWidget(self, routeKey: str):
        """移除导航部件

        Args:
            routeKey: 导航项的唯一标识
        """
        self.panel.removeWidget(routeKey)

    def setCurrentItem(self, name: str):
        """设置当前选中项

        Args:
            name: 导航项的唯一标识
        """
        self.panel.setCurrentItem(name)

    def expand(self, useAni=True):
        """展开导航面板

        Args:
            useAni: 是否使用动画
        """
        self.panel.expand(useAni)

    def toggle(self):
        """切换导航面板的展开状态"""
        self.panel.toggle()

    def setExpandWidth(self, width: int):
        """设置导航面板的展开宽度上限

        Args:
            width: 面板展开宽度
        """
        self.panel.setExpandWidth(width)

    def setMinimumExpandWidth(self, width: int):
        """设置允许面板展开的最小窗口宽度

        Args:
            width: 最小窗口宽度
        """
        self.panel.setMinimumExpandWidth(width)

    def setMenuButtonVisible(self, isVisible: bool):
        """设置菜单按钮是否可见

        Args:
            isVisible: 是否可见
        """
        self.panel.setMenuButtonVisible(isVisible)

    def setReturnButtonVisible(self, isVisible: bool):
        """设置返回按钮是否可见

        Args:
            isVisible: 是否可见
        """
        self.panel.setReturnButtonVisible(isVisible)

    def setCollapsible(self, collapsible: bool):
        """设置导航界面是否可折叠

        Args:
            collapsible: 是否可折叠
        """
        self.panel.setCollapsible(collapsible)

    def isAcrylicEnabled(self):
        """判断是否启用了亚克力背景效果

        Returns:
            是否启用亚克力背景效果
        """
        return self.panel.isAcrylicEnabled()

    def setAcrylicEnabled(self, isEnabled: bool):
        """设置是否启用亚克力背景效果

        Args:
            isEnabled: 是否启用
        """
        self.panel.setAcrylicEnabled(isEnabled)

    def isIndicatorAnimationEnabled(self):
        """判断是否启用了指示器滑动动画

        Returns:
            是否启用指示器滑动动画
        """
        return self.panel.isIndicatorAnimationEnabled()

    def setIndicatorAnimationEnabled(self, isEnabled: bool):
        """设置是否启用指示器滑动动画

        Args:
            isEnabled: 是否启用
        """
        self.panel.setIndicatorAnimationEnabled(isEnabled)

    def isUpdateIndicatorPosOnCollapseFinished(self):
        """判断折叠动画结束后是否更新指示器位置

        Returns:
            是否更新指示器位置
        """
        return self.panel.isUpdateIndicatorPosOnCollapseFinished()

    def setUpdateIndicatorPosOnCollapseFinished(self, update: bool):
        """设置折叠动画结束后是否更新指示器位置

        Args:
            update: 是否更新指示器位置
        """
        self.panel.setUpdateIndicatorPosOnCollapseFinished(update)

    def widget(self, routeKey: str):
        """获取导航部件

        Args:
            routeKey: 导航项的唯一标识

        Returns:
            对应的导航部件
        """
        return self.panel.widget(routeKey)

    def eventFilter(self, obj, e: QEvent):
        """事件过滤器

        Args:
            obj: 被监视的对象
            e: 事件对象

        Returns:
            是否拦截该事件
        """
        if obj is not self.panel or e.type() != QEvent.Resize:
            return super().eventFilter(obj, e)

        if self.panel.displayMode != NavigationDisplayMode.MENU:
            event = QResizeEvent(e)
            if event.oldSize().width() != event.size().width():
                self.setFixedWidth(event.size().width())

        return super().eventFilter(obj, e)

    def resizeEvent(self, e: QResizeEvent):
        """处理窗口调整大小事件

        Args:
            e: 调整大小事件
        """
        if e.oldSize().height() != self.height():
            self.panel.setFixedHeight(self.height())