# coding: utf-8
"""聊天消息气泡组件

单条消息气泡 = 头像 + 主体 (时间戳 + Markdown 内容 + 操作栏).
USER 角色靠右布局, AGENT 角色靠左布局, SYSTEM 角色居中弱化.
操作栏 (复制/编辑/删除) 默认隐藏, 鼠标进入气泡时淡入显示.
"""

from typing import Optional, Union

from PySide6.QtCore import QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QSizePolicy,
    QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..button import TransparentToolButton
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from .chat_avatar import ChatAvatar
from .chat_message import ChatMessage, ChatRole
from .markdown_view import MarkdownView


__all__ = ['ChatBubble']


# ----------------------------------------------------------------------
# ChatBubble 主体
# ----------------------------------------------------------------------

class ChatBubble(QFrame):
    """单条聊天消息组件

    根据消息角色自动选择两种渲染模式:

    - **USER**:  气泡风格, 整体右对齐, 头像在右侧, 内容外包浅色气泡背景.
                 适合短消息, 视觉上清晰区分用户输入.
    - **AGENT**: 平铺风格, 顶部 [头像 + 发送者名 (加粗) | subtitle], 下方
                 markdown 内容直接铺展, 无气泡背景. 适合长篇 Agent 回答.
    - **SYSTEM**: 居中弱化展示 (透明背景, 无头像).

    信号:
        copyClicked(str):   复制按钮点击, 参数为消息 id
        editClicked(str):   编辑按钮点击, 参数为消息 id
        deleteClicked(str): 删除按钮点击, 参数为消息 id

    构造函数:
        ChatBubble(message: ChatMessage, parent: QWidget = None)
    """

    copyClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)

    _MAX_CONTENT_WIDTH = 920
    # 平铺模式: 头像尺寸. 正文不再缩进, 直接占满整行宽度.
    _FLAT_HEADER_AVATAR_SIZE = 28

    def __init__(self, message: ChatMessage, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._message = message
        self._defaultSenderName: Optional[str] = None  # ChatView 注入的默认名
        self._actionBarVisible = False
        # 用于存放 widgets 引用; 不同布局共用相同字段
        self._timestamp: Optional[CaptionLabel] = None
        self._senderLabel: Optional[StrongBodyLabel] = None
        self._subtitleLabel: Optional[BodyLabel] = None

        self._setupUi()
        self._applyMessage()
        FluentStyleSheet.CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _setupUi(self):
        self.setObjectName("chatBubble")
        self.setProperty("role", self._message.role.value)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # 操作栏 (所有模式共用, 内部根据 role 决定显隐与对齐)
        self._buildActionBar()

        if self._message.role == ChatRole.USER:
            self._setupUserBubble()
        elif self._message.role == ChatRole.AGENT:
            self._setupAgentFlat()
        else:
            self._setupSystem()

    # -- 操作栏 -----------------------------------------------------------

    def _buildActionBar(self):
        self._actionBar = QWidget(self)
        self._actionBar.setObjectName("actionBar")
        actionLayout = QHBoxLayout(self._actionBar)
        actionLayout.setContentsMargins(0, 0, 0, 0)
        actionLayout.setSpacing(2)

        self._copyBtn = TransparentToolButton(FluentIcon.COPY, self._actionBar)
        self._copyBtn.setFixedSize(24, 24)
        self._copyBtn.setIconSize(QSize(14, 14))
        self._copyBtn.setToolTip(self.tr("复制消息"))
        self._copyBtn.clicked.connect(lambda: self.copyClicked.emit(self._message.id))

        self._editBtn = TransparentToolButton(FluentIcon.EDIT, self._actionBar)
        self._editBtn.setFixedSize(24, 24)
        self._editBtn.setIconSize(QSize(14, 14))
        self._editBtn.setToolTip(self.tr("编辑消息"))
        self._editBtn.clicked.connect(lambda: self.editClicked.emit(self._message.id))

        self._deleteBtn = TransparentToolButton(FluentIcon.DELETE, self._actionBar)
        self._deleteBtn.setFixedSize(24, 24)
        self._deleteBtn.setIconSize(QSize(14, 14))
        self._deleteBtn.setToolTip(self.tr("删除消息"))
        self._deleteBtn.clicked.connect(lambda: self.deleteClicked.emit(self._message.id))

        actionLayout.addWidget(self._copyBtn)
        actionLayout.addWidget(self._editBtn)
        actionLayout.addWidget(self._deleteBtn)

        # 淡入动画
        self._actionEffect = QGraphicsOpacityEffect(self._actionBar)
        self._actionEffect.setOpacity(0.0)
        self._actionBar.setGraphicsEffect(self._actionEffect)
        self._fadeAni = QPropertyAnimation(self._actionEffect, b"opacity", self)
        self._fadeAni.setDuration(150)

    # -- USER: 气泡布局 ------------------------------------------------

    def _setupUserBubble(self):
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(8, 2, 8, 2)
        rootLayout.setSpacing(6)

        # ---- header: [stretch] [name + subtitle 列, 右对齐] [avatar] ----
        headerRow = QWidget(self)
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(10)

        textCol = QWidget(headerRow)
        textColLayout = QVBoxLayout(textCol)
        textColLayout.setContentsMargins(0, 0, 0, 0)
        textColLayout.setSpacing(0)

        self._senderLabel = StrongBodyLabel(self._displayName(), textCol)
        self._senderLabel.setObjectName("senderName")
        self._senderLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._subtitleLabel = CaptionLabel("", textCol)
        self._subtitleLabel.setObjectName("senderSubtitle")
        self._subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._subtitleLabel.hide()

        textColLayout.addWidget(self._senderLabel, 0, Qt.AlignmentFlag.AlignRight)
        textColLayout.addWidget(self._subtitleLabel, 0, Qt.AlignmentFlag.AlignRight)

        self._avatar = ChatAvatar(self._message.role, 32, headerRow)

        headerLayout.addStretch(1)
        headerLayout.addWidget(textCol, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- bubble row: [stretch] [bubble body] (贴右边, 无右 margin) ----
        bubbleRow = QWidget(self)
        bubbleLayout = QHBoxLayout(bubbleRow)
        bubbleLayout.setContentsMargins(0, 0, 0, 0)
        bubbleLayout.setSpacing(0)

        self._body = QFrame(bubbleRow)
        self._body.setObjectName("bubbleBody")
        self._body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._body.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._body.setMaximumWidth(self._MAX_CONTENT_WIDTH)
        bodyLayout = QVBoxLayout(self._body)
        # 上下 padding 略微下偏 (8/6), 抵消 QTextDocument 顶部 line leading 造成的视觉偏上
        bodyLayout.setContentsMargins(12, 8, 12, 6)
        bodyLayout.setSpacing(2)

        self._content = MarkdownView("", self._body)
        bodyLayout.addWidget(self._content)

        bubbleLayout.addStretch(1)
        bubbleLayout.addWidget(self._body, 0)

        # ---- 操作栏行: 贴右对齐 (与气泡右缘对齐) ----
        actionRow = QWidget(self)
        actionRowLayout = QHBoxLayout(actionRow)
        actionRowLayout.setContentsMargins(0, 0, 0, 0)
        actionRowLayout.setSpacing(0)
        actionRowLayout.addStretch(1)
        actionRowLayout.addWidget(self._actionBar)

        rootLayout.addWidget(headerRow)
        rootLayout.addWidget(bubbleRow)
        rootLayout.addWidget(actionRow)

    # -- AGENT: 平铺布局 -----------------------------------------------

    def _setupAgentFlat(self):
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(8, 6, 8, 6)
        rootLayout.setSpacing(8)

        # 顶部: [头像] [name + subtitle 列, 左对齐] [stretch]
        headerRow = QWidget(self)
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(10)

        self._avatar = ChatAvatar(
            self._message.role, self._FLAT_HEADER_AVATAR_SIZE, headerRow
        )

        textCol = QWidget(headerRow)
        textColLayout = QVBoxLayout(textCol)
        textColLayout.setContentsMargins(0, 0, 0, 0)
        textColLayout.setSpacing(0)

        self._senderLabel = StrongBodyLabel(self._displayName(), textCol)
        self._senderLabel.setObjectName("senderName")
        self._senderLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self._subtitleLabel = CaptionLabel("", textCol)
        self._subtitleLabel.setObjectName("senderSubtitle")
        self._subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._subtitleLabel.hide()

        textColLayout.addWidget(self._senderLabel, 0, Qt.AlignmentFlag.AlignLeft)
        textColLayout.addWidget(self._subtitleLabel, 0, Qt.AlignmentFlag.AlignLeft)

        headerLayout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(textCol, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)

        # 内容区: 直接占满整行宽度, 不缩进
        self._body = QFrame(self)
        self._body.setObjectName("bubbleBody")  # QSS 中 agent role 设为 transparent
        self._body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._body.setMaximumWidth(self._MAX_CONTENT_WIDTH)
        bodyLayout = QVBoxLayout(self._body)
        bodyLayout.setContentsMargins(0, 0, 0, 0)
        bodyLayout.setSpacing(6)

        self._content = MarkdownView("", self._body)
        bodyLayout.addWidget(self._content)

        # 操作栏: 左对齐, 与正文同左缘
        actionRow = QWidget(self)
        actionRowLayout = QHBoxLayout(actionRow)
        actionRowLayout.setContentsMargins(0, 0, 0, 0)
        actionRowLayout.setSpacing(0)
        actionRowLayout.addWidget(self._actionBar)
        actionRowLayout.addStretch(1)

        rootLayout.addWidget(headerRow)
        rootLayout.addWidget(self._body)
        rootLayout.addWidget(actionRow)

    # -- SYSTEM: 居中提示 ----------------------------------------------

    def _setupSystem(self):
        rootLayout = QHBoxLayout(self)
        rootLayout.setContentsMargins(8, 4, 8, 4)
        rootLayout.setSpacing(0)

        self._avatar = ChatAvatar(self._message.role, 2, self)
        self._avatar.hide()

        self._body = QFrame(self)
        self._body.setObjectName("bubbleBody")
        self._body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bodyLayout = QVBoxLayout(self._body)
        bodyLayout.setContentsMargins(12, 6, 12, 6)
        self._content = MarkdownView("", self._body)
        bodyLayout.addWidget(self._content)

        rootLayout.addStretch(1)
        rootLayout.addWidget(self._body)
        rootLayout.addStretch(1)

        self._actionBar.hide()

    # ------------------------------------------------------------------
    # 显示名 / 内容应用
    # ------------------------------------------------------------------

    def _displayName(self) -> str:
        """计算应显示的发送者名: message.sender_name > defaultSenderName > role 默认值"""
        if self._message.sender_name:
            return self._message.sender_name
        if self._defaultSenderName:
            return self._defaultSenderName
        return {
            ChatRole.USER: self.tr("您"),
            ChatRole.AGENT: self.tr("Agent"),
            ChatRole.SYSTEM: self.tr("系统"),
        }.get(self._message.role, "")

    def _applyMessage(self):
        self._avatar.setAvatar(self._message.avatar)
        self._content.setMarkdown(self._message.content)

        # 同步 sender / subtitle (USER 与 AGENT 均使用; subtitle 垂直布局, 无需分隔符)
        if self._senderLabel is not None:
            self._senderLabel.setText(self._displayName())
        if self._subtitleLabel is not None:
            sub = self._message.subtitle
            if sub:
                self._subtitleLabel.setText(sub)
                self._subtitleLabel.show()
            else:
                self._subtitleLabel.hide()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def message(self) -> ChatMessage:
        """返回此气泡承载的 ChatMessage (注意是同一引用)."""
        return self._message

    def appendDelta(self, delta: str):
        """流式追加内容 (转发到内部 MarkdownView)."""
        self._message.content += delta
        self._content.appendMarkdown(delta)

    def setContent(self, markdown: str):
        """覆盖式设置 markdown 内容."""
        self._message.content = markdown
        self._content.setMarkdown(markdown)

    def setUserAvatarFallback(self, avatar: Optional[Union[QIcon, str]]):
        """当消息自身未指定头像时使用此 fallback (由 ChatView 调用)."""
        if self._message.avatar is None:
            self._avatar.setAvatar(avatar)

    def setDefaultSenderName(self, name: Optional[str]):
        """设置 fallback 显示名 (仅当 message.sender_name 为空时生效).

        通常由 ChatView 在 addMessage 时调用, 把 setAgentDisplayName /
        setUserDisplayName 注册的全局名注入到本气泡.
        """
        self._defaultSenderName = name
        if self._senderLabel is not None and not self._message.sender_name:
            self._senderLabel.setText(self._displayName())

    # ------------------------------------------------------------------
    # 操作栏 hover 显隐 (USER 与 AGENT 都启用)
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        if self._message.role != ChatRole.SYSTEM:
            self._fadeAni.stop()
            self._fadeAni.setStartValue(self._actionEffect.opacity())
            self._fadeAni.setEndValue(1.0)
            self._fadeAni.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._message.role != ChatRole.SYSTEM:
            self._fadeAni.stop()
            self._fadeAni.setStartValue(self._actionEffect.opacity())
            self._fadeAni.setEndValue(0.0)
            self._fadeAni.start()
        super().leaveEvent(event)
