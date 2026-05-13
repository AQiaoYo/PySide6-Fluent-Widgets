# coding: utf-8
"""Agent 聊天面板 (消息流 + 输入框)

提供两类组件:

* :class:`ChatInputEdit`
    Agent 场景定制的多行输入框. 继承 ``PlainTextEdit`` 不动原组件, 在自身
    内部叠加 [+ 附件] / [↑ 圆形发送] 按钮 (用 ``setViewportMargins`` 给文
    本预留底部空间, 避免与按钮重叠), 而不是用外层 "卡片" 容器把 textedit
    + 按钮拼起来. 视觉上按钮就是输入框的一部分, 跟 ChatGPT / Claude 同款.

* :class:`AgentChatPanel`
    完整聊天面板 = ``AgentChatView`` (消息流) + ``ChatInputEdit`` (输入框).
    输入框宽度严格等于消息区 inner 宽度 (``setFixedWidth(min(viewport,
    maxContentWidth))``), 跟 ChatGPT / DeepSeek 居中布局视觉一致.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from .._clickable import ClickableWidget
from ..button import TransparentToolButton
from ..flyout import Flyout, FlyoutAnimationType, FlyoutViewBase
from ..icon_widget import IconWidget
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from ..line_edit import PlainTextEdit
from ..progress_bar import ProgressBar
from ..tool_tip import ToolTipFilter, ToolTipPosition
from .agent_chat_view import AgentChatView
from .chat_message import ChatMessage
from .generation_status_bar import GenerationStatusBar


__all__ = ['ChatInputEdit', 'AgentChatPanel']


class _TokenInfoFlyoutView(FlyoutViewBase):
    """Token 预估详情 Flyout 视图.

    显示在指示器上方, 内含:
    - 上下文条数: ``n / m`` + ProgressBar
    - 估算 Token 数: ``n / m`` + ProgressBar
    - 提示: 估算策略说明

    使用方式: ``Flyout.make(_TokenInfoFlyoutView(...), target=indicator, parent=window)``
    """

    _MIN_WIDTH = 280

    def __init__(self, context_used: int, context_max: int,
                 tokens_used: int, tokens_max: int,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(self._MIN_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # 标题
        titleLabel = StrongBodyLabel(self.tr("Token 用量"), self)
        layout.addWidget(titleLabel)

        # 上下文进度条
        layout.addLayout(self._buildRow(
            label=self.tr("上下文条数"),
            value_text=f"{context_used} / {context_max}" if context_max > 0 else f"{context_used}",
            ratio=self._safe_ratio(context_used, context_max),
        ))

        # Token 进度条
        layout.addLayout(self._buildRow(
            label=self.tr("预估 Token"),
            value_text=f"{tokens_used} / {tokens_max}" if tokens_max > 0 else f"{tokens_used}",
            ratio=self._safe_ratio(tokens_used, tokens_max),
        ))

        # 提示
        hint = CaptionLabel(self.tr("估算策略: ~4 字符 ≈ 1 token (粗略)"), self)
        hint.setObjectName("tokenInfoHint")
        layout.addWidget(hint)

    @staticmethod
    def _safe_ratio(used: int, max_: int) -> float:
        if max_ <= 0:
            return 0.0
        return min(1.0, max(0.0, used / max_))

    def _buildRow(self, label: str, value_text: str, ratio: float) -> QVBoxLayout:
        """构造一行: ``[label]  [value]\n[progress]``."""
        rowLayout = QVBoxLayout()
        rowLayout.setContentsMargins(0, 0, 0, 0)
        rowLayout.setSpacing(4)

        topRow = QHBoxLayout()
        topRow.setContentsMargins(0, 0, 0, 0)
        topRow.setSpacing(8)
        labelW = BodyLabel(label, self)
        valueW = CaptionLabel(value_text, self)
        valueW.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        topRow.addWidget(labelW, 1, Qt.AlignmentFlag.AlignLeft)
        topRow.addWidget(valueW, 0, Qt.AlignmentFlag.AlignRight)
        rowLayout.addLayout(topRow)

        bar = ProgressBar(self)
        bar.setRange(0, 1000)
        bar.setValue(int(ratio * 1000))
        bar.setTextVisible(False)
        bar.setFixedHeight(4)
        rowLayout.addWidget(bar)

        return rowLayout


class ChatInputEdit(PlainTextEdit):
    """Agent 聊天场景的多行输入框 (内嵌附件 / 发送按钮).

    与 ``PlainTextEdit`` 的区别:
    - **内部叠加** [+ 附件] (左下) 和 [↑ 圆形发送] (右下) 两个按钮 —
      不是外层 widget 拼凑, 是 PlainTextEdit 自身的 child, 通过
      ``setViewportMargins`` 给文本预留空间, 通过 ``resizeEvent`` 重新
      定位按钮. 视觉上按钮就是输入框的一部分.
    - **高度自适应** ``_MIN_HEIGHT`` ~ ``_MAX_HEIGHT`` (超出滚动)
    - **键盘绑定** Enter 发送 (非空时); Shift+Enter 换行
    - 输入空时发送按钮自动禁用

    信号:
        sendRequested(str):     发送时触发, 参数 = 文本
        attachmentRequested():  附件按钮触发
    """

    sendRequested = Signal(str)
    attachmentRequested = Signal()

    _MIN_HEIGHT = 104         # 默认 ~2 行可见 (含底部按钮区 48 + 文本区 ~56)
    _MAX_HEIGHT = 260         # 超出后内部滚动
    _BUTTON_SIZE = 32         # 附件 / 发送按钮共用尺寸 (圆形发送 = 直径)
    _BUTTON_PADDING = 8       # 按钮距输入框左/右/下边沿
    # 文本区底部预留: 按钮高度 + 上下留白
    _BOTTOM_RESERVE = _BUTTON_SIZE + _BUTTON_PADDING * 2

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("chatInputEdit")
        self.setPlaceholderText(self.tr("在这里输入消息, 按 Enter 发送"))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setViewportMargins(0, 0, 0, self._BOTTOM_RESERVE)
        self.setFixedHeight(self._MIN_HEIGHT)

        # 附件按钮 (左下)
        self._attachBtn = TransparentToolButton(FluentIcon.ADD, self)
        self._attachBtn.setObjectName("chatAttachButton")
        self._attachBtn.setFixedSize(self._BUTTON_SIZE, self._BUTTON_SIZE)
        self._attachBtn.setToolTip(self.tr("添加附件"))
        self._attachBtn.installEventFilter(
            ToolTipFilter(self._attachBtn, showDelay=300, position=ToolTipPosition.TOP)
        )
        self._attachBtn.clicked.connect(self.attachmentRequested.emit)

        # Token 预估指示器 (右下, 发送按钮左侧). 用户通过 setTokenInfo(...)
        # 更新 used / max 值; 默认隐藏, 直到首次 setTokenInfo 调用.
        # ``_lastTokenInfo`` 缓存最近一次 setTokenInfo 的参数, click 弹
        # Flyout 时直接读这份快照 (省得 flyout view 反复持有 indicator 引用).
        self._lastTokenInfo: tuple = (0, 0, 0, 0)
        self._tokenIndicator = self._buildTokenIndicator()

        # 圆形发送按钮 (右下)
        self._sendBtn = TransparentToolButton(FluentIcon.UP, self)
        self._sendBtn.setObjectName("chatSendButton")
        self._sendBtn.setFixedSize(self._BUTTON_SIZE, self._BUTTON_SIZE)
        self._sendBtn.setToolTip(self.tr("发送消息 (Enter)"))
        self._sendBtn.installEventFilter(
            ToolTipFilter(self._sendBtn, showDelay=300, position=ToolTipPosition.TOP)
        )
        self._sendBtn.setEnabled(False)
        self._sendBtn.clicked.connect(self._emitSend)

        # 文本变化 -> 自适应高度 + 更新按钮可用状态
        self.textChanged.connect(self._onTextChanged)

        # 让按钮一开始就到位
        self._repositionButtons()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def text(self) -> str:
        """获取输入框当前文本"""
        return self.toPlainText()

    def setText(self, text: str):
        """设置输入框文本"""
        self.setPlainText(text)

    def setInputEnabled(self, enabled: bool) -> None:
        """设置输入是否可用.

        禁用时: 文本区只读, 发送按钮禁用, Enter 不触发发送.
        启用时: 恢复正常交互.

        与 ``setEnabled(False)`` 的区别: 不会让整个 widget 变灰,
        只是阻止发送行为, 视觉上更柔和.

        Args:
            enabled: True 启用, False 禁用
        """
        self._inputEnabled = bool(enabled)
        self.setReadOnly(not enabled)
        self._sendBtn.setEnabled(enabled and bool(self.toPlainText().strip()))

    def isInputEnabled(self) -> bool:
        """输入是否可用."""
        return getattr(self, '_inputEnabled', True)

    def attachButton(self) -> TransparentToolButton:
        """返回附件按钮 (供应用方改图标 / 隐藏)."""
        return self._attachBtn

    def sendButton(self) -> TransparentToolButton:
        """返回圆形发送按钮 (供应用方改图标)."""
        return self._sendBtn

    def tokenIndicator(self) -> QWidget:
        """返回 token 预估指示器 (供应用方进一步定制 / 隐藏).

        默认隐藏, 调用 ``setTokenInfo(...)`` 后自动显示.
        """
        return self._tokenIndicator

    def setTokenInfo(self, context_used: int, context_max: int,
                     tokens_used: int, tokens_max: int) -> None:
        """更新 token 预估指示器 (发送按钮左侧).

        紧凑显示: ``≡ {context_used}/{context_max} | ↑ {tokens_used}/{tokens_max}``.
        悬停显示完整 ToolTip:
            上下文数 / 最大上下文数: {context_used} / {context_max}
            预估 Token 数: {tokens_used}

        所有参数 <= 0 时自动隐藏指示器.

        Args:
            context_used: 当前已占用的上下文条数 (历史消息数)
            context_max: 上下文上限
            tokens_used: 当前估算的 token 总数 (历史 + 输入框文本)
            tokens_max: token 数上限 (模型 context window)
        """
        if context_max <= 0 and tokens_max <= 0:
            self._tokenIndicator.hide()
            return

        self._lastTokenInfo = (context_used, context_max, tokens_used, tokens_max)
        self._contextLabel.setText(f"{context_used}/{context_max}")
        self._tokenCountLabel.setText(f"{tokens_used}/{tokens_max}")
        self._tokenIndicator.setToolTip(
            self.tr("点击查看详细 Token 用量")
        )
        self._tokenIndicator.adjustSize()
        self._tokenIndicator.show()
        self._repositionButtons()

    def clearTokenInfo(self) -> None:
        """隐藏 token 预估指示器 (与未调用 ``setTokenInfo`` 时等价)."""
        self._tokenIndicator.hide()

    def setSlashPopover(self, popover) -> None:
        """注入 SlashCommandPopover, 输入 / 时自动弹出.

        自动连接 ``tabCompleted`` 信号实现 Tab 补全: 按 Tab 时把选中命令
        文本填入输入框 (替换当前输入), 光标移到末尾, 弹窗保持打开.

        Args:
            popover: SlashCommandPopover 实例 (或 None 禁用)
        """
        self._slashPopover = popover
        if popover is not None:
            popover.tabCompleted.connect(self._onSlashTabComplete)

    def _onSlashTabComplete(self, command: str) -> None:
        """Slash Tab 补全: 替换输入框文本为完整命令."""
        self.setPlainText(command)
        # 光标移到末尾
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)

    def setMentionPopover(self, popover) -> None:
        """注入 MentionPopover, 输入 @ 时自动弹出.

        Args:
            popover: MentionPopover 实例 (或 None 禁用)
        """
        self._mentionPopover = popover

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _buildTokenIndicator(self) -> QWidget:
        """构造 token 预估指示器: ``[≡ icon] [n/m] | [↑ icon] [n/m]``.

        默认 hide, 直到 ``setTokenInfo`` 被调用. 点击触发 Flyout 详情弹窗
        (含 ProgressBar + 提示文案). 悬停显示简短 ToolTip 作为兜底.
        """
        indicator = ClickableWidget(self)
        indicator.setObjectName("chatTokenIndicator")
        indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QHBoxLayout(indicator)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ≡ 上下文图标 (3 横线)
        contextIcon = IconWidget(FluentIcon.MENU, indicator)
        contextIcon.setFixedSize(12, 12)

        self._contextLabel = CaptionLabel("0/0", indicator)
        self._contextLabel.setObjectName("chatContextLabel")

        # 分隔符
        sep = CaptionLabel("|", indicator)
        sep.setObjectName("chatTokenSeparator")

        # ↑ 当前 token 数图标
        tokenIcon = IconWidget(FluentIcon.UP, indicator)
        tokenIcon.setFixedSize(12, 12)

        self._tokenCountLabel = CaptionLabel("0/0", indicator)
        self._tokenCountLabel.setObjectName("chatTokenCountLabel")

        layout.addWidget(contextIcon, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._contextLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(sep, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(tokenIcon, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._tokenCountLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        indicator.hide()
        # 兜底 ToolTip (300ms 悬停后弹出, 被 click->flyout 取代后仍保留作为
        # 鼠标悬停的提示, 因为不是所有用户都会去点).
        indicator.installEventFilter(
            ToolTipFilter(indicator, showDelay=300, position=ToolTipPosition.TOP)
        )
        # 点击 -> 弹 Flyout 详情卡片
        indicator.clicked.connect(self._showTokenFlyout)
        return indicator

    def _showTokenFlyout(self):
        """点击 token 指示器时弹出 Flyout 详情视图.

        Flyout 自动定位到 indicator 上方 (PULL_UP 动画), parent 设为
        window() 让弹层落在最顶层 — 不会被 chat panel 的滚动遮挡.
        """
        c_used, c_max, t_used, t_max = self._lastTokenInfo
        view = _TokenInfoFlyoutView(c_used, c_max, t_used, t_max, parent=None)
        Flyout.make(
            view,
            target=self._tokenIndicator,
            parent=self.window(),
            aniType=FlyoutAnimationType.PULL_UP,
            isDeleteOnClose=True,
        )

    def _onTextChanged(self):
        """根据 document size 自适应高度 + 更新发送按钮 enabled 状态 + 触发弹窗"""
        doc = self.document()
        # document 内容高度 + 底部按钮区预留 + 上下边距
        natural_h = int(doc.size().height()) + self._BOTTOM_RESERVE + 8
        clamped = max(self._MIN_HEIGHT, min(natural_h, self._MAX_HEIGHT))
        if self.height() != clamped:
            self.setFixedHeight(clamped)
        has_text = bool(self.toPlainText().strip())
        self._sendBtn.setEnabled(has_text and self.isInputEnabled())

        # Slash / Mention 弹窗触发
        self._checkPopoverTrigger()

    def _checkPopoverTrigger(self):
        """检测当前输入是否应该触发 slash 或 mention 弹窗."""
        text = self.toPlainText()
        cursor = self.textCursor()
        pos = cursor.position()

        # 取光标前的文本
        before = text[:pos] if pos <= len(text) else text

        # Slash: 行首输入 "/" 开头 (整行只有 /xxx)
        current_line = before.split("\n")[-1] if before else ""
        if current_line.startswith("/") and " " not in current_line:
            if hasattr(self, '_slashPopover') and self._slashPopover is not None:
                # 同步宽度跟输入框对齐
                self._slashPopover.setFixedWidth(self.width())
                self._slashPopover.popup(current_line)
                return

        # Mention: "@" 后面跟非空格字符
        at_idx = current_line.rfind("@")
        if at_idx >= 0:
            after_at = current_line[at_idx + 1:]
            if " " not in after_at:
                if hasattr(self, '_mentionPopover') and self._mentionPopover is not None:
                    self._mentionPopover.setFixedWidth(self.width())
                    self._mentionPopover.popup(after_at)
                    return

        # 都不匹配: 收起弹窗 (带动画)
        if hasattr(self, '_slashPopover') and self._slashPopover and self._slashPopover.isVisible():
            self._slashPopover._animateClose()
        if hasattr(self, '_mentionPopover') and self._mentionPopover and self._mentionPopover.isVisible():
            self._mentionPopover._animateClose()

    def _emitSend(self):
        """Enter / 点发送触发: 文本非空时 emit + 清空输入"""
        if not self.isInputEnabled():
            return
        text = self.toPlainText().strip()
        if not text:
            return
        self.sendRequested.emit(text)
        self.clear()

    def keyPressEvent(self, event: QKeyEvent):
        """Enter 发送, Shift+Enter 换行, 方向键转发给弹窗"""
        # 优先让弹窗处理
        if hasattr(self, '_slashPopover') and self._slashPopover and self._slashPopover.isVisible():
            if self._slashPopover.handleKeyPress(event):
                return
        if hasattr(self, '_mentionPopover') and self._mentionPopover and self._mentionPopover.isVisible():
            if self._mentionPopover.handleKeyPress(event):
                return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
                return
            self._emitSend()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._repositionButtons()

    def _repositionButtons(self):
        """把按钮放到 widget 底部 (左 = 附件, 右 = 发送, token 指示器贴 send 左侧)"""
        bs = self._BUTTON_SIZE
        bp = self._BUTTON_PADDING
        h = self.height()
        w = self.width()
        # 底部按钮 y 中线对齐底部预留区
        y = h - bp - bs
        self._attachBtn.move(bp, y)
        self._sendBtn.move(w - bp - bs, y)

        # Token 指示器: 紧贴 sendBtn 左侧, 与 send 按钮垂直居中对齐
        if self._tokenIndicator.isVisibleTo(self):
            self._tokenIndicator.adjustSize()
            ind_w = self._tokenIndicator.width()
            ind_h = self._tokenIndicator.height()
            ind_x = w - bp - bs - 8 - ind_w
            ind_y = y + (bs - ind_h) // 2
            self._tokenIndicator.move(max(bp + bs + 8, ind_x), ind_y)


class AgentChatPanel(QWidget):
    """Agent 聊天完整面板 = AgentChatView + ChatInputEdit.

    应用方监听 ``sendRequested`` / ``attachmentRequested`` 触发后端逻辑.
    用 ``chatView()`` 拿消息流容器调 ``addMessage`` / ``appendDelta`` 等.

    宽度策略:
        输入框宽度严格等于消息区 inner 宽度 = ``min(viewport,
        maxContentWidth)``. 通过 ``resizeEvent`` 锁死, 不靠 layout stretch
        (stretch 会让 inputBar 缩到 sizeHint, 跟消息区不齐).

    信号:
        sendRequested(str):     用户按 Enter / 发送按钮 触发
        attachmentRequested():  用户点附件 触发

    构造函数重载:
        * AgentChatPanel(parent: QWidget = None)
    """

    sendRequested = Signal(str)
    attachmentRequested = Signal()

    # 跟 ``AgentChatView._DEFAULT_MAX_CONTENT_WIDTH`` 保持一致
    _DEFAULT_MAX_CONTENT_WIDTH = 760
    # 输入框距 panel 底部 / 距消息区上方 的留白
    _INPUT_BOTTOM_MARGIN = 16
    _INPUT_TOP_MARGIN = 8
    # **关键**: inputEdit 应该对齐到 chatView 内的**消息气泡** (bubble),
    # 而不是消息流容器 (``_inner``). 因为 ``AgentChatView._vLayout`` 在
    # ``_inner`` 内还有左右各 20px 的 contentMargins, bubble 在 _vLayout
    # 里, 所以 ``bubble.left = _inner.left + 20``, ``bubble.width = 760 - 40``.
    # 输入框宽度 / 居中位置必须扣除这 40, 否则比 bubble (含表格/文字内容)
    # 宽 40px, 左偏 20px - 用户看到的 "宽一截". 这个常量必须与
    # ``AgentChatView._vLayout`` 的左右 contentsMargins 之和保持一致, 改
    # 一处必须改另一处.
    _BUBBLE_HORIZONTAL_INSET = 40

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("agentChatPanel")

        self._chatView = AgentChatView(self)
        self._chatView.setMaxContentWidth(self._DEFAULT_MAX_CONTENT_WIDTH)

        # 输入框: 不用外层卡片, 自身就是 textedit + 内嵌按钮
        self._inputEdit = ChatInputEdit(self)
        # SizePolicy Fixed: 由 resizeEvent 用 setFixedWidth 直接锁宽,
        # 不靠 layout stretch (stretch 会缩到 sizeHint).
        self._inputEdit.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed,
        )

        # 自己 new 一个 GenerationStatusBar 注入给 chatView 用 — view 默认
        # 不创建内部 bar, 这样彻底避免之前 "view 创建默认 bar -> panel reparent
        # 到自己 -> view 还要做 parent != viewport 守卫" 的脆弱链路.
        # 视觉上 bar 是 "从输入框向上延伸出来的一张小卡片", 不悬浮在消息区
        # 顶部 (那种会盖住第一条消息).
        self._genBar = GenerationStatusBar(self)
        self._genBar.setObjectName("chatGenBarCard")
        self._genBar.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed,
        )
        # 默认 hide: 旧版 view 内部 lazy 创建后会立即 hide(), 现在 panel
        # 自建 bar 后必须自己 hide() 一下, 否则启动就把 "正在生成..." 横条
        # 显示在输入框上方 (实际并未在生成).
        self._genBar.hide()
        self._chatView.setStatusBar(self._genBar)

        # 状态条居中容器: stretch + genBar + stretch (与 inputRow 对齐)
        self._genBarRow = QWidget(self)
        self._genBarRow.setObjectName("chatGenBarRow")
        genBarRowLayout = QHBoxLayout(self._genBarRow)
        genBarRowLayout.setContentsMargins(0, 0, 0, 0)
        genBarRowLayout.setSpacing(0)
        genBarRowLayout.addStretch(1)
        genBarRowLayout.addWidget(self._genBar, 0)
        genBarRowLayout.addStretch(1)
        # genBar 自身 hide() 后整行视觉空间为 0 (genBar 是 row 中唯一非
        # stretch 项, sizeHint=0); 仍保留 row 在 layout 中, 后续 show() 时
        # 直接出现, 不需要 toggle 整行 visible.

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._chatView, 1)
        layout.addWidget(self._genBarRow, 0)
        layout.addWidget(self._inputRow_widget(), 0)

        self._maxContentWidth = self._DEFAULT_MAX_CONTENT_WIDTH

        # 信号转发
        # sendRequested 不直接转发, 多一层 hook: 应用层 slot 完成 addMessage 后
        # 主动 force-smooth-scroll 到底, 让用户看到自己刚发的消息.
        self._inputEdit.sendRequested.connect(self._onUserSendRequested)
        self._inputEdit.attachmentRequested.connect(self.attachmentRequested.emit)

    def _inputRow_widget(self) -> QWidget:
        """构造输入框居中容器 (stretch + inputEdit + stretch)."""
        self._inputRow = QWidget(self)
        self._inputRow.setObjectName("chatInputRow")
        rowLayout = QHBoxLayout(self._inputRow)
        # 左/右 0, 由 _applyInputWidth 动态调右 = scrollbar 宽
        rowLayout.setContentsMargins(
            0, self._INPUT_TOP_MARGIN,
            0, self._INPUT_BOTTOM_MARGIN,
        )
        rowLayout.setSpacing(0)
        rowLayout.addStretch(1)
        rowLayout.addWidget(self._inputEdit, 0)
        rowLayout.addStretch(1)
        return self._inputRow

    # ------------------------------------------------------------------
    # 宽度策略
    # ------------------------------------------------------------------

    def setMaxContentWidth(self, width: int) -> None:
        """同时设置消息区和输入框最大宽度.

        Args:
            width: 像素宽度. 0 / 负数 = 不限制 (铺满 viewport).
        """
        self._maxContentWidth = max(0, int(width))
        self._chatView.setMaxContentWidth(self._maxContentWidth)
        self._applyInputWidth()

    def maxContentWidth(self) -> int:
        return self._maxContentWidth

    def _applyInputWidth(self):
        """把 inputEdit 宽度 / 居中位置锁定到与 chatView 内**消息气泡**对齐.

        参考 ``AgentChatView`` 的 layout 链路:

            chatView (SmoothScrollArea)
              └─ container (HBoxLayout: stretch + inner + stretch)
                  └─ inner (FixedWidth = min(viewport, maxContentWidth))
                      └─ vLayout (contentsMargins = 20, 16, 20, 16)
                          └─ ChatBubble  ← 实际看到的气泡 (含表格/文字)

        所以 bubble 的几何 = ``_inner.geometry`` 减去 _vLayout 左右各 20px:
            bubble.width = inner.width - _BUBBLE_HORIZONTAL_INSET (= 40)
            bubble.left  = inner.left  + 20

        输入框对齐到 bubble (而不是 inner) 才能跟实际可视消息内容左右对齐.
        居中靠 ``inputRow`` 内 stretch + inputEdit + stretch 自动完成,
        只要 inputEdit.width 设对即可. ``SmoothScrollArea`` 默认 overlay
        滚动条不占 viewport 宽, 所以 ``vp_w == self.width()``, 不需要补
        scrollbar padding.
        """
        vp = self._chatView.viewport()
        vp_w = vp.width()
        if vp_w <= 0:
            return

        # bubble 实际宽 = min(viewport, max) - 40
        outer = min(vp_w, self._maxContentWidth) if self._maxContentWidth > 0 else vp_w
        target = outer - self._BUBBLE_HORIZONTAL_INSET
        if target <= 0:
            return
        if self._inputEdit.width() != target:
            self._inputEdit.setFixedWidth(target)

        # 状态条与输入框等宽: 视觉上是输入框上方延伸出来的一张小卡片,
        # 左右边沿与输入框对齐 (用户反馈 之前窄一截看起来不齐).
        if self._genBar.width() != target:
            self._genBar.setFixedWidth(target)

        # inputRow / genBarRow 右侧均补 scrollbar 占的宽度 (overlay 模式
        # 通常 = 0). 两行用同样的居中策略, 视觉上左右对齐.
        sb_w = max(0, self.width() - vp_w)
        for row in (self._inputRow, self._genBarRow):
            row_layout = row.layout()
            m = row_layout.contentsMargins()
            if m.right() != sb_w:
                row_layout.setContentsMargins(m.left(), m.top(), sb_w, m.bottom())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._applyInputWidth()

    def showEvent(self, event):
        super().showEvent(event)
        # 首次 show 后再锁一次宽 — 防止 __init__ 时 self.width() 还是 0
        self._applyInputWidth()

    # ------------------------------------------------------------------
    # 子组件访问
    # ------------------------------------------------------------------

    def chatView(self) -> AgentChatView:
        """返回内部 ``AgentChatView``."""
        return self._chatView

    def inputEdit(self) -> ChatInputEdit:
        """返回内部 ``ChatInputEdit`` (输入框 + 内嵌按钮)."""
        return self._inputEdit

    # ------------------------------------------------------------------
    # 输入区便捷代理
    # ------------------------------------------------------------------

    def setInputPlaceholder(self, text: str):
        self._inputEdit.setPlaceholderText(text)

    def inputText(self) -> str:
        return self._inputEdit.text()

    def setInputText(self, text: str):
        self._inputEdit.setText(text)

    def clearInput(self):
        self._inputEdit.clear()

    def focusInput(self):
        self._inputEdit.setFocus()

    def setInputEnabled(self, enabled: bool) -> None:
        """设置输入框是否可用 (代理 ``ChatInputEdit.setInputEnabled``).

        禁用时文本区只读, 发送按钮禁用, Enter 不触发发送.
        典型场景: Agent 生成中禁止用户发送新消息.

        Args:
            enabled: True 启用, False 禁用
        """
        self._inputEdit.setInputEnabled(enabled)

    def isInputEnabled(self) -> bool:
        """输入框是否可用."""
        return self._inputEdit.isInputEnabled()

    def setTokenInfo(self, context_used: int, context_max: int,
                     tokens_used: int, tokens_max: int) -> None:
        """更新输入区 token 预估指示器 (代理 ``ChatInputEdit.setTokenInfo``).

        Args:
            context_used: 当前已占用上下文条数
            context_max: 上下文上限
            tokens_used: 当前估算 token 数
            tokens_max: token 上限
        """
        self._inputEdit.setTokenInfo(context_used, context_max,
                                     tokens_used, tokens_max)

    def clearTokenInfo(self) -> None:
        """隐藏 token 预估指示器 (代理 ``ChatInputEdit.clearTokenInfo``)."""
        self._inputEdit.clearTokenInfo()

    # ------------------------------------------------------------------
    # 消息流便捷代理
    # ------------------------------------------------------------------

    def addMessage(self, message: ChatMessage):
        return self._chatView.addMessage(message)

    def removeMessage(self, message_id: str):
        return self._chatView.removeMessage(message_id)

    def clear(self):
        return self._chatView.clear()

    def messageCount(self) -> int:
        """返回当前消息总数 (代理 ``AgentChatView.messageCount``)."""
        return self._chatView.messageCount()

    def lastMessage(self) -> 'Optional[ChatMessage]':
        """返回最后一条消息 (代理 ``AgentChatView.lastMessage``)."""
        return self._chatView.lastMessage()

    def addSystemMessage(self, text: str) -> str:
        """快速插入系统消息 (代理 ``AgentChatView.addSystemMessage``)."""
        return self._chatView.addSystemMessage(text)

    def beginAgentResponse(self, status_text=None, **msg_kwargs) -> str:
        """一步创建空 AGENT 消息并开始生成 (代理 ``AgentChatView.beginAgentResponse``)."""
        return self._chatView.beginAgentResponse(status_text, **msg_kwargs)

    def scrollToMessage(self, message_id: str, highlight: bool = False) -> None:
        """平滑滚动到指定消息 (代理 ``AgentChatView.scrollToMessage``)."""
        self._chatView.scrollToMessage(message_id, highlight)

    def exportAsMarkdown(self) -> str:
        """导出对话为 Markdown (代理 ``AgentChatView.exportAsMarkdown``)."""
        return self._chatView.exportAsMarkdown()

    def exportAsDict(self) -> 'List[dict]':
        """导出对话为字典列表 (代理 ``AgentChatView.exportAsDict``)."""
        return self._chatView.exportAsDict()

    # ------------------------------------------------------------------
    # 发送消息 hook + 动画总开关
    # ------------------------------------------------------------------

    def _onUserSendRequested(self, text: str) -> None:
        """用户发送消息 hook.

        顺序关键:

        1. 先 ``sendRequested.emit(text)`` -- Qt 同步发射, 应用层 slot
           (一般是调 ``addMessage(USER消息)`` + ``addMessage(AGENT消息)``
           + ``beginGeneration``) 在本行返回前已同步跑完, ``_inner.sizeHint``
           已包含新 bubble, ``bar.maximum()`` 已是包含新内容的真值.
        2. 后 ``chatView._forceSmoothScrollToBottom(280)`` -- 把 ``_autoScroll``
           强制设为 True 后平滑滚到 maximum. 用户在上方查看历史时
           也能被带回底部.

        顺序不能反: 先滚动后 emit 时新消息尚未加入, ``bar.maximum()``
        是旧值, 动画会停在旧底部, 而后 ``_onRangeChanged`` 在
        ``_autoScroll == False`` 时又不会自动贴底, 就会出现"滚动动画跑完
        但底下还有新消息没看到"的视觉割裂.
        """
        self.sendRequested.emit(text)
        self._chatView._forceSmoothScrollToBottom()

    def setAnimationsEnabled(self, enabled: bool) -> None:
        """总开关: 一次关掉 panel 内所有过渡动画.

        转发到 ``chatView.setAnimationsEnabled(b)`` (递归覆盖 view + 子组件)
        并同步调 ``genBar.setEnterExitAnimationEnabled(b)`` 幂等设置
        (genBar 也会通过 ``animations_enabled_root`` 查 view 总开关, 但
        这里再设一次幂等, 避免任何缓存状态不同步).
        """
        self._chatView.setAnimationsEnabled(enabled)
        self._genBar.setEnterExitAnimationEnabled(enabled)

    def animationsEnabled(self) -> bool:
        return self._chatView.animationsEnabled()
