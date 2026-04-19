# coding:utf-8
"""
CommandBar 演示

展示内容：
- CommandBar 命令栏
- CommandBarView 弹出式命令栏
- 下拉按钮菜单
- 隐藏操作项
- 工具按钮样式切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    FluentIcon, TransparentDropDownPushButton, RoundMenu, CommandBar, Action,
    setFont, CommandBarView, Flyout, FlyoutAnimationType,
    ImageLabel, ToolButton, PushButton, BodyLabel,
)
from qframelesswindow import FramelessWindow, StandardTitleBar


class Demo1(QWidget):
    """CommandBar 演示窗口 1"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CommandBar - 演示 1')
        self.resize(400, 60)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化命令栏"""
        self.commandBar = CommandBar(self)
        self.dropDownButton = self.createDropDownButton()

        # 工具按钮样式
        self.commandBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.addButton(FluentIcon.ADD, '添加')
        self.commandBar.addSeparator()

        self.isEdit = False
        self.commandBar.addAction(Action(FluentIcon.EDIT, '编辑', triggered=self.onEdit, checkable=True))
        self.addButton(FluentIcon.COPY, '复制')
        self.addButton(FluentIcon.SHARE, '分享')

        # 自定义控件
        self.commandBar.addWidget(self.dropDownButton)

        # 隐藏操作项
        self.commandBar.addHiddenAction(Action(FluentIcon.SCROLL, '排序', triggered=lambda: print('排序')))
        self.commandBar.addHiddenAction(Action(FluentIcon.SETTING, '设置', shortcut='Ctrl+S'))

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.commandBar, 0)

    def addButton(self, icon, text):
        """添加按钮"""
        action = Action(icon, text, self)
        action.triggered.connect(lambda: print(text))
        self.commandBar.addAction(action)

    def onEdit(self):
        """编辑模式切换"""
        self.isEdit = not self.isEdit
        print('进入编辑模式' if self.isEdit else '退出编辑模式')

    def createDropDownButton(self):
        """创建下拉按钮"""
        button = TransparentDropDownPushButton('菜单', self, FluentIcon.MENU)
        button.setFixedHeight(34)
        setFont(button, 12)

        menu = RoundMenu(parent=self)
        menu.addActions([
            Action(FluentIcon.COPY, '复制'),
            Action(FluentIcon.CUT, '剪切'),
            Action(FluentIcon.PASTE, '粘贴'),
            Action(FluentIcon.CANCEL, '取消'),
            Action('全选'),
        ])
        button.setMenu(menu)
        return button


class Demo2(FramelessWindow):
    """CommandBar 演示窗口 2 — 图片点击弹出命令栏"""

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))
        self.setWindowTitle('CommandBar - 演示 2')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.imageLabel = ImageLabel('resource/pink_memory.jpg')
        self.imageLabel.scaledToWidth(380)
        self.imageLabel.clicked.connect(self.showCommandBar)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 80, 0, 0)
        mainLayout.addWidget(self.imageLabel)
        self.setStyleSheet('Demo2{background: white}')

    def showCommandBar(self):
        """显示命令栏弹出层"""
        view = CommandBarView(self)

        view.addAction(Action(FluentIcon.SHARE, '分享'))
        view.addAction(Action(FluentIcon.SAVE, '保存'))
        view.addAction(Action(FluentIcon.DELETE, '删除'))

        view.addHiddenAction(Action(FluentIcon.APPLICATION, '应用', shortcut='Ctrl+A'))
        view.addHiddenAction(Action(FluentIcon.SETTING, '设置', shortcut='Ctrl+S'))
        view.resizeToSuitableWidth()

        Flyout.make(view, self.imageLabel, self, FlyoutAnimationType.FADE_IN)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w1 = Demo1()
    w1.show()
    w2 = Demo2()
    w2.show()
    app.exec()
