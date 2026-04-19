# coding:utf-8
"""
NavigationInterface (Stack) 演示

展示内容：
- NavigationInterface 侧边导航栏
- 树形层级菜单（子菜单展开/折叠记忆）
- 自定义头像组件
- 与 QStackedWidget 联动
- 页面切换动画与路由
"""
import sys

from PySide6.QtCore import Qt, QRect, QUrl
from PySide6.QtGui import QIcon, QPainter, QImage, QBrush, QColor, QFont, QDesktopServices
from PySide6.QtWidgets import QApplication, QFrame, QStackedWidget, QHBoxLayout, QLabel

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox,
    isDarkTheme, setTheme, Theme, qrouter,
)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, StandardTitleBar


class Widget(QFrame):
    """子页面组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class AvatarWidget(NavigationWidget):
    """自定义头像导航组件"""

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.avatar = QImage('resource/shoko.png').scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # 悬停背景
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # 绘制头像
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont('Segoe UI')
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, 'zhiyiYo')


class Window(FramelessWindow):
    """NavigationInterface 演示主窗口"""

    def __init__(self):
        super().__init__()
        self.setTitleBar(StandardTitleBar(self))

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.stackWidget = QStackedWidget(self)

        # 创建子页面
        self.searchInterface = Widget('搜索页面', self)
        self.musicInterface = Widget('音乐库', self)
        self.videoInterface = Widget('视频库', self)
        self.folderInterface = Widget('文件夹', self)
        self.settingInterface = Widget('设置', self)
        self.albumInterface = Widget('专辑', self)
        self.albumInterface1 = Widget('专辑 1', self)
        self.albumInterface2 = Widget('专辑 2', self)
        self.albumInterface1_1 = Widget('专辑 1.1', self)

        self.initLayout()
        self.initNavigation()
        self.initWindow()

    def initLayout(self):
        """初始化布局"""
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

    def initNavigation(self):
        """初始化导航栏"""
        self.addSubInterface(self.searchInterface, FIF.SEARCH, '搜索')
        self.addSubInterface(self.musicInterface, FIF.MUSIC, '音乐库')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频库')

        self.navigationInterface.addSeparator()

        # 树形菜单
        self.addSubInterface(self.albumInterface, FIF.ALBUM, '专辑', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.albumInterface1, FIF.ALBUM, '专辑 1', parent=self.albumInterface)
        self.addSubInterface(self.albumInterface1_1, FIF.ALBUM, '专辑 1.1', parent=self.albumInterface1)
        self.addSubInterface(self.albumInterface2, FIF.ALBUM, '专辑 2', parent=self.albumInterface)

        # 记忆展开状态
        self.navigationInterface.widget('专辑').setRememberExpandState(True)
        self.navigationInterface.widget('专辑-1').setRememberExpandState(True)

        self.addSubInterface(self.folderInterface, FIF.FOLDER, '文件夹', NavigationItemPosition.SCROLL)

        # 底部自定义头像
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', NavigationItemPosition.BOTTOM)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(1)

    def initWindow(self):
        """初始化窗口"""
        self.resize(900, 700)
        self.setWindowIcon(QIcon('resource/logo.png'))
        self.setWindowTitle('NavigationInterface - 演示')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP, parent=None):
        """添加子页面"""
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text,
            parentRouteKey=parent.objectName() if parent else None
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
        """页面变化时同步导航栏选中状态"""
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())

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
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
