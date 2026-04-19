# coding:utf-8
"""
AcrylicBrush 演示

展示内容：
- 亚克力笔刷效果
- 自定义裁剪路径（圆形、矩形）
- 图像缩放与填充
- 背景模糊强度调整
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets.components.widgets.acrylic_label import AcrylicBrush
from qfluentwidgets import PushButton, BodyLabel


class Demo(QWidget):
    """AcrylicBrush 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicBrush - 演示')
        self.resize(500, 450)
        self.initWidgets()
        self.initLayout()
        self.clipMode = 'circle'

    def initWidgets(self):
        """初始化亚克力笔刷组件"""
        # 圆形亚克力效果
        self.circleBrush = AcrylicBrush(self, 15)
        self._setupBrush(self.circleBrush, 'circle')

        # 矩形亚克力效果
        self.rectBrush = AcrylicBrush(self, 15)
        self._setupBrush(self.rectBrush, 'rect')

        # 控制按钮
        self.btnToggleShape = PushButton('切换形状', self)
        self.btnToggleShape.clicked.connect(self.onToggleShape)

        self.btnStrongBlur = PushButton('增强模糊', self)
        self.btnStrongBlur.clicked.connect(self.onStrongBlur)

        self.statusLabel = BodyLabel('亚克力笔刷效果演示', self)

    def _setupBrush(self, brush, mode):
        """配置笔刷的裁剪路径和图像"""
        path = QPainterPath()
        if mode == 'circle':
            path.addEllipse(0, 0, 200, 200)
        else:
            path.addRect(0, 0, 200, 150)
        brush.setClipPath(path)

        try:
            pixmap = QPixmap('resource/shoko.png')
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                brush.setImage(scaled)
        except Exception:
            pass

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        # 笔刷预览区域（通过 paintEvent 绘制）
        self.setMinimumHeight(400)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addWidget(self.btnToggleShape)
        btnLayout.addWidget(self.btnStrongBlur)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel)

    def paintEvent(self, e):
        """绘制亚克力效果"""
        if self.clipMode == 'circle':
            self.circleBrush.paint()
        else:
            self.rectBrush.paint()
        super().paintEvent(e)

    def onToggleShape(self):
        """切换裁剪形状"""
        self.clipMode = 'rect' if self.clipMode == 'circle' else 'circle'
        self.statusLabel.setText(f'当前形状: {"圆形" if self.clipMode == "circle" else "矩形"}')
        self.update()

    def onStrongBlur(self):
        """增强模糊效果"""
        self.circleBrush = AcrylicBrush(self, 30)
        self._setupBrush(self.circleBrush, 'circle')
        self.rectBrush = AcrylicBrush(self, 30)
        self._setupBrush(self.rectBrush, 'rect')
        self.statusLabel.setText('模糊强度已增强')
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
