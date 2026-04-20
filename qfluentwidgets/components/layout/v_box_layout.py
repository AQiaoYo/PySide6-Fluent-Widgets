# coding: utf-8
"""提供垂直盒式布局组件

当需要纵向线性排列按钮、标签、卡片等控件时，可使用本模块中的 VBoxLayout 来简化界面构建流程
"""

from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget


class VBoxLayout(QVBoxLayout):
    """垂直盒式布局，用于纵向排列控件
    
    适用于需要自上而下依次放置多个控件的场景，常用于侧边栏、设置面板等纵向界面的快速搭建
    """

    def __init__(self, parent):
        """初始化布局

        Args:
            parent: 父级部件
        """
        super().__init__(parent)
        self.widgets = []

    def addWidgets(self, widgets: List[QWidget], stretch=0, alignment=Qt.AlignTop):
        """批量添加部件到布局

        Args:
            widgets: 要添加的部件列表
            stretch: 伸展因子
            alignment: 对齐方式
        """
        for widget in widgets:
            self.addWidget(widget, stretch, alignment)

    def addWidget(self, widget: QWidget, stretch=0, alignment=Qt.AlignTop):
        """添加部件到布局

        Args:
            widget: 要添加的部件
            stretch: 伸展因子
            alignment: 对齐方式
        """
        super().addWidget(widget, stretch, alignment)
        self.widgets.append(widget)
        widget.show()

    def removeWidget(self, widget: QWidget):
        """从布局中移除部件（不删除）

        Args:
            widget: 要移除的部件
        """
        super().removeWidget(widget)
        self.widgets.remove(widget)

    def deleteWidget(self, widget: QWidget):
        """从布局中移除并删除部件

        Args:
            widget: 要移除并删除的部件
        """
        self.removeWidget(widget)
        widget.hide()
        widget.deleteLater()

    def removeAllWidget(self):
        """移除布局中的所有部件"""
        for widget in self.widgets:
            super().removeWidget(widget)

        self.widgets.clear()