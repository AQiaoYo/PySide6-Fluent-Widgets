# coding: utf-8
"""菜单组件模块，提供圆角菜单、可选中菜单、系统托盘菜单及各类右键菜单实现
包含菜单动画管理器、菜单项委托和子菜单部件，用于构建 Fluent Design 风格的完整菜单体系
"""
from enum import Enum
from typing import List, Union

from qframelesswindow import WindowEffect
from PySide6.QtCore import (QEasingCurve, QEvent, QPropertyAnimation, QObject, QModelIndex,
                          Qt, QSize, QRectF, Signal, QPoint, QTimer, QObject, QParallelAnimationGroup, QRect)
from PySide6.QtGui import (QAction, QIcon, QColor, QPainter, QPen, QPixmap, QRegion, QCursor, QTextCursor, QHoverEvent,
                           QFontMetrics, QKeySequence)
from PySide6.QtWidgets import (QApplication, QMenu, QProxyStyle, QStyle, QStyleFactory,
                               QGraphicsDropShadowEffect, QListWidget, QWidget, QHBoxLayout,
                               QListWidgetItem, QLineEdit, QTextEdit, QStyledItemDelegate, QStyleOptionViewItem, QLabel)

from ...common.icon import FluentIcon as FIF
from ...common.icon import FluentIconEngine, Action, FluentIconBase, Icon
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.screen import getCurrentScreenGeometry
from ...common.font import getFont, fontStyleSheet
from ...common.config import isDarkTheme
from .scroll_bar import SmoothScrollDelegate
from .tool_tip import ItemViewToolTipDelegate, ItemViewToolTipType


class CustomMenuStyle(QProxyStyle):
    """自定义菜单样式
    继承自 QProxyStyle，用于自定义菜单绘制逻辑，调整菜单项间距、图标尺寸和文本对齐方式
    适用于需要微调菜单视觉表现但不想完全重绘的场景
    """

    def __init__(self, iconSize=14):
        """
        Args:
            iconSize: 图标大小
        """
        super().__init__()
        self.iconSize = iconSize

    def pixelMetric(self, metric, option, widget):
        if metric == QStyle.PM_SmallIconSize:
            return self.iconSize

        return super().pixelMetric(metric, option, widget)


class DWMMenu(QMenu):
    """使用 DWM 阴影的菜单
    基于 Windows DWM（Desktop Window Manager）实现系统级阴影效果，提升菜单视觉层级
    通常作为启用系统阴影的菜单基类使用，仅在 Windows 平台生效
    """

    def __init__(self, title="", parent=None):
        """初始化 DWM 阴影菜单
        
        Args:
            title: 菜单标题文本，若为 None 则不显示标题栏
            parent: 父窗口或部件，决定菜单的层级关系
        """
        super().__init__(title, parent)
        self.windowEffect = WindowEffect(self)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.Popup | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyle(CustomMenuStyle())
        FluentStyleSheet.MENU.apply(self)

    def event(self, e: QEvent):
        if e.type() == QEvent.WinIdChange:
            self.windowEffect.addMenuShadowEffect(self.winId())
        return QMenu.event(self, e)


class MenuAnimationType(Enum):
    """菜单动画类型
    定义菜单弹出时使用的动画效果枚举，包括无动画、下拉、上拉、淡入下拉和淡入上拉
    通过 RoundMenu.setAnimationType() 设置，控制菜单显隐的过渡效果
    """

    NONE = 0
    DROP_DOWN = 1
    PULL_UP = 2
    FADE_IN_DROP_DOWN = 3
    FADE_IN_PULL_UP = 4



class SubMenuItemWidget(QWidget):
    """子菜单项部件
    用于在菜单项右侧绘制向右箭头，标识该项包含子菜单，支持悬停自动弹出子菜单
    通常由 RoundMenu 内部创建，无需手动实例化
    """

    showMenuSig = Signal(QListWidgetItem)

    def __init__(self, menu, item, parent=None):
        """
        Args:
            menu: 子菜单
            item: 菜单项
            parent: 父部件
        """
        super().__init__(parent)
        self.menu = menu
        self.item = item

    def enterEvent(self, e):
        super().enterEvent(e)
        self.showMenuSig.emit(self.item)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制向右箭头.
        FIF.CHEVRON_RIGHT.render(painter, QRectF(
            self.width()-10, self.height()/2-9/2, 9, 9))


