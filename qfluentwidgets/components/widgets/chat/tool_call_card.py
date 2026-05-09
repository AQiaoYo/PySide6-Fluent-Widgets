# coding: utf-8
"""工具调用卡片组件

紧凑展示单次工具 (function) 调用的状态和详情:

- 折叠态 (默认): [icon] [tool_name] [● spinner / ✓ / ✗] [(用时 1.2s)]  [▶]
- 展开态: header + 调用参数 (json/text 代码块) + 返回结果 (markdown 区)

支持流式更新:
- 状态从 PENDING 转为 SUCCESS / ERROR 时, header 自动切换状态指示
- 调用 ``appendResultDelta`` 持续追加结果
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QMouseEvent
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..label import BodyLabel, CaptionLabel
from ..progress_ring import IndeterminateProgressRing
from .chat_message import ToolCallSegment, ToolCallStatus
from .code_block import CodeBlock
from .markdown_view import MarkdownView


__all__ = ['ToolCallCard']


class _ClickableFrame(QFrame):
    """可点击 QFrame, 鼠标进入显示手型, 点击发出 clicked 信号."""

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class ToolCallCard(QFrame):
    """工具调用展示卡片.

    生命周期:
        1. ``setSegment(seg)`` 绑定 ToolCallSegment
        2. 流式过程: 调 ``appendResultDelta`` 累积返回结果
        3. ``setStatus(SUCCESS/ERROR, duration_ms)`` 完成调用

    Attributes:
        expandedChanged(bool): 展开状态变化信号

    构造函数:
        ToolCallCard(parent: QWidget = None)
    """

    expandedChanged = Signal(bool)

    _ICON_SIZE = 14
    _STATUS_SIZE = 14
    _CHEVRON_SIZE = 12

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("toolCallCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 横向 Expanding: 卡片铺满父容器宽度, 与 ThinkingCard 一致
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._segment: Optional[ToolCallSegment] = None
        self._expanded = False

        self._setupUi()
        self._refreshHeader()
        FluentStyleSheet.CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self):
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header ----
        self._header = _ClickableFrame(self)
        self._header.setObjectName("toolCallHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(36)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(12, 0, 12, 0)
        headerLayout.setSpacing(8)

        # 工具 icon
        self._iconLabel = QLabel(self._header)
        self._iconLabel.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
        self._iconLabel.setPixmap(
            FluentIcon.DEVELOPER_TOOLS.icon().pixmap(
                QSize(self._ICON_SIZE, self._ICON_SIZE)
            )
        )

        # 工具名 (粗体小)
        self._nameLabel = BodyLabel("", self._header)
        self._nameLabel.setObjectName("toolCallName")

        # 状态指示: spinner (PENDING) / accept (SUCCESS) / cancel (ERROR)
        # 三者 stack 在同一容器, 切换时显隐
        self._statusContainer = QWidget(self._header)
        self._statusContainer.setFixedSize(self._STATUS_SIZE, self._STATUS_SIZE)
        statusStack = QHBoxLayout(self._statusContainer)
        statusStack.setContentsMargins(0, 0, 0, 0)
        statusStack.setSpacing(0)

        self._spinner = IndeterminateProgressRing(self._statusContainer, start=False)
        self._spinner.setFixedSize(self._STATUS_SIZE, self._STATUS_SIZE)
        self._spinner.setStrokeWidth(2)
        self._spinner.setTextVisible(False)

        self._statusIcon = QLabel(self._statusContainer)
        self._statusIcon.setFixedSize(self._STATUS_SIZE, self._STATUS_SIZE)
        self._statusIcon.hide()

        statusStack.addWidget(self._spinner)
        statusStack.addWidget(self._statusIcon)

        # 耗时 (灰色小字)
        self._durationLabel = CaptionLabel("", self._header)
        self._durationLabel.setObjectName("toolCallDuration")
        self._durationLabel.hide()

        # 展开箭头
        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)
        self._updateChevron()

        headerLayout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._nameLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._statusContainer, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._durationLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)
        headerLayout.addWidget(self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- content ----
        self._contentWrap = QFrame(self)
        self._contentWrap.setObjectName("toolCallContentWrap")
        self._contentWrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapLayout = QVBoxLayout(self._contentWrap)
        wrapLayout.setContentsMargins(12, 8, 12, 12)
        wrapLayout.setSpacing(8)

        # 参数标题 + 代码块
        self._argsLabel = CaptionLabel(self.tr("参数"), self._contentWrap)
        self._argsLabel.setObjectName("toolCallSectionLabel")
        self._argsBlock = CodeBlock("", "json", self._contentWrap)

        # 结果标题 + markdown
        self._resultLabel = CaptionLabel(self.tr("结果"), self._contentWrap)
        self._resultLabel.setObjectName("toolCallSectionLabel")
        self._resultView = MarkdownView("", self._contentWrap)

        wrapLayout.addWidget(self._argsLabel)
        wrapLayout.addWidget(self._argsBlock)
        wrapLayout.addWidget(self._resultLabel)
        wrapLayout.addWidget(self._resultView)

        self._contentWrap.hide()

        rootLayout.addWidget(self._header)
        rootLayout.addWidget(self._contentWrap)

    def _updateChevron(self):
        icon = (
            FluentIcon.CHEVRON_DOWN_MED if self._expanded
            else FluentIcon.CHEVRON_RIGHT_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )

    # ------------------------------------------------------------------
    # 公共 API: 数据
    # ------------------------------------------------------------------

    def setSegment(self, segment: ToolCallSegment):
        """绑定 ToolCallSegment 数据."""
        self._segment = segment
        self._argsBlock.setCode(segment.arguments)
        self._resultView.setMarkdown(segment.result)
        self._refreshHeader()

    def segment(self) -> Optional[ToolCallSegment]:
        return self._segment

    def setArguments(self, arguments: str):
        """更新调用参数 (覆盖式)."""
        if self._segment is not None:
            self._segment.arguments = arguments
        self._argsBlock.setCode(arguments)

    def appendArgumentsDelta(self, delta: str):
        """流式追加调用参数 (LLM 流式输出 JSON 参数时使用).

        注意: ``CodeBlock`` 没有原生的流式 API, 这里实现为
        "累积 + 重设", 适合参数文本通常较短 (一两行 JSON) 的场景.
        """
        if not delta:
            return
        if self._segment is not None:
            self._segment.arguments += delta
            self._argsBlock.setCode(self._segment.arguments)
        else:
            # 没绑定 segment 时回退到读取当前内容追加
            self._argsBlock.setCode(self._argsBlock._code + delta)

    def setResult(self, result: str):
        """覆盖式设置结果."""
        if self._segment is not None:
            self._segment.result = result
        self._resultView.setMarkdown(result)

    def setCodeBlockMaxVisibleLines(self, n: int):
        """设置卡片内 CodeBlock (参数区) 与结果 MarkdownView 内 CodeBlock 的
        最大可见行数. 详见 ``CodeBlock.setMaxVisibleLines``.
        """
        self._argsBlock.setMaxVisibleLines(n)
        self._resultView.setCodeBlockMaxVisibleLines(n)

    def codeBlockMaxVisibleLines(self) -> int:
        """获取参数区 CodeBlock 的最大可见行数 (与结果区一致)."""
        return self._argsBlock.maxVisibleLines()

    def appendResultDelta(self, delta: str):
        """流式追加结果."""
        if not delta:
            return
        if self._segment is not None:
            self._segment.result += delta
        self._resultView.appendMarkdown(delta)

    def setStatus(self, status: ToolCallStatus,
                  duration_ms: Optional[int] = None):
        """更新调用状态. duration_ms 不为 None 时同步更新耗时显示."""
        if self._segment is not None:
            self._segment.status = status
            if duration_ms is not None:
                self._segment.duration_ms = duration_ms
        self._refreshHeader()

    # ------------------------------------------------------------------
    # 公共 API: 展开 / 折叠
    # ------------------------------------------------------------------

    def setExpanded(self, expanded: bool):
        expanded = bool(expanded)
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._contentWrap.setVisible(expanded)
        self._updateChevron()
        self.expandedChanged.emit(expanded)

    def isExpanded(self) -> bool:
        return self._expanded

    def toggle(self):
        self.setExpanded(not self._expanded)

    # ------------------------------------------------------------------
    # 内部: 刷新 header
    # ------------------------------------------------------------------

    def _refreshHeader(self):
        seg = self._segment
        # 工具名
        name = seg.tool_name if seg else ""
        self._nameLabel.setText(name or self.tr("未知工具"))

        # 状态: 切换 spinner 与 status icon
        status = seg.status if seg else ToolCallStatus.PENDING
        if status == ToolCallStatus.PENDING:
            self._spinner.show()
            self._spinner.start()
            self._statusIcon.hide()
        else:
            self._spinner.stop()
            self._spinner.hide()
            self._statusIcon.show()
            if status == ToolCallStatus.SUCCESS:
                fi = FluentIcon.ACCEPT_MEDIUM
                color = QColor(40, 167, 69)  # 绿
            else:  # ERROR
                fi = FluentIcon.CANCEL_MEDIUM
                color = QColor(220, 53, 69)  # 红
            try:
                qicon = fi.icon(color=color)
            except TypeError:
                # 某些版本 FluentIcon.icon() 不支持 color 参数
                qicon = fi.icon()
            self._statusIcon.setPixmap(
                qicon.pixmap(QSize(self._STATUS_SIZE, self._STATUS_SIZE))
            )

        # 耗时
        if seg and seg.duration_ms is not None:
            ms = seg.duration_ms
            text = (f"{ms} ms" if ms < 1000
                    else f"{ms / 1000:.1f} s")
            self._durationLabel.setText(text)
            self._durationLabel.show()
        else:
            self._durationLabel.hide()
