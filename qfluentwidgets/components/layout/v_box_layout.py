# coding: utf-8
from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget


class VBoxLayout(QVBoxLayout):
    """ 垂直盒布局 """

    def __init__(self, parent):
        super().__init__(parent)
        self.widgets = []

    def addWidgets(self, widgets: List[QWidget], stretch=0, alignment=Qt.AlignTop):
        """ 将部件添加到布局 """
        for widget in widgets:
            self.addWidget(widget, stretch, alignment)

    def addWidget(self, widget: QWidget, stretch=0, alignment=Qt.AlignTop):
        """ 将部件添加到布局 """
        super().addWidget(widget, stretch, alignment)
        self.widgets.append(widget)
        widget.show()

    def removeWidget(self, widget: QWidget):
        """ 从布局 but not delete it移除部件 """
        super().removeWidget(widget)
        self.widgets.remove(widget)

    def deleteWidget(self, widget: QWidget):
        """ 从布局 和 delete it移除部件 """
        self.removeWidget(widget)
        widget.hide()
        widget.deleteLater()

    def removeAllWidget(self):
        """ 移除布局中的全部部件 """
        for widget in self.widgets:
            super().removeWidget(widget)

        self.widgets.clear()
