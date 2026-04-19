# coding: utf-8
"""堆叠部件"""

from PySide6.QtCore import Qt, Signal, QEasingCurve
from PySide6.QtWidgets import QFrame, QHBoxLayout, QAbstractScrollArea

from ..components.widgets.stacked_widget import PopUpAniStackedWidget, EntranceTransitionStackedWidget



class StackedWidget(QFrame):
    """堆叠部件"""

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        """初始化堆叠部件

        Args:
            parent: 父部件，默认为 None
        """
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.view = PopUpAniStackedWidget(self)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view)

        self.view.currentChanged.connect(self.currentChanged)
        self.setAttribute(Qt.WA_StyledBackground)

    def isAnimationEnabled(self) -> bool:
        """获取动画是否已启用

        Returns:
            动画是否已启用
        """
        return self.view.isAnimationEnabled

    def setAnimationEnabled(self, isEnabled: bool):
        """设置是否启用弹出动画

        Args:
            isEnabled: 是否启用动画
        """
        self.view.setAnimationEnabled(isEnabled)

    def addWidget(self, widget):
        """将部件添加到视图

        Args:
            widget: 要添加的部件
        """
        self.view.addWidget(widget)

    def removeWidget(self, widget):
        """从视图中移除部件

        Args:
            widget: 要移除的部件
        """
        self.view.removeWidget(widget)

    def widget(self, index: int):
        """获取指定索引处的部件

        Args:
            index: 部件索引

        Returns:
            指定索引处的部件
        """
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=True):
        """设置当前部件

        Args:
            widget: 要设置为当前的部件
            popOut: 是否使用弹出动画，默认为 True
        """
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().setValue(0)

        if not popOut:
            self.view.setCurrentWidget(widget, duration=300)
        else:
            self.view.setCurrentWidget(
                widget, True, False, 300, QEasingCurve.Type.InQuad)

    def setCurrentIndex(self, index, popOut=True):
        """设置当前索引

        Args:
            index: 目标索引
            popOut: 是否使用弹出动画，默认为 True
        """
        self.setCurrentWidget(self.view.widget(index), popOut)

    def currentIndex(self):
        """获取当前索引

        Returns:
            当前索引
        """
        return self.view.currentIndex()

    def currentWidget(self):
        """获取当前部件

        Returns:
            当前部件
        """
        return self.view.currentWidget()

    def indexOf(self, widget):
        """获取部件的索引

        Args:
            widget: 目标部件

        Returns:
            部件的索引
        """
        return self.view.indexOf(widget)

    def count(self):
        """获取部件数量

        Returns:
            部件数量
        """
        return self.view.count()