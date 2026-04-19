# coding:utf-8
"""
TimePicker / DatePicker 演示

展示内容：
- DatePicker 日期选择器
- ZhDatePicker 中文日期选择器
- AMTimePicker 12小时制时间选择器
- TimePicker 24小时制时间选择器
- 自定义列格式化器
- 日期/时间变化信号
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import (
    TimePicker, AMTimePicker, DatePicker, ZhDatePicker,
    BodyLabel, setTheme, Theme, PickerColumnFormatter, PushButton,
)


class SecondsFormatter(PickerColumnFormatter):
    """秒数列格式化器"""

    def encode(self, value):
        return str(value) + "秒"

    def decode(self, value: str):
        return int(value[:-1])


class Demo(QWidget):
    """TimePicker 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TimePicker - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化选择器"""
        self.statusLabel = BodyLabel('请选择日期或时间', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.datePicker1 = DatePicker(self)
        self.datePicker2 = ZhDatePicker(self)
        self.timePicker1 = AMTimePicker(self)
        self.timePicker2 = TimePicker(self)
        self.timePicker3 = TimePicker(self, showSeconds=True)

        # 自定义秒数列格式
        self.timePicker3.setColumnFormatter(2, SecondsFormatter())

        # 信号连接
        self.datePicker1.dateChanged.connect(lambda d: self.onChanged(f'日期: {d.toString()}'))
        self.datePicker2.dateChanged.connect(lambda d: self.onChanged(f'中文日期: {d.toString()}'))
        self.timePicker1.timeChanged.connect(lambda t: self.onChanged(f'12小时制: {t.toString()}'))
        self.timePicker2.timeChanged.connect(lambda t: self.onChanged(f'24小时制: {t.toString()}'))
        self.timePicker3.timeChanged.connect(lambda t: self.onChanged(f'带秒数: {t.toString()}'))

        # 主题切换
        self.themeBtn = PushButton('切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 20, 30, 20)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.datePicker1, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.datePicker2, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.timePicker1, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.timePicker2, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.timePicker3, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignHCenter)

    def onChanged(self, text: str):
        """日期/时间变化"""
        self.statusLabel.setText(text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
