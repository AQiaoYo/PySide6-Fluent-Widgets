# coding: utf-8
"""聊天消息数据模型

定义聊天消息的角色枚举和数据类, 不依赖任何 UI 组件,
便于在视图层之外独立持有/序列化消息列表.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Union
from uuid import uuid4

from PySide6.QtGui import QIcon


__all__ = ['ChatRole', 'ChatMessage']


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


@dataclass
class ChatMessage:
    """聊天消息数据类

    Attributes:
        role:        消息角色 (USER / AGENT / SYSTEM)
        content:     消息内容, markdown 文本
        sender_name: 发送者显示名 (如 "DeepSeek V4" / "您"), Agent 平铺模式下显示在头像旁
                     None 时回退到 ChatView 注册的默认名 (setAgentDisplayName / setUserDisplayName)
        subtitle:    副标题, 显示在 sender_name 之后, 用 "|" 分隔 (如供应商 "深度求索"); None 不显示
        timestamp:   消息时间戳, 默认 None 表示由视图层决定是否显示
        avatar:      自定义头像, 可选 QIcon 或图片路径字符串, None 时使用 ChatView 默认头像
        id:          消息唯一标识, 用于流式追加 / 删除定位; 留空时自动生成
    """

    role: ChatRole
    content: str = ""
    sender_name: Optional[str] = None
    subtitle: Optional[str] = None
    timestamp: Optional[datetime] = None
    avatar: Optional[Union[QIcon, str]] = None
    id: str = field(default_factory=_new_id)

    def __post_init__(self):
        if not self.id:
            self.id = _new_id()
