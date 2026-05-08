# coding: utf-8
"""聊天消息视图容器

可滚动的消息容器, 自上而下垂直排列 ChatBubble. 支持自动滚到底、用户上滚
时暂停自动滚动, 提供 addMessage / appendDelta / removeMessage / clear 等
高层 API, 转发各 bubble 的复制 / 编辑 / 删除信号.
"""

from typing import Dict, List, Optional, Union

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QClipboard, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ....common.overload import singledispatchmethod
from ..button import PillPushButton
from ..scroll_area import SmoothScrollArea
from .chat_bubble import ChatBubble
from .chat_message import ChatMessage, ChatRole


__all__ = ['ChatView']


class ChatView(SmoothScrollArea):
    """聊天消息视图容器

    管理一个垂直消息流, 提供消息增删改查与流式追加 API. 自动滚到底, 当用户
    主动向上滚动 (距底 > 100px) 时暂停, 距底 < 30px 时恢复自动滚到底.

    信号:
        messageCopied(str):          复制消息时发出 (参数为 message id)
        messageEditRequested(str):   请求编辑消息时发出 (参数为 message id)
        messageDeleteRequested(str): 请求删除消息时发出 (参数为 message id)
        lastMessageChanged():        当前最后一条消息内容变化时发出

    构造函数重载:
        * ChatView(parent: QWidget = None)
    """

    messageCopied = Signal(str)
    messageEditRequested = Signal(str)
    messageDeleteRequested = Signal(str)
    lastMessageChanged = Signal()

    _SCROLL_BOTTOM_THRESHOLD = 30
    _SCROLL_PAUSE_THRESHOLD = 100
    # 默认最大内容宽度 (类似 ChatGPT/DeepSeek 的对话栏宽度).
    # 设为 0 即不限制 (内容铺满整个 viewport).
    _DEFAULT_MAX_CONTENT_WIDTH = 760

    @singledispatchmethod
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化 ChatView

        Args:
            parent: 父级 QWidget, 默认 None
        """
        super().__init__(parent)
        self._postInit()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _postInit(self):
        self.setObjectName("chatView")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 外层 container 横向占满 viewport, 内层 inner 受最大宽度限制并居中.
        # 结构: container[ stretch | inner | stretch ]
        self._container = QWidget(self)
        self._container.setObjectName("chatScrollContainer")
        self._container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setWidget(self._container)

        self._outerLayout = QHBoxLayout(self._container)
        self._outerLayout.setContentsMargins(0, 0, 0, 0)
        self._outerLayout.setSpacing(0)

        self._inner = QWidget(self._container)
        self._inner.setObjectName("chatContent")
        # Expanding: 在 maximumWidth 限制下撑满, 让两侧 stretch 平均分配剩余空间
        self._inner.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._outerLayout.addStretch(1)
        self._outerLayout.addWidget(self._inner, 0)
        self._outerLayout.addStretch(1)

        self._maxContentWidth = self._DEFAULT_MAX_CONTENT_WIDTH
        self._applyMaxContentWidth()

        self._vLayout = QVBoxLayout(self._inner)
        self._vLayout.setContentsMargins(20, 16, 20, 16)
        self._vLayout.setSpacing(16)
        self._vLayout.addStretch(1)

        self._bubbles: Dict[str, ChatBubble] = {}
        self._order: List[str] = []
        self._autoScroll = True
        self._userAvatar: Optional[Union[QIcon, str]] = None
        self._agentAvatar: Optional[Union[QIcon, str]] = None
        self._userDisplayName: Optional[str] = None
        self._agentDisplayName: Optional[str] = None

        # 「回到最新」浮动按钮 (挂在 viewport 上层, 否则会被滚动内容盖住)
        self._jumpBtn = PillPushButton(FluentIcon.DOWN, self.tr("回到最新"), self.viewport())
        self._jumpBtn.setCheckable(False)
        self._jumpBtn.hide()
        self._jumpBtn.clicked.connect(self._scrollToBottom)
        self._jumpBtn.setFixedHeight(32)

        # 滚动监听
        self.verticalScrollBar().valueChanged.connect(self._onScrollChanged)
        self.verticalScrollBar().rangeChanged.connect(self._onRangeChanged)

        FluentStyleSheet.CHAT_VIEW.apply(self)
        FluentStyleSheet.CHAT_VIEW.apply(self._container)
        FluentStyleSheet.CHAT_VIEW.apply(self._inner)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addMessage(self, message: ChatMessage) -> ChatBubble:
        """追加一条消息.

        Args:
            message: ChatMessage 实例

        Returns:
            创建的 ChatBubble (已加入布局)
        """
        bubble = ChatBubble(message, self._inner)
        # 应用默认头像 + 默认显示名 fallback
        if message.role == ChatRole.USER:
            bubble.setUserAvatarFallback(self._userAvatar)
            bubble.setDefaultSenderName(self._userDisplayName)
        elif message.role == ChatRole.AGENT:
            bubble.setUserAvatarFallback(self._agentAvatar)
            bubble.setDefaultSenderName(self._agentDisplayName)

        bubble.copyClicked.connect(self._onCopyRequested)
        bubble.editClicked.connect(self.messageEditRequested)
        bubble.deleteClicked.connect(self.messageDeleteRequested)

        # 插入到 stretch 之前
        insert_index = self._vLayout.count() - 1
        self._vLayout.insertWidget(insert_index, bubble)

        self._bubbles[message.id] = bubble
        self._order.append(message.id)
        self.lastMessageChanged.emit()

        if self._autoScroll:
            # 不主动 scroll: bubble 加入 → layout 异步更新 → scrollbar
            # range 变化 → _onRangeChanged 同步滚到底, 与内容增长同步.
            pass
        else:
            self._jumpBtn.show()

        return bubble

    def appendDelta(self, message_id: str, delta: str) -> None:
        """流式追加内容到指定消息.

        Args:
            message_id: 目标消息 id (来自 addMessage 时使用的 ChatMessage.id)
            delta:      新增 markdown 文本片段
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None or not delta:
            return
        bubble.appendDelta(delta)
        self.lastMessageChanged.emit()
        # 不主动 scroll, 等 markdown 渲染 + layout 跑完, _onRangeChanged
        # 会同步把 viewport 贴到底, 避免"先追加内容后滚到底"的两步抖动.

    def removeMessage(self, message_id: str) -> None:
        """删除指定消息."""
        bubble = self._bubbles.pop(message_id, None)
        if bubble is None:
            return
        self._vLayout.removeWidget(bubble)
        bubble.setParent(None)
        bubble.deleteLater()
        if message_id in self._order:
            self._order.remove(message_id)

    def clear(self) -> None:
        """清空所有消息."""
        for mid in list(self._order):
            self.removeMessage(mid)

    def messages(self) -> List[ChatMessage]:
        """按时间顺序返回当前所有消息 (返回的是引用列表)."""
        return [self._bubbles[mid].message() for mid in self._order if mid in self._bubbles]

    def setUserAvatar(self, avatar: Optional[Union[QIcon, str]]) -> None:
        """设置用户消息默认头像 (后续 addMessage 时生效)."""
        self._userAvatar = avatar

    def setAgentAvatar(self, avatar: Optional[Union[QIcon, str]]) -> None:
        """设置 Agent 消息默认头像 (后续 addMessage 时生效)."""
        self._agentAvatar = avatar

    def setUserDisplayName(self, name: Optional[str]) -> None:
        """设置用户消息默认发送者名 (后续 addMessage 时生效).

        优先级: ChatMessage.sender_name > 此默认名 > "您".
        """
        self._userDisplayName = name

    def setAgentDisplayName(self, name: Optional[str]) -> None:
        """设置 Agent 消息默认发送者名 (后续 addMessage 时生效, 如 "DeepSeek V4").

        优先级: ChatMessage.sender_name > 此默认名 > "Agent".
        """
        self._agentDisplayName = name

    def setMaxContentWidth(self, width: int) -> None:
        """设置消息内容最大宽度 (类 ChatGPT/DeepSeek 居中布局).

        Args:
            width: 最大像素宽度. 设为 0 或负数表示不限制 (内容铺满 viewport).
        """
        self._maxContentWidth = max(0, int(width))
        self._applyMaxContentWidth()

    def maxContentWidth(self) -> int:
        """获取当前最大内容宽度 (0 表示无限制)."""
        return self._maxContentWidth

    def _applyMaxContentWidth(self):
        """根据 _maxContentWidth 调整 inner 容器宽度策略.

        inner 始终 Expanding; 通过 maximumWidth 限制上限,
        两侧 stretch 把剩余空间平分实现居中.
        设为 0 时取消上限, inner 铺满整个 viewport.
        """
        # QWIDGETSIZE_MAX = 16777215 (Qt 内部上限)
        if self._maxContentWidth > 0:
            self._inner.setMaximumWidth(self._maxContentWidth)
        else:
            self._inner.setMaximumWidth(16777215)

    def setAutoScroll(self, enabled: bool) -> None:
        """显式控制是否自动滚到底."""
        self._autoScroll = bool(enabled)
        if self._autoScroll:
            self._jumpBtn.hide()
            self._scrollToBottom()

    def autoScroll(self) -> bool:
        return self._autoScroll

    # ------------------------------------------------------------------
    # 内部信号转发
    # ------------------------------------------------------------------

    def _onCopyRequested(self, message_id: str):
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(bubble.message().content)
        self.messageCopied.emit(message_id)

    # ------------------------------------------------------------------
    # 滚动逻辑
    # ------------------------------------------------------------------

    def _scrollToBottom(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _distanceToBottom(self) -> int:
        bar = self.verticalScrollBar()
        return bar.maximum() - bar.value()

    def _onScrollChanged(self, _value: int):
        dist = self._distanceToBottom()
        if dist > self._SCROLL_PAUSE_THRESHOLD and self._autoScroll:
            self._autoScroll = False
            self._jumpBtn.show()
            self._positionJumpButton()
        elif dist < self._SCROLL_BOTTOM_THRESHOLD and not self._autoScroll:
            self._autoScroll = True
            self._jumpBtn.hide()

    def _onRangeChanged(self, _min: int, _max: int):
        # 同步滚到底.
        # rangeChanged 在 Qt 完成 layout 重新计算后才发出, 此时 maximum 是
        # 内容稳定后的真值, 立即 setValue(maximum) 能让 viewport 与内容
        # 增长保持完美同步, 不会出现"内容已增长但 scroll 还没跟上"的滞后.
        if self._autoScroll:
            self._scrollToBottom()

    # ------------------------------------------------------------------
    # 浮动按钮定位
    # ------------------------------------------------------------------

    def _positionJumpButton(self):
        if not self._jumpBtn.isVisible():
            return
        vp = self.viewport()
        btnSize = self._jumpBtn.sizeHint()
        x = (vp.width() - btnSize.width()) // 2
        y = vp.height() - btnSize.height() - 16
        self._jumpBtn.setGeometry(x, y, btnSize.width(), btnSize.height())
        self._jumpBtn.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._positionJumpButton()
