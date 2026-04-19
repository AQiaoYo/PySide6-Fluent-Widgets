# 执行计划：Examples 质量精修

**日期**: 2026-04-19
**需求文档**: `docs/requirements/2026-04-19-examples-quality.md`
**内部等级**: L（串行分批次执行，每批次内可并行验证）

---

## 1. 等级决策

选择 **L 等级**（串行分批次执行）。理由：
- 75 个文件看似多，但每个 demo 独立，修改逻辑简单
- 统一代码风格是关键，串行执行更利于风格一致性控制
- XL 多代理在此场景下协调成本高（需要同步风格模板），增益有限
- 分三批实施降低风险，每批完成后验收再继续

---

## 2. Wave 结构

### Wave 1: 低质量 demo 重写（14 个）
**目标**: 将 14 个低质量 demo 从零重写到 ~80-120 行，满足精修标准。

**文件清单**:
1. `examples/widgets/check_box/demo.py`
2. `examples/widgets/switch_button/demo.py`
3. `examples/widgets/radio_button/demo.py`
4. `examples/widgets/avatar_widget/demo.py`
5. `examples/widgets/image_label/demo.py`
6. `examples/widgets/scroll_area/demo.py`
7. `examples/widgets/state_tool_tip/demo.py`
8. `examples/widgets/tree_view/demo.py`
9. `examples/dialog_box/color_dialog/demo.py`
10. `examples/dialog_box/folder_list_dialog/demo.py`
11. `examples/material/acrylic_brush/demo.py`
12. `examples/material/acrylic_label/demo.py`
13. `examples/apps/splash_screen/demo.py`

> 注：实际 13 个（原清单 14 个含 gallery/demo.py，但 gallery 为入口文件不纳入）

**重写要点**:
- 每个 demo 展示至少 2 个组件变体
- 添加至少 1 个信号槽连接
- 使用合理的布局（QVBoxLayout/QHBoxLayout）
- 中文注释说明关键逻辑
- 符合统一代码模板（3.1 节）

**验证**: 每个重写后立即 `py_compile`，完成后整批运行抽查。

### Wave 2: 中等质量 demo 优化（25 个）
**目标**: 在现有框架上补充多变体、交互逻辑和注释。

**文件清单**:
1. `examples/date_time/calendar_picker/demo.py`
2. `examples/dialog_box/dialog/demo.py`
3. `examples/dialog_box/message_dialog/demo.py`
4. `examples/layout/flow_layout/demo.py`
5. `examples/material/acrylic_combo_box/demo.py`
6. `examples/material/acrylic_menu/demo.py`
7. `examples/navigation/fluent_window/demo.py`
8. `examples/navigation/ms_fluent_window/demo.py`
9. `examples/navigation/navigation_header/demo.py`
10. `examples/navigation/navigation_user_card/demo.py`
11. `examples/navigation/split_fluent_window/demo.py`
12. `examples/navigation/tab_widget/demo.py`
13. `examples/widgets/fluent_widget/demo.py`
14. `examples/widgets/info_badge/demo.py`
15. `examples/widgets/label/demo.py`
16. `examples/widgets/media_player/demo.py`
17. `examples/widgets/pips_pager/demo.py`
18. `examples/widgets/slider/demo.py`
19. `examples/widgets/spin_box/demo.py`
20. `examples/widgets/system_tray_menu/demo.py`
21. `examples/widgets/text_browser/demo.py`
22. `examples/widgets/tree_widget/demo.py`
23. `examples/apps/clock/demo.py`
24. `examples/apps/login/demo.py`
25. `examples/apps/web_engine/demo.py`

**优化要点**:
- 补充中文注释（当前可能只有英文或缺少注释）
- 增加变体展示（如从 1 个变体增加到 2-3 个）
- 添加交互逻辑（信号槽连接）
- 统一代码结构为模板格式

**验证**: 整批 `py_compile`，抽查运行。

### Wave 3: 高质量 demo 风格统一（36 个）
**目标**: 统一代码结构、补充注释、检查是否遗漏关键用法。

