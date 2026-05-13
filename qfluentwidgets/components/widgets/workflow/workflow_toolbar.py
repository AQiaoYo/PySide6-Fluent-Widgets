# coding: utf-8
"""工作流底部工具栏

使用 CommandBarView 提供浮动胶囊式工具栏, 居中悬浮在画布底部
"""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget

from ....common.icon import FluentIcon as FIF, Action
from ..command_bar import CommandBarView


__all__ = ['WorkflowToolBar']


class WorkflowToolBar(CommandBarView):
    """工作流底部工具栏

    继承 CommandBarView, 预置保存/撤销/重做/预览/禁用工作流等操作

    Signals:
        saveClicked:    保存按钮点击
        undoClicked:    撤销按钮点击
        redoClicked:    重做按钮点击
        previewClicked: 预览按钮点击
        toggleClicked:  启用/禁用按钮点击
    """

    saveClicked = Signal()
    undoClicked = Signal()
    redoClicked = Signal()
    previewClicked = Signal()
    toggleClicked = Signal(bool)

    def __init__(self, parent: QWidget = None):
        """初始化工具栏

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self._isWorkflowEnabled = True
        self._initActions()

    def _initActions(self):
        """初始化操作按钮"""
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setButtonTight(False)
        self.setIconSize(QSize(16, 16))

        # Add actions
        self.saveAction = Action(FIF.SAVE, self.tr('保存'), self)
        self.undoAction = Action(FIF.RETURN, self.tr('撤销'), self)
        self.redoAction = Action(FIF.SYNC, self.tr('重做'), self)
        self.previewAction = Action(FIF.PLAY, self.tr('预览活动'), self)
        self.toggleAction = Action(FIF.POWER_BUTTON, self.tr('禁用工作流'), self)

        self.addAction(self.saveAction)
        self.addAction(self.undoAction)
        self.addAction(self.redoAction)
        self.addSeparator()
        self.addAction(self.previewAction)
        self.addSeparator()
        self.addAction(self.toggleAction)

        # Resize with extra padding to prevent right-side clipping
        self.resizeToSuitableWidth()
        self.setFixedWidth(self.suitableWidth() + 12)

        # Connect signals
        self.saveAction.triggered.connect(self.saveClicked)
        self.undoAction.triggered.connect(self.undoClicked)
        self.redoAction.triggered.connect(self.redoClicked)
        self.previewAction.triggered.connect(self.previewClicked)
        self.toggleAction.triggered.connect(self._onToggleClicked)

    def _onToggleClicked(self):
        """切换工作流启用/禁用状态"""
        self._isWorkflowEnabled = not self._isWorkflowEnabled

        if self._isWorkflowEnabled:
            self.toggleAction.setText(self.tr('禁用工作流'))
        else:
            self.toggleAction.setText(self.tr('启用工作流'))

        self.resizeToSuitableWidth()
        self.setFixedWidth(self.suitableWidth() + 12)
        self.toggleClicked.emit(self._isWorkflowEnabled)

    def isWorkflowEnabled(self) -> bool:
        """获取工作流启用状态

        Returns:
            是否启用
        """
        return self._isWorkflowEnabled

    def setWorkflowEnabled(self, enabled: bool):
        """设置工作流启用状态

        Args:
            enabled: 是否启用
        """
        self._isWorkflowEnabled = enabled
        if enabled:
            self.toggleAction.setText(self.tr('禁用工作流'))
        else:
            self.toggleAction.setText(self.tr('启用工作流'))

        self.resizeToSuitableWidth()
        self.setFixedWidth(self.suitableWidth() + 12)
