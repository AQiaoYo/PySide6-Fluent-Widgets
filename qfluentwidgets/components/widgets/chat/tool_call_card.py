# coding: utf-8
"""工具调用卡片组件

提供两层结构:

- ``ToolCallCardBase`` -- 抽象基类, 持有 header (icon + name + spinner /
  status icon + duration + chevron + 审批按钮区) 与 content 容器, 把内容
  实现交给子类的 ``_buildContent()``.
- ``GenericToolCallCard`` -- 通用渲染器: 参数 (CodeBlock json) + 结果
  (MarkdownView). 不知道 tool 类型时使用.

特化渲染器 (FileReadCard / FileEditCard / BashCard / ...) 在
``tool_renderers`` 模块中定义, 同样继承 ``ToolCallCardBase``.

历史名 ``ToolCallCard`` 保留为 ``GenericToolCallCard`` 的别名以保证
向后兼容.
"""

from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.config import qconfig
from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from .._clickable import ClickableFrame
from ..button import PrimaryPushButton, PushButton
from ..label import BodyLabel, CaptionLabel
from ..progress_ring import IndeterminateProgressRing
from ._collapse_anim import animate_collapse, animations_enabled_root
from .chat_message import ToolCallSegment, ToolCallStatus
from .code_block import CodeBlock
from .markdown_view import MarkdownView


__all__ = [
    'ToolCallCardBase', 'GenericToolCallCard', 'ToolCallCard',
]


# ----------------------------------------------------------------------
# ToolCallCardBase
# ----------------------------------------------------------------------

