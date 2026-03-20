# coding: utf-8
from copy import deepcopy
from enum import Enum
from typing import Dict, List, Union
from uuid import uuid1
from PySide6.QtCore import Qt, Signal, Property, QRectF, QSize, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter, QColor, QIcon, QPainterPath, QLinearGradient, QPen, QBrush, QMouseEvent
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, QApplication, QStackedWidget

from ...common.icon import FluentIcon, FluentIconBase, drawIcon
from ...common.style_sheet import isDarkTheme, FluentStyleSheet
from ...common.font import setFont
from ...common.router import qrouter
from .button import TransparentToolButton, PushButton
from .scroll_area import SingleDirectionScrollArea
from .tool_tip import ToolTipFilter


class TabCloseButtonDisplayMode(Enum):
    """ Tab 关闭 按钮 display 模式 """
    ALWAYS = 0
    ON_HOVER = 1
    NEVER = 2


def checkIndex(*default):
    """ decorator 用于 索引 checking

    参数
    ----------
    *default:
        default 值 returned 当 索引 溢出
    """

    def outer(func):

        def inner(tabBar, index: int, *args, **kwargs):
            if 0 <= index < len(tabBar.items):
                return func(tabBar, index, *args, **kwargs)

            value = deepcopy(default)
            if len(value) == 0:
                return None
            elif len(value) == 1:
                return value[0]

            return value

        return inner

    return outer


class TabToolButton(TransparentToolButton):
    """ Tab 工具按钮 """

    def _postInit(self):
        self.setFixedSize(32, 24)
        self.setIconSize(QSize(12, 12))

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.Off):
        color = '#eaeaea' if isDarkTheme() else '#484848'
        icon = icon.icon(color=color)
        super()._drawIcon(icon, painter, rect, state)


