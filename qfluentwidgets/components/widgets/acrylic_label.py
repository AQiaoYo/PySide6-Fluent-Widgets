# coding: utf-8
"""提供实现亚克力（Acrylic）材质效果的标签组件与相关工具类
包含用于创建 Fluent Design 风格毛玻璃背景的各种控件和辅助线程，适用于需要现代模糊透明视觉效果的界面场景
"""

import warnings
from  typing import Union

from PySide6.QtCore import Qt, QThread, Signal, QRect
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap, QPainterPath
from PySide6.QtWidgets import QLabel, QApplication, QWidget

from ...common.screen import getCurrentScreen

try:
    from ...common.image_utils import gaussianBlur

    isAcrylicAvailable = True
except ImportError as e:
    isAcrylicAvailable = False

    def gaussianBlur(imagePath, blurRadius=18, brightFactor=1, blurPicSize=None):
        return QPixmap(imagePath)


def checkAcrylicAvailability():
    if not isAcrylicAvailable:
        warnings.warn(
            'Acrylic is not supported in current qfluentwidgets, use `pip install PySide6-Fluent-Widgets[full]` to enable it.')

    return isAcrylicAvailable


class BlurCoverThread(QThread):
    """在后台线程中对图像进行高斯模糊处理的线程
    适用于需要避免在主线程执行耗时模糊运算的场景，通过信号将处理后的模糊图像传回主界面进行展示
    """

    blurFinished = Signal(QPixmap)

    def __init__(self, parent=None):
        """
        Args:
            parent: 父对象，默认为 None
        """
        super().__init__(parent)
        self.imagePath = ""
        self.blurRadius = 7
        self.maxSize = None

    def run(self):
        """运行线程，对图像路径进行高斯模糊处理并发射完成信号"""
        if not self.imagePath:
            return

        pixmap = gaussianBlur(
            self.imagePath, self.blurRadius, 0.85, self.maxSize)
        self.blurFinished.emit(pixmap)

    def blur(self, imagePath: str, blurRadius=6, maxSize: tuple = (450, 450)):
        """
        Args:
            imagePath: 图像文件路径
            blurRadius: 模糊半径，默认为 6
            maxSize: 最大模糊尺寸，默认为 (450, 450)
        """
        self.imagePath = imagePath
        self.blurRadius = blurRadius
        self.maxSize = maxSize or self.maxSize
        self.start()


class AcrylicTextureLabel(QLabel):
    """用于渲染亚克力材质纹理层的标签控件
    通常作为 AcrylicLabel 的底层纹理实现，负责叠加噪声纹理与模糊背景以模拟真实的亚克力物理质感
    """

    def __init__(self, tintColor: QColor, luminosityColor: QColor, noiseOpacity=0.03, parent=None):
        """
        Args:
            tintColor: RGB 色调颜色
            luminosityColor: 亮度层颜色
            noiseOpacity: 噪声层不透明度，默认为 0.03
            parent: 父窗口，默认为 None
        """
        super().__init__(parent=parent)
        self.tintColor = QColor(tintColor)
        self.luminosityColor = QColor(luminosityColor)
        self.noiseOpacity = noiseOpacity
        self.noiseImage = QImage(':/qfluentwidgets/images/acrylic/noise.png')
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setTintColor(self, color: QColor):
        """
        Args:
            color: 色调颜色
        """
        self.tintColor = color
        self.update()

    def paintEvent(self, e):
        """绘制亚克力纹理效果"""
        acrylicTexture = QImage(64, 64, QImage.Format_ARGB32_Premultiplied)

        # 绘制luminosity layer
        acrylicTexture.fill(self.luminosityColor)

        # 绘制tint 颜色
        painter = QPainter(acrylicTexture)
        painter.fillRect(acrylicTexture.rect(), self.tintColor)

        # 绘制noise
        painter.setOpacity(self.noiseOpacity)
        painter.drawImage(acrylicTexture.rect(), self.noiseImage)

        acrylicBrush = QBrush(acrylicTexture)
        painter = QPainter(self)
        painter.fillRect(self.rect(), acrylicBrush)


