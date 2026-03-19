<p align="center">
  <img width="18%" align="center" src="https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/master/docs/source/_static/logo.png" alt="logo">
</p>
  <h1 align="center">
  PySide6-Fluent-Widgets-Qiao
</h1>
<p align="center">
  基于 PySide6 的 Fluent Design 风格组件库
</p>


<div align="center">

[![Version](https://img.shields.io/pypi/v/pyside6-fluent-widgets-qiao?color=%2334D058&label=Version)](https://pypi.org/project/PySide6-Fluent-Widgets-Qiao/)
[![Download](https://static.pepy.tech/personalized-badge/pyside6-fluent-widgets-qiao?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)]()
[![GPLv3](https://img.shields.io/badge/License-GPLv3-blue?color=#4ec820)](LICENSE)
[![Platform Win32 | Linux | macOS](https://img.shields.io/badge/Platform-Win32%20|%20Linux%20|%20macOS-blue?color=#4ec820)]()

</div>

<p align="center">
<a href="../README.md">English</a> | 简体中文 | <a href="https://github.com/AQiaoYo/PySide6-Fluent-Widgets">GitHub</a>
</p>

![Interface](https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/master/docs/source/_static/Interface.jpg)


## 安装📥
使用 `uv` 安装轻量版 (亚克力组件不可用)：
```shell
uv add PySide6-Fluent-Widgets-Qiao
```
安装完整版：
```shell
uv add "PySide6-Fluent-Widgets-Qiao[full]"
```

如果你更习惯 `pip`，等价命令是：
```shell
pip install PySide6-Fluent-Widgets-Qiao -i https://pypi.org/simple/
pip install "PySide6-Fluent-Widgets-Qiao[full]" -i https://pypi.org/simple/
```


这个 fork 保留 `qfluentwidgets` 作为导入包名，但在 PyPI 上发布为 `PySide6-Fluent-Widgets-Qiao`。

> [!Warning]
> 请勿同时安装 `PyQt-Fluent-Widgets`、`PyQt6-Fluent-Widgets`、`PySide2-Fluent-Widgets`、`PySide6-Fluent-Widgets` 和 `PySide6-Fluent-Widgets-Qiao`，因为它们暴露的导入包名都是 `qfluentwidgets`


## 运行示例▶️
克隆此仓库后，推荐使用 `uv` 创建环境并运行示例：
```shell
uv sync
uv run python examples/gallery/demo.py
```

如果你需要可选依赖或文档构建环境：
```shell
uv sync --extra full --group docs
```

如果你已经从 PyPI 安装了包，也可以像下面这样直接运行仓库里的示例：
```shell
cd examples/gallery
python demo.py
```

如果遇到 `ImportError: cannot import name 'XXX' from 'qfluentwidgets'`，这表明安装的包版本过低。可以按照上面的安装指令将 pypi 源替换为 https://pypi.org/simple 并重新安装.

## 开发命令🛠
常用的 `uv` 项目命令：
```shell
uv lock
uv build
uv run sphinx-build -b html docs/source docs/build/html
```

推荐发布流程：
```shell
git tag v1.11.1
git push origin v1.11.1
```

## 在线文档📕
想要了解这个 fork 的使用方式，请直接阅读本仓库中的文档和示例。

## 许可证📄
PySide6-Fluent-Widgets-Qiao 使用 [GPLv3](../LICENSE) 许可证进行授权。

Copyright © 2021 by zhiyiYo，fork 维护与打包变更由 AQiaoYo 完成。



## Fluent Client🚩
[Fluent Client](https://qfluentwidgets.com/zh/pages/designer) 集成了设计师插件和脚手架功能，支持在 Designer 中直接拖拽使用 QFluentWidgets 的组件，所见即所得，让现代化界面搭建如丝般顺滑！可在 [淘宝](https://item.taobao.com/item.htm?ft=t&id=767961666600) 购买使用 Fluent Client。

![Fluent Designer](./source/_static/Designer_plugin.jpg)


## 另见👀
下面是一些基于 PyQt-Fluent-Widgets 的项目：
* [**zhiyiYo/Fluent-M3U8**: 美观易用的跨平台 m3u8 下载器](https://fluent-m3u8.org)
* [**zhiyiYo/Groove**: 基于 PyQt5 的跨平台音乐播放器](https://github.com/zhiyiYo/Groove)
* [**zhiyiYo/Alpha-Gobang-Zero**: 基于强化学习的五子棋机器人](https://github.com/zhiyiYo/Alpha-Gobang-Zero)

## 参考
* [**Windows design**: Design guidelines and toolkits for creating native app experiences](https://learn.microsoft.com/zh-cn/windows/apps/design/)
* [**Microsoft/WinUI-Gallery**: An app demonstrates the controls available in WinUI and the Fluent Design System](https://github.com/microsoft/WinUI-Gallery)
