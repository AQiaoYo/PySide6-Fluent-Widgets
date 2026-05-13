# coding: utf-8
"""工作流缩放控制组件

提供左下角的缩放控制按钮组, 包含放大, 缩小, 适应画布, 重置缩放
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame

from ....common.icon import FluentIcon as FIF
from ....common.style_sheet import isDarkTheme
from ..button import TransparentToolButton


__all__ = ['WorkflowZoomControl']


class WorkflowZoomControl(QFrame):
    """工作流缩放控制

    左下角的缩放控制按钮组

    Signals:
        zoomInClicked:  放大按钮点击
        zoomOutClicked: 缩小按钮点击
        fitClicked:     适应画布按钮点击
        resetClicked:   重置缩放按钮点击
    """

    zoomInClicked = Signal()
    zoomOutClicked = Signal()
    fitClicked = Signal()
    resetClicked = Signal()

    def __init__(self, parent: QWidget = None):
        """初始化缩放控制

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self._initUi()

    def _initUi(self):
        """初始化界面"""
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(4, 4, 4, 4)
        self.vBoxLayout.setSpacing(2)

        self.zoomInButton = TransparentToolButton(FIF.ADD, self)
        self.zoomOutButton = TransparentToolButton(FIF.REMOVE, self)
        self.fitButton = TransparentToolButton(FIF.FIT_PAGE, self)
        self.resetButton = TransparentToolButton(FIF.FULL_SCREEN, self)

        for btn in [self.zoomInButton, self.zoomOutButton, self.fitButton, self.resetButton]:
            btn.setFixedSize(32, 32)
            self.vBoxLayout.addWidget(btn)

        # Connect signals
        self.zoomInButton.clicked.connect(self.zoomInClicked)
        self.zoomOutButton.clicked.connect(self.zoomOutClicked)
        self.fitButton.clicked.connect(self.fitClicked)
        self.resetButton.clicked.connect(self.resetClicked)

        self.setFixedSize(40, 4 + 32 * 4 + 2 * 3 + 4)

    def paintEvent(self, e):
        """绘制背景"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        bgColor = QColor(43, 43, 43, 200) if isDark else QColor(255, 255, 255, 220)
        borderColor = QColor(60, 60, 60) if isDark else QColor(210, 210, 210)

        painter.setPen(borderColor)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
