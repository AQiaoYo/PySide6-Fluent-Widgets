# coding: utf-8
"""带数值气泡提示的滑动条组件

提供在拖拽或悬停时于手柄上方显示当前数值气泡的滑动条控件,
适用于需要精确反馈当前值的音量、亮度、进度等调节场景
"""

from typing import Callable

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtWidgets import QWidget

from ...common.overload import singledispatchmethod
from .slider import Slider
from .tool_tip import ToolTip


class ToolTipSlider(Slider):
    """带数值气泡提示的滑动条, 使用方式与 Slider 完全相同

    在鼠标悬停手柄或拖拽时, 于手柄上方显示当前数值的浮动气泡提示,
    适用于音量调节、亮度控制、进度选择等需要精确数值反馈的场景

    构造函数重载:
        * ToolTipSlider(parent: QWidget = None)
        * ToolTipSlider(orient: Qt.Orientation, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化带气泡提示的滑动条

        Args:
            parent: 父级 QWidget 实例, 默认为 None
        """
        super().__init__(parent)
        self._postTooltipInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        super().__init__(orientation, parent=parent)
        self._postTooltipInit()

    def _postTooltipInit(self):
        """初始化气泡相关状态"""
        self._formatter: Callable[[float], str] = lambda v: f"{v:.1f}"
        self._isDragging = False
        self._isHandleHovered = False

        # Reuse ToolTip directly — inherits shadow, animation, theme switching for free
        self._tooltip = ToolTip()
        self._tooltip.setDuration(-1)  # Never auto-hide

        self.handle.pressed.connect(self._onHandlePressed)
        self.handle.released.connect(self._onHandleReleased)
        self.handle.installEventFilter(self)
        self.valueChanged.connect(self._onValueChanged)

    def setValueFormatter(self, func: Callable[[float], str]):
        """设置数值格式化函数

        Args:
            func: 接受当前数值并返回显示字符串的可调用对象,
                  默认为 lambda v: f"{v:.1f}"
        """
        self._formatter = func
        self._updateTooltipText()

    def _tooltipGlobalPos(self) -> QPoint:
        """计算气泡在屏幕上的全局坐标 (手柄正上方居中)"""
        handle = self.handle
        handleCenter = self.mapToGlobal(
            QPoint(handle.x() + handle.width() // 2, handle.y())
        )
        tw = self._tooltip.width()
        th = self._tooltip.height()
        x = handleCenter.x() - tw // 2
        y = handleCenter.y() - th
        return QPoint(x, y)

    def _updateTooltipText(self):
        self._tooltip.setText(self._formatter(self.value()))

    def _updateTooltipPos(self):
        self._tooltip.move(self._tooltipGlobalPos())

    def _showTooltip(self):
        self._updateTooltipText()
        self._updateTooltipPos()
        self._tooltip.show()

    def _hideTooltip(self):
        if not self._isDragging and not self._isHandleHovered:
            self._tooltip.hide()

    def _onHandlePressed(self):
        self._isDragging = True
        self._showTooltip()

    def _onHandleReleased(self):
        self._isDragging = False
        self._hideTooltip()

    def _onValueChanged(self, value: int):
        if self._tooltip.isVisible():
            self._updateTooltipText()
            self._updateTooltipPos()

    def eventFilter(self, obj, e):
        if obj is self.handle:
            if e.type() == QEvent.Enter:
                self._isHandleHovered = True
                self._showTooltip()
            elif e.type() == QEvent.Leave:
                self._isHandleHovered = False
                self._hideTooltip()

        return super().eventFilter(obj, e)

    def mousePressEvent(self, e):
        """点击槽道时也触发气泡显示"""
        super().mousePressEvent(e)
        self._isDragging = True
        self._showTooltip()

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)
        if self._isDragging:
            self._updateTooltipText()
            self._updateTooltipPos()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._isDragging = False
        self._hideTooltip()

    def hideEvent(self, e):
        self._tooltip.hide()
        super().hideEvent(e)

    def closeEvent(self, e):
        self._tooltip.hide()
        super().closeEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._tooltip.isVisible():
            self._updateTooltipPos()
