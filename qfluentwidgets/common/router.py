# coding: utf-8
from typing import Dict, List
from itertools import groupby

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QWidget, QStackedWidget


class RouteItem:
    """ Route 项 """

    def __init__(self, stacked: QStackedWidget, routeKey: str):
        self.stacked = stacked
        self.routeKey = routeKey

    def __eq__(self, other):
        if other is None:
            return False

        return other.stacked is self.stacked and self.routeKey == other.routeKey


class StackedHistory:
    """ Stacked history """

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
    """ Router """

    emptyChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.history = []   # type: 列表[RouteItem]
        self.stackHistories = {}  # type: Dict[QStackedWidget, StackedHistory]

    def setDefaultRouteKey(self, stacked: QStackedWidget, routeKey: str):
        """ 设置stacked 部件的default 路由键 """
        if stacked not in self.stackHistories:
            self.stackHistories[stacked] = StackedHistory(stacked)

        self.stackHistories[stacked].setDefaultRouteKey(routeKey)

    def push(self, stacked: QStackedWidget, routeKey: str):
        """ push history

        参数
        ----------
        stacked: QStackedWidget
            stacked 部件

        routeKey: str
            路由键 的 sub insterface, it should be 对象 name 的 子界面
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
        """ pop history """
        if not self.history:
            return

        item = self.history.pop()
        self.emptyChanged.emit(not bool(self.history))
        self.stackHistories[item.stacked].pop()

    def remove(self, routeKey: str):
        """ 移除 history """
        self.history = [i for i in self.history if i.routeKey != routeKey]
        self.history = [list(g)[0] for k, g in groupby(self.history, lambda i: i.routeKey)]
        self.emptyChanged.emit(not bool(self.history))

        for stacked, history in self.stackHistories.items():
            w = stacked.findChild(QWidget, routeKey)
            if w:
                return history.remove(routeKey)


qrouter = Router()