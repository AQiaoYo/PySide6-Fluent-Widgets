# coding:utf-8
from enum import Enum


class NavigationDisplayMode(Enum):
    """ Navigation display mode """

    MINIMAL = 0
    COMPACT = 1
    EXPAND = 2
    MENU = 3


class NavigationItemPosition(Enum):
    """ Navigation item position """

    TOP = 0
    SCROLL = 1
    BOTTOM = 2


class RouteKeyError(Exception):
    """ Route key error """
