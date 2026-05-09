# coding: utf-8
"""Segment 渲染注册表.

把 ``ChatMessage.segments`` 列表里的 ``Segment`` 对象变成 timeline 内的
``QWidget`` 时, 之前用的是 ``AgentBubbleBody._appendSegmentWidget`` 里写死
的 ``isinstance(seg, X)`` 链:

    if isinstance(seg, TextSegment): create MarkdownView
    elif isinstance(seg, ThinkingSegment): create ThinkingCard
    elif isinstance(seg, ToolCallSegment): create ToolCallCardBase via factory
    else: placeholder QWidget

加新 segment 类型 (例: ``TaskListSegment``) 必须改 ``agent_body.py``. 高耦合
且违反 OCP. 本模块改成注册表 + 适配器:

    register_segment_renderer(SegmentKind.TASK_LIST, my_renderer)

之后 agent_body 直接走 ``resolve_segment_renderer(seg.kind).create_widget(...)``,
对新 segment 类型零改动.

Renderer 协议:
    create_widget(segment, parent, code_max_visible_lines) -> QWidget
        创建并返回该 segment 对应的 widget.

模块自己注册 3 个内置类型 (TEXT / THINKING / TOOL_CALL) 在 import 时完成
(见模块底部 ``_register_builtins()``).
"""

from typing import Callable, Dict, Optional

from PySide6.QtWidgets import QWidget

from .chat_message import (
    Segment, SegmentKind, TextSegment, ThinkingSegment, ToolCallSegment,
)


__all__ = [
    'SegmentRendererFn',
    'register_segment_renderer',
    'unregister_segment_renderer',
    'resolve_segment_renderer',
    'registered_segment_kinds',
]


# Renderer 函数签名: (segment, parent, code_max_visible_lines) -> widget.
# code_max_visible_lines 由 AgentBubbleBody 注入, 让 renderer 给内嵌 CodeBlock
# 设上限. 不需要的 renderer 可以忽略此参数.
SegmentRendererFn = Callable[[Segment, Optional[QWidget], int], QWidget]


_REGISTRY: Dict[SegmentKind, SegmentRendererFn] = {}


def register_segment_renderer(kind: SegmentKind,
                              renderer: SegmentRendererFn) -> None:
    """注册某 segment 类型的渲染器. 同 kind 重复注册会覆盖前者.

    Args:
        kind: 要注册的段类型.
        renderer: 创建该段对应 widget 的函数, 签名 ``(segment, parent,
                  code_max_visible_lines) -> QWidget``.
    """
    _REGISTRY[kind] = renderer


def unregister_segment_renderer(kind: SegmentKind) -> None:
    """从注册表中移除某 segment 类型. 未注册的 kind 静默忽略."""
    _REGISTRY.pop(kind, None)


def resolve_segment_renderer(
    kind: SegmentKind,
) -> Optional[SegmentRendererFn]:
    """返回某 segment 类型的渲染器, 未注册时返回 ``None`` (调用方应回退到
    placeholder).
    """
    return _REGISTRY.get(kind)


def registered_segment_kinds() -> Dict[SegmentKind, SegmentRendererFn]:
    """返回当前注册表副本 (供调试 / 测试用)."""
    return dict(_REGISTRY)


# ----------------------------------------------------------------------
# 内置 renderer
# ----------------------------------------------------------------------

def _renderText(segment: Segment, parent: Optional[QWidget],
                code_max_visible_lines: int) -> QWidget:
    from .markdown_view import MarkdownView
    assert isinstance(segment, TextSegment)
    view = MarkdownView(segment.content, parent)
    view.setCodeBlockMaxVisibleLines(code_max_visible_lines)
    return view


def _renderThinking(segment: Segment, parent: Optional[QWidget],
                    code_max_visible_lines: int) -> QWidget:
    from .thinking_card import ThinkingCard
    assert isinstance(segment, ThinkingSegment)
    card = ThinkingCard(parent)
    card.setCodeBlockMaxVisibleLines(code_max_visible_lines)
    card.setSegment(segment)
    return card


def _renderToolCall(segment: Segment, parent: Optional[QWidget],
                    code_max_visible_lines: int) -> QWidget:
    """创建工具调用卡片. 通过 ``tool_renderers`` 注册表解析特化 card,
    失败时回退 ``GenericToolCallCard``.
    """
    from .tool_call_card import GenericToolCallCard
    assert isinstance(segment, ToolCallSegment)
    try:
        from .tool_renderers import resolveToolRenderer
        factory = resolveToolRenderer(segment.tool_name)
        card = factory(parent)
    except Exception:  # pragma: no cover - 注册表异常时 fallback
        card = GenericToolCallCard(parent)
    card.setCodeBlockMaxVisibleLines(code_max_visible_lines)
    card.setSegment(segment)
    return card


def _renderTaskList(segment: Segment, parent: Optional[QWidget],
                    code_max_visible_lines: int) -> QWidget:
    """P2d: 创建 TaskListCard."""
    from ._task_list_card import TaskListCard
    from .chat_message import TaskListSegment
    assert isinstance(segment, TaskListSegment)
    card = TaskListCard(parent)
    card.setSegment(segment)
    return card


def _register_builtins() -> None:
    """模块加载时把 4 个内置 segment 类型挂上去.

    TEXT / THINKING / TOOL_CALL 是从一开始就内置的;
    TASK_LIST 是 P2d 新增, 通过注册表挂入, 不需要改 ``AgentBubbleBody``.
    """
    register_segment_renderer(SegmentKind.TEXT, _renderText)
    register_segment_renderer(SegmentKind.THINKING, _renderThinking)
    register_segment_renderer(SegmentKind.TOOL_CALL, _renderToolCall)
    register_segment_renderer(SegmentKind.TASK_LIST, _renderTaskList)


_register_builtins()
