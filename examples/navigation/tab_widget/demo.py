# coding:utf-8
"""
TabWidget 演示

展示内容：
- TabWidget 标签页组件
- 可拖拽标签页
- 动态添加新标签页
- 标签页关闭事件
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import TabWidget, SubtitleLabel, setFont, IconWidget, FluentIcon as FIF


class TabInterface(QWidget):
    """标签页内容组件"""

    def __init__(self, text: str, icon, parent=None):
        super().__init__(parent=parent)
        self.iconWidget = IconWidget(icon, self)
        self.label = SubtitleLabel(text, self)
        self.iconWidget.setFixedSize(120, 120)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.label, 0, Qt.AlignCenter)
        setFont(self.label, 24)


class Window(QWidget):
    """TabWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TabWidget - 演示')
        self.resize(900, 600)
        self.tabCount = 1
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化标签页组件"""
        self.tabWidget = TabWidget(self)
        self.tabWidget.setMovable(True)

        # 添加初始标签页
        self.tabWidget.addTab(
            TabInterface('Heart', FIF.HEART),
            'Tab 1',
            icon=FIF.HEART,
        )

        # 信号连接
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        self.tabWidget.tabCloseRequested.connect(self.tabWidget.removeTab)
        self.tabWidget.tabAddRequested.connect(self.addNewPage)

    def initLayout(self):
        """初始化布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.tabWidget)

    def onTabChanged(self, index):
        """标签页切换时更新标题"""
        self.setWindowTitle(f'TabWidget - 标签 {index + 1}')

    def addNewPage(self):
        """添加新标签页"""
        text = f'新标签页 #{self.tabCount}'
        self.tabWidget.addTab(
            TabInterface(text, FIF.DOCUMENT),
            text,
            icon=FIF.DOCUMENT,
        )
        self.tabCount += 1


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