class TabItem(PushButton):
    """ Tab 项 """

    closed = Signal()
    doubleClicked = Signal()

    def _postInit(self):
        super()._postInit()
        self.borderRadius = 5
        self.isSelected = False
        self.isShadowEnabled = True
        self.closeButtonDisplayMode = TabCloseButtonDisplayMode.ALWAYS

        self._routeKey = None
        self.textColor = None
        self.lightSelectedBackgroundColor = QColor(249, 249, 249)
        self.darkSelectedBackgroundColor = QColor(40, 40, 40)

        self.closeButton = TabToolButton(FluentIcon.CLOSE, self)
        self.shadowEffect = QGraphicsDropShadowEffect(self)

        self.slideAni = QPropertyAnimation(self, b'pos', self)

        self.__initWidget()

    def __initWidget(self):
        setFont(self, 12)
        self.setFixedHeight(36)
        self.setMaximumWidth(240)
        self.setMinimumWidth(64)
        self.installEventFilter(ToolTipFilter(self, showDelay=1000))
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        self.closeButton.setIconSize(QSize(10, 10))

        self.shadowEffect.setBlurRadius(5)
        self.shadowEffect.setOffset(0, 1)
        self.setGraphicsEffect(self.shadowEffect)
        self.setSelected(False)

        self.closeButton.clicked.connect(self.closed)

    def slideTo(self, x: int, duration=250):
        self.slideAni.setStartValue(self.pos())
        self.slideAni.setEndValue(QPoint(x, self.y()))
        self.slideAni.setDuration(duration)
        self.slideAni.setEasingCurve(QEasingCurve.InOutQuad)
        self.slideAni.start()

    def setShadowEnabled(self, isEnabled: bool):
        """ 设置 是否 shadow is 已启用 """
        if isEnabled == self.isShadowEnabled:
            return

        self.isShadowEnabled = isEnabled
        self.shadowEffect.setColor(QColor(0, 0, 0, 50*self._canShowShadow()))

    def _canShowShadow(self):
        return self.isSelected and self.isShadowEnabled

    def setRouteKey(self, key: str):
        self._routeKey = key

    def routeKey(self):
        return self._routeKey

    def setBorderRadius(self, radius: int):
        self.borderRadius = radius
        self.update()

    def setSelected(self, isSelected: bool):
        self.isSelected = isSelected

        self.shadowEffect.setColor(QColor(0, 0, 0, 50*self._canShowShadow()))
        self.update()

        if isSelected:
            self.raise_()

        if self.closeButtonDisplayMode == TabCloseButtonDisplayMode.ON_HOVER:
            self.closeButton.setVisible(isSelected)

    def setCloseButtonDisplayMode(self, mode: TabCloseButtonDisplayMode):
        """ 设置 关闭 按钮 display 模式 """
        if mode == self.closeButtonDisplayMode:
            return

        self.closeButtonDisplayMode = mode

        if mode == TabCloseButtonDisplayMode.NEVER:
            self.closeButton.hide()
        elif mode == TabCloseButtonDisplayMode.ALWAYS:
            self.closeButton.show()
        else:
            self.closeButton.setVisible(self.isHover or self.isSelected)

    def setTextColor(self, color: QColor):
        self.textColor = QColor(color)
        self.update()

    def setSelectedBackgroundColor(self, light: QColor, dark: QColor):
        """ 设置 背景色 中的 selected state """
        self.lightSelectedBackgroundColor = QColor(light)
        self.darkSelectedBackgroundColor = QColor(dark)
        self.update()

    def resizeEvent(self, e):
        self.closeButton.move(
            self.width()-6-self.closeButton.width(), int(self.height()/2-self.closeButton.height()/2))

    def enterEvent(self, e):
        super().enterEvent(e)
        if self.closeButtonDisplayMode == TabCloseButtonDisplayMode.ON_HOVER:
            self.closeButton.show()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        if self.closeButtonDisplayMode == TabCloseButtonDisplayMode.ON_HOVER and not self.isSelected:
            self.closeButton.hide()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self._forwardMouseEvent(e)

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        self._forwardMouseEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._forwardMouseEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()

        return super().mouseDoubleClickEvent(e)

    def _forwardMouseEvent(self, e: QMouseEvent):
        pos = self.mapToParent(e.pos())
        event = QMouseEvent(e.type(), pos, e.button(),
                            e.buttons(), e.modifiers())
        QApplication.sendEvent(self.parent(), event)

    def sizeHint(self):
        return QSize(self.maximumWidth(), 36)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if self.isSelected:
            self._drawSelectedBackground(painter)
        else:
            self._drawNotSelectedBackground(painter)

        # 绘制图标
        if not self.isSelected:
            painter.setOpacity(0.79 if isDarkTheme() else 0.61)

        drawIcon(self._icon, painter, QRectF(10, 10, 16, 16))

        # 绘制文本
        self._drawText(painter)

    def _drawSelectedBackground(self, painter: QPainter):
        w, h = self.width(), self.height()
        r = self.borderRadius
        d = 2 * r

        isDark = isDarkTheme()

        # 绘制top 边框
        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 225)
        path.arcTo(1, h - d - 1, d, d, 225, -45)
        path.lineTo(1, r)
        path.arcTo(1, 1, d, d, -180, -90)
        path.lineTo(w - r, 1)
        path.arcTo(w - d - 1, 1, d, d, 90, -90)
        path.lineTo(w - 1, h - r)
        path.arcTo(w - d - 1, h - d - 1, d, d, 0, -45)

        topBorderColor = QColor(0, 0, 0, 20)
        if isDark:
            if self.isPressed:
                topBorderColor = QColor(255, 255, 255, 18)
            elif self.isHover:
                topBorderColor = QColor(255, 255, 255, 13)
        else:
            topBorderColor = QColor(0, 0, 0, 16)

        painter.strokePath(path, topBorderColor)

        # 绘制bottom 边框
        path = QPainterPath()
        path.arcMoveTo(1, h - d - 1, d, d, 225)
        path.arcTo(1, h - d - 1, d, d, 225, 45)
        path.lineTo(w - r - 1, h - 1)
        path.arcTo(w - d - 1, h - d - 1, d, d, 270, 45)

        bottomBorderColor = topBorderColor
        if not isDark:
            bottomBorderColor = QColor(0, 0, 0, 63)

        painter.strokePath(path, bottomBorderColor)

        # 绘制背景
        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(
            self.darkSelectedBackgroundColor if isDark else self.lightSelectedBackgroundColor)
        painter.drawRoundedRect(rect, r, r)

    def _drawNotSelectedBackground(self, painter: QPainter):
        if not (self.isPressed or self.isHover):
            return

        isDark = isDarkTheme()

        if self.isPressed:
            color = QColor(255, 255, 255, 12) if isDark else QColor(0, 0, 0, 7)
        else:
            color = QColor(255, 255, 255, 15) if isDark else QColor(
                0, 0, 0, 10)

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(
            1, 1, -1, -1), self.borderRadius, self.borderRadius)

    def _drawText(self, painter: QPainter):
        tw = self.fontMetrics().boundingRect(self.text()).width()

        if self.icon().isNull():
            dw = 47 if self.closeButton.isVisible() else 20
            rect = QRectF(10, 0, self.width() - dw, self.height())
        else:
            dw = 70 if self.closeButton.isVisible() else 45
            rect = QRectF(33, 0, self.width() - dw, self.height())

        pen = QPen()
        color = Qt.white if isDarkTheme() else Qt.black
        color = self.textColor or color
        rw = rect.width()

        if tw > rw:
            gradient = QLinearGradient(rect.x(), 0, tw+rect.x(), 0)
            gradient.setColorAt(0, color)
            gradient.setColorAt(max(0, (rw - 10) / tw), color)
            gradient.setColorAt(max(0, rw / tw), Qt.transparent)
            gradient.setColorAt(1, Qt.transparent)
            pen.setBrush(QBrush(gradient))
        else:
            pen.setColor(color)

        painter.setPen(pen)
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())


