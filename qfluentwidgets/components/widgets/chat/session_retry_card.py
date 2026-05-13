# coding: utf-8
"""重试倒计时卡片 (SessionRetryCard)

当 LLM 请求遇到 429 / 超时 / 临时错误需要自动重试时, 在消息流中显示一张
小卡片, 告知用户:

- 错误原因摘要
- 当前第几次重试
- 距下次重试的倒计时秒数 (自动递减)

视觉参考 opencode 的 ``session-retry`` 组件:
- 浅红/浅橙背景卡片 (error variant)
- 左侧 spinner + 右侧文字
- 倒计时实时更新

使用方式:
    card = SessionRetryCard(parent)
    card.setRetryInfo(message="Rate limit exceeded", attempt=2, next_retry_ms=18000)
    # 倒计时自动递减; 重试成功后:
    card.hide()  # 或 card.deleteLater()
"""

from typing import Optional

from PySide6.QtCore import QElapsedTimer, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..label import BodyLabel, CaptionLabel
from ..progress_ring import IndeterminateProgressRing


__all__ = ['SessionRetryCard']


class SessionRetryCard(QFrame):
    """重试倒计时卡片.

    Signals:
        expired(): 倒计时归零时发出 (表示应该开始重试了)

    构造函数:
        SessionRetryCard(parent: QWidget = None)
    """

    expired = Signal()

    _HEIGHT = 48
    _SPINNER_SIZE = 14
    _MAX_MESSAGE_LEN = 80

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sessionRetryCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed,
        )
        self.setFixedHeight(self._HEIGHT)

        self._message = ""
        self._attempt = 0
        self._remainingMs = 0

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._onTick)
        self._elapsed = QElapsedTimer()

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # spinner
        self._spinner = IndeterminateProgressRing(self, start=False)
        self._spinner.setFixedSize(self._SPINNER_SIZE, self._SPINNER_SIZE)
        self._spinner.setStrokeWidth(2)
        self._spinner.setTextVisible(False)

        # 文字区
        textContainer = QWidget(self)
        textLayout = QVBoxLayout(textContainer)
        textLayout.setContentsMargins(0, 0, 0, 0)
        textLayout.setSpacing(2)

        self._messageLabel = BodyLabel("", textContainer)
        self._messageLabel.setObjectName("retryMessage")
        self._messageLabel.setWordWrap(False)

        self._infoLabel = CaptionLabel("", textContainer)
        self._infoLabel.setObjectName("retryInfo")

        textLayout.addWidget(self._messageLabel)
        textLayout.addWidget(self._infoLabel)

        layout.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(textContainer, 1, Qt.AlignmentFlag.AlignVCenter)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setRetryInfo(self, message: str, attempt: int = 1,
                     next_retry_ms: int = 0) -> None:
        """设置重试信息并启动倒计时.

        Args:
            message:       错误原因摘要 (超过 80 字符会截断)
            attempt:       当前第几次重试 (从 1 开始)
            next_retry_ms: 距下次重试的毫秒数 (0 表示立即重试, 不显示倒计时)
        """
        self._message = message
        self._attempt = max(1, attempt)
        self._remainingMs = max(0, next_retry_ms)

        # 截断过长消息
        display_msg = message
        if len(display_msg) > self._MAX_MESSAGE_LEN:
            display_msg = display_msg[:self._MAX_MESSAGE_LEN] + "..."
            self._messageLabel.setToolTip(message)
        else:
            self._messageLabel.setToolTip("")
        self._messageLabel.setText(display_msg)

        self._refreshInfo()
        self._startCountdown()
        self.show()

    def attempt(self) -> int:
        return self._attempt

    def message(self) -> str:
        return self._message

    def remainingSeconds(self) -> int:
        return max(0, self._remainingMs // 1000)

    def stop(self) -> None:
        """停止倒计时 (重试成功后调用)."""
        self._timer.stop()
        self._spinner.stop()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _startCountdown(self) -> None:
        self._spinner.start()
        if self._remainingMs > 0:
            self._elapsed.start()
            self._timer.start()
        else:
            self._timer.stop()

    def _onTick(self) -> None:
        elapsed = self._elapsed.elapsed()
        remaining = max(0, self._remainingMs - int(elapsed))
        if remaining <= 0:
            self._timer.stop()
            self._remainingMs = 0
            self._refreshInfo()
            self.expired.emit()
            return
        self._refreshInfo()

    def _refreshInfo(self) -> None:
        elapsed = 0
        if self._elapsed.isValid() and self._timer.isActive():
            elapsed = self._elapsed.elapsed()
        remaining_s = max(0, (self._remainingMs - int(elapsed)) // 1000)

        parts = []
        parts.append(self.tr("正在重试"))
        if remaining_s > 0:
            parts.append(self.tr("{seconds} 秒后").format(seconds=remaining_s))
        attempt_text = self.tr("第 {n} 次尝试").format(n=self._attempt)
        info = " ".join(parts) + f" · {attempt_text}"
        self._infoLabel.setText(info)