class AcrylicLabel(QLabel):
    """具有亚克力（Acrylic）材质效果的标签控件
    通过叠加模糊背景、色调层和噪声纹理实现 Fluent Design 风格的毛玻璃效果，适合用作卡片背景、侧边栏或弹窗的底层容器
    """

    def __init__(self, blurRadius: int, tintColor: QColor, luminosityColor=QColor(255, 255, 255, 0),
                 maxBlurSize: tuple = None, parent=None):
        """
        Args:
            blurRadius: 模糊半径
            tintColor: 色调颜色
            luminosityColor: 亮度层颜色，默认为 QColor(255, 255, 255, 0)
            maxBlurSize: 最大模糊图像大小，默认为 None
            parent: 父窗口，默认为 None
        """
        super().__init__(parent=parent)
        checkAcrylicAvailability()

        self.imagePath = ''
        self.blurPixmap = QPixmap()
        self.blurRadius = blurRadius
        self.maxBlurSize = maxBlurSize
        self.acrylicTextureLabel = AcrylicTextureLabel(
            tintColor, luminosityColor, parent=self)
        self.blurThread = BlurCoverThread(self)
        self.blurThread.blurFinished.connect(self.__onBlurFinished)

    def __onBlurFinished(self, blurPixmap: QPixmap):
        """模糊完成后的槽函数"""
        self.blurPixmap = blurPixmap
        self.setPixmap(self.blurPixmap)
        self.adjustSize()

    def setImage(self, imagePath: str):
        """设置需要模糊的图像"""
        self.imagePath = imagePath
        self.blurThread.blur(imagePath, self.blurRadius, self.maxBlurSize)

    def setTintColor(self, color: QColor):
        """
        Args:
            color: 色调颜色
        """
        self.acrylicTextureLabel.setTintColor(color)

    def resizeEvent(self, e):
        """处理大小调整事件"""
        super().resizeEvent(e)
        self.acrylicTextureLabel.resize(self.size())

        if not self.blurPixmap.isNull() and self.blurPixmap.size() != self.size():
            self.setPixmap(self.blurPixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))


class AcrylicBrush:
    """用于绘制亚克力材质效果的画笔类
    负责管理模糊图像的生成、色调叠加和性能优化，通常与 AcrylicLabel 配合使用以实现可复用的亚克力背景绘制逻辑
    """

    def __init__(self, device: QWidget, blurRadius: int, tintColor=QColor(242, 242, 242, 150),
                 luminosityColor=QColor(255, 255, 255, 10), noiseOpacity=0.03):
        """
        Args:
            device: 绘制设备
            blurRadius: 模糊半径
            tintColor: 色调颜色，默认为 QColor(242, 242, 242, 150)
            luminosityColor: 亮度层颜色，默认为 QColor(255, 255, 255, 10)
            noiseOpacity: 噪声层不透明度，默认为 0.03
        """
        self.device = device
        self.blurRadius = blurRadius
        self.tintColor = QColor(tintColor)
        self.luminosityColor = QColor(luminosityColor)
        self.noiseOpacity = noiseOpacity
        self.noiseImage = QImage(':/qfluentwidgets/images/acrylic/noise.png')
        self.originalImage = QPixmap()
        self.image = QPixmap()

        self.clipPath = QPainterPath()

    def setBlurRadius(self, radius: int):
        """
        Args:
            radius: 模糊半径
        """
        if radius == self.blurRadius:
            return

        self.blurRadius = radius
        self.setImage(self.originalImage)

    def setTintColor(self, color: QColor):
        """
        Args:
            color: 色调颜色
        """
        self.tintColor = QColor(color)
        self.device.update()

    def setLuminosityColor(self, color: QColor):
        """
        Args:
            color: 亮度层颜色
        """
        self.luminosityColor = QColor(color)
        self.device.update()

    def isAvailable(self):
        """返回亚克力效果是否可用"""
        return isAcrylicAvailable

    def grabImage(self, rect: QRect):
        """从屏幕抓取图像

        Args:
            rect: 抓取区域
        """
        screen = getCurrentScreen()
        if not screen:
            screen = QApplication.screens()[0]

        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        x -= screen.geometry().x()
        y -= screen.geometry().y()
        self.setImage(screen.grabWindow(0, x, y, w, h))

    def setImage(self, image: Union[str, QImage, QPixmap]):
        """设置模糊图像"""
        if isinstance(image, str):
            image = QPixmap(image)
        elif isinstance(image, QImage):
            image = QPixmap.fromImage(image)

        self.originalImage = image
        if not image.isNull():
            checkAcrylicAvailability()

            self.image = gaussianBlur(image, self.blurRadius)

        self.device.update()

    def setClipPath(self, path: QPainterPath):
        """
        Args:
            path: 裁剪路径
        """
        self.clipPath = path
        self.device.update()

    def textureImage(self):
        """返回亚克力纹理图像"""
        texture = QImage(64, 64, QImage.Format_ARGB32_Premultiplied)
        texture.fill(self.luminosityColor)

        # 绘制tint 颜色
        painter = QPainter(texture)
        painter.fillRect(texture.rect(), self.tintColor)

        # 绘制noise
        painter.setOpacity(self.noiseOpacity)
        painter.drawImage(texture.rect(), self.noiseImage)

        return texture

    def paint(self):
        """绘制亚克力效果"""
        device = self.device

        painter = QPainter(device)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.clipPath.isEmpty():
            painter.setClipPath(self.clipPath)

        # 绘制图像
        image = self.image.scaled(device.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, image)

        # 绘制亚克力 texture
        painter.fillRect(device.rect(), QBrush(self.textureImage()))