class TabBar(SingleDirectionScrollArea):
    """ Tab 栏 """

    currentChanged = Signal(int)
    tabBarClicked = Signal(int)
    tabBarDoubleClicked = Signal(int)
    tabCloseRequested = Signal(int)
    tabAddRequested = Signal()
    tabMoved = Signal(int, int)  # (from, to)

    def __init__(self, parent=None):
        super().__init__(parent=parent, orient=Qt.Horizontal)
        self.items = []  # type: 列表[TabItem]
        self.itemMap = {} # type: Dict[str, TabItem]

        self._currentIndex = -1

        self._isMovable = False
        self._isScrollable = False
        self._isTabShadowEnabled = True

        self._tabMaxWidth = 240
        self._tabMinWidth = 64

        self.dragPos = QPoint()
        self.isDraging = False

        self.lightSelectedBackgroundColor = QColor(249, 249, 249)
        self.darkSelectedBackgroundColor = QColor(40, 40, 40)
        self.closeButtonDisplayMode = TabCloseButtonDisplayMode.ALWAYS

        self.view = QWidget(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.itemLayout = QHBoxLayout()
        self.widgetLayout = QHBoxLayout()

        self.addButton = TabToolButton(FluentIcon.ADD, self)

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(46)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMaximumSize)

        self.addButton.clicked.connect(self.tabAddRequested)

        self.view.setObjectName('view')
        FluentStyleSheet.TAB_VIEW.apply(self)
        FluentStyleSheet.TAB_VIEW.apply(self.view)

        self.__initLayout()

    def __initLayout(self):
        self.hBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.itemLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.widgetLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.itemLayout.setContentsMargins(5, 5, 5, 5)
        self.widgetLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.itemLayout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)

        self.hBoxLayout.setSpacing(0)
        self.itemLayout.setSpacing(0)

        self.hBoxLayout.addLayout(self.itemLayout)
        self.hBoxLayout.addSpacing(3)

        self.widgetLayout.addWidget(self.addButton, 0, Qt.AlignLeft)
        self.hBoxLayout.addLayout(self.widgetLayout)
        self.hBoxLayout.addStretch(1)

    def setAddButtonVisible(self, isVisible: bool):
        self.addButton.setVisible(isVisible)

    def addTab(self, routeKey: str, text: str, icon: Union[QIcon, str, FluentIconBase] = None, onClick=None):
        """ 添加 tab

        参数
        ----------
        routeKey: str
            unique name 的 tab 项

        text: str
            文本 的 tab 项

        text: str
            图标 的 tab 项

        onClick: callable
            槽函数 connected 到 项 clicked 信号
        """
        return self.insertTab(-1, routeKey, text, icon, onClick)

    def insertTab(self, index: int, routeKey: str, text: str, icon: Union[QIcon, str, FluentIconBase] = None,
                  onClick=None):
        """ 插入 tab

        参数
        ----------
        index: int
            插入 位置 的 tab 项

        routeKey: str
            unique name 的 tab 项

        text: str
            文本 的 tab 项

        text: str
            图标 的 tab 项

        onClick: callable
            槽函数 connected 到 项 clicked 信号
        """
        if routeKey in self.itemMap:
            raise ValueError(f"The route key `{routeKey}` is duplicated.")

        if index == -1:
            index = len(self.items)

        # 调整当前 索引
        if index <= self.currentIndex() and self.currentIndex() >= 0:
            self._currentIndex += 1

        item = TabItem(text, self.view, icon)
        item.setRouteKey(routeKey)

        # 设置tab的大小
        w = self.tabMaximumWidth() if self.isScrollable() else self.tabMinimumWidth()
        item.setMinimumWidth(w)
        item.setMaximumWidth(self.tabMaximumWidth())

        item.setShadowEnabled(self.isTabShadowEnabled())
        item.setCloseButtonDisplayMode(self.closeButtonDisplayMode)
        item.setSelectedBackgroundColor(
            self.lightSelectedBackgroundColor, self.darkSelectedBackgroundColor)

        item.pressed.connect(self._onItemPressed)
        item.doubleClicked.connect(lambda: self.tabBarDoubleClicked.emit(self.items.index(item)))
        item.closed.connect(lambda: self.tabCloseRequested.emit(self.items.index(item)))
        if onClick:
            item.pressed.connect(onClick)

        self.itemLayout.insertWidget(index, item, 1)
        self.items.insert(index, item)
        self.itemMap[routeKey] = item

        if len(self.items) == 1:
            self.setCurrentIndex(0)

        return item

    def removeTab(self, index: int):
        if not 0 <= index < len(self.items):
            return

        # 调整当前 索引
        if index < self.currentIndex():
            self._currentIndex -= 1
        elif index == self.currentIndex():
            if self.currentIndex() > 0:
                self.setCurrentIndex(self.currentIndex() - 1)
                self.currentChanged.emit(self.currentIndex())
            elif len(self.items) == 1:
                self._currentIndex = -1
            else:
                self.setCurrentIndex(1)
                self._currentIndex = 0
                self.currentChanged.emit(0)

        # 移除 tab
        item = self.items.pop(index)
        self.itemMap.pop(item.routeKey())
        self.hBoxLayout.removeWidget(item)
        qrouter.remove(item.routeKey())
        item.deleteLater()

        # 移除 shadow
        self.update()

    def removeTabByKey(self, routeKey: str):
        if routeKey not in self.itemMap:
            return

        self.removeTab(self.items.index(self.tab(routeKey)))

    def setCurrentIndex(self, index: int):
        """ 设置当前索引 """
        if index == self._currentIndex:
            return

        if self.currentIndex() >= 0:
            self.items[self.currentIndex()].setSelected(False)

        self._currentIndex = index
        self.items[index].setSelected(True)

    def setCurrentTab(self, routeKey: str):
        if routeKey not in self.itemMap:
            return

        self.setCurrentIndex(self.items.index(self.tab(routeKey)))

    def currentIndex(self):
        return self._currentIndex

    def currentTab(self):
        return self.tabItem(self.currentIndex())

    def _onItemPressed(self):
        for item in self.items:
            item.setSelected(item is self.sender())

        index = self.items.index(self.sender())
        self.tabBarClicked.emit(index)

        if index != self.currentIndex():
            self.setCurrentIndex(index)
            self.currentChanged.emit(index)

    def setCloseButtonDisplayMode(self, mode: TabCloseButtonDisplayMode):
        """ 设置 关闭 按钮 display 模式 """
        if mode == self.closeButtonDisplayMode:
            return

        self.closeButtonDisplayMode = mode
        for item in self.items:
            item.setCloseButtonDisplayMode(mode)

    @checkIndex()
    def tabItem(self, index: int):
        return self.items[index]

    def tab(self, routeKey: str):
        return self.itemMap.get(routeKey, None)

    def tabRegion(self) -> QRect:
        """ 返回all tabs的bounding 区域 """
        return self.itemLayout.geometry()

    @checkIndex()
    def tabRect(self, index: int):
        """ 返回the tab at 位置 索引的visual rectangle """
        x = 0
        for i in range(index):
            x += self.tabItem(i).width()

        rect = self.tabItem(index).geometry()
        rect.moveLeft(x)
        return rect

    @checkIndex()
    def tabData(self, index: int):
        return self.tabItem(index).property("data")

    @checkIndex()
    def setTabData(self, index: int, data):
        self.tabItem(index).setProperty("data", data)

    @checkIndex('')
    def tabText(self, index: int):
        return self.tabItem(index).text()

    @checkIndex()
    def tabIcon(self, index: int):
        return self.tabItem(index).icon()

    @checkIndex('')
    def tabToolTip(self, index: int):
        return self.tabItem(index).toolTip()

    @checkIndex(False)
    def isTabEnabled(self, index: int):
        return self.tabItem(index).isEnabled()

    @checkIndex()
    def setTabEnabled(self, index: int, isEnabled: bool):
        self.tabItem(index).setEnabled(isEnabled)

    def setTabsClosable(self, isClosable: bool):
        """ 设置 是否 tab is closable """
        if isClosable:
            self.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ALWAYS)
        else:
            self.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.NEVER)

    def tabsClosable(self):
        return self.closeButtonDisplayMode != TabCloseButtonDisplayMode.NEVER

    @checkIndex()
    def setTabIcon(self, index: int, icon: Union[QIcon, FluentIconBase, str]):
        """ 设置 tab 图标 """
        self.tabItem(index).setIcon(icon)

    @checkIndex()
    def setTabText(self, index: int, text: str):
        """ 设置 tab 文本 """
        self.tabItem(index).setText(text)

    @checkIndex(False)
    def isTabVisible(self, index: int):
        return self.tabItem(index).isVisible(index)

    @checkIndex()
    def setTabVisible(self, index: int, isVisible: bool):
        """ 设置tab的可见性 """
        self.tabItem(index).setVisible(isVisible)

        if isVisible and self.currentIndex() < 0:
            self.setCurrentIndex(0)
        elif not isVisible:
            if self.currentIndex() > 0:
                self.setCurrentIndex(self.currentIndex() - 1)
                self.currentChanged.emit(self.currentIndex())
            elif len(self.items) == 1:
                self._currentIndex = -1
            else:
                self.setCurrentIndex(1)
                self._currentIndex = 0
                self.currentChanged.emit(0)

    @checkIndex()
    def setTabTextColor(self, index: int, color: QColor):
        """ 设置tab 项的文本 颜色 """
        self.tabItem(index).setTextColor(color)

    @checkIndex()
    def setTabToolTip(self, index: int, toolTip: str):
        """ 设置 工具提示 的 tab """
        self.tabItem(index).setToolTip(toolTip)

    def setTabSelectedBackgroundColor(self, light: QColor, dark: QColor):
        """ 设置 背景 中的 selected state """
        self.lightSelectedBackgroundColor = QColor(light)
        self.darkSelectedBackgroundColor = QColor(dark)

        for item in self.items:
            item.setSelectedBackgroundColor(light, dark)

    def setTabShadowEnabled(self, isEnabled: bool):
        """ 设置 是否 shadow 的 tab is 已启用 """
        if isEnabled == self.isTabShadowEnabled():
            return

        self._isTabShadowEnabled = isEnabled
        for item in self.items:
            item.setShadowEnabled(isEnabled)

    def isTabShadowEnabled(self):
        return self._isTabShadowEnabled

    def paintEvent(self, e):
        painter = QPainter(self.viewport())
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制separators
        if isDarkTheme():
            color = QColor(255, 255, 255, 21)
        else:
            color = QColor(0, 0, 0, 15)

        painter.setPen(color)

        for i, item in enumerate(self.items):
            canDraw = not (item.isHover or item.isSelected)
            if i < len(self.items) - 1:
                nextItem = self.items[i + 1]
                if nextItem.isHover or nextItem.isSelected:
                    canDraw = False

            if canDraw:
                x = item.geometry().right()
                y = self.height() // 2 - 8
                painter.drawLine(x, y, x, y + 16)

    def setMovable(self, movable: bool):
        self._isMovable = movable

    def isMovable(self):
        return self._isMovable

    def setScrollable(self, scrollable: bool):
        self._isScrollable = scrollable
        w = self._tabMaxWidth if scrollable else self._tabMinWidth
        for item in self.items:
            item.setMinimumWidth(w)

    def setTabMaximumWidth(self, width: int):
        """ 设置tab的maximum 宽度 """
        if width == self._tabMaxWidth:
            return

        self._tabMaxWidth = width
        for item in self.items:
            item.setMaximumWidth(width)

    def setTabMinimumWidth(self, width: int):
        """ 设置tab的minimum 宽度 """
        if width == self._tabMinWidth:
            return

        self._tabMinWidth = width

        if not self.isScrollable():
            for item in self.items:
                item.setMinimumWidth(width)

    def tabMaximumWidth(self):
        return self._tabMaxWidth

    def tabMinimumWidth(self):
        return self._tabMinWidth

    def isScrollable(self):
        return self._isScrollable

    def count(self):
        """ 返回tabs的number """
        return len(self.items)

    def clear(self):
        """ 移除 all tabs """
        while self.count() > 0:
            self.removeTab(self.count() - 1)

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if not self.isMovable() or e.button() != Qt.LeftButton or \
                not self.itemLayout.geometry().contains(e.pos()):
            return

        self.dragPos = e.pos()

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)

        if not self.isMovable() or self.count() <= 1 or not self.itemLayout.geometry().contains(e.pos()):
            return

        index = self.currentIndex()
        item = self.tabItem(index)
        dx = e.pos().x() - self.dragPos.x()
        self.dragPos = e.pos()

        # first tab can't move left
        if index == 0 and dx < 0 and item.x() <= 0:
            return

        # last tab can't move right
        if index == self.count() - 1 and dx > 0 and item.geometry().right() >= self.itemLayout.sizeHint().width():
            return

        item.move(item.x() + dx, item.y())
        self.isDraging = True

        # move left sibling 项 到 right
        if dx < 0 and index > 0:
            siblingIndex = index - 1

            if item.x() < self.tabItem(siblingIndex).geometry().center().x():
                self._swapItem(siblingIndex)

        # move right sibling 项 到 left
        elif dx > 0 and index < self.count() - 1:
            siblingIndex = index + 1

            if item.geometry().right() > self.tabItem(siblingIndex).geometry().center().x():
                self._swapItem(siblingIndex)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)

        if not self.isMovable() or not self.isDraging:
            return

        self.isDraging = False

        item = self.tabItem(self.currentIndex())
        x = self.tabRect(self.currentIndex()).x()
        duration = int(abs(item.x() - x) * 250 / item.width())
        item.slideTo(x, duration)
        item.slideAni.finished.connect(self._adjustLayout)

    def _adjustLayout(self):
        self.sender().finished.disconnect()

        for item in self.items:
            self.itemLayout.removeWidget(item)

        for item in self.items:
            self.itemLayout.addWidget(item)

    def _swapItem(self, index: int):
        items = self.items
        swappedItem = self.tabItem(index)
        x = self.tabRect(self.currentIndex()).x()

        oldIndex = self.currentIndex()
        items[oldIndex], items[index] = items[index], items[oldIndex]
        self._currentIndex = index
        swappedItem.slideTo(x)

        self.tabMoved.emit(oldIndex, index)

    movable = Property(bool, isMovable, setMovable)
    scrollable = Property(bool, isScrollable, setScrollable)
    tabMaxWidth = Property(int, tabMaximumWidth, setTabMaximumWidth)
    tabMinWidth = Property(int, tabMinimumWidth, setTabMinimumWidth)
    tabShadowEnabled = Property(bool, isTabShadowEnabled, setTabShadowEnabled)


