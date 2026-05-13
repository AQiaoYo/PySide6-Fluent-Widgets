# coding: utf-8
"""工具错误详情卡片 (ToolErrorCard)

当工具调用失败时, 在消息流中显示一张可折叠的错误详情卡片:

- 折叠态: [⊘ 图标] [工具名] [错误摘要]  [▶]
- 展开态: header + 下方完整错误文本 (可选择 + 一键复制)

视觉参考 opencode 的 ``tool-error-card`` 组件:
- 浅红边框 / 背景 (error variant)
- 折叠式 header: 图标 + 工具名 + 摘要
- 展开后显示完整错误文本 + 复制按钮

与 ``ToolCallCardBase`` 的 ERROR 状态区别:
- ToolCallCardBase 是完整的工具调用卡片 (含参数/结果), ERROR 只是其中一种状态
- ToolErrorCard 是独立的轻量错误展示卡片, 不含参数/结果, 只聚焦错误信息

使用方式:
    card = ToolErrorCard(parent)
    card.setError(tool_name="read_file", error="FileNotFoundError: /foo/bar.py")
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from .._clickable import ClickableFrame
from ..button import TransparentToolButton
from ..label import BodyLabel, CaptionLabel


__all__ = ['ToolErrorCard']


class ToolErrorCard(QFrame):
    """工具错误详情卡片.

    Signals:
        copied(str): 用户点击复制按钮后发出, 参数为错误文本

    构造函数:
        ToolErrorCard(parent: QWidget = None)
    """

    copied = Signal(str)

    _ICON_SIZE = 14
    _CHEVRON_SIZE = 12
    _COPY_FEEDBACK_MS = 1200

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("toolErrorCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        self._toolName = ""
        self._errorText = ""
        self._expanded = False

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header (可点击) ----
        self._header = ClickableFrame(self)
        self._header.setObjectName("toolErrorHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(36)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(12, 0, 12, 0)
        headerLayout.setSpacing(8)

        # 错误图标
        self._iconLabel = QLabel(self._header)
        self._iconLabel.setObjectName("toolErrorIcon")
        self._iconLabel.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
        self._iconLabel.setPixmap(
            FluentIcon.CANCEL.icon().pixmap(
                QSize(self._ICON_SIZE, self._ICON_SIZE)
            )
        )

        # 工具名
        self._nameLabel = BodyLabel("", self._header)
        self._nameLabel.setObjectName("toolErrorName")

        # 错误摘要 (单行截断)
        self._summaryLabel = CaptionLabel("", self._header)
        self._summaryLabel.setObjectName("toolErrorSummary")
        self._summaryLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        # 展开箭头
        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setObjectName("toolErrorChevron")
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)

        headerLayout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._nameLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._summaryLabel, 1, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- content (可折叠) ----
        self._content = QFrame(self)
        self._content.setObjectName("toolErrorContent")
        self._content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        contentLayout = QVBoxLayout(self._content)
        contentLayout.setContentsMargins(12, 8, 12, 10)
        contentLayout.setSpacing(6)

        # 复制按钮行
        copyRow = QHBoxLayout()
        copyRow.setContentsMargins(0, 0, 0, 0)
        copyRow.addStretch(1)
        self._copyBtn = TransparentToolButton(FluentIcon.COPY, self._content)
        self._copyBtn.setFixedSize(24, 24)
        self._copyBtn.setIconSize(QSize(14, 14))
        self._copyBtn.setToolTip(self.tr("复制错误信息"))
        self._copyBtn.clicked.connect(self._onCopyClicked)
        copyRow.addWidget(self._copyBtn)
        contentLayout.addLayout(copyRow)

        # 错误详情文本
        self._detailLabel = BodyLabel("", self._content)
        self._detailLabel.setObjectName("toolErrorDetail")
        self._detailLabel.setWordWrap(True)
        self._detailLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        contentLayout.addWidget(self._detailLabel)

        self._content.hide()

        rootLayout.addWidget(self._header)
        rootLayout.addWidget(self._content)

        self._updateChevron()

        # 复制反馈 timer
        self._copyResetTimer = QTimer(self)
        self._copyResetTimer.setSingleShot(True)
        self._copyResetTimer.timeout.connect(self._resetCopyIcon)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setError(self, tool_name: str, error: str,
                 subtitle: Optional[str] = None) -> None:
        """设置错误信息.

        Args:
            tool_name: 工具名称 (如 "read_file", "bash")
            error:     完整错误文本
            subtitle:  可选的摘要覆盖 (默认从 error 首行提取)
        """
        self._toolName = tool_name
        self._errorText = error

        self._nameLabel.setText(tool_name)
        self._detailLabel.setText(error)

        # 提取摘要
        if subtitle:
            summary = subtitle
        else:
            # 取 error 首行, 去掉 "Error: " 前缀
            first_line = error.split("\n", 1)[0].strip()
            if first_line.startswith("Error:"):
                first_line = first_line[6:].strip()
            summary = first_line
        self._summaryLabel.setText(summary)

    def toolName(self) -> str:
        return self._toolName

    def errorText(self) -> str:
        return self._errorText

    def toggle(self) -> None:
        self.setExpanded(not self._expanded)

    def setExpanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = bool(expanded)
        self._content.setVisible(self._expanded)
        self._updateChevron()

    def isExpanded(self) -> bool:
        return self._expanded

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _updateChevron(self) -> None:
        icon = (
            FluentIcon.CHEVRON_DOWN_MED if self._expanded
            else FluentIcon.CHEVRON_RIGHT_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )

    def _onCopyClicked(self) -> None:
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(self._errorText)
        self._copyBtn.setIcon(FluentIcon.ACCEPT)
        self._copyResetTimer.start(self._COPY_FEEDBACK_MS)
        self.copied.emit(self._errorText)

    def _resetCopyIcon(self) -> None:
        self._copyBtn.setIcon(FluentIcon.COPY)
