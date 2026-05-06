# coding:utf-8
"""
MultiSegmentProgressRing 演示

展示内容:
- MultiSegmentProgressRing 分段环形进度条
- 存储空间分段可视化
- 中心文本和主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import (
    BodyLabel, CaptionLabel, FluentIcon, MultiSegmentProgressRing,
    PushButton, setTheme
)


class Demo(QWidget):
    """MultiSegmentProgressRing 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MultiSegmentProgressRing - 演示')
        self.resize(300, 320)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化分段进度环组件"""
        self.titleLabel = BodyLabel('分段进度环', self)
        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.progressRing = MultiSegmentProgressRing(self)
        self.progressRing.setFixedSize(140, 140)
        self.progressRing.setStrokeWidth(9)
        self.progressRing.setGapAngle(10)
        self.progressRing.setTrackVisible(False)
        self.progressRing.setTextVisible(True)
        self.progressRing.setCenterText('1.1\nMB')
        self.progressRing.setSegments([
            (55, '#0F7BFF', '#4CC2FF'),
            (22, '#3CB6F8', '#3CB6F8'),
            (4, '#4CD964', '#4CD964'),
        ])

        self.tipLabel = CaptionLabel('蓝色: 已用空间    绿色: 可恢复空间', self)
        self.tipLabel.setAlignment(Qt.AlignCenter)

        self.themeBtn = PushButton(FluentIcon.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.progressRing, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.tipLabel)
        self.vBoxLayout.addWidget(self.themeBtn, 0, Qt.AlignHCenter)
        self.vBoxLayout.addStretch(1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()

