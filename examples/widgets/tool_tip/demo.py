# coding:utf-8
"""
ToolTip 演示

展示内容：
- ToolTip 工具提示
- ToolTipFilter 事件过滤器
- 不同显示位置（上/下/右）
- 显示时长设置
- 点击打开链接
"""
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import ToolTip, ToolTipFilter, PushButton, ToolTipPosition, setTheme, Theme


class Demo(QWidget):
    """ToolTip 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ToolTip - 演示')
        self.resize(480, 240)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化按钮与工具提示"""
        self.button1 = PushButton('悬停上方', self)
        self.button2 = PushButton('悬停下方', self)
        self.button3 = PushButton('悬停右侧', self)

        self.button1.setToolTip('这是显示在上方的工具提示')
        self.button2.setToolTip('这是显示在下方的工具提示')
        self.button3.setToolTip('这是显示在右侧的工具提示')
        self.button1.setToolTipDuration(1000)

        self.button1.installEventFilter(ToolTipFilter(self.button1, 0, ToolTipPosition.TOP))
        self.button2.installEventFilter(ToolTipFilter(self.button2, 0, ToolTipPosition.BOTTOM))
        self.button3.installEventFilter(ToolTipFilter(self.button3, 300, ToolTipPosition.RIGHT))

        self.button1.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://qfluentwidgets.com')))
        self.button2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/zhiyiYo/PyQt-Fluent-Widgets')))
        self.button3.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.youtube.com')))

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(24, 24, 24, 24)
        mainLayout.setSpacing(16)
        mainLayout.addWidget(self.button1)
        mainLayout.addWidget(self.button2)
        mainLayout.addWidget(self.button3)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
