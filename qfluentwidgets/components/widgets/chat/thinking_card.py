# coding: utf-8
"""思考过程卡片组件

用于展示推理模型 (deepseek-r1 / o1 等) 的思考过程.
卡片默认折叠, 点击 header 展开 / 折叠. 支持流式追加思考内容.

视觉:
- 折叠态: [icon] "正在深度思考..." / "已深度思考 (用时 X.X 秒)"  [▶]
- 展开态: header + 下方 markdown 区 (左侧细 border + 缩进)
"""

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..label import BodyLabel
from .chat_message import ThinkingSegment
from .markdown_view import MarkdownView


__all__ = ['ThinkingCard']


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


class ThinkingCard(QFrame):
    """思考过程展示卡片.

    生命周期:
        1. ``setSegment(seg)`` 绑定数据 (或随后调 ``update()``)
        2. 流式过程: 反复调 ``setContent`` / ``appendDelta`` 累积内容
        3. 调 ``finish(duration_ms)`` 进入"已深度思考"状态

    Attributes:
        expandedChanged(bool):  展开状态变化信号 (True=已展开)

    构造函数:
        ThinkingCard(parent: QWidget = None)
    """

    expandedChanged = Signal(bool)

    _ICON_SIZE = 16
    _CHEVRON_SIZE = 12

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("thinkingCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 横向 Expanding: 卡片永远铺满父容器 (segmentsWrap) 宽度, 不让内部
        # MarkdownView 等通过 sizeHint 反向撑大卡片自身.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._segment: Optional[ThinkingSegment] = None
        self._expanded = False
        self._defaultExpanded = False

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

        # ---- header (可点击) ----
        self._header = _ClickableFrame(self)
        self._header.setObjectName("thinkingHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(40)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(14, 0, 14, 0)
        headerLayout.setSpacing(10)

        self._iconLabel = QLabel(self._header)
        self._iconLabel.setObjectName("thinkingIcon")
        self._iconLabel.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
        self._iconLabel.setPixmap(
            FluentIcon.HIGHTLIGHT.icon().pixmap(QSize(self._ICON_SIZE, self._ICON_SIZE))
        )

        self._titleLabel = BodyLabel(self.tr("正在深度思考..."), self._header)
        self._titleLabel.setObjectName("thinkingTitle")

        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setObjectName("thinkingChevron")
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)
        self._updateChevron()

        headerLayout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._titleLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)
        headerLayout.addWidget(self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- content (markdown 区, 默认隐藏) ----
        self._contentWrap = QFrame(self)
        self._contentWrap.setObjectName("thinkingContentWrap")
        self._contentWrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapLayout = QVBoxLayout(self._contentWrap)
        # 与 header 对齐的水平内边距, 上下留呼吸空间
        wrapLayout.setContentsMargins(16, 8, 14, 12)
        wrapLayout.setSpacing(0)

        self._content = MarkdownView("", self._contentWrap)
        wrapLayout.addWidget(self._content)

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

    def setSegment(self, segment: ThinkingSegment):
        """绑定 ThinkingSegment 数据. 后续 segment 字段被外部修改后, 调
        ``update()`` 同步 UI."""
        self._segment = segment
        self._content.setMarkdown(segment.content)
        self._refreshHeader()

    def segment(self) -> Optional[ThinkingSegment]:
        return self._segment

    def setContent(self, markdown: str):
        """覆盖式设置思考内容."""
        if self._segment is not None:
            self._segment.content = markdown
        self._content.setMarkdown(markdown)

    def setCodeBlockMaxVisibleLines(self, n: int):
        """设置思考内容内嵌 CodeBlock 的最大可见行数.

        详见 ``CodeBlock.setMaxVisibleLines``.
        """
        self._content.setCodeBlockMaxVisibleLines(n)

    def codeBlockMaxVisibleLines(self) -> int:
        """获取思考内容内嵌 CodeBlock 的最大可见行数."""
        return self._content.codeBlockMaxVisibleLines()

    def appendDelta(self, delta: str):
        """流式追加思考内容."""
        if not delta:
            return
        if self._segment is not None:
            self._segment.content += delta
        self._content.appendMarkdown(delta)

    def finish(self, duration_ms: Optional[int] = None):
        """标记思考结束, 切换 header 文本为 "已深度思考(用时 X.X 秒)"."""
        if self._segment is not None:
            self._segment.finished = True
            if duration_ms is not None:
                self._segment.duration_ms = duration_ms
        self._refreshHeader()

    # ------------------------------------------------------------------
    # 公共 API: 展开 / 折叠
    # ------------------------------------------------------------------

    def setExpanded(self, expanded: bool):
        """显式设置展开状态."""
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

    def setDefaultExpanded(self, expanded: bool):
        """设置初始展开状态 (仅对未交互过的卡片生效)."""
        self._defaultExpanded = bool(expanded)
        self.setExpanded(self._defaultExpanded)

    # ------------------------------------------------------------------
    # 内部: 刷新 header 文案
    # ------------------------------------------------------------------

    def _refreshHeader(self):
        """根据 finished / duration 切换标题文本."""
        seg = self._segment
        if seg is None or not seg.finished:
            self._titleLabel.setText(self.tr("正在深度思考..."))
            return
        if seg.duration_ms is not None:
            secs = seg.duration_ms / 1000.0
            self._titleLabel.setText(
                self.tr("已深度思考 (用时 {:.1f} 秒)").format(secs)
            )
        else:
            self._titleLabel.setText(self.tr("已深度思考"))
