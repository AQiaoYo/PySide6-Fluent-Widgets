# 执行计划：examples 目录结构重构

**日期**: 2026-04-19
**需求文档**: `docs/requirements/2026-04-19-examples-refactor.md`
**内部等级**: L（串行原生执行，分波次推进）

---

## 1. 等级决策

选择 **L 等级**（串行原生执行）。理由：
- 任务核心是文件系统操作（移动/重命名）和文档生成
- 操作间有顺序依赖（必须先创建目录再移动文件）
- 虽然涉及 60+ 文件，但每个操作简单且可预测
- XL 的多代理并行在此场景下增益有限，且增加协调风险

---

## 2. Wave 结构

### Wave 1: widgets/ 分类重组
**目标**: 将 basic_input、media、menu、scroll、status_info、text、view、window/fluent_widget 下的目录移到 widgets/ 下。

**操作清单**:
1. 创建 `examples/widgets/` 目录
2. 移动 `examples/basic_input/*` -> `examples/widgets/`
3. 移动 `examples/media/*` -> `examples/widgets/`
4. 移动 `examples/menu/*` -> `examples/widgets/`
5. 移动 `examples/scroll/*` -> `examples/widgets/`
6. 移动 `examples/status_info/*` -> `examples/widgets/`
7. 移动 `examples/text/*` -> `examples/widgets/`
8. 移动 `examples/view/*` -> `examples/widgets/`
9. 移动 `examples/window/fluent_widget/` -> `examples/widgets/`
10. 删除空目录 `examples/basic_input/`、`examples/media/`、`examples/menu/`、`examples/scroll/`、`examples/status_info/`、`examples/text/`、`examples/view/`

**验证**: 检查 `examples/widgets/` 下目录数量是否为 34+。

### Wave 2: dialog_box/ 重组
**目标**: 将 dialog_flyout/ 下的 dialog 相关示例保留，flyout/teaching_tip 移到 widgets/。

**操作清单**:
1. 创建 `examples/dialog_box/` 目录
2. 移动 `examples/dialog_flyout/color_dialog/` -> `examples/dialog_box/`
3. 移动 `examples/dialog_flyout/custom_message_box/` -> `examples/dialog_box/`
4. 移动 `examples/dialog_flyout/dialog/` -> `examples/dialog_box/`
5. 移动 `examples/dialog_flyout/folder_list_dialog/` -> `examples/dialog_box/`
6. 移动 `examples/dialog_flyout/message_dialog/` -> `examples/dialog_box/`
7. 移动 `examples/dialog_flyout/flyout/` -> `examples/widgets/flyout/`
8. 移动 `examples/dialog_flyout/teaching_tip/` -> `examples/widgets/teaching_tip/`
9. 删除空目录 `examples/dialog_flyout/`

**验证**: 检查 `examples/dialog_box/` 和 `examples/widgets/` 内容正确。

### Wave 3: navigation/ 重组
**目标**: 将 window/ 下的导航相关示例移到 navigation/，语义化命名 navigation1/2/3。

**操作清单**:
1. 移动 `examples/window/navigation1/` -> `examples/navigation/navigation_stack/`
2. 移动 `examples/window/navigation2/` -> `examples/navigation/navigation_pivot/`
3. 移动 `examples/window/navigation3/` -> `examples/navigation/navigation_segmented/`
4. 移动 `examples/window/fluent_window/` -> `examples/navigation/fluent_window/`
5. 移动 `examples/window/ms_fluent_window/` -> `examples/navigation/ms_fluent_window/`
6. 移动 `examples/window/split_fluent_window/` -> `examples/navigation/split_fluent_window/`
7. 移动 `examples/window/navigation_bar/` -> `examples/navigation/navigation_bar/`（如已存在则合并/覆盖确认）
8. 移动 `examples/window/navigation_header/` -> `examples/navigation/navigation_header/`
9. 移动 `examples/window/navigation_user_card/` -> `examples/navigation/navigation_user_card/`
10. 移动 `examples/window/pivot/` -> `examples/navigation/pivot/`
11. 移动 `examples/window/segmented_tool_widget/` -> `examples/navigation/segmented_tool_widget/`
12. 移动 `examples/window/segmented_widget/` -> `examples/navigation/segmented_widget/`
13. 移动 `examples/window/stacked_widget/` -> `examples/navigation/stacked_widget/`
14. 移动 `examples/window/tab_view/` -> `examples/navigation/tab_view/`
15. 移动 `examples/window/tab_widget/` -> `examples/navigation/tab_widget/`

