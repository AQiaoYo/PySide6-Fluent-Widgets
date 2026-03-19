from pathlib import Path

from ..._lazy import LazyExportNames, build_package_exports, export_dir, load_child_module, load_export

_EXPORT_SPEC = """
from .navigation_widget import *
from .navigation_panel import NavigationPanel
from .navigation_types import NavigationItemPosition, NavigationDisplayMode
from .navigation_interface import NavigationInterface
from .navigation_bar import *
from .pivot import *
from .segmented_widget import *
from .breadcrumb import *
"""

_EXPORTS = None


def _exports():
    global _EXPORTS
    if _EXPORTS is None:
        _EXPORTS = build_package_exports(__name__, str(Path(__file__).resolve().parent), _EXPORT_SPEC)

    return _EXPORTS


__all__ = LazyExportNames(_exports)


def __getattr__(name: str):
    exports = _exports()
    if name in exports:
        return load_export(globals(), name, exports)

    return load_child_module(globals(), name)


def __dir__():
    return export_dir(globals(), _exports())
