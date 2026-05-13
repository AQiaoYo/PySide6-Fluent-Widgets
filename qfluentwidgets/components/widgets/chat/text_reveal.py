# coding: utf-8
"""逐字淡入动画组件 (TextReveal)

文字逐字符从透明淡入到完全可见, 模拟打字机效果但更柔和.
适用于 Agent 回复的首行标题、状态文字等.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, Qt, QTimer,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget

from ....common.font import setFont
from ....common.style_sheet import isDarkTheme


__all__ = ['TextReveal']


class TextReveal(QWidget):
    """逐字淡入动画组件

    设置文字后调用 start(), 文字会逐字符从透明淡入.
    每个字符有独立的 opacity 过渡, 整体呈现波浪式淡入效果.

    构造函数:
        TextReveal(text: str = "", parent: QWidget = None)
    """

    _CHAR_DURATION = 80   # 每个字符的淡入时长 ms
    _CHAR_DELAY = 30      # 字符之间的延迟 ms

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._text = text
        self._revealCount = len(text)  # 已显示的字符数 (动画驱动)
        self._running = False

        self._ani = QPropertyAnimation(self, b'revealCount', self)
        self._ani.setEasingCurve(QEasingCurve.Type.Linear)

        setFont(self)
        self.setFixedHeight(20)
        self._adjustWidth()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setText(self, text: str) -> None:
        self._text = text
        self._revealCount = len(text)
        self._adjustWidth()
        self.update()

    def text(self) -> str:
        return self._text

    def start(self) -> None:
        """开始逐字淡入动画."""
        if not self._text:
            return
        self._running = True
        self._revealCount = 0
        total_duration = len(self._text) * self._CHAR_DELAY + self._CHAR_DURATION
        self._ani.stop()
        self._ani.setDuration(total_duration)
        self._ani.setStartValue(0)
        self._ani.setEndValue(len(self._text))
        self._ani.start()

    def stop(self) -> None:
        """停止动画, 立即显示全部文字."""
        self._running = False
        self._ani.stop()
        self._revealCount = len(self._text)
        self.update()

    def isRunning(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------

    def _getRevealCount(self) -> int:
        return self._revealCount

    def _setRevealCount(self, v: int) -> None:
        self._revealCount = min(v, len(self._text))
        self.update()

    revealCount = Property(int, _getRevealCount, _setRevealCount)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        isDark = isDarkTheme()
        baseColor = QColor(255, 255, 255) if isDark else QColor(0, 0, 0)

        fm = QFontMetrics(self.font())
        x = 0
        y_center = self.height() // 2 + fm.ascent() // 2

        for i, ch in enumerate(self._text):
            if i < self._revealCount:
                alpha = 220
            else:
                alpha = 0
            color = QColor(baseColor.red(), baseColor.green(), baseColor.blue(), alpha)
            painter.setPen(color)
            painter.drawText(x, y_center, ch)
            x += fm.horizontalAdvance(ch)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._text) + 4
        return QSize(max(40, w), 20)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _adjustWidth(self) -> None:
        fm = QFontMetrics(self.font())
        w = fm.horizontalAdvance(self._text) + 8
        self.setMinimumWidth(max(40, w))
