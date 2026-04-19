# 需求文档：Examples 质量精修

**日期**: 2026-04-19
**状态**: 已冻结
**前置**: `docs/requirements/2026-04-19-examples-refactor.md`（目录结构重构已完成）

---

## 1. 目标

将 75 个 demo.py 全部提升到统一的高质量教学标准，使 examples 成为框架使用者学习组件用法的权威参考。

## 2. 现状量化

通过自动化质量扫描（行数、注释、布局、多变体、自定义样式、交互六个维度），当前分布为：

| 等级 | 数量 | 占比 | 典型特征 |
|------|------|------|----------|
| 高质量 | 36 | 48% | 代码完整，展示多变体/交互/布局 |
| 中等 | 25 | 33% | 基本用法正确，但缺少深度或注释 |
| 低质量 | 14 | 19% | 代码极简，与 preview 高度重叠 |

### 2.1 低质量 demo 清单（14 个）

- `examples/apps/splash_screen/demo.py` (49行)
- `examples/dialog_box/color_dialog/demo.py` (25行)
- `examples/dialog_box/folder_list_dialog/demo.py` (35行)
- `examples/material/acrylic_brush/demo.py` (35行)
- `examples/material/acrylic_label/demo.py` (15行)
- `examples/widgets/avatar_widget/demo.py` (34行)
- `examples/widgets/check_box/demo.py` (26行)
- `examples/widgets/image_label/demo.py` (36行)
- `examples/widgets/radio_button/demo.py` (29行)
- `examples/widgets/scroll_area/demo.py` (35行)
- `examples/widgets/state_tool_tip/demo.py` (39行)
- `examples/widgets/switch_button/demo.py` (27行)
- `examples/widgets/tree_view/demo.py` (35行)

> `apps/gallery/demo.py` 为入口文件，不纳入 demo 质量评估。

### 2.2 中等质量 demo 典型问题

- 缺少中文/英文注释说明为什么这么写
- 只展示了一个变体，没有覆盖组件的主要使用场景
- 没有展示信号槽连接（交互逻辑）
- 布局过于简单（单一 widget 居中）

## 3. 精修标准

每个 demo.py 必须满足以下最低标准：

### 3.1 结构规范

```python
# coding:utf-8
"""
组件名演示

展示内容：
- 用法1：xxx
- 用法2：xxx
- 用法3：xxx
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, ...
from qfluentwidgets import ...


class Demo(QWidget):
    """主演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('组件名 - 演示')
        self.resize(600, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        pass

    def initLayout(self):
        """初始化布局"""
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
```

### 3.2 内容要求

| 要求 | 说明 | 优先级 |
|------|------|--------|
| 多变体展示 | 展示组件的主要变体（如 PushButton/PrimaryPushButton/TransparentPushButton） | P0 |
| 交互逻辑 | 至少一个信号槽连接，展示组件的交互能力 | P0 |
| 布局技巧 | 使用合理的布局管理器（QVBoxLayout/QHBoxLayout/QGridLayout），避免 absolute positioning | P1 |
| 注释 | 关键代码行有中文注释，说明"为什么"和"效果是什么" | P1 |
| 样式定制 | 如有相关 API（setCustomStyleSheet、setTheme 等），至少展示一个 | P2 |
| 实际数据 | 使用有意义的示例数据（不要全是 "Item 1" "Item 2"） | P2 |

### 3.3 代码风格

- 类名使用 `Demo` 或 `Demo1`/`Demo2`（多个窗口时）
- 方法命名：`initWidgets()`、`initLayout()`、`onXxxClicked()`
- 字符串引号：单引号
- 注释语言：中文

## 4. 实施策略

### 4.1 分三批实施（降低风险）

**第一批：低质量 demo（14 个）**
- 工作量最大，需要重写
- 预期产出：每个 demo 从 ~30 行提升到 ~80-120 行
- 完成后立即验证运行

**第二批：中等质量 demo（25 个）**
- 已有基本框架，需要补充多变体/交互/注释
- 预期产出：补充注释、增加变体展示、添加交互逻辑

**第三批：高质量 demo（36 个）**
- 已有较好基础，只需统一代码风格和补充注释
- 预期产出：统一结构、补注释、检查是否遗漏关键用法

### 4.2 每次修改后验证

```bash
python -m py_compile <path>/demo.py
python <path>/demo.py  # 需要 GUI 环境
```

## 5. 验收标准

1. 所有 75 个 demo.py 通过 py_compile 语法检查
2. 每个 demo 展示至少 2 个组件变体（除非组件只有单一形态）
3. 每个 demo 至少包含 1 个信号槽连接（除非组件无交互能力）
4. 每个 demo 有中文注释说明关键逻辑
5. 代码结构符合 3.1 的规范模板

## 6. 非目标

- 不修改 demo.py 以外的文件（如 gallery interface、resource 等）
- 不新增组件示例（只精修现有 demo）
- 不修改组件库本身

## 7. 风险

| 风险 | 缓解措施 |
|------|----------|
| 工作量过大（75个文件） | 分三批实施，每批完成后验收 |
| 重写引入 bug | 每个 demo 修改后立即运行验证 |
| 风格不一致 | 预先定义统一的代码模板（3.1） |
| GUI 验证困难 | 先 py_compile 语法检查，再选择性运行 |
