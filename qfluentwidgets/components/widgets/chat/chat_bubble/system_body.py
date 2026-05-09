# coding: utf-8
"""SYSTEM 角色 ChatBubble body — 居中弱化的纯文字提示.

无头像, 无操作栏, 仅一个 ``MarkdownView`` 居中. 用于显示对话级别的状态
通告 (例: "对话已重置", "已切换到 v2 分支" 等).
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from ..chat_message import ChatMessage, ChatRole
from ..markdown_view import MarkdownView
from ._body_base import BubbleBodyBase


__all__ = ['SystemBubbleBody']


class SystemBubbleBody(BubbleBodyBase):
    """SYSTEM 角色气泡 body — 居中提示."""

    def __init__(self, message: ChatMessage, parent=None):
        super().__init__(message, parent)
        assert message.role == ChatRole.SYSTEM

        self._setupUi()
        self.applyMessage()

    def _setupUi(self) -> None:
        rootLayout = QHBoxLayout(self)
        rootLayout.setContentsMargins(8, 4, 8, 4)
        rootLayout.setSpacing(0)

        self._bubble = QFrame(self)
        self._bubble.setObjectName("bubbleBody")
        self._bubble.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bodyLayout = QVBoxLayout(self._bubble)
        bodyLayout.setContentsMargins(12, 6, 12, 6)
        self._content = MarkdownView("", self._bubble)
        bodyLayout.addWidget(self._content)

        rootLayout.addStretch(1)
        rootLayout.addWidget(self._bubble)
        rootLayout.addStretch(1)

    def applyMessage(self) -> None:
        self._content.setMarkdown(self._message.content)

    def appendDelta(self, delta: str) -> None:
        if not delta:
            return
        self._message.content = self._message.content + delta
        self._content.appendMarkdown(delta)

    def setContent(self, markdown: str) -> None:
        self._message.content = markdown
        self._content.setMarkdown(self._message.content)

    def setCodeBlockMaxVisibleLines(self, n: int) -> None:
        super().setCodeBlockMaxVisibleLines(n)
        self._content.setCodeBlockMaxVisibleLines(self._codeMaxVisibleLines)
