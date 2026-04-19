# coding:utf-8
"""
AcrylicFlyout 演示

展示内容：
- AcrylicFlyout 亚克力弹出层
- AcrylicFlyoutView 亚克力自定义视图
- AcrylicFlyoutViewBase 完全自定义内容
- 不同动画类型
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    PushButton, InfoBarIcon, FlyoutAnimationType,
    BodyLabel, PrimaryPushButton,
)
from qfluentwidgets.components.material import AcrylicFlyoutView, AcrylicFlyoutViewBase, AcrylicFlyout


class CustomFlyoutView(AcrylicFlyoutViewBase):
    """自定义亚克力弹出层视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.label = BodyLabel('这是一个自定义的 AcrylicFlyout 视图，\n带有亚克力背景效果。')
        self.button = PrimaryPushButton('确认')

        self.button.setFixedWidth(140)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.vBoxLayout.addWidget(self.label)
        self.vBoxLayout.addWidget(self.button)


class Demo(QWidget):
    """AcrylicFlyout 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicFlyout - 演示')
        self.resize(750, 550)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化按钮"""
        self.button1 = PushButton('标准弹出层', self)
        self.button2 = PushButton('带图片弹出层', self)
        self.button3 = PushButton('自定义视图', self)

        self.button1.clicked.connect(self.showFlyout1)
        self.button2.clicked.connect(self.showFlyout2)
        self.button3.clicked.connect(self.showFlyout3)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(30, 50, 30, 50)
        mainLayout.addWidget(self.button1, 0, Qt.AlignBottom)
        mainLayout.addWidget(self.button2, 0, Qt.AlignBottom)
        mainLayout.addWidget(self.button3, 0, Qt.AlignBottom)

    def showFlyout1(self):
        """标准亚克力弹出层"""
        AcrylicFlyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='操作成功',
            content="数据已成功保存，您可以继续下一步操作。",
            target=self.button1,
            parent=self,
            isClosable=True
        )

    def showFlyout2(self):
        """带图片的亚克力弹出层"""
        view = AcrylicFlyoutView(
            title='组件库介绍',
            content="PyQt-Fluent-Widgets 是一个基于 PyQt/PySide 的 Fluent Design 风格组件库，"
                    "包含许多美观实用的组件，帮助开发者快速构建现代化界面。",
            image='resource/SBR.jpg',
            isClosable=True
        )

        button = PushButton('了解更多')
        button.setFixedWidth(120)
        view.addWidget(button, align=Qt.AlignRight)

        view.widgetLayout.insertSpacing(1, 5)
        view.widgetLayout.addSpacing(5)

        w = AcrylicFlyout.make(view, self.button2, self)
        view.closed.connect(w.close)

    def showFlyout3(self):
        """自定义视图亚克力弹出层"""
        AcrylicFlyout.make(CustomFlyoutView(), self.button3, self, aniType=FlyoutAnimationType.DROP_DOWN)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
