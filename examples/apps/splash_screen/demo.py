# coding:utf-8
"""
SplashScreen 演示

展示内容：
- 启动画面显示
- 图标尺寸自定义
- 模拟加载过程
- 加载完成后关闭启动画面
"""
import sys

from PySide6.QtCore import Qt, QEventLoop, QTimer, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from qfluentwidgets import SplashScreen, BodyLabel, ProgressBar
from qframelesswindow import FramelessWindow, StandardTitleBar


class Demo(FramelessWindow):
    """SplashScreen 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SplashScreen - 演示')
        self.resize(700, 500)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        # 在启动画面上添加进度条
        self.progressBar = ProgressBar(self.splashScreen)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFixedWidth(200)
        self.progressBar.move(
            (self.splashScreen.width() - 200) // 2,
            self.splashScreen.height() - 60,
        )

        # 显示窗口和启动画面
        self.show()
        self.splashScreen.show()

        # 模拟加载过程
        self.loadProgress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.onLoading)
        self.timer.start(50)

        # 主界面内容
        self.contentLabel = BodyLabel('主界面内容已加载', self)
        self.contentLabel.move(280, 220)
        self.contentLabel.hide()

    def onLoading(self):
        """模拟加载进度"""
        self.loadProgress += 2
        self.progressBar.setValue(self.loadProgress)

        if self.loadProgress >= 100:
            self.timer.stop()
            self.splashScreen.finish()
            self.contentLabel.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
