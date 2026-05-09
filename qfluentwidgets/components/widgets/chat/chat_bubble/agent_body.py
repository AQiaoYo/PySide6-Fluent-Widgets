# coding: utf-8
"""AGENT 角色 ChatBubble body.

视觉: 平铺布局 (timeline). 顶部 [小头像 + 发送者名 + subtitle], 中间是
按 ``message.segments`` 顺序渲染的 timeline 容器 (TextSegment ->
MarkdownView, ThinkingSegment -> ThinkingCard, ToolCallSegment ->
ToolCallCardBase 子类), 底部是操作栏.

支持流式追加 (``appendDelta``), 思考/工具调用插入 (``ensureThinking``,
``addToolCall``), 中断标记 (``markStopped``), 重新生成按钮 (``setRegenerateEnabled``).
"""

from typing import Dict, Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ...label import CaptionLabel, StrongBodyLabel
from ..chat_avatar import ChatAvatar
from ..chat_message import (
    ChatMessage, ChatRole, Segment, TextSegment,
    ThinkingSegment, ToolCallSegment,
)
from ..markdown_view import MarkdownView
from ..segment_renderers import resolve_segment_renderer
from ..thinking_card import ThinkingCard
from ..tool_call_card import ToolCallCardBase
from ._action_bar import BubbleActionBar
from ._body_base import BubbleAction, BubbleBodyBase


__all__ = ['AgentBubbleBody']


