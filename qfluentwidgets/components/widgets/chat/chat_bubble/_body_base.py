# coding: utf-8
"""ChatBubble body 抽象基类.

每条消息气泡按角色拆成三个 body 子 widget:
    UserBubbleBody / AgentBubbleBody / SystemBubbleBody

它们都继承本类, 共享:
    * ``_message`` 数据引用与默认显示名 / 副标题处理
    * ``_codeMaxVisibleLines`` 全局 CodeBlock 行数上限
    * **单个** ``actionTriggered(action_name, msg_id, payload)`` 信号 (P1b
      收敛: 此前 9 个独立 signal 改成 1 个 action ID 模式 — 用户操作的
      "动作名" 用字符串区分, 多余 1 个语义参数走 payload 传)
    * 一组 no-op 默认实现, 让 ChatBubble dispatcher 不需要 isinstance 检查
      角色就能盲调任意公共方法 — 不适用的角色直接静默忽略

为什么不用 ABC: 让默认实现"做空"比抛 NotImplementedError 更友好
(``ChatBubble.markStopped`` 在 USER 上调用应该静默, 而不是炸).

Action ID 模式 (与 ChatBubble.actionTriggered 一致):
    "copy"               payload=None       — 复制按钮点击
    "edit"               payload=None       — 编辑按钮点击 (UserBody 同时进入内联编辑)
    "edit_confirm"       payload=new_content(str) — 内联编辑保存
    "edit_cancel"        payload=None       — 内联编辑取消
    "delete"             payload=None       — 删除按钮点击
    "regenerate"         payload=None       — 重新生成按钮点击
    "resume"             payload=None       — 流式被 Stop 后点 [继续生成] (P2c)
    "version_switch"     payload=index(int) — 选页器切换
    "tool_approve"       payload=call_id(str) — 工具卡片 [批准]
    "tool_reject"        payload=call_id(str) — 工具卡片 [拒绝]
    "tool_always_allow"  payload=call_id(str) — 工具卡片 [总是允许] (本次允许 + ALLOW)
    "tool_always_reject" payload=call_id(str) — 工具卡片 [总是拒绝] (本次拒绝 + DENY)
"""

from typing import Dict, Optional, Tuple, Union

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from ..chat_message import ChatMessage, ChatRole
from ..code_block import CodeBlock
from ..thinking_card import ThinkingCard
from ..tool_call_card import ToolCallCardBase
from ..chat_message import ToolCallSegment


__all__ = ['BubbleBodyBase', 'BubbleAction']


class BubbleAction:
    """``actionTriggered`` 信号的 action 名常量集.

    用类作为 namespace, 让 IDE 自动补全且避免拼写错误.
    """
    COPY = "copy"
    EDIT = "edit"
    EDIT_CONFIRM = "edit_confirm"
    EDIT_CANCEL = "edit_cancel"
    DELETE = "delete"
    REGENERATE = "regenerate"
    RESUME = "resume"
    VERSION_SWITCH = "version_switch"
    TOOL_APPROVE = "tool_approve"
    TOOL_REJECT = "tool_reject"
    TOOL_ALWAYS_ALLOW = "tool_always_allow"
    TOOL_ALWAYS_REJECT = "tool_always_reject"


