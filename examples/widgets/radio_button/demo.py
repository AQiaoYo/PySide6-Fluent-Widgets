# coding:utf-8
"""
RadioButton 演示

展示内容：
- 单选按钮分组（同一组内互斥）
- 多组单选按钮（组间独立）
- 禁用状态的单选按钮
- 信号槽连接获取选中变化
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QButtonGroup,
)

from qfluentwidgets import RadioButton, BodyLabel


class Demo(QWidget):
    """RadioButton 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('RadioButton - 演示')
        self.resize(450, 350)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化单选按钮组件"""
        # 第一组：主题选择
        self.themeLabel = BodyLabel('选择主题:', self)
        self.group1 = QButtonGroup(self)
        self.radioLight = RadioButton('浅色主题', self)
        self.radioDark = RadioButton('深色主题', self)
        self.radioAuto = RadioButton('自动跟随系统', self)
        self.radioLight.setChecked(True)
        self.group1.addButton(self.radioLight)
        self.group1.addButton(self.radioDark)
        self.group1.addButton(self.radioAuto)
        self.group1.buttonClicked.connect(self.onSelectionChanged)

        # 第二组：通知设置
        self.notifyLabel = BodyLabel('通知设置:', self)
        self.group2 = QButtonGroup(self)
        self.radioAll = RadioButton('接收所有通知', self)
        self.radioMention = RadioButton('仅提及我的', self)
        self.radioNone = RadioButton('关闭通知', self)
        self.radioNone.setEnabled(False)  # 禁用状态
        self.group2.addButton(self.radioAll)
        self.group2.addButton(self.radioMention)
        self.group2.addButton(self.radioNone)
        self.group2.buttonClicked.connect(self.onSelectionChanged)

        # 状态显示
        self.statusLabel = BodyLabel('请选择选项...', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        # 第一组布局
        mainLayout.addWidget(self.themeLabel)
        mainLayout.addWidget(self.radioLight)
        mainLayout.addWidget(self.radioDark)
        mainLayout.addWidget(self.radioAuto)
        mainLayout.addSpacing(20)

        # 第二组布局
        mainLayout.addWidget(self.notifyLabel)
        mainLayout.addWidget(self.radioAll)
        mainLayout.addWidget(self.radioMention)
        mainLayout.addWidget(self.radioNone)
        mainLayout.addStretch(1)

        mainLayout.addWidget(self.statusLabel)

    def onSelectionChanged(self):
        """选中变化时更新状态显示"""
        sender = self.sender()
        selected = sender.checkedButton()
        if selected:
            self.statusLabel.setText(f'已选择: {selected.text()}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
