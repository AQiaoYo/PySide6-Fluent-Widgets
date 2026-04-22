# coding:utf-8
"""
ToolTipSlider Demo

展示内容:
- ToolTipSlider 基础用法 (水平)
- 自定义格式化函数
- 亮色/暗色主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import BodyLabel, Theme, TogglePushButton, ToolTipSlider, setTheme


class Demo(QWidget):
    """Demo 窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ToolTipSlider - Demo')
        self.resize(480, 320)

        # Basic slider (default formatter: 1 decimal place)
        self.slider1 = ToolTipSlider(Qt.Horizontal, self)
        self.slider1.setRange(0, 100)
        self.slider1.setValue(40)

        # Slider with custom integer formatter
        self.slider2 = ToolTipSlider(Qt.Horizontal, self)
        self.slider2.setRange(0, 10)
        self.slider2.setValue(4)
        self.slider2.setValueFormatter(lambda v: str(int(v)))

        # Theme toggle button
        self.themeBtn = TogglePushButton('Dark Theme', self)
        self.themeBtn.toggled.connect(
            lambda checked: setTheme(Theme.DARK if checked else Theme.LIGHT)
        )

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(40, 40, 40, 40)
        self.vBoxLayout.addWidget(BodyLabel('ToolTipSlider (default formatter)', self))
        self.vBoxLayout.addWidget(self.slider1)
        self.vBoxLayout.addWidget(BodyLabel('ToolTipSlider (integer formatter)', self))
        self.vBoxLayout.addWidget(self.slider2)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.themeBtn)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
