# coding: utf-8
"""回滚 Dock (RevertDock)

列出 Agent 最近几次文件编辑的 checkpoint, 用户可以一键回滚到某个状态.

视觉参考 opencode 的 ``SessionRevertDock``:
- 折叠态: "3 个可回滚点" + 最近一条预览
- 展开态: 列表, 每条 [描述] [回滚按钮]

使用方式:
    dock = RevertDock(parent)
    dock.addCheckpoint("cp1", "修改了 src/main.py (+12 -3)")
    dock.addCheckpoint("cp2", "修改了 src/utils.py (+5 -1)")
    dock.restoreRequested.connect(lambda cp_id: ...)
    dock.show()
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ..button import PushButton
from ..label import BodyLabel, CaptionLabel
from .dock_surface import DockSurface


__all__ = ['RevertDock']


class _CheckpointItem(QWidget):
    """单条 checkpoint."""

    restoreClicked = Signal(str)  # checkpoint_id

    def __init__(self, cp_id: str, text: str,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._cpId = cp_id
        self._text = text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self._label = BodyLabel(text, self)
        self._label.setObjectName("revertItemText")
        self._label.setWordWrap(False)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        self._restoreBtn = PushButton(
            FluentIcon.HISTORY, self.tr("回滚"), self,
        )
        self._restoreBtn.setFixedHeight(24)
        self._restoreBtn.setObjectName("revertItemBtn")
        self._restoreBtn.clicked.connect(
            lambda: self.restoreClicked.emit(self._cpId)
        )

        layout.addWidget(self._label, 1)
        layout.addWidget(self._restoreBtn, 0)

    def checkpointId(self) -> str:
        return self._cpId

    def text(self) -> str:
        return self._text


class RevertDock(DockSurface):
    """回滚 Dock.

    Signals:
        restoreRequested(str): 用户点击某条的 [回滚] 按钮, 参数为 checkpoint_id

    构造函数:
        RevertDock(parent: QWidget = None)
    """

    restoreRequested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        self._items: List[_CheckpointItem] = []
        self._itemIndex: Dict[str, _CheckpointItem] = {}
        super().__init__(parent, collapsible=True)
        self.setObjectName("revertDock")
        self.hide()

    # ------------------------------------------------------------------
    # 子类覆盖
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        return 34

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        self._summaryLabel = BodyLabel("", self._header)
        self._summaryLabel.setObjectName("revertSummary")
        self._summaryLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        self._previewLabel = CaptionLabel("", self._header)
        self._previewLabel.setObjectName("revertPreview")
        self._previewLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        layout.addWidget(self._summaryLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._previewLabel, 1, Qt.AlignmentFlag.AlignVCenter)

    def _buildContent(self, layout: QVBoxLayout) -> None:
        self._listContainer = QWidget(self._content)
        self._listLayout = QVBoxLayout(self._listContainer)
        self._listLayout.setContentsMargins(0, 0, 0, 0)
        self._listLayout.setSpacing(2)
        layout.addWidget(self._listContainer)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addCheckpoint(self, cp_id: str, text: str) -> None:
        """添加一个回滚点.

        Args:
            cp_id: checkpoint 唯一标识
            text:  描述文本 (如 "修改了 src/main.py (+12 -3)")
        """
        if cp_id in self._itemIndex:
            return
        item = _CheckpointItem(cp_id, text, self._listContainer)
        item.restoreClicked.connect(self.restoreRequested.emit)
        self._listLayout.addWidget(item)
        self._items.append(item)
        self._itemIndex[cp_id] = item
        self._refreshSummary()
        if not self.isVisible():
            self.show()

    def removeCheckpoint(self, cp_id: str) -> None:
        """移除一个回滚点."""
        item = self._itemIndex.pop(cp_id, None)
        if item is None:
            return
        self._items.remove(item)
        self._listLayout.removeWidget(item)
        item.setParent(None)
        item.deleteLater()
        self._refreshSummary()
        if not self._items:
            self.hide()

    def clear(self) -> None:
        """清空所有回滚点."""
        for item in self._items:
            self._listLayout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._itemIndex.clear()
        self._refreshSummary()
        self.hide()

    def checkpointCount(self) -> int:
        return len(self._items)

    def setRestoring(self, cp_id: Optional[str]) -> None:
        """标记某个 checkpoint 正在回滚中 (禁用其按钮).

        Args:
            cp_id: 正在回滚的 checkpoint ID, None 表示恢复所有按钮
        """
        for item in self._items:
            btn = item._restoreBtn
            if cp_id is None:
                btn.setEnabled(True)
            else:
                btn.setEnabled(item.checkpointId() != cp_id)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _refreshSummary(self) -> None:
        n = len(self._items)
        if n == 0:
            self._summaryLabel.setText("")
            self._previewLabel.setText("")
            return
        self._summaryLabel.setText(
            self.tr("{n} 个可回滚点").format(n=n)
        )
        if self._items:
            preview = self._items[0].text()
            if len(preview) > 40:
                preview = preview[:40] + "..."
            self._previewLabel.setText(preview)
        else:
            self._previewLabel.setText("")
