# coding: utf-8
"""双手柄范围滑动条组件

提供水平/垂直方向的双手柄滑动条控件, 允许用户通过拖拽两个手柄分别设置
范围的低端值和高端值. 手柄悬停或拖拽时在手柄上方(水平)或左侧(垂直)
显示数值气泡, 气泡复用 ToolTip 以获得阴影、淡入动画和主题自适应能力.
"""

from typing import Callable, Optional

from PySide6.QtCore import (
    QEvent, QPoint, QRectF, Qt, Signal,
)
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QWidget

from ...common.color import autoFallbackThemeColor
from ...common.overload import singledispatchmethod
from ...common.style_sheet import FluentStyleSheet, isDarkTheme
from .slider import SliderHandle
from .tool_tip import ToolTip


__all__ = ['RangeSlider']


class RangeSlider(QWidget):
    """水平/垂直双手柄范围滑动条

    通过拖拽低端手柄和高端手柄分别设置范围的最小值和最大值端点.
    手柄悬停或拖拽时在手柄上方(水平方向)或手柄左侧(垂直方向)显示数值气泡.

    信号:
        rangeChanged(int, int): 低值或高值发生变化时发出 (低值, 高值)
        lowValueChanged(int):   低端手柄值变化时发出
        highValueChanged(int):  高端手柄值变化时发出

    构造函数重载:
        * RangeSlider(parent: QWidget = None)
        * RangeSlider(orientation: Qt.Orientation, parent: QWidget = None)
    """

    rangeChanged = Signal(int, int)
    lowValueChanged = Signal(int)
    highValueChanged = Signal(int)

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化水平方向的范围滑动条

        Args:
            parent: 父级 QWidget 实例, 默认为 None
        """
        super().__init__(parent)
        self._postInit(Qt.Orientation.Horizontal)

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent: QWidget = None):
        """初始化指定方向的范围滑动条

        Args:
            orientation: Qt.Orientation.Horizontal 或 Qt.Orientation.Vertical
            parent:      父级 QWidget 实例, 默认为 None
        """
        super().__init__(parent)
        self._postInit(orientation)

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _postInit(self, orientation: Qt.Orientation):
        """完成初始化

        Args:
            orientation: 滑动条方向
        """
        self._orientation = orientation
        self._minimum = 0
        self._maximum = 100
        self._lowValue = 20
        self._highValue = 80

        # 自定义主题色（空 QColor 表示使用全局主题色）
        self._lightGrooveColor = QColor()
        self._darkGrooveColor = QColor()

        # 格式化函数
        self._formatter: Callable[[float], str] = lambda v: f"{v:.1f}"

        # 拖拽状态
        self._dragging: Optional[str] = None   # 'low' | 'high' | None
        self._dragOffset = 0

        # 悬停状态
        self._hoveredHandle: Optional[str] = None  # 'low' | 'high' | None

        # 创建两个手柄（复用 SliderHandle 的动画逻辑）
        self._lowHandle = SliderHandle(self)
        self._highHandle = SliderHandle(self)

        # 连接手柄信号
        self._lowHandle.pressed.connect(lambda: self._onHandlePressed('low'))
        self._lowHandle.released.connect(lambda: self._onHandleReleased('low'))
        self._highHandle.pressed.connect(lambda: self._onHandlePressed('high'))
        self._highHandle.released.connect(lambda: self._onHandleReleased('high'))

        # 安装事件过滤器以捕获手柄的 Enter/Leave 事件
        self._lowHandle.installEventFilter(self)
        self._highHandle.installEventFilter(self)

        # 创建两个气泡（复用 ToolTip）
        self._lowTooltip = ToolTip()
        self._lowTooltip.setDuration(-1)
        self._highTooltip = ToolTip()
        self._highTooltip.setDuration(-1)

        # 设置最小尺寸并调整方向
        self._applyOrientation()

        # 应用 QSS
        FluentStyleSheet.RANGE_SLIDER.apply(self)

        # 初始布局手柄
        self._adjustHandlePositions()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def setRange(self, minimum: int, maximum: int):
        """设置允许的数值范围

        Args:
            minimum: 最小值
            maximum: 最大值 (必须 >= minimum)
        """
        if maximum < minimum:
            maximum = minimum
        self._minimum = minimum
        self._maximum = maximum
        # 将当前值夹紧到新范围
        self._lowValue = max(minimum, min(self._lowValue, maximum))
        self._highValue = max(minimum, min(self._highValue, maximum))
        if self._lowValue > self._highValue:
            self._lowValue = self._highValue
        self._adjustHandlePositions()
        self.update()

    def setLowValue(self, value: int):
        """设置低端手柄的值

        Args:
            value: 新的低端值, 会被夹紧到 [minimum, highValue]
        """
        value = max(self._minimum, min(value, self._highValue))
        if value == self._lowValue:
            return
        self._lowValue = value
        self._adjustHandlePositions()
        self.update()
        self.lowValueChanged.emit(value)
        self.rangeChanged.emit(self._lowValue, self._highValue)

    def setHighValue(self, value: int):
        """设置高端手柄的值

        Args:
            value: 新的高端值, 会被夹紧到 [lowValue, maximum]
        """
        value = max(self._lowValue, min(value, self._maximum))
        if value == self._highValue:
            return
        self._highValue = value
        self._adjustHandlePositions()
        self.update()
        self.highValueChanged.emit(value)
        self.rangeChanged.emit(self._lowValue, self._highValue)

    def lowValue(self) -> int:
        """返回低端手柄的当前值"""
        return self._lowValue

    def highValue(self) -> int:
        """返回高端手柄的当前值"""
        return self._highValue

    def minimum(self) -> int:
        """返回允许的最小值"""
        return self._minimum

    def maximum(self) -> int:
        """返回允许的最大值"""
        return self._maximum

    def setOrientation(self, orientation: Qt.Orientation):
        """切换滑动条方向

        Args:
            orientation: Qt.Orientation.Horizontal 或 Qt.Orientation.Vertical
        """
        if orientation == self._orientation:
            return
        self._orientation = orientation
        self._applyOrientation()
        self._adjustHandlePositions()
        self.update()

    def orientation(self) -> Qt.Orientation:
        """返回当前方向"""
        return self._orientation

    def setValueFormatter(self, func: Callable[[float], str]):
        """设置数值格式化函数

        Args:
            func: 接受当前数值并返回显示字符串的可调用对象,
                  默认为 lambda v: f"{v:.1f}"
        """
        self._formatter = func

    def setThemeColor(self, light, dark):
        """设置自定义主题色

        Args:
            light: 亮色模式下的选中区域颜色 (QColor | str | Qt.GlobalColor)
            dark:  暗色模式下的选中区域颜色 (QColor | str | Qt.GlobalColor)
        """
        self._lightGrooveColor = QColor(light)
        self._darkGrooveColor = QColor(dark)
        self._lowHandle.setHandleColor(light, dark)
        self._highHandle.setHandleColor(light, dark)
        self.update()

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _applyOrientation(self):
        """根据方向设置最小尺寸"""
        hw = self._lowHandle.width()   # 22px
        if self._orientation == Qt.Orientation.Horizontal:
            self.setMinimumSize(hw * 2 + 10, hw)
        else:
            self.setMinimumSize(hw, hw * 2 + 10)

    @property
    def _grooveLength(self) -> int:
        """槽道有效长度（总长度减去一个手柄宽度，使手柄中心对齐端点）"""
        hw = self._lowHandle.width()
        if self._orientation == Qt.Orientation.Horizontal:
            return max(self.width() - hw, 1)
        return max(self.height() - hw, 1)

    def _valueToPos(self, value: int) -> int:
        """将数值转换为手柄左上角坐标（沿主轴方向）

        Args:
            value: 要转换的数值

        Returns:
            int: 手柄左上角在主轴方向上的像素坐标
        """
        span = max(self._maximum - self._minimum, 1)
        ratio = (value - self._minimum) / span
        return int(ratio * self._grooveLength)

    def _posToValue(self, pos: int) -> int:
        """将像素坐标转换为数值

        Args:
            pos: 鼠标在主轴方向上的像素坐标

        Returns:
            int: 对应的数值, 已夹紧到 [minimum, maximum]
        """
        hw = self._lowHandle.width()
        gl = self._grooveLength
        ratio = (pos - hw / 2) / gl
        value = ratio * (self._maximum - self._minimum) + self._minimum
        return int(max(self._minimum, min(self._maximum, round(value))))

    def _adjustHandlePositions(self):
        """根据当前低值/高值重新定位两个手柄"""
        hw = self._lowHandle.width()
        lp = self._valueToPos(self._lowValue)
        hp = self._valueToPos(self._highValue)

        if self._orientation == Qt.Orientation.Horizontal:
            self._lowHandle.move(lp, 0)
            self._highHandle.move(hp, 0)
        else:
            self._lowHandle.move(0, lp)
            self._highHandle.move(0, hp)

    def _nearestHandle(self, pos: QPoint) -> str:
        """返回距离点击位置最近的手柄标识

        Args:
            pos: 鼠标点击位置（控件坐标系）

        Returns:
            str: 'low' 或 'high'
        """
        if self._orientation == Qt.Orientation.Horizontal:
            coord = pos.x()
            lc = self._lowHandle.x() + self._lowHandle.width() // 2
            hc = self._highHandle.x() + self._highHandle.width() // 2
        else:
            coord = pos.y()
            lc = self._lowHandle.y() + self._lowHandle.height() // 2
            hc = self._highHandle.y() + self._highHandle.height() // 2

        return 'low' if abs(coord - lc) <= abs(coord - hc) else 'high'

    # ------------------------------------------------------------------
    # 气泡管理
    # ------------------------------------------------------------------

    def _tooltipGlobalPos(self, which: str) -> QPoint:
        """计算指定手柄气泡的全局坐标

        Args:
            which: 'low' 或 'high'

        Returns:
            QPoint: 气泡左上角的全局坐标
        """
        handle = self._lowHandle if which == 'low' else self._highHandle
        tooltip = self._lowTooltip if which == 'low' else self._highTooltip

        if self._orientation == Qt.Orientation.Horizontal:
            # 手柄正上方居中
            center = self.mapToGlobal(
                QPoint(handle.x() + handle.width() // 2, handle.y())
            )
            x = center.x() - tooltip.width() // 2
            y = center.y() - tooltip.height()
        else:
            # 手柄正左侧居中
            center = self.mapToGlobal(
                QPoint(handle.x(), handle.y() + handle.height() // 2)
            )
            x = center.x() - tooltip.width()
            y = center.y() - tooltip.height() // 2

        return QPoint(x, y)

    def _updateTooltip(self, which: str):
        """更新指定手柄气泡的文本和位置

        Args:
            which: 'low' 或 'high'
        """
        value = self._lowValue if which == 'low' else self._highValue
        tooltip = self._lowTooltip if which == 'low' else self._highTooltip
        tooltip.setText(self._formatter(value))
        tooltip.move(self._tooltipGlobalPos(which))

    def _showTooltip(self, which: str):
        """显示指定手柄的气泡

        Args:
            which: 'low' 或 'high'
        """
        self._updateTooltip(which)
        tooltip = self._lowTooltip if which == 'low' else self._highTooltip
        tooltip.show()

    def _hideTooltip(self, which: str):
        """在条件满足时隐藏指定手柄的气泡

        仅当该手柄既未被悬停也未在拖拽时才隐藏.

        Args:
            which: 'low' 或 'high'
        """
        is_dragging = self._dragging == which
        is_hovered = self._hoveredHandle == which
        if not is_dragging and not is_hovered:
            tooltip = self._lowTooltip if which == 'low' else self._highTooltip
            tooltip.hide()

    # ------------------------------------------------------------------
    # 手柄信号槽
    # ------------------------------------------------------------------

    def _onHandlePressed(self, which: str):
        """手柄被按下时开始拖拽并显示气泡

        Args:
            which: 'low' 或 'high'
        """
        self._dragging = which
        self._showTooltip(which)

    def _onHandleReleased(self, which: str):
        """手柄释放时结束拖拽并尝试隐藏气泡

        Args:
            which: 'low' 或 'high'
        """
        self._dragging = None
        self._hideTooltip(which)

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def eventFilter(self, obj, e: QEvent) -> bool:
        """拦截手柄的 Enter/Leave 事件以控制气泡显隐"""
        if obj is self._lowHandle:
            if e.type() == QEvent.Type.Enter:
                self._hoveredHandle = 'low'
                self._showTooltip('low')
            elif e.type() == QEvent.Type.Leave:
                self._hoveredHandle = None
                self._hideTooltip('low')
        elif obj is self._highHandle:
            if e.type() == QEvent.Type.Enter:
                self._hoveredHandle = 'high'
                self._showTooltip('high')
            elif e.type() == QEvent.Type.Leave:
                self._hoveredHandle = None
                self._hideTooltip('high')
        return super().eventFilter(obj, e)

    def mousePressEvent(self, e: QMouseEvent):
        """点击槽道空白区域时将最近的手柄移动到点击位置"""
        pos = e.pos()
        which = self._nearestHandle(pos)
        coord = pos.x() if self._orientation == Qt.Orientation.Horizontal else pos.y()
        value = self._posToValue(coord)

        if which == 'low':
            # 低值手柄不能超过高值手柄
            value = min(value, self._highValue)
            old = self._lowValue
            self._lowValue = value
            if value != old:
                self._adjustHandlePositions()
                self.update()
                self.lowValueChanged.emit(value)
                self.rangeChanged.emit(self._lowValue, self._highValue)
        else:
            # 高值手柄不能低于低值手柄
            value = max(value, self._lowValue)
            old = self._highValue
            self._highValue = value
            if value != old:
                self._adjustHandlePositions()
                self.update()
                self.highValueChanged.emit(value)
                self.rangeChanged.emit(self._lowValue, self._highValue)

        self._dragging = which
        self._showTooltip(which)

    def mouseMoveEvent(self, e: QMouseEvent):
        """拖拽时更新手柄位置和气泡"""
        if self._dragging is None:
            return

        coord = e.pos().x() if self._orientation == Qt.Orientation.Horizontal else e.pos().y()
        value = self._posToValue(coord)

        if self._dragging == 'low':
            value = max(self._minimum, min(value, self._highValue))
            old = self._lowValue
            self._lowValue = value
            if value != old:
                self._adjustHandlePositions()
                self.update()
                self.lowValueChanged.emit(value)
                self.rangeChanged.emit(self._lowValue, self._highValue)
        else:
            value = max(self._lowValue, min(value, self._maximum))
            old = self._highValue
            self._highValue = value
            if value != old:
                self._adjustHandlePositions()
                self.update()
                self.highValueChanged.emit(value)
                self.rangeChanged.emit(self._lowValue, self._highValue)

        self._updateTooltip(self._dragging)

    def mouseReleaseEvent(self, e: QMouseEvent):
        """释放鼠标时结束拖拽"""
        which = self._dragging
        self._dragging = None
        if which:
            self._hideTooltip(which)

    def resizeEvent(self, e):
        """窗口尺寸变化时重新定位手柄"""
        super().resizeEvent(e)
        self._adjustHandlePositions()
        # 如果气泡可见则同步更新位置
        if self._lowTooltip.isVisible():
            self._updateTooltip('low')
        if self._highTooltip.isVisible():
            self._updateTooltip('high')

    def hideEvent(self, e):
        """控件隐藏时同步隐藏气泡"""
        self._lowTooltip.hide()
        self._highTooltip.hide()
        super().hideEvent(e)

    def closeEvent(self, e):
        """控件关闭时同步隐藏气泡"""
        self._lowTooltip.hide()
        self._highTooltip.hide()
        super().closeEvent(e)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        """绘制槽道（灰色背景 + 主题色选中区域）"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        if self._orientation == Qt.Orientation.Horizontal:
            self._drawHorizontalGroove(painter)
        else:
            self._drawVerticalGroove(painter)

    def _drawHorizontalGroove(self, painter: QPainter):
        """绘制水平槽道

        Args:
            painter: QPainter 实例
        """
        w = self.width()
        hw = self._lowHandle.width()   # 22
        r = hw / 2                     # 11
        groove_y = r - 2               # 槽道顶部 y 坐标
        groove_h = 4

        # 灰色背景槽道（全长）
        painter.setBrush(
            QColor(255, 255, 255, 115) if isDarkTheme() else QColor(0, 0, 0, 100)
        )
        painter.drawRoundedRect(QRectF(r, groove_y, w - r * 2, groove_h), 2, 2)

        # 主题色选中区域（低值手柄中心到高值手柄中心）
        span = max(self._maximum - self._minimum, 1)
        lp = (self._lowValue - self._minimum) / span * (w - r * 2) + r
        hp = (self._highValue - self._minimum) / span * (w - r * 2) + r
        sel_w = hp - lp
        if sel_w > 0:
            painter.setBrush(
                autoFallbackThemeColor(self._lightGrooveColor, self._darkGrooveColor)
            )
            painter.drawRoundedRect(QRectF(lp, groove_y, sel_w, groove_h), 2, 2)

    def _drawVerticalGroove(self, painter: QPainter):
        """绘制垂直槽道

        Args:
            painter: QPainter 实例
        """
        h = self.height()
        hw = self._lowHandle.height()  # 22
        r = hw / 2                     # 11
        groove_x = r - 2               # 槽道左侧 x 坐标
        groove_w = 4

        # 灰色背景槽道（全长）
        painter.setBrush(
            QColor(255, 255, 255, 115) if isDarkTheme() else QColor(0, 0, 0, 100)
        )
        painter.drawRoundedRect(QRectF(groove_x, r, groove_w, h - r * 2), 2, 2)

        # 主题色选中区域（低值手柄中心到高值手柄中心）
        span = max(self._maximum - self._minimum, 1)
        lp = (self._lowValue - self._minimum) / span * (h - r * 2) + r
        hp = (self._highValue - self._minimum) / span * (h - r * 2) + r
        sel_h = hp - lp
        if sel_h > 0:
            painter.setBrush(
                autoFallbackThemeColor(self._lightGrooveColor, self._darkGrooveColor)
            )
            painter.drawRoundedRect(QRectF(groove_x, lp, groove_w, sel_h), 2, 2)
