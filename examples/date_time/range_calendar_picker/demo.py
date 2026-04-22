# coding: utf-8
"""
RangeCalendarPicker 演示

展示内容:
- 日期范围选择器基础用法
- 日期范围变化信号响应
- 程序化设置日期范围
- 自定义日期显示格式
- 重置功能
- 亮色/暗色主题切换
"""
import sys

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    RangeCalendarPicker, BodyLabel, PushButton, TogglePushButton,
    setTheme, Theme, TitleLabel, CaptionLabel
)


class Demo(QWidget):
    """RangeCalendarPicker 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('RangeCalendarPicker - 演示')
        self.resize(560, 420)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        # 标题
        self.titleLabel = TitleLabel('日期范围选择器', self)

        # --- 基础用法 ---
        self.basicLabel = CaptionLabel('基础用法', self)
        self.picker = RangeCalendarPicker(self)
        self.picker.setFixedWidth(280)
        self.picker.dateRangeChanged.connect(self.onDateRangeChanged)

        # --- 自定义格式 ---
        self.fmtLabel = CaptionLabel('自定义格式 (yyyy/MM/dd)', self)
        self.fmtPicker = RangeCalendarPicker(self)
        self.fmtPicker.setFixedWidth(280)
        self.fmtPicker.setDateFormat('yyyy/MM/dd')
        self.fmtPicker.dateRangeChanged.connect(self.onFmtDateRangeChanged)

        # 状态显示
        self.statusLabel = BodyLabel('请在上方选择日期范围...', self)
        self.fmtStatusLabel = BodyLabel('请在上方选择日期范围...', self)

        # --- 操作按钮 ---
        self.btnSetRange = PushButton('设为 2024-03-13 ~ 2024-03-21', self)
        self.btnSetRange.clicked.connect(self.onSetRange)

        self.btnReset = PushButton('重置', self)
        self.btnReset.clicked.connect(self.onReset)

        # 主题切换
        self.themeBtn = TogglePushButton('切换暗色主题', self)
        self.themeBtn.toggled.connect(self.onThemeToggled)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(36, 28, 36, 28)

        mainLayout.addWidget(self.titleLabel)
        mainLayout.addSpacing(4)

        # 基础用法区域
        mainLayout.addWidget(self.basicLabel)
        mainLayout.addWidget(self.picker)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addSpacing(8)

        # 自定义格式区域
        mainLayout.addWidget(self.fmtLabel)
        mainLayout.addWidget(self.fmtPicker)
        mainLayout.addWidget(self.fmtStatusLabel)
        mainLayout.addSpacing(8)

        # 操作按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addWidget(self.btnSetRange)
        btnLayout.addWidget(self.btnReset)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)

        # 主题切换
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignRight)

    def onDateRangeChanged(self, startDate: QDate, endDate: QDate):
        """基础选择器日期范围变化时更新状态显示

        Args:
            startDate: 起始日期
            endDate: 结束日期
        """
        start = startDate.toString('yyyy-MM-dd')
        end = endDate.toString('yyyy-MM-dd')
        self.statusLabel.setText(f'已选范围: {start} ~ {end}')

    def onFmtDateRangeChanged(self, startDate: QDate, endDate: QDate):
        """自定义格式选择器日期范围变化时更新状态显示

        Args:
            startDate: 起始日期
            endDate: 结束日期
        """
        start = startDate.toString('yyyy/MM/dd')
        end = endDate.toString('yyyy/MM/dd')
        self.fmtStatusLabel.setText(f'已选范围: {start} ~ {end}')

    def onSetRange(self):
        """程序化设置日期范围"""
        self.picker.setDateRange(QDate(2024, 3, 13), QDate(2024, 3, 21))

    def onReset(self):
        """重置两个选择器"""
        self.picker.reset()
        self.fmtPicker.reset()
        self.statusLabel.setText('请在上方选择日期范围...')
        self.fmtStatusLabel.setText('请在上方选择日期范围...')

    def onThemeToggled(self, checked: bool):
        """切换亮色/暗色主题

        Args:
            checked: 是否切换到暗色主题
        """
        setTheme(Theme.DARK if checked else Theme.LIGHT)
        self.themeBtn.setText('切换亮色主题' if checked else '切换暗色主题')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
