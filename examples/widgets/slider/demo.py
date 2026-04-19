# coding:utf-8
"""
Slider 演示

展示内容：
- Slider 水平/垂直滑块
- HollowHandleStyle 自定义滑块样式
- 数值变化信号
- 范围与步长设置
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider

from qfluentwidgets import Slider, HollowHandleStyle, BodyLabel, setTheme, Theme, PushButton
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """Slider 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Slider - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化滑块组件"""
        # 状态标签
        self.statusLabel = BodyLabel('拖动滑块查看数值', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # 水平滑块
        self.hSlider = Slider(Qt.Horizontal, self)
        self.hSlider.setRange(0, 100)
        self.hSlider.setValue(30)
        self.hSlider.setSingleStep(1)
        self.hSlider.setPageStep(10)
        self.hSlider.valueChanged.connect(self.onValueChanged)

        # 垂直滑块
        self.vSlider = Slider(Qt.Vertical, self)
        self.vSlider.setRange(0, 100)
        self.vSlider.setValue(60)
        self.vSlider.valueChanged.connect(self.onValueChanged)

        # 自定义样式滑块 (HollowHandleStyle)
        self.customSlider = QSlider(Qt.Horizontal, self)
        style = {"sub-page.color": QColor(0, 90, 158)}
        self.customSlider.setStyle(HollowHandleStyle(style))
        self.customSlider.setRange(0, 100)
        self.customSlider.setValue(50)
        self.customSlider.valueChanged.connect(self.onCustomValueChanged)

        self.customLabel = BodyLabel('自定义样式: 50', self)

        # 主题切换按钮
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)

        # 滑块区域
        sliderLayout = QHBoxLayout()
        sliderLayout.setSpacing(30)

        # 左侧：水平滑块 + 自定义滑块
        leftLayout = QVBoxLayout()
        leftLayout.setSpacing(20)
        leftLayout.addWidget(BodyLabel('水平滑块 (0-100)', self))
        leftLayout.addWidget(self.hSlider)
        leftLayout.addSpacing(20)
        leftLayout.addWidget(BodyLabel('自定义 HollowHandle 样式', self))
        leftLayout.addWidget(self.customSlider)
        leftLayout.addWidget(self.customLabel)
        leftLayout.addStretch(1)
        sliderLayout.addLayout(leftLayout, 2)

        # 右侧：垂直滑块
        rightLayout = QVBoxLayout()
        rightLayout.setAlignment(Qt.AlignHCenter)
        rightLayout.addWidget(BodyLabel('垂直滑块', self))
        rightLayout.addWidget(self.vSlider, 0, Qt.AlignHCenter)
        sliderLayout.addLayout(rightLayout, 1)

        mainLayout.addLayout(sliderLayout, 1)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onValueChanged(self, value: int):
        """滑块数值变化"""
        sender = self.sender()
        direction = '水平' if sender == self.hSlider else '垂直'
        self.statusLabel.setText(f'{direction}滑块数值: {value}')

    def onCustomValueChanged(self, value: int):
        """自定义滑块数值变化"""
        self.customLabel.setText(f'自定义样式: {value}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
