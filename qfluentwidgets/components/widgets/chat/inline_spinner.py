# coding: utf-8
"""内联微型转圈组件 (InlineSpinner)

12-16px 的极小 spinner, 用于工具卡片标题、消息流内文字旁边等需要
内联 loading 指示的场景. 比 IndeterminateProgressRing 更轻量,
不继承 QProgressBar, 纯 QPainter 绘制 + QPropertyAnimation 驱动旋转.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QPropertyAnimation, QSequentialAnimationGroup, Qt,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ....common.style_sheet import isDarkTheme, themeColor


__all__ = ['InlineSpinner']


class InlineSpinner(QWidget):
    """内联微型 spinner (12-16px)

    纯绘制实现, 不继承 QProgressBar. 通过 QPropertyAnimation 驱动
    startAngle 旋转 + spanAngle 伸缩, 视觉效果与 IndeterminateProgressRing 一致.

    构造函数:
        InlineSpinner(size: int = 14, parent: QWidget = None, start: bool = True)
    """

    _STROKE_WIDTH = 2.0

    def __init__(self, size: int = 14, parent: Optional[QWidget] = None,
                 start: bool = True):
        """初始化

        Args:
            size: spinner 边长 (像素), 默认 14
            parent: 父级 QWidget
            start: 是否立即开始动画
        """
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._startAngle = 0
        self._spanAngle = 60

        # 动画: startAngle 持续旋转, spanAngle 伸缩
        self._startAni1 = QPropertyAnimation(self, b'startAngle', self)
        self._startAni1.setDuration(800)
        self._startAni1.setStartValue(0)
        self._startAni1.setEndValue(360)

        self._startAni2 = QPropertyAnimation(self, b'startAngle', self)
        self._startAni2.setDuration(800)
        self._startAni2.setStartValue(360)
        self._startAni2.setEndValue(720)

        self._spanAni1 = QPropertyAnimation(self, b'spanAngle', self)
        self._spanAni1.setDuration(800)
        self._spanAni1.setStartValue(30)
        self._spanAni1.setEndValue(150)

        self._spanAni2 = QPropertyAnimation(self, b'spanAngle', self)
        self._spanAni2.setDuration(800)
        self._spanAni2.setStartValue(150)
        self._spanAni2.setEndValue(30)

        from PySide6.QtCore import QParallelAnimationGroup
        self._startGroup = QSequentialAnimationGroup(self)
        self._startGroup.addAnimation(self._startAni1)
        self._startGroup.addAnimation(self._startAni2)

        self._spanGroup = QSequentialAnimationGroup(self)
        self._spanGroup.addAnimation(self._spanAni1)
        self._spanGroup.addAnimation(self._spanAni2)

        self._aniGroup = QParallelAnimationGroup(self)
        self._aniGroup.addAnimation(self._startGroup)
        self._aniGroup.addAnimation(self._spanGroup)
        self._aniGroup.setLoopCount(-1)

        if start:
            self.start()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """开始旋转动画."""
        self._aniGroup.start()

    def stop(self) -> None:
        """停止旋转动画."""
        self._aniGroup.stop()

    def isRunning(self) -> bool:
        """动画是否正在运行."""
        from PySide6.QtCore import QAbstractAnimation
        return self._aniGroup.state() == QAbstractAnimation.State.Running

    # ------------------------------------------------------------------
    # Properties (动画驱动)
    # ------------------------------------------------------------------

    def _getStartAngle(self) -> int:
        return self._startAngle

    def _setStartAngle(self, v: int) -> None:
        self._startAngle = v
        self.update()

    def _getSpanAngle(self) -> int:
        return self._spanAngle

    def _setSpanAngle(self, v: int) -> None:
        self._spanAngle = v
        self.update()

    startAngle = Property(int, _getStartAngle, _setStartAngle)
    spanAngle = Property(int, _getSpanAngle, _setSpanAngle)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        sw = self._STROKE_WIDTH
        from PySide6.QtCore import QRectF
        rect = QRectF(sw / 2, sw / 2, self._size - sw, self._size - sw)

        # 前景弧: 主题色
        color = themeColor()
        pen = QPen(color, sw)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Qt drawArc: angle 单位是 1/16 度, 从 3 点钟方向逆时针
        start = self._startAngle * 16
        span = self._spanAngle * 16
        painter.drawArc(rect, start, span)
