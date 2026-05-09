# coding: utf-8
"""``AgentChatView`` 的生成控制子领域 (extracted in cleanup phase).

把 "当前正在生成的 message id + 顶部 ``GenerationStatusBar`` 的 lazy 创建
+ 注入 + begin/set/end 时机" 这一组 ~140 行逻辑从主类抽出来, 让
``AgentChatView`` 不再在自己 1000+ 行里塞这些细节.

使用方式 (composition, 不是 mixin):

    class AgentChatView:
        def __init__(self, ...):
            ...
            self._generation = _GenerationController(self)

        def beginGeneration(self, msg_id, status_text=None):
            self._generation.begin(msg_id, status_text)
        ...

控制器持有对 view 的反向引用, 用于:

* ``view.viewport()`` 给 lazy 创建的默认 bar 当 parent
* ``view.stopRequested.emit(...)`` 转发 Stop 按钮事件
* ``view._bubbles`` (在 ``end(stopped=True)`` 时给目标 bubble markStopped)

不持有任何 Qt widget 状态以外的"业务"知识 (审批 / 分叉 / 滚动 等不归本类管).
"""

from typing import TYPE_CHECKING, Optional

from .generation_status_bar import GenerationStatusBar


if TYPE_CHECKING:  # pragma: no cover - 只为类型注释
    from .agent_chat_view import AgentChatView


__all__ = ['_GenerationController']


class _GenerationController:
    """生成状态子系统.

    维护:
        * ``_currentGeneratingMsgId``: 当前流式中的 AGENT 消息 id (None 表示未生成)
        * ``_bar``: ``GenerationStatusBar`` 实例 (lazy 创建 / 可被宿主 ``setStatusBar`` 注入)

    公共方法:
        begin / setStatus / setTokens / end / isGenerating / currentGeneratingMessageId
        statusBar / setStatusBar / positionBar
    """

    def __init__(self, view: 'AgentChatView'):
        self._view = view
        self._currentGeneratingMsgId: Optional[str] = None
        self._bar: Optional[GenerationStatusBar] = None

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    @property
    def currentMessageId(self) -> Optional[str]:
        return self._currentGeneratingMsgId

    @property
    def isGenerating(self) -> bool:
        return self._currentGeneratingMsgId is not None

    @property
    def bar(self) -> Optional[GenerationStatusBar]:
        """返回当前 bar (None 表示尚未 lazy 创建也未注入)."""
        return self._bar

    # ------------------------------------------------------------------
    # bar 管理: lazy 创建 / 注入
    # ------------------------------------------------------------------

    def statusBar(self) -> GenerationStatusBar:
        """返回 (必要时 lazy 创建) 生成状态条.

        默认 parent = ``view.viewport()``, 浮动在消息区顶部. 宿主侧若希望
        状态条嵌在自己的布局里, 应该自己创建 bar 后调 ``setStatusBar(bar)``
        注入, 不要 reparent 这一份.
        """
        if self._bar is None:
            self._bar = GenerationStatusBar(self._view.viewport())
            self._bar.hide()
            self._bar.stopRequested.connect(self._onStop)
        return self._bar

    def setStatusBar(self, bar: GenerationStatusBar) -> None:
        """注入外部创建的 ``GenerationStatusBar`` 替换 lazy bar.

        Args:
            bar: 已经构造好且 parent 设妥的 bar; 不能为 None.
        """
        if bar is None:
            raise ValueError("setStatusBar(bar) 不接受 None")
        if self._bar is bar:
            return
        if self._bar is not None:
            try:
                self._bar.stopRequested.disconnect(self._onStop)
            except (RuntimeError, TypeError):
                pass
        self._bar = bar
        self._bar.stopRequested.connect(self._onStop)

    def _onStop(self) -> None:
        """Bar 的 Stop 按钮 点击 -> view.stopRequested(msg_id)."""
        if self._currentGeneratingMsgId is not None:
            self._view.stopRequested.emit(self._currentGeneratingMsgId)

    # ------------------------------------------------------------------
    # 生命周期: begin / set* / end
    # ------------------------------------------------------------------

    def begin(self, message_id: str,
              status_text: Optional[str] = None) -> None:
        """开始一次生成: 显示状态条 + spinner + 计时. 同时 ``positionBar``."""
        self._currentGeneratingMsgId = message_id
        bar = self.statusBar()
        bar.reset()
        if status_text:
            bar.setStatusText(status_text)
        bar.start()
        bar.show()
        self.positionBar()

    def setStatus(self, message_id: str, text: str) -> None:
        if message_id == self._currentGeneratingMsgId and self._bar is not None:
            self._bar.setStatusText(text)

    def setTokens(self, message_id: str, total: int,
                  rate: Optional[float] = None) -> None:
        if message_id == self._currentGeneratingMsgId and self._bar is not None:
            self._bar.setTokens(total, rate)

    def end(self, message_id: str, stopped: bool = False) -> None:
        """结束流式: 隐藏 bar; ``stopped=True`` 时给 bubble 加 [继续生成] 行."""
        if message_id != self._currentGeneratingMsgId:
            return
        if self._bar is not None:
            self._bar.stop()
            self._bar.hide()
        self._currentGeneratingMsgId = None
        if stopped:
            bubble = self._view._bubbles.get(message_id)
            if bubble is not None:
                bubble.markStopped(True)

    # ------------------------------------------------------------------
    # 位置 (仅当 bar 还在 viewport 浮动模式下生效; 注入式 bar 由宿主 layout)
    # ------------------------------------------------------------------

    def positionBar(self) -> None:
        if self._bar is None or not self._bar.isVisible():
            return
        if self._bar.parent() is not self._view.viewport():
            # 注入模式: 宿主自己负责 layout
            return
        h = self._bar.height()
        vp = self._view.viewport()
        self._bar.setGeometry(0, 0, vp.width(), h)
        self._bar.raise_()
