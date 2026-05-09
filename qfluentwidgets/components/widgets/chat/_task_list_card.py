# coding: utf-8
"""TaskListSegment 对应的 card widget (P2d).

视觉参考 Claude Code 的任务计划面板: 一张可折叠卡片, header 里是 "任务
计划 (1/3)" + chevron, 内容是每个任务一行 ``[状态图标] 文字``. 状态图标:

    TODO        -> [ ]  空心方框, 暗色
    IN_PROGRESS -> [⟳]  旋转圈, 主题色
    DONE        -> [✓]  对勾, 主题色

状态变化由宿主 (demo 或真实 agent) 通过 ``AgentChatView.updateTaskItem``
触发, 本 card 只负责呈现.

暴露的 ``setSegment(TaskListSegment)`` 让 segment_renderers 把数据绑进来,
后续调 ``refresh()`` 即可根据最新 items 重画行 (或者增量 ``updateItem``).
"""

from typing import Dict, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from .._clickable import ClickableFrame
from ..label import BodyLabel, StrongBodyLabel
from .chat_message import TaskItem, TaskListSegment, TaskStatus


__all__ = ['TaskListCard']


class _TaskItemRow(QWidget):
    """单行任务项 UI: [状态图标] [文字]."""

    def __init__(self, item: TaskItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._item = item

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # 状态图标用 QLabel + 固定 unicode 字符, 保持跨 theme 的一致性.
        # 不用 IconWidget 因为 FluentIcon 没对应的任务 status 图标, 且 unicode
        # 方案更轻量.
        self._iconLabel = QLabel(self)
        self._iconLabel.setObjectName("taskItemIcon")
        self._iconLabel.setFixedWidth(18)
        self._iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._textLabel = BodyLabel("", self)
        self._textLabel.setObjectName("taskItemText")
        self._textLabel.setWordWrap(True)
        self._textLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        layout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._textLabel, 1)

        self._refresh()

    def item(self) -> TaskItem:
        return self._item

    def setItem(self, item: TaskItem) -> None:
        self._item = item
        self._refresh()

    def _refresh(self) -> None:
        # 文字: 完成后加删除线感 (用属性让 QSS 控制, 避免硬编码 color)
        self._textLabel.setText(self._item.text or "")
        self.setProperty("status", self._item.status.value)
        # 刷 style 让 QSS 属性选择器重新匹配
        self.style().unpolish(self)
        self.style().polish(self)

        # 用 Unicode 方块 / 对勾 / 圆圈; QSS 给颜色, 不在此写 inline 样式.
        if self._item.status == TaskStatus.DONE:
            icon_text = "\u2713"   # ✓
        elif self._item.status == TaskStatus.IN_PROGRESS:
            icon_text = "\u25ce"   # ◎ (双圆圈, 代表进行中)
        else:  # TODO
            icon_text = "\u25a1"   # □
        self._iconLabel.setText(icon_text)
        self._iconLabel.setProperty("status", self._item.status.value)
        self._iconLabel.style().unpolish(self._iconLabel)
        self._iconLabel.style().polish(self._iconLabel)


class TaskListCard(QFrame):
    """任务列表卡片 widget.

    Signals: 无. 状态翻转 / 项新增 / 项删除 由宿主通过 ``refresh()`` 或
    ``updateItem(item_id, status)`` 驱动.

    生命周期:
        1. ``setSegment(seg)`` 绑定 TaskListSegment
        2. ``refresh()`` / ``updateItem(id, status)`` 更新可视
        3. 点击 header 可折叠/展开列表内容

    构造函数:
        TaskListCard(parent: QWidget = None)
    """

    _CHEVRON_SIZE = 12

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("taskListCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        self._segment: Optional[TaskListSegment] = None
        self._expanded = True
        # item.id -> _TaskItemRow
        self._rowIndex: Dict[str, _TaskItemRow] = {}

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header: [chevron] [标题] [进度文案] ----
        self._header = ClickableFrame(self)
        self._header.setObjectName("taskListHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(36)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(12, 0, 12, 0)
        headerLayout.setSpacing(8)

        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setObjectName("taskListChevron")
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)

        self._titleLabel = StrongBodyLabel(self.tr("任务计划"), self._header)
        self._titleLabel.setObjectName("taskListTitle")

        self._progressLabel = BodyLabel("", self._header)
        self._progressLabel.setObjectName("taskListProgress")

        headerLayout.addWidget(
            self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter,
        )
        headerLayout.addWidget(
            self._titleLabel, 0, Qt.AlignmentFlag.AlignVCenter,
        )
        headerLayout.addWidget(
            self._progressLabel, 0, Qt.AlignmentFlag.AlignVCenter,
        )
        headerLayout.addStretch(1)

        # ---- content: 可折叠任务列表 ----
        self._content = QFrame(self)
        self._content.setObjectName("taskListContent")
        self._content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._contentLayout = QVBoxLayout(self._content)
        self._contentLayout.setContentsMargins(16, 6, 16, 10)
        self._contentLayout.setSpacing(2)

        rootLayout.addWidget(self._header)
        rootLayout.addWidget(self._content)

        self._updateChevron()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setSegment(self, segment: TaskListSegment) -> None:
        """绑定 TaskListSegment, 重建整个列表 UI."""
        self._segment = segment
        self._rebuildList()

    def segment(self) -> Optional[TaskListSegment]:
        return self._segment

    def refresh(self) -> None:
        """根据 ``self._segment.items`` 重建列表 UI. 适合任务数量变化时调."""
        self._rebuildList()

    def updateItem(self, item_id: str, status: TaskStatus,
                   text: Optional[str] = None) -> None:
        """增量更新某个任务项的状态 / 文字. 未知 item_id 静默忽略."""
        if self._segment is None:
            return
        for it in self._segment.items:
            if it.id == item_id:
                it.status = status
                if text is not None:
                    it.text = text
                row = self._rowIndex.get(item_id)
                if row is not None:
                    row.setItem(it)
                self._refreshProgress()
                return

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

    def _rebuildList(self) -> None:
        # 清空现有 rows
        for _, row in list(self._rowIndex.items()):
            self._contentLayout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._rowIndex.clear()

        if self._segment is None:
            return

        if self._segment.title:
            self._titleLabel.setText(self._segment.title)
        else:
            self._titleLabel.setText(self.tr("任务计划"))

        for item in self._segment.items:
            row = _TaskItemRow(item, self._content)
            self._contentLayout.addWidget(row)
            self._rowIndex[item.id] = row

        self._refreshProgress()

    def _refreshProgress(self) -> None:
        if self._segment is None:
            self._progressLabel.setText("")
            return
        total = len(self._segment.items)
        done = sum(
            1 for it in self._segment.items if it.status == TaskStatus.DONE
        )
        self._progressLabel.setText(f"({done}/{total})")

    def _updateChevron(self) -> None:
        icon = (
            FluentIcon.CHEVRON_DOWN_MED if self._expanded
            else FluentIcon.CHEVRON_RIGHT_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )
