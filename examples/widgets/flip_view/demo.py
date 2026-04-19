# coding:utf-8
"""
FlipView 演示

展示内容：
- HorizontalFlipView 水平翻页视图
- HorizontalPipsPager 分页指示器联动
- 自定义 FlipImageDelegate
- 图片加载与切换信号
"""
import sys
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QRect, QSize
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QWidget, QVBoxLayout

from qfluentwidgets import (
    FlipImageDelegate, HorizontalPipsPager, HorizontalFlipView,
    BodyLabel, setTheme, Theme, PushButton, getFont,
)
from qfluentwidgets import FluentIcon as FIF


class CustomFlipItemDelegate(FlipImageDelegate):
    """自定义翻页项委托 — 在图片上绘制文字遮罩"""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        painter.save()

        # 绘制遮罩
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(Qt.NoPen)
        rect = option.rect
        rect = QRect(rect.x(), rect.y(), 200, rect.height())
        painter.drawRect(rect)

        # 绘制文字
        painter.setPen(Qt.black)
        painter.setFont(getFont(16, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, '自定义委托\nFlipImageDelegate')

        painter.restore()


class Demo(QWidget):
    """FlipView 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FlipView - 演示')
        self.resize(600, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化翻页组件"""
        self.statusLabel = BodyLabel('当前图片: 1', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.flipView = HorizontalFlipView(self)
        self.pager = HorizontalPipsPager(self)

        self.flipView.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)

        # 加载图片
        images = [str(i) for i in Path('./resource').glob('*')]
        if images:
            self.flipView.addImages(images)
        self.pager.setPageNumber(self.flipView.count())

        # 联动信号
        self.pager.currentIndexChanged.connect(self.flipView.setCurrentIndex)
        self.flipView.currentIndexChanged.connect(self.pager.setCurrentIndex)
        self.flipView.currentIndexChanged.connect(self.onIndexChanged)

        # 主题切换
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(20)
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setAlignment(Qt.AlignCenter)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.flipView, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.pager, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onIndexChanged(self, index: int):
        """图片索引变化"""
        self.statusLabel.setText(f'当前图片: {index + 1} / {self.flipView.count()}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
