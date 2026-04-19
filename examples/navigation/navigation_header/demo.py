# coding: utf-8
"""
Navigation Header 演示

展示内容：
- NavigationInterface 分组头部（addItemHeader）
- 分组导航项组织
- 栈式界面切换
- 选中项同步更新
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QStackedWidget, QFrame

from qfluentwidgets import NavigationInterface, NavigationItemPosition, FluentIcon as FIF


class DemoInterface(QFrame):
    """子界面占位组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName(text.replace(' ', '-'))


class Window(QWidget):
    """Navigation Header 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Navigation Header - 演示')
        self.resize(900, 600)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化导航组件"""
        self.navigationInterface = NavigationInterface(self)
        self.stackedWidget = QStackedWidget(self)
        self.interfaces = {}

        # 主页
        self.addInterface('home', FIF.HOME, 'Home')
        self.navigationInterface.addSeparator()

        # Basic Input 分组
        self.navigationInterface.addItemHeader('Basic Input', NavigationItemPosition.SCROLL)
        self.addInterface('button', FIF.CHECKBOX, 'Button', NavigationItemPosition.SCROLL)
        self.addInterface('input', FIF.EDIT, 'Input', NavigationItemPosition.SCROLL)

        # Data 分组
        self.navigationInterface.addItemHeader('Data', NavigationItemPosition.SCROLL)
        self.addInterface('table', FIF.DOCUMENT, 'Table', NavigationItemPosition.SCROLL)
        self.addInterface('list', FIF.MENU, 'List', NavigationItemPosition.SCROLL)

        # 设置
        self.addInterface('settings', FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # 默认选中首页
        self.stackedWidget.setCurrentIndex(0)
        self.navigationInterface.setCurrentItem('home')
        self.navigationInterface.setUpdateIndicatorPosOnCollapseFinished(True)

    def initLayout(self):
        """初始化布局"""
        hBox = QHBoxLayout(self)
        hBox.setContentsMargins(0, 0, 0, 0)
        hBox.setSpacing(0)
        hBox.addWidget(self.navigationInterface)
        hBox.addWidget(self.stackedWidget)
        hBox.setStretchFactor(self.stackedWidget, 1)

    def addInterface(self, routeKey: str, icon, text: str, position=NavigationItemPosition.TOP):
        """添加子界面到导航"""
        interface = DemoInterface(text, self)
        self.interfaces[routeKey] = interface
        self.stackedWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=routeKey,
            icon=icon,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(interface),
            position=position
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
