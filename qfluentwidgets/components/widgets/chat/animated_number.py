# coding: utf-8
"""数字跳动动画组件 (AnimatedNumber)

显示一个数字, 当数值变化时以滚轮/插值动画过渡到新值.
适用于 token 计数、消息数等需要动态更新的数字展示.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, Qt,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget

from ....common.font import setFont
from ....common.style_sheet import isDarkTheme


__all__ = ['AnimatedNumber']


class AnimatedNumber(QWidget):
    """数字跳动动画组件

    数值变化时以 OutCubic 插值动画过渡, 视觉上数字平滑递增/递减.
    支持 k/M 单位自动格式化.

    构造函数:
        AnimatedNumber(parent: QWidget = None)
    """

    _DURATION = 300  # 动画时长 ms

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._value = 0.0       # 当前动画中间值 (float)
        self._targetValue = 0   # 目标整数值
        self._displayText = "0"
        self._useKFormat = True  # 是否用 k/M 格式化

        self._ani = QPropertyAnimation(self, b'animValue', self)
        self._ani.setDuration(self._DURATION)
        self._ani.setEasingCurve(QEasingCurve.Type.OutCubic)

        setFont(self)
        self.setFixedHeight(20)
        self.setMinimumWidth(30)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setValue(self, value: int, animated: bool = True) -> None:
        """设置目标数值.

        Args:
            value: 目标整数值
            animated: 是否动画过渡 (默认 True)
        """
        self._targetValue = value
        if not animated or not self.isVisible():
            self._value = float(value)
            self._refreshDisplay()
            self.update()
            return

        self._ani.stop()
        self._ani.setStartValue(self._value)
        self._ani.setEndValue(float(value))
        self._ani.start()

    def value(self) -> int:
        return self._targetValue

    def setUseKFormat(self, enabled: bool) -> None:
        """是否使用 k/M 格式化 (默认 True)."""
        self._useKFormat = enabled
        self._refreshDisplay()
        self.update()

    # ------------------------------------------------------------------
    # Property (动画驱动)
    # ------------------------------------------------------------------

    def _getAnimValue(self) -> float:
        return self._value

    def _setAnimValue(self, v: float) -> None:
        self._value = v
        self._refreshDisplay()
        self.update()

    animValue = Property(float, _getAnimValue, _setAnimValue)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        color = QColor(255, 255, 255, 220) if isDarkTheme() else QColor(0, 0, 0, 200)
        painter.setPen(color)
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self._displayText)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._displayText) + 4
        return QSize(max(30, w), 20)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _refreshDisplay(self) -> None:
        n = int(round(self._value))
        if self._useKFormat:
            self._displayText = self._fmt(n)
        else:
            self._displayText = str(n)
        # 动态调整宽度
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._displayText) + 4
        if self.width() < w:
            self.setMinimumWidth(w)

    @staticmethod
    def _fmt(n: int) -> str:
        if abs(n) >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if abs(n) >= 1000:
            return f"{n / 1000:.1f}k"
        return str(n)
