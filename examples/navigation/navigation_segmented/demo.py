# coding:utf-8
"""
NavigationBar + NavigationPanel 演示

展示内容：
- NavigationBar 顶部导航栏
- NavigationPanel 弹出式导航面板
- 亚克力效果
- 与 QStackedWidget 联动
"""
import sys

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStackedWidget, QHBoxLayout, QLabel, QWidget, QVBoxLayout

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
    isDarkTheme, setTheme, Theme, NavigationToolButton, NavigationPanel,
)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, StandardTitleBar


class Widget(QWidget):
    """子页面组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class NavigationBar(QWidget):
    """自定义导航栏组件"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.menuButton = NavigationToolButton(FIF.MENU, self)
        self.navigationPanel = NavigationPanel(parent, True)
        self.titleLabel = QLabel(self)

        self.navigationPanel.move(0, 31)
        self.hBoxLayout.setContentsMargins(5, 5, 5, 5)
        self.hBoxLayout.addWidget(self.menuButton)
        self.hBoxLayout.addWidget(self.titleLabel)

        self.menuButton.clicked.connect(self.showNavigationPanel)
        self.navigationPanel.setExpandWidth(260)
        self.navigationPanel.setMenuButtonVisible(True)
        self.navigationPanel.hide()
        self.navigationPanel.setAcrylicEnabled(True)

        self.window().installEventFilter(self)

    def setTitle(self, title: str):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def showNavigationPanel(self):
        self.navigationPanel.show()
        self.navigationPanel.raise_()
        self.navigationPanel.expand()

    def addItem(self, routeKey, icon, text: str, onClick, selectable=True, position=NavigationItemPosition.TOP):
        def wrapper():
            onClick()
            self.setTitle(text)

        self.navigationPanel.addItem(
            routeKey, icon, text, wrapper, selectable, position)

    def addSeparator(self, position=NavigationItemPosition.TOP):
        self.navigationPanel.addSeparator(position)

    def setCurrentItem(self, routeKey: str):
        self.navigationPanel.setCurrentItem(routeKey)
        self.setTitle(self.navigationPanel.widget(routeKey).text())

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Resize:
                self.navigationPanel.setFixedHeight(e.size().height() - 31)
        return super().eventFilter(obj, e)


class Window(FramelessWindow):
    """NavigationBar 演示主窗口"""

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))

        self.vBoxLayout = QVBoxLayout(self)
        self.navigationInterface = NavigationBar(self)
        self.stackWidget = QStackedWidget(self)

        # 创建子页面
        self.searchInterface = Widget('搜索页面', self)
        self.musicInterface = Widget('音乐库', self)
        self.videoInterface = Widget('视频库', self)
        self.folderInterface = Widget('文件夹', self)
        self.settingInterface = Widget('设置', self)

        self.stackWidget.addWidget(self.searchInterface)
        self.stackWidget.addWidget(self.musicInterface)
        self.stackWidget.addWidget(self.videoInterface)
        self.stackWidget.addWidget(self.folderInterface)
        self.stackWidget.addWidget(self.settingInterface)

        self.initLayout()
        self.initNavigation()
        self.initWindow()

    def initLayout(self):
        """初始化布局"""
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.vBoxLayout.addWidget(self.navigationInterface)
        self.vBoxLayout.addWidget(self.stackWidget)
        self.vBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        """初始化导航"""
        self.addSubInterface(self.searchInterface, FIF.SEARCH, '搜索')
        self.addSubInterface(self.musicInterface, FIF.MUSIC, '音乐库')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频库')

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.folderInterface, FIF.FOLDER, '文件夹', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(1)

    def initWindow(self):
        """初始化窗口"""
        self.resize(500, 600)
        self.setWindowIcon(QIcon('resource/logo.png'))
        self.setWindowTitle('NavigationBar - 演示')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()

    def addSubInterface(self, w: QWidget, icon, text, position=NavigationItemPosition.TOP):
        self.stackWidget.addWidget(w)
        self.navigationInterface.addItem(
            routeKey=w.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(w),
            position=position
        )

    def setQss(self):
        """加载样式表"""
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        """切换页面"""
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        """页面变化时同步导航栏"""
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())

    def showMessageBox(self):
        """显示帮助对话框"""
        w = MessageBox(
            '帮助信息',
            '这是一个自定义导航组件示例，可以通过 NavigationInterface.addWidget() 添加更多自定义控件。',
            self
        )
        w.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
