# coding:utf-8
"""
Label 演示

展示内容：
- Fluent 标签层级（Caption 到 Display）
- 超链接标签
- 文本颜色自定义
- 字体大小调整
"""
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    CaptionLabel, BodyLabel, StrongBodyLabel, SubtitleLabel,
    TitleLabel, LargeTitleLabel, DisplayLabel,
    HyperlinkLabel, PushButton, BodyLabel as StatusLabel,
)


class Demo(QWidget):
    """Label 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Label - 演示')
        self.resize(500, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化标签组件"""
        # 超链接标签
        self.hyperlinkLabel = HyperlinkLabel(QUrl('https://github.com/'), 'GitHub')
        self.hyperlinkLabel.setUnderlineVisible(True)

        # 各级别标签
        self.labels = [
            CaptionLabel('Caption - 12px 小字'),
            BodyLabel('Body - 14px 正文'),
            StrongBodyLabel('Body Strong - 14px 粗体'),
            SubtitleLabel('Subtitle - 20px 副标题'),
            TitleLabel('Title - 28px 标题'),
            LargeTitleLabel('Title Large - 40px 大标题'),
            DisplayLabel('Display - 68px 展示'),
        ]

        # 控制按钮
        self.btnToggleColor = PushButton('切换强调色', self)
        self.btnToggleColor.clicked.connect(self.onToggleColor)

        self.statusLabel = StatusLabel('标签层级展示', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.hyperlinkLabel)
        mainLayout.addSpacing(10)

        for label in self.labels:
            mainLayout.addWidget(label)

        mainLayout.addStretch(1)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnToggleColor)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onToggleColor(self):
        """切换标签颜色"""
        for label in self.labels:
            label.setTextColor('#0078d4', '#0078d4')
        self.statusLabel.setText('已应用强调色')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
