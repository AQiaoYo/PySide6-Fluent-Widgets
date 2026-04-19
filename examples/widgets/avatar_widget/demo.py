# coding:utf-8
"""
AvatarWidget 演示

展示内容：
- 图像头像（不同尺寸）
- 文字头像（自动提取首字母）
- 自定义形状（圆形、圆角矩形）
- 头像点击交互
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import AvatarWidget, BodyLabel


class Demo(QWidget):
    """AvatarWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AvatarWidget - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化头像组件"""
        # 图像头像 - 不同尺寸
        self.imageLabel = BodyLabel('图像头像:', self)
        self.avatarLarge = AvatarWidget(self)
        self.avatarLarge.setRadius(32)
        # 使用文字头像作为 fallback（图像文件可能不存在）
        try:
            pixmap = QPixmap('resource/shoko.png')
            if not pixmap.isNull():
                self.avatarLarge.setImage(pixmap)
            else:
                self.avatarLarge.setText('A')
        except Exception:
            self.avatarLarge.setText('A')

        self.avatarMedium = AvatarWidget(self)
        self.avatarMedium.setRadius(24)
        self.avatarMedium.setText('B')

        self.avatarSmall = AvatarWidget(self)
        self.avatarSmall.setRadius(16)
        self.avatarSmall.setText('C')

        # 文字头像 - 不同内容
        self.textLabel = BodyLabel('文字头像:', self)
        self.textAvatar1 = AvatarWidget(self)
        self.textAvatar1.setRadius(28)
        self.textAvatar1.setText('张三')

        self.textAvatar2 = AvatarWidget(self)
        self.textAvatar2.setRadius(28)
        self.textAvatar2.setText('Li')

        self.textAvatar3 = AvatarWidget(self)
        self.textAvatar3.setRadius(28)
        self.textAvatar3.setText('AI')

        # 点击交互
        self.clickableAvatar = AvatarWidget(self)
        self.clickableAvatar.setRadius(32)
        self.clickableAvatar.setText('Click')
        self.clickableAvatar.setCursor(Qt.PointingHandCursor)
        self.clickableAvatar.mousePressEvent = lambda e: self.onAvatarClicked()

        self.statusLabel = BodyLabel('点击右下角头像查看交互', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        # 图像头像行
        imageLayout = QHBoxLayout()
        imageLayout.setSpacing(16)
        imageLayout.addWidget(self.imageLabel)
        imageLayout.addWidget(self.avatarLarge)
        imageLayout.addWidget(self.avatarMedium)
        imageLayout.addWidget(self.avatarSmall)
        imageLayout.addStretch(1)
        mainLayout.addLayout(imageLayout)

        # 文字头像行
        textLayout = QHBoxLayout()
        textLayout.setSpacing(16)
        textLayout.addWidget(self.textLabel)
        textLayout.addWidget(self.textAvatar1)
        textLayout.addWidget(self.textAvatar2)
        textLayout.addWidget(self.textAvatar3)
        textLayout.addStretch(1)
        mainLayout.addLayout(textLayout)

        mainLayout.addStretch(1)

        # 交互区域
        clickLayout = QHBoxLayout()
        clickLayout.addWidget(self.statusLabel)
        clickLayout.addStretch(1)
        clickLayout.addWidget(self.clickableAvatar)
        mainLayout.addLayout(clickLayout)

    def onAvatarClicked(self):
        """头像点击响应"""
        self.statusLabel.setText('头像被点击了！')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
