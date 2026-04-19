# coding:utf-8
"""
ScrollArea 演示

展示内容：
- SmoothScrollArea 平滑滚动
- 自定义滚动条样式
- 滚动动画参数调整
- 内容加载与展示
"""
import sys

from PySide6.QtCore import QEasingCurve, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import (
    SmoothScrollArea, PixmapLabel, BodyLabel,
    PushButton, ScrollBarHandleDisplayMode,
)


class Demo(QWidget):
    """ScrollArea 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ScrollArea - 演示')
        self.resize(600, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化滚动区域组件"""
        # 平滑滚动区域
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setFixedSize(500, 300)

        # 设置滚动动画参数（时长 500ms，缓动曲线 OutQuint）
        self.scrollArea.setScrollAnimation(Qt.Vertical, 500, QEasingCurve.OutQuint)
        self.scrollArea.setScrollAnimation(Qt.Horizontal, 500, QEasingCurve.OutQuint)

        # 大图像作为滚动内容
        self.contentLabel = PixmapLabel(self.scrollArea)
        try:
            pixmap = QPixmap('resource/shoko.jpg')
            if not pixmap.isNull():
                self.contentLabel.setPixmap(pixmap)
            else:
                self.contentLabel.setText('滚动内容区域\\n(图像加载失败，使用文本占位)')
                self.contentLabel.setFixedSize(800, 600)
        except Exception:
            self.contentLabel.setText('滚动内容区域\\n(图像加载失败，使用文本占位)')
            self.contentLabel.setFixedSize(800, 600)

        self.scrollArea.setWidget(self.contentLabel)

        # 控制按钮
        self.btnHoverMode = PushButton('悬停显示滚动条', self)
        self.btnHoverMode.clicked.connect(self.onToggleHoverMode)

        self.btnFastScroll = PushButton('快速滚动', self)
        self.btnFastScroll.clicked.connect(self.onFastScroll)

        self.statusLabel = BodyLabel('滚动区域已就绪', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.scrollArea, 0, Qt.AlignCenter)

        btnLayout = QVBoxLayout()
        btnLayout.setSpacing(8)
        btnLayout.addWidget(self.btnHoverMode, 0, Qt.AlignCenter)
        btnLayout.addWidget(self.btnFastScroll, 0, Qt.AlignCenter)
        mainLayout.addLayout(btnLayout)

        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onToggleHoverMode(self):
        """切换滚动条显示模式"""
        vbar = self.scrollArea.verticalScrollBar()
        if hasattr(vbar, 'setHandleDisplayMode'):
            vbar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)
            self.statusLabel.setText('滚动条模式: 悬停时显示')
        else:
            self.statusLabel.setText('当前滚动条不支持此模式')

    def onFastScroll(self):
        """调整快速滚动动画"""
        self.scrollArea.setScrollAnimation(Qt.Vertical, 200, QEasingCurve.OutCubic)
        self.statusLabel.setText('滚动动画已加速 (200ms)')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
