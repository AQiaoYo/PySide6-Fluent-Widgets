# coding: utf-8
from enum import Enum


class NavigationDisplayMode(Enum):
    """ Navigation display 模式 """

    MINIMAL = 0
    COMPACT = 1
    EXPAND = 2
    MENU = 3


class NavigationItemPosition(Enum):
    """ Navigation 项 位置 """

    TOP = 0
    SCROLL = 1
    BOTTOM = 2


class RouteKeyError(Exception):
    """ 路由键 错误 """