# coding:utf-8
"""
AcrylicMenu 演示

展示内容：
- 亚克力右键菜单（AcrylicMenu）
- 子菜单嵌套
- 可勾选菜单项
- 系统托盘菜单（AcrylicSystemTrayMenu）
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
            Action('唱'),
            Action('跳'),
            Action('RAP'),
            Action('篮球', triggered=self.ikun),
        ])
        self.setContextMenu(self.menu)

    def ikun(self):
        """托盘菜单点击响应"""
        w = MessageBox(
            title='提示',
            content='系统托盘菜单项被点击',
            parent=self.parent()
        )
        w.exec()


class Demo(ImageLabel):
    """AcrylicMenu 演示窗口（基于 ImageLabel 展示右键菜单）"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicMenu - 演示')
        self.setImage('resource/chidanta.jpg')
        self.scaledToWidth(500)

        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

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
    w = Demo()
    w.show()
    app.exec()
