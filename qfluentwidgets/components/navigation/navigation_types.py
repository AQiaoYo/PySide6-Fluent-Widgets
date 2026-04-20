# coding: utf-8
"""定义导航组件中使用的类型枚举与异常

 这些类型用于控制导航栏的显示模式、导航项的排布位置，以及在路由不匹配时抛出异常，是构建自定义导航界面的基础类型定义
"""

from enum import Enum


class NavigationDisplayMode(Enum):
    """枚举导航栏的显示模式
    
     用于设置 NavigationInterface 在不同窗口宽度下的展开、折叠或最小化表现，可通过 setDisplayMode() 方法应用到导航组件
     包含最小化、紧凑、展开和菜单等模式，适用于需要响应式布局的侧边导航场景
    """

    MINIMAL = 0
    COMPACT = 1
    EXPAND = 2
    MENU = 3


class NavigationItemPosition(Enum):
    """枚举导航项在导航栏中的排布位置
    
     用于 addItem()、addWidget() 等方法中指定导航项应放置在顶部固定区、可滚动区还是底部固定区
     顶部项通常放置高频功能入口，底部项适合放置设置与用户信息，可滚动区用于承载大量中间菜单
    """

    TOP = 0
    SCROLL = 1
    BOTTOM = 2


class RouteKeyError(Exception):
    """路由键不存在或发生冲突时抛出的异常
    
     在通过路由键查找导航项、切换界面或注册重复键时由导航接口抛出，提示开发者检查路由键的正确性与唯一性
    """
