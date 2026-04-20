# 入门教程

本教程面向已有 Python 和基础 Qt 经验的开发者，帮助你在 15 分钟内上手 PySide6-Fluent-Widgets。

---

## 第 1 步：安装

### 使用 uv（推荐）

```bash
uv add PySide6-Fluent-Widgets-Qiao
```

安装完整版（包含 AcrylicLabel 等材质效果组件）：

```bash
uv add "PySide6-Fluent-Widgets-Qiao[full]"
```

### 使用 pip

```bash
pip install PySide6-Fluent-Widgets-Qiao -i https://pypi.org/simple/
```

> **注意**：不要同时安装多个 Fluent Widgets 包（如 `PyQt-Fluent-Widgets`、`PySide6-Fluent-Widgets` 等），它们使用相同的导入名 `qfluentwidgets`，会互相冲突。

---

## 第 2 步：运行第一个示例

安装完成后，先运行组件画廊，看看这个库能提供什么效果：

```bash
# 克隆仓库

git clone https://github.com/AQiaoYo/PySide6-Fluent-Widgets.git
cd PySide6-Fluent-Widgets

# 安装依赖
uv sync

# 运行画廊
uv run python examples/apps/gallery/demo.py
```

画廊应用展示了所有组件的实际效果，浏览一遍你就能对"这个库有什么"有个直观印象。

> **本节目标**：确认安装成功，对组件库的整体面貌有初步了解。

---

## 第 3 步：写一个简单界面

现在从零开始写一个只包含两个按钮和一个标签的窗口。

创建 `my_first_app.py`：

```python
# coding: utf-8
"""我的第一个 Fluent 界面"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import PushButton, SwitchButton, BodyLabel, setTheme, Theme


class MyWindow(QWidget):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('My First Fluent App')
        self.resize(400, 200)

        # 创建控件
        self.label = BodyLabel('欢迎使用 PySide6-Fluent-Widgets', self)
        self.button = PushButton('点击我', self)
        self.switch = SwitchButton(self)

        # 连接信号
        self.button.clicked.connect(self.on_button_clicked)
        self.switch.checkedChanged.connect(self.on_switch_toggled)

        # 布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.switch)
        layout.addStretch(1)

    def on_button_clicked(self):
        self.label.setText('按钮被点击了！')

    def on_switch_toggled(self, is_checked: bool):
        state = '开启' if is_checked else '关闭'
        self.label.setText(f'开关状态: {state}')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 设置深色主题
    setTheme(Theme.DARK)

    window = MyWindow()
    window.show()
    app.exec()
```

运行：

```bash
python my_first_app.py
```

你应该会看到一个带有 Fluent Design 样式的窗口：按钮有圆角和悬停效果，开关有平滑动画，整体自动适配深色主题。

> **关键概念**：
> - `qfluentwidgets` 的组件继承自标准 Qt 组件（如 `PushButton` 继承 `QPushButton`），所以所有 Qt 的 API 都能正常使用
> - `setTheme(Theme.DARK)` 一行代码切换全局主题，组件会自动响应
> - 不需要写 QSS，组件自带 Fluent 样式

> **本节目标**：理解"导入即用"的开发模式，知道组件和标准 Qt 组件的关系。

---

## 第 4 步：切换主题

PySide6-Fluent-Widgets 支持三种主题模式：

```python
from qfluentwidgets import setTheme, Theme

setTheme(Theme.LIGHT)   # 浅色主题
setTheme(Theme.DARK)    # 深色主题
setTheme(Theme.AUTO)    # 跟随系统主题
```

主题切换是全局的，只需要在应用启动时设置一次。

如果你想让自定义控件也跟随主题变化，可以继承 `StyleSheetBase`：

```python
from enum import Enum
from qfluentwidgets import StyleSheetBase, Theme, qconfig


class MyStyleSheet(StyleSheetBase, Enum):
    """自定义样式表"""
    MAIN_WINDOW = "main_window"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"app/resource/qss/{theme.value.lower()}/{self.value}.qss"


# 使用
MyStyleSheet.MAIN_WINDOW.apply(my_window)
```

> **本节目标**：掌握主题切换，知道如何让自己的样式也跟随主题变化。

---

## 第 5 步：构建带导航的多页面应用

