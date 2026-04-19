# coding:utf-8
"""
TeachingTip 演示

展示内容：
- TeachingTip 教学提示（顶部/底部弹出）
- TeachingTipView 带图片的教学提示
- PopupTeachingTip 自定义内容教学提示
- CustomFlyoutView 完全自定义视图
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    PushButton, TeachingTip, TeachingTipTailPosition, InfoBarIcon,
    TeachingTipView, FlyoutViewBase, BodyLabel, PrimaryPushButton, PopupTeachingTip,
)


class CustomFlyoutView(FlyoutViewBase):
    """自定义教学提示视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.label = BodyLabel('这是一个自定义的教学提示视图，\n可以展示任何您想要的内容。')
        self.button = PrimaryPushButton('我知道了')

        self.button.setFixedWidth(140)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.vBoxLayout.addWidget(self.label)
        self.vBoxLayout.addWidget(self.button)

    def paintEvent(self, e):
        pass


class Demo(QWidget):
    """TeachingTip 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TeachingTip - 演示')
        self.resize(700, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化按钮"""
        self.button1 = PushButton('顶部提示', self)
        self.button2 = PushButton('底部提示', self)
        self.button3 = PushButton('自定义视图', self)

        self.button1.setFixedWidth(150)
        self.button2.setFixedWidth(150)
        self.button3.setFixedWidth(150)

        self.button1.clicked.connect(self.showTopTip)
        self.button2.clicked.connect(self.showBottomTip)
        self.button3.clicked.connect(self.showCustomTip)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.button2, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.button1, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.button3, 0, Qt.AlignHCenter)

    def showTopTip(self):
        """顶部教学提示"""
        position = TeachingTipTailPosition.BOTTOM
        view = TeachingTipView(
            icon=None,
            title='新功能介绍',
            content="我们新增了暗色主题支持，您可以在设置中切换主题模式。",
            image='resource/Gyro.jpg',
            isClosable=True,
            tailPosition=position,
        )

        button = PushButton('立即体验')
        button.setFixedWidth(120)
        view.addWidget(button, align=Qt.AlignRight)

        w = TeachingTip.make(
            target=self.button1,
            view=view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        view.closed.connect(w.close)

    def showBottomTip(self):
        """底部教学提示"""
        TeachingTip.create(
            target=self.button2,
            icon=InfoBarIcon.SUCCESS,
            title='设置已保存',
            content="您的偏好设置已成功保存，将在下次启动时生效。",
            isClosable=True,
            tailPosition=TeachingTipTailPosition.TOP,
            duration=2000,
            parent=self
        )

    def showCustomTip(self):
        """自定义视图教学提示"""
        PopupTeachingTip.make(
            target=self.button3,
            view=CustomFlyoutView(),
            tailPosition=TeachingTipTailPosition.RIGHT,
            duration=2000,
            parent=self
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
