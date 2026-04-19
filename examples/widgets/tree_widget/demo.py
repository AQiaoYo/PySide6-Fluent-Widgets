# coding:utf-8
"""
TreeWidget 演示

展示内容：
- TreeWidget 树形控件
- TreeView 树形视图（文件系统模型）
- 节点展开/折叠
- 节点点击信号
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QTreeWidgetItem, QHBoxLayout, QFileSystemModel

from qfluentwidgets import TreeWidget, TreeView, BodyLabel


class Demo(QWidget):
    """TreeWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TreeWidget - 演示')
        self.resize(700, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化树形控件"""
        self.statusLabel = BodyLabel('请点击树节点查看信息', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # TreeWidget - 自定义数据树
        self.treeWidget = TreeWidget(self)
        self.treeWidget.setHeaderLabels(['名称', '类型', '描述'])
        self.treeWidget.setColumnWidth(0, 200)
        self.treeWidget.setColumnWidth(1, 100)

        # 构建示例数据树
        root = QTreeWidgetItem(['项目结构', '根节点', '演示项目'])
        root.addChildren([
            QTreeWidgetItem(['src', '文件夹', '源代码目录']),
            QTreeWidgetItem(['docs', '文件夹', '文档目录']),
            QTreeWidgetItem(['tests', '文件夹', '测试目录']),
        ])

        src = root.child(0)
        src.addChildren([
            QTreeWidgetItem(['main.py', '文件', '程序入口']),
            QTreeWidgetItem(['utils.py', '文件', '工具函数']),
            QTreeWidgetItem(['config.py', '文件', '配置文件']),
        ])

        docs = root.child(1)
        docs.addChildren([
            QTreeWidgetItem(['README.md', '文件', '项目说明']),
            QTreeWidgetItem(['API.md', '文件', '接口文档']),
        ])

        self.treeWidget.addTopLevelItem(root)
        self.treeWidget.expandAll()

        # 信号连接
        self.treeWidget.itemClicked.connect(self.onItemClicked)
        self.treeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)

        # TreeView - 文件系统视图
        self.treeView = TreeView(self)
        self.fileModel = QFileSystemModel(self)
        self.fileModel.setRootPath('')
        self.treeView.setModel(self.fileModel)
        self.treeView.setColumnWidth(0, 200)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.statusLabel)

        treeLayout = QHBoxLayout()
        treeLayout.setSpacing(16)
        treeLayout.addWidget(self.treeWidget, 1)
        treeLayout.addWidget(self.treeView, 1)
        mainLayout.addLayout(treeLayout, 1)

    def onItemClicked(self, item: QTreeWidgetItem, column: int):
        """节点点击事件"""
        text = item.text(0)
        itemType = item.text(1)
        self.statusLabel.setText(f'选中: {text} ({itemType})')

    def onItemDoubleClicked(self, item: QTreeWidgetItem, column: int):
        """节点双击事件"""
        text = item.text(0)
        desc = item.text(2)
        self.statusLabel.setText(f'双击: {text} — {desc}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
