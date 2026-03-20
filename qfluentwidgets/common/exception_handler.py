# coding: utf-8
from copy import deepcopy



def exceptionHandler(*default):
    """ decorator 用于 exception handling

    参数
    ----------
    *default:
        default 值 returned 当 exception occurs
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
