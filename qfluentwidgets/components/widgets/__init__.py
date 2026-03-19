from pathlib import Path

from ..._lazy import LazyExportNames, build_package_exports, export_dir, load_child_module, load_export

_EXPORT_SPEC = """
from .button import *
from .card_widget import *
from .check_box import *
from .combo_box import *
from .model_combo_box import *
from .command_bar import *
from .flip_view import *
from .line_edit import *
from .icon_widget import *
from .label import *
from .list_view import *
from .menu import *
from .info_bar import *
from .info_badge import *
from .scroll_area import *
from .slider import *
from .spin_box import *
from .stacked_widget import *
from .state_tool_tip import *
from .switch_button import *
from .table_view import *
from .tool_tip import *
from .tree_view import *
from .cycle_list_widget import *
from .progress_bar import *
from .progress_ring import *
from .scroll_bar import *
from .teaching_tip import *
from .flyout import *
from .tab_view import *
from .pips_pager import *
from .separator import *
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
