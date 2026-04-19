# coding:utf-8
"""
PipsPager 演示

展示内容：
- HorizontalPipsPager 水平分页指示器
- VerticalPipsPager 垂直分页指示器
- 页面数量与可见数量设置
- 翻页按钮显示模式
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    PipsScrollButtonDisplayMode, HorizontalPipsPager, VerticalPipsPager,
    BodyLabel,
)


class Demo(QWidget):
    """PipsPager 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('PipsPager - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化分页指示器"""
        # 水平分页指示器
        self.hPager = HorizontalPipsPager(self)
        self.hPager.setPageNumber(15)
        self.hPager.setVisibleNumber(8)
        self.hPager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.hPager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.hPager.currentIndexChanged.connect(self.onPageChanged)

        # 垂直分页指示器
        self.vPager = VerticalPipsPager(self)
        self.vPager.setPageNumber(15)
        self.vPager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.vPager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ON_HOVER)

        self.statusLabel = BodyLabel('水平分页: 第 1 页', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        pagerLayout = QHBoxLayout()
        pagerLayout.addWidget(self.hPager)
        pagerLayout.addWidget(self.vPager)
        mainLayout.addLayout(pagerLayout)

        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onPageChanged(self, index):
        """页码变化时更新状态"""
        self.statusLabel.setText(f'水平分页: 第 {index + 1} 页')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
