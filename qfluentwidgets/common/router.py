# coding: utf-8
"""路由管理模块，提供基于 QStackedWidget 的路由导航功能

通过 Router 单例管理多个堆叠部件的导航历史，支持页面跳转、返回和路由状态追踪
适用于多页面应用的层级导航场景，可与 SubtitleInterface 等组件配合实现面包屑或标签导航
"""

from typing import Dict, List
from itertools import groupby

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QWidget, QStackedWidget


class RouteItem:
    """路由项，用于标识堆叠部件中的子界面
    
    将 QStackedWidget 中的子页面与唯一路由键绑定，便于 Router 进行页面定位和历史追踪
    通常在自定义接口类中作为内部标识使用，不建议直接在外部手动创建
    """

    def __init__(self, stacked: QStackedWidget, routeKey: str):
        """初始化路由项
        
        Args:
            stacked (QStackedWidget): 子界面所属的堆叠部件
            routeKey (str): 路由唯一标识键，用于在 Router 中定位对应页面
        """
        self.stacked = stacked
        self.routeKey = routeKey

    def __eq__(self, other):
        if other is None:
            return False

        return other.stacked is self.stacked and self.routeKey == other.routeKey


class StackedHistory:
    """堆叠部件路由历史记录，管理单个 QStackedWidget 的页面切换历史
    
    维护当前堆叠部件内页面切换的先后顺序，支持前进、后退以及历史栈清理
    每个 QStackedWidget 对应一个 StackedHistory 实例，由 Router 统一管理和调度
    """

    def __init__(self, stacked: QStackedWidget):
        """初始化历史记录管理器
        
        Args:
            stacked (QStackedWidget): 需要管理切换历史的堆叠部件
        """
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
    """路由管理器，维护全局路由栈和各堆叠部件的历史记录
    
    以单例形式提供全局路由导航能力，自动为注册的 QStackedWidget 创建 StackedHistory
    常用于多层级页面应用，支持通过 routeKey 在不同子界面间跳转并自动维护后退栈
    """

    emptyChanged = Signal(bool)

    def __init__(self, parent=None):
        """初始化路由管理器
        
        Args:
            parent (QObject): 父对象
        """
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