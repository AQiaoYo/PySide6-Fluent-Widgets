# coding:utf-8
"""
InfoBar 演示

展示内容：
- InfoBar 信息提示条（信息/成功/警告/错误）
- 自定义 InfoBar（图标、背景色）
- 桌面右下角通知
- 自定义 InfoBarManager 位置管理器
"""
import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    InfoBarIcon, InfoBar, PushButton, FluentIcon,
    InfoBarPosition, InfoBarManager, setTheme, Theme,
)


@InfoBarManager.register('Custom')
class CustomInfoBarManager(InfoBarManager):
    """自定义 InfoBar 位置管理器 — 居中显示"""

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()
        x = (parentSize.width() - infoBar.width()) // 2
        y = (parentSize.height() - infoBar.height()) // 2

        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


class Demo(QWidget):
    """InfoBar 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('InfoBar - 演示')
        self.resize(700, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化按钮"""
        self.button1 = PushButton('信息', self)
        self.button2 = PushButton('成功', self)
        self.button3 = PushButton('警告', self)
        self.button4 = PushButton('错误', self)
        self.button5 = PushButton('自定义', self)
        self.button6 = PushButton('桌面通知', self)

        self.button1.clicked.connect(self.createInfoInfoBar)
        self.button2.clicked.connect(self.createSuccessInfoBar)
        self.button3.clicked.connect(self.createWarningInfoBar)
        self.button4.clicked.connect(self.createErrorInfoBar)
        self.button5.clicked.connect(self.createCustomInfoBar)
        self.button6.clicked.connect(self.createDesktopInfoBar)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        for btn in [self.button1, self.button2, self.button3, self.button4, self.button5, self.button6]:
            mainLayout.addWidget(btn)

    def createInfoInfoBar(self):
        """信息提示"""
        w = InfoBar(
            icon=InfoBarIcon.INFORMATION,
            title='提示',
            content='这是一条信息提示，会在 2 秒后自动消失。',
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        w.addWidget(PushButton('操作'))
        w.show()

    def createSuccessInfoBar(self):
        """成功提示"""
        InfoBar.success(
            title='操作成功',
            content='数据已成功保存到服务器。',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def createWarningInfoBar(self):
        """警告提示"""
        InfoBar.warning(
            title='注意',
            content='当前网络连接不稳定，请检查网络设置。',
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_LEFT,
            duration=2000,
            parent=self
        )

    def createErrorInfoBar(self):
        """错误提示"""
        InfoBar.error(
            title='操作失败',
            content='无法连接到服务器，请稍后重试。',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self
        )

    def createCustomInfoBar(self):
        """自定义提示"""
        w = InfoBar.new(
            icon=FluentIcon.GITHUB,
            title='自定义样式',
            content='使用 new() 方法创建自定义样式的 InfoBar。',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')

    def createDesktopInfoBar(self):
        """桌面通知"""
        InfoBar.warning(
            title='电源通知',
            content="当前电量为 64%",
            orient=Qt.Vertical,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=InfoBar.desktopView()
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