class ToolCallCardBase(QFrame):
    """工具调用卡片抽象基类.

    提供统一的 header (icon / name / spinner / status icon / duration /
    chevron / 审批按钮区) 与可折叠 content 容器. 子类只需实现
    ``_buildContent(parent)`` 把具体内容塞进容器, 以及可选地覆盖
    ``_refreshHeader()`` / ``_displayName(seg)`` / ``_displayIcon(seg)``
    定制 header 文案与图标.

    生命周期:
        1. ``setSegment(seg)`` 绑定数据
        2. (可选) 流式 ``appendArgumentsDelta`` / ``appendResultDelta``
        3. ``setStatus(SUCCESS/ERROR, duration_ms)`` 完成调用
        4. PENDING_APPROVAL 状态下显示 [批准] [拒绝] 按钮, 用户点击发出
           ``approveClicked`` / ``rejectClicked`` 信号

    Attributes:
        expandedChanged(bool): 展开状态变化信号
        approveClicked():       用户点击 [批准] 按钮 (本次允许)
        rejectClicked():        用户点击 [拒绝] 按钮 (本次拒绝)
        alwaysAllowClicked():   用户点击 [总是允许] 按钮 (本次允许 + 把工具策略设为 ALLOW)
        alwaysRejectClicked():  用户点击 [总是拒绝] 按钮 (本次拒绝 + 把工具策略设为 DENY)

    构造函数:
        ToolCallCardBase(parent: QWidget = None)
    """

    expandedChanged = Signal(bool)
    approveClicked = Signal()
    rejectClicked = Signal()
    alwaysAllowClicked = Signal()
    alwaysRejectClicked = Signal()

    _ICON_SIZE = 14
    _STATUS_SIZE = 14
    _CHEVRON_SIZE = 12
    _APPROVAL_HEIGHT = 26

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("toolCallCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # 横向 Expanding: 卡片铺满父容器宽度, 与 ThinkingCard 一致
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._segment: Optional[ToolCallSegment] = None
        self._expanded = False
        self._codeMaxVisibleLines = CodeBlock._DEFAULT_MAX_VISIBLE_LINES
        # 展开 / 折叠动画状态
        self._expandAnim: Optional[QPropertyAnimation] = None
        self._expandAnimEnabled: bool = True

        self._setupUi()
        self._refreshHeader()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

        # FluentIcon 的 ``Theme.AUTO`` 在 _refreshIcon / _updateChevron 调
        # 用时会读 ``qconfig.theme`` 选黑/白 svg 路径, 但 setPixmap 之后
        # QLabel 不会自动跟随主题变化. 监听 themeChanged 主动重画.
        qconfig.themeChanged.connect(self._onThemeChanged)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setupUi(self):
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header ----
        self._header = ClickableFrame(self)
        self._header.setObjectName("toolCallHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(36)
        self._header.clicked.connect(self.toggle)

        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(12, 0, 12, 0)
        headerLayout.setSpacing(8)

        # 工具 icon
        self._iconLabel = QLabel(self._header)
        self._iconLabel.setObjectName("toolCallIcon")
        self._iconLabel.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
        self._refreshIcon()

        # 工具名 (粗体)
        self._nameLabel = BodyLabel("", self._header)
        self._nameLabel.setObjectName("toolCallName")

        # 状态指示: spinner (PENDING) / accept (SUCCESS) / cancel (ERROR / REJECTED)
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
        self._statusIcon.setObjectName("toolCallStatusIcon")
        self._statusIcon.setFixedSize(self._STATUS_SIZE, self._STATUS_SIZE)
        self._statusIcon.hide()

        statusStack.addWidget(self._spinner)
        statusStack.addWidget(self._statusIcon)

        # 状态文案 (REJECTED 时显示 "已拒绝", 其它时机隐藏)
        self._statusTextLabel = CaptionLabel("", self._header)
        self._statusTextLabel.setObjectName("toolCallStatusText")
        self._statusTextLabel.hide()

        # 耗时 (灰色小字)
        self._durationLabel = CaptionLabel("", self._header)
        self._durationLabel.setObjectName("toolCallDuration")
        self._durationLabel.hide()

        # 审批按钮区 (PENDING_APPROVAL 时显示)
        self._approvalRow = QWidget(self._header)
        self._approvalRow.setObjectName("toolCallApproval")
        approvalLayout = QHBoxLayout(self._approvalRow)
        approvalLayout.setContentsMargins(0, 0, 0, 0)
        approvalLayout.setSpacing(6)

        self._approveBtn = PrimaryPushButton(
            FluentIcon.ACCEPT, self.tr("批准"), self._approvalRow,
        )
        self._approveBtn.setFixedHeight(self._APPROVAL_HEIGHT)
        self._approveBtn.setIconSize(QSize(12, 12))
        self._approveBtn.clicked.connect(self.approveClicked)

        self._alwaysAllowBtn = PushButton(
            self.tr("总是允许"), self._approvalRow,
        )
        self._alwaysAllowBtn.setFixedHeight(self._APPROVAL_HEIGHT)
        self._alwaysAllowBtn.setToolTip(
            self.tr("批准本次, 并把此工具的审批策略改成 ALLOW (后续不再询问)")
        )
        self._alwaysAllowBtn.clicked.connect(self.alwaysAllowClicked)

        self._rejectBtn = PushButton(
            FluentIcon.CANCEL, self.tr("拒绝"), self._approvalRow,
        )
        self._rejectBtn.setFixedHeight(self._APPROVAL_HEIGHT)
        self._rejectBtn.setIconSize(QSize(12, 12))
        self._rejectBtn.clicked.connect(self.rejectClicked)

        self._alwaysRejectBtn = PushButton(
            self.tr("总是拒绝"), self._approvalRow,
        )
        self._alwaysRejectBtn.setFixedHeight(self._APPROVAL_HEIGHT)
        self._alwaysRejectBtn.setToolTip(
            self.tr("拒绝本次, 并把此工具的审批策略改成 DENY (后续自动拒绝)")
        )
        self._alwaysRejectBtn.clicked.connect(self.alwaysRejectClicked)

        approvalLayout.addWidget(self._approveBtn)
        approvalLayout.addWidget(self._alwaysAllowBtn)
        approvalLayout.addWidget(self._rejectBtn)
        approvalLayout.addWidget(self._alwaysRejectBtn)
        self._approvalRow.hide()

        # 展开箭头
        self._chevronLabel = QLabel(self._header)
        self._chevronLabel.setObjectName("toolCallChevron")
        self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)
        self._updateChevron()

        headerLayout.addWidget(self._iconLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._nameLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._statusContainer, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._statusTextLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._durationLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)
        headerLayout.addWidget(self._approvalRow, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        # ---- content (子类填充) ----
        self._contentWrap = QFrame(self)
        self._contentWrap.setObjectName("toolCallContentWrap")
        self._contentWrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._contentLayout = QVBoxLayout(self._contentWrap)
        self._contentLayout.setContentsMargins(12, 8, 12, 12)
        self._contentLayout.setSpacing(8)

        self._buildContent(self._contentWrap)
        self._contentWrap.hide()

        rootLayout.addWidget(self._header)
        # AlignTop: 让 _contentWrap 在 rootLayout 给的 alloc 内顶部对齐.
        # 默认 Qt 给 widget 在 alloc 内垂直居中, 当 widget.maxH < alloc.h
        # (动画起始 widget 被压扁时) 居中会让内容看起来 "从中间向上下展开".
        # AlignTop 让窗帘从顶部向下揭开, 视觉自然.
        rootLayout.addWidget(self._contentWrap, 0, Qt.AlignmentFlag.AlignTop)

    def _updateChevron(self):
        icon = (
            FluentIcon.CHEVRON_DOWN_MED if self._expanded
            else FluentIcon.CHEVRON_RIGHT_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )

    def _refreshIcon(self):
        """刷新 header 左侧工具图标. 子类可覆盖以使用语义化图标."""
        fi = self._displayIcon(self._segment)
        self._iconLabel.setPixmap(
            fi.icon().pixmap(QSize(self._ICON_SIZE, self._ICON_SIZE))
        )

    def _onThemeChanged(self, _theme=None) -> None:
        """主题切换时主动重新生成 pixmap 类图标.

        QSS 由 ``FluentStyleSheet`` 自动刷, 但 ``QLabel.setPixmap`` 设进去
        的位图不会跟主题色变. 这里只刷 header 工具图标 + chevron — status
        图标 (绿对勾 / 红叉 / 橙 INFO) 用的是固定 RGB 颜色, 不需要主题适配.
        """
        self._refreshIcon()
        self._updateChevron()

    # ------------------------------------------------------------------
    # 子类重载点
    # ------------------------------------------------------------------

    def _buildContent(self, parent: QWidget) -> None:
        """子类在此向 ``self._contentLayout`` 添加内容子项.

        默认空实现 (基类不强制有 content).
        """

    def _displayIcon(self, segment: Optional[ToolCallSegment]):
        """返回 header 左侧图标 (FluentIconBase). 默认 ``DEVELOPER_TOOLS``."""
        return FluentIcon.DEVELOPER_TOOLS

    def _displayName(self, segment: Optional[ToolCallSegment]) -> str:
        """返回 header 显示文本. 默认即 ``segment.tool_name``."""
        if segment is None:
            return self.tr("未知工具")
        return segment.tool_name or self.tr("未知工具")

    def _onSegmentChanged(self, segment: Optional[ToolCallSegment]) -> None:
        """``setSegment`` 后调用, 子类用来同步内容到自身 widget."""

    # ------------------------------------------------------------------
    # 公共 API: 数据绑定
    # ------------------------------------------------------------------

    def setSegment(self, segment: ToolCallSegment):
        """绑定 ToolCallSegment 数据."""
        self._segment = segment
        self._refreshIcon()
        self._refreshHeader()
        self._onSegmentChanged(segment)

    def segment(self) -> Optional[ToolCallSegment]:
        return self._segment

    def setArguments(self, arguments: str):
        """更新调用参数 (覆盖式). 子类按需处理."""
        if self._segment is not None:
            self._segment.arguments = arguments
        self._onSegmentChanged(self._segment)

    def appendArgumentsDelta(self, delta: str):
        """流式追加调用参数. 子类按需处理."""
        if not delta:
            return
        if self._segment is not None:
            self._segment.arguments += delta
        self._onSegmentChanged(self._segment)

    def setResult(self, result: str):
        """覆盖式设置结果. 子类按需处理."""
        if self._segment is not None:
            self._segment.result = result
        self._onSegmentChanged(self._segment)

    def appendResultDelta(self, delta: str):
        """流式追加结果. 子类按需处理."""
        if not delta:
            return
        if self._segment is not None:
            self._segment.result += delta
        self._onSegmentChanged(self._segment)

    def setStatus(self, status: ToolCallStatus,
                  duration_ms: Optional[int] = None):
        """更新调用状态. duration_ms 不为 None 时同步更新耗时显示."""
        if self._segment is not None:
            self._segment.status = status
            if duration_ms is not None:
                self._segment.duration_ms = duration_ms
        self._refreshHeader()

    def setCodeBlockMaxVisibleLines(self, n: int):
        """设置卡片内 CodeBlock 的最大可见行数. 子类可覆盖以传递到自己的
        子 widget. 详见 ``CodeBlock.setMaxVisibleLines``.
        """
        n = max(1, int(n))
        self._codeMaxVisibleLines = n

    def codeBlockMaxVisibleLines(self) -> int:
        return self._codeMaxVisibleLines

    # ------------------------------------------------------------------
    # 展开 / 折叠
    # ------------------------------------------------------------------

    def setExpanded(self, expanded: bool):
        """显式设置展开 / 折叠 (瞬时, 无动画)."""
        expanded = bool(expanded)
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._updateChevron()
        self.expandedChanged.emit(expanded)
        self._contentWrap.setVisible(expanded)

    def isExpanded(self) -> bool:
        return self._expanded

    def toggle(self):
        self.setExpanded(not self._expanded)

    # ------------------------------------------------------------------
    # 动画控制
    # ------------------------------------------------------------------

    def setExpandAnimationEnabled(self, enabled: bool) -> None:
        """设置展开 / 折叠动画是否启用 (默认 ``True``).

        关闭后 ``setExpanded`` / ``toggle`` 退化为瞬间 setVisible, 与本期
        改造前行为等价.
        """
        self._expandAnimEnabled = bool(enabled)

    def expandAnimationEnabled(self) -> bool:
        return self._expandAnimEnabled

    def _shouldAnimateExpand(self) -> bool:
        """综合本卡开关 + 宿主总开关 + visible 状态 决定是否走动画."""
        if not self._expandAnimEnabled:
            return False
        if not self.isVisible():
            return False
        if not animations_enabled_root(self):
            return False
        return True

    # ------------------------------------------------------------------
    # 内部: 刷新 header
    # ------------------------------------------------------------------

    def _refreshHeader(self):
        seg = self._segment
        # 工具名
        self._nameLabel.setText(self._displayName(seg))

        status = seg.status if seg else ToolCallStatus.PENDING

        # PENDING_APPROVAL: 隐藏 spinner / status icon, 显示审批按钮
        if status == ToolCallStatus.PENDING_APPROVAL:
            self._spinner.stop()
            self._spinner.hide()
            self._statusIcon.show()
            try:
                qicon = FluentIcon.INFO.icon(color=QColor(255, 165, 0))
            except TypeError:
                qicon = FluentIcon.INFO.icon()
            self._statusIcon.setPixmap(
                qicon.pixmap(QSize(self._STATUS_SIZE, self._STATUS_SIZE))
            )
            self._statusTextLabel.hide()
            self._approvalRow.show()
        else:
            self._approvalRow.hide()
            if status == ToolCallStatus.PENDING:
                self._spinner.show()
                self._spinner.start()
                self._statusIcon.hide()
                self._statusTextLabel.hide()
            else:
                self._spinner.stop()
                self._spinner.hide()
                self._statusIcon.show()
                if status == ToolCallStatus.SUCCESS:
                    fi = FluentIcon.ACCEPT_MEDIUM
                    color = QColor(40, 167, 69)  # 绿
                elif status == ToolCallStatus.REJECTED:
                    fi = FluentIcon.CANCEL_MEDIUM
                    color = QColor(220, 53, 69)  # 红
                else:  # ERROR
                    fi = FluentIcon.CANCEL_MEDIUM
                    color = QColor(220, 53, 69)
                try:
                    qicon = fi.icon(color=color)
                except TypeError:
                    qicon = fi.icon()
                self._statusIcon.setPixmap(
                    qicon.pixmap(QSize(self._STATUS_SIZE, self._STATUS_SIZE))
                )

                if status == ToolCallStatus.REJECTED:
                    self._statusTextLabel.setText(self.tr("已拒绝"))
                    self._statusTextLabel.show()
                else:
                    self._statusTextLabel.hide()

        # 耗时
        if seg and seg.duration_ms is not None and status not in (
            ToolCallStatus.PENDING_APPROVAL, ToolCallStatus.PENDING,
        ):
            ms = seg.duration_ms
            text = (f"{ms} ms" if ms < 1000
                    else f"{ms / 1000:.1f} s")
            self._durationLabel.setText(text)
            self._durationLabel.show()
        else:
            self._durationLabel.hide()


# ----------------------------------------------------------------------
# GenericToolCallCard (默认渲染器)
# ----------------------------------------------------------------------

class GenericToolCallCard(ToolCallCardBase):
    """通用工具调用渲染器: 参数 (CodeBlock json) + 结果 (MarkdownView).

    用作 ``tool_renderers`` 注册表中找不到匹配的工具名时的 fallback,
    也是历史 ``ToolCallCard`` 的对等替换 (功能完全一致).

    构造函数:
        GenericToolCallCard(parent: QWidget = None)
    """

    def _buildContent(self, parent: QWidget) -> None:
        # 参数标题 + 代码块
        self._argsLabel = CaptionLabel(self.tr("参数"), parent)
        self._argsLabel.setObjectName("toolCallSectionLabel")
        self._argsBlock = CodeBlock("", "json", parent)

        # 结果标题 + markdown
        self._resultLabel = CaptionLabel(self.tr("结果"), parent)
        self._resultLabel.setObjectName("toolCallSectionLabel")
        self._resultView = MarkdownView("", parent)

        self._contentLayout.addWidget(self._argsLabel)
        self._contentLayout.addWidget(self._argsBlock)
        self._contentLayout.addWidget(self._resultLabel)
        self._contentLayout.addWidget(self._resultView)

    def _onSegmentChanged(self, segment: Optional[ToolCallSegment]) -> None:
        if segment is None:
            self._argsBlock.setCode("")
            self._resultView.setMarkdown("")
            return
        # 仅当数据真的变化时才重设, 避免流式中频繁重建
        if self._argsBlock._code != segment.arguments:
            self._argsBlock.setCode(segment.arguments)
        if self._resultView.markdown() != segment.result:
            self._resultView.setMarkdown(segment.result)

    def appendArgumentsDelta(self, delta: str):
        if not delta:
            return
        super().appendArgumentsDelta(delta)
        if self._segment is not None:
            self._argsBlock.setCode(self._segment.arguments)
        else:
            self._argsBlock.setCode(self._argsBlock._code + delta)

    def appendResultDelta(self, delta: str):
        if not delta:
            return
        # super 已经累积到 segment.result
        super().appendResultDelta(delta)
        # MarkdownView 支持原生增量追加
        self._resultView.appendMarkdown(delta)

    def setCodeBlockMaxVisibleLines(self, n: int):
        super().setCodeBlockMaxVisibleLines(n)
        self._argsBlock.setMaxVisibleLines(n)
        self._resultView.setCodeBlockMaxVisibleLines(n)


# ----------------------------------------------------------------------
# 历史名兼容
# ----------------------------------------------------------------------

ToolCallCard = GenericToolCallCard
