# coding: utf-8
"""路由管理模块，提供基于 QStackedWidget 的路由导航功能"""

from typing import Dict, List
from itertools import groupby

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QWidget, QStackedWidget


class RouteItem:
    """路由项，用于标识堆叠部件中的子界面"""

    def __init__(self, stacked: QStackedWidget, routeKey: str):
        self.stacked = stacked
        self.routeKey = routeKey

    def __eq__(self, other):
        if other is None:
            return False

        return other.stacked is self.stacked and self.routeKey == other.routeKey


class StackedHistory:
    """堆叠部件路由历史记录，管理单个 QStackedWidget 的页面切换历史"""

    def __init__(self, stacked: QStackedWidget):
        self.stacked = stacked
        self.defaultRouteKey = None  # type: str
        self.history = [self.defaultRouteKey]   # type: 列表[str]

    def __len__(self):
        return len(self.history)

    def isEmpty(self):
        return len(self) <= 1

    def push(self, routeKey: str):
        if self.history[-1] == routeKey:
            return False

        self.history.append(routeKey)
        return True

    def pop(self):
        if self.isEmpty():
            return

        self.history.pop()
        self.goToTop()

    def remove(self, routeKey: str):
        if routeKey not in self.history:
            return

        self.history[1:] = [i for i in self.history[1:] if i != routeKey]
        self.history = [k for k, g in groupby(self.history)]
        self.goToTop()

    def top(self):
        return self.history[-1]

    def setDefaultRouteKey(self, routeKey: str):
        self.defaultRouteKey = routeKey
        self.history[0] = routeKey

    def goToTop(self):
        w = self.stacked.findChild(QWidget, self.top())
        if w:
            self.stacked.setCurrentWidget(w)


class Router(QObject):
    """路由管理器，维护全局路由栈和各堆叠部件的历史记录"""

    emptyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.history = []   # type: 列表[RouteItem]
        self.stackHistories = {}  # type: Dict[QStackedWidget, StackedHistory]

    def setDefaultRouteKey(self, stacked: QStackedWidget, routeKey: str):
        """设置堆叠部件的默认路由键

        Args:
            stacked: 堆叠部件
            routeKey: 默认路由键
        """
        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        self.stackHistories[stacked].setDefaultRouteKey(routeKey)

    def push(self, stacked: QStackedWidget, routeKey: str):
        """压入路由历史记录

        Args:
            stacked: 堆叠部件
            routeKey: 子界面的路由键，应与该子界面的 objectName 一致
        """
        item = RouteItem(stacked, routeKey)

        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        # don't 添加 duplicated history
        success = self.stackHistories[stacked].push(routeKey)
        if success:
            self.history.append(item)

        self.emptyChanged.emit(not bool(self.history))

    def pop(self):
        """弹出当前路由历史记录并回退到上一个页面"""
        if not self.history:
            return

        item = self.history.pop()
        self.emptyChanged.emit(not bool(self.history))
        self.stackHistories[item.stacked].pop()

    def remove(self, routeKey: str):
        """移除指定路由键对应的历史记录

        Args:
            routeKey: 要移除的路由键
        """
        self.history = [i for i in self.history if i.routeKey != routeKey]
        self.history = [list(g)[0] for k, g in groupby(self.history, lambda i: i.routeKey)]
        self.emptyChanged.emit(not bool(self.history))

        for stacked, history in self.stackHistories.items():
            w = stacked.findChild(QWidget, routeKey)
            if w:
                return history.remove(routeKey)


qrouter = Router()