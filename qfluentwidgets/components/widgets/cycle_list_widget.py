# coding: utf-8
"""循环列表部件"""

from typing import Iterable

from PySide6.QtCore import Qt, Signal, QSize, QEvent, QRectF, QEasingCurve, QTime
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QToolButton

from .scroll_area import SmoothScrollBar
from ...common.icon import FluentIcon, isDarkTheme


class ScrollButton(QToolButton):
    """滚动按钮"""

    def __init__(self, icon: FluentIcon, parent=None):
        """初始化滚动按钮

        Args:
            icon: 按钮图标
            parent: 父部件，默认为 None
        """
        super().__init__(parent=parent)
        self._icon = icon
        self.isPressed = False
        self.installEventFilter(self)

    def eventFilter(self, obj, e: QEvent):
        """事件过滤器，处理鼠标按下和释放事件

        Args:
            obj: 被监视的对象
            e: 事件对象

        Returns:
            是否已处理该事件
        """
        if obj is self:
            if e.type() == QEvent.MouseButtonPress:
                self.isPressed = True
                self.update()
            elif e.type() == QEvent.MouseButtonRelease:
                self.isPressed = False
                self.update()

        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        """绘制按钮图标

        Args:
            e: 绘制事件
        """
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
    """循环列表部件，支持通过上下按钮或键盘进行循环滚动选择"""

    currentItemChanged = Signal(QListWidgetItem)

    def __init__(self, items: Iterable, itemSize: QSize, align=Qt.AlignCenter, parent=None):
        """初始化循环列表部件

        Args:
            items: 要添加的项列表
            itemSize: 列表项的尺寸
            align: 项文本的对齐方式，默认为 Qt.AlignCenter
            parent: 父部件，默认为 None
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
        """设置列表中的项

        Args:
            items: 要添加的项列表
        """
        self.clear()
        self._createItems(items)

    def _createItems(self, items: list):
        """创建列表项，根据项数决定是否启用循环滚动

        Args:
            items: 项列表
        """
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
        """添加一列项到列表中

        Args:
            items: 要添加的项列表
            disabled: 是否禁用这些项，默认为 False
        """
        for i in items:
            item = QListWidgetItem(str(i), self)
            item.setSizeHint(self.itemSize)
            item.setTextAlignment(self.align | Qt.AlignVCenter)
            if disabled:
                item.setFlags(Qt.NoItemFlags)

            self.addItem(item)

    def _onItemClicked(self, item):
        """处理项点击事件，设置当前索引并滚动到该项

        Args:
            item: 被点击的项
        """
        self.setCurrentIndex(self.row(item))
        self.scrollToItem(self.currentItem())

    def setSelectedItem(self, text: str):
        """设置当前选中项

        Args:
            text: 要选中的项的文本
        """
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
        """滚动到指定项并将其置于中心位置

        Args:
            item: 要滚动到的项
            hint: 滚动提示，默认为 PositionAtCenter
        """
        # 滚动 到 center 位置
        index = self.row(item)
        y = item.sizeHint().height() * (index - self.visibleNumber // 2)
        self.vScrollBar.scrollTo(y)

        # 清空selection
        self.clearSelection()
        item.setSelected(False)

        self.currentItemChanged.emit(item)

    def wheelEvent(self, e):
        """处理鼠标滚轮事件

        Args:
            e: 滚轮事件
        """
        if e.angleDelta().y() < 0:
            self.scrollDown()
        else:
            self.scrollUp()

    def setScrollButtonRepeatEnabled(self, isEnabled: bool):
        """设置是否启用滚动按钮的自动重复功能

        Args:
            isEnabled: 是否启用自动重复
        """
        if self._scrollButtonRepeatEnabled == isEnabled:
            return

        self._scrollButtonRepeatEnabled = isEnabled
        self.upButton.setAutoRepeat(isEnabled)
        self.downButton.setAutoRepeat(isEnabled)

    def _scrollWithAnimation(self, index: int):
        """使用动画滚动到指定索引

        根据滚动频率自适应选择快速线性动画或平滑动画

        Args:
            index: 目标索引
        """
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
        """向下滚动一项"""
        self._scrollWithAnimation(self.currentIndex() + 1)

    def scrollUp(self):
        """向上滚动一项"""
        self._scrollWithAnimation(self.currentIndex() - 1)

    def _setButtonsVisible(self, visible: bool):
        """设置滚动按钮的可见性

        Args:
            visible: 是否可见
        """
        self.upButton.setVisible(visible)
        self.downButton.setVisible(visible)

    def enterEvent(self, e):
        """鼠标进入部件时显示滚动按钮

        Args:
            e: 进入事件
        """
        self._setButtonsVisible(True)

    def leaveEvent(self, e):
        """鼠标离开部件时隐藏滚动按钮

        Args:
            e: 离开事件
        """
        self._setButtonsVisible(False)

    def resizeEvent(self, e):
        """调整部件大小时更新滚动按钮的位置和尺寸

        Args:
            e: 尺寸调整事件
        """
        w, h = self.width(), 34
        self.upButton.resize(w, h)
        self.downButton.resize(w, h)
        self.downButton.move(0, self.height() - h)

    def eventFilter(self, obj, e: QEvent):
        """事件过滤器，处理上下方向键事件

        Args:
            obj: 被监视的对象
            e: 事件对象

        Returns:
            是否已处理该事件
        """
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
        """获取当前项

        Returns:
            当前选中的列表项
        """
        return self.item(self.currentIndex())

    def currentIndex(self):
        """获取当前索引

        Returns:
            当前项的索引
        """
        return self._currentIndex

    def setCurrentIndex(self, index: int):
        """设置当前索引，支持循环滚动边界处理

        Args:
            index: 目标索引
        """
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