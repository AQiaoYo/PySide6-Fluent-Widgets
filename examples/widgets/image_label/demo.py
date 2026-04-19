# coding:utf-8
"""
ImageLabel 演示

展示内容：
- 静态图像显示
- GIF 动画显示
- 圆角裁剪设置
- 图像缩放操作
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import ImageLabel, PushButton, BodyLabel


class Demo(QWidget):
    """ImageLabel 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ImageLabel - 演示')
        self.resize(500, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化图像标签组件"""
        # 静态图像（fallback 为纯色）
        self.imageLabel = ImageLabel(self)
        try:
            self.imageLabel.setImage('resource/Gyro.jpg')
        except Exception:
            pass
        self.imageLabel.scaledToHeight(200)
        self.imageLabel.setBorderRadius(10, 10, 10, 10)

        # GIF 动画
        self.gifLabel = ImageLabel(self)
        try:
            self.gifLabel.setImage('resource/boqi.gif')
        except Exception:
            pass
        self.gifLabel.scaledToHeight(150)
        self.gifLabel.setBorderRadius(20, 20, 20, 20)

        # 控制按钮
        self.btnScaleUp = PushButton('放大', self)
        self.btnScaleUp.clicked.connect(self.onScaleUp)

        self.btnScaleDown = PushButton('缩小', self)
        self.btnScaleDown.clicked.connect(self.onScaleDown)

        self.btnToggleRadius = PushButton('切换圆角', self)
        self.btnToggleRadius.clicked.connect(self.onToggleRadius)

        self.statusLabel = BodyLabel('点击按钮操作图像', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.imageLabel, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.gifLabel, 0, Qt.AlignCenter)

        # 控制按钮行
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnScaleUp)
        btnLayout.addWidget(self.btnScaleDown)
        btnLayout.addWidget(self.btnToggleRadius)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onScaleUp(self):
        """放大图像"""
        self.imageLabel.scaledToHeight(min(self.imageLabel.height() + 30, 350))
        self.statusLabel.setText(f'当前高度: {self.imageLabel.height()}px')

    def onScaleDown(self):
        """缩小图像"""
        self.imageLabel.scaledToHeight(max(self.imageLabel.height() - 30, 80))
        self.statusLabel.setText(f'当前高度: {self.imageLabel.height()}px')

    def onToggleRadius(self):
        """切换圆角样式"""
        if self.imageLabel.borderRadius == (10, 10, 10, 10):
            self.imageLabel.setBorderRadius(0, 0, 0, 0)
            self.statusLabel.setText('圆角已关闭')
        else:
            self.imageLabel.setBorderRadius(10, 10, 10, 10)
            self.statusLabel.setText('圆角已开启')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