大多数应用不止一个页面。这里展示如何用 `FluentWindow` 构建一个带侧边栏导航的多页面应用：

```python
# coding: utf-8
"""带导航的多页面应用示例"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition,
    PushButton, BodyLabel, setTheme, Theme
)


class HomePage(QWidget):
    """首页"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = BodyLabel('这是首页', self)
        label.setStyleSheet('font-size: 24px;')
        layout.addWidget(label)


class SettingsPage(QWidget):
    """设置页"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = BodyLabel('这是设置页', self)
        label.setStyleSheet('font-size: 24px;')
        layout.addWidget(label)


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('多页面应用')
        self.resize(900, 700)

        # 创建子页面
        self.home_page = HomePage(self)
        self.settings_page = SettingsPage(self)

        # 添加导航项
        self.addSubInterface(self.home_page, FluentIcon.HOME, '首页')
        self.addSubInterface(
            self.settings_page, FluentIcon.SETTING, '设置',
            position=NavigationItemPosition.BOTTOM
        )

        # 设置默认页面
        self.navigationInterface.setDefaultRouteKey(self.home_page.objectName())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)

    # 需要导入图标
    from qfluentwidgets import FluentIcon

    window = MainWindow()
    window.show()
    app.exec()
```

> **关键概念**：
> - `FluentWindow` 已经内置了导航栏 + 内容区的布局
> - `addSubInterface()` 将页面添加到导航栏，点击自动切换
> - `NavigationItemPosition.BOTTOM` 将项放在导航栏底部

> **本节目标**：理解导航模式，知道如何组织多页面应用的结构。

---

## 第 6 步：找到你需要的组件

本库组件很多，如何快速找到想要的？

### 方法 1：组件索引

查看 [COMPONENTS.md](COMPONENTS.md)，按分类浏览所有组件，每个组件都有对应的示例代码链接。

### 方法 2：画廊应用

运行 `examples/apps/gallery/demo.py`，左侧导航按分类展示所有组件，右侧是实时预览和代码片段。

### 方法 3：示例目录

```
examples/
  widgets/        # 基础组件：按钮、输入框、标签等
  navigation/     # 导航：侧边栏、Pivot、Tab 等
  dialog_box/     # 对话框
  layout/         # 布局容器
  date_time/      # 日期时间选择器
  material/       # 亚克力材质效果
  apps/           # 完整应用参考
```

每个子目录下都有一个 `demo.py`，直接运行即可看到效果。

### 方法 4：源码 docstring

所有组件的源码都带有中文 docstring，描述了使用场景和参数。例如：

```python
class PushButton(QPushButton):
    """标准推送按钮，用于触发常见的界面操作

    适用于提交表单、确认对话框、执行命令等常规交互场景

    构造函数重载:
        * PushButton(parent: QWidget = None)
        * PushButton(text: str, parent: QWidget = None, icon: ...)
    """
```

> **本节目标**：掌握"从需求到组件"的查找路径，不再"不知道这个库有什么"。

---

## 下一步

现在你已经掌握了基本用法，建议按以下路径深入：

1. **看示例**：运行 `examples/` 下你感兴趣的 demo，复制代码到自己项目中修改
2. **查组件索引**：[COMPONENTS.md](COMPONENTS.md) 按功能分类，快速定位
3. **读源码 docstring**：需要了解某个组件的详细参数时，直接看源码
4. **参考画廊应用**：`examples/apps/gallery/` 是一个完整的、可直接学习的应用架构

---

## 常见问题

### Q: 运行示例时报 `ImportError: cannot import name 'XXX'`？

A: 说明你安装的包版本过低。使用官方源重新安装：

```bash
pip install --upgrade PySide6-Fluent-Widgets-Qiao -i https://pypi.org/simple/
```

### Q: 组件样式没有生效？

A: 确保你使用的是 `qfluentwidgets` 的组件而不是标准 Qt 组件。例如用 `qfluentwidgets.PushButton` 而不是 `QPushButton`。

### Q: 如何自定义主题色？

A: 使用 `setThemeColor()`：

```python
from qfluentwidgets import setThemeColor
setThemeColor('#0065d5')  # 支持 QColor、Qt.GlobalColor、str
```

### Q: 想在 Designer 里拖拽使用？

A: 查看 README 中的 "Work with Designer" 部分，了解 Fluent Client 插件。
