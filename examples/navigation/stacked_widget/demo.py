# coding:utf-8
"""
Transition StackedWidget 演示

展示内容：
- EntranceTransitionStackedWidget 进入过渡动画
- DrillInTransitionStackedWidget 钻入过渡动画
- 前后导航控制
- 过渡模式切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QStackedWidget, QButtonGroup

from qfluentwidgets import (
    DrillInTransitionStackedWidget, EntranceTransitionStackedWidget,
    RadioButton, PushButton, BodyLabel, SubtitleLabel, TitleLabel, themeColor,
)

LOREM = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et '
         'dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip '
         'ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu '
         'fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt '
         'mollit anim id est laborum.')


class ColorBlock(QFrame):
    """颜色块组件"""

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f'background: {color.name()};')


class SamplePage1(QWidget):
    """示例页面 1 — 网格布局"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        accent = ColorBlock(themeColor(), self)
        accent.setMinimumWidth(200)
        layout.addWidget(accent, 0, 0, 2, 1)

        darkGray = ColorBlock(QColor(128, 128, 128), self)
        lightGray1 = ColorBlock(QColor(192, 192, 192), self)
        lightGray2 = ColorBlock(QColor(192, 192, 192), self)
        darkGray2 = ColorBlock(QColor(160, 160, 160), self)

        for blk in [darkGray, lightGray1, lightGray2, darkGray2]:
            blk.setMinimumHeight(120)

        layout.addWidget(darkGray, 0, 1)
        layout.addWidget(lightGray1, 0, 2)
        layout.addWidget(lightGray2, 1, 1)
        layout.addWidget(darkGray2, 1, 2)

        lbl = BodyLabel(LOREM, self)
        lbl.setWordWrap(True)
        layout.addWidget(lbl, 2, 0, 1, 3)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)


class SamplePage2(QWidget):
    """示例页面 2 — 左右布局"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        accent = ColorBlock(themeColor(), self)
        accent.setFixedSize(140, 180)
        layout.addWidget(accent, 0, Qt.AlignTop)

        vbox = QVBoxLayout()
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 0, 0)

        title = TitleLabel('Lorem ipsum dolor sit amet, consectetur adipiscing elit', self)
        title.setWordWrap(True)
        vbox.addWidget(title)

        body = BodyLabel(LOREM, self)
        body.setWordWrap(True)
        vbox.addWidget(body)
        vbox.addStretch(1)

        layout.addLayout(vbox, 1)


class Demo(QWidget):
    """Transition StackedWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Transition StackedWidget - 演示')
        self.resize(800, 700)
        self._backStack = []
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化过渡组件"""
        self.stackedWidget = QStackedWidget(self)

        # 进入过渡
        self.entranceStackedWidget = EntranceTransitionStackedWidget()
        self.entranceStackedWidget.setMinimumHeight(500)
        self.entranceStackedWidget.addWidget(SamplePage1())
        self.entranceStackedWidget.addWidget(SamplePage2())
        self.stackedWidget.addWidget(self.entranceStackedWidget)

        # 钻入过渡
        self.drillInStackedWidget = DrillInTransitionStackedWidget()
        self.drillInStackedWidget.setMinimumHeight(500)
        self.drillInStackedWidget.addWidget(SamplePage1())
        self.drillInStackedWidget.addWidget(SamplePage2())
        self.stackedWidget.addWidget(self.drillInStackedWidget)

        # 控制面板
        self.ctrlPanel = QWidget(self)
        self.ctrlPanel.setFixedWidth(260)
        self.buttonGroup = QButtonGroup(self)

        layout = QVBoxLayout(self.ctrlPanel)
        layout.addWidget(SubtitleLabel('过渡模式', self.ctrlPanel))

        self.modes = [
            ('进入过渡 (Entrance)', self.entranceStackedWidget),
            ('钻入过渡 (DrillIn)', self.drillInStackedWidget),
        ]

        for i, (name, widget) in enumerate(self.modes):
            button = RadioButton(name, self.ctrlPanel)
            button.setProperty("index", i)
            self.buttonGroup.addButton(button)
            layout.addWidget(button)
            if i == 0:
                button.setChecked(True)

        layout.addSpacing(16)
        layout.addWidget(SubtitleLabel('导航', self.ctrlPanel))
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.fwdBtn = PushButton('向前导航', self.ctrlPanel)
        self.bwdBtn = PushButton('向后导航', self.ctrlPanel)
        layout.addWidget(self.fwdBtn)
        layout.addWidget(self.bwdBtn)
        layout.addStretch(1)

        # 信号连接
        self.fwdBtn.clicked.connect(self._onForward)
        self.bwdBtn.clicked.connect(self._onBackward)
        self.buttonGroup.idClicked.connect(
            lambda: self.stackedWidget.setCurrentIndex(self.buttonGroup.checkedButton().property('index')))

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.stackedWidget, 1)
        mainLayout.addWidget(self.ctrlPanel, 0)

    def _onForward(self):
        """向前导航"""
        stack = self.stackedWidget.currentWidget()
        self._backStack.append(stack.currentIndex())
        stack.setCurrentIndex((stack.currentIndex() + 1) % stack.count())

    def _onBackward(self):
        """向后导航"""
        if not self._backStack:
            return
        stack = self.stackedWidget.currentWidget()
        stack.setCurrentIndex(self._backStack.pop(), isBack=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
