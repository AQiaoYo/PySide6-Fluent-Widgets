# coding: utf-8
"""聊天消息数据模型

定义聊天消息的角色枚举和数据类, 不依赖任何 UI 组件,
便于在视图层之外独立持有/序列化消息列表.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from uuid import uuid4

from PySide6.QtGui import QIcon


__all__ = [
    'ChatRole', 'ChatMessage',
    'ThinkingSegment', 'ToolCallStatus', 'ToolCallSegment',
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
    """生成新的消息 id (uuid4 hex 前 12 位足够区分)."""
    return uuid4().hex[:12]


# ----------------------------------------------------------------------
# Thinking / Tool call 子段
# ----------------------------------------------------------------------

@dataclass
class ThinkingSegment:
    """模型思考过程片段 (deepseek-r1 / o1 类推理模型).

    Attributes:
        content:      思考过程 markdown 文本 (可流式累积)
        finished:     是否已结束思考 (True 后视图切换为 "已深度思考" 状态)
        duration_ms:  思考耗时 (毫秒), finished=True 时设置, 用于显示
    """

    content: str = ""
    finished: bool = False
    duration_ms: Optional[int] = None


class ToolCallStatus(Enum):
    """工具调用状态.

    PENDING: 调用中 (UI 显示 spinner)
    SUCCESS: 调用成功
    ERROR:   调用失败
    """

    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ToolCallSegment:
    """单次工具调用记录.

    Attributes:
        tool_name:    工具名 (如 ``read_file``)
        arguments:    调用参数 (建议 JSON 字符串, 也可任意纯文本); 不解析
        result:       工具返回结果 (纯文本/markdown), 可流式追加
        status:       当前状态 (PENDING / SUCCESS / ERROR)
        duration_ms:  耗时 (ms), 完成时设置
        id:           唯一标识, 用于流式定位; 留空自动生成
    """

    tool_name: str = ""
    arguments: str = ""
    result: str = ""
    status: ToolCallStatus = ToolCallStatus.PENDING
    duration_ms: Optional[int] = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id()


# ----------------------------------------------------------------------
# 主消息
# ----------------------------------------------------------------------

@dataclass
class ChatMessage:
    """聊天消息数据类

    一条消息可能包含多个段落:

    1. ``thinking``  - 模型思考过程 (可选, 仅 AGENT)
    2. ``tool_calls`` - 工具调用列表 (可选, 仅 AGENT)
    3. ``content``   - 最终 markdown 答案

    渲染顺序: thinking → tool_calls → content

    Attributes:
        role:        消息角色 (USER / AGENT / SYSTEM)
        content:     最终答案 markdown 文本
        sender_name: 发送者显示名 (如 "DeepSeek V4" / "您"), Agent 平铺模式下显示在头像旁
                     None 时回退到 ChatView 注册的默认名 (setAgentDisplayName / setUserDisplayName)
        subtitle:    副标题, 显示在 sender_name 下方第二行 (如时间 / token 信息); None 不显示
        timestamp:   消息时间戳, 默认 None 表示由视图层决定是否显示
        avatar:      自定义头像, 可选 QIcon 或图片路径字符串, None 时使用 ChatView 默认头像
        id:          消息唯一标识, 用于流式追加 / 删除定位; 留空时自动生成
        thinking:    思考过程片段 (可选, 仅 AGENT 显示)
        tool_calls:  工具调用列表 (可选, 仅 AGENT 显示)
    """

    role: ChatRole
    content: str = ""
    sender_name: Optional[str] = None
    subtitle: Optional[str] = None
    timestamp: Optional[datetime] = None
    avatar: Optional[Union[QIcon, str]] = None
    id: str = field(default_factory=_new_id)
    thinking: Optional[ThinkingSegment] = None
    tool_calls: List[ToolCallSegment] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id()
