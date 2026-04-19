# coding:utf-8
"""
CalendarPicker 演示

展示内容：
- 日历选择器基础用法
- 日期变化信号响应
- 日期格式自定义
- 重置功能
"""
import sys

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import CalendarPicker, BodyLabel, PushButton, setTheme, Theme


class Demo(QWidget):
    """CalendarPicker 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CalendarPicker - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化日历选择器组件"""
        # 标准日历选择器
        self.picker = CalendarPicker(self)
        self.picker.dateChanged.connect(self.onDateChanged)

        # 预设日期按钮
        self.btnSetDate = PushButton('设为 2024-06-01', self)
        self.btnSetDate.clicked.connect(self.onSetDate)

        self.btnReset = PushButton('重置', self)
        self.btnReset.clicked.connect(self.onReset)

        # 状态显示
        self.statusLabel = BodyLabel('请选择日期...', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.picker, 0, Qt.AlignCenter)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnSetDate)
        btnLayout.addWidget(self.btnReset)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onDateChanged(self, date):
        """日期变化时更新显示"""
        self.statusLabel.setText(f'选中日期: {date.toString("yyyy-MM-dd")}')

    def onSetDate(self):
        """预设日期"""
        self.picker.setDate(QDate(2024, 6, 1))

    def onReset(self):
        """重置日期"""
        self.picker.setDate(QDate.currentDate())
        self.statusLabel.setText('日期已重置为今天')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
