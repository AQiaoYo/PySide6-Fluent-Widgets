# coding: utf-8
"""工具状态标题组件 (ToolStatusTitle)

显示工具调用的状态文字, 在 active/done 之间切换时有文字 morphing 过渡.
例如 "Reading file..." -> "Read file" 的平滑过渡.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, Qt, QTimer,
)
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget

from ....common.font import setFont
from ....common.style_sheet import isDarkTheme


__all__ = ['ToolStatusTitle']


class ToolStatusTitle(QWidget):
    """工具状态标题 (active/done morphing)

    设置 activeText 和 doneText, 通过 setActive(bool) 切换.
    切换时文字以淡入淡出过渡.

    构造函数:
        ToolStatusTitle(activeText: str = "", doneText: str = "", parent: QWidget = None)
    """

    _DURATION = 200  # 过渡时长 ms

    def __init__(self, activeText: str = "", doneText: str = "",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._activeText = activeText
        self._doneText = doneText
        self._isActive = True
        self._opacity = 1.0  # 当前文字 opacity (动画驱动)
        self._transitioning = False
        self._pendingActive: Optional[bool] = None

        self._fadeOutAni = QPropertyAnimation(self, b'textOpacity', self)
        self._fadeOutAni.setDuration(self._DURATION // 2)
        self._fadeOutAni.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fadeOutAni.setStartValue(1.0)
        self._fadeOutAni.setEndValue(0.0)
        self._fadeOutAni.finished.connect(self._onFadeOutDone)

        self._fadeInAni = QPropertyAnimation(self, b'textOpacity', self)
        self._fadeInAni.setDuration(self._DURATION // 2)
        self._fadeInAni.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fadeInAni.setStartValue(0.0)
        self._fadeInAni.setEndValue(1.0)
        self._fadeInAni.finished.connect(self._onFadeInDone)

        setFont(self)
        self.setFixedHeight(20)
        self._adjustWidth()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setActiveText(self, text: str) -> None:
        self._activeText = text
        self._adjustWidth()
        self.update()

    def setDoneText(self, text: str) -> None:
        self._doneText = text
        self._adjustWidth()
        self.update()

    def activeText(self) -> str:
        return self._activeText

    def doneText(self) -> str:
        return self._doneText

    def setActive(self, active: bool) -> None:
        """切换 active/done 状态 (带过渡动画).

        Args:
            active: True 显示 activeText, False 显示 doneText
        """
        if active == self._isActive and not self._transitioning:
            return
        if self._transitioning:
            # 排队
            self._pendingActive = active
            return
        self._transitioning = True
        self._pendingActive = active
        # 先淡出当前文字
        self._fadeOutAni.stop()
        self._fadeInAni.stop()
        self._fadeOutAni.start()

    def isActive(self) -> bool:
        return self._isActive

    def currentText(self) -> str:
        return self._activeText if self._isActive else self._doneText

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------

    def _getOpacity(self) -> float:
        return self._opacity

    def _setOpacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    textOpacity = Property(float, _getOpacity, _setOpacity)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        isDark = isDarkTheme()
        baseColor = QColor(255, 255, 255, 220) if isDark else QColor(0, 0, 0, 200)
        color = QColor(baseColor.red(), baseColor.green(), baseColor.blue(),
                       int(baseColor.alpha() * self._opacity))
        painter.setPen(color)

        text = self.currentText()
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         text)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        fm = QFontMetrics(self.font())
        w = max(fm.horizontalAdvance(self._activeText),
                fm.horizontalAdvance(self._doneText)) + 4
        return QSize(max(40, w), 20)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _onFadeOutDone(self) -> None:
        # 切换文字
        if self._pendingActive is not None:
            self._isActive = self._pendingActive
        # 淡入新文字
        self._fadeInAni.start()

    def _onFadeInDone(self) -> None:
        self._transitioning = False
        # 检查是否有排队的切换
        if self._pendingActive is not None and self._pendingActive != self._isActive:
            pending = self._pendingActive
            self._pendingActive = None
            self.setActive(pending)
        else:
            self._pendingActive = None

    def _adjustWidth(self) -> None:
        fm = QFontMetrics(self.font())
        w = max(fm.horizontalAdvance(self._activeText),
                fm.horizontalAdvance(self._doneText)) + 8
        self.setMinimumWidth(max(40, w))
