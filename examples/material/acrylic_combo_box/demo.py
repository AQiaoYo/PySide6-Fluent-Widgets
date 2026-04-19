# coding:utf-8
"""
AcrylicComboBox 演示

展示内容：
- 亚克力下拉框（AcrylicComboBox）
- 可编辑亚克力下拉框（AcrylicEditableComboBox）
- 自动补全功能
- 主题色自定义
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCompleter

from qfluentwidgets import (
    AcrylicComboBox, AcrylicEditableComboBox,
    BodyLabel, PushButton, setThemeColor,
)


class Demo(QWidget):
    """AcrylicComboBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicComboBox - 演示')
        self.resize(400, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化亚克力下拉框组件"""
        items = ['shoko', '西宫硝子', 'aiko', '柳井爱子', '一级棒卡哇伊']

        # 标准亚克力下拉框
        self.comboBox = AcrylicComboBox(self)
        self.comboBox.addItems(items)
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentTextChanged.connect(self.onTextChanged)

        # 可编辑亚克力下拉框（支持输入和自动补全）
        self.editableCombo = AcrylicEditableComboBox(self)
        self.editableCombo.addItems(items)
        self.editableCombo.setCurrentIndex(0)

        # 配置自动补全
        self.completer = QCompleter(items, self)
        self.editableCombo.setCompleter(self.completer)

        # 控制按钮
        self.btnTheme = PushButton('切换主题色', self)
        self.btnTheme.clicked.connect(self.onChangeTheme)

        self.statusLabel = BodyLabel('请选择或输入内容...', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.comboBox)
        mainLayout.addWidget(self.editableCombo)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnTheme)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

        self.setStyleSheet('Demo{background:white}')

    def onTextChanged(self, text):
        """下拉框文本变化时更新状态"""
        self.statusLabel.setText(f'选中: {text}')

    def onChangeTheme(self):
        """切换主题色"""
        setThemeColor('#0078d4')
        self.statusLabel.setText('主题色已更新')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
