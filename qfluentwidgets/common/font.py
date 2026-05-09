# coding: utf-8
"""字体工具模块"""

import logging
from typing import List
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
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


logger = logging.getLogger(__name__)


class FontManager:
    """字体管理器，用于加载和管理通过 QRC 内嵌的自定义字体"""

    _font_loaded = False
    _loaded_families: list[str] = []

    @classmethod
    def initialize_fonts(cls) -> None:
        """初始化内嵌字体，仅在首次调用时加载"""
        if not cls._font_loaded:
            cls._load_single_font(":/qfluentwidgets/font/JB-MAPLE.ttf")
            cls._font_loaded = True

    @classmethod
    def _load_single_font(cls, font_path: str) -> str:
        """加载单个字体并返回字体家族"""
        if (font_id := QFontDatabase.addApplicationFont(font_path)) == -1:
            logger.error(f"字体加载失败: {font_path}")
            return ""

        if font_families := QFontDatabase.applicationFontFamilies(font_id):
            for family in font_families:
                if family not in cls._loaded_families:
                    cls._loaded_families.append(family)
            logger.debug(f"字体加载成功: {font_families[0]}")
            return font_families[0]

        logger.error(f"未找到字体家族: {font_path}")
        return ""

    @classmethod
    def code_font_families(cls) -> list[str]:
        """返回代码编辑器优先使用的等宽字体栈"""
        cls.initialize_fonts()
        preferred = [
            family for family in cls._loaded_families
            if "maple" in family.lower() or "mono" in family.lower()
        ]
        fallback = [
            "Cascadia Mono",
            "Cascadia Code",
            "JetBrains Mono",
            "Consolas",
            "Microsoft YaHei UI",
        ]

        result: list[str] = []
        for family in preferred + fallback:
            if family not in result:
                result.append(family)

        return result

    @classmethod
    def loaded_families(cls) -> list[str]:
        """返回所有已加载的自定义字体家族名称"""
        return cls._loaded_families.copy()