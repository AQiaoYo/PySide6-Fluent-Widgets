# coding:utf-8
"""
ColorDialog 演示

展示内容：
- 颜色选择对话框
- 颜色预览与确认
- 自定义初始颜色
- 颜色值输出与响应
"""
import sys

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    ColorDialog, PushButton, PrimaryPushButton,
    BodyLabel, CardWidget,
)


class Demo(QWidget):
    """ColorDialog 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ColorDialog - 演示')
        self.resize(450, 250)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化颜色对话框相关组件"""
        # 颜色预览卡片
        self.colorCard = CardWidget(self)
        self.colorCard.setFixedSize(120, 80)
        self.colorCard.setStyleSheet('background-color: #0078d4; border-radius: 8px;')

        self.colorLabel = BodyLabel('#0078d4', self)

        # 打开颜色对话框按钮
        self.btnPick = PrimaryPushButton('选择颜色', self)
        self.btnPick.clicked.connect(self.onPickColor)

        # 预设颜色快速选择
        self.btnRed = PushButton('红色', self)
        self.btnRed.clicked.connect(lambda: self.applyColor('#d13438'))

        self.btnGreen = PushButton('绿色', self)
        self.btnGreen.clicked.connect(lambda: self.applyColor('#107c10'))

        self.btnBlue = PushButton('蓝色', self)
        self.btnBlue.clicked.connect(lambda: self.applyColor('#0078d4'))

        self.statusLabel = BodyLabel('点击按钮选择或预设颜色', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        # 预览区
        previewLayout = QHBoxLayout()
        previewLayout.addWidget(self.colorCard)
        previewLayout.addWidget(self.colorLabel)
        previewLayout.addStretch(1)
        mainLayout.addLayout(previewLayout)

        # 按钮区
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(10)
        btnLayout.addWidget(self.btnPick)
        btnLayout.addWidget(self.btnRed)
        btnLayout.addWidget(self.btnGreen)
        btnLayout.addWidget(self.btnBlue)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel)

    def onPickColor(self):
        """打开颜色选择对话框"""
        w = ColorDialog(
            QColor(self.colorLabel.text()),
            '选择主题颜色',
            self,
        )
        w.colorChanged.connect(lambda c: self.statusLabel.setText(f'预览颜色: {c.name()}'))
        if w.exec():
            self.applyColor(w.color.name())
            self.statusLabel.setText(f'已确认颜色: {w.color.name()}')

    def applyColor(self, color_hex: str):
        """应用颜色到预览卡片"""
        self.colorCard.setStyleSheet(f'background-color: {color_hex}; border-radius: 8px;')
        self.colorLabel.setText(color_hex)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
