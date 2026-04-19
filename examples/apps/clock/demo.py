# coding:utf-8
"""
Clock 演示

展示内容：
- SplitFluentWindow 多页面应用框架
- 专注时段倒计时
- 秒表计时器
- 导航栏头像与设置项
- 主题与翻译器配置
"""
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition, MessageBox, setTheme, Theme,
    NavigationAvatarWidget, SplitFluentWindow, FluentTranslator,
)
from qfluentwidgets import FluentIcon as FIF

from view.focus_interface import FocusInterface
from view.stop_watch_interface import StopWatchInterface


class Window(SplitFluentWindow):
    """Clock 演示主窗口"""

    def __init__(self):
        super().__init__()
        self.focusInterface = FocusInterface(self)
        self.stopWatchInterface = StopWatchInterface(self)
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        """初始化导航栏"""
        self.addSubInterface(self.focusInterface, FIF.RINGER, '专注时段')
        self.addSubInterface(self.stopWatchInterface, FIF.STOP_WATCH, '秒表')

        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('zhiyiYo', 'resource/images/shoko.png'),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.addItem(
            routeKey='settingInterface',
            icon=FIF.SETTING,
            text='设置',
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setExpandWidth(280)

    def initWindow(self):
        """初始化窗口属性"""
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('Clock - 演示')

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def showMessageBox(self):
        """显示支持作者对话框"""
        w = MessageBox(
            '支持作者',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水。',
            self
        )
        w.yesButton.setText('支持一下')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))


if __name__ == '__main__':
    setTheme(Theme.DARK)

    app = QApplication(sys.argv)

    translator = FluentTranslator()
    app.installTranslator(translator)

    w = Window()
    w.show()
    app.exec()
