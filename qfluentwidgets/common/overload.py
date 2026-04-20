# coding: utf-8
"""基于单分派的泛型方法装饰器

该模块提供根据首个参数类型自动分发调用逻辑的装饰器工具，适用于需要为同一方法针对不同类型实现差异化处理的场景，可有效降低复杂类型分支判断的维护成本
"""

from functools import singledispatch, update_wrapper


class singledispatchmethod:
    """单分派泛型方法描述符

    支持包装现有描述符，并将非描述符可调用对象作为实例方法处理
    """

    def __init__(self, func):
        """初始化泛型方法分发器
        
        Args:
            func (Callable): 默认处理函数，当未匹配到注册类型时调用该函数处理请求，通常作为泛型方法的通用回退实现
        """
        if not callable(func) and not hasattr(func, "__get__"):
            raise TypeError(f"{func!r} is not callable or a descriptor")

        self.dispatcher = singledispatch(func)
        self.func = func

    def register(self, cls, method=None):
        """注册给定类型的新实现

        Args:
            cls: 要注册的类型
            method: 要注册的方法，默认为 None

        Returns:
            注册的方法
        """
        return self.dispatcher.register(cls, func=method)

    def __get__(self, obj, cls=None):
        def _method(*args, **kwargs):
            if args:
                method = self.dispatcher.dispatch(args[0].__class__)
            else:
                method = self.func
                for v in kwargs.values():
                    if v.__class__ in self.dispatcher.registry:
                        method = self.dispatcher.dispatch(v.__class__)
                        if method is not self.func:
                            break

            return method.__get__(obj, cls)(*args, **kwargs)

        _method.__isabstractmethod__ = self.__isabstractmethod__
        _method.register = self.register
        update_wrapper(_method, self.func)
        return _method

    @property
    def __isabstractmethod__(self):
        return getattr(self.func, '__isabstractmethod__', False)