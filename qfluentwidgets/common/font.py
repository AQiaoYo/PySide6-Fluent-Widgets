# coding: utf-8
"""字体工具模块"""

from typing import List
from PySide6.QtGui import QFont
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget

from .config import qconfig


def setFontFamilies(families: List[str], save=False):
    """设置所有部件使用的字体族

    Args:
        families: 字体族名称列表, 默认值为 `['Segoe UI', 'Microsoft YaHei', 'PingFang SC']`
        save: 是否将更改保存到配置文件
    """
    qconfig.set(qconfig.fontFamilies, families, save)


def fontFamilies() -> List[str]:
    """返回所有部件使用的字体族"""
    return qconfig.get(qconfig.fontFamilies).copy()


def setFont(widget: QWidget, fontSize=14, weight=QFont.Normal):
    """设置部件的字体

    Args:
        widget: 要设置字体的部件
        fontSize: 字体像素大小
        weight: 字体粗细
    """
    widget.setFont(getFont(fontSize, weight))


def getFont(fontSize=14, weight=QFont.Normal):
    """创建字体

    Args:
        fontSize: 字体像素大小
        weight: 字体粗细
    """
    font = QFont()
    font.setFamilies(qconfig.get(qconfig.fontFamilies))
    font.setPointSizeF(fontSize * 72 / _logical_dpi())
    font.setWeight(weight)
    return font


def fontPixelSize(font: QFont) -> int:
    """返回字体当前等效的像素大小"""
    pixel_size = font.pixelSize()
    if pixel_size > 0:
        return pixel_size

    point_size = font.pointSizeF()
    if point_size > 0:
        return round(point_size * _logical_dpi() / 72)

    return 14


def fontStyleSheet(font: QFont):
    """返回样式表的字体"""
    families = []
    for family in font.families():
        families.append(f"'{family}'")

    qss = f"font: {fontPixelSize(font)}px {','.join(families)}"
    return qss


def _logical_dpi() -> float:
    """返回逻辑 DPI"""
    app = QGuiApplication.instance()
    screen = app.primaryScreen() if app is not None else None
    dpi = screen.logicalDotsPerInchY() if screen is not None else 96.0
    return dpi or 96.0