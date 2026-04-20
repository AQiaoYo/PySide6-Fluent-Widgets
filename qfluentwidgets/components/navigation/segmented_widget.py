# coding: utf-8
"""分段控件

提供一组用于在多个互斥选项中进行单选的 Segmented 控件，包括文本样式、工具样式和可切换工具样式，适用于导航栏或紧凑的工具切换场景
"""

from typing import Union
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QIcon, QColor
from PySide6.QtWidgets import QApplication, QWidget

from ...common.font import setFont
from ...common.icon import FluentIconBase, drawIcon, Theme
from ...common.color import autoFallbackThemeColor
from ...common.style_sheet import themeColor, FluentStyleSheet, isDarkTheme
from ...common.animation import FluentAnimation, FluentAnimationType, FluentAnimationProperty, ScaleSlideAnimation
from ..widgets.button import PushButton, ToolButton, TransparentToolButton
from .pivot import Pivot, PivotItem


class SegmentedItem(PivotItem):
    """Segmented 项
    
    用于 SegmentedWidget 的选项单元，通过文本标签展示选项内容，用户点击后切换选中状态
    """

    def _postInit(self):
        super()._postInit()
        setFont(self, 14)


class SegmentedToolItem(ToolButton):
    """Segmented tool 项
    
    用于 SegmentedToolWidget 的选项单元，以图标形式展示选项，适用于空间受限或更强调视觉识别的场景
    """

    itemClicked = Signal(bool)

    def _postInit(self):
        self.isSelected = False
        self.setProperty('isSelected', False)
        self.clicked.connect(lambda: self.itemClicked.emit(True))

        self.setFixedSize(38, 33)
        FluentStyleSheet.PIVOT.apply(self)

    def setSelected(self, isSelected: bool):
        if self.isSelected == isSelected:
            return

        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())
        self.update()


class SegmentedToggleToolItem(TransparentToolButton):
    """Segmented toggle tool 项
    
    用于 SegmentedToggleToolWidget 的选项单元，支持在选中与未选中状态间切换，常用于工具栏的开关型分段选择
    """

    itemClicked = Signal(bool)

    def _postInit(self):
        super()._postInit()
        self.isSelected = False

        self.setFixedSize(50, 32)
        self.clicked.connect(lambda: self.itemClicked.emit(True))

    def setSelected(self, isSelected: bool):
        if self.isSelected == isSelected:
            return

        self.isSelected = isSelected
        self.setChecked(isSelected)

    def _drawIcon(self, icon, painter: QPainter, rect: QRectF, state=QIcon.State.Off):
        if self.isSelected and isinstance(icon, FluentIconBase):
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            icon = icon.icon(theme)

        return drawIcon(icon, painter, rect, state)


class SegmentedWidget(Pivot):
    """Segmented 部件
    
    以文本标签形式展示多个互斥选项，同一时间仅允许选中一项，常用于视图切换、内容分类筛选等导航场景
    """

    def __init__(self, parent=None):
        """初始化 SegmentedWidget 实例
        
        Args:
            parent (QWidget, optional): 父控件，默认为 None，若为 None 则作为顶层窗口独立存在
        """
        super().__init__(parent)
        self.slideAni = FluentAnimation.create(
            FluentAnimationType.POINT_TO_POINT, FluentAnimationProperty.SCALE, value=0, parent=self)
        self.setAttribute(Qt.WA_StyledBackground)

    def insertItem(self, index: int, routeKey: str, text: str, onClick=None, icon=None):
        if routeKey in self.items:
            return

        item = SegmentedItem(text, self)
        if icon:
            item.setIcon(icon)

        self.insertWidget(index, routeKey, item, onClick)
        return item

    def paintEvent(self, e):
        QWidget.paintEvent(self, e)

        if not self.currentItem():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制背景
        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255, 14))
            painter.setBrush(QColor(255, 255, 255, 15))
        else:
            painter.setPen(QColor(0, 0, 0, 19))
            painter.setBrush(QColor(255, 255, 255, 179))

        item = self.currentItem()
        rect = item.rect().adjusted(1, 1, -1, -1).translated(int(self.slideAni.value()), 0)
        painter.drawRoundedRect(rect, 5, 5)

        # 绘制指示器
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))

        x = int(self.currentItem().width() / 2 - 8 + self.slideAni.value())
        painter.drawRoundedRect(QRectF(x, self.height() - 3.5, 16, 3), 1.5, 1.5)

    def currentIndicatorGeometry(self):
        return self.currentItem().x() if self.currentItem() else 0


class SegmentedToolWidget(SegmentedWidget):
    """Segmented tool 部件
    
    以图标形式展示多个互斥选项，外观更为紧凑，适用于工具栏或需要图标化导航的场景
    """

    def __init__(self, parent=None):
        """初始化 SegmentedToolWidget 实例
        
        Args:
            parent (QWidget, optional): 父控件，默认为 None，若为 None 则作为顶层窗口独立存在
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)

    def addItem(self, routeKey: str, icon: Union[str, QIcon, FluentIconBase], onClick=None):
        """添加项

        Args:
            routeKey: 项的唯一标识名
            icon: 导航项图标
            onClick: 点击信号触发的回调函数
        """
        return self.insertItem(-1, routeKey, icon, onClick)

    def insertItem(self, index: int, routeKey: str, icon: Union[str, QIcon, FluentIconBase], onClick=None):
        if routeKey in self.items:
            return

        item = self._createItem(icon)
        self.insertWidget(index, routeKey, item, onClick)
        return item

    def _createItem(self, icon):
        return SegmentedToolItem(icon)


class SegmentedToggleToolWidget(SegmentedToolWidget):
    """Segmented toggle tool 部件
    
    以图标形式展示选项并支持切换状态，可用于需要在选中与未选中之间切换的工具栏场景，如开关组合或模式切换
    """

    def _createItem(self, icon):
        return SegmentedToggleToolItem(icon)

    def paintEvent(self, e):
        QWidget.paintEvent(self, e)

        if not self.currentItem():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))

        item = self.currentItem()
        painter.drawRoundedRect(
            QRectF(self.slideAni.value(), 0, item.width(), item.height()), 4, 4)