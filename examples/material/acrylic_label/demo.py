# coding:utf-8
"""
AcrylicLabel 演示

展示内容：
- 亚克力标签效果
- 不同模糊半径对比
- 图像与颜色叠加
- 圆角与尺寸调整
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets.components.widgets.acrylic_label import AcrylicLabel
from qfluentwidgets import PushButton, BodyLabel


class Demo(QWidget):
    """AcrylicLabel 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicLabel - 演示')
        self.resize(600, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化亚克力标签组件"""
        # 不同模糊半径的标签
        self.labelLight = AcrylicLabel(10, QColor(105, 114, 168, 80), self)
        self.labelLight.setFixedSize(180, 120)
        self._setLabelImage(self.labelLight)

        self.labelMedium = AcrylicLabel(25, QColor(105, 114, 168, 120), self)
        self.labelMedium.setFixedSize(180, 120)
        self._setLabelImage(self.labelMedium)

        self.labelHeavy = AcrylicLabel(40, QColor(105, 114, 168, 160), self)
        self.labelHeavy.setFixedSize(180, 120)
        self._setLabelImage(self.labelHeavy)

        # 控制按钮
        self.btnChangeImage = PushButton('切换图像', self)
        self.btnChangeImage.clicked.connect(self.onChangeImage)

        self.statusLabel = BodyLabel('模糊半径: 10 / 25 / 40', self)

    def _setLabelImage(self, label):
        """设置标签图像"""
        try:
            label.setImage('resource/shoko.png')
        except Exception:
            label.setStyleSheet('background-color: #6a71a8;')

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        labelLayout = QHBoxLayout()
        labelLayout.setSpacing(16)
        labelLayout.addWidget(self.labelLight)
        labelLayout.addWidget(self.labelMedium)
        labelLayout.addWidget(self.labelHeavy)
        labelLayout.addStretch(1)
        mainLayout.addLayout(labelLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.btnChangeImage, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onChangeImage(self):
        """切换显示内容"""
        self.statusLabel.setText('图像切换功能演示（需要有效图像文件）')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
