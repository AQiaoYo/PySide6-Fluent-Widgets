# coding: utf-8
"""导航类型定义"""

from enum import Enum


class NavigationDisplayMode(Enum):
    """导航显示模式"""

    MINIMAL = 0
    COMPACT = 1
    EXPAND = 2
    MENU = 3


class NavigationItemPosition(Enum):
    """导航项位置"""

    TOP = 0
    SCROLL = 1
    BOTTOM = 2


class RouteKeyError(Exception):
    """路由键错误"""