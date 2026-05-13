# coding: utf-8
"""聊天消息视图容器

可滚动的消息容器, 自上而下垂直排列 ChatBubble. 支持自动滚到底、用户上滚
时暂停自动滚动, 提供 addMessage / appendDelta / removeMessage / clear 等
高层 API, 转发各 bubble 的复制 / 编辑 / 删除信号.
"""

from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Union

from PySide6.QtCore import (
    QEasingCurve, QEvent, QPoint, QPropertyAnimation, Qt, QTimer, Signal,
)
from PySide6.QtGui import QClipboard, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ....common.overload import singledispatchmethod
from ..button import PillPushButton
from ..scroll_area import SmoothScrollArea
from ._branch_manager import _BranchManager
from ._branch_overlay import BranchSnapshotPlayer
from ._generation_controller import _GenerationController
from .chat_bubble import BubbleAction, ChatBubble
from .chat_message import (
    ApprovalPolicy, ChatMessage, ChatRole,
    TaskItem, TaskListSegment, TaskStatus,
    ToolCallSegment, ToolCallStatus,
)
from .code_block import CodeBlock
from .generation_status_bar import GenerationStatusBar
from .thinking_card import ThinkingCard
from .tool_call_card import ToolCallCard


__all__ = ['AgentChatView']


# 对话分叉数据模型 (_MessageVersion / _BranchPoint) 已抽到 _branch_manager.py.
# 生成状态条管理 (_currentGeneratingMsgId / _genBar) 已抽到
# _generation_controller.py. 主类只保留 facade 转发, 让本文件聚焦消息 CRUD
# + segments 派发 + 滚动 + 审批策略 这些核心职责.


