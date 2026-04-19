# coding:utf-8
"""
MessageDialog / MessageBox 演示

展示内容：
- MessageBox 基础用法
- MessageDialog 风格选择
- 可拖拽对话框
- 点击遮罩关闭
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import MessageDialog, MessageBox, PrimaryPushButton, PushButton, BodyLabel


class Demo(QWidget):
    """MessageDialog 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MessageDialog - 演示')
        self.resize(500, 250)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化消息对话框触发组件"""
        self.btnMessageBox = PrimaryPushButton('MessageBox', self)
        self.btnMessageBox.clicked.connect(self.onShowMessageBox)

        self.btnMessageDialog = PushButton('MessageDialog', self)
        self.btnMessageDialog.clicked.connect(self.onShowMessageDialog)

        self.statusLabel = BodyLabel('点击按钮打开消息对话框', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnMessageBox)
        btnLayout.addWidget(self.btnMessageDialog)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onShowMessageBox(self):
        """显示 MessageBox"""
        w = MessageBox(
            '确认删除',
            '删除后该文件夹将不再出现在列表中。',
            self,
        )
        w.setClosableOnMaskClicked(True)
        w.setDraggable(True)
        if w.exec():
            self.statusLabel.setText('MessageBox: 确认')
        else:
            self.statusLabel.setText('MessageBox: 取消')

    def onShowMessageDialog(self):
        """显示 MessageDialog (Win10 风格)"""
        w = MessageDialog(
            '确认删除',
            '删除后该文件夹将不再出现在列表中。',
            self,
        )
        if w.exec():
            self.statusLabel.setText('MessageDialog: 确认')
        else:
            self.statusLabel.setText('MessageDialog: 取消')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
