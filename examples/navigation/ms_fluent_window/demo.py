# coding:utf-8
"""
MSFluentWindow 演示

展示内容：
- MSFluentWindow 微软风格导航窗口
- 底部导航栏
- 选中/未选中图标状态
- 不可选中的帮助项
"""
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    NavigationItemPosition, MessageBox, MSFluentWindow,
    SubtitleLabel, setFont,
)
from qfluentwidgets import FluentIcon as FIF


class Widget(QWidget):
    """子界面占位组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(MSFluentWindow):
    """MSFluentWindow 导航窗口"""

    def __init__(self):
        super().__init__()
        self.initInterfaces()
        self.initNavigation()
        self.initWindow()

    def initInterfaces(self):
        """初始化子界面"""
        self.homeInterface = Widget('Home Interface', self)
        self.appInterface = Widget('Application Interface', self)
        self.videoInterface = Widget('Video Interface', self)
        self.libraryInterface = Widget('Library Interface', self)

    def initNavigation(self):
        """初始化导航"""
        # 顶部导航项（带选中/未选中两种图标）
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频')

        # 底部导航项
        self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, '库', FIF.LIBRARY_FILL, NavigationItemPosition.BOTTOM)

        # 不可选中的帮助项
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        """初始化窗口"""
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('MSFluentWindow - 演示')

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def showMessageBox(self):
        """显示帮助对话框"""
        w = MessageBox(
            'MSFluentWindow',
            'MSFluentWindow 提供微软风格的底部导航栏，支持选中/未选中两种图标状态。',
            self
        )
        w.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
