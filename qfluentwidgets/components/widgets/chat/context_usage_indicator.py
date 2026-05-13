# coding: utf-8
"""上下文用量指示器 (ContextUsageIndicator)

一个 16*16 的微型圆环进度组件, 设计为嵌入 ChatInputEdit 内部
(放在 + 附件按钮旁边). 只显示圆环, 不显示文字.

交互:
- hover: ToolTip 显示 "45.0k / 200.0k tokens (22%)"
- click: 弹出 Flyout 详情面板, 含分类 breakdown + ProgressBar

颜色随占比变化: <70% 蓝, 70-90% 橙, >90% 红.

使用方式:
    indicator = ContextUsageIndicator(parent)
    indicator.setUsage(
        used_tokens=45000,
        max_tokens=200000,
        breakdown={"system": 5000, "user": 12000, "assistant": 20000, "tool": 8000}
    )
    # 嵌入 ChatInputEdit 时, 在 _repositionButtons 里定位它
"""

from typing import Dict, Optional

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.style_sheet import FluentStyleSheet
from ..flyout import Flyout, FlyoutAnimationType, FlyoutViewBase
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from ..progress_bar import ProgressBar
from ..tool_tip import ToolTipFilter, ToolTipPosition


__all__ = ['ContextUsageIndicator']


class _ContextUsageFlyoutView(FlyoutViewBase):
    """上下文用量详情 Flyout 视图.

    显示:
    - 总用量: "45.0k / 200.0k tokens" + ProgressBar
    - 分类明细: 每类一行 "system: 5.0k (11%)" + ProgressBar
    """

    _MIN_WIDTH = 260

    def __init__(self, used: int, max_tokens: int,
                 breakdown: Dict[str, int],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(self._MIN_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # 标题
        title = StrongBodyLabel(self.tr("上下文用量"), self)
        layout.addWidget(title)

        # 总用量
        total_text = f"{self._fmt(used)} / {self._fmt(max_tokens)} tokens"
        ratio = min(1.0, used / max(1, max_tokens))
        layout.addLayout(self._buildRow(total_text, ratio))

        # 分类明细
        if breakdown:
            layout.addWidget(CaptionLabel(self.tr("分类明细:"), self))
            for category, tokens in breakdown.items():
                pct = tokens / max(1, used) * 100
                label = f"{category}: {self._fmt(tokens)} ({pct:.0f}%)"
                cat_ratio = tokens / max(1, max_tokens)
                layout.addLayout(self._buildRow(label, cat_ratio))

    def _buildRow(self, label: str, ratio: float) -> QVBoxLayout:
        row = QVBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(3)

        lab = BodyLabel(label, self)
        row.addWidget(lab)

        bar = ProgressBar(self)
        bar.setFixedHeight(4)
        bar.setRange(0, 1000)
        bar.setValue(int(ratio * 1000))
        row.addWidget(bar)

        return row

    @staticmethod
    def _fmt(n: int) -> str:
        if n >= 1000:
            return f"{n / 1000:.1f}k"
        return str(n)


class ContextUsageIndicator(QWidget):
    """上下文用量指示器 (微型圆环, 16*16).

    Signals:
        clicked(): 用户点击时发出

    构造函数:
        ContextUsageIndicator(parent: QWidget = None)
    """

    clicked = Signal()

    _SIZE = 16
    _RING_WIDTH = 2.5

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("contextUsageIndicator")
        self.setFixedSize(self._SIZE, self._SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._ratio = 0.0
        self._usedTokens = 0
        self._maxTokens = 0
        self._breakdown: Dict[str, int] = {}

        self.installEventFilter(
            ToolTipFilter(self, showDelay=400, position=ToolTipPosition.TOP)
        )

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setUsage(self, used_tokens: int, max_tokens: int,
                 breakdown: Optional[Dict[str, int]] = None) -> None:
        """设置用量数据.

        Args:
            used_tokens: 已使用 token 数
            max_tokens:  最大 token 数 (上下文窗口)
            breakdown:   可选的分类明细
        """
        self._usedTokens = max(0, used_tokens)
        self._maxTokens = max(1, max_tokens)
        self._breakdown = breakdown or {}
        self._ratio = self._usedTokens / self._maxTokens
        self._updateTooltip()
        self.update()

    def usedTokens(self) -> int:
        return self._usedTokens

    def maxTokens(self) -> int:
        return self._maxTokens

    def breakdown(self) -> Dict[str, int]:
        return dict(self._breakdown)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(
            self._RING_WIDTH / 2, self._RING_WIDTH / 2,
            self._SIZE - self._RING_WIDTH, self._SIZE - self._RING_WIDTH,
        )

        # 背景环
        bg_pen = QPen(QColor(0, 0, 0, 30), self._RING_WIDTH)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # 前景弧
        if self._ratio > 0:
            if self._ratio < 0.7:
                color = QColor(0, 120, 212)
            elif self._ratio < 0.9:
                color = QColor(255, 140, 0)
            else:
                color = QColor(220, 53, 69)

            fg_pen = QPen(color, self._RING_WIDTH)
            fg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(fg_pen)
            span = -int(self._ratio * 360 * 16)
            painter.drawArc(rect, 90 * 16, span)

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            self._showFlyout()
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _showFlyout(self):
        """点击时弹出详情 Flyout."""
        view = _ContextUsageFlyoutView(
            self._usedTokens, self._maxTokens, self._breakdown,
        )
        Flyout.make(
            view,
            target=self,
            parent=self.window(),
            aniType=FlyoutAnimationType.PULL_UP,
            isDeleteOnClose=True,
        )

    def _updateTooltip(self) -> None:
        pct = self._ratio * 100
        used_str = self._fmt(self._usedTokens)
        max_str = self._fmt(self._maxTokens)
        self.setToolTip(f"{used_str} / {max_str} tokens ({pct:.0f}%)")

    @staticmethod
    def _fmt(n: int) -> str:
        if n >= 1000:
            return f"{n / 1000:.1f}k"
        return str(n)
