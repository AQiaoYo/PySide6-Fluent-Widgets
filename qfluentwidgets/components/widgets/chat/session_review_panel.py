# coding: utf-8
"""多文件 diff 汇总审阅面板 (SessionReviewPanel)

将一个 turn 中 agent 产生的多文件变更汇总到一个可折叠的审阅面板中.
每个文件一个 Accordion 项, 展开后显示 DiffView.

视觉参考 opencode 的 ``session-review`` 组件:
- 顶部统计: "3 files changed, +42 -18"
- 文件列表: 每项 [文件图标] [文件名] [+N -M]  可折叠
- 展开后: DiffView (unified diff)

使用方式:
    panel = SessionReviewPanel(parent)
    panel.addFileDiff("src/main.py", unified_diff_text, additions=10, deletions=3)
    panel.addFileDiff("src/utils.py", unified_diff_text, additions=5, deletions=2)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from .._clickable import ClickableFrame
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from .diff_view import DiffView


__all__ = ['SessionReviewPanel']


@dataclass
class _FileDiffEntry:
    """内部数据: 一个文件的 diff 信息."""
    file_path: str
    diff_text: str
    additions: int = 0
    deletions: int = 0


class _FileAccordionItem(QFrame):
    """单个文件的可折叠 diff 项."""

    _CHEVRON_SIZE = 12

    def __init__(self, entry: _FileDiffEntry, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("reviewFileItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        self._entry = entry
        self._expanded = False

        self._setupUi()

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header ----
        self._header = ClickableFrame(self)
        self._header.setObjectName("reviewFileHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(32)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(10, 0, 10, 0)
        headerLayout.setSpacing(6)

        # chevron
        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setObjectName("reviewFileChevron")
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)

        # 文件名
        self._fileLabel = BodyLabel(self._entry.file_path, self._header)
        self._fileLabel.setObjectName("reviewFileName")
        self._fileLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        # 增删统计
        stats_parts = []
        if self._entry.additions > 0:
            stats_parts.append(f"+{self._entry.additions}")
        if self._entry.deletions > 0:
            stats_parts.append(f"-{self._entry.deletions}")
        stats_text = " ".join(stats_parts) if stats_parts else ""

        self._statsLabel = CaptionLabel(stats_text, self._header)
        self._statsLabel.setObjectName("reviewFileStats")

        headerLayout.addWidget(self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._fileLabel, 1, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._statsLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- content: DiffView ----
        self._content = QFrame(self)
        self._content.setObjectName("reviewFileContent")
        contentLayout = QVBoxLayout(self._content)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)

        self._diffView = DiffView(self._content)
        if self._entry.diff_text:
            self._diffView.setUnifiedDiff(self._entry.diff_text)
        contentLayout.addWidget(self._diffView)

        self._content.hide()

        rootLayout.addWidget(self._header)
        rootLayout.addWidget(self._content)

        self._updateChevron()

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

    def entry(self) -> _FileDiffEntry:
        return self._entry

    def _updateChevron(self) -> None:
        icon = (
            FluentIcon.CHEVRON_DOWN_MED if self._expanded
            else FluentIcon.CHEVRON_RIGHT_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )


class SessionReviewPanel(QFrame):
    """多文件 diff 汇总审阅面板.

    Signals:
        fileClicked(str): 用户点击某个文件 header 时发出, 参数为文件路径

    构造函数:
        SessionReviewPanel(parent: QWidget = None)
    """

    fileClicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sessionReviewPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
        )

        self._entries: List[_FileDiffEntry] = []
        self._items: List[_FileAccordionItem] = []

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- 顶部统计栏 ----
        self._statsBar = QFrame(self)
        self._statsBar.setObjectName("reviewStatsBar")
        self._statsBar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._statsBar.setFixedHeight(36)

        statsLayout = QHBoxLayout(self._statsBar)
        statsLayout.setContentsMargins(12, 0, 12, 0)
        statsLayout.setSpacing(8)

        self._summaryLabel = StrongBodyLabel("", self._statsBar)
        self._summaryLabel.setObjectName("reviewSummary")

        self._totalStatsLabel = CaptionLabel("", self._statsBar)
        self._totalStatsLabel.setObjectName("reviewTotalStats")

        statsLayout.addWidget(self._summaryLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        statsLayout.addStretch(1)
        statsLayout.addWidget(self._totalStatsLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- 文件列表 (可滚动) ----
        self._scrollArea = QScrollArea(self)
        self._scrollArea.setObjectName("reviewScrollArea")
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self._scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._listContainer = QWidget(self._scrollArea)
        self._listLayout = QVBoxLayout(self._listContainer)
        self._listLayout.setContentsMargins(0, 0, 0, 0)
        self._listLayout.setSpacing(1)
        self._listLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scrollArea.setWidget(self._listContainer)

        rootLayout.addWidget(self._statsBar)
        rootLayout.addWidget(self._scrollArea, 1)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addFileDiff(self, file_path: str, diff_text: str,
                    additions: int = 0, deletions: int = 0) -> None:
        """添加一个文件的 diff.

        Args:
            file_path:  文件路径 (如 "src/main.py")
            diff_text:  unified diff 文本
            additions:  新增行数
            deletions:  删除行数
        """
        entry = _FileDiffEntry(
            file_path=file_path,
            diff_text=diff_text,
            additions=additions,
            deletions=deletions,
        )
        self._entries.append(entry)

        item = _FileAccordionItem(entry, self._listContainer)
        self._items.append(item)
        self._listLayout.addWidget(item)

        self._refreshStats()

    def removeFileDiff(self, file_path: str) -> None:
        """移除一个文件的 diff."""
        for i, entry in enumerate(self._entries):
            if entry.file_path == file_path:
                item = self._items[i]
                self._listLayout.removeWidget(item)
                item.setParent(None)
                item.deleteLater()
                self._entries.pop(i)
                self._items.pop(i)
                self._refreshStats()
                return

    def clear(self) -> None:
        """清空所有文件 diff."""
        for item in self._items:
            self._listLayout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._entries.clear()
        self._refreshStats()

    def fileCount(self) -> int:
        return len(self._entries)

    def totalAdditions(self) -> int:
        return sum(e.additions for e in self._entries)

    def totalDeletions(self) -> int:
        return sum(e.deletions for e in self._entries)

    def expandAll(self) -> None:
        """展开所有文件."""
        for item in self._items:
            item.setExpanded(True)

    def collapseAll(self) -> None:
        """折叠所有文件."""
        for item in self._items:
            item.setExpanded(False)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _refreshStats(self) -> None:
        n = len(self._entries)
        if n == 0:
            self._summaryLabel.setText(self.tr("无变更"))
            self._totalStatsLabel.setText("")
            return

        self._summaryLabel.setText(
            self.tr("{n} 个文件变更").format(n=n)
        )

        total_add = self.totalAdditions()
        total_del = self.totalDeletions()
        parts = []
        if total_add > 0:
            parts.append(f"+{total_add}")
        if total_del > 0:
            parts.append(f"-{total_del}")
        self._totalStatsLabel.setText(" ".join(parts))
