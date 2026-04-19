# coding:utf-8
"""
FluentWidget 演示

展示内容：
- FluentWidget 基础用法（无标题栏窗口）
- 主题切换（toggleTheme）
- Mica 效果控制
- 自定义背景色
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QVBoxLayout

from qfluentwidgets import FluentWidget, toggleTheme, PushButton, BodyLabel
from qfluentwidgets import FluentIcon as FIF


class Window(FluentWidget):
    """FluentWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FluentWidget - 演示')
        self.initWidgets()
        self.initLayout()
        self.initWindow()

    def initWidgets(self):
        """初始化组件"""
        self.label = BodyLabel('FluentWidget 是无标题栏窗口基类', self)
        self.btnTheme = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.btnTheme.clicked.connect(toggleTheme)

    def initLayout(self):
        """初始化布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        layout.addWidget(self.label, 0, Qt.AlignCenter)
        layout.addWidget(self.btnTheme, 0, Qt.AlignCenter)

    def initWindow(self):
        """初始化窗口"""
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
