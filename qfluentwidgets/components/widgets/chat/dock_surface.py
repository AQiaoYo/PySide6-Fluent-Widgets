# coding: utf-8
"""Dock 面板基类 (DockSurface)

提供"附着在输入框上方"的面板基础结构. 所有 Dock 组件 (PermissionDock /
QuestionDock / FollowupDock / RevertDock / TodoDock) 都继承此基类.

视觉特征:
- 与输入框共圆角 (5px), 1px 边框
- 可折叠 (header + content)
- 默认 hide, 由宿主 (AgentChatPanel) 在需要时 show

布局模型:
    DockSurface
      ├─ _header (QFrame, 固定高度, 可点击折叠)
      └─ _content (QFrame, 可折叠区域)

子类职责:
    1. 覆盖 ``_buildHeader(layout: QHBoxLayout)`` 填充 header 内容
    2. 覆盖 ``_buildContent(layout: QVBoxLayout)`` 填充 content 内容
    3. 可选覆盖 ``_headerHeight() -> int`` 调整 header 高度 (默认 36)
"""

from typing import Optional

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from .._clickable import ClickableFrame


__all__ = ['DockSurface']


class DockSurface(QFrame):
    """Dock 面板基类.

    Signals:
        visibilityChanged(bool): 面板显示/隐藏时发出
        collapsed(bool):         折叠状态变化时发出 (True=已折叠)

    构造函数:
        DockSurface(parent: QWidget = None, collapsible: bool = True)
    """

    visibilityChanged = Signal(bool)
    collapsed = Signal(bool)

    _CHEVRON_SIZE = 12

    def __init__(self, parent: Optional[QWidget] = None,
                 collapsible: bool = True):
        super().__init__(parent)
        self.setObjectName("dockSurface")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        self._collapsible = collapsible
        self._isCollapsed = False

        self._setupUi()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # UI 骨架
    # ------------------------------------------------------------------

    def _setupUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(0)

        # ---- header ----
        self._header = ClickableFrame(self)
        self._header.setObjectName("dockHeader")
        self._header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._header.setFixedHeight(self._headerHeight())
        if self._collapsible:
            self._header.clicked.connect(self.toggleCollapse)

        self._headerLayout = QHBoxLayout(self._header)
        self._headerLayout.setContentsMargins(16, 0, 12, 0)
        self._headerLayout.setSpacing(8)

        # 子类填充 header 内容
        self._buildHeader(self._headerLayout)

        # 折叠箭头 (可选)
        if self._collapsible:
            self._chevronLabel = QLabel(self._header)
            self._chevronLabel.setObjectName("dockChevron")
            self._chevronLabel.setFixedSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE)
            self._headerLayout.addWidget(
                self._chevronLabel, 0, Qt.AlignmentFlag.AlignVCenter,
            )
            self._updateChevron()

        # ---- content ----
        self._content = QFrame(self)
        self._content.setObjectName("dockContent")
        self._content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._contentLayout = QVBoxLayout(self._content)
        self._contentLayout.setContentsMargins(16, 10, 16, 14)
        self._contentLayout.setSpacing(8)

        # 子类填充 content 内容
        self._buildContent(self._contentLayout)

        rootLayout.addWidget(self._header)
        rootLayout.addWidget(self._content)

    # ------------------------------------------------------------------
    # 子类覆盖点
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        """header 高度, 子类可覆盖."""
        return 40

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        """子类覆盖: 往 header layout 里添加 widget.

        layout 已设好 margins 和 spacing, 子类只需 addWidget.
        注意: 如果 collapsible=True, 基类会在 layout 末尾追加 chevron.
        """
        pass

    def _buildContent(self, layout: QVBoxLayout) -> None:
        """子类覆盖: 往 content layout 里添加 widget."""
        pass

    # ------------------------------------------------------------------
    # 折叠 API
    # ------------------------------------------------------------------

    def toggleCollapse(self) -> None:
        self.setCollapsed(not self._isCollapsed)

    def setCollapsed(self, collapsed: bool) -> None:
        if not self._collapsible:
            return
        if collapsed == self._isCollapsed:
            return
        self._isCollapsed = bool(collapsed)
        self._content.setVisible(not self._isCollapsed)
        self._updateChevron()
        self.collapsed.emit(self._isCollapsed)

    def isCollapsed(self) -> bool:
        return self._isCollapsed

    # ------------------------------------------------------------------
    # 显隐
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self.visibilityChanged.emit(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.visibilityChanged.emit(False)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _updateChevron(self) -> None:
        if not self._collapsible:
            return
        icon = (
            FluentIcon.CHEVRON_RIGHT_MED if self._isCollapsed
            else FluentIcon.CHEVRON_DOWN_MED
        )
        self._chevronLabel.setPixmap(
            icon.icon().pixmap(QSize(self._CHEVRON_SIZE, self._CHEVRON_SIZE))
        )

    def paintEvent(self, e):
        """自绘圆角卡片背景 + 边框, 适配亮色/暗色主题."""
        from ....common.style_sheet import isDarkTheme
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # 背景
        if isDarkTheme():
            bg = QColor(44, 44, 48, 250)
            border = QColor(255, 255, 255, 20)
        else:
            bg = QColor(255, 255, 255, 250)
            border = QColor(0, 0, 0, 20)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 8.0

        # 填充背景
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, radius, radius)

        # 边框
        pen = QPen(border, 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
