# coding:utf-8
"""
Dialog 演示

展示内容：
- 基础对话框显示
- 自定义按钮文本
- 对话框结果处理
- 内容可复制设置
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import Dialog, PrimaryPushButton, PushButton, BodyLabel


class Demo(QWidget):
    """Dialog 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Dialog - 演示')
        self.resize(500, 250)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化对话框触发组件"""
        self.btnBasic = PrimaryPushButton('基础对话框', self)
        self.btnBasic.clicked.connect(self.onShowBasicDialog)

        self.btnCustom = PushButton('自定义按钮', self)
        self.btnCustom.clicked.connect(self.onShowCustomDialog)

        self.statusLabel = BodyLabel('点击按钮打开对话框', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnBasic)
        btnLayout.addWidget(self.btnCustom)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onShowBasicDialog(self):
        """显示基础对话框"""
        w = Dialog(
            '确认删除',
            '删除后文件夹将不再出现在列表中，但不会从磁盘删除。',
            self,
        )
        if w.exec():
            self.statusLabel.setText('用户点击了确认')
        else:
            self.statusLabel.setText('用户点击了取消')

    def onShowCustomDialog(self):
        """显示自定义对话框"""
        w = Dialog(
            '保存更改',
            '文件已修改，是否保存？',
            self,
        )
        w.yesButton.setText('保存')
        w.cancelButton.setText('不保存')
        w.setContentCopyable(True)
        if w.exec():
            self.statusLabel.setText('已选择保存')
        else:
            self.statusLabel.setText('已选择不保存')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
