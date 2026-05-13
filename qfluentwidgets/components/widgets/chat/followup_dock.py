# coding: utf-8
"""跟进消息队列 Dock (FollowupDock)

当 Agent 正在生成回复时, 用户提交的新 prompt 不立刻发送, 而是排队.
此 Dock 在输入框上方显示排队中的消息列表, 生成完成后自动发送.

视觉参考 opencode 的 ``SessionFollowupDock``:
- 折叠态: "3 条待发送" + 第一条预览
- 展开态: 完整列表, 每条可点击编辑或发送

使用方式:
    dock = FollowupDock(parent)
    dock.addItem("id1", "请帮我加上错误处理")
    dock.addItem("id2", "还有单元测试也要写")
    dock.itemSendRequested.connect(lambda item_id: ...)
    dock.show()
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ..button import TransparentToolButton
from ..label import BodyLabel, CaptionLabel
from .dock_surface import DockSurface


__all__ = ['FollowupDock']


class _FollowupItem(QWidget):
    """单条排队消息."""

    sendClicked = Signal(str)   # item_id
    editClicked = Signal(str)   # item_id

    def __init__(self, item_id: str, text: str,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._itemId = item_id
        self._text = text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(6)

        self._label = BodyLabel(text, self)
        self._label.setObjectName("followupItemText")
        self._label.setWordWrap(False)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        self._editBtn = TransparentToolButton(FluentIcon.EDIT, self)
        self._editBtn.setFixedSize(20, 20)
        self._editBtn.setIconSize(QSize(12, 12))
        self._editBtn.setToolTip("编辑")
        self._editBtn.clicked.connect(lambda: self.editClicked.emit(self._itemId))

        self._sendBtn = TransparentToolButton(FluentIcon.SEND, self)
        self._sendBtn.setFixedSize(20, 20)
        self._sendBtn.setIconSize(QSize(12, 12))
        self._sendBtn.setToolTip("立即发送")
        self._sendBtn.clicked.connect(lambda: self.sendClicked.emit(self._itemId))

        layout.addWidget(self._label, 1)
        layout.addWidget(self._editBtn, 0)
        layout.addWidget(self._sendBtn, 0)

    def itemId(self) -> str:
        return self._itemId

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        self._text = text
        self._label.setText(text)


class FollowupDock(DockSurface):
    """跟进消息队列 Dock.

    Signals:
        itemSendRequested(str): 用户点击某条的 [发送] 按钮, 参数为 item_id
        itemEditRequested(str): 用户点击某条的 [编辑] 按钮, 参数为 item_id

    构造函数:
        FollowupDock(parent: QWidget = None)
    """

    itemSendRequested = Signal(str)
    itemEditRequested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        self._items: List[_FollowupItem] = []
        self._itemIndex: Dict[str, _FollowupItem] = {}
        super().__init__(parent, collapsible=True)
        self.setObjectName("followupDock")
        self.hide()

    # ------------------------------------------------------------------
    # 子类覆盖
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        return 34

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        self._summaryLabel = BodyLabel("", self._header)
        self._summaryLabel.setObjectName("followupSummary")
        self._summaryLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        self._previewLabel = CaptionLabel("", self._header)
        self._previewLabel.setObjectName("followupPreview")
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

    def addItem(self, item_id: str, text: str) -> None:
        """添加一条排队消息.

        Args:
            item_id: 唯一标识
            text:    消息文本
        """
        if item_id in self._itemIndex:
            return
        item = _FollowupItem(item_id, text, self._listContainer)
        item.sendClicked.connect(self.itemSendRequested.emit)
        item.editClicked.connect(self.itemEditRequested.emit)
        self._listLayout.addWidget(item)
        self._items.append(item)
        self._itemIndex[item_id] = item
        self._refreshSummary()
        if not self.isVisible():
            self.show()

    def removeItem(self, item_id: str) -> None:
        """移除一条排队消息."""
        item = self._itemIndex.pop(item_id, None)
        if item is None:
            return
        self._items.remove(item)
        self._listLayout.removeWidget(item)
        item.setParent(None)
        item.deleteLater()
        self._refreshSummary()
        if not self._items:
            self.hide()

    def updateItem(self, item_id: str, text: str) -> None:
        """更新某条消息的文本."""
        item = self._itemIndex.get(item_id)
        if item:
            item.setText(text)
            self._refreshSummary()

    def clear(self) -> None:
        """清空所有排队消息."""
        for item in self._items:
            self._listLayout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._items.clear()
        self._itemIndex.clear()
        self._refreshSummary()
        self.hide()

    def itemCount(self) -> int:
        return len(self._items)

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
            self.tr("{n} 条待发送").format(n=n)
        )
        # 折叠态时显示第一条预览
        if self._items:
            preview = self._items[0].text()
            if len(preview) > 40:
                preview = preview[:40] + "..."
            self._previewLabel.setText(preview)
        else:
            self._previewLabel.setText("")
