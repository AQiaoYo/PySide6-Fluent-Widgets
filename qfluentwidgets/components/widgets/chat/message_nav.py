# coding: utf-8
"""消息导航条 (MessageNav)

在聊天视图侧边显示一列小圆点, 每个圆点对应一条 USER 消息.
点击圆点跳转到对应消息位置. 当前可见消息高亮.

视觉参考 opencode 的 ``message-nav`` 组件:
- 竖向排列的小圆点 (6px)
- 当前消息对应的圆点放大 + 主题色填充
- hover 时显示 tooltip (消息摘要)
- 紧凑模式: 只显示圆点; 普通模式: 圆点 + 截断文字

使用方式:
    nav = MessageNav(parent)
    nav.addAnchor(message_id, summary_text)
    nav.setCurrentAnchor(message_id)
    nav.anchorClicked.connect(lambda mid: chatView.scrollToMessage(mid))
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.style_sheet import FluentStyleSheet
from ..tool_tip import ToolTipFilter, ToolTipPosition


__all__ = ['MessageNav']


class _NavDot(QWidget):
    """单个导航圆点."""

    clicked = Signal(str)  # message_id

    _NORMAL_SIZE = 6
    _ACTIVE_SIZE = 8
    _HIT_SIZE = 20  # 点击热区

    def __init__(self, message_id: str, summary: str = "",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._messageId = message_id
        self._summary = summary
        self._active = False

        self.setFixedSize(self._HIT_SIZE, self._HIT_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(summary or message_id[:8])
        self.installEventFilter(
            ToolTipFilter(self, showDelay=300, position=ToolTipPosition.LEFT)
        )

    def messageId(self) -> str:
        return self._messageId

    def setSummary(self, text: str) -> None:
        self._summary = text
        self.setToolTip(text or self._messageId[:8])

    def setActive(self, active: bool) -> None:
        if self._active == active:
            return
        self._active = active
        self.update()

    def isActive(self) -> bool:
        return self._active

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._messageId)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        if self._active:
            size = self._ACTIVE_SIZE
            color = QColor(0, 120, 212)  # 主题蓝, QSS 可覆盖
        else:
            size = self._NORMAL_SIZE
            color = QColor(0, 0, 0, 80)

        # 居中绘制圆点
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        painter.setBrush(color)
        painter.drawEllipse(int(x), int(y), size, size)


class MessageNav(QFrame):
    """消息导航条.

    竖向排列的圆点列表, 每个圆点对应一条 USER 消息.

    Signals:
        anchorClicked(str): 用户点击某个圆点, 参数为 message_id

    构造函数:
        MessageNav(parent: QWidget = None)
    """

    anchorClicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("messageNav")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding,
        )
        self.setFixedWidth(24)

        self._dots: List[_NavDot] = []
        self._dotIndex: Dict[str, _NavDot] = {}
        self._currentId: Optional[str] = None

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addAnchor(self, message_id: str, summary: str = "") -> None:
        """添加一个导航锚点 (对应一条 USER 消息).

        Args:
            message_id: 消息唯一 ID
            summary:    消息摘要 (用于 tooltip), 建议 <= 30 字符
        """
        if message_id in self._dotIndex:
            return
        dot = _NavDot(message_id, summary, self)
        dot.clicked.connect(self._onDotClicked)
        self._layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignHCenter)
        self._dots.append(dot)
        self._dotIndex[message_id] = dot

    def removeAnchor(self, message_id: str) -> None:
        """移除一个导航锚点."""
        dot = self._dotIndex.pop(message_id, None)
        if dot is None:
            return
        self._dots.remove(dot)
        self._layout.removeWidget(dot)
        dot.setParent(None)
        dot.deleteLater()
        if self._currentId == message_id:
            self._currentId = None

    def setCurrentAnchor(self, message_id: Optional[str]) -> None:
        """设置当前高亮的锚点.

        Args:
            message_id: 要高亮的消息 ID, None 表示取消所有高亮
        """
        if self._currentId == message_id:
            return
        # 取消旧的
        if self._currentId and self._currentId in self._dotIndex:
            self._dotIndex[self._currentId].setActive(False)
        # 设置新的
        self._currentId = message_id
        if message_id and message_id in self._dotIndex:
            self._dotIndex[message_id].setActive(True)

    def currentAnchor(self) -> Optional[str]:
        """返回当前高亮的 message_id."""
        return self._currentId

    def clear(self) -> None:
        """清空所有锚点."""
        for dot in self._dots:
            self._layout.removeWidget(dot)
            dot.setParent(None)
            dot.deleteLater()
        self._dots.clear()
        self._dotIndex.clear()
        self._currentId = None

    def anchorCount(self) -> int:
        return len(self._dots)

    def updateSummary(self, message_id: str, summary: str) -> None:
        """更新某个锚点的摘要文字."""
        dot = self._dotIndex.get(message_id)
        if dot:
            dot.setSummary(summary)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _onDotClicked(self, message_id: str) -> None:
        self.setCurrentAnchor(message_id)
        self.anchorClicked.emit(message_id)
