# coding: utf-8
"""USER 角色 ChatBubble body.

视觉: 整体右对齐, 头部 [name + subtitle | avatar], 中间是浅色气泡背景的
``MarkdownView`` (展示态) 或 ``PlainTextEdit`` (编辑态), 底部是 [选页器 +
操作栏] 行.

本 body 独有功能:
    * 内联编辑模式 (inline editor + Save/Cancel 按钮)
    * 版本选页器 (◀ {n}/{N} ▶), 用于 ``editAndFork`` 后切换分叉版本
"""

from typing import Optional, Tuple, Union

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from .....common.icon import FluentIcon
from ...button import PrimaryPushButton, PushButton, TransparentToolButton
from ...label import CaptionLabel, StrongBodyLabel
from ...line_edit import PlainTextEdit
from ...tool_tip import ToolTipFilter, ToolTipPosition
from ..chat_avatar import ChatAvatar
from ..chat_message import ChatMessage, ChatRole
from ..markdown_view import MarkdownView
from ._action_bar import BubbleActionBar
from ._body_base import BubbleAction, BubbleBodyBase


__all__ = ['UserBubbleBody']


class UserBubbleBody(BubbleBodyBase):
    """USER 角色气泡 body — 右对齐气泡 + 内联编辑器 + 版本选页器."""

    def __init__(self, message: ChatMessage,
                 parent: Optional[QWidget] = None):
        super().__init__(message, parent)
        assert message.role == ChatRole.USER

        # 操作栏 (USER: 复制 + 编辑 + 删除).
        # 4 个原始按钮 signal 在本类被翻译成 ``actionTriggered`` 上的 action ID
        # (见模块 BubbleAction 常量). ChatBubble dispatcher 只需 connect 1 个
        # 信号, 不再连 9 条.
        self._actionBar = BubbleActionBar(message.id, ChatRole.USER, self)
        self._actionBar.copyClicked.connect(self._emitCopy)
        self._actionBar.editClicked.connect(self._emitEdit)
        self._actionBar.deleteClicked.connect(self._emitDelete)
        # 编辑按钮额外触发: 进入内联编辑模式
        self._actionBar.editButton().clicked.connect(self._onEditBtnClicked)

        # 版本选页器
        self._versionTotal = 1
        self._versionActive = 0

        self._setupUi()
        self.applyMessage()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(8, 2, 8, 2)
        rootLayout.setSpacing(6)

        # ---- 头部行: [stretch] [name + subtitle 列, 右对齐] [avatar] ----
        headerRow = QWidget(self)
        headerLayout = QHBoxLayout(headerRow)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(10)

        textCol = QWidget(headerRow)
        textColLayout = QVBoxLayout(textCol)
        textColLayout.setContentsMargins(0, 0, 0, 0)
        textColLayout.setSpacing(0)

        self._senderLabel = StrongBodyLabel(self.displayName(), textCol)
        self._senderLabel.setObjectName("senderName")
        self._senderLabel.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )

        self._subtitleLabel = CaptionLabel("", textCol)
        self._subtitleLabel.setObjectName("senderSubtitle")
        self._subtitleLabel.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        self._subtitleLabel.hide()

        textColLayout.addWidget(self._senderLabel, 0, Qt.AlignmentFlag.AlignRight)
        textColLayout.addWidget(self._subtitleLabel, 0, Qt.AlignmentFlag.AlignRight)

        self._avatar = ChatAvatar(ChatRole.USER, 32, headerRow)

        headerLayout.addStretch(1)
        headerLayout.addWidget(textCol, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- 气泡行: [stretch] [body 框] ----
        bubbleRow = QWidget(self)
        bubbleLayout = QHBoxLayout(bubbleRow)
        bubbleLayout.setContentsMargins(0, 0, 0, 0)
        bubbleLayout.setSpacing(0)

        self._bubble = QFrame(bubbleRow)
        self._bubble.setObjectName("bubbleBody")
        self._bubble.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred,
        )
        self._bubble.setMaximumWidth(self._MAX_CONTENT_WIDTH)
        bodyLayout = QVBoxLayout(self._bubble)
        bodyLayout.setContentsMargins(12, 8, 12, 6)
        bodyLayout.setSpacing(2)

        # 显示态: MarkdownView
        self._content = MarkdownView("", self._bubble)
        bodyLayout.addWidget(self._content)

        # 编辑态: PlainTextEdit + Save/Cancel 按钮 (默认 hide)
        self._editor = PlainTextEdit(self._bubble)
        self._editor.setObjectName("bubbleInlineEditor")
        self._editor.setMinimumHeight(80)
        self._editor.hide()
        bodyLayout.addWidget(self._editor)

        self._editToolbar = QWidget(self._bubble)
        self._editToolbar.setObjectName("bubbleInlineEditToolbar")
        editToolbarLayout = QHBoxLayout(self._editToolbar)
        editToolbarLayout.setContentsMargins(0, 6, 0, 0)
        editToolbarLayout.setSpacing(8)
        editToolbarLayout.addStretch(1)

        self._editCancelBtn = PushButton(self.tr("取消"), self._editToolbar)
        self._editCancelBtn.clicked.connect(lambda: self.exitEditMode(save=False))

        self._editSaveBtn = PrimaryPushButton(
            self.tr("保存并重新生成"), self._editToolbar,
        )
        self._editSaveBtn.clicked.connect(lambda: self.exitEditMode(save=True))

        editToolbarLayout.addWidget(self._editCancelBtn, 0)
        editToolbarLayout.addWidget(self._editSaveBtn, 0)
        self._editToolbar.hide()
        bodyLayout.addWidget(self._editToolbar)

        bubbleLayout.addStretch(1)
        bubbleLayout.addWidget(self._bubble, 0)

        # ---- 操作行: [stretch] [选页器 (默认 hide) + actionBar] ----
        actionRow = QWidget(self)
        actionRowLayout = QHBoxLayout(actionRow)
        actionRowLayout.setContentsMargins(0, 0, 0, 0)
        actionRowLayout.setSpacing(8)
        actionRowLayout.addStretch(1)
        actionRowLayout.addWidget(self._buildVersionPager())
        actionRowLayout.addWidget(self._actionBar)

        rootLayout.addWidget(headerRow)
        rootLayout.addWidget(bubbleRow)
        rootLayout.addWidget(actionRow)

    def _buildVersionPager(self) -> QWidget:
        """构造版本选页器: ``◀ {n}/{N} ▶``. 默认 hidden."""
        self._versionPager = QWidget(self)
        self._versionPager.setObjectName("bubbleVersionPager")
        layout = QHBoxLayout(self._versionPager)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._versionPrevBtn = TransparentToolButton(
            FluentIcon.LEFT_ARROW, self._versionPager,
        )
        self._versionPrevBtn.setFixedSize(20, 20)
        self._versionPrevBtn.setIconSize(QSize(10, 10))
        self._versionPrevBtn.setToolTip(self.tr("上一版本"))
        self._versionPrevBtn.installEventFilter(
            ToolTipFilter(
                self._versionPrevBtn, showDelay=300,
                position=ToolTipPosition.TOP,
            )
        )
        self._versionPrevBtn.clicked.connect(
            lambda: self._onVersionPagerClicked(-1)
        )

        self._versionLabel = CaptionLabel("1/1", self._versionPager)
        self._versionLabel.setObjectName("bubbleVersionLabel")
        self._versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._versionLabel.setMinimumWidth(28)

        self._versionNextBtn = TransparentToolButton(
            FluentIcon.RIGHT_ARROW, self._versionPager,
        )
        self._versionNextBtn.setFixedSize(20, 20)
        self._versionNextBtn.setIconSize(QSize(10, 10))
        self._versionNextBtn.setToolTip(self.tr("下一版本"))
        self._versionNextBtn.installEventFilter(
            ToolTipFilter(
                self._versionNextBtn, showDelay=300,
                position=ToolTipPosition.TOP,
            )
        )
        self._versionNextBtn.clicked.connect(
            lambda: self._onVersionPagerClicked(+1)
        )

        layout.addWidget(self._versionPrevBtn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._versionLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._versionNextBtn, 0, Qt.AlignmentFlag.AlignVCenter)
        self._versionPager.hide()
        return self._versionPager

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

        self._content.setMarkdown(self._message.content)

    def appendDelta(self, delta: str) -> None:
        if not delta:
            return
        self._message.content = self._message.content + delta
        self._content.appendMarkdown(delta)

    def setContent(self, markdown: str) -> None:
        self._message.content = markdown
        self._content.setMarkdown(self._message.content)

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
        self._content.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)

    # ------------------------------------------------------------------
    # 内联编辑
    # ------------------------------------------------------------------

    def isInEditMode(self) -> bool:
        return self._editor.isVisible()

    def enterEditMode(self) -> None:
        if self.isInEditMode():
            return
        self._editor.setPlainText(self._message.content)
        self._content.hide()
        self._editor.show()
        self._editToolbar.show()
        self._editor.setFocus()
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._editor.setTextCursor(cursor)

    def exitEditMode(self, save: bool = False) -> None:
        if not self.isInEditMode():
            return

        new_text = self._editor.toPlainText().strip()
        self._editor.hide()
        self._editToolbar.hide()
        self._content.show()

        if save and new_text and new_text != self._message.content:
            self.actionTriggered.emit(
                BubbleAction.EDIT_CONFIRM, self._message.id, new_text,
            )
        else:
            self.actionTriggered.emit(
                BubbleAction.EDIT_CANCEL, self._message.id, None,
            )

    def _onEditBtnClicked(self) -> None:
        # 编辑按钮: 默认进入内联编辑; ``editClicked`` 信号已经由 BubbleActionBar
        # 独立 emit, 这里只额外驱动编辑模式.
        if not self.isInEditMode():
            self.enterEditMode()

    # ------------------------------------------------------------------
    # 版本选页器
    # ------------------------------------------------------------------

    def setVersionInfo(self, total: int, active: int) -> None:
        self._versionTotal = max(1, int(total))
        self._versionActive = max(0, min(self._versionTotal - 1, int(active)))
        if self._versionTotal <= 1:
            self._versionPager.hide()
            return
        self._versionLabel.setText(
            f"{self._versionActive + 1}/{self._versionTotal}"
        )
        self._versionPrevBtn.setEnabled(self._versionActive > 0)
        self._versionNextBtn.setEnabled(
            self._versionActive < self._versionTotal - 1
        )
        self._versionPager.show()

    def versionInfo(self) -> Optional[Tuple[int, int]]:
        if self._versionTotal <= 1:
            return None
        return (self._versionTotal, self._versionActive)

    def _onVersionPagerClicked(self, delta: int) -> None:
        target = self._versionActive + delta
        if 0 <= target < self._versionTotal and target != self._versionActive:
            self.actionTriggered.emit(
                BubbleAction.VERSION_SWITCH, self._message.id, target,
            )

    # ------------------------------------------------------------------
    # actionBar -> actionTriggered 适配器
    # ------------------------------------------------------------------

    def _emitCopy(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.COPY, msg_id, None)

    def _emitEdit(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.EDIT, msg_id, None)

    def _emitDelete(self, msg_id: str) -> None:
        self.actionTriggered.emit(BubbleAction.DELETE, msg_id, None)

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
