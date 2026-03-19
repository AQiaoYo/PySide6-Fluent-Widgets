"""
PySide6-Fluent-Widgets-Qiao
===========================
A fluent design widgets library based on PySide6.

Documentation is available in the docstrings and
online at https://github.com/AQiaoYo/PySide6-Fluent-Widgets#readme.

Examples are available at https://github.com/AQiaoYo/PySide6-Fluent-Widgets/tree/main/examples.

:copyright: (c) 2021 by zhiyiYo, fork maintained by AQiaoYo.
:license: GPLv3 for non-commercial project, see README for more details.
"""

from importlib import import_module
from pathlib import Path

from ._lazy import LazyExportNames, build_package_exports, export_dir, load_child_module, load_export

__version__ = "1.11.1"
__author__ = "AQiaoYo"
__maintainer__ = "AQiaoYo"
__maintainer_email__ = "AQiaoYo@qq.com"
__credits__ = ["zhiyiYo", "AQiaoYo"]

_EXPORT_SPEC = """
from .components import *
from .common import *
from .window import *
from ._rc import resource
"""

_EXPORTS = None


def _exports():
    global _EXPORTS
    if _EXPORTS is None:
        _EXPORTS = build_package_exports(__name__, str(Path(__file__).resolve().parent), _EXPORT_SPEC)
        _EXPORTS["resource"] = "qfluentwidgets._rc.resource"

    return _EXPORTS


def _all_exports():
    names = {
        "__version__": None,
        "__author__": None,
        "__maintainer__": None,
        "__maintainer_email__": None,
        "__credits__": None,
    }
    names.update(_exports())
    return names

# Resource registration must happen during package import so qrc icon paths
# are available before any widget/icon class is first accessed.
resource = import_module("qfluentwidgets._rc.resource")

__all__ = LazyExportNames(_all_exports)


def __getattr__(name: str):
    exports = _exports()
    if name in exports:
        return load_export(globals(), name, exports)

    return load_child_module(globals(), name)


def __dir__():
    return export_dir(globals(), _exports())
