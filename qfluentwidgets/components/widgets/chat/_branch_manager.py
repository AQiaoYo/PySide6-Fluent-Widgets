# coding: utf-8
"""``AgentChatView`` 的对话分叉子领域 (extracted in cleanup phase).

把 "用户编辑某条 USER 消息时, 把它后面的整段对话存档为 v0, 创建 v1 新分支,
之后用 ◀ {n}/{N} ▶ 选页器在不同版本间切换" 的 ~250 行逻辑从主类抽出来.

数据模型 (本模块独占, 主类不再持有):

    _branchPoints: Dict[anchor_id, _BranchPoint]
        所有分叉点; key 是该 user 消息第一个版本的 id.

    _anchorOf: Dict[user_msg_id, anchor_id]
        让任意可见 user_msg id 都能反查到 anchor_id.

    _MessageVersion(user_message, tail_messages)
        一个分叉版本 = (user_msg 变体 + 它的整段后续消息).

    _BranchPoint(versions, active)
        同一条 USER 消息的所有版本.

公共方法 (view 通过 facade 转发):
    editAndFork(user_msg_id, new_content) -> str
    switchVersion(user_msg_id, new_index) -> str
    versionInfo(user_msg_id) -> Optional[Tuple[int, int]]
    isAnchor(user_msg_id) -> bool

依赖 view 的:
    view._bubbles  (msg_id -> ChatBubble)
    view._order    (List[str])
    view.addMessage(msg) / view.removeMessage(msg_id)
    view._refreshScrollState (jumpBtn 状态刷新, 内容跳变后调)
    view.userMessageEdited.emit(...)
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from PySide6.QtCore import QTimer

from .chat_message import ChatMessage, ChatRole


if TYPE_CHECKING:  # pragma: no cover
    from .agent_chat_view import AgentChatView


__all__ = ['_BranchManager', '_BranchPoint', '_MessageVersion']


@dataclass
class _MessageVersion:
    """一个分叉版本 = (user_msg 变体 + 它的整段后续消息).

    Attributes:
        user_message:  这个版本里的用户消息 (id 不同的 ChatMessage).
        tail_messages: user_message 之后的所有消息 (AGENT/USER/SYSTEM 都算).
    """

    user_message: ChatMessage
    tail_messages: List[ChatMessage] = field(default_factory=list)


@dataclass
class _BranchPoint:
    """一个分叉点 = 同一条 USER 消息的所有版本.

    在第一次编辑该 USER 消息时创建; ``versions[0]`` = 编辑前的原始内容 + 当时
    的对话尾段; ``versions[1..n]`` = 之后每次编辑产生的新版本. ``active``
    指向当前 UI 上可见的那个版本下标.
    """

    versions: List[_MessageVersion] = field(default_factory=list)
    active: int = 0


class _BranchManager:
    """对话分叉管理器. 通过 composition 持有对 view 的反向引用."""

    def __init__(self, view: 'AgentChatView'):
        self._view = view
        self._points: Dict[str, _BranchPoint] = {}
        self._anchorOf: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def anchorOf(self, user_msg_id: str) -> Optional[str]:
        return self._anchorOf.get(user_msg_id)

    def isAnchor(self, user_msg_id: str) -> bool:
        return user_msg_id in self._anchorOf

    def versionInfo(self, user_msg_id: str) -> Optional[Tuple[int, int]]:
        anchor_id = self._anchorOf.get(user_msg_id)
        if anchor_id is None:
            return None
        bp = self._points.get(anchor_id)
        if bp is None or len(bp.versions) <= 1:
            return None
        return (len(bp.versions), bp.active)

    # ------------------------------------------------------------------
    # editAndFork
    # ------------------------------------------------------------------

    def editAndFork(self, user_msg_id: str, new_content: str) -> str:
        """编辑某条 USER 消息并在该消息处生成新分支."""
        view = self._view
        if user_msg_id not in view._order:
            return user_msg_id
        bubble = view._bubbles.get(user_msg_id)
        if bubble is None or bubble.message().role != ChatRole.USER:
            return user_msg_id

        idx = view._order.index(user_msg_id)
        anchor_id = self._anchorOf.get(user_msg_id, user_msg_id)

        bp = self._points.get(anchor_id)
        if bp is None:
            # 第一次编辑 -> 把当前状态作为 versions[0] 存档
            v0_user = bubble.message()
            v0_tail = [
                view._bubbles[mid].message()
                for mid in view._order[idx + 1:]
                if mid in view._bubbles
            ]
            bp = _BranchPoint(versions=[_MessageVersion(v0_user, v0_tail)])
            self._points[anchor_id] = bp
            self._anchorOf[user_msg_id] = anchor_id
        else:
            # 已存在分叉 -> 把当前状态写到当前活动版本
            cur_v = bp.versions[bp.active]
            cur_v.user_message = bubble.message()
            cur_v.tail_messages = [
                view._bubbles[mid].message()
                for mid in view._order[idx + 1:]
                if mid in view._bubbles
            ]

        # 构造新版本
        new_msg = ChatMessage(role=ChatRole.USER, content=new_content)
        bp.versions.append(_MessageVersion(new_msg, []))
        bp.active = len(bp.versions) - 1
        self._anchorOf[new_msg.id] = anchor_id

        # 视图重建: 删 user_msg 及其后所有气泡, 加回新 user_msg
        for mid in list(view._order[idx:]):
            view.removeMessage(mid)
        new_bubble = view.addMessage(new_msg)
        new_bubble.setVersionInfo(len(bp.versions), bp.active)

        # 内容跳变后 viewport 距底距离会突变, 等 layout 跑完再刷一次 jumpBtn,
        # 避免切到更短分支后 jumpBtn 残留 visible.
        QTimer.singleShot(0, view._refreshScrollState)

        view.userMessageEdited.emit(new_msg.id, new_content)
        return new_msg.id

    # ------------------------------------------------------------------
    # switchVersion
    # ------------------------------------------------------------------

    def switchVersion(self, user_msg_id: str, new_index: int) -> str:
        """切换到该 USER 消息的某个版本."""
        view = self._view
        anchor_id = self._anchorOf.get(user_msg_id)
        if anchor_id is None:
            return user_msg_id
        bp = self._points.get(anchor_id)
        if bp is None or not (0 <= new_index < len(bp.versions)):
            return user_msg_id
        if new_index == bp.active:
            return user_msg_id
        if user_msg_id not in view._order:
            return user_msg_id

        idx = view._order.index(user_msg_id)

        # 写回当前活动版本的 tail
        cur_v = bp.versions[bp.active]
        cur_v.user_message = view._bubbles[user_msg_id].message()
        cur_v.tail_messages = [
            view._bubbles[mid].message()
            for mid in view._order[idx + 1:]
            if mid in view._bubbles
        ]

        # 切版本
        bp.active = new_index
        target = bp.versions[new_index]

        # 视图重建
        for mid in list(view._order[idx:]):
            view.removeMessage(mid)
        self._anchorOf[target.user_message.id] = anchor_id
        new_bubble = view.addMessage(target.user_message)
        new_bubble.setVersionInfo(len(bp.versions), bp.active)
        for tm in target.tail_messages:
            tm_bubble = view.addMessage(tm)
            # 多层分叉: tail 里的 user 消息可能也是分叉点 (用户在 v0 里又
            # 编辑过它). 重建时同步更新内部 bp.active 并恢复选页器 UI.
            if tm.role != ChatRole.USER:
                continue
            inner_anchor = self._anchorOf.get(tm.id)
            if inner_anchor is None or inner_anchor not in self._points:
                continue
            inner_bp = self._points[inner_anchor]
            for i, v in enumerate(inner_bp.versions):
                if v.user_message.id == tm.id:
                    inner_bp.active = i
                    break
            tm_bubble.setVersionInfo(len(inner_bp.versions), inner_bp.active)

        QTimer.singleShot(0, view._refreshScrollState)
        return target.user_message.id
