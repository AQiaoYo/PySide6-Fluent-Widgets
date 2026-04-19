# coding:utf-8
"""
FastCalendarPicker 演示

展示内容：
- FastCalendarPicker 快速日历选择器
- 日期变化信号
- 重置功能
- 动画类型自定义
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    FastCalendarPicker, BodyLabel, setTheme, Theme,
    FluentTranslator, FlyoutAnimationType, PushButton,
)


class Demo(QWidget):
    """FastCalendarPicker 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FastCalendarPicker - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化日历选择器"""
        self.statusLabel = BodyLabel('请选择一个日期', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.picker = FastCalendarPicker(self)
        self.picker.dateChanged.connect(self.onDateChanged)

        # 主题切换
        self.themeBtn = PushButton('切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.picker, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onDateChanged(self, date):
        """日期变化"""
        self.statusLabel.setText(f'选中日期: {date.toString()}')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    translator = FluentTranslator()
    app.installTranslator(translator)

    w = Demo()
    w.show()
    app.exec()
