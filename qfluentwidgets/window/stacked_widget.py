# coding: utf-8
from PySide6.QtCore import Qt, Signal, QEasingCurve
from PySide6.QtWidgets import QFrame, QHBoxLayout, QAbstractScrollArea

from ..components.widgets.stacked_widget import PopUpAniStackedWidget, EntranceTransitionStackedWidget



class StackedWidget(QFrame):
    """ 堆叠部件 """

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.view = PopUpAniStackedWidget(self)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.view)

        self.view.currentChanged.connect(self.currentChanged)
        self.setAttribute(Qt.WA_StyledBackground)

    def isAnimationEnabled(self) -> bool:
        return self.view.isAnimationEnabled

    def setAnimationEnabled(self, isEnabled: bool):
        """设置 是否 pop 动画 is 已启用"""
        self.view.setAnimationEnabled(isEnabled)

    def addWidget(self, widget):
        """ 将部件添加到视图 """
        self.view.addWidget(widget)

    def removeWidget(self, widget):
        """ 从视图移除部件 """
        self.view.removeWidget(widget)

    def widget(self, index: int):
        return self.view.widget(index)

    def setCurrentWidget(self, widget, popOut=True):
        if isinstance(widget, QAbstractScrollArea):
            widget.verticalScrollBar().setValue(0)

        if not popOut:
            self.view.setCurrentWidget(widget, duration=300)
        else:
            self.view.setCurrentWidget(
                widget, True, False, 300, QEasingCurve.Type.InQuad)

    def setCurrentIndex(self, index, popOut=True):
        self.setCurrentWidget(self.view.widget(index), popOut)

    def currentIndex(self):
        return self.view.currentIndex()

    def currentWidget(self):
        return self.view.currentWidget()

    def indexOf(self, widget):
        return self.view.indexOf(widget)

    def count(self):
        return self.view.count()
