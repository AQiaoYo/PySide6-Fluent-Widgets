# coding: utf-8
"""卡片高度展开 / 折叠工具

模块级辅助, 给 :class:`ThinkingCard` / :class:`ToolCallCardBase` /
:class:`GenerationStatusBar` 共用. 不暴露 public API, 仅在 chat 子包内部使用.

v11: ToolCallCard / ThinkingCard 的展开折叠改为瞬时 show/hide (不做动画).
CodeBlock / GenerationStatusBar 的动画保留不变.
begin_layout_animation / end_layout_animation 仍保留给 CodeBlock 使用.
"""

from typing import Callable, Optional

from PySide6.QtCore import QEasingCurve, Qt, QVariantAnimation
from PySide6.QtWidgets import QWidget


__all__ = [
    "animate_collapse",
    "animations_enabled_root",
    "begin_layout_animation",
    "end_layout_animation",
]


def _find_layout_anim_host(widget: QWidget) -> Optional[QWidget]:
    """沿 parent 链找最近提供 ``beginLayoutAnimation`` /
    ``endLayoutAnimation`` 的 ancestor (一般是 :class:`AgentChatView`).
    """
    w: Optional[QWidget] = widget
    while w is not None:
        begin = getattr(w, "beginLayoutAnimation", None)
        end = getattr(w, "endLayoutAnimation", None)
        if callable(begin) and callable(end):
            return w
        w = w.parentWidget()
    return None


def begin_layout_animation(widget: QWidget) -> Optional[QWidget]:
    """通知 ancestor view 进入 layout 动画会席 (CodeBlock 展开时使用)."""
    host = _find_layout_anim_host(widget)
    if host is not None:
        try:
            host.beginLayoutAnimation(widget)
        except TypeError:
            try:
                host.beginLayoutAnimation()
            except Exception:
                host = None
        except Exception:
            host = None
    return host


def end_layout_animation(host: Optional[QWidget]) -> None:
    """释放 layout 动画会席."""
    if host is None:
        return
    try:
        host.endLayoutAnimation()
    except Exception:
        pass


def animations_enabled_root(widget: QWidget) -> bool:
    """沿 parent 链向上查找最近的具备 ``_animationsEnabled`` 的容器,
    返回其总开关值. 找不到时默认返回 ``True``.
    """
    w: Optional[QWidget] = widget
    while w is not None:
        flag = getattr(w, "_animationsEnabled", None)
        if isinstance(flag, bool):
            return flag
        w = w.parentWidget()
    return True


def animate_collapse(
    widget: QWidget,
    expand: bool,
    duration: int = 180,
    easing: QEasingCurve.Type = QEasingCurve.Type.OutQuint,
    on_finished: Optional[Callable[[], None]] = None,
) -> Optional[QVariantAnimation]:
    """瞬时展开 / 折叠 widget (不做动画).

    保留函数签名以兼容现有调用方. 返回 None (无动画对象).
    """
    widget.setVisible(expand)
    if on_finished is not None:
        try:
            on_finished()
        except Exception:
            pass
    return None
