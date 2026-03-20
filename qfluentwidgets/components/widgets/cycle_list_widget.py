# coding: utf-8
from typing import Iterable

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QRectF, QEasingCurve, QTime
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QToolButton

from .scroll_area import SmoothScrollBar
from ...common.icon import FluentIcon, isDarkTheme


class ScrollButton(QToolButton):
    """ 滚动按钮 """

    def __init__(self, icon: FluentIcon, parent=None):
        super().__init__(parent=parent)
        self._icon = icon
        self.isPressed = False
        self.installEventFilter(self)

    def eventFilter(self, obj, e: QEvent):
        if obj is self:
            if e.type() == QEvent.MouseButtonPress:
                self.isPressed = True
                self.update()
            elif e.type() == QEvent.MouseButtonRelease:
                self.isPressed = False
                self.update()

        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.isPressed:
            w, h = 10, 10
        else:
            w, h = 8, 8

        x = (self.width() - w) / 2
        y = (self.height() - h) / 2

        if not isDarkTheme():
            self._icon.render(painter, QRectF(x, y, w, h), fill="#5e5e5e")
        else:
            self._icon.render(painter, QRectF(x, y, w, h))


class CycleListWidget(QListWidget):
    """ Cycle 列表 部件 """

    currentItemChanged = Signal(QListWidgetItem)

    def __init__(self, items: Iterable, itemSize: QSize, align=Qt.AlignCenter, parent=None):
        """
        参数
        ----------
        items: Iterable[Any]
            项 到 be added

        itemSize: QSize
            大小 的 项

        align: Qt.AlignmentFlag
            项文本对齐方式.

        parent: QWidget
            父部件.
        """
        super().__init__(parent=parent)
        self.itemSize = itemSize
        self.align = align

        self.upButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
        self.downButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
        self.scrollDuration = 250
        self.originItems = list(items)
        self._lastScrollTime = QTime.currentTime()
        self._scrollButtonRepeatEnabled = False

        self.vScrollBar = SmoothScrollBar(Qt.Vertical, self)
        self.visibleNumber = 9

        # repeat adding 项 到 achieve circular scrolling
        self.setItems(items)

        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.vScrollBar.setScrollAnimation(self.scrollDuration)
        self.vScrollBar.setForceHidden(True)

        self.setViewportMargins(0, 0, 0, 0)
        self.setFixedSize(itemSize.width()+8,
                          itemSize.height()*self.visibleNumber)

        # 隐藏滚动 栏
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.itemClicked.connect(self._onItemClicked)
        self.installEventFilter(self)

        # 启用auto-repeat by default
        self.upButton.clicked.connect(self.scrollUp)
        self.downButton.clicked.connect(self.scrollDown)
        self.upButton.setAutoRepeatDelay(500)
        self.upButton.setAutoRepeatInterval(50)
        self.downButton.setAutoRepeatDelay(500)
        self.downButton.setAutoRepeatInterval(50)

        self.setScrollButtonRepeatEnabled(True)
        self._setButtonsVisible(False)

    def setItems(self, items: list):
        """ 设置 项 中的 列表

        参数
        ----------
        items: Iterable[Any]
            项 到 be added

        itemSize: QSize
            大小 的 项

        align: Qt.AlignmentFlag
            文本 alignment 的 项
        """
        self.clear()
        self._createItems(items)

    def _createItems(self, items: list):
        N = len(items)
        self.isCycle = N > self.visibleNumber

        if self.isCycle:
            for _ in range(2):
                self._addColumnItems(items)

            self._currentIndex = len(items)
            super().scrollToItem(
                self.item(self.currentIndex()-self.visibleNumber//2), QListWidget.PositionAtTop)
        else:
            n = self.visibleNumber // 2  # 将empty 项添加到启用 scrolling

            self._addColumnItems(['']*n, True)
            self._addColumnItems(items)
            self._addColumnItems(['']*n, True)

            self._currentIndex = n

    def _addColumnItems(self, items, disabled=False):
        for i in items:
            item = QListWidgetItem(str(i), self)
            item.setSizeHint(self.itemSize)
            item.setTextAlignment(self.align | Qt.AlignVCenter)
            if disabled:
                item.setFlags(Qt.NoItemFlags)

            self.addItem(item)

    def _onItemClicked(self, item):
        self.setCurrentIndex(self.row(item))
        self.scrollToItem(self.currentItem())

    def setSelectedItem(self, text: str):
        """ 设置 选中项 """
        if text is None:
            return

        items = self.findItems(str(text), Qt.MatchExactly)
        if not items:
            return

        if len(items) >= 2:
            self.setCurrentIndex(self.row(items[1]))
        else:
            self.setCurrentIndex(self.row(items[0]))

        super().scrollToItem(self.currentItem(), QListWidget.ScrollHint.PositionAtCenter)

    def scrollToItem(self, item: QListWidgetItem, hint=QListWidget.ScrollHint.PositionAtCenter):
        """ 滚动 到 项 """
        # 滚动 到 center 位置
        index = self.row(item)
        y = item.sizeHint().height() * (index - self.visibleNumber // 2)
        self.vScrollBar.scrollTo(y)

        # 清空selection
        self.clearSelection()
        item.setSelected(False)

        self.currentItemChanged.emit(item)

    def wheelEvent(self, e):
        if e.angleDelta().y() < 0:
            self.scrollDown()
        else:
            self.scrollUp()

    def setScrollButtonRepeatEnabled(self, isEnabled: bool):
        """设置是否启用滚动按钮自动重复."""
        if self._scrollButtonRepeatEnabled == isEnabled:
            return

        self._scrollButtonRepeatEnabled = isEnabled
        self.upButton.setAutoRepeat(isEnabled)
        self.downButton.setAutoRepeat(isEnabled)

    def _scrollWithAnimation(self, index: int):
        """ 滚动 使用 adaptive 动画 """
        t = QTime.currentTime()
        elapsed = self._lastScrollTime.msecsTo(t)
        self._lastScrollTime = t

        # fast linear 动画 用于 rapid repeat, smooth 用于 single 点击
        if (self.upButton.isDown() or self.downButton.isDown()) and elapsed < 200:
            duration, easing = 100, QEasingCurve.Linear
        else:
            duration, easing = 250, QEasingCurve.OutQuad

        self.vScrollBar.setScrollAnimation(duration, easing)
        self.setCurrentIndex(index)
        self.scrollToItem(self.currentItem())

    def scrollDown(self):
        """ 滚动 down 项 """
        self._scrollWithAnimation(self.currentIndex() + 1)

    def scrollUp(self):
        """ 滚动 up 项 """
        self._scrollWithAnimation(self.currentIndex() - 1)

    def _setButtonsVisible(self, visible: bool):
        """ 设置 滚动 按钮 可见性 """
        self.upButton.setVisible(visible)
        self.downButton.setVisible(visible)

    def enterEvent(self, e):
        self._setButtonsVisible(True)

    def leaveEvent(self, e):
        self._setButtonsVisible(False)

    def resizeEvent(self, e):
        w, h = self.width(), 34
        self.upButton.resize(w, h)
        self.downButton.resize(w, h)
        self.downButton.move(0, self.height() - h)

    def eventFilter(self, obj, e: QEvent):
        if obj is not self or e.type() != QEvent.KeyPress:
            return super().eventFilter(obj, e)

        if e.key() == Qt.Key_Down:
            self.scrollDown()
            return True
        elif e.key() == Qt.Key_Up:
            self.scrollUp()
            return True

        return super().eventFilter(obj, e)

    def currentItem(self):
        return self.item(self.currentIndex())

    def currentIndex(self):
        return self._currentIndex

    def setCurrentIndex(self, index: int):
        if not self.isCycle:
            n = self.visibleNumber // 2
            self._currentIndex = max(
                n, min(n + len(self.originItems) - 1, index))
        else:
            N = self.count() // 2
            m = (self.visibleNumber + 1) // 2
            self._currentIndex = index

            # 滚动 到 center 到 achieve circular scrolling
            if index >= self.count() - m:
                self._currentIndex = N + index - self.count()
                super().scrollToItem(self.item(self.currentIndex() - 1), self.ScrollHint.PositionAtCenter)
            elif index <= m - 1:
                self._currentIndex = N + index
                super().scrollToItem(self.item(N + index + 1), self.ScrollHint.PositionAtCenter)
