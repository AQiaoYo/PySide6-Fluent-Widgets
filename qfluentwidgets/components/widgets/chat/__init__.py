"""Chat 聊天组件子包

提供面向 Agent 对话场景的聊天消息视图组件, 支持用户/Agent 双向消息气泡布局,
Markdown 内容渲染 (含独立卡片化代码块), 流式追加输出以及消息级别的复制/编辑/删除操作.

主要类:
    * ChatRole       — 消息角色枚举 (USER / AGENT / SYSTEM)
    * ChatMessage    — 消息数据类
    * ChatAvatar     — 聊天头像组件 (基于 AvatarWidget, 角色感知默认色)
    * CodeBlock      — 独立代码块卡片 (带语言头与复制按钮)
    * MarkdownView   — Markdown 渲染视图 (代码块切片 + 文本段)
    * ChatBubble     — 单条消息气泡
    * ChatView       — 聊天消息容器
"""

from .chat_message import ChatRole, ChatMessage
from .chat_avatar import ChatAvatar
from .code_block import CodeBlock
from .markdown_view import MarkdownView
from .chat_bubble import ChatBubble
from .chat_view import ChatView


__all__ = [
    'ChatRole', 'ChatMessage', 'ChatAvatar',
    'CodeBlock', 'MarkdownView', 'ChatBubble', 'ChatView',
]
