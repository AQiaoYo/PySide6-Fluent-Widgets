# coding: utf-8
"""ChatBubble 主类 — 一个轻量 dispatcher, 实际渲染由 role-specific body 完成.

历史背景: 旧版 ``chat_bubble.py`` 把 USER / AGENT / SYSTEM 三种角色的 UI
构建 + 状态机都塞进一个 ~957 行的 ``ChatBubble`` 类, 内部反复 ``if role ==
ChatRole.X`` 分支, 维护成本高. 本次重构把每种角色的 body 抽到独立 widget
(``UserBubbleBody`` / ``AgentBubbleBody`` / ``SystemBubbleBody``),
``ChatBubble`` 退化为 ~120 行的 dispatcher: 只负责选 body + 把 1 个 action
信号 re-emit + 把公共方法盲转发给 body.

由于 body 基类 ``BubbleBodyBase`` 给所有公共方法提供了 no-op 默认实现,
dispatcher 这层不需要任何 isinstance / role 检查 (除了构造时选 body).

P1b: 9 个独立 button signal 收敛为 1 个 ``actionTriggered`` action ID 信号
(见 :class:`BubbleAction` 常量集).
"""

from typing import Dict, Optional, Tuple, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget

from .....common.style_sheet import FluentStyleSheet
from ..chat_message import (
    ChatMessage, ChatRole, ToolCallSegment,
)
from ..thinking_card import ThinkingCard
from ..tool_call_card import ToolCallCardBase
from ._body_base import BubbleAction, BubbleBodyBase
from .agent_body import AgentBubbleBody
from .system_body import SystemBubbleBody
from .user_body import UserBubbleBody


__all__ = ['ChatBubble']


class ChatBubble(QFrame):
    """单条聊天消息组件 — dispatcher.

    根据 ``message.role`` 自动实例化 ``UserBubbleBody`` / ``AgentBubbleBody``
    / ``SystemBubbleBody`` 之一作为内层 body, 把所有公共 API 转发给它,
    把 body 发出的 ``actionTriggered`` 信号原样 re-emit 给上层 ``AgentChatView``.

    Signals:
        actionTriggered(str, str, object): 用户在气泡内触发任何动作时 emit.
            参数 ``(action_name, message_id, payload)``. ``action_name``
            取自 :class:`BubbleAction` 常量 ("copy" / "edit" / "edit_confirm"
            / "edit_cancel" / "delete" / "regenerate" / "version_switch"
            / "tool_approve" / "tool_reject"). payload 类型由 action 决定.

    构造函数:
        ChatBubble(message: ChatMessage, parent: QWidget = None)
    """

    actionTriggered = Signal(str, str, object)

    def __init__(self, message: ChatMessage, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._message = message

        self.setObjectName("chatBubble")
        self.setProperty("role", message.role.value)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        # 创建 role-specific body 并嵌进单一 layout
        self._body: BubbleBodyBase = self._makeBody()
        # 单条信号转发: body.actionTriggered -> self.actionTriggered
        self._body.actionTriggered.connect(self.actionTriggered)

        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)
        rootLayout.addWidget(self._body)

        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # body 工厂
    # ------------------------------------------------------------------

    def _makeBody(self) -> BubbleBodyBase:
        role = self._message.role
        if role == ChatRole.USER:
            return UserBubbleBody(self._message, self)
        if role == ChatRole.AGENT:
            return AgentBubbleBody(self._message, self)
        return SystemBubbleBody(self._message, self)

    # ------------------------------------------------------------------
    # 数据访问
    # ------------------------------------------------------------------

    def message(self) -> ChatMessage:
        """返回此气泡承载的 ChatMessage (注意是同一引用)."""
        return self._message

    def body(self) -> BubbleBodyBase:
        """返回内层 body (供高级用法 / 测试访问 role-specific 状态)."""
        return self._body

    # ------------------------------------------------------------------
    # 公共 API: 全部转发给 body (body 基类已给所有方法 no-op 默认)
    # ------------------------------------------------------------------

    def appendDelta(self, delta: str) -> None:
        self._body.appendDelta(delta)

    def setContent(self, markdown: str) -> None:
        self._body.setContent(markdown)

    def setSubtitle(self, text: Optional[str]) -> None:
        self._body.setSubtitle(text)

    def setUserAvatarFallback(self, avatar: Optional[Union[QIcon, str]]) -> None:
        self._body.setUserAvatarFallback(avatar)

    def setDefaultSenderName(self, name: Optional[str]) -> None:
        self._body.setDefaultSenderName(name)

    def setCodeBlockMaxVisibleLines(self, n: int) -> None:
        self._body.setCodeBlockMaxVisibleLines(n)

    def codeBlockMaxVisibleLines(self) -> int:
        return self._body.codeBlockMaxVisibleLines()

    # AGENT 专用 (USER/SYSTEM 上调用静默 no-op / RuntimeError)
    def thinkingCard(self) -> Optional[ThinkingCard]:
        return self._body.thinkingCard()

    def ensureThinking(self) -> ThinkingCard:
        return self._body.ensureThinking()

    def addToolCall(self, segment: ToolCallSegment) -> ToolCallCardBase:
        return self._body.addToolCall(segment)

    def toolCallCard(self, call_id: str) -> Optional[ToolCallCardBase]:
        return self._body.toolCallCard(call_id)

    def toolCallCards(self) -> Dict[str, ToolCallCardBase]:
        return self._body.toolCallCards()

    def markStopped(self, stopped: bool = True) -> None:
        self._body.markStopped(stopped)

    def setRegenerateEnabled(self, enabled: bool) -> None:
        self._body.setRegenerateEnabled(enabled)

    def isRegenerateEnabled(self) -> bool:
        return self._body.isRegenerateEnabled()

    # USER 专用 (AGENT/SYSTEM 上调用静默 no-op)
    def isInEditMode(self) -> bool:
        return self._body.isInEditMode()

    def enterEditMode(self) -> None:
        self._body.enterEditMode()

    def exitEditMode(self, save: bool = False) -> None:
        self._body.exitEditMode(save)

    def setVersionInfo(self, total: int, active: int) -> None:
        self._body.setVersionInfo(total, active)

    def versionInfo(self) -> Optional[Tuple[int, int]]:
        return self._body.versionInfo()

    # 操作栏 always-visible / hover-fade
    def setActionsAlwaysVisible(self, always: bool) -> None:
        self._body.setActionsAlwaysVisible(always)

    def actionsAlwaysVisible(self) -> bool:
        return self._body.actionsAlwaysVisible()

    # ------------------------------------------------------------------
    # 鼠标 hover 转发: 给 body 决定是否触发 fade
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        self._body.onBubbleEnterEvent()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._body.onBubbleLeaveEvent()
        super().leaveEvent(event)