class AgentBubbleBody(BubbleBodyBase):
    """AGENT 角色气泡 body — 平铺 timeline 布局."""

    _FLAT_HEADER_AVATAR_SIZE = 28

    def __init__(self, message: ChatMessage,
                 parent: Optional[QWidget] = None):
        super().__init__(message, parent)
        assert message.role == ChatRole.AGENT

        # AGENT 模式: timeline 容器 + segment.id -> widget 索引
        self._segmentWidgets: Dict[str, QWidget] = {}
        # 流式中断时显示的 "已停止 [继续生成]" 行 (默认 hide). P2c 从纯
        # CaptionLabel 升级为 QWidget (label + Resume 按钮), 让用户可以从
        # 断点续写.
        self._stoppedRow: Optional[QWidget] = None

        # 操作栏 (AGENT: 复制 + 重生成 (默认隐藏) + 删除).
        # 3 个按钮 signal 通过适配器统一翻成 ``actionTriggered`` 上的 action ID.
        self._actionBar = BubbleActionBar(message.id, ChatRole.AGENT, self)
        self._actionBar.copyClicked.connect(self._emitCopy)
        self._actionBar.deleteClicked.connect(self._emitDelete)
        self._actionBar.regenerateClicked.connect(self._emitRegenerate)

        self._setupUi()
        self.applyMessage()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(8, 6, 8, 6)
        rootLayout.setSpacing(8)

        # ---- 顶部: [小头像] [name + subtitle 列, 左对齐] [stretch] ----
        headerRow = QWidget(self)
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(10)

        self._avatar = ChatAvatar(
            ChatRole.AGENT, self._FLAT_HEADER_AVATAR_SIZE, headerRow,
        )

        textCol = QWidget(headerRow)
        textColLayout = QVBoxLayout(textCol)
        textColLayout.setContentsMargins(0, 0, 0, 0)
        textColLayout.setSpacing(0)

        self._senderLabel = StrongBodyLabel(self.displayName(), textCol)
        self._senderLabel.setObjectName("senderName")
        self._senderLabel.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        self._subtitleLabel = CaptionLabel("", textCol)
        self._subtitleLabel.setObjectName("senderSubtitle")
        self._subtitleLabel.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        self._subtitleLabel.hide()

        textColLayout.addWidget(self._senderLabel, 0, Qt.AlignmentFlag.AlignLeft)
        textColLayout.addWidget(self._subtitleLabel, 0, Qt.AlignmentFlag.AlignLeft)

        headerLayout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(textCol, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)

        # ---- timeline 容器: 按 segments 顺序渲染 ----
        # 横向 Expanding: 子项 sizeHint 不能反向撑大 timelineWrap.
        self._timelineWrap = QFrame(self)
        self._timelineWrap.setObjectName("timelineWrap")
        self._timelineWrap.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True,
        )
        self._timelineLayout = QVBoxLayout(self._timelineWrap)
        self._timelineLayout.setContentsMargins(0, 0, 0, 0)
        self._timelineLayout.setSpacing(8)
        self._timelineWrap.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )
        self._timelineWrap.setMaximumWidth(self._MAX_CONTENT_WIDTH)

        # ---- 操作行: 左对齐, 与 timeline 同左缘 ----
        actionRow = QWidget(self)
        actionRowLayout = QHBoxLayout(actionRow)
        actionRowLayout.setContentsMargins(0, 0, 0, 0)
        actionRowLayout.setSpacing(0)
        actionRowLayout.addWidget(self._actionBar)
        actionRowLayout.addStretch(1)

        rootLayout.addWidget(headerRow)
        rootLayout.addWidget(self._timelineWrap)
        rootLayout.addWidget(actionRow)

    # ------------------------------------------------------------------
    # 数据 -> UI
    # ------------------------------------------------------------------

    def applyMessage(self) -> None:
        self._avatar.setAvatar(self._message.avatar)
        self._senderLabel.setText(self.displayName())

        sub = self._message.subtitle
        if sub:
            self._subtitleLabel.setText(sub)
            self._subtitleLabel.show()
        else:
            self._subtitleLabel.hide()

        self._clearTimeline()
        for seg in self._message.segments:
            self._appendSegmentWidget(seg)

    def appendDelta(self, delta: str) -> None:
        if not delta:
            return
        # 末尾是 TextSegment 则原地追加, 否则新建 TextSegment + widget
        last = self._message.segments[-1] if self._message.segments else None
        if isinstance(last, TextSegment):
            last.content += delta
            view = self._segmentWidgets.get(last.id)
            if isinstance(view, MarkdownView):
                view.appendMarkdown(delta)
        else:
            seg = TextSegment(content=delta)
            self._message.segments.append(seg)
            self._appendSegmentWidget(seg)

    def setContent(self, markdown: str) -> None:
        # 走 ChatMessage.content setter, 它会规整 segments 末尾 TextSegment
        self._message.content = markdown

        # 删掉所有现存 TextSegment 对应的 widget; 然后定位 message setter
        # 刚追加到末尾的 TextSegment 并补一个 widget.
        text_seg_ids = {
            sid for sid in self._segmentWidgets
            if isinstance(self._segmentWidgets[sid], MarkdownView)
        }
        for sid in text_seg_ids:
            w = self._segmentWidgets.pop(sid, None)
            if w is not None:
                self._timelineLayout.removeWidget(w)
                w.setParent(None)
                w.deleteLater()

        if (self._message.segments
                and isinstance(self._message.segments[-1], TextSegment)):
            tail = self._message.segments[-1]
            if tail.id not in self._segmentWidgets:
                self._appendSegmentWidget(tail)

    def setSubtitle(self, text: Optional[str]) -> None:
        super().setSubtitle(text)
        if text:
            self._subtitleLabel.setText(text)
            self._subtitleLabel.show()
        else:
            self._subtitleLabel.hide()

    def setUserAvatarFallback(self, avatar: Optional[Union[QIcon, str]]) -> None:
        if self._message.avatar is None:
            self._avatar.setAvatar(avatar)

    def setDefaultSenderName(self, name: Optional[str]) -> None:
        super().setDefaultSenderName(name)
        if not self._message.sender_name:
            self._senderLabel.setText(self.displayName())

    def setCodeBlockMaxVisibleLines(self, n: int) -> None:
        super().setCodeBlockMaxVisibleLines(n)
        for widget in self._segmentWidgets.values():
            if isinstance(widget, MarkdownView):
                widget.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)
            elif isinstance(widget, ThinkingCard):
                widget.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)
            elif isinstance(widget, ToolCallCardBase):
                widget.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)

    # ------------------------------------------------------------------
    # 重新生成 / 已停止
    # ------------------------------------------------------------------

    def setRegenerateEnabled(self, enabled: bool) -> None:
        self._actionBar.setRegenerateEnabled(enabled)

    def isRegenerateEnabled(self) -> bool:
        return self._actionBar.isRegenerateEnabled()

    def markStopped(self, stopped: bool = True) -> None:
        """标记流式被中断; 同时在 timeline 末尾显示 / 隐藏 "已停止 [继续生成]" 行.

        "继续生成" 链接触发 ``actionTriggered(RESUME, msg_id, None)``, 宿主
        通过 ``AgentChatView.resumeRequested(msg_id)`` 接收并从断点续写.
        """
        if stopped:
            self._ensureStoppedRow()
            self._stoppedRow.show()
        else:
            if self._stoppedRow is not None:
                self._stoppedRow.hide()

    def _ensureStoppedRow(self) -> None:
        """懒建 "已停止 [继续生成]" 行 (label + 链接按钮). 幂等."""
        if self._stoppedRow is not None:
            return
        row = QWidget(self._timelineWrap)
        row.setObjectName("bubbleStoppedRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = CaptionLabel(self.tr("已停止"), row)
        label.setObjectName("bubbleStoppedLabel")
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)

        # "继续生成" 用 TransparentToolButton 方便跟 Fluent 风格统一
        from ...button import TransparentPushButton
        resume_btn = TransparentPushButton(self.tr("继续生成"), row)
        resume_btn.setObjectName("bubbleResumeButton")
        resume_btn.clicked.connect(self._emitResume)
        layout.addWidget(resume_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

        self._timelineLayout.addWidget(row)
        self._stoppedRow = row

    def _emitResume(self) -> None:
        """继续生成 按钮点击 -> actionTriggered(RESUME, msg_id, None)."""
        self.actionTriggered.emit(
            BubbleAction.RESUME, self._message.id, None,
        )

    # ------------------------------------------------------------------
    # Thinking / Tool call
    # ------------------------------------------------------------------

    def thinkingCard(self) -> Optional[ThinkingCard]:
        last_card: Optional[ThinkingCard] = None
        last_unfinished: Optional[ThinkingCard] = None
        for seg in self._message.segments:
            if isinstance(seg, ThinkingSegment):
                w = self._segmentWidgets.get(seg.id)
                if isinstance(w, ThinkingCard):
                    last_card = w
                    if not seg.finished:
                        last_unfinished = w
        return last_unfinished or last_card

    def ensureThinking(self) -> ThinkingCard:
        last = self._message.segments[-1] if self._message.segments else None
        if isinstance(last, ThinkingSegment) and not last.finished:
            w = self._segmentWidgets.get(last.id)
            if isinstance(w, ThinkingCard):
                return w
            return self._appendSegmentWidget(last)  # type: ignore[return-value]

        seg = ThinkingSegment()
        self._message.segments.append(seg)
        return self._appendSegmentWidget(seg)  # type: ignore[return-value]

    def addToolCall(self, segment: ToolCallSegment) -> ToolCallCardBase:
        existing = self._segmentWidgets.get(segment.id)
        if isinstance(existing, ToolCallCardBase):
            return existing

        if segment not in self._message.segments:
            self._message.segments.append(segment)
        return self._appendSegmentWidget(segment)  # type: ignore[return-value]

    def toolCallCard(self, call_id: str) -> Optional[ToolCallCardBase]:
        w = self._segmentWidgets.get(call_id)
        return w if isinstance(w, ToolCallCardBase) else None

    def toolCallCards(self) -> Dict[str, ToolCallCardBase]:
        return {
            sid: w for sid, w in self._segmentWidgets.items()
            if isinstance(w, ToolCallCardBase)
        }

    # ------------------------------------------------------------------
    # 内部: timeline 管理
    # ------------------------------------------------------------------

    def _clearTimeline(self) -> None:
        for sid, w in list(self._segmentWidgets.items()):
            self._timelineLayout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self._segmentWidgets.clear()

    def _appendSegmentWidget(self, segment: Segment) -> QWidget:
        """根据 ``segment.kind`` 走 segment_renderers 注册表创建 widget.

        新增 segment 类型时只需调 ``register_segment_renderer`` 注册渲染器,
        本方法不需要改动 (P2a).

        渲染器注册表里没有的 kind 会回退到一个空 ``QWidget`` placeholder,
        避免崩.
        """
        renderer = resolve_segment_renderer(segment.kind)
        if renderer is None:
            widget: QWidget = QWidget(self._timelineWrap)
        else:
            widget = renderer(
                segment, self._timelineWrap, self._codeMaxVisibleLines,
            )

        # ToolCallSegment 创建出的 ToolCallCardBase 需要把审批信号转发到
        # body 的 actionTriggered. 其它 segment 不需要这一步.
        if isinstance(segment, ToolCallSegment) and isinstance(widget, ToolCallCardBase):
            self._wireToolCallCard(widget, segment)

        self._timelineLayout.addWidget(widget)
        self._segmentWidgets[segment.id] = widget
        return widget

    def _wireToolCallCard(self, card: ToolCallCardBase,
                          segment: ToolCallSegment) -> None:
        """把卡片的 4 个审批按钮翻译成 ``actionTriggered`` 上的 4 个 TOOL_*
        action, payload = call_id (str).
        """
        msg_id = self._message.id
        call_id = segment.id
        card.approveClicked.connect(
            lambda mid=msg_id, cid=call_id:
            self.actionTriggered.emit(BubbleAction.TOOL_APPROVE, mid, cid)
        )
        card.rejectClicked.connect(
            lambda mid=msg_id, cid=call_id:
            self.actionTriggered.emit(BubbleAction.TOOL_REJECT, mid, cid)
        )
        card.alwaysAllowClicked.connect(
            lambda mid=msg_id, cid=call_id:
            self.actionTriggered.emit(BubbleAction.TOOL_ALWAYS_ALLOW, mid, cid)
        )
        card.alwaysRejectClicked.connect(
            lambda mid=msg_id, cid=call_id:
            self.actionTriggered.emit(BubbleAction.TOOL_ALWAYS_REJECT, mid, cid)
        )

    # ------------------------------------------------------------------
    # actionBar -> actionTriggered 适配器
    # ------------------------------------------------------------------

    def _emitCopy(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.COPY, msg_id, None)

    def _emitDelete(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.DELETE, msg_id, None)

    def _emitRegenerate(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.REGENERATE, msg_id, None)

    # ------------------------------------------------------------------
    # 操作栏 always-visible / hover-fade
    # ------------------------------------------------------------------

    def setActionsAlwaysVisible(self, always: bool) -> None:
        self._actionBar.setAlwaysVisible(always)

    def actionsAlwaysVisible(self) -> bool:
        return self._actionBar.alwaysVisible()

    def onBubbleEnterEvent(self) -> None:
        self._actionBar.fadeIn()

    def onBubbleLeaveEvent(self) -> None:
        self._actionBar.fadeOut()