class MenuItemDelegate(QStyledItemDelegate):
    """菜单项委托
    负责菜单列表中单个选项的绘制与布局，包括文本、图标、快捷键和分隔符的渲染
    可通过继承此类并重写 paint 方法来自定义菜单项外观
    """

    def __init__(self, parent=None):
        """初始化菜单项委托
        
        Args:
            parent: 父对象，通常为关联的列表部件
        """
        super().__init__(parent)
        self.tooltipDelegate = None

    def _isSeparator(self, index: QModelIndex):
        return index.model().data(index, Qt.DecorationRole) == "seperator"

    def paint(self, painter, option, index):
        if not self._isSeparator(index):
            return super().paint(painter, option, index)

        # 绘制分隔线.
        painter.save()

        c = 0 if not isDarkTheme() else 255
        pen = QPen(QColor(c, c, c, 25), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        rect = option.rect
        painter.drawLine(0, rect.y() + 4, rect.width() + 12, rect.y() + 4)

        painter.restore()

    def helpEvent(self, event, view, option, index):
        if not self.tooltipDelegate:
            self.tooltipDelegate = ItemViewToolTipDelegate(view, 100, ItemViewToolTipType.LIST)

        return self.tooltipDelegate.helpEvent(event, view, option, index)


class ShortcutMenuItemDelegate(MenuItemDelegate):
    """带快捷键文本的菜单项委托
    在菜单项右侧预留区域绘制 QAction 的快捷键文本，支持调整快捷键与文本的间距
    适用于需要展示键盘快捷方式的菜单场景
    """

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        if self._isSeparator(index):
            return

        # 绘制快捷键文本.
        action = index.data(Qt.UserRole)  # type: QAction
        if not isinstance(action, QAction) or action.shortcut().isEmpty():
            return

        painter.save()

        if not option.state & QStyle.State_Enabled:
            painter.setOpacity(0.5 if isDarkTheme() else 0.6)

        font = getFont(12)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 200) if isDarkTheme() else QColor(0, 0, 0, 153))

        fm = QFontMetrics(font)
        shortcut = action.shortcut().toString(QKeySequence.NativeText)

        sw = fm.horizontalAdvance(shortcut)
        painter.translate(option.rect.width()-sw-20, 0)

        rect = QRectF(0, option.rect.y(), sw, option.rect.height())
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, shortcut)

        painter.restore()


class MenuActionListWidget(QListWidget):
    """菜单动作列表部件
    内部使用 QListWidget 承载 QAction，负责动作与列表项的映射、尺寸计算和事件转发
    作为 RoundMenu 的核心内容区域，管理所有菜单项的排布与交互
    """

    def __init__(self, parent=None):
        """初始化菜单动作列表部件
        
        Args:
            parent: 父菜单实例，用于接收动作触发事件和尺寸调整通知
        """
        super().__init__(parent)
        self._itemHeight = 28
        self._maxVisibleItems = -1  # 根据屏幕尺寸调整可见项数量.

        self.setViewportMargins(0, 6, 0, 6)
        self.setTextElideMode(Qt.ElideNone)
        self.setDragEnabled(False)
        self.setMouseTracking(True)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setIconSize(QSize(14, 14))
        self.setItemDelegate(ShortcutMenuItemDelegate(self))

        self.scrollDelegate = SmoothScrollDelegate(self)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def insertItem(self, row, item):
        """在指定行插入菜单项"""
        super().insertItem(row, item)
        self.adjustSize()

    def addItem(self, item):
        """在列表末尾添加菜单项"""
        super().addItem(item)
        self.adjustSize()

    def takeItem(self, row):
        """从列表中删除指定项"""
        item = super().takeItem(row)
        self.adjustSize()
        return item

    def adjustSize(self, pos=None, aniType=MenuAnimationType.NONE):
        size = QSize()
        for i in range(self.count()):
            s = self.item(i).sizeHint()
            size.setWidth(max(s.width(), size.width(), 1))
            size.setHeight(max(1, size.height() + s.height()))

        # 调整视口高度.
        w, h = MenuAnimationManager.make(self, aniType).availableViewSize(pos)

        # fixes https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/844
        # self.viewport().adjustSize()

        # 调整列表部件高度.
        m = self.viewportMargins()
        size += QSize(m.left()+m.right()+2, m.top()+m.bottom())
        size.setHeight(min(h, size.height()+3))
        size.setWidth(max(min(w, size.width()), self.minimumWidth()))

        if self.maxVisibleItems() > 0:
            size.setHeight(min(
                size.height(), self.maxVisibleItems() * self._itemHeight + m.top()+m.bottom() + 3))

        self.setFixedSize(size)

    def setItemHeight(self, height: int):
        """设置项的高度"""
        if height == self._itemHeight:
            return

        for i in range(self.count()):
            item = self.item(i)
            if not self.itemWidget(item):
                item.setSizeHint(QSize(item.sizeHint().width(), height))

        self._itemHeight = height
        self.adjustSize()

    def setMaxVisibleItems(self, num: int):
        """设置最大可见项数"""
        self._maxVisibleItems = num
        self.adjustSize()

    def maxVisibleItems(self):
        return self._maxVisibleItems

    def heightForAnimation(self, pos: QPoint, aniType: MenuAnimationType):
        """返回动画可用高度"""
        ih = self.itemsHeight()
        _, sh = MenuAnimationManager.make(self, aniType).availableViewSize(pos)
        return min(ih, sh)

    def itemsHeight(self):
        """返回所有项的总高度"""
        N = self.count() if self.maxVisibleItems() < 0 else min(self.maxVisibleItems(), self.count())
        h = sum(self.item(i).sizeHint().height() for i in range(N))
        m = self.viewportMargins()
        return h + m.top() + m.bottom()


