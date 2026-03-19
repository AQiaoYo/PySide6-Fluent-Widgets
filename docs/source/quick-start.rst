Quick start
-----------

Install
~~~~~~~

To install lite version (``AcrylicLabel`` is not available) use ``uv``:

.. code:: shell

   uv add PySide6-Fluent-Widgets

Or install the full-featured version:

.. code:: shell

   uv add "PySide6-Fluent-Widgets[full]"

If you prefer ``pip``, the equivalent commands are:

.. code:: shell

   pip install PySide6-Fluent-Widgets -i https://pypi.org/simple/
   pip install "PySide6-Fluent-Widgets[full]" -i https://pypi.org/simple/

This repository maintains the ``PySide6`` branch only.

.. warning:: Don't install PyQt-Fluent-Widgets, PyQt6-Fluent-Widgets, PySide2-Fluent-Widgets and PySide6-Fluent-Widgets at the same time, because their package names are all ``qfluentwidgets``.

Run example
~~~~~~~~~~~

After cloning this repository, sync the environment with ``uv`` and run any
demo in the examples directory, for example:

.. code:: shell

   uv sync
   uv run python examples/gallery/demo.py

If you need the optional dependencies or the documentation environment:

.. code:: shell

   uv sync --extra full --group docs

If you already installed the package from PyPI, you can also run examples like this:

.. code:: shell

   cd examples/gallery
   python demo.py

.. note:: If you encounter ``ImportError: cannot import name 'XXX' from 'qfluentwidgets'``, it indicates that the package version you installed is too low. You can replace the mirror source with https://pypi.org/simple and reinstall again.