class TabWidget(QWidget):

    currentChanged = Signal(int)
    tabBarClicked = Signal(int)
    tabCloseRequested = Signal(int)
    tabAddRequested = Signal()
    tabBarDoubleClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabBar = TabBar(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.__initWidget()

    def __initWidget(self):
        self.vBoxLayout.addWidget(self.tabBar, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.stackedWidget, 1)
        self.vBoxLayout.setSpacing(1)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self._connectTabBarSignalToSlot()

    def addPage(self, widget: QWidget, label: str, icon: Union[QIcon, str, FluentIconBase] = None, routeKey=None) -> int:
        """ Adds tab 使用 given 页面, 图标, 和 标签 到 标签部件, 和 返回 索引 的 tab 中的 tab 栏.

        参数
        ----------
        widget: QWidget
            部件 中的 new tab

        label: str
            标题 的 tab

        icon: str | QIcon | FluentIconBase
            图标 的 tab

        routeKey: str
            路由键 的 new tab, 如果 not provided, unique uuid will be generated as 路由键

        返回
        -------
        index: int
            索引 的 tab
        """
        return self.insertTab(-1, widget, label, icon, routeKey)

    def addTab(self, widget: QWidget, label: str, icon: Union[QIcon, str, FluentIconBase] = None, routeKey=None) -> int:
        """ Adds tab 使用 given 页面, 图标, 和 标签 到 标签部件, 和 返回 索引 的 tab 中的 tab 栏.

        参数
        ----------
        widget: QWidget
            部件 中的 new tab

        label: str
            标题 的 tab

        icon: str | QIcon | FluentIconBase
            图标 的 tab

        routeKey: str
            路由键 的 new tab, 如果 not provided, unique uuid will be generated as 路由键

        返回
        -------
        index: int
            索引 的 tab
        """
        return self.insertTab(-1, widget, label, icon, routeKey)

    def insertTab(self, index: int, widget: QWidget, label: str, icon: Union[QIcon, str, FluentIconBase] = None, routeKey=None) -> int:
        """ Inserts tab 使用 given 标签 和 页面 into 标签部件 at specified 索引, 和 返回 索引 的 inserted tab 中的 tab 栏.

        参数
        ----------
        index: int
            索引 的 new tab 到 be inserted

        widget: QWidget
            部件 中的 new tab

        label: str
            标题 的 tab

        icon: str | QIcon | FluentIconBase
            图标 的 tab

        routeKey: str
            路由键 的 new tab, 如果 not provided, unique uuid will be generated as 路由键

        返回
        -------
        index: int
            索引 的 tab
        """
        if self.stackedWidget.indexOf(widget) >= 0:
            return -1

        # generate unique 路由键
        routeKey = routeKey or uuid1().hex
        widget.setProperty('routeKey', routeKey)

        # 创建a new tab
        self.tabBar.insertTab(index, routeKey, label, icon)
        self.stackedWidget.insertWidget(index, widget)

        return self.stackedWidget.indexOf(widget)

    def removeTab(self, index: int):
        """ Removes tab at 位置 索引 从 this stack 的 部件. 页面 部件 itself is not deleted.

        参数
        ----------
        index: int
            索引 的 removed 部件
        """
        if not 0 <= index < self.stackedWidget.count():
            return

        self.stackedWidget.removeWidget(self.stackedWidget.widget(index))
        self.tabBar.removeTab(index)

    def clear(self):
        """ Removes all pages, but does not delete them. """
        while self.stackedWidget.count():
            self.stackedWidget.removeWidget(self.stackedWidget.widget(0))

        self.tabBar.clear()

    def widget(self, index: int):
        """ 返回 tab 页面 at 索引 位置 索引 或 `None` 如果 索引 is out 的 range. """
        return self.stackedWidget.widget(index)

    def currentWidget(self) -> QWidget:
        "" "Returns a pointer to the page currently being displayed. """
        return self.stackedWidget.currentWidget()

    def currentIndex(self):
        """ 返回 索引 位置 的 当前 tab 页面, 返回 -1 如果 there is no 当前 部件. """
        return self.stackedWidget.currentIndex()

    def setTabBar(self, tabBar):
        """ Replaces original tab 栏 使用 new one. 注意 that this must be called before any tabs have been added, 或 behavior is undefined. """
        if tabBar == self.tabBar:
            return

        if self.tabBar:
            self.vBoxLayout.removeWidget(self.tabBar)
            self.tabBar.deleteLater()
            self.tabBar.hide()

        self.tabBar = tabBar
        self.vBoxLayout.insertWidget(0, self.tabBar)
        self._connectTabBarSignalToSlot()

    def isMovable(self):
        """ 返回 是否 user can move tabs within tabbar area. """
        return self.tabBar.isMovable()

    def setMovable(self, movable: bool):
        self.tabBar.setMovable(movable)

    def isTabEnabled(self, index: int):
        return self.tabBar.isTabEnabled(index)

    def setTabEnabled(self, index: int, isEnabled: bool):
        self.tabBar.setTabEnabled(index, isEnabled)

    def isTabVisible(self, index: int):
        return self.tabBar.isTabVisible(index)

    def setTabVisible(self, index: int, isVisible: bool):
        self.tabBar.setTabVisible(index, isVisible)

    def tabText(self, index: int):
        return self.tabBar.tabText(index)

    def tabIcon(self, index: int):
        return self.tabBar.tabIcon(index)

    def tabToolTip(self, index: int):
        return self.tabBar.tabToolTip(index)

    def setTabsClosable(self, closable: bool):
        self.tabBar.setTabsClosable(closable)

    def tabsClosable(self) -> bool:
        return self.tabBar.tabsClosable()

    def setTabIcon(self, index: int, icon: Union[QIcon, FluentIconBase, str]):
        self.tabBar.setTabIcon(index, icon)

    def setTabText(self, index: int, text: str):
        self.tabBar.setTabText(index, text)

    def setTabToolTip(self, index: int, tip: str):
        self.tabBar.setTabToolTip(index, tip)

    def setTabTextColor(self, index: int, color):
        self.tabBar.setTabTextColor(index, color)

    def setTabSelectedBackgroundColor(self, light, dark):
        self.tabBar.setTabSelectedBackgroundColor(light, dark)

    def setTabShadowEnabled(self, enabled: bool):
        self.tabBar.setTabShadowEnabled(enabled)

    def setScrollable(self, scrollable: bool):
        self.tabBar.setScrollable(scrollable)

    def isScrollable(self) -> bool:
        return self.tabBar.isScrollable()

    def setTabMaximumWidth(self, width: int):
        self.tabBar.setTabMaximumWidth(width)

    def setTabMinimumWidth(self, width: int):
        self.tabBar.setTabMinimumWidth(width)

    def tabMaximumWidth(self) -> int:
        return self.tabBar.tabMaximumWidth()

    def tabMinimumWidth(self) -> int:
        return self.tabBar.tabMinimumWidth()

    def tabData(self, index: int):
        return self.tabBar.tabData(index)

    def setTabData(self, index: int, data):
        self.tabBar.setTabData(index, data)

    def count(self) -> int:
        """ 返回 number 的 tabs 中的 tab 栏. """
        return self.stackedWidget.count()

    def setCurrentIndex(self, index: int):
        """ 索引 的 tab 栏's 可见 tab """
        self.tabBar.setCurrentIndex(index)
        self.stackedWidget.setCurrentIndex(index)

    def setCurrentWidget(self, widget: QWidget):
        """ 设置 当前 tab 到 tab which contains given 部件. """
        index = self.stackedWidget.indexOf(widget)
        if index != -1:
            self.setCurrentIndex(index)

    def setCloseButtonDisplayMode(self, mode: TabCloseButtonDisplayMode):
        self.tabBar.setCloseButtonDisplayMode(mode)

    def _connectTabBarSignalToSlot(self):
        self.tabBar.tabCloseRequested.connect(self.tabCloseRequested)
        self.tabBar.tabBarClicked.connect(self.tabBarClicked)
        self.tabBar.tabBarDoubleClicked.connect(self.tabBarDoubleClicked)
        self.tabBar.tabAddRequested.connect(self.tabAddRequested)
        self.tabBar.currentChanged.connect(self._onCurrentTabChanged)
        self.tabBar.tabMoved.connect(self._onTabMoved)

    def _onTabMoved(self, fromIndex: int, toIndex: int):
        widget = self.stackedWidget.widget(fromIndex)
        self.stackedWidget.removeWidget(widget)
        self.stackedWidget.insertWidget(toIndex, widget)
        self.stackedWidget.setCurrentIndex(toIndex)

    def _onCurrentTabChanged(self, index: int):
        self.stackedWidget.setCurrentIndex(index)
        self.currentChanged.emit(index)

