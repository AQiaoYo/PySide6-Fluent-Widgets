# coding:utf-8
"""
FolderListDialog 演示

展示内容：
- 文件夹列表对话框
- 添加/移除文件夹路径
- 对话框结果处理
- 动态更新文件夹列表
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    FolderListDialog, PrimaryPushButton, PushButton,
    BodyLabel, LineEdit,
)


class Demo(QWidget):
    """FolderListDialog 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FolderListDialog - 演示')
        self.resize(500, 250)
        self.initWidgets()
        self.initLayout()
        self.folderPaths = []

    def initWidgets(self):
        """初始化文件夹对话框相关组件"""
        # 路径输入
        self.pathEdit = LineEdit(self)
        self.pathEdit.setPlaceholderText('输入文件夹路径后点击添加...')

        # 按钮
        self.btnAdd = PushButton('添加到列表', self)
        self.btnAdd.clicked.connect(self.onAddPath)

        self.btnShowDialog = PrimaryPushButton('打开文件夹列表对话框', self)
        self.btnShowDialog.clicked.connect(self.onShowDialog)

        # 状态显示
        self.statusLabel = BodyLabel('当前无文件夹路径', self)
        self.resultLabel = BodyLabel('', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        inputLayout = QHBoxLayout()
        inputLayout.addWidget(self.pathEdit, 2)
        inputLayout.addWidget(self.btnAdd, 1)
        mainLayout.addLayout(inputLayout)

        mainLayout.addWidget(self.btnShowDialog, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.resultLabel)
        mainLayout.addStretch(1)

    def onAddPath(self):
        """添加路径到列表"""
        path = self.pathEdit.text().strip()
        if path and path not in self.folderPaths:
            self.folderPaths.append(path)
            self.statusLabel.setText(f'已添加 {len(self.folderPaths)} 个路径')
            self.pathEdit.clear()

    def onShowDialog(self):
        """显示文件夹列表对话框"""
        if not self.folderPaths:
            self.folderPaths = ['C:/Users', 'D:/Downloads']

        w = FolderListDialog(
            self.folderPaths,
            '管理本地音乐文件夹',
            '以下文件夹将用于构建您的音乐库：',
            self,
        )
        w.folderChanged.connect(self.onFolderChanged)
        w.exec()

    def onFolderChanged(self, folders):
        """文件夹列表变化时更新"""
        self.folderPaths = folders
        self.resultLabel.setText(f'更新后共 {len(folders)} 个文件夹')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
