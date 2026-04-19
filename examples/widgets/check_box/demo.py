# coding:utf-8
"""
CheckBox 演示

展示内容：
- 两态复选框（勾选/未勾选）
- 三态复选框（勾选/部分勾选/未勾选）
- 禁用状态的复选框
- 信号槽连接获取状态变化
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import CheckBox, BodyLabel


class Demo(QWidget):
    """CheckBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CheckBox - 演示')
        self.resize(400, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化复选框组件"""
        # 两态复选框
        self.checkBox1 = CheckBox('两态复选框', self)
        self.checkBox1.stateChanged.connect(self.onStateChanged)

        # 三态复选框
        self.checkBox2 = CheckBox('三态复选框', self)
        self.checkBox2.setTristate(True)
        self.checkBox2.stateChanged.connect(self.onStateChanged)

        # 禁用状态
        self.checkBox3 = CheckBox('禁用 - 已勾选', self)
        self.checkBox3.setChecked(True)
        self.checkBox3.setEnabled(False)

        self.checkBox4 = CheckBox('禁用 - 未勾选', self)
        self.checkBox4.setEnabled(False)

        # 状态显示标签
        self.statusLabel = BodyLabel('等待操作...', self)

    def initLayout(self):
        """初始化布局"""
        vLayout = QVBoxLayout(self)
        vLayout.setSpacing(16)
        vLayout.setContentsMargins(30, 30, 30, 30)

        vLayout.addWidget(self.checkBox1)
        vLayout.addWidget(self.checkBox2)
        vLayout.addWidget(self.checkBox3)
        vLayout.addWidget(self.checkBox4)
        vLayout.addStretch(1)
        vLayout.addWidget(self.statusLabel)

    def onStateChanged(self, state):
        """状态变化时更新显示"""
        sender = self.sender()
        names = {0: '未勾选', 1: '部分勾选', 2: '已勾选'}
        self.statusLabel.setText(f'{sender.text()}: {names.get(state, "未知")}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
