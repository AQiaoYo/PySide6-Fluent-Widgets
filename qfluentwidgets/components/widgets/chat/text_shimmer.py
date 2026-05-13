# coding: utf-8
"""文字微光效果组件 (TextShimmer)

在文字上叠加一道从左到右扫过的高光, 表示"正在生成中".
适用于 GenerationStatusBar 的状态文字、工具卡片标题等.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, Qt,
)
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QLinearGradient, QPainter,
)
from PySide6.QtWidgets import QWidget

from ....common.font import setFont
from ....common.style_sheet import isDarkTheme


__all__ = ['TextShimmer']


class TextShimmer(QWidget):
    """文字微光效果组件

    显示一段文字, 上面有一道高光从左到右循环扫过.
    调用 start() 开始动画, stop() 停止 (文字保持显示, 高光消失).

    构造函数:
        TextShimmer(text: str = "", parent: QWidget = None)
    """

    _DURATION = 1500  # 一次扫过的时长 ms
    _SHIMMER_WIDTH_RATIO = 0.3  # 高光宽度占文字宽度的比例

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._text = text
        self._progress = 0.0  # 0.0 ~ 1.0, 高光位置
        self._running = False

        self._ani = QPropertyAnimation(self, b'shimmerProgress', self)
        self._ani.setDuration(self._DURATION)
        self._ani.setStartValue(0.0)
        self._ani.setEndValue(1.0)
        self._ani.setEasingCurve(QEasingCurve.Type.Linear)
        self._ani.setLoopCount(-1)

        setFont(self)
        self.setFixedHeight(20)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setText(self, text: str) -> None:
        self._text = text
        self._adjustWidth()
        self.update()

    def text(self) -> str:
        return self._text

    def start(self) -> None:
        """开始 shimmer 动画."""
        self._running = True
        self._ani.start()

    def stop(self) -> None:
        """停止 shimmer 动画 (文字保持显示)."""
        self._running = False
        self._ani.stop()
        self._progress = 0.0
        self.update()

    def isRunning(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------

    def _getProgress(self) -> float:
        return self._progress

    def _setProgress(self, v: float) -> None:
        self._progress = v
        self.update()

    shimmerProgress = Property(float, _getProgress, _setProgress)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        isDark = isDarkTheme()
        textColor = QColor(255, 255, 255, 200) if isDark else QColor(0, 0, 0, 180)

        if not self._running:
            # 静态文字
            painter.setPen(textColor)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             self._text)
            return

        # 绘制带 shimmer 的文字
        w = self.width()
        shimmerW = int(w * self._SHIMMER_WIDTH_RATIO)
        center = self._progress * (w + shimmerW) - shimmerW

        # 用 gradient 作为文字颜色
        gradient = QLinearGradient(center - shimmerW / 2, 0, center + shimmerW / 2, 0)
        highlightColor = QColor(255, 255, 255, 180) if isDark else QColor(0, 120, 212, 180)

        gradient.setColorAt(0.0, textColor)
        gradient.setColorAt(0.4, highlightColor)
        gradient.setColorAt(0.6, highlightColor)
        gradient.setColorAt(1.0, textColor)

        from PySide6.QtGui import QBrush, QPen
        pen = QPen(QBrush(gradient), 0)
        painter.setPen(pen)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self._text)

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
