# coding: utf-8
"""ChatBubble 操作栏 (复制 / 重新生成 / 编辑 / 删除).

USER 与 AGENT 角色都需要这条 bar; SYSTEM 角色直接 hide. 此前散落在
``ChatBubble._buildActionBar`` 里 ~80 行 + 鼠标 enter/leave 渐显逻辑 50
行, 现统一抽到这里, 给 ``UserBubbleBody`` / ``AgentBubbleBody`` 复用.

操作栏对外 4 个信号:
    copyClicked / editClicked / deleteClicked / regenerateClicked
都把 ``message_id`` 当 payload 一起 emit, 上层 ``ChatBubble`` 只是
re-emit 给 ``AgentChatView``.
"""

from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect, QHBoxLayout, QWidget,
)

from .....common.icon import FluentIcon
from ...button import TransparentToolButton
from ...tool_tip import ToolTipFilter, ToolTipPosition
from ..chat_message import ChatRole


__all__ = ['BubbleActionBar']


class BubbleActionBar(QWidget):
    """复制 / 重新生成 / 编辑 / 删除 四个 24x24 工具按钮.

    根据传入的 role 自动隐藏不适用的按钮:
        USER:  复制 + 编辑 + 删除 (隐藏 重新生成)
        AGENT: 复制 + 重新生成 + 删除 (隐藏 编辑); 重新生成 默认还多 hide
               一层, 由 ``setRegenerateEnabled(True)`` 才显示
        SYSTEM: 不该构造此 bar (调用方应直接跳过)

    可视化策略:
        默认始终可见 (跟 ChatGPT/Claude 一致). ``setActionsAlwaysVisible(False)``
        切换为 hover-fade 模式 — 鼠标进入父级 bubble 时淡入, 离开时淡出.
        切换 fade 模式时本类负责挂 / 卸 ``QGraphicsOpacityEffect``, 避免与
        FluentWindow 的 Mica 绘制 pipeline 冲突.

    Signals:
        copyClicked(str): 复制按钮点击, 带 message_id
        editClicked(str): 编辑按钮点击, 带 message_id
        deleteClicked(str): 删除按钮点击, 带 message_id
        regenerateClicked(str): 重新生成按钮点击, 带 message_id

    构造函数:
        BubbleActionBar(message_id, role, parent=None)
    """

    copyClicked = Signal(str)
    editClicked = Signal(str)
    deleteClicked = Signal(str)
    regenerateClicked = Signal(str)

    def __init__(self, message_id: str, role: ChatRole,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._messageId = message_id
        self._role = role

        self.setObjectName("actionBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._copyBtn = self._mkBtn(FluentIcon.COPY, self.tr("复制消息"))
        self._copyBtn.clicked.connect(
            lambda: self.copyClicked.emit(self._messageId)
        )

        self._regenerateBtn = self._mkBtn(FluentIcon.SYNC, self.tr("重新生成"))
        self._regenerateBtn.clicked.connect(
            lambda: self.regenerateClicked.emit(self._messageId)
        )
        # 默认隐藏: 由 AgentChatView.setRegenerateEnabled(True) 全局启用
        self._regenerateBtn.hide()

        self._editBtn = self._mkBtn(FluentIcon.EDIT, self.tr("编辑消息"))
        self._editBtn.clicked.connect(
            lambda: self.editClicked.emit(self._messageId)
        )

        self._deleteBtn = self._mkBtn(FluentIcon.DELETE, self.tr("删除消息"))
        self._deleteBtn.clicked.connect(
            lambda: self.deleteClicked.emit(self._messageId)
        )

        layout.addWidget(self._copyBtn)
        layout.addWidget(self._regenerateBtn)
        layout.addWidget(self._editBtn)
        layout.addWidget(self._deleteBtn)

        # 按角色策略隐藏
        if role == ChatRole.AGENT:
            self._editBtn.hide()
        elif role == ChatRole.USER:
            self._regenerateBtn.hide()

        # 渐显效果 (懒加载, 默认 always-visible)
        self._effect: Optional[QGraphicsOpacityEffect] = None
        self._fadeAni: Optional[QPropertyAnimation] = None
        self._alwaysVisible = True

    # ------------------------------------------------------------------
    # 按钮工厂
    # ------------------------------------------------------------------

    def _mkBtn(self, icon: FluentIcon, tip: str) -> TransparentToolButton:
        btn = TransparentToolButton(icon, self)
        btn.setFixedSize(24, 24)
        btn.setIconSize(QSize(14, 14))
        btn.setToolTip(tip)
        btn.installEventFilter(
            ToolTipFilter(btn, showDelay=300, position=ToolTipPosition.TOP)
        )
        return btn

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def editButton(self) -> TransparentToolButton:
        """返回 编辑 按钮 (供 USER 气泡额外接 inline editor 触发).

        UserBubbleBody 需要在编辑按钮被点击时除了 emit ``editClicked``
        还要主动进入内联编辑模式, 因此需要拿到这个按钮挂额外 slot.
        """
        return self._editBtn

    def setRegenerateEnabled(self, enabled: bool) -> None:
        """控制 重新生成 按钮可见性 (仅 AGENT 有效)."""
        if self._role != ChatRole.AGENT:
            return
        self._regenerateBtn.setVisible(bool(enabled))

    def isRegenerateEnabled(self) -> bool:
        if self._role != ChatRole.AGENT:
            return False
        return not self._regenerateBtn.isHidden()

    def setAlwaysVisible(self, always: bool) -> None:
        """切换 always-visible / hover-fade 模式.

        always=True:  卸下 GraphicsEffect, 默认 paint 路径, 操作栏始终 1.0 透明度
        always=False: 挂 GraphicsEffect 并立即 setOpacity(0.0), 等待 hover 唤起
        """
        always = bool(always)
        self._alwaysVisible = always
        if always:
            self._detachEffect()
        else:
            effect = self._ensureEffect()
            self._fadeAni.stop()
            effect.setOpacity(0.0)

    def alwaysVisible(self) -> bool:
        return self._alwaysVisible

    def fadeIn(self) -> None:
        """鼠标进入父级时调用; 仅 hover-fade 模式生效."""
        if self._alwaysVisible:
            return
        effect = self._ensureEffect()
        self._fadeAni.stop()
        self._fadeAni.setStartValue(effect.opacity())
        self._fadeAni.setEndValue(1.0)
        self._fadeAni.start()

    def fadeOut(self) -> None:
        """鼠标离开父级时调用; 仅 hover-fade 模式生效."""
        if self._alwaysVisible:
            return
        effect = self._ensureEffect()
        self._fadeAni.stop()
        self._fadeAni.setStartValue(effect.opacity())
        self._fadeAni.setEndValue(0.0)
        self._fadeAni.start()

    # ------------------------------------------------------------------
    # 内部: GraphicsEffect 懒加载 / 卸载
    # ------------------------------------------------------------------

    def _ensureEffect(self) -> QGraphicsOpacityEffect:
        if self._effect is None:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(0.0)
            self.setGraphicsEffect(effect)
            self._effect = effect
            self._fadeAni = QPropertyAnimation(effect, b"opacity", self)
            self._fadeAni.setDuration(150)
        return self._effect

    def _detachEffect(self) -> None:
        if self._fadeAni is not None:
            self._fadeAni.stop()
            self._fadeAni.deleteLater()
            self._fadeAni = None
        if self._effect is not None:
            self.setGraphicsEffect(None)
            self._effect = None
