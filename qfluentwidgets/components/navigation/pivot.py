# coding: utf-8
from typing import Dict

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout, QSizePolicy

from ...common.font import setFont
from ...common.router import qrouter
from ...common.style_sheet import themeColor, FluentStyleSheet
from ...common.color import autoFallbackThemeColor
from ...common.animation import FluentAnimation, FluentAnimationType, FluentAnimationProperty, ScaleSlideAnimation
from ..widgets.button import PushButton
from .navigation_types import RouteKeyError


class PivotItem(PushButton):
    """ Pivot 项 """

    itemClicked = Signal(bool)

    def _postInit(self):
        self.isSelected = False
        self.setProperty('isSelected', False)
        self.clicked.connect(lambda: self.itemClicked.emit(True))
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        FluentStyleSheet.PIVOT.apply(self)
        setFont(self, 18)

    def setSelected(self, isSelected: bool):
        if self.isSelected == isSelected:
            return

        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())
        self.update()


class Pivot(QWidget):
    """ Pivot """

    currentItemChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = {}  # type: Dict[str, PivotItem]
        self._currentRouteKey = None
        self._indicatorLength = 16

        self.lightIndicatorColor = QColor()
        self.darkIndicatorColor = QColor()

        self.hBoxLayout = QHBoxLayout(self)
        self.slideAni = ScaleSlideAnimation(self)

        FluentStyleSheet.PIVOT.apply(self)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setAlignment(Qt.AlignLeft)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.slideAni.valueChanged.connect(lambda: self.update())

    def addItem(self, routeKey: str, text: str, onClick=None, icon=None):
        """ 添加 项

        参数
        ----------
        routeKey: str
            导航项的唯一标识.

        text: str
            导航项文本.

        onClick: callable
            连接到点击信号的槽函数.

        icon: str
            导航项图标.
        """
        return self.insertItem(-1, routeKey, text, onClick, icon)

    def addWidget(self, routeKey: str, widget: PivotItem, onClick=None):
        """添加部件.

        参数
        ----------
        routeKey: str
            导航项的唯一标识.

        widget: PivotItem
            导航部件.

        onClick: callable
            连接到点击信号的槽函数.
        """
        self.insertWidget(-1, routeKey, widget, onClick)

    def insertItem(self, index: int, routeKey: str, text: str, onClick=None, icon=None):
        """ 插入 项

        参数
        ----------
        index: int
            插入 位置

        routeKey: str
            导航项的唯一标识.

        text: str
            导航项文本.

        onClick: callable
            连接到点击信号的槽函数.

        icon: str
            导航项图标.
        """
        if routeKey in self.items:
            return

        item = PivotItem(text, self)
        if icon:
            item.setIcon(icon)

        self.insertWidget(index, routeKey, item, onClick)
        return item

    def insertWidget(self, index: int, routeKey: str, widget: PivotItem, onClick=None):
        """插入项.

        参数
        ----------
        index: int
            插入位置.

        routeKey: str
            导航项的唯一标识.

        widget: PivotItem
            导航部件.

        onClick: callable
            连接到点击信号的槽函数.
        """
        if routeKey in self.items:
            return

        widget.setProperty('routeKey', routeKey)
        widget.itemClicked.connect(self._onItemClicked)
        if onClick:
            widget.itemClicked.connect(onClick)

        self.items[routeKey] = widget
        self.hBoxLayout.insertWidget(index, widget, 1)

    def removeWidget(self, routeKey: str):
        """ 移除 部件

        参数
        ----------
        routeKey: str
            unique name 的 项
        """
        if routeKey not in self.items:
            return

        item = self.items.pop(routeKey)
        self.hBoxLayout.removeWidget(item)
        qrouter.remove(routeKey)
        item.deleteLater()

        if not self.items:
            self._currentRouteKey = None

    def clear(self):
        """清空所有导航项."""
        for k, w in self.items.items():
            self.hBoxLayout.removeWidget(w)
            qrouter.remove(k)
            w.deleteLater()

        self.items.clear()
        self._currentRouteKey = None

    def currentItem(self):
        """ 返回 当前 选中项 """
        if self._currentRouteKey is None:
            return None

        return self.widget(self._currentRouteKey)

    def currentRouteKey(self):
        return self._currentRouteKey

    def setCurrentItem(self, routeKey: str):
        """ 设置 当前 选中项

        参数
        ----------
        routeKey: str
            unique name 的 项
        """
        if routeKey not in self.items or routeKey == self.currentRouteKey():
            return

        self._adjustIndicatorPos()

        self._currentRouteKey = routeKey
        self.slideAni.startAnimation(self.currentIndicatorGeometry())

        for k, item in self.items.items():
            item.setSelected(k == routeKey)

        self.currentItemChanged.emit(routeKey)

    def showEvent(self, e):
        super().showEvent(e)
        self._adjustIndicatorPos()

    def setIndicatorLength(self, len: int):
        self._indicatorLength = len
        self._adjustIndicatorPos()

    def indicatorLength(self):
        return self._indicatorLength

    def setItemFontSize(self, size: int):
        """ 设置项的pixel font 大小 """
        for item in self.items.values():
            font = item.font()
            font.setPixelSize(size)
            item.setFont(font)
            item.adjustSize()

    def setItemText(self, routeKey: str, text: str):
        """ 设置项的文本 """
        item = self.widget(routeKey)
        item.setText(text)

    def setIndicatorColor(self, light, dark):
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()

    def _onItemClicked(self):
        item = self.sender()  # type: PivotItem
        self.setCurrentItem(item.property('routeKey'))

    def widget(self, routeKey: str):
        if routeKey not in self.items:
            raise RouteKeyError(f"`{routeKey}` is illegal.")

        return self.items[routeKey]

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._adjustIndicatorPos()

    def _adjustIndicatorPos(self):
        item = self.currentItem()
        if item:
            self.slideAni.stop()
            self.slideAni.setValue(self.currentIndicatorGeometry())

    def currentIndicatorGeometry(self):
        item = self.currentItem()
        if not item:
            return QRectF(0, self.height() - 3, self.indicatorLength(), 3)

        rect = item.geometry()
        return QRectF(rect.x() - 8 + rect.width() // 2, self.height() - 3, self.indicatorLength(), 3)

    def paintEvent(self, e):
        super().paintEvent(e)

        if not self.currentItem():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))
        painter.drawRoundedRect(self.slideAni.geometry, 1.5, 1.5)