class RoundMenu(QMenu):
    """圆角菜单
    提供 Fluent Design 风格的圆角弹出菜单，支持图标、快捷键、子菜单和自定义动作
    适用于按钮下拉菜单、右键上下文菜单等常见场景，可配合 MenuAnimationManager 实现弹出动画
    构造函数重载:
        - RoundMenu(parent)
        - RoundMenu(title, parent)
    """

    closedSignal = Signal()

    def __init__(self, title="", parent=None):
        """初始化圆角菜单
        
        Args:
            title: 菜单标题文本，若为 None 则不显示标题栏
            parent: 父窗口或部件，用于定位菜单和内存管理
        """
        super().__init__(parent=parent)
        self.setTitle(title)
        self._icon = QIcon()
        self._actions = []  # type: List[QAction]
        self._subMenus = []

        self.isSubMenu = False
        self.parentMenu = None
        self.menuItem = None
        self.lastHoverItem = None
        self.lastHoverSubMenuItem = None
        self.isHideBySystem = True
        self.itemHeight = 28

        self.hBoxLayout = QHBoxLayout(self)
        self.view = MenuActionListWidget(self)

        self.aniManager = None
        self.timer = QTimer(self)

        self.__initWidgets()

    def __initWidgets(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                            Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # fixes https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/848
        self.setStyle(QStyleFactory.create("fusion"))

        self.timer.setSingleShot(True)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self._onShowMenuTimeOut)

        self.setShadowEffect()
        self.hBoxLayout.addWidget(self.view, 1, Qt.AlignCenter)

        self.hBoxLayout.setContentsMargins(12, 8, 12, 20)
        FluentStyleSheet.MENU.apply(self)

        self.view.itemClicked.connect(self._onItemClicked)
        self.view.itemEntered.connect(self._onItemEntered)

    def setMaxVisibleItems(self, num: int):
        """设置最大可见项数"""
        self.view.setMaxVisibleItems(num)
        self.adjustSize()

    def setItemHeight(self, height):
        """设置菜单项高度"""
        if height == self.itemHeight:
            return

        self.itemHeight = height
        self.view.setItemHeight(height)

    def setShadowEffect(self, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        """为菜单添加阴影效果"""
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def _setParentMenu(self, parent, item):
        self.parentMenu = parent
        self.menuItem = item
        self.isSubMenu = True if parent else False

    def adjustSize(self):
        m = self.layout().contentsMargins()
        w = self.view.width() + m.left() + m.right()
        h = self.view.height() + m.top() + m.bottom()
        self.setFixedSize(w, h)

    def icon(self):
        return self._icon

    def title(self):
        return self._title

    def clear(self):
        """清空所有动作"""
        while self._actions:
            self.removeAction(self._actions[-1])

        while self._subMenus:
            self.removeMenu(self._subMenus[-1])

    def setIcon(self, icon: Union[QIcon, FluentIconBase]):
        """设置菜单的图标"""
        if isinstance(icon, FluentIconBase):
            icon = Icon(icon)

        self._icon = icon

    def setTitle(self, title: str):
        self._title = title
        super().setTitle(title)

    def addAction(self, action: Union[QAction, Action]):
        """向菜单中添加动作

        Args:
            action: 菜单动作
        """
        item = self._createActionItem(action)
        self.view.addItem(item)
        self.adjustSize()

    def addWidget(self, widget: QWidget, selectable=True, onClick=None):
        """向菜单中添加自定义部件

        Args:
            widget: 自定义部件
            selectable: 对应菜单项是否可选中
            onClick: 连接到点击信号的槽函数
        """
        action = QAction()
        action.setProperty('selectable', selectable)

        item = self._createActionItem(action)
        item.setSizeHint(widget.size())

        self.view.addItem(item)
        self.view.setItemWidget(item, widget)

        if not selectable:
            item.setFlags(Qt.NoItemFlags)

        if onClick:
            action.triggered.connect(onClick)

        self.adjustSize()

    def _createActionItem(self, action: QAction, before=None):
        """创建菜单动作项"""
        if not before:
            self._actions.append(action)
            super().addAction(action)
        elif before in self._actions:
            index = self._actions.index(before)
            self._actions.insert(index, action)
            super().insertAction(before, action)
        else:
            raise ValueError('`before` is not in the action list')

        item = QListWidgetItem(self._createItemIcon(action), action.text())
        self._adjustItemText(item, action)

        # 如果动作不可用, 则禁用对应菜单项.
        if not action.isEnabled():
            item.setFlags(Qt.NoItemFlags)
        if action.text() != action.toolTip():
            item.setToolTip(action.toolTip())

        item.setData(Qt.UserRole, action)
        action.setProperty('item', item)
        action.changed.connect(self._onActionChanged)
        return item

    def _hasItemIcon(self):
        return any(not i.icon().isNull() for i in self._actions+self._subMenus)

    def _adjustItemText(self, item: QListWidgetItem, action: QAction):
        """调整菜单项文本宽度"""
        # 为快捷键文本预留一些空间.
        if isinstance(self.view.itemDelegate(), ShortcutMenuItemDelegate):
            sw = self._longestShortcutWidth()
            if sw:
                sw += 22
        else:
            sw = 0

        # 调整菜单项宽度.
        if not self._hasItemIcon():
            item.setText(action.text())
            w = 40 + self.view.fontMetrics().boundingRect(action.text()).width() + sw
        else:
            # 添加一个空格, 以增大图标与文本之间的间距.
            item.setText(" " + action.text())
            space = 4 - self.view.fontMetrics().boundingRect(" ").width()
            w = 60 + self.view.fontMetrics().boundingRect(item.text()).width() + sw + space

        item.setSizeHint(QSize(w, self.itemHeight))
        return w

    def _longestShortcutWidth(self):
        """返回最长快捷键文本的宽度"""
        fm = QFontMetrics(getFont(12))
        return max(fm.horizontalAdvance(a.shortcut().toString(QKeySequence.NativeText)) for a in self.menuActions())

    def _createItemIcon(self, w):
        """创建菜单项图标"""
        hasIcon = self._hasItemIcon()
        icon = QIcon(FluentIconEngine(w.icon()))

        if hasIcon and w.icon().isNull():
            pixmap = QPixmap(self.view.iconSize())
            pixmap.fill(Qt.transparent)
            icon = QIcon(pixmap)
        elif not hasIcon:
            icon = QIcon()

        return icon

    def insertAction(self, before: Union[QAction, Action], action: Union[QAction, Action]):
        """在指定动作前插入动作"""
        if before not in self._actions:
            return

        beforeItem = before.property('item')
        if not beforeItem:
            return

        index = self.view.row(beforeItem)
        item = self._createActionItem(action, before)
        self.view.insertItem(index, item)
        self.adjustSize()

    def addActions(self, actions: List[Union[QAction, Action]]):
        """向菜单中添加多个动作

        Args:
            actions: 菜单动作列表
        """
        for action in actions:
            self.addAction(action)

    def insertActions(self, before: Union[QAction, Action], actions: List[Union[QAction, Action]]):
        """在指定动作前插入多个动作"""
        for action in actions:
            self.insertAction(before, action)

    def removeAction(self, action: Union[QAction, Action]):
        """从菜单中移除动作"""
        if action not in self._actions:
            return

        # 移除动作.
        item = action.property("item")
        self._actions.remove(action)
        action.setProperty('item', None)

        if not item:
            return

        # 移除菜单项.
        self._removeItem(item)
        super().removeAction(action)

    def removeMenu(self, menu):
        """移除子菜单"""
        if menu not in self._subMenus:
            return

        item = menu.menuItem
        self._subMenus.remove(menu)
        self._removeItem(item)

    def setDefaultAction(self, action: Union[QAction, Action]):
        """设置默认动作"""
        if action not in self._actions:
            return

        item = action.property("item")
        if item:
            self.view.setCurrentItem(item)

    def addMenu(self, menu):
        """添加子菜单

        Args:
            menu: 子圆角菜单
        """
        if not isinstance(menu, RoundMenu):
            raise ValueError('`menu` should be an instance of `RoundMenu`.')

        item, w = self._createSubMenuItem(menu)
        self.view.addItem(item)
        self.view.setItemWidget(item, w)
        self.adjustSize()

    def insertMenu(self, before: Union[QAction, Action], menu):
        """在指定动作前插入子菜单"""
        if not isinstance(menu, RoundMenu):
            raise ValueError('`menu` should be an instance of `RoundMenu`.')

        if before not in self._actions:
            raise ValueError('`before` should be in menu action list')

        item, w = self._createSubMenuItem(menu)
        self.view.insertItem(self.view.row(before.property('item')), item)
        self.view.setItemWidget(item, w)
        self.adjustSize()

    def _createSubMenuItem(self, menu):
        self._subMenus.append(menu)

        item = QListWidgetItem(self._createItemIcon(menu), menu.title())
        if not self._hasItemIcon():
            w = 60 + self.view.fontMetrics().boundingRect(menu.title()).width()
        else:
            # 添加一个空格, 以增大图标与文本之间的间距.
            item.setText(" " + item.text())
            w = 72 + self.view.fontMetrics().boundingRect(item.text()).width()

        # 添加子菜单项.
        menu._setParentMenu(self, item)
        item.setSizeHint(QSize(w, self.itemHeight))
        item.setData(Qt.UserRole, menu)
        w = SubMenuItemWidget(menu, item, self)
        w.showMenuSig.connect(self._showSubMenu)
        w.resize(item.sizeHint())

        return item, w

    def _removeItem(self, item):
        self.view.takeItem(self.view.row(item))
        item.setData(Qt.UserRole, None)

        # 删除关联部件.
        widget = self.view.itemWidget(item)
        if widget:
            widget.deleteLater()

    def _showSubMenu(self, item):
        """显示子菜单"""
        self.lastHoverItem = item
        self.lastHoverSubMenuItem = item
        # 延迟 400 毫秒以避免抖动.
        self.timer.stop()
        self.timer.start()

    def _onShowMenuTimeOut(self):
        if self.lastHoverSubMenuItem is None or not self.lastHoverItem is self.lastHoverSubMenuItem:
            return

        w = self.view.itemWidget(self.lastHoverSubMenuItem)

        if w.menu.parentMenu.isHidden():
            return

        itemRect = QRect(w.mapToGlobal(w.rect().topLeft()), w.size())
        x = itemRect.right() + 5
        y = itemRect.y() - 5

        screenRect = getCurrentScreenGeometry()
        subMenuSize = w.menu.sizeHint()
        if (x + subMenuSize.width()) > screenRect.right():
            x = max(itemRect.left() - subMenuSize.width() - 5, screenRect.left())

        if (y + subMenuSize.height()) > screenRect.bottom():
            y = screenRect.bottom() - subMenuSize.height()

        y = max(y, screenRect.top())

        w.menu.exec(QPoint(x, y))

    def addSeparator(self):
        """向菜单中添加分隔符"""
        m = self.view.viewportMargins()
        w = self.view.width()-m.left()-m.right()

        # 将分隔符添加到列表部件中.
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(w, 9))
        self.view.addItem(item)
        item.setData(Qt.DecorationRole, "seperator")
        self.adjustSize()

    def _onItemClicked(self, item):
        action = item.data(Qt.UserRole)  # type: QAction
        if action not in self._actions or not action.isEnabled():
            return

        if self.view.itemWidget(item) and not action.property('selectable'):
            return

        self._hideMenu(False)

        if not self.isSubMenu:
            action.trigger()
            return

        # 关闭父级菜单.
        self._closeParentMenu()
        action.trigger()

    def _closeParentMenu(self):
        menu = self
        while menu:
            menu.close()
            menu = menu.parentMenu

    def _onItemEntered(self, item):
        self.lastHoverItem = item
        if not isinstance(item.data(Qt.UserRole), RoundMenu):
            return

        self._showSubMenu(item)

    def _hideMenu(self, isHideBySystem=False):
        self.isHideBySystem = isHideBySystem
        self.view.clearSelection()
        if self.isSubMenu:
            self.hide()
        else:
            self.close()

    def hideEvent(self, e):
        if self.isHideBySystem and self.isSubMenu:
            self._closeParentMenu()

        self.isHideBySystem = True
        e.accept()

    def closeEvent(self, e):
        e.accept()
        self.closedSignal.emit()
        self.view.clearSelection()

    def menuActions(self):
        return self._actions

    def mousePressEvent(self, e):
        w = self.childAt(e.pos())
        if (w is not self.view) and (not self.view.isAncestorOf(w)):
            self._hideMenu(True)

    def mouseMoveEvent(self, e):
        if not self.isSubMenu:
            return

        # 鼠标移出子菜单项时隐藏子菜单.
        pos = e.globalPos()
        view = self.parentMenu.view

        # 获取菜单项所在区域.
        margin = view.viewportMargins()
        rect = view.visualItemRect(self.menuItem).translated(view.mapToGlobal(QPoint()))
        rect = rect.translated(margin.left(), margin.top()+2)
        if self.parentMenu.geometry().contains(pos) and not rect.contains(pos) and \
                not self.geometry().contains(pos):
            view.clearSelection()
            self._hideMenu(False)

    def _onActionChanged(self):
        """动作变更时更新对应菜单项"""
        action = self.sender()  # type: QAction
        item = action.property('item')  # type: QListWidgetItem
        item.setIcon(self._createItemIcon(action))

        if action.text() != action.toolTip():
            item.setToolTip(action.toolTip())

        self._adjustItemText(item, action)

        if action.isEnabled():
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        else:
            item.setFlags(Qt.NoItemFlags)

        self.view.adjustSize()
        self.adjustSize()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """显示菜单

        Args:
            pos: 弹出位置
            ani: 是否显示弹出动画
            aniType: 菜单动画类型
        """
        #if self.isVisible():
        #    aniType = MenuAnimationType.NONE

        self.aniManager = MenuAnimationManager.make(self, aniType)
        self.aniManager.exec(pos)

        self.show()

        if self.isSubMenu:
            self.menuItem.setSelected(True)

    def exec_(self, pos: QPoint, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        """显示菜单

        Args:
            pos: 弹出位置
            ani: 是否显示弹出动画
            aniType: 菜单动画类型
        """
        self.exec(pos, ani, aniType)

    def adjustPosition(self):
        m = self.layout().contentsMargins()
        rect = getCurrentScreenGeometry()
        w, h = self.layout().sizeHint().width() + 5, self.layout().sizeHint().height()

        x = min(self.x() - m.left(), rect.right() - w)
        y = self.y()
        if y > rect.bottom() - h:
            y = self.y() - h + m.bottom()

        self.move(x, y)

    def paintEvent(self, e):
        pass


class MenuAnimationManager(QObject):
    """菜单动画管理器
    抽象基类，负责计算菜单弹出位置和执行显示/隐藏动画序列
    子类需实现 availableGeometry、moveTo 和 play 方法以提供具体的动画行为
    """

    managers = {}

    def __init__(self, menu: RoundMenu):
        """初始化菜单动画管理器
        
        Args:
            menu: 目标 RoundMenu 实例，动画将作用于此菜单
        """
        super().__init__()
        self.menu = menu
        self.ani = QPropertyAnimation(menu, b'pos', menu)

        self.ani.setDuration(250)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.ani.valueChanged.connect(self._onValueChanged)
        self.ani.valueChanged.connect(self._updateMenuViewport)

    def _onValueChanged(self):
        pass

    def availableViewSize(self, pos: QPoint):
        """返回视图可用尺寸"""
        ss = getCurrentScreenGeometry()
        w, h = ss.width() - 100, ss.height() - 100
        return w, h

    def _updateMenuViewport(self):
        self.menu.view.viewport().update()
        self.menu.view.setAttribute(Qt.WA_UnderMouse, True)
        e = QHoverEvent(QEvent.HoverEnter, QPoint(), QPoint(1, 1))
        QApplication.sendEvent(self.menu.view, e)

    def _endPosition(self, pos):
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = min(pos.y() - 4, rect.bottom() - h + 10)

        return QPoint(x, y)

    def _menuSize(self):
        m = self.menu.layout().contentsMargins()
        w = self.menu.view.width() + m.left() + m.right() + 120
        h = self.menu.view.height() + m.top() + m.bottom() + 20
        return w, h

    def exec(self, pos: QPoint):
        pass

    @classmethod
    def register(cls, name):
        """注册菜单动画管理器

        Args:
            name: 管理器名称，必须唯一
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def make(cls, menu: RoundMenu, aniType: MenuAnimationType):
        if aniType not in cls.managers:
            raise ValueError(f'`{aniType}` is an invalid menu animation type.')

        return cls.managers[aniType](menu)


@MenuAnimationManager.register(MenuAnimationType.NONE)
class DummyMenuAnimationManager(MenuAnimationManager):
    """空菜单动画管理器
    禁用所有动画效果，菜单将直接显示在目标位置而不产生过渡动画
    适用于追求响应速度或对动画性能敏感的场景
    """

    def exec(self, pos: QPoint):
        self.menu.move(self._endPosition(pos))


@MenuAnimationManager.register(MenuAnimationType.DROP_DOWN)
class DropDownMenuAnimationManager(MenuAnimationManager):
    """下拉菜单动画管理器
    菜单从触发点下方展开，若下方空间不足则自动翻转至上方的标准下拉动画
    适用于 ComboBox、PushButton 等控件的下拉菜单场景
    """

    def exec(self, pos):
        pos = self._endPosition(pos)
        h = self.menu.height() + 5

        self.ani.setStartValue(pos-QPoint(0, int(h/2)))
        self.ani.setEndValue(pos)
        self.ani.start()

    def availableViewSize(self, pos: QPoint):
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(ss.bottom() - pos.y() - 10, 1)

    def _onValueChanged(self):
        w, h = self._menuSize()
        y = self.ani.endValue().y() - self.ani.currentValue().y()
        self.menu.setMask(QRegion(0, y, w, h))


@MenuAnimationManager.register(MenuAnimationType.PULL_UP)
class PullUpMenuAnimationManager(MenuAnimationManager):
    """上拉菜单动画管理器
    菜单从触发点上方展开，若上方空间不足则自动翻转至下方
    适用于任务栏、底部工具栏等靠近屏幕边缘的弹出菜单场景
    """

    def _endPosition(self, pos):
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = max(pos.y() - h + 10, rect.top() + 4)
        return QPoint(x, y)

    def exec(self, pos):
        pos = self._endPosition(pos)
        h = self.menu.height() + 5

        self.ani.setStartValue(pos+QPoint(0, int(h/2)))
        self.ani.setEndValue(pos)
        self.ani.start()

    def availableViewSize(self, pos: QPoint):
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(pos.y() - ss.top() - 28, 1)

    def _onValueChanged(self):
        w, h = self._menuSize()
        y = self.ani.endValue().y() - self.ani.currentValue().y()
        self.menu.setMask(QRegion(0, y, w, h - 28))


@MenuAnimationManager.register(MenuAnimationType.FADE_IN_DROP_DOWN)
class FadeInDropDownMenuAnimationManager(MenuAnimationManager):
    """淡入下拉菜单动画管理器
    在下拉展开的同时叠加透明度从 0 到 1 的淡入效果，增强视觉流畅感
    适用于需要柔和过渡效果的下拉菜单场景
    """

    def __init__(self, menu: RoundMenu):
        """初始化淡入下拉菜单动画管理器
        
        Args:
            menu: 目标 RoundMenu 实例，将应用淡入下拉动画
        """
        super().__init__(menu)
        self.opacityAni = QPropertyAnimation(menu, b'windowOpacity', self)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.ani)
        self.aniGroup.addAnimation(self.opacityAni)

    def exec(self, pos):
        pos = self._endPosition(pos)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)

        self.ani.setStartValue(pos-QPoint(0, 8))
        self.ani.setEndValue(pos)
        self.ani.setDuration(150)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)

        self.aniGroup.start()

    def availableViewSize(self, pos: QPoint):
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, max(ss.bottom() - pos.y() - 10, 1)


@MenuAnimationManager.register(MenuAnimationType.FADE_IN_PULL_UP)
class FadeInPullUpMenuAnimationManager(MenuAnimationManager):
    """淡入上拉菜单动画管理器
    在上拉展开的同时叠加透明度渐变效果，兼顾空间适配与视觉平滑度
    适用于底部弹出且需要柔和显隐过渡的菜单场景
    """

    def __init__(self, menu: RoundMenu):
        """初始化淡入上拉菜单动画管理器
        
        Args:
            menu: 目标 RoundMenu 实例，将应用淡入上拉动画
        """
        super().__init__(menu)
        self.opacityAni = QPropertyAnimation(menu, b'windowOpacity', self)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.ani)
        self.aniGroup.addAnimation(self.opacityAni)

    def _endPosition(self, pos):
        m = self.menu
        rect = getCurrentScreenGeometry()
        w, h = m.width() + 5, m.height()
        x = min(pos.x() - m.layout().contentsMargins().left(), rect.right() - w)
        y = max(pos.y() - h + 15, rect.top() + 4)
        return QPoint(x, y)

    def exec(self, pos):
        pos = self._endPosition(pos)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)

        self.ani.setStartValue(pos+QPoint(0, 8))
        self.ani.setEndValue(pos)
        self.ani.setDuration(200)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.aniGroup.start()

    def availableViewSize(self, pos: QPoint):
        ss = getCurrentScreenGeometry()
        return ss.width() - 100, pos.y()- ss.top() - 28


class EditMenu(RoundMenu):
    """编辑菜单
    提供剪切、复制、粘贴、删除和全选等标准文本编辑操作，自动根据当前选区状态启用或禁用动作
    适用于文本输入类控件的通用右键菜单，可配合 QLineEdit、QTextEdit 使用
    """

    def createActions(self):
        self.cutAct = QAction(
            FIF.CUT.icon(),
            self.tr("Cut"),
            self,
            shortcut="Ctrl+X",
            triggered=self.parent().cut,
        )
        self.copyAct = QAction(
            FIF.COPY.icon(),
            self.tr("Copy"),
            self,
            shortcut="Ctrl+C",
            triggered=self.parent().copy,
        )
        self.pasteAct = QAction(
            FIF.PASTE.icon(),
            self.tr("Paste"),
            self,
            shortcut="Ctrl+V",
            triggered=self.parent().paste,
        )
        self.cancelAct = QAction(
            FIF.CANCEL.icon(),
            self.tr("Cancel"),
            self,
            shortcut="Ctrl+Z",
            triggered=self.parent().undo,
        )
        self.selectAllAct = QAction(
            self.tr("Select all"),
            self,
            shortcut="Ctrl+A",
            triggered=self.parent().selectAll
        )
        self.action_list = [
            self.cutAct, self.copyAct,
            self.pasteAct, self.cancelAct, self.selectAllAct
        ]

    def _parentText(self):
        raise NotImplementedError

    def _parentSelectedText(self):
        raise NotImplementedError

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        self.clear()
        self.createActions()

        if QApplication.clipboard().mimeData().hasText():
            if self._parentText():
                if self._parentSelectedText():
                    if self.parent().isReadOnly():
                        self.addActions([self.copyAct, self.selectAllAct])
                    else:
                        self.addActions(self.action_list)
                else:
                    if self.parent().isReadOnly():
                        self.addAction(self.selectAllAct)
                    else:
                        self.addActions(self.action_list[2:])
            elif not self.parent().isReadOnly():
                self.addAction(self.pasteAct)
            else:
                return
        else:
            if not self._parentText():
                return

            if self._parentSelectedText():
                if self.parent().isReadOnly():
                    self.addActions([self.copyAct, self.selectAllAct])
                else:
                    self.addActions(
                        self.action_list[:2] + self.action_list[3:])
            else:
                if self.parent().isReadOnly():
                    self.addAction(self.selectAllAct)
                else:
                    self.addActions(self.action_list[3:])

        super().exec(pos, ani, aniType)


class LineEditMenu(EditMenu):
    """行编辑器菜单
    专为 QLineEdit 设计的右键菜单，集成撤销、重做、剪切、复制、粘贴、删除和全选功能
    自动识别编辑器状态，在无选中内容时禁用剪切/复制/删除，在不可编辑时禁用修改类操作
    """

    def __init__(self, parent: QLineEdit):
        """初始化行编辑器菜单
        
        Args:
            parent: 关联的 QLineEdit 实例，菜单将作用于该编辑器
        """
        super().__init__("", parent)
        self.selectionStart = parent.selectionStart()
        self.selectionLength = parent.selectionLength()

    def _onItemClicked(self, item):
        if self.selectionStart >= 0:
            self.parent().setSelection(self.selectionStart, self.selectionLength)

        super()._onItemClicked(item)

    def _parentText(self):
        return self.parent().text()

    def _parentSelectedText(self):
        return self.parent().selectedText()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)


class TextEditMenu(EditMenu):
    """文本编辑菜单
    专为 QTextEdit 和 QPlainTextEdit 设计的右键菜单，支持富文本和纯文本的编辑操作
    除标准编辑功能外，可自动适配文本状态并支持扩展自定义动作
    """

    def __init__(self, parent: QTextEdit):
        """初始化文本编辑菜单
        
        Args:
            parent: 关联的文本编辑器实例，通常为 QTextEdit 或 QPlainTextEdit
        """
        super().__init__("", parent)
        cursor = parent.textCursor()
        self.selectionStart = cursor.selectionStart()
        self.selectionLength = cursor.selectionEnd() - self.selectionStart + 1

    def _parentText(self):
        return self.parent().toPlainText()

    def _parentSelectedText(self):
        return self.parent().textCursor().selectedText()

    def _onItemClicked(self, item):
        if self.selectionStart >= 0:
            cursor = self.parent().textCursor()
            cursor.setPosition(self.selectionStart)
            cursor.movePosition(
                QTextCursor.Right, QTextCursor.KeepAnchor, self.selectionLength)

        super()._onItemClicked(item)

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)


class IndicatorMenuItemDelegate(MenuItemDelegate):
    """带指示器的菜单项委托
    在菜单项左侧绘制选中状态指示器（单选或复选框），继承自 MenuItemDelegate
    用于 CheckableMenu 内部，根据 indicatorType 决定绘制样式
    """

    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)
        if not option.state & QStyle.State_Selected:
            return

        painter.save()
        painter.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(themeColor())
        painter.drawRoundedRect(6, 11+option.rect.y(), 3, 15, 1.5, 1.5)

        painter.restore()


class CheckableMenuItemDelegate(ShortcutMenuItemDelegate):
    """可选中菜单项委托
    支持在菜单项左侧显示勾选标记的委托基类，处理 checked 状态的绘制和布局偏移
    适用于需要展示选中/未选中状态的菜单项，通常与 CheckableMenu 配合使用
    """

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        raise NotImplementedError

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)

        # 绘制指示器
        action = index.data(Qt.UserRole)  # type: QAction
        if not (isinstance(action, QAction) and action.isChecked()):
            return

        painter.save()
        self._drawIndicator(painter, option, index)
        painter.restore()


class RadioIndicatorMenuItemDelegate(CheckableMenuItemDelegate):
    """带单选指示器的可选中菜单项委托
    绘制圆形单选按钮样式的指示器，用于标识一组互斥选项中的当前选中项
    适用于 CheckableMenu 的 indicatorType 为 Radio 时的菜单项渲染
    """

    def _drawIndicator(self, painter, option, index):
        rect = option.rect
        r = 5
        x = rect.x() + 22
        y = rect.center().y() - r / 2

        painter.setRenderHints(QPainter.Antialiasing)
        if not option.state & QStyle.State_MouseOver:
            painter.setOpacity(0.75 if isDarkTheme() else 0.65)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white if isDarkTheme() else Qt.black)
        painter.drawEllipse(QRectF(x, y, r, r))


class CheckIndicatorMenuItemDelegate(CheckableMenuItemDelegate):
    """带复选指示器的可选中菜单项委托
    绘制方形复选框样式的指示器，支持勾选和未勾选两种视觉状态
    适用于 CheckableMenu 的 indicatorType 为 Check 时的菜单项渲染
    """

    def _drawIndicator(self, painter, option, index):
        rect = option.rect
        s = 11
        x = rect.x() + 19
        y = rect.center().y() - s / 2

        painter.setRenderHints(QPainter.Antialiasing)
        if not option.state & QStyle.State_MouseOver:
            painter.setOpacity(0.75)

        FIF.ACCEPT.render(painter, QRectF(x, y, s, s))


class MenuIndicatorType(Enum):
    """菜单指示器类型
    定义可选中菜单项的指示器样式枚举，包括无指示器、单选按钮和复选框
    通过 CheckableMenu 设置，控制所有子菜单项的选中表现形式
    """
    CHECK = 0
    RADIO = 1


def createCheckableMenuItemDelegate(style: MenuIndicatorType):
    """创建可选中菜单项委托"""
    if style == MenuIndicatorType.RADIO:
        return RadioIndicatorMenuItemDelegate()
    if style == MenuIndicatorType.CHECK:
        return CheckIndicatorMenuItemDelegate()

    raise ValueError(f'`{style}` is not a valid menu indicator type.')


class CheckableMenu(RoundMenu):
    """可选中菜单
    支持添加带单选或复选指示器的菜单项，用户可通过点击切换选中状态
    适用于需要让用户进行多项选择或单项选择的弹出菜单场景，如视图设置、筛选条件等
    """

    def __init__(self, title="", parent=None, indicatorType=MenuIndicatorType.CHECK):
        """初始化可选中菜单
        
        Args:
            title: 菜单标题文本，若为 None 则不显示标题栏
            parent: 父窗口或部件
            indicatorType: 指示器类型，决定菜单项使用 Radio 单选或 Check 复选样式
        """
        super().__init__(title, parent)
        self.view.setItemDelegate(createCheckableMenuItemDelegate(indicatorType))
        self.view.setObjectName('checkableListWidget')

    def _adjustItemText(self, item: QListWidgetItem, action: QAction):
        w = super()._adjustItemText(item, action)
        item.setSizeHint(QSize(w + 26, self.itemHeight))

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)


class SystemTrayMenu(RoundMenu):
    """系统托盘菜单
    专为 QSystemTrayIcon 设计的上下文菜单，支持圆角风格和 Fluent Design 视觉效果
    适用于托盘图标右键弹出的操作菜单，可添加常规动作和子菜单
    """

    def sizeHint(self) -> QSize:
        m = self.layout().contentsMargins()
        s = self.layout().sizeHint()
        return QSize(s.width() - m.right() + 5, s.height() - m.bottom())


class CheckableSystemTrayMenu(CheckableMenu):
    """可选中系统托盘菜单
    在系统托盘菜单基础上支持单选/复选菜单项，允许用户在托盘菜单中进行状态切换
    适用于需要展示开关状态或模式选择的托盘快捷菜单，如显示/隐藏窗口、切换主题等
    """

    def sizeHint(self) -> QSize:
        m = self.layout().contentsMargins()
        s = self.layout().sizeHint()
        return QSize(s.width() - m.right() + 5, s.height() - m.bottom())


class LabelContextMenu(RoundMenu):
    """标签上下文菜单
    为 QLabel 提供的轻量级右键菜单，默认包含复制文本功能
    适用于不可编辑文本标签的快速复制交互，可扩展添加自定义动作
    """

    def __init__(self, parent: QLabel):
        """初始化标签上下文菜单
        
        Args:
            parent: 关联的 QLabel 实例，菜单将读取该标签文本用于复制操作
        """
        super().__init__("", parent)
        self.selectedText = parent.selectedText()

        self.copyAct = QAction(
            FIF.COPY.icon(),
            self.tr("Copy"),
            self,
            shortcut="Ctrl+C",
            triggered=self._onCopy
        )
        self.selectAllAct = QAction(
            self.tr("Select all"),
            self,
            shortcut="Ctrl+A",
            triggered=self._onSelectAll
        )

    def _onCopy(self):
        QApplication.clipboard().setText(self.selectedText)

    def _onSelectAll(self):
        self.label().setSelection(0, len(self.label().text()))

    def label(self) -> QLabel:
        return self.parent()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        if self.label().hasSelectedText():
            self.addActions([self.copyAct, self.selectAllAct])
        else:
            self.addAction(self.selectAllAct)

        return super().exec(pos, ani, aniType)