# coding: utf-8
"""生成状态条 (Generation Status Bar)

显示在 ``AgentChatView`` 顶部 (浮动覆盖在 viewport 上, 不参与滚动) 的
状态条, 用于在 LLM 流式生成期间向用户展示:

- 旋转 spinner
- 主状态文本 (如 ``正在调用 read_file...``)
- 累计 token 数 + token / 秒 速率
- 生成耗时计时
- Stop 按钮 (用户主动取消)

公共 API:
    setStatusText(text)          -- 主状态文本
    setTokens(total, rate=None)  -- 累计 token + 可选 rate (tok/s)
    setElapsedMs(ms)             -- 计时显示 (ms 也接受)
    start() / stop()             -- spinner + 自动计时
    reset()                      -- 把所有显示还原到初始

信号:
    stopRequested(): Stop 按钮被点击
"""

from typing import Optional

from PySide6.QtCore import (
    QEasingCurve, QElapsedTimer, QPropertyAnimation, QSize, Qt, QTimer, Signal,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QWidget

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..button import TransparentToolButton
from ..label import BodyLabel, CaptionLabel
from ..progress_ring import IndeterminateProgressRing
from ._collapse_anim import animations_enabled_root
from .inline_spinner import InlineSpinner
from .text_shimmer import TextShimmer


__all__ = ['GenerationStatusBar']


def _format_elapsed(ms: int) -> str:
    """把毫秒格式化为 ``mm:ss`` (最多到 99:59) 或 ``hh:mm:ss``."""
    if ms < 0:
        ms = 0
    seconds = ms // 1000
    if seconds < 3600:
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _format_tokens(total: int, rate: Optional[float]) -> str:
    """token 数 + 可选 rate. 无 rate 时只显示 ``N tokens``."""
    parts = []
    if total >= 1000:
        parts.append(f"{total / 1000:.1f}k tokens")
    else:
        parts.append(f"{total} tokens")
    if rate is not None:
        parts.append(f"{rate:.1f} tok/s")
    return " · ".join(parts)


class GenerationStatusBar(QFrame):
    """生成状态条.

    构造函数:
        GenerationStatusBar(parent: QWidget = None)
    """

    stopRequested = Signal()

    _HEIGHT = 32
    _SPINNER_SIZE = 14
    # 进入 / 退出动画时长 (默认 200ms, 比卡片展开 220 略快)
    _ENTER_EXIT_ANIM_MS = 200

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("generationStatusBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 不再走 setFixedHeight, 改为 min == max == _HEIGHT 等价设置.
        # 进入 / 退出动画要动画 maximumHeight 从 0 -> _HEIGHT (反之),
        # 需要临时 setMinimumHeight(0) 释放锁死. 如果走 setFixedHeight
        # minimumHeight 会被锁在 _HEIGHT, 动画走不下去.
        self.setMinimumHeight(self._HEIGHT)
        self.setMaximumHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._onTick)
        self._elapsed = QElapsedTimer()
        self._extraElapsedMs = 0  # 调用 setElapsedMs 时手动注入的偏置

        # 进入 / 退出 高度动画状态
        self._enterExitAnim: Optional[QPropertyAnimation] = None
        self._enterExitAnimEnabled: bool = True

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    def _setupUi(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(8)

        # spinner
        self._spinner = InlineSpinner(self._SPINNER_SIZE, self, start=False)

        # 主状态文本 (带 shimmer 效果)
        self._statusShimmer = TextShimmer(self.tr("正在生成..."), self)
        self._statusShimmer.setObjectName("generationStatusText")
        self._statusShimmer.setFixedHeight(20)
        # 保留 _statusLabel 引用兼容现有 API
        self._statusLabel = self._statusShimmer

        # token 信息
        self._tokensLabel = CaptionLabel("", self)
        self._tokensLabel.setObjectName("generationStatusTokens")
        self._tokensLabel.hide()

        # 计时
        self._elapsedLabel = CaptionLabel("00:00", self)
        self._elapsedLabel.setObjectName("generationStatusElapsed")

        # Stop 按钮
        self._stopBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self._stopBtn.setFixedSize(24, 24)
        self._stopBtn.setIconSize(QSize(12, 12))
        self._stopBtn.setToolTip(self.tr("停止生成"))
        self._stopBtn.clicked.connect(self.stopRequested)

        layout.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._statusShimmer, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._tokensLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._elapsedLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._stopBtn, 0, Qt.AlignmentFlag.AlignVCenter)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setStatusText(self, text: str) -> None:
        self._statusShimmer.setText(text or "")

    def statusText(self) -> str:
        return self._statusShimmer.text()

    def setTokens(self, total: int,
                  rate: Optional[float] = None) -> None:
        """更新 token 数与可选速率. ``total`` < 0 隐藏 token 显示."""
        if total is None or total < 0:
            self._tokensLabel.hide()
            return
        self._tokensLabel.setText(_format_tokens(int(total), rate))
        self._tokensLabel.show()

    def setElapsedMs(self, ms: int) -> None:
        """显式设置计时显示 (注入新基线; 仍由内部 timer 自驱继续累加)."""
        ms = max(0, int(ms))
        self._extraElapsedMs = ms
        if self._elapsed.isValid():
            self._elapsed.restart()
        self._elapsedLabel.setText(_format_elapsed(ms))

    def setStopButtonVisible(self, visible: bool) -> None:
        self._stopBtn.setVisible(bool(visible))

    def start(self) -> None:
        """启动 spinner + shimmer + 自动计时."""
        self._spinner.start()
        self._statusShimmer.start()
        if not self._elapsed.isValid():
            self._elapsed.start()
        else:
            self._elapsed.restart()
        self._timer.start()

    def stop(self) -> None:
        """停止 spinner + shimmer + 自动计时. 不重置显示."""
        self._spinner.stop()
        self._statusShimmer.stop()
        self._timer.stop()

    def reset(self) -> None:
        """还原为初始状态: 文本默认, token 隐藏, 计时归零."""
        self.stop()
        self._statusShimmer.setText(self.tr("正在生成..."))
        self._tokensLabel.hide()
        self._tokensLabel.setText("")
        self._elapsedLabel.setText("00:00")
        self._extraElapsedMs = 0
        self._elapsed.invalidate()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _onTick(self) -> None:
        if not self._elapsed.isValid():
            return
        total_ms = self._extraElapsedMs + self._elapsed.elapsed()
        self._elapsedLabel.setText(_format_elapsed(total_ms))

    # ------------------------------------------------------------------
    # 进入 / 退出 高度动画 (Override show / hide)
    # ------------------------------------------------------------------

    def setEnterExitAnimationEnabled(self, enabled: bool) -> None:
        """设置进入 / 退出动画是否启用 (默认 ``True``).

        关闭后 ``show()`` / ``hide()`` 退化为原生瞬间路径, 与本期改造
        前行为等价.
        """
        self._enterExitAnimEnabled = bool(enabled)

    def enterExitAnimationEnabled(self) -> bool:
        return self._enterExitAnimEnabled

    def _shouldAnimateEnterExit(self) -> bool:
        """本卡开关 + 宿主总开关 决定是否走动画."""
        if not self._enterExitAnimEnabled:
            return False
        if not animations_enabled_root(self):
            return False
        return True

    def show(self) -> None:
        """进入路径: 如果当前 hidden 走高度展开动画 (0 -> _HEIGHT, 200ms OutCubic).

        已经 visible 时 (包含出场动画中依然是 visible) 不重启进入动画,
        仅取消出场动画并锁回 _HEIGHT.
        """
        # 出场动画进行中被 show: 取消出场 + 锁回高度.
        if (self._enterExitAnim is not None
                and self._enterExitAnim.state() == QPropertyAnimation.State.Running):
            self._enterExitAnim.stop()
            self._lockHeight()
            super().show()
            return

        if self.isVisible():
            super().show()
            return
        if not self._shouldAnimateEnterExit():
            super().show()
            return

        # 进入动画: 先 super().show() 让 widget 进入 visible 状态, 为 0 高度
        # 看不见; 然后动画 0 -> _HEIGHT.
        self.setMinimumHeight(0)
        self.setMaximumHeight(0)
        super().show()
        self._animateEnter()

    def hide(self) -> None:
        """退出路径: 如果当前 visible 走高度收缩动画 (current -> 0, 200ms OutCubic),
        finished 后才真正 ``QFrame.hide`` widget.

        已经 hidden 不重启退出动画.
        """
        # 进入动画中被 hide: 作为反转, 取消进入 + 启动出场.
        if (self._enterExitAnim is not None
                and self._enterExitAnim.state() == QPropertyAnimation.State.Running):
            self._enterExitAnim.stop()

        if not self.isVisible():
            super().hide()
            return
        if not self._shouldAnimateEnterExit():
            super().hide()
            return
        self._animateExit()

    def _animateEnter(self) -> None:
        anim = QPropertyAnimation(self, b"maximumHeight", self)
        anim.setDuration(self._ENTER_EXIT_ANIM_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(0)
        anim.setEndValue(self._HEIGHT)
        anim.finished.connect(self._lockHeight)
        self._enterExitAnim = anim
        anim.start()

    def _animateExit(self) -> None:
        # 需要先放开 minimumHeight 才能动到 0
        self.setMinimumHeight(0)
        start_h = self.height() or self._HEIGHT
        anim = QPropertyAnimation(self, b"maximumHeight", self)
        anim.setDuration(self._ENTER_EXIT_ANIM_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(start_h)
        anim.setEndValue(0)
        anim.finished.connect(self._onExitFinished)
        self._enterExitAnim = anim
        anim.start()

    def _lockHeight(self) -> None:
        """进入动画 finished: 锁回 _HEIGHT 让 widget 保持固定高度."""
        self.setMinimumHeight(self._HEIGHT)
        self.setMaximumHeight(self._HEIGHT)

    def _onExitFinished(self) -> None:
        """退出动画 finished: 真正隐藏 widget + 锁回 _HEIGHT (下次 show 时默认高度正确)."""
        # 字面调 QFrame.hide 代替 super().hide() 让代码 避免走本类 override
        # 重新启动出场动画限制为递归.
        QFrame.hide(self)
        self.setMinimumHeight(self._HEIGHT)
        self.setMaximumHeight(self._HEIGHT)
