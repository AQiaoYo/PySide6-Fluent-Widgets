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

from PySide6.QtCore import QSize, Qt, QTimer, QElapsedTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QWidget

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..button import TransparentToolButton
from ..label import BodyLabel, CaptionLabel
from ..progress_ring import IndeterminateProgressRing


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

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("generationStatusBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._onTick)
        self._elapsed = QElapsedTimer()
        self._extraElapsedMs = 0  # 调用 setElapsedMs 时手动注入的偏置

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    def _setupUi(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(8)

        # spinner
        self._spinner = IndeterminateProgressRing(self, start=False)
        self._spinner.setFixedSize(self._SPINNER_SIZE, self._SPINNER_SIZE)
        self._spinner.setStrokeWidth(2)
        self._spinner.setTextVisible(False)

        # 主状态文本
        self._statusLabel = BodyLabel(self.tr("正在生成..."), self)
        self._statusLabel.setObjectName("generationStatusText")

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
        layout.addWidget(self._statusLabel, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._tokensLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._elapsedLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._stopBtn, 0, Qt.AlignmentFlag.AlignVCenter)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setStatusText(self, text: str) -> None:
        self._statusLabel.setText(text or "")

    def statusText(self) -> str:
        return self._statusLabel.text()

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
        """启动 spinner + 自动计时."""
        self._spinner.start()
        if not self._elapsed.isValid():
            self._elapsed.start()
        else:
            self._elapsed.restart()
        self._timer.start()

    def stop(self) -> None:
        """停止 spinner + 自动计时. 不重置显示."""
        self._spinner.stop()
        self._timer.stop()

    def reset(self) -> None:
        """还原为初始状态: 文本默认, token 隐藏, 计时归零."""
        self.stop()
        self._statusLabel.setText(self.tr("正在生成..."))
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