**文件清单**:
1. `examples/date_time/fast_calendar_picker/demo.py`
2. `examples/date_time/time_picker/demo.py`
3. `examples/dialog_box/custom_message_box/demo.py`
4. `examples/material/acrylic_flyout/demo.py`
5. `examples/material/acrylic_line_edit/demo.py`
6. `examples/material/acrylic_tool_tip/demo.py`
7. `examples/material/acrylic_widget_menu/demo.py`
8. `examples/navigation/breadcrumb_bar/demo.py`
9. `examples/navigation/navigation_bar/demo.py`
10. `examples/navigation/navigation_pivot/demo.py`
11. `examples/navigation/navigation_segmented/demo.py`
12. `examples/navigation/navigation_stack/demo.py`
13. `examples/navigation/pivot/demo.py`
14. `examples/navigation/segmented_tool_widget/demo.py`
15. `examples/navigation/segmented_widget/demo.py`
16. `examples/navigation/stacked_widget/demo.py`
17. `examples/navigation/tab_view/demo.py`
18. `examples/widgets/button/demo.py`
19. `examples/widgets/card_widget/demo.py`
20. `examples/widgets/combo_box/demo.py`
21. `examples/widgets/command_bar/demo.py`
22. `examples/widgets/flip_view/demo.py`
23. `examples/widgets/flyout/demo.py`
24. `examples/widgets/font_icon/demo.py`
25. `examples/widgets/info_bar/demo.py`
26. `examples/widgets/line_edit/demo.py`
27. `examples/widgets/list_view/demo.py`
28. `examples/widgets/menu/demo.py`
29. `examples/widgets/model_combo_box/demo.py`
30. `examples/widgets/progress_bar/demo.py`
31. `examples/widgets/progress_ring/demo.py`
32. `examples/widgets/table_view/demo.py`
33. `examples/widgets/teaching_tip/demo.py`
34. `examples/widgets/tool_tip/demo.py`
35. `examples/widgets/widget_menu/demo.py`
36. `examples/apps/settings_app/demo.py`

**优化要点**:
- 统一代码结构（是否符合 3.1 模板）
- 补充/修正中文注释
- 检查是否有遗漏的关键用法或变体
- 字符串引号统一为单引号

**验证**: 整批 `py_compile`。

### Wave 4: 全局验证
**目标**: 全量验证所有 75 个 demo。

**操作**:
1. `find examples/ -name demo.py -exec python -m py_compile {} \;`
2. 运行 5-10 个关键 demo 做 GUI 验证
3. 检查是否有遗漏的旧路径引用
4. 生成质量报告

### Wave 5: 清理
**目标**: 清理临时文件和残留。

**操作**:
1. 删除所有 `__pycache__` 和 `.pyc`
2. 确认无空目录
3. 生成清理收据

---

## 3. 统一代码模板

所有 demo 必须遵循以下结构：

```python
# coding:utf-8
"""
<组件名>演示

展示内容：
- 用法1：<简要描述>
- 用法2：<简要描述>
- 用法3：<简要描述>
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, ...
from qfluentwidgets import ...


class Demo(QWidget):
    """主演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('<组件名> - 演示')
        self.resize(600, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        ...

    def initLayout(self):
        """初始化布局"""
        ...

    def on<Signal>Triggered(self):
        """信号响应"""
        ...


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
```

---

## 4. 验证命令

```bash
# 全量语法检查
find examples/ -name "demo.py" -exec python -m py_compile {} \;

# 统计检查
find examples/ -name "demo.py" | wc -l

# 检查旧路径引用
grep -r "examples/(basic_input|media|menu|scroll|status_info|text|view|window/|dialog_flyout)" --include="*.py" .
```

---

## 5. 交付验收计划

| 检查项 | 验收标准 |
|--------|----------|
| 语法检查 | 全部 75 个 demo.py 通过 py_compile |
| 变体覆盖 | 每个 demo 至少 2 个变体（单一形态组件除外） |
| 交互逻辑 | 每个 demo 至少 1 个信号槽连接（无交互组件除外） |
| 注释覆盖 | 每个 demo 有中文注释 |
| 结构统一 | 代码结构符合统一模板 |
| 旧路径 | 无残留的旧路径引用 |

---

## 6. 完成语言规则

- **允许声称完成的条件**: 所有 waves 执行完毕，全量验证通过
- **必须使用的措辞**: "已验证"、"已确认"、"所有检查项通过"

---

## 7. 回滚规则

- 执行前确保 `git status` clean
- 回滚方式: `git checkout -- examples/`
- 部分回滚: `git checkout -- <具体文件>`

---

## 8. 工作量预估

| 批次 | 文件数 | 预估每文件工作量 | 总计 |
|------|--------|------------------|------|
| Wave 1（低质量） | 13 | 重写 ~15 分钟 | ~195 分钟 |
| Wave 2（中等） | 25 | 优化 ~8 分钟 | ~200 分钟 |
| Wave 3（高质量） | 36 | 微调 ~5 分钟 | ~180 分钟 |
| Wave 4-5（验证清理） | - | - | ~30 分钟 |

**总计**: 约 10 小时的工作量。
