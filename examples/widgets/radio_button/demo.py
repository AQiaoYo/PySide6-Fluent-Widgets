# coding:utf-8
"""
RadioButton 演示

展示内容：
- 单选按钮分组（同一组内互斥）
- SubtitleRadioButton（带子标题的单选按钮）
- 禁用状态的单选按钮
- 信号槽连接获取选中变化
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QButtonGroup,
)

from qfluentwidgets import RadioButton, SubtitleRadioButton, BodyLabel, CaptionLabel, setFont


class Demo(QWidget):
    """RadioButton 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RadioButton - 演示")
        self.resize(500, 520)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化单选按钮组件"""
        # RadioButton 区域
        self.themeLabel = BodyLabel("RadioButton", self)
        setFont(self.themeLabel, 16)

        self.group1 = QButtonGroup(self)
        self.radioLight = RadioButton("浅色主题", self)
        self.radioDark = RadioButton("深色主题", self)
        self.radioAuto = RadioButton("自动跟随系统", self)
        self.radioLight.setChecked(True)
        self.group1.addButton(self.radioLight)
        self.group1.addButton(self.radioDark)
        self.group1.addButton(self.radioAuto)

        # SubtitleRadioButton 区域
        self.subLabel = BodyLabel("SubtitleRadioButton", self)
        setFont(self.subLabel, 16)

        self.group2 = QButtonGroup(self)
        self.subRb1 = SubtitleRadioButton("扬声器", self)
        self.subRb1.setSubtitle("Realtek(R) Audio")
        self.subRb1.setChecked(True)

        self.subRb2 = SubtitleRadioButton("耳机", self)
        self.subRb2.setSubtitle("AirPods Pro 2")

        self.subRb3 = SubtitleRadioButton("禁用设备", self)
        self.subRb3.setSubtitle("此设备不可用")
        self.subRb3.setEnabled(False)

        self.group2.addButton(self.subRb1)
        self.group2.addButton(self.subRb2)
        self.group2.addButton(self.subRb3)

        # 状态显示
        self.statusLabel = BodyLabel("请选择选项...", self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        # RadioButton 区域
        mainLayout.addWidget(self.themeLabel)
        mainLayout.addWidget(self.radioLight)
        mainLayout.addWidget(self.radioDark)
        mainLayout.addWidget(self.radioAuto)
        mainLayout.addSpacing(20)

        # SubtitleRadioButton 区域
        mainLayout.addWidget(self.subLabel)
        mainLayout.addWidget(
            CaptionLabel("带有标题和子标题，使用方式与 QRadioButton 相同", self)
        )
        mainLayout.addWidget(self.subRb1)
        mainLayout.addWidget(self.subRb2)
        mainLayout.addWidget(self.subRb3)
        mainLayout.addStretch(1)

        mainLayout.addWidget(self.statusLabel)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
