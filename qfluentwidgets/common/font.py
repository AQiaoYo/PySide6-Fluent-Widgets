# coding: utf-8
from typing import List
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from .config import qconfig


def setFontFamilies(families: List[str], save=False):
    """ 设置 font families used by all 部件

    参数
    ----------
    families: 列表[str]
        font family names, default 值 is `['Segoe UI', 'Microsoft YaHei', 'PingFang SC']`

    save: bool
        是否 到 save 更改 到 配置 file
    """
    qconfig.set(qconfig.fontFamilies, families, save)


def fontFamilies() -> List[str]:
    """ 返回 font families used by all 部件 """
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