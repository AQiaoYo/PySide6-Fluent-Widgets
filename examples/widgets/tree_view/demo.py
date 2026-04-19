# coding:utf-8
"""
TreeView 演示

展示内容：
- 文件系统模型绑定
- 自定义边框样式
- 树形数据展开与折叠
- 选中项变化响应
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QFileSystemModel,
)

from qfluentwidgets import TreeView, BodyLabel, PushButton


class Demo(QWidget):
    """TreeView 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TreeView - 演示')
        self.resize(600, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化树形视图组件"""
        # 文件系统树形视图
        self.treeView = TreeView(self)
        self.model = QFileSystemModel()
        self.model.setRootPath('.')
        self.treeView.setModel(self.model)

        # 自定义边框
        self.treeView.setBorderVisible(True)
        self.treeView.setBorderRadius(8)

        # 选中变化信号
        self.treeView.selectionModel().currentChanged.connect(self.onSelectionChanged)

        # 控制按钮
        self.btnExpand = PushButton('展开全部', self)
        self.btnExpand.clicked.connect(self.treeView.expandAll)

        self.btnCollapse = PushButton('折叠全部', self)
        self.btnCollapse.clicked.connect(self.treeView.collapseAll)

        self.statusLabel = BodyLabel('请在左侧选择文件或文件夹', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        # 左侧树形视图
        mainLayout.addWidget(self.treeView, 2)

        # 右侧控制面板
        rightLayout = QVBoxLayout()
        rightLayout.setSpacing(12)
        rightLayout.addWidget(self.btnExpand)
        rightLayout.addWidget(self.btnCollapse)
        rightLayout.addStretch(1)
        rightLayout.addWidget(self.statusLabel)
        mainLayout.addLayout(rightLayout, 1)

    def onSelectionChanged(self, current, previous):
        """选中项变化时更新状态"""
        if current.isValid():
            path = self.model.filePath(current)
            self.statusLabel.setText(f'选中: {path}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
