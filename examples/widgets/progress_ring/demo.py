# coding:utf-8
"""
ProgressRing 演示

展示内容：
- ProgressRing 环形进度条
- IndeterminateProgressRing 不确定环形进度条
- SpinBox 数值控制
- 播放/暂停控制
- 主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    ProgressRing, SpinBox, IndeterminateProgressRing,
    ToggleToolButton, FluentIcon, BodyLabel, setTheme, Theme, PushButton,
)


class Demo(QWidget):
    """ProgressRing 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ProgressRing - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化环形进度条组件"""
        self.statusLabel = BodyLabel('进度: 50%', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.progressRing = ProgressRing(self)
        self.progressRing.setValue(50)
        self.progressRing.setTextVisible(True)
        self.progressRing.setFixedSize(80, 80)

        self.spinBox = SpinBox(self)
        self.spinBox.setRange(0, 100)
        self.spinBox.setValue(50)
        self.spinBox.valueChanged.connect(self.onSpinBoxValueChanged)

        self.spinner = IndeterminateProgressRing(self)

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

        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.progressRing, 0, Qt.AlignHCenter)
        controlLayout.addWidget(self.spinBox, 0, Qt.AlignHCenter)
        mainLayout.addLayout(controlLayout)

        mainLayout.addWidget(self.spinner, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.button, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignHCenter)
        mainLayout.addStretch(1)

    def onSpinBoxValueChanged(self, value: int):
        """SpinBox 数值变化"""
        self.progressRing.setValue(value)
        self.statusLabel.setText(f'进度: {value}%')

    def onButtonClicked(self):
        """播放/暂停切换"""
        if not self.progressRing.isPaused():
            self.progressRing.pause()
            self.button.setIcon(FluentIcon.PLAY_SOLID)
        else:
            self.progressRing.resume()
            self.button.setIcon(FluentIcon.PAUSE_BOLD)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
