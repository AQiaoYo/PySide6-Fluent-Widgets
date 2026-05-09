# coding: utf-8
"""聊天消息数据模型 (Segment 化版本)

定义聊天消息的角色枚举和段 (Segment) 数据模型, 不依赖任何 UI 组件,
便于在视图层之外独立持有 / 序列化消息列表.

本版本相对于早期 ChatMessage(thinking, tool_calls, content) 三段固定结构
做了硬重构: 一条 AGENT 消息可以是任意 (TEXT | THINKING | TOOL_CALL) 段
的有序序列, 以表示真实 Agent 多轮交错的思考 -> 工具 -> 思考 -> 工具 -> 答案
模式. ``content`` 字段降级为 TextSegment 内容的聚合 property.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import uuid4

from PySide6.QtGui import QIcon


__all__ = [
    'ChatRole',
    'SegmentKind', 'Segment', 'TextSegment', 'ThinkingSegment',
    'ToolCallStatus', 'ApprovalPolicy', 'ToolCallSegment',
    'TaskStatus', 'TaskItem', 'TaskListSegment',
    'ChatMessage',
]


class ChatRole(Enum):
    """聊天消息角色

    USER:   终端用户发送的消息
    AGENT:  Agent / 助手返回的消息 (可包含 markdown / 代码块)
    SYSTEM: 系统提示消息 (居中弱化展示)
    """

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


def _new_id() -> str:
    """生成新的消息 / 段 id (uuid4 hex 前 12 位足够区分)."""
    return uuid4().hex[:12]


# ----------------------------------------------------------------------
# Segment 基类与子类
# ----------------------------------------------------------------------

class SegmentKind(Enum):
    """段类型枚举.

    内置四种:
        TEXT       - Markdown 文本段
        THINKING   - 模型思考过程
        TOOL_CALL  - 工具调用
        TASK_LIST  - 任务列表 (对齐 Claude Code 的 agent 任务计划展示)

    扩展:  使用 :func:`segment_renderers.register_segment_renderer` 注册
    自定义 kind 对应的渲染器, 可新增类型而不需改 ``AgentBubbleBody``.
    """

    TEXT = "text"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TASK_LIST = "task_list"


@dataclass
class Segment:
    """段抽象基类.

    所有具体段类型 (TextSegment / ThinkingSegment / ToolCallSegment) 都继承
    自此类, 共享 ``id`` 字段, 通过 ``kind`` 属性返回各自类型枚举值.

    Attributes:
        id: 段唯一标识, 用于在流式追加 / 局部更新时定位; 留空时自动生成
    """

    id: str = field(default_factory=_new_id)

    @property
    def kind(self) -> SegmentKind:  # pragma: no cover - 抽象
        """段类型 (子类必须覆盖)."""
        raise NotImplementedError(
            "Segment 子类必须实现 kind property"
        )


@dataclass
class TextSegment(Segment):
    """Markdown 文本段 (Agent 中间或最终回答).

    一条 AGENT 消息可以包含多个 TextSegment: 例如在两次工具调用之间
    Agent 输出了一段文本, 然后又调用工具, 最后再输出最终答案. 视图层会
    按 segments 顺序渲染每个 TextSegment 为独立的 MarkdownView.

    Attributes:
        content: markdown 文本 (可流式追加).
    """

    content: str = ""

    @property
    def kind(self) -> SegmentKind:
        return SegmentKind.TEXT


@dataclass
class ThinkingSegment(Segment):
    """模型思考过程片段 (deepseek-r1 / o1 / claude extended-thinking 等).

    一条 AGENT 消息可以包含多个 ThinkingSegment, 表示模型在不同阶段的
    多次思考 (例如 Claude 在工具调用前后会有不同思考轮次).

    Attributes:
        content:      思考过程 markdown 文本 (可流式累积)
        finished:     是否已结束思考 (True 后视图切换为 "已深度思考" 状态)
        duration_ms:  思考耗时 (毫秒), finished=True 时设置, 用于显示
    """

    content: str = ""
    finished: bool = False
    duration_ms: Optional[int] = None

    @property
    def kind(self) -> SegmentKind:
        return SegmentKind.THINKING


class ToolCallStatus(Enum):
    """工具调用状态机.

    流程:
        PENDING_APPROVAL -> (用户批准) -> PENDING -> SUCCESS / ERROR
        PENDING_APPROVAL -> (用户拒绝) -> REJECTED
        PENDING -> SUCCESS / ERROR (host 直接发起, 无需审批)

    枚举值:
        PENDING_APPROVAL: 等待用户审批 (UI 显示批准 / 拒绝按钮)
        PENDING:          调用中 (UI 显示 spinner)
        SUCCESS:          调用成功
        ERROR:            调用失败
        REJECTED:         用户拒绝调用 (UI 显示红色 ✗ + 已拒绝 文案)
    """

    PENDING_APPROVAL = "pending_approval"
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    REJECTED = "rejected"


class ApprovalPolicy(Enum):
    """工具调用审批策略 (对齐 OpenCode / Claude Code 的三态语义).

    用于 ``AgentChatView.setApprovalPolicy(tool_name, policy)`` 注册每个工具
    的默认行为. ``addToolCall`` 不显式传 ``requires_approval`` 时查此表决定
    初始 ``ToolCallStatus``.

    枚举值:
        ALLOW: 不弹审批, 直接 PENDING (等价于旧 ``requires_approval=False``)
        ASK:   弹审批 UI, 初始 PENDING_APPROVAL (等价于旧 ``requires_approval=True``)
        DENY:  不弹审批, 直接 REJECTED (自动拒绝, 对敏感工具可用)
    """

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass
class ToolCallSegment(Segment):
    """单次工具调用记录.

    Attributes:
        tool_name:    工具名 (如 ``read_file`` / ``bash`` / ``edit_file``)
        arguments:    调用参数 (建议 JSON 字符串, 也可任意纯文本); 不解析
        result:       工具返回结果 (纯文本 / markdown), 可流式追加
        status:       当前状态 (PENDING_APPROVAL / PENDING / SUCCESS / ERROR / REJECTED)
        duration_ms:  耗时 (ms), 完成时设置
        metadata:     给特化渲染器使用的额外字段 dict (如 ``path`` / ``language`` /
                      ``exit_code`` / ``results`` / ``hits`` / ``old`` / ``new``).
                      渲染器对每一个字段都做容错降级, 缺失即 fallback 到通用渲染.
    """

    tool_name: str = ""
    arguments: str = ""
    result: str = ""
    status: ToolCallStatus = ToolCallStatus.PENDING
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def kind(self) -> SegmentKind:
        return SegmentKind.TOOL_CALL


# ----------------------------------------------------------------------
# TaskListSegment: 任务列表段 (P2d, 对齐 Claude Code 的 agent 任务计划)
# ----------------------------------------------------------------------

class TaskStatus(Enum):
    """单个任务状态机.

    TODO:        未开始 (☐ 空心方框)
    IN_PROGRESS: 进行中 (⟳ 旋转圈)
    DONE:        已完成 (✓ 对勾)
    """

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class TaskItem:
    """任务列表中的单个任务.

    Attributes:
        id:     任务唯一标识 (供 ``updateTaskItem`` 定位). 留空时自动生成.
        text:   任务文字描述 (markdown 不解析, 纯文本渲染).
        status: 任务状态, 默认 TODO.
    """

    id: str = field(default_factory=_new_id)
    text: str = ""
    status: TaskStatus = TaskStatus.TODO


@dataclass
class TaskListSegment(Segment):
    """任务列表段.

    用于展示 Agent 的任务计划, 类似 Claude Code 在长任务中显示的 TODO list
    (☐ 未开始 / ⟳ 进行中 / ✓ 已完成). 列表项可以流式状态翻转.

    Attributes:
        title: 列表标题 (可选, 形如 "任务计划 (1/3)"). 渲染器也可自己根据
               items 算出 "completed/total" 进度显示.
        items: 任务项列表.
    """

    title: str = ""
    items: List[TaskItem] = field(default_factory=list)

    @property
    def kind(self) -> SegmentKind:
        return SegmentKind.TASK_LIST


# ----------------------------------------------------------------------
# 主消息
# ----------------------------------------------------------------------

class ChatMessage:
    """聊天消息.

    一条消息由有序的 ``segments: List[Segment]`` 表示, 元素是
    ``TextSegment`` / ``ThinkingSegment`` / ``ToolCallSegment`` 之一.
    AGENT 消息可任意交错三种段; USER / SYSTEM 通常只放单一 TextSegment.

    便利路径:
        ``ChatMessage(role=USER, content="hi")`` -> 自动 append TextSegment
        ``msg.content`` -> 聚合所有 TextSegment.content (read)
        ``msg.content = "new text"`` -> 删除所有 TextSegment, 新建一个 (write)

    硬重构语义:
        本版本 **不再有** ``thinking`` / ``tool_calls`` 字段. 任何外部代码
        若读这两个字段会立即抛 AttributeError, 这是预期行为, 帮助使用者
        在升级时立即定位.

    Attributes:
        role:        消息角色 (USER / AGENT / SYSTEM)
        sender_name: 发送者显示名 (如 "DeepSeek V4" / "您"), 视图层显示在头像旁.
                     None 时回退到 AgentChatView 注册的默认名.
        subtitle:    副标题, 显示在 sender_name 下方 (如时间 / token 信息); None 不显示.
        timestamp:   消息时间戳, 默认 None 表示由视图层决定是否显示.
        avatar:      自定义头像, 可选 QIcon 或图片路径; None 时使用 AgentChatView 默认头像.
        id:          消息唯一标识, 用于流式追加 / 删除定位; 留空时自动生成.
        segments:    段列表 (有序). 渲染顺序即列表顺序.
    """

    def __init__(
        self,
        role: ChatRole,
        content: str = "",
        *,
        sender_name: Optional[str] = None,
        subtitle: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        avatar: Optional[Union[QIcon, str]] = None,
        id: str = "",
        segments: Optional[Iterable[Segment]] = None,
    ):
        """构造一条消息.

        Args:
            role:        消息角色
            content:     便利字段, 等价于 segments=[TextSegment(content=content)].
                         若同时给了 segments, 此参数被忽略.
            sender_name: 显示名
            subtitle:    副标题
            timestamp:   时间戳
            avatar:      自定义头像
            id:          消息 id, 留空自动生成
            segments:    显式段列表, 优先级高于 content
        """
        self.role = role
        self.sender_name = sender_name
        self.subtitle = subtitle
        self.timestamp = timestamp
        self.avatar = avatar
        self.id = id or _new_id()

        if segments is not None:
            self.segments: List[Segment] = list(segments)
        else:
            self.segments = []
            if content:
                self.segments.append(TextSegment(content=content))

    # ------------------------------------------------------------------
    # content 聚合 property
    # ------------------------------------------------------------------

    @property
    def content(self) -> str:
        """聚合所有 TextSegment 内容 (read).

        多个 TextSegment 之间不插任何分隔符, 直接拼接. 这与 "流式追加
        token 总和" 的语义一致.
        """
        return "".join(
            s.content for s in self.segments if isinstance(s, TextSegment)
        )

    @content.setter
    def content(self, value: str) -> None:
        """覆盖式设置: 删除所有 TextSegment, 新建一个 TextSegment 并追加.

        非 TEXT 段 (THINKING / TOOL_CALL) 保留位置不变. 这与历史语义最贴近:
        旧 setContent / appendDelta 只动文本.
        """
        self.segments = [
            s for s in self.segments if not isinstance(s, TextSegment)
        ]
        if value:
            self.segments.append(TextSegment(content=value))

    # ------------------------------------------------------------------
    # 便利访问器 (供视图层 / facade API 使用)
    # ------------------------------------------------------------------

    def text_segments(self) -> List[TextSegment]:
        """返回所有 TextSegment (按 segments 顺序)."""
        return [s for s in self.segments if isinstance(s, TextSegment)]

    def thinking_segments(self) -> List[ThinkingSegment]:
        """返回所有 ThinkingSegment (按 segments 顺序)."""
        return [s for s in self.segments if isinstance(s, ThinkingSegment)]

    def tool_call_segments(self) -> List[ToolCallSegment]:
        """返回所有 ToolCallSegment (按 segments 顺序)."""
        return [s for s in self.segments if isinstance(s, ToolCallSegment)]

    def find_segment(self, segment_id: str) -> Optional[Segment]:
        """按段 id 查找; 不存在返回 None."""
        for s in self.segments:
            if s.id == segment_id:
                return s
        return None

    def __repr__(self) -> str:
        return (
            f"ChatMessage(role={self.role.value!r}, id={self.id!r}, "
            f"segments={len(self.segments)})"
        )
