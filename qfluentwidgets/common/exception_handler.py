# coding: utf-8
"""异常处理装饰器"""
from copy import deepcopy



def exceptionHandler(*default):
    """用于异常处理的装饰器

    Args:
        *default: 发生异常时返回的默认值，未提供则返回 None

    Returns:
        用于包装目标函数的装饰器，可捕获异常并返回默认值
    """

    def outer(func):

        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as e:
                value = deepcopy(default)
                if len(value) == 0:
                    return None
                elif len(value) == 1:
                    return value[0]

                return value

        return inner

    return outer