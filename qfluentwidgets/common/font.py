# coding: utf-8
from typing import List
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from .config import qconfig


def setFontFamilies(families: List[str], save=False):
    """设置所有部件使用的字体族.

    参数
    ----------
    families: 列表[str]
        字体族名称列表, 默认值为 `['Segoe UI', 'Microsoft YaHei', 'PingFang SC']`.

    save: bool
        是否将更改保存到配置文件.
    """
    qconfig.set(qconfig.fontFamilies, families, save)


def fontFamilies() -> List[str]:
    """返回所有部件使用的字体族."""
    return qconfig.get(qconfig.fontFamilies).copy()


def setFont(widget: QWidget, fontSize=14, weight=QFont.Normal):
    """ 设置部件的font

    参数
    ----------
    widget: QWidget
        部件 到 设置 font

    fontSize: int
        font pixel 大小

    weight: `QFont.Weight`
        font weight
    """
    widget.setFont(getFont(fontSize, weight))


def getFont(fontSize=14, weight=QFont.Normal):
    """ 创建font

    参数
    ----------
    fontSize: int
        font pixel 大小

    weight: `QFont.Weight`
        font weight
    """
    font = QFont()
    font.setFamilies(qconfig.get(qconfig.fontFamilies))
    font.setPixelSize(fontSize)
    font.setWeight(weight)
    return font


def fontStyleSheet(font: QFont):
    """ 返回 样式表 的 font """
    families = []
    for family in font.families():
        families.append(f"'{family}'")

    qss = f"font: {font.pixelSize()}px {','.join(families)}"
    return qss
