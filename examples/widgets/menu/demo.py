# coding:utf-8
"""
Menu 演示

展示内容：
- RoundMenu 圆角菜单
- 子菜单嵌套
- 可勾选菜单项
- 菜单动画效果
- 快捷键设置
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel

from qfluentwidgets import (
    RoundMenu, Action, MenuAnimationType, setTheme, Theme,
)
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """Menu 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Menu - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.label = QLabel('在此区域点击鼠标右键', self)
        self.label.setAlignment(Qt.AlignCenter)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.label)
        self.setStyleSheet('Demo{background: white} QLabel{font-size: 20px}')

    def contextMenuEvent(self, e):
        """右键显示菜单"""
        menu = RoundMenu(parent=self)

        # 基础操作
        menu.addAction(Action(FIF.COPY, '复制'))
        menu.addAction(Action(FIF.CUT, '剪切'))
        menu.actions()[0].setCheckable(True)
        menu.actions()[0].setChecked(True)

        # 子菜单
        submenu = RoundMenu("添加到", self)
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
        menu.addAction(QAction('全选', shortcut='Ctrl+A'))

        # 插入操作
        menu.insertAction(
            menu.actions()[-1], Action(FIF.SETTING, '设置', shortcut='Ctrl+S'))
        menu.insertActions(
            menu.actions()[-1],
            [Action(FIF.HELP, '帮助', shortcut='Ctrl+H'),
             Action(FIF.FEEDBACK, '反馈', shortcut='Ctrl+F')]
        )
        menu.actions()[-2].setCheckable(True)
        menu.actions()[-2].setChecked(True)

        # 显示菜单
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
