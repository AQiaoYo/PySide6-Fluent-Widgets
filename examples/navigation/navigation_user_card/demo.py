# coding:utf-8
"""
Navigation User Card 演示

展示内容：
- 导航用户卡片（addUserCard）
- 头像、标题、副标题展示
- 卡片位置配置（aboveMenuButton）
- 点击交互
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout

from qfluentwidgets import (
    NavigationItemPosition, MessageBox, FluentWindow,
    SubtitleLabel, setFont,
)
from qfluentwidgets import FluentIcon as FIF


class Widget(QFrame):
    """子界面占位组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):
    """Navigation User Card 演示窗口"""

    def __init__(self):
        super().__init__()
        self.initInterfaces()
        self.initNavigation()
        self.initWindow()

    def initInterfaces(self):
        """初始化子界面"""
        self.homeInterface = Widget('Home Interface', self)
        self.musicInterface = Widget('Music Interface', self)
        self.videoInterface = Widget('Video Interface', self)
        self.settingInterface = Widget('Setting Interface', self)

    def initNavigation(self):
        """初始化导航与用户卡片"""
        # 添加用户卡片（位于展开/折叠按钮下方）
        self.userCard = self.navigationInterface.addUserCard(
            routeKey='userCard',
            avatar='resource/shoko.png',
            title='zhiyiYo',
            subtitle='shokokawaii@outlook.com',
            onClick=self.showMessageBox,
            position=NavigationItemPosition.TOP,
            aboveMenuButton=False,
        )

        # 导航项
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.musicInterface, FIF.MUSIC, 'Music library')

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.videoInterface, FIF.VIDEO, 'Video library')
        self.addSubInterface(self.settingInterface, FIF.SETTING,
                             'Settings', NavigationItemPosition.BOTTOM)

        self.navigationInterface.setUpdateIndicatorPosOnCollapseFinished(True)

    def initWindow(self):
        """初始化窗口"""
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('Navigation User Card - 演示')

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def showMessageBox(self):
        """显示用户卡片信息"""
        w = MessageBox(
            'User Card',
            '导航用户卡片支持头像、标题和副标题展示。\\n\\n'
            '位置配置:\\n'
            '• aboveMenuButton=True: 位于展开/折叠按钮上方\\n'
            '• aboveMenuButton=False: 位于菜单按钮下方（默认）',
            self
        )
        w.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
