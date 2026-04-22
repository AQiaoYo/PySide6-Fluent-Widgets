# coding:utf-8
"""
CalendarTimePicker 演示

展示内容:
- 日历时间选择器基础用法
- 程序化设置日期时间
- 日期时间变化信号响应
- 重置功能
- 亮色/暗色主题切换
"""
import sys

from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    CalendarTimePicker, BodyLabel, PushButton,
    TogglePushButton, setTheme, Theme
)


class Demo(QWidget):
    """CalendarTimePicker 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CalendarTimePicker - 演示')
        self.resize(600, 320)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        # 基础用法
        self.picker = CalendarTimePicker(self)
        self.picker.setFixedWidth(260)
        self.picker.dateTimeChanged.connect(self.onDateTimeChanged)

        # 预设日期时间按钮
        self.btnSetDateTime = PushButton('设为 2026-01-01 08:30:00', self)
        self.btnSetDateTime.clicked.connect(self.onSetDateTime)

        self.btnReset = PushButton('重置', self)
        self.btnReset.clicked.connect(self.picker.reset)

        # 主题切换
        self.themeBtn = TogglePushButton('切换暗色主题', self)
        self.themeBtn.toggled.connect(self.onThemeToggled)

        # 状态显示
        self.statusLabel = BodyLabel('请选择日期和时间...', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(40, 40, 40, 40)

        mainLayout.addWidget(self.picker, 0, Qt.AlignCenter)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnSetDateTime)
        btnLayout.addWidget(self.btnReset)
        btnLayout.addWidget(self.themeBtn)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onDateTimeChanged(self, dt: QDateTime):
        """日期时间变化时更新状态标签"""
        self.statusLabel.setText(f'选中: {dt.toString("yyyy-MM-dd HH:mm:ss")}')

    def onSetDateTime(self):
        """程序化设置日期时间"""
        dt = QDateTime.fromString('2026-01-01 08:30:00', 'yyyy-MM-dd HH:mm:ss')
        self.picker.setDateTime(dt)

    def onThemeToggled(self, checked: bool):
        """切换亮色/暗色主题"""
        setTheme(Theme.DARK if checked else Theme.LIGHT)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