**验证**: 检查 `examples/navigation/` 下目录数量是否为 15+。

### Wave 4: 完整应用归类（apps/）
**目标**: 将 gallery 和 window/ 下的完整应用移到 apps/ 下。

**操作清单**:
1. 创建 `examples/apps/` 目录
2. 移动 `examples/gallery/` -> `examples/apps/gallery/`
3. 移动 `examples/window/clock/` -> `examples/apps/clock/`
4. 移动 `examples/window/login/` -> `examples/apps/login/`
5. 移动 `examples/window/settings/` -> `examples/apps/settings_app/`
6. 移动 `examples/window/splash_screen/` -> `examples/apps/splash_screen/`
7. 移动 `examples/window/web_engine/` -> `examples/apps/web_engine/`
8. 删除空目录 `examples/window/`

**验证**: 检查 `examples/apps/` 下目录完整。

### Wave 5: 生成索引文档
**目标**: 为每个分类目录和顶层生成 README.md。

**操作清单**:
1. 生成 `examples/README.md`（顶层总览）
2. 生成 `examples/widgets/README.md`
3. 生成 `examples/date_time/README.md`
4. 生成 `examples/dialog_box/README.md`
5. 生成 `examples/layout/README.md`
6. 生成 `examples/material/README.md`
7. 生成 `examples/navigation/README.md`
8. 生成 `examples/settings/README.md`
9. 生成 `examples/apps/README.md`

**验证**: 手动检查 README 内容正确。

### Wave 6: 验证
**目标**: 确保所有 demo.py 在新路径下仍可运行。

**操作清单**:
1. 运行 `python examples/widgets/button/demo.py`（基础组件）
2. 运行 `python examples/navigation/navigation_stack/demo.py`（导航组件）
3. 运行 `python examples/dialog_box/dialog/demo.py`（对话框组件）
4. 运行 `python examples/apps/gallery/demo.py`（完整应用）
5. 检查是否有残留的 import 错误或路径问题

**验证**: 所有 demo.py 启动无异常。

### Wave 7: 清理
**目标**: 删除所有空目录，确保没有遗漏。

**操作清单**:
1. 递归检查 `examples/` 下是否有空目录
2. 删除空目录
3. 生成清理收据

---

## 3. 所有权边界

- 当前会话（主 lane）负责所有 waves 的执行
- 文件系统操作由本代理直接执行
- README 生成由本代理直接编写

---

## 4. 验证命令

```bash
# 验证目录结构
find examples/ -maxdepth 2 -type d | sort

# 验证 demo.py 存在且非空
find examples/ -name "demo.py" | wc -l

# 运行关键 demo 验证（需要 GUI 环境，可能只能做语法检查）
python -m py_compile examples/widgets/button/demo.py
python -m py_compile examples/navigation/navigation_stack/demo.py
python -m py_compile examples/dialog_box/dialog/demo.py
python -m py_compile examples/apps/gallery/demo.py
```

---

## 5. 交付验收计划

| 检查项 | 验收标准 |
|--------|----------|
| 目录结构 | 与需求文档"目标结构"一致 |
| demo.py 数量 | 不少于重构前数量（无丢失） |
| README 覆盖 | 每个分类目录 + 顶层均有 README.md |
| 语法验证 | 所有 demo.py 通过 `py_compile` |
| 空目录检查 | `examples/` 下无空目录 |

---

## 6. 完成语言规则

- **允许声称完成的条件**: 所有 waves 执行完毕，验证通过，无遗留问题
- **禁止的措辞**: "应该可以"、"大概没问题"、"目测正确"
- **必须使用的措辞**: "已验证"、"已确认"、"所有检查项通过"

---

## 7. 回滚规则

由于本次操作以文件系统移动为主：
1. **首选回滚方式**: `git checkout -- examples/` 恢复原始状态（执行前确保所有变更已提交或暂存）
2. **若已提交**: `git revert` 最后一次提交
3. **部分回滚**: 针对单个 wave 的问题，可手动逆向操作（从目标路径移回源路径）

**执行前检查**: 确认 `git status` 为 clean，避免与未提交的变更冲突。

---

## 8. 阶段清理预期

- **临时文件**: 无（本任务不产生临时文件）
- **废弃代码**: 无（本任务不修改代码内容）
- **残留目录**: Wave 7 结束后确保无空目录
- **文档更新**: 若有其他文档引用了 `examples/` 的旧路径，需要同步更新（如根目录 README、docs 等）
