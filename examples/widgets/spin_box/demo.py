# coding:utf-8
"""
SpinBox 演示

展示内容：
- 标准 SpinBox / DoubleSpinBox
- 紧凑版本 CompactSpinBox
- 日期时间编辑器
- 加速输入与范围限制
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QGridLayout

from qfluentwidgets import (
    SpinBox, CompactSpinBox, DoubleSpinBox, CompactDoubleSpinBox,
    DateTimeEdit, CompactDateTimeEdit, DateEdit, CompactDateEdit,
    TimeEdit, CompactTimeEdit, BodyLabel,
)


class Demo(QWidget):
    """SpinBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SpinBox - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化数值输入组件"""
        # 整数输入
        self.spinBox = SpinBox(self)
        self.spinBox.setRange(0, 100)
        self.spinBox.setValue(42)
        self.spinBox.setAccelerated(True)
        self.spinBox.valueChanged.connect(self.onValueChanged)

        self.compactSpinBox = CompactSpinBox(self)
        self.compactSpinBox.setRange(0, 100)
        self.compactSpinBox.setValue(42)
        self.compactSpinBox.setAccelerated(True)

        # 浮点数输入
        self.doubleSpinBox = DoubleSpinBox(self)
        self.doubleSpinBox.setRange(0, 1)
        self.doubleSpinBox.setSingleStep(0.1)
        self.doubleSpinBox.setValue(0.5)

        self.compactDoubleSpinBox = CompactDoubleSpinBox(self)
        self.compactDoubleSpinBox.setRange(0, 1)
        self.compactDoubleSpinBox.setSingleStep(0.1)
        self.compactDoubleSpinBox.setValue(0.5)

        # 日期时间
        self.timeEdit = TimeEdit(self)
        self.compactTimeEdit = CompactTimeEdit(self)

        self.dateEdit = DateEdit(self)
        self.compactDateEdit = CompactDateEdit(self)

        self.dateTimeEdit = DateTimeEdit(self)
        self.compactDateTimeEdit = CompactDateTimeEdit(self)

        self.statusLabel = BodyLabel('修改数值查看变化', self)

    def initLayout(self):
        """初始化布局"""
        grid = QGridLayout(self)
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(50, 30, 50, 30)

        grid.addWidget(BodyLabel('整数:'), 0, 0)
        grid.addWidget(self.spinBox, 0, 1)
        grid.addWidget(self.compactSpinBox, 0, 2)

        grid.addWidget(BodyLabel('浮点数:'), 1, 0)
        grid.addWidget(self.doubleSpinBox, 1, 1)
        grid.addWidget(self.compactDoubleSpinBox, 1, 2)

        grid.addWidget(BodyLabel('时间:'), 2, 0)
        grid.addWidget(self.timeEdit, 2, 1)
        grid.addWidget(self.compactTimeEdit, 2, 2)

        grid.addWidget(BodyLabel('日期:'), 3, 0)
        grid.addWidget(self.dateEdit, 3, 1)
        grid.addWidget(self.compactDateEdit, 3, 2)

        grid.addWidget(BodyLabel('日期时间:'), 4, 0)
        grid.addWidget(self.dateTimeEdit, 4, 1)
        grid.addWidget(self.compactDateTimeEdit, 4, 2)

        grid.addWidget(self.statusLabel, 5, 0, 1, 3, Qt.AlignCenter)

    def onValueChanged(self, value):
        """数值变化时更新状态"""
        self.statusLabel.setText(f'当前值: {value}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
