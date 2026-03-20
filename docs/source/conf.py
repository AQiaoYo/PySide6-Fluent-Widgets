# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "qfluentwidgets" / "_version.py"
VERSION_MATCH = re.search(
    r'(?m)^__version__ = "(?P<version>\d+\.\d+\.\d+)"$',
    VERSION_FILE.read_text(encoding="utf-8"),
)
if VERSION_MATCH is None:
    raise RuntimeError(f"Could not read version from {VERSION_FILE}")

PACKAGE_VERSION = VERSION_MATCH.group("version")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PySide6-Fluent-Widgets-Qiao'
copyright = '2026, zhiyiYo, AQiaoYo'
author = 'AQiaoYo'
version = PACKAGE_VERSION
release = f'v{PACKAGE_VERSION}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

source_parsers = {
    '.md': 'recommonmark.parser.CommonMarkParser',
}
source_suffix = ['.rst', '.md']
extensions = ['recommonmark', 'sphinx_markdown_tables']

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "sidebar_hide_name": False,
}

html_show_sourcelink = True
html_title = "PySide6-Fluent-Widgets-Qiao"
html_favicon = "_static/logo.png"
html_css_files = [
    'css/fancybox.css',
    'css/custom.css',
]
html_js_files = [
    'js/fancybox.umd.js',
    'js/fancybox.js',
]

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
