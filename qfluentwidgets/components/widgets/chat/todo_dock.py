# coding: utf-8
"""会话级 Todo Dock (TodoDock)

在输入框上方悬浮一个持续存在的 todo 进度条, 显示当前会话的任务执行进度.
与消息流内的 ``TaskListCard`` 不同: TaskListCard 是某条 AGENT 消息内的
计划展示, TodoDock 是会话级的持续状态.

视觉参考 opencode 的 ``SessionTodoDock``:
- 折叠态: "☐ 3/7" + 当前正在执行的任务预览 + 进度条
- 展开态: 完整任务列表 (带 checkbox 状态)

使用方式:
    dock = TodoDock(parent)
    dock.addTodo("t1", "分析需求文档")
    dock.addTodo("t2", "编写核心逻辑")
    dock.addTodo("t3", "添加错误处理")
    dock.setTodoStatus("t1", "completed")
    dock.setTodoStatus("t2", "in_progress")
    dock.show()
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..label import BodyLabel, CaptionLabel
from ..progress_bar import ProgressBar
from .dock_surface import DockSurface


__all__ = ['TodoDock']


class _TodoStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class _TodoItemRow(QWidget):
    """单行 todo 项."""

    def __init__(self, todo_id: str, text: str,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._todoId = todo_id
        self._text = text
        self._status = _TodoStatus.PENDING

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self._iconLabel = QLabel(self)
        self._iconLabel.setObjectName("todoItemIcon")
        self._iconLabel.setFixedWidth(16)
        self._iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._textLabel = BodyLabel(text, self)
        self._textLabel.setObjectName("todoItemText")
        self._textLabel.setWordWrap(False)
        self._textLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        layout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._textLabel, 1)

        self._refreshIcon()

    def todoId(self) -> str:
        return self._todoId

    def text(self) -> str:
        return self._text

    def status(self) -> str:
        return self._status

    def setStatus(self, status: str) -> None:
        self._status = status
        self._refreshIcon()
        # 用 property 让 QSS 可以按状态选择样式
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)

    def _refreshIcon(self) -> None:
        if self._status == _TodoStatus.COMPLETED:
            self._iconLabel.setText("\u2713")   # ✓
        elif self._status == _TodoStatus.IN_PROGRESS:
            self._iconLabel.setText("\u25ce")   # ◎
        else:
            self._iconLabel.setText("\u25a1")   # □


class TodoDock(DockSurface):
    """会话级 Todo Dock.

    Signals:
        todoToggled(str, str): todo 状态变化时发出, 参数 (todo_id, new_status)

    构造函数:
        TodoDock(parent: QWidget = None)
    """

    todoToggled = Signal(str, str)

    def __init__(self, parent: Optional[QWidget] = None):
        self._todos: List[_TodoItemRow] = []
        self._todoIndex: Dict[str, _TodoItemRow] = {}
        super().__init__(parent, collapsible=True)
        self.setObjectName("todoDock")
        self.hide()

    # ------------------------------------------------------------------
    # 子类覆盖
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        return 38

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        # 进度文字: "3/7"
        self._progressLabel = BodyLabel("", self._header)
        self._progressLabel.setObjectName("todoProgress")

        # 当前任务预览
        self._previewLabel = CaptionLabel("", self._header)
        self._previewLabel.setObjectName("todoPreview")
        self._previewLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )

        # 进度条
        self._progressBar = ProgressBar(self._header)
        self._progressBar.setObjectName("todoProgressBar")
        self._progressBar.setFixedWidth(60)
        self._progressBar.setFixedHeight(4)

        layout.addWidget(self._progressLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._previewLabel, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._progressBar, 0, Qt.AlignmentFlag.AlignVCenter)

    def _buildContent(self, layout: QVBoxLayout) -> None:
        self._listContainer = QWidget(self._content)
        self._listLayout = QVBoxLayout(self._listContainer)
        self._listLayout.setContentsMargins(0, 0, 0, 0)
        self._listLayout.setSpacing(2)
        layout.addWidget(self._listContainer)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addTodo(self, todo_id: str, text: str,
                status: str = _TodoStatus.PENDING) -> None:
        """添加一个 todo 项.

        Args:
            todo_id: 唯一标识
            text:    任务描述
            status:  初始状态 ("pending" / "in_progress" / "completed")
        """
        if todo_id in self._todoIndex:
            return
        row = _TodoItemRow(todo_id, text, self._listContainer)
        row.setStatus(status)
        self._listLayout.addWidget(row)
        self._todos.append(row)
        self._todoIndex[todo_id] = row
        self._refreshProgress()
        if not self.isVisible():
            self.show()

    def removeTodo(self, todo_id: str) -> None:
        """移除一个 todo 项."""
        row = self._todoIndex.pop(todo_id, None)
        if row is None:
            return
        self._todos.remove(row)
        self._listLayout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._refreshProgress()
        if not self._todos:
            self.hide()

    def setTodoStatus(self, todo_id: str, status: str) -> None:
        """更新某个 todo 的状态.

        Args:
            todo_id: todo 唯一标识
            status:  新状态 ("pending" / "in_progress" / "completed")
        """
        row = self._todoIndex.get(todo_id)
        if row is None:
            return
        old = row.status()
        row.setStatus(status)
        self._refreshProgress()
        if old != status:
            self.todoToggled.emit(todo_id, status)

    def clear(self) -> None:
        """清空所有 todo."""
        for row in self._todos:
            self._listLayout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._todos.clear()
        self._todoIndex.clear()
        self._refreshProgress()
        self.hide()

    def todoCount(self) -> int:
        return len(self._todos)

    def completedCount(self) -> int:
        return sum(1 for r in self._todos if r.status() == _TodoStatus.COMPLETED)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _refreshProgress(self) -> None:
        total = len(self._todos)
        done = self.completedCount()

        if total == 0:
            self._progressLabel.setText("")
            self._previewLabel.setText("")
            self._progressBar.setValue(0)
            return

        self._progressLabel.setText(f"{done}/{total}")
        self._progressBar.setRange(0, total)
        self._progressBar.setValue(done)

        # 预览: 当前 in_progress 的, 没有则取第一个 pending 的
        active = None
        for row in self._todos:
            if row.status() == _TodoStatus.IN_PROGRESS:
                active = row
                break
        if active is None:
            for row in self._todos:
                if row.status() == _TodoStatus.PENDING:
                    active = row
                    break
        if active is None and self._todos:
            active = self._todos[-1]

        if active:
            preview = active.text()
            if len(preview) > 35:
                preview = preview[:35] + "..."
            self._previewLabel.setText(preview)
        else:
            self._previewLabel.setText("")
