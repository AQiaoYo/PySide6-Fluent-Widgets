from pathlib import Path

from .._lazy import LazyExportNames, build_package_exports, export_dir, load_child_module, load_export

_EXPORT_SPEC = """
from .config import *
from .font import setFont, getFont, setFontFamilies, fontFamilies, fontStyleSheet
from .auto_wrap import TextWrap
from .icon import Action, Icon, getIconColor, drawSvgIcon, FluentIcon, drawIcon, FluentIconBase, writeSvg, FluentFontIconBase
from .style_sheet import (setStyleSheet, getStyleSheet, setTheme, ThemeColor, themeColor,
                          setThemeColor, applyThemeColor, FluentStyleSheet, StyleSheetBase,
                          StyleSheetFile, StyleSheetCompose, CustomStyleSheet, toggleTheme, setCustomStyleSheet, renderQss)
from .smooth_scroll import SmoothScroll, SmoothMode
from .translator import FluentTranslator
from .router import qrouter, Router
from .color import FluentThemeColor, FluentSystemColor
from .theme_listener import SystemThemeListener
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
