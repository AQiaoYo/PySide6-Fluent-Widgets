"""Chat 聊天组件子包

提供面向 Agent 对话场景的聊天消息视图组件, 支持用户/Agent 双向消息气泡布局,
Markdown 内容渲染 (含独立卡片化代码块), 流式追加输出以及消息级别的复制/编辑/删除操作.

主要类:
    * ChatRole              — 消息角色枚举 (USER / AGENT / SYSTEM)
    * SegmentKind           — 段类型枚举 (TEXT / THINKING / TOOL_CALL)
    * Segment               — 段抽象基类
    * TextSegment           — Markdown 文本段
    * ThinkingSegment       — 思考过程段
    * ToolCallSegment       — 工具调用段
    * ToolCallStatus        — 工具调用状态机 (PENDING_APPROVAL / PENDING / SUCCESS / ERROR / REJECTED)
    * ChatMessage           — 消息数据类 (有序段流)
    * ChatAvatar            — 聊天头像组件
    * CodeBlock             — 独立代码块卡片 (带语言头与复制按钮)
    * MarkdownView          — Markdown 渲染视图
    * ThinkingCard          — 思考过程卡片
    * ToolCallCardBase      — 工具调用卡片抽象基类
    * GenericToolCallCard   — 通用工具调用渲染器
    * ToolCallCard          — GenericToolCallCard 的历史别名 (向后兼容)
    * ChatBubble            — 单条消息气泡
    * AgentChatView         — Agent 聊天消息容器
    * ChatInputEdit         — Agent 聊天输入框 (内嵌附件 / 圆形发送按钮)
    * AgentChatPanel        — 完整聊天面板 (消息流 + 输入框)
"""

from .chat_message import (
    ChatRole, ChatMessage,
    SegmentKind, Segment, TextSegment, ThinkingSegment,
    ToolCallStatus, ApprovalPolicy, ToolCallSegment,
    TaskStatus, TaskItem, TaskListSegment,
)
from .segment_renderers import (
    register_segment_renderer, unregister_segment_renderer,
    resolve_segment_renderer,
)
from .chat_avatar import ChatAvatar
from .code_block import CodeBlock
from .markdown_view import MarkdownView
from .thinking_card import ThinkingCard
from .tool_call_card import ToolCallCardBase, GenericToolCallCard, ToolCallCard
from .diff_view import DiffView
from .tool_renderers import (
    ToolCardFactory,
    registerToolRenderer, unregisterToolRenderer,
    resolveToolRenderer, registeredToolNames,
    FileReadCard, FileWriteCard, FileEditCard,
    BashCard, WebSearchCard, GrepSearchCard,
    McpToolCard, SkillCard,
)
from .generation_status_bar import GenerationStatusBar
from .chat_bubble import ChatBubble, BubbleAction
from .agent_chat_view import AgentChatView
from .agent_chat_panel import AgentChatPanel, ChatInputEdit
from .message_nav import MessageNav
from .session_retry_card import SessionRetryCard
from .tool_error_card import ToolErrorCard
from .context_usage_indicator import ContextUsageIndicator
from .session_review_panel import SessionReviewPanel
from .dock_surface import DockSurface
from .permission_dock import PermissionDock
from .question_dock import QuestionDock
from .followup_dock import FollowupDock
from .revert_dock import RevertDock
from .todo_dock import TodoDock
from .inline_spinner import InlineSpinner
from .animated_number import AnimatedNumber
from .text_shimmer import TextShimmer
from .text_reveal import TextReveal
from .tool_status_title import ToolStatusTitle
from .keybind_label import KeybindLabel
from .attachment_preview import AttachmentPreview
from .slash_command_popover import SlashCommandPopover
from .mention_popover import MentionPopover, MentionItem


__all__ = [
    'ChatRole', 'ChatMessage',
    'SegmentKind', 'Segment', 'TextSegment', 'ThinkingSegment',
    'ToolCallStatus', 'ApprovalPolicy', 'ToolCallSegment',
    'TaskStatus', 'TaskItem', 'TaskListSegment',
    'register_segment_renderer', 'unregister_segment_renderer',
    'resolve_segment_renderer',
    'ChatAvatar',
    'CodeBlock', 'MarkdownView',
    'ThinkingCard',
    'ToolCallCardBase', 'GenericToolCallCard', 'ToolCallCard',
    'DiffView',
    'ToolCardFactory',
    'registerToolRenderer', 'unregisterToolRenderer',
    'resolveToolRenderer', 'registeredToolNames',
    'FileReadCard', 'FileWriteCard', 'FileEditCard',
    'BashCard', 'WebSearchCard', 'GrepSearchCard',
    'McpToolCard', 'SkillCard',
    'GenerationStatusBar',
    'ChatBubble', 'BubbleAction', 'AgentChatView',
    'ChatInputEdit', 'AgentChatPanel',
    'MessageNav',
    'SessionRetryCard',
    'ToolErrorCard',
    'ContextUsageIndicator',
    'SessionReviewPanel',
    'DockSurface',
    'PermissionDock',
    'QuestionDock',
    'FollowupDock',
    'RevertDock',
    'TodoDock',
    'InlineSpinner',
    'AnimatedNumber',
    'TextShimmer',
    'TextReveal',
    'ToolStatusTitle',
    'KeybindLabel',
    'AttachmentPreview',
    'SlashCommandPopover',
    'MentionPopover', 'MentionItem',
]