class BubbleBodyBase(QWidget):
    """ChatBubble 内层 body 抽象基类.

    ChatBubble dispatcher 把所有公共 API 都盲转发给当前 body, 因此本类必须
    把每个 API 都至少给个默认 (大多 no-op) 实现, 子类按角色 override
    需要的方法即可.

    Signals:
        actionTriggered(str, str, object): 用户在气泡内触发任何动作时 emit.
            参数 (action_name, message_id, payload). payload 类型由
            ``action_name`` 决定 (见模块 docstring 表).
    """

    actionTriggered = Signal(str, str, object)

    _MAX_CONTENT_WIDTH = 920

    def __init__(self, message: ChatMessage,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._message = message
        self._defaultSenderName: Optional[str] = None
        self._codeMaxVisibleLines = CodeBlock._DEFAULT_MAX_VISIBLE_LINES

    # ------------------------------------------------------------------
    # 数据访问
    # ------------------------------------------------------------------

    def message(self) -> ChatMessage:
        return self._message

    # ------------------------------------------------------------------
    # 显示名 / 默认头像
    # ------------------------------------------------------------------

    def displayName(self) -> str:
        if self._message.sender_name:
            return self._message.sender_name
        if self._defaultSenderName:
            return self._defaultSenderName
        return self._fallbackName(self._message.role)

    @staticmethod
    def _fallbackName(role: ChatRole) -> str:
        return {
            ChatRole.USER: "您",
            ChatRole.AGENT: "Agent",
            ChatRole.SYSTEM: "系统",
        }.get(role, "")

    def setDefaultSenderName(self, name: Optional[str]) -> None:
        self._defaultSenderName = name
        # 子类如果有 senderLabel, 在 override 中刷新

    def setUserAvatarFallback(self, avatar: Optional[Union[QIcon, str]]) -> None:
        # 子类有 _avatar 时 override
        pass

    # ------------------------------------------------------------------
    # 内容流式
    # ------------------------------------------------------------------

    def appendDelta(self, delta: str) -> None:
        """追加内容. 子类按角色实现 (USER/SYSTEM 直接拼到 content;
        AGENT 走 segment 路径).
        """
        if not delta:
            return

    def setContent(self, markdown: str) -> None:
        """覆盖式设置内容. 子类按角色 override."""
        self._message.content = markdown

    def setSubtitle(self, text: Optional[str]) -> None:
        self._message.subtitle = text or None
        # 子类有 _subtitleLabel 时 override

    # ------------------------------------------------------------------
    # CodeBlock 行数上限
    # ------------------------------------------------------------------

    def setCodeBlockMaxVisibleLines(self, n: int) -> None:
        self._codeMaxVisibleLines = max(1, int(n))

    def codeBlockMaxVisibleLines(self) -> int:
        return self._codeMaxVisibleLines

    # ------------------------------------------------------------------
    # AGENT 专用 (默认 no-op)
    # ------------------------------------------------------------------

    def thinkingCard(self) -> Optional[ThinkingCard]:
        return None

    def ensureThinking(self) -> ThinkingCard:
        raise RuntimeError("ThinkingCard 仅在 AGENT 角色消息上可用")

    def addToolCall(self, segment: ToolCallSegment) -> ToolCallCardBase:
        raise RuntimeError("ToolCallCard 仅在 AGENT 角色消息上可用")

    def toolCallCard(self, call_id: str) -> Optional[ToolCallCardBase]:
        return None

    def toolCallCards(self) -> Dict[str, ToolCallCardBase]:
        return {}

    def markStopped(self, stopped: bool = True) -> None:
        pass

    def setRegenerateEnabled(self, enabled: bool) -> None:
        pass

    def isRegenerateEnabled(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # USER 专用 (默认 no-op)
    # ------------------------------------------------------------------

    def isInEditMode(self) -> bool:
        return False

    def enterEditMode(self) -> None:
        pass

    def exitEditMode(self, save: bool = False) -> None:
        pass

    def setVersionInfo(self, total: int, active: int) -> None:
        pass

    def versionInfo(self) -> Optional[Tuple[int, int]]:
        return None

    # ------------------------------------------------------------------
    # 操作栏 always-visible / hover-fade (USER + AGENT 子类 override)
    # ------------------------------------------------------------------

    def setActionsAlwaysVisible(self, always: bool) -> None:
        pass

    def actionsAlwaysVisible(self) -> bool:
        return True

    def onBubbleEnterEvent(self) -> None:
        """父级 ChatBubble 收到 enterEvent 时, dispatcher 转发到 body."""
        pass

    def onBubbleLeaveEvent(self) -> None:
        """父级 ChatBubble 收到 leaveEvent 时, dispatcher 转发到 body."""
        pass

    # ------------------------------------------------------------------
    # 数据 -> UI 的初始填充 (子类必须 override)
    # ------------------------------------------------------------------

    def applyMessage(self) -> None:
        """根据 ``self._message`` 当前状态把内容塞进 UI. 子类 override."""
        raise NotImplementedError
