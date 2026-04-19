# coding:utf-8
"""
AcrylicMenu 演示

展示内容：
- AcrylicMenu 亚克力右键菜单
- 子菜单嵌套
- 可勾选菜单项
- AcrylicSystemTrayMenu 亚克力系统托盘菜单
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from qfluentwidgets import (
    MessageBox, ImageLabel, Action, MenuAnimationType,
    AcrylicMenu, AcrylicSystemTrayMenu,
)
from qfluentwidgets import FluentIcon as FIF


class SystemTrayIcon(QSystemTrayIcon):
    """系统托盘图标（使用 AcrylicSystemTrayMenu）"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setIcon(parent.windowIcon())
        self.setToolTip('AcrylicMenu 演示')

        self.menu = AcrylicSystemTrayMenu(parent=parent)
        self.menu.addActions([
            Action('显示窗口', triggered=parent.show),
            Action('隐藏窗口', triggered=parent.hide),
            Action('退出', triggered=self.onExit),
        ])
        self.setContextMenu(self.menu)

    def onExit(self):
        """退出应用"""
        QApplication.quit()


class Demo(ImageLabel):
    """AcrylicMenu 演示窗口（基于 ImageLabel 展示右键菜单）"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicMenu - 演示')
        self.setImage('resource/chidanta.jpg')
        self.scaledToWidth(500)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        # 创建并显示托盘图标
        self.systemTrayIcon = SystemTrayIcon(self)
        self.systemTrayIcon.show()

    def contextMenuEvent(self, e):
        """右键显示亚克力菜单"""
        menu = AcrylicMenu(parent=self)

        # 基础操作
        menu.addAction(Action(FIF.COPY, '复制'))
        menu.addAction(Action(FIF.CUT, '剪切'))
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)

        # 子菜单
        submenu = AcrylicMenu('添加到', self)
        submenu.setIcon(FIF.ADD)
        submenu.addActions([
            Action(FIF.VIDEO, '视频'),
            Action(FIF.MUSIC, '音乐'),
        ])
        menu.addMenu(submenu)

        # 更多操作
        menu.addActions([
            Action(FIF.PASTE, '粘贴'),
            Action(FIF.CANCEL, '撤销')
        ])

        # 分隔线
        menu.addSeparator()

        # 插入操作
        menu.insertAction(
            menu.actions()[-1], Action(FIF.SETTING, '设置', shortcut='Ctrl+S'))

        # 在光标位置显示菜单（带动画）
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = Demo()
    w.show()
    app.exec()