class AgentChatView(SmoothScrollArea):
    """Agent 聊天消息视图容器

    面向 Agent 对话场景设计的消息流容器: 用户/Agent 双向消息气泡、
    Markdown 内容渲染、代码块卡片、思考过程与工具调用卡片、流式追加输出.

    管理一个垂直消息流, 提供消息增删改查与流式追加 API. 自动滚到底, 当用户
    主动向上滚动 (距底 > 100px) 时暂停, 距底 < 30px 时恢复自动滚到底.

    信号:
        messageCopied(str):          复制消息时发出 (参数为 message id)
        messageEditRequested(str):   请求编辑消息时发出 (参数为 message id)
        messageDeleteRequested(str): 请求删除消息时发出 (参数为 message id)
        messageAdded(str):           消息添加完成后发出 (参数为 message id)
        messageRemoved(str):         消息删除完成后发出 (参数为 message id)
        messagesCleared():           clear() 调用完成后发出
        lastMessageChanged():        当前最后一条消息内容变化时发出

    构造函数重载:
        * AgentChatView(parent: QWidget = None)
    """

    messageCopied = Signal(str)
    messageEditRequested = Signal(str)
    messageDeleteRequested = Signal(str)
    lastMessageChanged = Signal()
    # 实际增删后的通知信号 (与上面 *Requested 信号区分: *Requested 是用户点
    # 击操作栏触发的请求, 下面三个是内部状态实际变化后的通知, 用于宿主同步
    # 持久化层 / 状态机)
    messageAdded = Signal(str)      # 参数: message_id
    messageRemoved = Signal(str)    # 参数: message_id
    messagesCleared = Signal()
    # 生成控制 / 重生成 / 断点续写
    stopRequested = Signal(str)         # 参数: 正在生成的 message_id
    regenerateRequested = Signal(str)   # 参数: AGENT message_id
    # P2c: 流式被 Stop 后用户点 [继续生成] 按钮时发出
    resumeRequested = Signal(str)       # 参数: AGENT message_id
    # 工具调用审批
    toolCallApprovalRequested = Signal(str, str)  # 参数: (message_id, call_id)
    toolCallApproved = Signal(str, str)           # 参数: (message_id, call_id)
    toolCallRejected = Signal(str, str)           # 参数: (message_id, call_id)
    # 对话分叉
    # ``userMessageEdited`` 在用户气泡内联编辑保存 (即 editAndFork 完成) 后
    # 发出, 宿主可据此触发 LLM 重新生成 AI 回复.
    userMessageEdited = Signal(str, str)          # 参数: (new_user_msg_id, new_content)

    _SCROLL_BOTTOM_THRESHOLD = 30
    _SCROLL_PAUSE_THRESHOLD = 100
    # 默认最大内容宽度 (类似 ChatGPT/DeepSeek 的对话栏宽度).
    # 设为 0 即不限制 (内容铺满整个 viewport).
    _DEFAULT_MAX_CONTENT_WIDTH = 760

    @singledispatchmethod
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化 AgentChatView

        Args:
            parent: 父级 QWidget, 默认 None
        """
        super().__init__(parent)
        self._postInit()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _postInit(self):
        self.setObjectName("agentChatView")
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
        # AGENT 消息默认副标题生成器: 接收 ChatMessage, 返回 subtitle 字符串.
        # 用于 ChatMessage.subtitle 为空时自动填充, 让头像旁的副标题始终
        # 有内容 (例如 "10:32:48"). 默认 = 当前 HH:MM:SS.
        self._agentSubtitleProvider: Optional[Callable[[ChatMessage], str]] = (
            lambda _msg: datetime.now().strftime("%H:%M:%S")
        )
        # 全局 CodeBlock 最大可见行数; addMessage 时注入到 bubble.
        self._codeMaxVisibleLines = CodeBlock._DEFAULT_MAX_VISIBLE_LINES
        # 重新生成按钮的全局启用状态 (默认 False)
        self._regenerateEnabled = False
        # 操作栏 (复制/重生成/编辑/删除) 是否始终可见 (默认 True, 跟
        # ChatGPT/Claude 一致). False 切回 hover-fade 模式.
        self._actionsAlwaysVisible = True
        # 审批策略: tool_name -> ApprovalPolicy 三态 (ALLOW / ASK / DENY).
        # 未含即 ALLOW (默认不弹审批). 仅在 addToolCall 未显式传
        # requires_approval 时生效.
        self._approvalPolicies: Dict[str, ApprovalPolicy] = {}

        # ===== 过渡动画相关 =====
        # 总开关: False 时 平滑滚动 / 分支截图过渡 全部退化为瞬间行为.
        # 子组件 (CodeBlock / ThinkingCard / ToolCallCardBase /
        # GenerationStatusBar) 通过 ``animations_enabled_root`` 沿 parent
        # 链查询本字段, 一次关掉子树里所有动画.
        self._animationsEnabled: bool = True
        # 平滑滚动单独开关.
        self._smoothScrollEnabled: bool = True
        # 分支切换截图过渡单独开关.
        self._branchSwitchAnimationEnabled: bool = True
        # 思考 / 工具卡展开后是否自动滚到 widget 底部 (默认 False, 不打扰阅读).
        self._autoScrollOnCardExpand: bool = False
        # 程序化滚动标志: 动画进行中阻止 ``_onScrollChanged`` 误判 ``_autoScroll``.
        self._programmaticScroll: bool = False
        # 滚动动画对象引用.
        self._scrollAnim: Optional[QPropertyAnimation] = None
        # 是否跟随 maximum 动态更新动画 endValue:
        # 仅在 ``_smoothScrollToBottom`` 发起的动画中为 True, ``rangeChanged``
        # 触发时把 anim.endValue 更新为 new max. 修复"发送消息后动画停在
        # 旧底部"问题 (Qt layout deferred 刷新, emit 后立即 grab maximum 是旧值).
        self._scrollAnimTrackingMax: bool = False
        # layout 动画计数器: 卡片展开 / 折叠 / GenerationStatusBar
        # show / hide 进出场 这些会连续改 sizeHint 的动画起运行后计
        # 数器 +1, finished -1. > 0 时 ``_onRangeChanged`` 会强制把 viewport
        # 锁回动画启动时保存的 ``_savedScrollValue``, 彻底冻结 viewport.
        # 这是抖动修复的最后一道防线:
        # - 动画每帧 sizeHint 变化 → maximum 变 → Qt 可能自动调 viewport.value
        # - 动画 finished 时 setMaximumHeight(QWIDGETSIZE_MAX) 解锁引起高度
        #   跳变 (target_h 跳到真实 sizeHint)
        # 都会改 viewport.value, 这里都拦住.
        # 归 0 后 schedule ``_catchUpToBottomIfNeeded`` 1 帧后 如果
        # ``_autoScroll == True`` 且离底, 启动 180ms 短动画平滑追到底.
        self._layoutAnimationDepth: int = 0
        # layout 动画启动时保存的 viewport 位置 (动画期间锁回这里).
        self._savedScrollValue: int = 0
        # layout 动画启动时记录的 _autoScroll 状态 (是否在底部). 动画期间
        # 用它决定 viewport 行为: True 时跟着 maximum 单调贴底, False 时
        # 锁回 _savedScrollValue. 单独缓存避免动画期间 setValue 自己改 _autoScroll.
        self._savedAtBottom: bool = False
        # rangeChanged debounce timer (16ms): 修复"整个 view 上下跳"的根因。
        # Qt layout chain (setVisible / addWidget / layout pass / polish) 会在
        # 短时间内 emit rangeChanged 多次, 每次 maximum 都不一样 (中间
        # 值). 如果每次都走 ``_scrollToBottom`` (setValue(maximum)),
        # viewport.value 会在几个中间 maximum 之间跳 —— 这就是看到的
        # “上下拖动”. Debounce 让连续快速 emit 合并为一次 setValue
        # (用最后稳定的 maximum), viewport 一次贴到真底.
        self._rangeCatchUpTimer: Optional[QTimer] = None
        # 分支切换截图播放器.
        self._branchSnapshotPlayer = BranchSnapshotPlayer(self)

        # 子领域控制器 (composition):
        # - ``_branches``    : 对话分叉 (editAndFork / switchVersion / versionInfo)
        # - ``_generation``  : 生成状态条 (begin / set / end / statusBar / setStatusBar)
        # 主类只保留 facade 方法转发, 不再持有这些子领域的内部状态.
        self._branches = _BranchManager(self)
        self._generation = _GenerationController(self)

        # 「回到最新」浮动按钮 (挂在 viewport 上层, 否则会被滚动内容盖住)
        self._jumpBtn = PillPushButton(FluentIcon.DOWN, self.tr("回到最新"), self.viewport())
        self._jumpBtn.setCheckable(False)
        self._jumpBtn.hide()
        # 点击 “回到最新” 走平滑滚动动画 (~280ms), 而不是瞬间跳
        self._jumpBtn.clicked.connect(self._smoothScrollToBottom)
        self._jumpBtn.setFixedHeight(32)

        # 滚动监听
        self.verticalScrollBar().valueChanged.connect(self._onScrollChanged)
        self.verticalScrollBar().rangeChanged.connect(self._onRangeChanged)

        # 用户主动输入 (拖滚动条) 时提前取消滚动动画, 避免动画 vs 用户
        # 拖拽 竞争导致 viewport 拖不动 / 倒退.
        self.verticalScrollBar().installEventFilter(self)

        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self._container)
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self._inner)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addMessage(self, message: ChatMessage) -> ChatBubble:
        """追加一条消息.

        Args:
            message: ChatMessage 实例

        Returns:
            创建的 ChatBubble (已加入布局)

        Note:
            ``message.role == USER`` 时方法末尾会主动调
            ``_forceSmoothScrollToBottom``, 覆盖 ``_autoScroll`` 状态将用户
            带回底部 —— 任何 USER 消息进入都意味着用户主动行为, 期望看
            到自己刚发的内容, 跟 ChatGPT/Claude 行为一致. ``AGENT`` 不
            force 滚动 (避免初始空占位 bubble 启动多余动画).
        """
        # AGENT 消息: subtitle 为空 -> 用默认 provider 自动填充, 保证头像
        # 下方副标题始终可见 (用户反馈 切到新分支 / 流式按钮 后副标题消失).
        if (message.role == ChatRole.AGENT
                and not message.subtitle
                and self._agentSubtitleProvider is not None):
            try:
                message.subtitle = self._agentSubtitleProvider(message)
            except Exception:
                # provider 异常不影响消息添加, 仅放弃自动填充
                pass

        bubble = ChatBubble(message, self._inner)
        # 应用默认头像 + 默认显示名 fallback
        if message.role == ChatRole.USER:
            bubble.setUserAvatarFallback(self._userAvatar)
            bubble.setDefaultSenderName(self._userDisplayName)
        elif message.role == ChatRole.AGENT:
            bubble.setUserAvatarFallback(self._agentAvatar)
            bubble.setDefaultSenderName(self._agentDisplayName)
        # 注入全局 CodeBlock 最大可见行数
        bubble.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)

        # P1b: 单条 ``actionTriggered`` 信号取代了原 8 条独立 signal connect.
        # ``_onBubbleAction`` 内部用 dict 路由分派.
        bubble.actionTriggered.connect(self._onBubbleAction)
        # AGENT 消息: 应用全局重生成启用状态
        if message.role == ChatRole.AGENT and self._regenerateEnabled:
            bubble.setRegenerateEnabled(True)
        # 应用全局 actions always-visible 策略
        bubble.setActionsAlwaysVisible(self._actionsAlwaysVisible)

        # 插入到 stretch 之前
        insert_index = self._vLayout.count() - 1
        self._vLayout.insertWidget(insert_index, bubble)

        self._bubbles[message.id] = bubble
        self._order.append(message.id)
        self.messageAdded.emit(message.id)
        self.lastMessageChanged.emit()

        if message.role == ChatRole.USER:
            # USER 消息进入 → 强制带回底部 (覆盖 _autoScroll == False).
            # 动画 endValue 会随 layout deferred 刷新后的 rangeChanged 动态
            # 追踪到 new maximum, 保证最终停在真底部.
            self._forceSmoothScrollToBottom()
        elif self._autoScroll:
            # 不主动 scroll: bubble 加入 → layout 异步更新 → scrollbar
            # range 变化 → _onRangeChanged 同步滚到底, 与内容增长同步.
            pass
        else:
            self._jumpBtn.show()

        return bubble

    def message(self, message_id: str) -> Optional[ChatMessage]:
        """根据 id 查找消息. 不存在返回 None."""
        bubble = self._bubbles.get(message_id)
        return bubble.message() if bubble is not None else None

    def bubble(self, message_id: str) -> Optional[ChatBubble]:
        """根据 id 查找消息气泡 widget. 不存在返回 None.

        通常不需要直接持有 bubble; 但当宿主想做高级定制 (如插入
        自定义 widget 到 bubble 上) 时可用.
        """
        return self._bubbles.get(message_id)

    def hasMessage(self, message_id: str) -> bool:
        """判断指定 id 的消息是否存在."""
        return message_id in self._bubbles

    def setMessageContent(self, message_id: str, markdown: str) -> None:
        """覆盖式设置指定消息的 markdown 内容.

        与 ``appendDelta`` 区别:
        - ``appendDelta``: 流式追加 (拼接到尾部, 触发节流增量渲染)
        - ``setMessageContent``: 整体替换 (典型场景: 编辑后保存 / 重生成回答)

        消息不存在时静默忽略.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        bubble.setContent(markdown)
        self.lastMessageChanged.emit()

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

    # ------------------------------------------------------------------
    # Thinking / Tool call 流式 API
    # ------------------------------------------------------------------
    # 这些 API 仅对 AGENT 消息有效; 其它角色或不存在的 message_id 静默忽略.

    def beginThinking(self, message_id: str) -> Optional[ThinkingCard]:
        """开始一段思考过程, 返回对应 ThinkingCard.

        如果 message 已存在 thinking, 则复用既有卡片. ChatBubble 会在
        message 中创建 ``ThinkingSegment`` (若 None).

        Args:
            message_id: AGENT 消息 id

        Returns:
            ThinkingCard, 当 message 不存在或非 AGENT 时返回 None.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None or bubble.message().role != ChatRole.AGENT:
            return None
        return bubble.ensureThinking()

    def appendThinkingDelta(self, message_id: str, delta: str) -> None:
        """流式追加思考过程内容. 若尚未 ``beginThinking`` 则自动调用之."""
        if not delta:
            return
        card = self.beginThinking(message_id)
        if card is None:
            return
        card.appendDelta(delta)

    def endThinking(self, message_id: str,
                    duration_ms: Optional[int] = None) -> None:
        """标记思考结束, 切换 header 为 "已深度思考".

        Args:
            message_id:  消息 id
            duration_ms: 思考耗时 (毫秒), 显示在标题中
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.thinkingCard()
        if card is None:
            return
        card.finish(duration_ms)

    def addToolCall(self, message_id: str, tool_name: str,
                    arguments: str = "",
                    metadata: Optional[Dict[str, object]] = None,
                    requires_approval: Optional[bool] = None) -> Optional[str]:
        """添加一次工具调用, 返回 ToolCallSegment.id.

        Args:
            message_id:        AGENT 消息 id
            tool_name:         工具名 (如 ``read_file`` / ``bash``)
            arguments:         调用参数, 建议 JSON 字符串. 不解析
            metadata:          特化渲染器使用的元数据 dict (如
                               ``{path, language, exit_code, results, hits}``). 可选.
            requires_approval: 是否要求审批.
                               - True:  初始状态 ``PENDING_APPROVAL``,
                                        同时发出 ``toolCallApprovalRequested(msg_id, call_id)``.
                               - False: 初始状态 ``PENDING`` (直接调用).
                               - None:  查 ``_approvalPolicies[tool_name]`` 决定
                                        (ALLOW -> PENDING, ASK -> PENDING_APPROVAL,
                                        DENY -> REJECTED). 默认 ALLOW.

        Returns:
            ToolCallSegment.id, 用于后续 appendToolCallResult /
            setToolCallStatus 定位. 当 message 不存在或非 AGENT 时返回 None.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None or bubble.message().role != ChatRole.AGENT:
            return None

        # 根据显式参数 / 注册策略决定初始状态.
        # 三态策略 (P2c):
        #   ALLOW -> PENDING         (直接执行)
        #   ASK   -> PENDING_APPROVAL (弹审批)
        #   DENY  -> REJECTED        (自动拒绝, 不弹 UI)
        if requires_approval is None:
            policy = self._approvalPolicies.get(tool_name, ApprovalPolicy.ALLOW)
        elif requires_approval:
            policy = ApprovalPolicy.ASK
        else:
            policy = ApprovalPolicy.ALLOW

        if policy == ApprovalPolicy.ASK:
            initial_status = ToolCallStatus.PENDING_APPROVAL
        elif policy == ApprovalPolicy.DENY:
            initial_status = ToolCallStatus.REJECTED
        else:  # ALLOW
            initial_status = ToolCallStatus.PENDING

        seg = ToolCallSegment(
            tool_name=tool_name,
            arguments=arguments,
            metadata=dict(metadata) if metadata else {},
            status=initial_status,
        )
        bubble.addToolCall(seg)
        if policy == ApprovalPolicy.ASK:
            self.toolCallApprovalRequested.emit(message_id, seg.id)
        elif policy == ApprovalPolicy.DENY:
            # 自动拒绝: 立即 emit toolCallRejected, 让宿主知情
            self.toolCallRejected.emit(message_id, seg.id)
        return seg.id

    def appendToolCallArguments(self, message_id: str, call_id: str,
                                delta: str) -> None:
        """流式追加某次工具调用的参数 (LLM 流式输出 JSON 参数时用).

        与 ``addToolCall`` 提供的初始 ``arguments`` 互补: 如果 LLM 流式输出
        参数, 应在 ``addToolCall(..., arguments="")`` 后反复调用此方法
        累积参数. 消息或调用不存在时静默忽略.
        """
        if not delta:
            return
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.toolCallCard(call_id)
        if card is None:
            return
        card.appendArgumentsDelta(delta)

    def appendToolCallResult(self, message_id: str, call_id: str,
                             delta: str) -> None:
        """流式追加某次工具调用的结果."""
        if not delta:
            return
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.toolCallCard(call_id)
        if card is None:
            return
        card.appendResultDelta(delta)

    def setToolCallStatus(self, message_id: str, call_id: str,
                          status: ToolCallStatus,
                          duration_ms: Optional[int] = None) -> None:
        """更新某次工具调用的状态 (PENDING -> SUCCESS / ERROR).

        Args:
            message_id:  消息 id
            call_id:     ToolCallSegment.id (来自 ``addToolCall`` 返回值)
            status:      新状态 ``ToolCallStatus.SUCCESS / ERROR``
            duration_ms: 总耗时 (毫秒)
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.toolCallCard(call_id)
        if card is None:
            return
        card.setStatus(status, duration_ms)

    # ------------------------------------------------------------------
    # 任务列表 公共 API (P2d)
    # ------------------------------------------------------------------

    def addTaskList(self, message_id: str,
                    items: List[TaskItem],
                    title: str = "") -> Optional[str]:
        """在指定 AGENT 消息末尾追加一个任务列表段.

        语义参考 Claude Code: Agent 开始长任务时先列出 TODO list, 每完成一
        项就把对应 ``TaskItem.status`` 切到 DONE (或 IN_PROGRESS), 通过
        ``updateTaskItem`` 触发局部 UI 刷新.

        Args:
            message_id: AGENT 消息 id
            items:      任务项列表
            title:      可选自定义标题 (不传则用默认 "任务计划")

        Returns:
            新建 TaskListSegment 的 id, 或在消息不存在 / 非 AGENT 时返回 None.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None or bubble.message().role != ChatRole.AGENT:
            return None
        seg = TaskListSegment(title=title, items=list(items))
        bubble.message().segments.append(seg)
        # body._appendSegmentWidget 走 segment_renderers 注册表 -> TaskListCard
        bubble.body()._appendSegmentWidget(seg)  # type: ignore[attr-defined]
        return seg.id

    def updateTaskItem(self, message_id: str, segment_id: str,
                       item_id: str, status: TaskStatus,
                       text: Optional[str] = None) -> None:
        """更新某个任务项状态 / 文字. 未知 id 静默忽略.

        Args:
            message_id: AGENT 消息 id
            segment_id: ``addTaskList`` 返回的 TaskListSegment id
            item_id:    要更新的 TaskItem.id
            status:     新状态 (TODO / IN_PROGRESS / DONE)
            text:       可选新文本
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        # 去 body 里找到对应的 TaskListCard 并 updateItem
        from ._task_list_card import TaskListCard
        body = bubble.body()
        seg_widgets = getattr(body, "_segmentWidgets", {})
        card = seg_widgets.get(segment_id)
        if isinstance(card, TaskListCard):
            card.updateItem(item_id, status, text)

    # ------------------------------------------------------------------
    # 消息删除 / 清空
    # ------------------------------------------------------------------

    def removeMessage(self, message_id: str) -> None:
        """删除指定消息. 删除完成后发出 ``messageRemoved(id)``."""
        bubble = self._bubbles.pop(message_id, None)
        if bubble is None:
            return
        self._vLayout.removeWidget(bubble)
        bubble.setParent(None)
        bubble.deleteLater()
        if message_id in self._order:
            self._order.remove(message_id)
        self.messageRemoved.emit(message_id)

    def clear(self) -> None:
        """清空所有消息. 完成后发出 ``messagesCleared()``.

        清空过程中每条消息的 ``messageRemoved`` 仍会触发, 宿主可按需选择
        监听哪个信号.
        """
        for mid in list(self._order):
            self.removeMessage(mid)
        self.messagesCleared.emit()

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

    def setAgentSubtitleProvider(
        self, provider: Optional[Callable[[ChatMessage], str]],
    ) -> None:
        """设置 AGENT 消息的默认副标题生成器.

        ``addMessage`` 时若 ``ChatMessage.subtitle`` 为空, 会调用该 provider
        生成 subtitle (如 ``"10:32:48"`` / ``"10:32:48 · GPT-4o"``). 传 None
        关闭自动填充, AGENT 消息回到 "subtitle 为空时不显示" 的旧行为.

        默认 provider = ``datetime.now().strftime("%H:%M:%S")``.
        """
        self._agentSubtitleProvider = provider

    def setMessageSubtitle(self, message_id: str, subtitle: Optional[str]) -> None:
        """运行期更新某条消息的副标题. 流式中可用于显示 token 数变化."""
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        bubble.setSubtitle(subtitle)
        self.lastMessageChanged.emit()

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

    def setCodeBlockMaxVisibleLines(self, n: int) -> None:
        """全局设置 CodeBlock 代码区最大可见行数.

        - 行数 ≤ ``n``: 代码块按内容高度铺开, 无垂直滚动
        - 行数 >  ``n``: 高度卡在 ``n`` 行, 垂直滚动条按需显示

        作用范围: 已存在的所有消息气泡 (正文 markdown / thinking / 工具调用
        参数与结果) 立即同步; 后续 ``addMessage`` 也会自动应用. 默认 10.

        Args:
            n: 最大可见行数 (≥ 1)
        """
        n = max(1, int(n))
        self._codeMaxVisibleLines = n
        for bubble in self._bubbles.values():
            bubble.setCodeBlockMaxVisibleLines(n)

    def codeBlockMaxVisibleLines(self) -> int:
        """获取当前全局 CodeBlock 最大可见行数."""
        return self._codeMaxVisibleLines

    def _applyMaxContentWidth(self):
        """把 inner 固定为 min(viewport_width, _maxContentWidth).

        关键: 必须用 setFixedWidth 把 inner 锁死, 不让内部子项 (CodeBlock
        minWidth=560 / MarkdownView idealWidth-based sizeHint 等) 通过
        sizeHint 反向决定 inner 宽度. 否则:

            - inner 取 sizeHint = max(子项 sizeHint) → 随 markdown 内容增长
              而忽宽忽窄
            - thinking 展开 / tool call 展开 / 流式追加 token 都会改变
              sizeHint → bubble 宽度抖动且突破 maxContentWidth

        viewport resize 时由 ``resizeEvent`` 重新计算并同步.
        ``_maxContentWidth == 0`` 表示无上限, inner 跟随 viewport.
        """
        vp = self.viewport().width()
        if vp <= 0:
            return
        target = min(vp, self._maxContentWidth) if self._maxContentWidth > 0 else vp
        if target <= 0:
            return
        if self._inner.width() != target or self._inner.minimumWidth() != target:
            self._inner.setFixedWidth(target)

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

    # P1b: bubble 单一 actionTriggered 路由器. payload 类型由 action 决定 (见
    # ``BubbleAction`` 注释表). 不在表里的 action 静默忽略, 不抛, 留给宿主侧
    # 升级 BubbleAction 时不需要改 view.
    def _onBubbleAction(self, action: str, message_id: str,
                        payload: object) -> None:
        if action == BubbleAction.COPY:
            self._onCopyRequested(message_id)
        elif action == BubbleAction.EDIT:
            self.messageEditRequested.emit(message_id)
        elif action == BubbleAction.EDIT_CONFIRM:
            new_content = payload if isinstance(payload, str) else ""
            self.editAndFork(message_id, new_content)
        elif action == BubbleAction.EDIT_CANCEL:
            # 当前无外部消费者; 留 hook
            pass
        elif action == BubbleAction.DELETE:
            self.messageDeleteRequested.emit(message_id)
        elif action == BubbleAction.REGENERATE:
            self.regenerateRequested.emit(message_id)
        elif action == BubbleAction.RESUME:
            # P2c: 气泡末尾的 [继续生成] 被点, 通知宿主从断点续写
            self.resumeRequested.emit(message_id)
            # 同时隐藏 "已停止 [继续生成]" 行 (续写即将开始)
            bubble = self._bubbles.get(message_id)
            if bubble is not None:
                bubble.markStopped(False)
        elif action == BubbleAction.VERSION_SWITCH:
            target = int(payload) if payload is not None else 0
            self.switchVersion(message_id, target)
        elif action == BubbleAction.TOOL_APPROVE:
            call_id = payload if isinstance(payload, str) else ""
            self._transitionApproval(message_id, call_id, approve=True)
        elif action == BubbleAction.TOOL_REJECT:
            call_id = payload if isinstance(payload, str) else ""
            self._transitionApproval(message_id, call_id, approve=False)
        elif action == BubbleAction.TOOL_ALWAYS_ALLOW:
            # P2c remember: 把工具策略设为 ALLOW, 然后批准本次
            call_id = payload if isinstance(payload, str) else ""
            self._rememberPolicyAndTransition(
                message_id, call_id,
                policy=ApprovalPolicy.ALLOW, approve=True,
            )
        elif action == BubbleAction.TOOL_ALWAYS_REJECT:
            # P2c remember: 把工具策略设为 DENY, 然后拒绝本次
            call_id = payload if isinstance(payload, str) else ""
            self._rememberPolicyAndTransition(
                message_id, call_id,
                policy=ApprovalPolicy.DENY, approve=False,
            )

    # ------------------------------------------------------------------
    # 生成控制 公共 API (facade -> _GenerationController)
    # ------------------------------------------------------------------

    def beginGeneration(self, message_id: str,
                        status_text: Optional[str] = None) -> None:
        """开始一次生成, 显示顶部状态条 + spinner + 计时."""
        self._generation.begin(message_id, status_text)

    def setGenerationStatus(self, message_id: str, text: str) -> None:
        """更新生成状态文本."""
        self._generation.setStatus(message_id, text)

    def setGenerationTokens(self, message_id: str, total: int,
                            rate: Optional[float] = None) -> None:
        """更新累计 token 与可选 tok/s."""
        self._generation.setTokens(message_id, total, rate)

    def endGeneration(self, message_id: str,
                      stopped: bool = False) -> None:
        """结束生成, 隐藏状态条; ``stopped=True`` 时给 bubble 显 [继续生成]."""
        self._generation.end(message_id, stopped)

    def isGenerating(self) -> bool:
        return self._generation.isGenerating

    def currentGeneratingMessageId(self) -> Optional[str]:
        return self._generation.currentMessageId

    def statusBar(self) -> GenerationStatusBar:
        """返回 (必要时 lazy 创建) 生成状态条."""
        return self._generation.statusBar()

    def setStatusBar(self, bar: GenerationStatusBar) -> None:
        """注入外部创建的 ``GenerationStatusBar``."""
        self._generation.setStatusBar(bar)

    def setRegenerateEnabled(self, enabled: bool) -> None:
        """全局启用 / 禁用 AGENT 消息气泡 重新生成 按钮.

        启用后: 现有所有 AGENT 消息都显示重新生成按钮, 后续 addMessage
        也会自动启用.

        点击 重新生成 时发出 ``regenerateRequested(message_id)`` 信号,
        宿主需响应 (在 LLM 接口重新发起请求 + 调用
        ``setMessageContent`` / ``appendDelta`` 覆写消息).
        """
        self._regenerateEnabled = bool(enabled)
        for bubble in self._bubbles.values():
            if bubble.message().role == ChatRole.AGENT:
                bubble.setRegenerateEnabled(self._regenerateEnabled)

    def isRegenerateEnabled(self) -> bool:
        return self._regenerateEnabled

    def setActionsAlwaysVisible(self, always: bool) -> None:
        """全局设置所有消息气泡 操作栏 (复制/重生成/编辑/删除) 是否始终可见.

        默认 ``True`` — 跟 ChatGPT/Claude 一致, 按钮常驻. 设 ``False`` 切
        回旧 hover-fade 行为 (鼠标进入气泡时淡入).

        Args:
            always: True 始终 1.0 透明度; False 进入 hover-fade 模式
        """
        self._actionsAlwaysVisible = bool(always)
        for bubble in self._bubbles.values():
            bubble.setActionsAlwaysVisible(self._actionsAlwaysVisible)

    def actionsAlwaysVisible(self) -> bool:
        return self._actionsAlwaysVisible

    # ------------------------------------------------------------------
    # 过渡动画 公共 API
    # ------------------------------------------------------------------

    def setAnimationsEnabled(self, enabled: bool) -> None:
        """总开关: 一次关掉所有过渡动画 (平滑滚动 / 分支截图 / 卡片展开).

        关闭后:

        - ``_smoothScrollTo`` / ``_smoothScrollToBottom`` 退化为瞬时 setValue.
        - ``_playBranchSwitchOverlay`` 不再启动.
        - 沿 parent 链查询本字段的子组件 (CodeBlock / ThinkingCard /
          ToolCallCardBase / GenerationStatusBar) 也退化为瞬时路径.

        打开后所有路径恢复动画 (假设各子开关也 enabled).
        """
        self._animationsEnabled = bool(enabled)
        if not self._animationsEnabled:
            # 取消正在跑的动画, 避免被关之后还看到过渡尾巴
            self._cancelScrollAnimation()
            if self._branchSnapshotPlayer.is_playing():
                self._branchSnapshotPlayer.cancel()

    def animationsEnabled(self) -> bool:
        return self._animationsEnabled

    def setSmoothScrollEnabled(self, enabled: bool) -> None:
        """单独控制平滑滚动 (默认 ``True``).

        关闭后 ``_smoothScrollTo`` / ``_smoothScrollToBottom`` /
        ``_forceSmoothScrollToBottom`` / ``_smoothScrollWidgetToTop`` 都退
        化为瞬时 setValue. ``_animationsEnabled`` 总开关依然生效 (它关
        后本开关状态不重要).
        """
        self._smoothScrollEnabled = bool(enabled)
        if not self._smoothScrollEnabled:
            self._cancelScrollAnimation()

    def smoothScrollEnabled(self) -> bool:
        return self._smoothScrollEnabled

    def setBranchSwitchAnimationEnabled(self, enabled: bool) -> None:
        """单独控制分支切换截图过渡 (默认 ``True``).

        关闭后 ``editAndFork`` / ``switchVersion`` 不再走截图淺出路径,
        视图重建瞬间发生.
        """
        self._branchSwitchAnimationEnabled = bool(enabled)
        if not self._branchSwitchAnimationEnabled:
            if self._branchSnapshotPlayer.is_playing():
                self._branchSnapshotPlayer.cancel()

    def branchSwitchAnimationEnabled(self) -> bool:
        return self._branchSwitchAnimationEnabled

    def setAutoScrollOnCardExpand(self, enabled: bool) -> None:
        """思考 / 工具卡片展开后是否自动滚动到卡片底部 (默认 ``False``).

        默认关: 思考 / 工具卡展开时用户通常在卡片附近, 强制滚动会丢失
        阅读位置. 没有需求不建议打开.
        """
        self._autoScrollOnCardExpand = bool(enabled)

    def autoScrollOnCardExpand(self) -> bool:
        return self._autoScrollOnCardExpand

    # ------------------------------------------------------------------
    # 对话分叉 (Conversation forking) 公共 API
    # ------------------------------------------------------------------

    def editAndFork(self, user_msg_id: str, new_content: str) -> str:
        """编辑某条 USER 消息并在该消息处生成新分支 (facade).

        步骤实现详见 ``_BranchManager.editAndFork``. 完成后会发出
        ``userMessageEdited(new_user_msg_id, new_content)``, 宿主据此触发
        LLM 重新生成 AI 回复.
        """
        return self._branches.editAndFork(user_msg_id, new_content)

    def switchVersion(self, user_msg_id: str, new_index: int) -> str:
        """切换到该 USER 消息的某个版本 (facade)."""
        return self._branches.switchVersion(user_msg_id, new_index)

    def versionInfo(self, user_msg_id: str) -> Optional[Tuple[int, int]]:
        """查询某条 USER 消息的 ``(total, active)``, 无分叉返回 ``None`` (facade)."""
        return self._branches.versionInfo(user_msg_id)

    # ------------------------------------------------------------------
    # 审批策略 公共 API (P2c 重构: bool -> ApprovalPolicy 三态)
    # ------------------------------------------------------------------

    def setApprovalPolicy(self, tool_name: str,
                          policy: ApprovalPolicy) -> None:
        """设置某个工具名的审批策略 (三态: ALLOW / ASK / DENY).

        后续 ``addToolCall(…, requires_approval=None)`` 时会查询本表:
            ALLOW -> 初始 PENDING       (直接执行)
            ASK   -> 初始 PENDING_APPROVAL (弹审批)
            DENY  -> 初始 REJECTED      (自动拒绝)

        显式传 ``requires_approval=True/False`` 会覆盖本默认.

        Args:
            tool_name: 工具名 (建议与 addToolCall 传入 ``tool_name`` 保持一致).
            policy:    ``ApprovalPolicy`` 枚举值.
        """
        if not tool_name:
            return
        self._approvalPolicies[tool_name] = policy

    def approvalPolicy(self, tool_name: str) -> ApprovalPolicy:
        """查询某个工具名的审批策略 (未设置返回 ALLOW)."""
        return self._approvalPolicies.get(tool_name, ApprovalPolicy.ALLOW)

    # --- 向后兼容的旧 bool API, 映射到三态 ---

    def setToolApprovalRequired(self, tool_name: str,
                                required: bool = True) -> None:
        """旧 API 包装: True -> ASK, False -> ALLOW. 新代码建议直接用
        ``setApprovalPolicy(tool_name, ApprovalPolicy.X)`` 表达三态语义.
        """
        self.setApprovalPolicy(
            tool_name,
            ApprovalPolicy.ASK if required else ApprovalPolicy.ALLOW,
        )

    def requireApproval(self, *tool_names: str) -> None:
        """便利方法: 批量设为 ASK (需审批)."""
        for n in tool_names:
            self.setApprovalPolicy(n, ApprovalPolicy.ASK)

    def alwaysApprove(self, *tool_names: str) -> None:
        """便利方法: 批量设为 ALLOW (不弹审批, 直接 PENDING)."""
        for n in tool_names:
            self.setApprovalPolicy(n, ApprovalPolicy.ALLOW)

    def alwaysReject(self, *tool_names: str) -> None:
        """便利方法: 批量设为 DENY (自动拒绝, 不弹 UI)."""
        for n in tool_names:
            self.setApprovalPolicy(n, ApprovalPolicy.DENY)

    def isApprovalRequired(self, tool_name: str) -> bool:
        """兼容旧 API: 仅当 policy == ASK 时返回 True."""
        return self._approvalPolicies.get(tool_name) == ApprovalPolicy.ASK

    def approveToolCall(self, message_id: str, call_id: str) -> None:
        """代码路径批准 (等同于用户点 批准 按钮).

        状态 PENDING_APPROVAL -> PENDING. 会同时发出
        ``toolCallApproved(msg_id, call_id)``.
        """
        self._transitionApproval(message_id, call_id, approve=True)

    def rejectToolCall(self, message_id: str, call_id: str) -> None:
        """代码路径拒绝. 状态 PENDING_APPROVAL -> REJECTED."""
        self._transitionApproval(message_id, call_id, approve=False)

    # ----- 内部: 审批状态转换 -----
    # P1b: 原本 _onToolCallApproveClicked / _onToolCallRejectClicked 两个藄薄包装
    # 被合并进 _onBubbleAction 路由, 这里只保留转换实现.

    def _transitionApproval(self, message_id: str, call_id: str,
                            approve: bool) -> None:
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.toolCallCard(call_id)
        if card is None:
            return
        seg = card.segment()
        if seg is None or seg.status != ToolCallStatus.PENDING_APPROVAL:
            # 重复点击 / 状态不匹配 静默忽略
            return
        new_status = (
            ToolCallStatus.PENDING if approve else ToolCallStatus.REJECTED
        )
        card.setStatus(new_status)
        if approve:
            self.toolCallApproved.emit(message_id, call_id)
        else:
            self.toolCallRejected.emit(message_id, call_id)

    def _rememberPolicyAndTransition(self, message_id: str, call_id: str,
                                     policy: ApprovalPolicy,
                                     approve: bool) -> None:
        """[总是允许] / [总是拒绝] 按钮的合并入口: 先把工具的审批策略写进
        ``_approvalPolicies`` (后续同 tool_name 自动应用此策略), 再转换本次
        调用的状态.
        """
        bubble = self._bubbles.get(message_id)
        if bubble is None:
            return
        card = bubble.toolCallCard(call_id)
        if card is None:
            return
        seg = card.segment()
        if seg is not None and seg.tool_name:
            self.setApprovalPolicy(seg.tool_name, policy)
        self._transitionApproval(message_id, call_id, approve=approve)

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
        # 动画驱动的 setValue 也会触发本信号. 动画期间不切换
        # ``_autoScroll`` 状态, 仅 finished 后由 ``_onScrollAnimFinished``
        # 调一次 ``_refreshScrollState`` 重新同步.
        if self._programmaticScroll:
            return
        dist = self._distanceToBottom()
        if dist > self._SCROLL_PAUSE_THRESHOLD and self._autoScroll:
            self._autoScroll = False
            self._jumpBtn.show()
            self._positionJumpButton()
        elif dist < self._SCROLL_BOTTOM_THRESHOLD and not self._autoScroll:
            self._autoScroll = True
            self._jumpBtn.hide()

    def _refreshScrollState(self) -> None:
        """强制根据当前滚动位置重新评估 jumpBtn 显隐 + autoScroll 状态.

        ``_onScrollChanged`` 只能处理 valueChanged 触发的状态切换 (用户主动
        滚动). 当代码批量 add/remove 消息 (例如 ``editAndFork`` /
        ``switchVersion``) 后, 内容高度跳变, 但用户没有滚动, 那两个 if 的
        前置条件 (``and self._autoScroll`` / ``and not self._autoScroll``)
        可能正好不命中 (例如分叉前用户已滚到底, autoScroll=True, 切到更
        短的分支后 dist 仍然 < threshold, 第二个 elif 不命中因为
        autoScroll 已经是 True), jumpBtn 残留 visible. 本方法直接根据距底
        距离重设两者, 显式同步状态.
        """
        dist = self._distanceToBottom()
        if dist < self._SCROLL_BOTTOM_THRESHOLD:
            self._autoScroll = True
            self._jumpBtn.hide()
        elif dist > self._SCROLL_PAUSE_THRESHOLD:
            self._autoScroll = False
            self._jumpBtn.show()
            self._positionJumpButton()

    def _onRangeChanged(self, _min: int, _max: int):
        # 同步滚到底.
        # rangeChanged 在 Qt 完成 layout 重新计算后才发出, 此时 maximum 是
        # 内容稳定后的真值.

        # 卡片展开 / 折叠 动画期间: **一律**锁 viewport.value 到启动时的
        # saved 快照, 不管启动时是否在底部. 这样:
        # - 上方 widget 视觉位置完全不动 (widget.y_in_content 不变 +
        #   viewport.value 不变 -> 视觉 y 不变), 不再有"上下漂移"抖动
        # - 卡片下方 widget 跟着卡片增长被推下 (视觉连续, 卡片在向下伸展)
        # - 启动时在底部的情况, endLayoutAnimation 后会触发 _catchUpToBottomIfNeeded
        #   平滑追到新底部, 形成"卡片展开 → 视图平滑追底"的双段式动画
        if self._layoutAnimationDepth > 0:
            bar = self.verticalScrollBar()
            target = max(0, min(self._savedScrollValue, _max))
            if bar.value() != target:
                self._programmaticScroll = True
                try:
                    bar.setValue(target)
                finally:
                    self._programmaticScroll = False
            return

        # 动画中且 tracking_max: 动态更新 endValue 让动画跟到真底部.
        # 使用场景: 用户发送消息 -> emit -> 应用层 addMessage 同步返回
        # 但 layout 未刷 -> _forceSmoothScrollToBottom 启动动画 (endValue=旧max)
        # -> Qt 异步刷 layout -> rangeChanged -> 这里把 anim.endValue 追到
        # new max, 动画顺滑跑到真底部.
        if (self._programmaticScroll and self._scrollAnimTrackingMax
                and self._scrollAnim is not None
                and self._scrollAnim.state() == QPropertyAnimation.State.Running):
            self._scrollAnim.setEndValue(int(_max))
            return

        # 非动画驱动 + 在底部状态: 贴底 (debounce 16ms).
        # 不再直接 ``_scrollToBottom``, 避免 Qt layout chain 连续 emit
        # 多次时 viewport 在多个中间 maximum 之间跳动.
        if self._autoScroll and not self._programmaticScroll:
            self._scheduleRangeCatchUp()

    # ------------------------------------------------------------------
    # layout 动画会席 (卡片展开 / 折叠 / GenerationStatusBar 进出场)
    # ------------------------------------------------------------------

    def beginLayoutAnimation(self, animating_widget: Optional[QWidget] = None) -> None:
        """卡片展开 / 折叠 动画启动时调用 (一般由 ``animate_collapse`` /
        ``CodeBlock.setExpanded`` 自动 duck-type 调).

        首次进入时 (depth 0->1) 保存当前 ``bar.value()`` 与 ``_autoScroll``
        快照. 动画期间 ``_onRangeChanged`` 一律锁 viewport.value 到 saved.

        v5 设计下 ``animate_collapse`` 在跳变 parent 那一帧锁住 parent
        的 min/max height, ChatBubble 只重排一次, sibling 一次跳到位. 整
        个 220ms 动画期间 ChatBubble 完全不重排, viewport 不动.

        Args:
            animating_widget: 已废弃 (v4 freeze 方案的残留参数, v5 不用).
                              保留只为向后兼容 ``begin_layout_animation``
                              helper 的新签名调用.
        """
        del animating_widget  # v5 不需要 (v4 freeze 方案废弃)
        if self._layoutAnimationDepth == 0:
            self._savedScrollValue = self.verticalScrollBar().value()
            self._savedAtBottom = bool(self._autoScroll)
        self._layoutAnimationDepth += 1

    def endLayoutAnimation(self) -> None:
        """卡片展开 / 折叠 动画结束时调用.

        计数器递减, 归 0 后 ``QTimer.singleShot(0, _catchUpToBottomIfNeeded)``
        推迟一帧让 layout 真正稳定 + 启动平滑追底 (如果启动时在底部).
        """
        self._layoutAnimationDepth = max(0, self._layoutAnimationDepth - 1)
        if self._layoutAnimationDepth == 0:
            QTimer.singleShot(0, self._catchUpToBottomIfNeeded)

    def _catchUpToBottomIfNeeded(self) -> None:
        """layout 动画结束后 追底的 catch-up 逻辑.

        新设计下 (v3): 动画期间 viewport 一律锁 saved, 动画结束时 viewport
        在原 saved 位置. 如果启动时**在底部** (``_savedAtBottom == True``),
        现在卡片展开后 saved 已经离底部很远了, 平滑追到新底部, 形成
        "卡片展开 220ms → viewport 平滑追底 180ms" 的双段式动画 — 视觉
        连续, 不抖.

        启动时不在底部 (用户在中间查看历史): 不追底, viewport 保持原位.
        """
        if self._layoutAnimationDepth > 0:
            return
        if self._programmaticScroll:
            return
        if not self._savedAtBottom:
            return
        if self._distanceToBottom() <= self._SCROLL_BOTTOM_THRESHOLD:
            return
        # 平滑追底 (180ms 动画), 与卡片 220ms 展开动画形成自然双段过渡
        self._smoothScrollToBottom(180)

    def _scheduleRangeCatchUp(self) -> None:
        """Debounce 贴底: 连续 16ms 内的 rangeChanged 合并为一次贴底.

        **抖动修复根因**: Qt layout chain 在 setVisible / addWidget /
        polish 多轮重算过程中 会 emit rangeChanged 多次, 每次
        ``maximum`` 是不同的中间值. 之前每次都走 ``_scrollToBottom``
        (设 viewport.value = 当时的 maximum), viewport 在多个中间
        maximum 之间跳 —— 这就是用户看到的“整个 view 区域上下跳”.

        **修复**: 每次重启 16ms timer (debounce), 连续快速 emit 会
        不断重置 timer, 直到 16ms 内没有新 emit 才 fire 一次 setValue,
        用的是最后稳定的 maximum, viewport 一次贴到真底.
        """
        if self._rangeCatchUpTimer is None:
            self._rangeCatchUpTimer = QTimer(self)
            self._rangeCatchUpTimer.setSingleShot(True)
            self._rangeCatchUpTimer.setInterval(16)
            self._rangeCatchUpTimer.timeout.connect(self._rangeCatchUpFire)
        # ``start`` 会重置 timer (取消上个 pending fire) —— 这就是 debounce.
        self._rangeCatchUpTimer.start()

    def _rangeCatchUpFire(self) -> None:
        """Debounce timer fire: 检查状态 + 瞬间贴到真底."""
        if not self._autoScroll:
            return
        if self._programmaticScroll:
            return
        # layout 动画期间也不贴底 (depth>0 路径锁住 saved)
        if self._layoutAnimationDepth > 0:
            return
        self._scrollToBottom()

    # ------------------------------------------------------------------
    # 平滑滚动 (“回到最新” / 发送消息后 / 卡片展开后定位)
    # ------------------------------------------------------------------

    def _shouldUseSmoothScroll(self) -> bool:
        """总开关 + 平滑滚动开关 + visible 决定是否走平滑动画."""
        if not self._smoothScrollEnabled:
            return False
        if not self._animationsEnabled:
            return False
        if not self.isVisible():
            return False
        return True

    def _smoothScrollTo(self, target: int, duration: int = 280) -> None:
        """平滑滚动到 verticalScrollBar 某个值 (clamp 到 [0, maximum]).

        起点 = 当前 value, OutCubic. 动画期间 ``_programmaticScroll = True``,
        ``_onScrollChanged`` 早 return 避免误切 ``_autoScroll`` 状态.
        finished 后清标志并刷新 ``_refreshScrollState``.
        关闭平滑滚动时退化为瞬间 setValue.

        注意: tracking_max 模式下 (``_smoothScrollToBottom`` 调起), 即使
        ``bar.value() == target`` (用户在底) 也不 short-circuit, 因为 layout
        异步刷后 maximum 会变大, ``rangeChanged`` 会追 endValue 到真底部.
        """
        bar = self.verticalScrollBar()
        target = max(0, min(int(target), bar.maximum()))
        if not self._shouldUseSmoothScroll():
            bar.setValue(target)
            return
        # tracking_max 模式: 不 short-circuit, 启动动画等待 rangeChanged 追 endValue.
        if bar.value() == target and not self._scrollAnimTrackingMax:
            return

        # 取消上一轮动画但保留 _scrollAnimTrackingMax 标志 ——
        # 该标志是 _smoothScrollToBottom 调本方法**之前**设的 True, 动画
        # 中 _onRangeChanged 会读它来决定是否 setEndValue. 不能在这里清掉.
        if (self._scrollAnim is not None
                and self._scrollAnim.state() == QPropertyAnimation.State.Running):
            self._scrollAnim.stop()
        self._programmaticScroll = True
        anim = QPropertyAnimation(bar, b"value", self)
        anim.setDuration(int(duration))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(int(bar.value()))
        anim.setEndValue(int(target))
        anim.finished.connect(self._onScrollAnimFinished)
        self._scrollAnim = anim
        anim.start()

    def _smoothScrollToBottom(self, duration: int = 280) -> None:
        """平滑滚到底. 启动前隐藏 jumpBtn (用户期望按钮立即消失).

        设 ``_scrollAnimTrackingMax = True``: 动画期间 ``rangeChanged`` 会
        动态更新 endValue, 跟随 Qt layout deferred 刷新后的真底部.
        """
        self._jumpBtn.hide()
        self._scrollAnimTrackingMax = True
        bar = self.verticalScrollBar()
        self._smoothScrollTo(bar.maximum(), duration)

    def _forceSmoothScrollToBottom(self, duration: int = 280) -> None:
        """强制平滑滚到底, 不管当前 ``_autoScroll`` 状态如何.

        用法: 用户发送消息后 (Panel 侧 hook), 即使用户在上方查看历史,
        也要被带回底部看自己刚发的消息. 充充重置 ``_autoScroll = True``.
        """
        self._autoScroll = True
        self._smoothScrollToBottom(duration)

    def _smoothScrollWidgetToTop(self, w: QWidget, duration: int = 280) -> None:
        """让指定 widget 的顶部与 viewport 顶部对齐 (扣除 _vLayout top padding).

        供 CodeBlock 展开后定位用. CodeBlock 在 setExpanded(True) 动画
        finished 时通过 duck typing 找最近的 ancestor (本 view) 调本方法.
        """
        if w is None or self.widget() is None:
            return
        # mapTo(scroll widget, (0,0)) -> widget 在滚动内容坐标系里的 y
        pos = w.mapTo(self.widget(), QPoint(0, 0))
        # 留出 _vLayout top padding 的呼吸空间 (16px), 让 widget 顶部别贴死
        # viewport 顶.
        target = max(0, pos.y() - 16)
        self._smoothScrollTo(target, duration)

    def _cancelScrollAnimation(self) -> None:
        """取消正在跑的滚动动画. stop 不会触发 finished, 手动清标志."""
        if (self._scrollAnim is not None
                and self._scrollAnim.state() == QPropertyAnimation.State.Running):
            self._scrollAnim.stop()
        self._programmaticScroll = False
        self._scrollAnimTrackingMax = False

    def _onScrollAnimFinished(self) -> None:
        """滚动动画自然跑完. 清 _programmaticScroll / tracking 标志 + 同步 jumpBtn / autoScroll."""
        self._programmaticScroll = False
        self._scrollAnimTrackingMax = False
        self._refreshScrollState()

    def _playBranchSwitchOverlay(self) -> None:
        """启动一次分支切换截图过渡. 给 :class:`_BranchManager` 在视图重建前调.

        抓取 ``_inner.grab()`` 当前截图, overlay 显示在 viewport 上,
        opacity 1->0 + offset_y 0->-8px, 220ms OutCubic. 重建逻辑由
        manager 处理, overlay 不参与 layout, 不影响重建后几何.
        """
        if not self._branchSwitchAnimationEnabled:
            return
        if not self._animationsEnabled:
            return
        if not self.isVisible():
            return
        # 上一次过渡还在跑: 立即收尾, 然后开始新一轮.
        if self._branchSnapshotPlayer.is_playing():
            self._branchSnapshotPlayer.cancel()
        snapshot = self._inner.grab()
        if snapshot.isNull() or snapshot.size().isEmpty():
            return
        self._branchSnapshotPlayer.play(
            self.viewport(), snapshot, duration=220, offset_y=-8,
        )

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

    def _positionGenBar(self):
        """Facade: 把几何重定位交给生成控制器."""
        self._generation.positionBar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # viewport 变化时重新锁定 inner 宽度, 否则窗口缩放时 inner 不更新
        self._applyMaxContentWidth()
        self._positionJumpButton()
        self._positionGenBar()

    # ------------------------------------------------------------------
    # 事件拦截: 用户主动输入时取消滚动动画
    # ------------------------------------------------------------------

    def wheelEvent(self, event):
        """用户滾轮 -> 立即停掉滚动动画 (用户优先), 然后让父类处理."""
        self._cancelScrollAnimation()
        super().wheelEvent(event)

    def eventFilter(self, obj, event):
        """用户在 verticalScrollBar 上 mouse press / wheel -> 停滚动动画.

        不走 ``mousePressEvent`` 路径是因为拖动滚动条的事件会被 QScrollBar
        拦截不到达 view, 只能用 eventFilter 看到.
        """
        if obj is self.verticalScrollBar():
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.Wheel):
                self._cancelScrollAnimation()
        return super().eventFilter(obj, event)
