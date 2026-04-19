# coding:utf-8
"""
SystemTrayMenu 演示

展示内容：
- SystemTrayIcon 系统托盘图标
- SystemTrayMenu 托盘菜单
- 菜单项点击事件
- 消息框交互
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QVBoxLayout, QLabel

from qfluentwidgets import Action, SystemTrayMenu, MessageBox, BodyLabel


class SystemTrayIcon(QSystemTrayIcon):
    """自定义系统托盘图标"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setIcon(parent.windowIcon())
        self.setToolTip('SystemTrayMenu 演示')

        # 创建托盘菜单
        self.menu = SystemTrayMenu(parent=parent)
        self.menu.addActions([
            Action('显示窗口', triggered=parent.show),
            Action('隐藏窗口', triggered=parent.hide),
            Action('退出', triggered=self.onExit),
        ])
        self.setContextMenu(self.menu)

    def onExit(self):
        """退出应用"""
        QApplication.quit()


class Demo(QWidget):
    """SystemTrayMenu 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SystemTrayMenu - 演示')
        self.resize(400, 200)
        self.initLayout()

        self.label = BodyLabel('系统托盘图标已创建\\n右键点击托盘图标查看菜单', self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        # 创建并显示托盘图标
        self.systemTrayIcon = SystemTrayIcon(self)
        self.systemTrayIcon.show()

    def initLayout(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = Demo()
    w.show()
    app.exec()
