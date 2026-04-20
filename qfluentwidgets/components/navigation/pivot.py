# coding: utf-8
"""提供 Pivot 导航组件，用于在同一页面内切换不同内容面板

Pivot 适用于需要在有限空间内组织多个关联视图的界面，例如设置页分类、文档章节切换等场景
相比 SegmentedControl，Pivot 通常与堆叠面板（QStackedWidget）配合使用，导航项呈水平排列
通过底部滑块指示当前选中项，支持鼠标点击和程序代码切换激活项
"""

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
    """Pivot 导航项，表示单个可切换的选项标签
    
    每个 PivotItem 对应一个具体视图或页面，通常通过 addItem 方法添加到 Pivot 导航栏中
    用于显示文本标签及可选图标，点击后会触发 Pivot 的当前选中项切换
    """

    itemClicked = Signal(bool)

    def _postInit(self):
        self.isSelected = False
        self.setProperty('isSelected', False)
        self.clicked.connect(lambda: self.itemClicked.emit(True))
        self.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        FluentStyleSheet.PIVOT.apply(self)
        setFont(self, 18)

    def setSelected(self, isSelected: bool):
        """设置选中状态

        Args:
            isSelected: 是否选中
        """
        if self.isSelected == isSelected:
            return

        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())
        self.update()


class Pivot(QWidget):
    """Pivot 导航栏，提供一组水平排列的可切换导航项
    
    常用于页面顶部的二级导航或内容分类切换，配合 QStackedWidget 可实现多面板内容的管理
    支持动态添加、删除导航项，当前选中项通过底部滑块高亮显示，切换时自动播放滑动动画
    """

    currentItemChanged = Signal(str)

    def __init__(self, parent=None):
        """初始化 Pivot 导航栏

        Args:
            parent: 父部件
        """
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
        """添加导航项

        Args:
            routeKey: 导航项的唯一标识
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            icon: 导航项图标
        """
        return self.insertItem(-1, routeKey, text, onClick, icon)

    def addWidget(self, routeKey: str, widget: PivotItem, onClick=None):
        """添加导航部件

        Args:
            routeKey: 导航项的唯一标识
            widget: 导航部件
            onClick: 连接到点击信号的槽函数
        """
        self.insertWidget(-1, routeKey, widget, onClick)

    def insertItem(self, index: int, routeKey: str, text: str, onClick=None, icon=None):
        """插入导航项

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            text: 导航项文本
            onClick: 连接到点击信号的槽函数
            icon: 导航项图标
        """
        if routeKey in self.items:
            return

        item = PivotItem(text, self)
        if icon:
            item.setIcon(icon)

        self.insertWidget(index, routeKey, item, onClick)
        return item

    def insertWidget(self, index: int, routeKey: str, widget: PivotItem, onClick=None):
        """插入导航部件

        Args:
            index: 插入位置
            routeKey: 导航项的唯一标识
            widget: 导航部件
            onClick: 连接到点击信号的槽函数
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
        """移除导航部件

        Args:
            routeKey: 导航项的唯一标识
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
        """清空所有导航项"""
        for k, w in self.items.items():
            self.hBoxLayout.removeWidget(w)
            qrouter.remove(k)
            w.deleteLater()

        self.items.clear()
        self._currentRouteKey = None

    def currentItem(self):
        """获取当前选中项

        Returns:
            当前选中的 PivotItem，如果没有则返回 None
        """
        if self._currentRouteKey is None:
            return None

        return self.widget(self._currentRouteKey)

    def currentRouteKey(self):
        """获取当前路由键

        Returns:
            当前选中项的路由键
        """
        return self._currentRouteKey

    def setCurrentItem(self, routeKey: str):
        """设置当前选中项

        Args:
            routeKey: 导航项的唯一标识
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
        """设置指示器长度

        Args:
            len: 指示器长度
        """
        self._indicatorLength = len
        self._adjustIndicatorPos()

    def indicatorLength(self):
        """获取指示器长度

        Returns:
            指示器长度
        """
        return self._indicatorLength

    def setItemFontSize(self, size: int):
        """设置导航项字体大小

        Args:
            size: 字体像素大小
        """
        for item in self.items.values():
            font = item.font()
            font.setPixelSize(size)
            item.setFont(font)
            item.adjustSize()

    def setItemText(self, routeKey: str, text: str):
        """设置导航项文本

        Args:
            routeKey: 导航项的唯一标识
            text: 导航项文本
        """
        item = self.widget(routeKey)
        item.setText(text)

    def setIndicatorColor(self, light, dark):
        """设置指示器颜色

        Args:
            light: 浅色模式下的颜色
            dark: 深色模式下的颜色
        """
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()

    def _onItemClicked(self):
        item = self.sender()  # type: PivotItem
        self.setCurrentItem(item.property('routeKey'))

    def widget(self, routeKey: str):
        """获取导航项部件

        Args:
            routeKey: 导航项的唯一标识

        Returns:
            对应的 PivotItem 部件

        Raises:
            RouteKeyError: 路由键不存在时抛出
        """
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
        """获取当前指示器几何形状

        Returns:
            当前指示器的 QRectF 几何区域
        """
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