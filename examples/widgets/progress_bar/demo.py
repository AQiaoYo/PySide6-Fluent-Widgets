# coding:utf-8
"""
ProgressBar 演示

展示内容：
- ProgressBar 进度条
- IndeterminateProgressBar 不确定进度条
- 播放/暂停控制
- 自定义颜色
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import (
    IndeterminateProgressBar, ProgressBar, ToggleToolButton,
    FluentIcon, BodyLabel, setTheme, Theme, PushButton,
)


class Demo(QWidget):
    """ProgressBar 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ProgressBar - 演示')
        self.resize(400, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化进度条组件"""
        self.statusLabel = BodyLabel('进度条已暂停', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(50)

        self.inProgressBar = IndeterminateProgressBar(self)

        self.button = ToggleToolButton(FluentIcon.PAUSE_BOLD, self)
        self.button.clicked.connect(self.onButtonClicked)

        # 主题切换
        self.themeBtn = PushButton(FluentIcon.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(self.inProgressBar)
        mainLayout.addWidget(self.button, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignHCenter)
        mainLayout.addStretch(1)

    def onButtonClicked(self):
        """播放/暂停切换"""
        if self.inProgressBar.isStarted():
            self.inProgressBar.pause()
            self.progressBar.pause()
            self.button.setIcon(FluentIcon.PLAY_SOLID)
            self.statusLabel.setText('进度条已暂停')
        else:
            self.inProgressBar.resume()
            self.progressBar.resume()
            self.button.setIcon(FluentIcon.PAUSE_BOLD)
            self.statusLabel.setText('进度条运行中')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
