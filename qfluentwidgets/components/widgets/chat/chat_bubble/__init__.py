# coding: utf-8
"""ChatBubble 子包 — 单条聊天消息气泡组件.

按角色拆分:

* :class:`ChatBubble`         主入口 dispatcher (向后兼容旧 ``from .chat_bubble import ChatBubble`` 路径)
* :class:`UserBubbleBody`     USER 角色 body (右对齐气泡 + 内联编辑器 + 版本选页器)
* :class:`AgentBubbleBody`    AGENT 角色 body (平铺 timeline)
* :class:`SystemBubbleBody`   SYSTEM 角色 body (居中提示)
* :class:`BubbleBodyBase`     body 抽象基类
* :class:`BubbleActionBar`    复制 / 重生成 / 编辑 / 删除 操作栏 (USER+AGENT 共用)

通常上层只需要 ``ChatBubble``; 暴露 body 类是为了让宿主侧做高级定制
(如插入自定义按钮 / 替换 timeline 容器).
"""

from .bubble import ChatBubble
from ._action_bar import BubbleActionBar
from ._body_base import BubbleAction, BubbleBodyBase
from .agent_body import AgentBubbleBody
from .system_body import SystemBubbleBody
from .user_body import UserBubbleBody


__all__ = [
    'ChatBubble',
    'BubbleAction',
    'BubbleBodyBase',
    'BubbleActionBar',
    'UserBubbleBody',
    'AgentBubbleBody',
    'SystemBubbleBody',
]
