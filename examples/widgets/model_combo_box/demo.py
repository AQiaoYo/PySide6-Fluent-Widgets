# coding:utf-8
"""
ModelComboBox 演示

展示内容：
- ModelComboBox 模型下拉框
- EditableModelComboBox 可编辑模型下拉框
- 占位符文本
- currentTextChanged 信号
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    ModelComboBox, EditableModelComboBox, BodyLabel, setTheme, Theme, PushButton,
)
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """ModelComboBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ModelComboBox - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化下拉框"""
        self.statusLabel = BodyLabel('请选择一个选项', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # ModelComboBox
        self.comboBox = ModelComboBox(self)
        self.comboBox.setPlaceholderText("选择一项")
        items = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++', 'Java']
        self.comboBox.addItems(items)
        self.comboBox.setCurrentIndex(-1)
        self.comboBox.currentTextChanged.connect(self.onTextChanged)

        # EditableModelComboBox
        self.editableComboBox = EditableModelComboBox(self)
        self.editableComboBox.setPlaceholderText("可编辑选择")
        self.editableComboBox.addItems(items)
        self.editableComboBox.setCurrentIndex(-1)

        # 主题切换
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)

        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.comboBox, 1)
        controlLayout.addWidget(self.editableComboBox, 1)
        mainLayout.addLayout(controlLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onTextChanged(self, text: str):
        """选项变化"""
        self.statusLabel.setText(f'当前选择: {text}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
