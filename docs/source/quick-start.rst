Quick start
-----------

Install
~~~~~~~

To install lite version (``AcrylicLabel`` is not available) use ``uv``:

.. code:: shell

   uv add PySide6-Fluent-Widgets-Qiao

Or install the full-featured version:

.. code:: shell

   uv add "PySide6-Fluent-Widgets-Qiao[full]"

If you prefer ``pip``, the equivalent commands are:

.. code:: shell

   pip install PySide6-Fluent-Widgets-Qiao -i https://pypi.org/simple/
   pip install "PySide6-Fluent-Widgets-Qiao[full]" -i https://pypi.org/simple/

This fork publishes to PyPI as ``PySide6-Fluent-Widgets-Qiao`` while keeping the import package name ``qfluentwidgets``.

.. warning:: Don't install PyQt-Fluent-Widgets, PyQt6-Fluent-Widgets, PySide2-Fluent-Widgets, PySide6-Fluent-Widgets, and PySide6-Fluent-Widgets-Qiao at the same time, because they all expose the same import package name ``qfluentwidgets``.

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
