# coding: utf-8
"""图像处理工具模块"""
from math import floor
from io import BytesIO
from typing import Union

import numpy as np
from colorthief import ColorThief
from PIL import Image
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QIODevice, QBuffer
from scipy.ndimage.filters import gaussian_filter

from .exception_handler import exceptionHandler



def gaussianBlur(image, blurRadius=18, brightFactor=1, blurPicSize= None):
    """对图像进行高斯模糊处理

    Args:
        image: 图像路径字符串或 QPixmap 对象
        blurRadius: 高斯模糊半径，默认 18
        brightFactor: 亮度调整因子，默认 1
        blurPicSize: 模糊处理的图像尺寸限制，用于降低计算量

    Returns:
        模糊后的 QPixmap 对象
    """
    if isinstance(image, str) and not image.startswith(':'):
        image = Image.open(image)
    else:
        image = fromqpixmap(QPixmap(image))

    if blurPicSize:
        # 调整图像 大小 到 reduce computation
        w, h = image.size
        ratio = min(blurPicSize[0] / w, blurPicSize[1] / h)
        w_, h_ = w * ratio, h * ratio

        if w_ < w:
            image = image.resize((int(w_), int(h_)), Image.ANTIALIAS)

    image = np.array(image)

    # 处理 灰度 图像
    if len(image.shape) == 2:
        image = np.stack([image, image, image], axis=-1)

    # blur each channel
    for i in range(3):
        image[:, :, i] = gaussian_filter(
            image[:, :, i], blurRadius) * brightFactor

    # 将ndarray转换为QPixmap
    h, w, c = image.shape
    if c == 3:
        format = QImage.Format_RGB888
    else:
        format = QImage.Format_RGBA8888

    return QPixmap.fromImage(QImage(image.data, w, h, c*w, format))


# https://github.com/python-pillow/Pillow/blob/main/src/PIL/ImageQt.py
def fromqpixmap(im: Union[QImage, QPixmap]):
    """将 QPixmap/QImage 转换为 PIL Image 对象

    Args:
        im: QImage 或 QPixmap 对象

    Returns:
        PIL Image 对象
    """
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.ReadWrite)

    # 需要保留透明通道时使用 png.
    # 否则使用更适合 Image.open() 读取的 ppm.
    if im.hasAlphaChannel():
        im.save(buffer, "png")
    else:
        im.save(buffer, "ppm")

    b = BytesIO()
    b.write(buffer.data())
    buffer.close()
    b.seek(0)

    return Image.open(b)


class DominantColor:
    """主色提取工具类"""

    @classmethod
    @exceptionHandler((24, 24, 24))
    def getDominantColor(cls, imagePath):
        """从图像中提取主色

        Args:
            imagePath: 图像路径

        Returns:
            主色的 RGB 元组，格式为 (r, g, b)
        """
        if imagePath.startswith(':'):
            return (24, 24, 24)

        colorThief = ColorThief(imagePath)

        # 缩放图像以加快计算.
        if max(colorThief.image.size) > 400:
            colorThief.image = colorThief.image.resize((400, 400))

        palette = colorThief.get_palette(quality=9)

        # 调整调色板亮度.
        palette = cls.__adjustPaletteValue(palette)
        for rgb in palette[:]:
            h, s, v = cls.rgb2hsv(rgb)
            if h < 0.02:
                palette.remove(rgb)
                if len(palette) <= 2:
                    break

        palette = palette[:5]
        palette.sort(key=lambda rgb: cls.colorfulness(*rgb), reverse=True)

        return palette[0]

    @classmethod
    def __adjustPaletteValue(cls, palette):
        """调整调色板亮度

        Args:
            palette: 原始调色板

        Returns:
            调整亮度后的新调色板
        """
        newPalette = []
        for rgb in palette:
            h, s, v = cls.rgb2hsv(rgb)
            if v > 0.9:
                factor = 0.8
            elif 0.8 < v <= 0.9:
                factor = 0.9
            elif 0.7 < v <= 0.8:
                factor = 0.95
            else:
                factor = 1
            v *= factor
            newPalette.append(cls.hsv2rgb(h, s, v))

        return newPalette

    @staticmethod
    def rgb2hsv(rgb):
        """将 RGB 转换为 HSV

        Args:
            rgb: RGB 颜色元组

        Returns:
            HSV 颜色元组
        """
        r, g, b = [i / 255 for i in rgb]
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        s = 0 if mx == 0 else df / mx
        v = mx
        return (h, s, v)

    @staticmethod
    def hsv2rgb(h, s, v):
        """将 HSV 转换为 RGB

        Args:
            h: 色相
            s: 饱和度
            v: 明度

        Returns:
            RGB 颜色元组
        """
        h60 = h / 60.0
        h60f = floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0:
            r, g, b = v, t, p
        elif hi == 1:
            r, g, b = q, v, p
        elif hi == 2:
            r, g, b = p, v, t
        elif hi == 3:
            r, g, b = p, q, v
        elif hi == 4:
            r, g, b = t, p, v
        elif hi == 5:
            r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return (r, g, b)

    @staticmethod
    def colorfulness(r: int, g: int, b: int):
        """计算色彩度

        Args:
            r: 红色通道值
            g: 绿色通道值
            b: 蓝色通道值

        Returns:
            色彩度数值
        """
        rg = np.absolute(r - g)
        yb = np.absolute(0.5 * (r + g) - b)

        # Compute mean 和 标准 deviation 的 both `rg` 和 `yb`.
        rg_mean, rg_std = (np.mean(rg), np.std(rg))
        yb_mean, yb_std = (np.mean(yb), np.std(yb))

        # Combine mean 和 标准 deviations.
        std_root = np.sqrt((rg_std ** 2) + (yb_std ** 2))
        mean_root = np.sqrt((rg_mean ** 2) + (yb_mean ** 2))

        return std_root + (0.3 * mean_root)