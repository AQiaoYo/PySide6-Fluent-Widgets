<p align="center">
  <img width="18%" align="center" src="https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/master/docs/source/_static/logo.png" alt="logo">
</p>
  <h1 align="center">
  PySide6-Fluent-Widgets-Qiao
</h1>
<p align="center">
  A fluent design widgets library based on PySide6
</p>

<div align="center">

[![Version](https://img.shields.io/pypi/v/pyside6-fluent-widgets-qiao?color=%2334D058&label=Version)](https://pypi.org/project/PySide6-Fluent-Widgets-Qiao/)
[![Download](https://static.pepy.tech/personalized-badge/pyside6-fluent-widgets-qiao?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)]()
[![GPLv3](https://img.shields.io/badge/License-GPLv3-blue?color=#4ec820)](LICENSE)
[![Platform Win32 | Linux | macOS](https://img.shields.io/badge/Platform-Win32%20|%20Linux%20|%20macOS-blue?color=#4ec820)]()

</div>


<p align="center">
English | <a href="docs/README_zh.md">简体中文</a> | <a href="https://github.com/AQiaoYo/PySide6-Fluent-Widgets">GitHub</a>
</p>

![Interface](https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/master/docs/source/_static/Interface.jpg)


## Install
Use `uv` to install the lite version:
```shell
uv add PySide6-Fluent-Widgets-Qiao
```

Or install the full-featured version (`AcrylicLabel` is available):
```shell
uv add "PySide6-Fluent-Widgets-Qiao[full]"
```

If you prefer `pip`, the equivalent commands are:
```shell
pip install PySide6-Fluent-Widgets-Qiao -i https://pypi.org/simple/
pip install "PySide6-Fluent-Widgets-Qiao[full]" -i https://pypi.org/simple/
```

This fork keeps the `qfluentwidgets` import name for compatibility, while publishing to PyPI as `PySide6-Fluent-Widgets-Qiao`.

The project repository is hosted at [AQiaoYo/PySide6-Fluent-Widgets](https://github.com/AQiaoYo/PySide6-Fluent-Widgets).

> [!Warning]
> Don't install `PyQt-Fluent-Widgets`, `PyQt6-Fluent-Widgets`, `PySide2-Fluent-Widgets`, `PySide6-Fluent-Widgets`, and `PySide6-Fluent-Widgets-Qiao` at the same time, because they all expose the same import package name: `qfluentwidgets`.


## Run Example
After cloning this repository, use `uv` to create the environment and run examples:
```shell
uv sync
uv run python examples/gallery/demo.py
```

If you need the optional dependencies or documentation environment:
```shell
uv sync --extra full --group docs
```

You can also work with the package directly after installing it from PyPI. For example:
```shell
cd examples/gallery
python demo.py
```

If you encounter `ImportError: cannot import name 'XXX' from 'qfluentwidgets'`, it indicates that the package version you installed is too low. You can replace the mirror source with https://pypi.org/simple and reinstall again.

## Development
Common project commands with `uv`:
```shell
uv run python scripts/bump_version.py
uv run python scripts/bump_version.py 2.1.0
uv run python scripts/bump_version.py --tag
uv run python scripts/bump_version.py --tag --push-tag
uv lock
uv build
uv run sphinx-build -b html docs/source docs/build/html
```

This fork publishes from the current repository. A recommended release flow is:
```shell
uv run python scripts/bump_version.py --tag --push-tag
```

## Documentation
Want to know more about this fork? Start with the repository docs and examples in this repo.


## License
PySide6-Fluent-Widgets-Qiao is distributed under [GPLv3](./LICENSE).

Copyright © 2021 by zhiyiYo. Fork maintenance and packaging changes by AQiaoYo.


## Work with Designer
[Fluent Client](https://www.youtube.com/watch?v=7UCmcsOlhTk) integrates designer plugins, supporting direct drag-and-drop usage of QFluentWidgets components in Designer. You can purchase the client from [TaoBao](https://item.taobao.com/item.htm?ft=t&id=767961666600) or [Afdian](https://afdian.com/item/6726fcc4247311ef8c6852540025c377).

![Fluent Designer](./docs/source/_static/Designer_plugin.jpg)


## See Also
Here are some projects based on PyQt-Fluent-Widgets:
* [**zhiyiYo/Fluent-M3U8**: A cross-platform m3u8 downloader](https://fluent-m3u8.org)
* [**zhiyiYo/Groove**: A cross-platform music player based on PyQt5](https://github.com/zhiyiYo/Groove)
* [**zhiyiYo/Alpha-Gobang-Zero**: A gobang robot based on reinforcement learning](https://github.com/zhiyiYo/Alpha-Gobang-Zero)

## Reference
* [**Windows design**: Design guidelines and toolkits for creating native app experiences](https://learn.microsoft.com/zh-cn/windows/apps/design/)
* [**Microsoft/WinUI-Gallery**: An app demonstrates the controls available in WinUI and the Fluent Design System](https://github.com/microsoft/WinUI-Gallery)
