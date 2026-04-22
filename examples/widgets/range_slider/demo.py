# coding: utf-8
"""
RangeSlider Demo

展示内容:
- RangeSlider 水平方向基础用法
- RangeSlider 垂直方向基础用法
- 自定义格式化函数（整数显示）
- 信号监听（rangeChanged）
- 亮色/暗色主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QWidget,
)

from qfluentwidgets import BodyLabel, Theme, TogglePushButton, setTheme
from qfluentwidgets import RangeSlider


class Demo(QWidget):
    """RangeSlider 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('RangeSlider - Demo')
        self.resize(560, 420)

        # --- 水平滑动条（默认格式化：1 位小数）---
        self.hSlider = RangeSlider(Qt.Orientation.Horizontal, self)
        self.hSlider.setRange(0, 100)
        self.hSlider.setLowValue(20)
        self.hSlider.setHighValue(80)

        # 状态标签
        self.hLabel = BodyLabel(self._rangeText(self.hSlider), self)
        self.hSlider.rangeChanged.connect(
            lambda lo, hi: self.hLabel.setText(f'水平范围: [{lo}, {hi}]')
        )

        # --- 水平滑动条（整数格式化）---
        self.hSlider2 = RangeSlider(Qt.Orientation.Horizontal, self)
        self.hSlider2.setRange(0, 10)
        self.hSlider2.setLowValue(2)
        self.hSlider2.setHighValue(7)
        self.hSlider2.setValueFormatter(lambda v: str(int(v)))

        self.hLabel2 = BodyLabel(self._rangeText(self.hSlider2), self)
        self.hSlider2.rangeChanged.connect(
            lambda lo, hi: self.hLabel2.setText(f'整数范围: [{lo}, {hi}]')
        )

        # --- 垂直滑动条 ---
        self.vSlider = RangeSlider(Qt.Orientation.Vertical, self)
        self.vSlider.setRange(0, 100)
        self.vSlider.setLowValue(30)
        self.vSlider.setHighValue(70)
        self.vSlider.setFixedHeight(200)

        self.vLabel = BodyLabel(self._rangeText(self.vSlider), self)
        self.vSlider.rangeChanged.connect(
            lambda lo, hi: self.vLabel.setText(f'垂直范围: [{lo}, {hi}]')
        )

        # --- 主题切换按钮 ---
        self.themeBtn = TogglePushButton('Dark Theme', self)
        self.themeBtn.toggled.connect(
            lambda checked: setTheme(Theme.DARK if checked else Theme.LIGHT)
        )

        # --- 布局 ---
        # 左侧：水平滑动条
        leftLayout = QVBoxLayout()
        leftLayout.setSpacing(16)
        leftLayout.addWidget(BodyLabel('水平 RangeSlider (默认格式化)', self))
        leftLayout.addWidget(self.hSlider)
        leftLayout.addWidget(self.hLabel)
        leftLayout.addSpacing(8)
        leftLayout.addWidget(BodyLabel('水平 RangeSlider (整数格式化)', self))
        leftLayout.addWidget(self.hSlider2)
        leftLayout.addWidget(self.hLabel2)
        leftLayout.addStretch(1)
        leftLayout.addWidget(self.themeBtn)

        # 右侧：垂直滑动条
        rightLayout = QVBoxLayout()
        rightLayout.setSpacing(8)
        rightLayout.addWidget(BodyLabel('垂直 RangeSlider', self))
        rightLayout.addWidget(self.vSlider)
        rightLayout.addWidget(self.vLabel)
        rightLayout.addStretch(1)

        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(40, 40, 40, 40)
        mainLayout.setSpacing(40)
        mainLayout.addLayout(leftLayout, 2)
        mainLayout.addLayout(rightLayout, 1)

    @staticmethod
    def _rangeText(slider: RangeSlider) -> str:
        """生成初始范围文本"""
        return f'范围: [{slider.lowValue()}, {slider.highValue()}]'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
