# coding: utf-8
"""权限审批 Dock (PermissionDock)

当 Agent 需要执行某个工具且审批策略为 ASK 时, 在输入框上方弹出一张
审批面板, 用户可以快速做出决策而不需要滚动到消息流中的工具卡片.

视觉参考 opencode 的 ``SessionPermissionDock``:
- header: [⚠ 图标] "需要权限确认"
- content: 工具描述 + 匹配模式列表
- footer: [拒绝] [总是允许] [本次允许]

使用方式:
    dock = PermissionDock(parent)
    dock.setRequest(
        tool_name="bash",
        description="执行 shell 命令: rm -rf /tmp/cache",
        patterns=["rm *", "sudo *"],
    )
    dock.approved.connect(lambda: ...)
    dock.rejected.connect(lambda: ...)
    dock.alwaysAllowed.connect(lambda: ...)
    dock.show()
"""

from typing import List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..button import PrimaryPushButton, PushButton
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from .dock_surface import DockSurface


__all__ = ['PermissionDock']


class PermissionDock(DockSurface):
    """权限审批 Dock.

    Signals:
        approved():       用户点击 [本次允许]
        rejected():       用户点击 [拒绝]
        alwaysAllowed():  用户点击 [总是允许]

    构造函数:
        PermissionDock(parent: QWidget = None)
    """

    approved = Signal()
    rejected = Signal()
    alwaysAllowed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        self._toolName = ""
        self._description = ""
        self._patterns: List[str] = []
        # 先初始化数据再调 super().__init__ (因为 _buildHeader/_buildContent 会用到)
        super().__init__(parent, collapsible=False)
        self.setObjectName("permissionDock")
        self.hide()  # 默认隐藏, 有请求时才 show

    # ------------------------------------------------------------------
    # 子类覆盖
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        return 40

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        # 警告图标
        self._warnIcon = QLabel(self._header)
        self._warnIcon.setObjectName("permissionWarnIcon")
        self._warnIcon.setFixedSize(16, 16)
        self._warnIcon.setPixmap(
            FluentIcon.INFO.icon().pixmap(QSize(16, 16))
        )

        # 标题
        self._titleLabel = StrongBodyLabel(self.tr("需要权限确认"), self._header)
        self._titleLabel.setObjectName("permissionTitle")

        layout.addWidget(self._warnIcon, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._titleLabel, 1, Qt.AlignmentFlag.AlignVCenter)

    def _buildContent(self, layout: QVBoxLayout) -> None:
        # 工具描述
        self._descLabel = BodyLabel("", self._content)
        self._descLabel.setObjectName("permissionDesc")
        self._descLabel.setWordWrap(True)
        layout.addWidget(self._descLabel)

        # 匹配模式列表容器
        self._patternsContainer = QWidget(self._content)
        self._patternsLayout = QVBoxLayout(self._patternsContainer)
        self._patternsLayout.setContentsMargins(0, 4, 0, 4)
        self._patternsLayout.setSpacing(2)
        self._patternsContainer.hide()
        layout.addWidget(self._patternsContainer)

        # 按钮行
        btnRow = QWidget(self._content)
        btnLayout = QHBoxLayout(btnRow)
        btnLayout.setContentsMargins(0, 8, 0, 0)
        btnLayout.setSpacing(8)

        self._rejectBtn = PushButton(
            FluentIcon.CANCEL, self.tr("拒绝"), btnRow,
        )
        self._rejectBtn.setFixedHeight(28)
        self._rejectBtn.clicked.connect(self._onReject)

        self._alwaysAllowBtn = PushButton(
            self.tr("总是允许"), btnRow,
        )
        self._alwaysAllowBtn.setFixedHeight(28)
        self._alwaysAllowBtn.setToolTip(
            self.tr("本次允许, 并将此工具设为始终允许")
        )
        self._alwaysAllowBtn.clicked.connect(self._onAlwaysAllow)

        self._approveBtn = PrimaryPushButton(
            FluentIcon.ACCEPT, self.tr("本次允许"), btnRow,
        )
        self._approveBtn.setFixedHeight(28)
        self._approveBtn.clicked.connect(self._onApprove)

        btnLayout.addStretch(1)
        btnLayout.addWidget(self._rejectBtn)
        btnLayout.addWidget(self._alwaysAllowBtn)
        btnLayout.addWidget(self._approveBtn)

        layout.addWidget(btnRow)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setRequest(self, tool_name: str, description: str = "",
                   patterns: Optional[List[str]] = None) -> None:
        """设置审批请求内容并显示.

        Args:
            tool_name:   工具名称 (如 "bash", "write_file")
            description: 工具调用描述 (如 "执行命令: rm -rf /tmp")
            patterns:    匹配模式列表 (如 ["rm *", "sudo *"])
        """
        self._toolName = tool_name
        self._description = description
        self._patterns = patterns or []

        self._titleLabel.setText(
            self.tr("需要权限确认: {tool}").format(tool=tool_name)
        )
        self._descLabel.setText(description)
        self._descLabel.setVisible(bool(description))

        # 重建 patterns 列表
        self._clearPatterns()
        if self._patterns:
            for p in self._patterns:
                lab = CaptionLabel(p, self._patternsContainer)
                lab.setObjectName("permissionPattern")
                lab.setWordWrap(False)
                self._patternsLayout.addWidget(lab)
            self._patternsContainer.show()
        else:
            self._patternsContainer.hide()

        self._setButtonsEnabled(True)
        self.show()

    def toolName(self) -> str:
        return self._toolName

    def description(self) -> str:
        return self._description

    def patterns(self) -> List[str]:
        return list(self._patterns)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _clearPatterns(self) -> None:
        while self._patternsLayout.count():
            item = self._patternsLayout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

    def _setButtonsEnabled(self, enabled: bool) -> None:
        self._approveBtn.setEnabled(enabled)
        self._rejectBtn.setEnabled(enabled)
        self._alwaysAllowBtn.setEnabled(enabled)

    def _onApprove(self) -> None:
        self._setButtonsEnabled(False)
        self.approved.emit()
        self.hide()

    def _onReject(self) -> None:
        self._setButtonsEnabled(False)
        self.rejected.emit()
        self.hide()

    def _onAlwaysAllow(self) -> None:
        self._setButtonsEnabled(False)
        self.alwaysAllowed.emit()
        self.hide()
