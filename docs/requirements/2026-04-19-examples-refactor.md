# 需求文档：examples 目录结构重构

**日期**: 2026-04-19
**状态**: 已冻结
**阶段**: 第一阶段（结构聚焦）

---

## 1. 目标

重构 `examples/` 目录结构，解决当前"分类混乱、层次不一致、缺少索引"的问题，使其对框架使用者清晰、可导航、可维护。

## 2. 当前问题诊断

### 2.1 分类与库结构不对齐

`qfluentwidgets.components` 子包结构为：
```
components/
  date_time/
  dialog_box/
  layout/
  material/
  navigation/
  settings/
  widgets/
    button/
    check_box/
    combo_box/
    label/
    line_edit/
    menu/
    ...
```

而 `examples/` 的分类为：
```
examples/
  basic_input/      ← 混合了 widgets/button, widgets/check_box, widgets/combo_box 等
  date_time/        ✅ 对齐
  dialog_flyout/    ← 混合了 dialog_box/ 和 widgets/ 下的 flyout/teaching_tip
  gallery/          ← 完整应用，层次不一致
  layout/           ✅ 对齐
  material/         ✅ 对齐
  media/            ← 对应 widgets/avatar_widget, widgets/media_player
  menu/             ← 对应 widgets/menu, widgets/command_bar 等
  navigation/       ✅ 对齐
  scroll/           ← 对应 widgets/pips_pager, widgets/scroll_area
  status_info/      ← 混合了 widgets/info_badge, info_bar, progress_bar, progress_ring, state_tool_tip, tool_tip
  text/             ← 混合了 widgets/label, line_edit, spin_box, text_browser, font_icon, image_label
  view/             ← 混合了 widgets/card_widget, flip_view, list_view, table_view, tree_view, tree_widget
  window/           ← 混合了组件示例（fluent_window）和完整应用（clock, login, settings）
```

### 2.2 层次不一致
- 大部分目录：`examples/分类/组件名/demo.py`（单层组件演示）
- `gallery/`：完整应用，含 `app/` 子目录（view, components, common）
- `window/clock/`、`window/login/`、`window/settings/`：完整应用，含 view/, resource/, config.py 等

### 2.3 命名不统一
- `navigation/navigation1/`、`navigation/navigation2/`、`navigation/navigation3/`：编号式命名，语义不清
- 有的目录用单数（`button/`），有的用复合词（`switch_button/`）

### 2.4 缺少索引
- 没有顶层 README 告诉用户 examples 里有什么
- 没有分类 README 说明每个分类包含什么、对应哪些组件

## 3. 需求边界

### 3.1 本次范围（第一阶段：结构聚焦）
- ✅ 目录结构调整与重命名
- ✅ 分类与 `components` 子包对齐
- ✅ 完整应用示例归类
- ✅ 索引文档（README）
- ❌ `demo.py` 内容质量改进（后续阶段）
- ❌ 与 `preview` 功能重叠的简单 demo 精简（后续阶段）
- ❌ 新增缺失的组件示例（后续阶段）

### 3.2 约束
- **不破坏现有功能**：所有 `demo.py` 的运行结果保持不变（只移动/重命名目录）
- **保持向后兼容**：如果有外部引用路径，应在 README 中说明旧路径映射
- **完整应用留在 examples 里**：`gallery/`、`window/clock/`、`window/login/`、`window/settings/` 不移出 examples

## 4. 目标结构

```
examples/
  README.md                           ← 顶层总览索引
  # 组件示例（与 components 子包对齐）
  widgets/
    README.md                         ← 分类说明
    button/
      demo.py
    check_box/
      demo.py
    combo_box/
      demo.py
    ...
  date_time/
    README.md
    calendar_picker/
      demo.py
    ...
  dialog_box/
    README.md
    color_dialog/
      demo.py
    ...
  layout/
    README.md
    flow_layout/
      demo.py
  material/
    README.md
    acrylic_brush/
      demo.py
    ...
  navigation/
    README.md
    breadcrumb_bar/
      demo.py
    fluent_window/
      demo.py
    ms_fluent_window/
      demo.py
    split_fluent_window/
      demo.py
    ...
  settings/                           ← 新增（components/settings/ 对应的示例）
    README.md
  # 完整应用示例
  apps/
    README.md
    gallery/
      demo.py
      app/
        ...
    clock/
      demo.py
      view/
        ...
      resource/
        ...
    login/
      demo.py
      Ui_LoginWindow.py
    settings_app/                     ← 原 window/settings/，改名避免与 settings/ 组件分类冲突
      demo.py
      config.py
      setting_interface.py
    splash_screen/
      demo.py
    web_engine/
      demo.py
```

### 4.1 关键变更说明

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `basic_input/button/` | `widgets/button/` | 归入 widgets 分类 |
| `basic_input/check_box/` | `widgets/check_box/` | 归入 widgets 分类 |
| `basic_input/combo_box/` | `widgets/combo_box/` | 归入 widgets 分类 |
| `basic_input/model_combo_box/` | `widgets/model_combo_box/` | 归入 widgets 分类 |
| `basic_input/radio_button/` | `widgets/radio_button/` | 归入 widgets 分类 |
| `basic_input/slider/` | `widgets/slider/` | 归入 widgets 分类 |
| `basic_input/switch_button/` | `widgets/switch_button/` | 归入 widgets 分类 |
| `dialog_flyout/` | `dialog_box/` | 与 components/dialog_box 对齐，widgets 下的 flyout/teaching_tip 移到 widgets/ |
| `media/avatar_widget/` | `widgets/avatar_widget/` | 归入 widgets 分类 |
| `media/media_player/` | `widgets/media_player/` | 归入 widgets 分类 |
| `menu/command_bar/` | `widgets/command_bar/` | 归入 widgets 分类 |
| `menu/menu/` | `widgets/menu/` | 归入 widgets 分类 |
| `menu/system_tray_menu/` | `widgets/system_tray_menu/` | 归入 widgets 分类 |
| `menu/widget_menu/` | `widgets/widget_menu/` | 归入 widgets 分类 |
| `scroll/pips_pager/` | `widgets/pips_pager/` | 归入 widgets 分类 |
| `scroll/scroll_area/` | `widgets/scroll_area/` | 归入 widgets 分类 |
| `status_info/info_badge/` | `widgets/info_badge/` | 归入 widgets 分类 |
| `status_info/info_bar/` | `widgets/info_bar/` | 归入 widgets 分类 |
| `status_info/progress_bar/` | `widgets/progress_bar/` | 归入 widgets 分类 |
| `status_info/progress_ring/` | `widgets/progress_ring/` | 归入 widgets 分类 |
| `status_info/state_tool_tip/` | `widgets/state_tool_tip/` | 归入 widgets 分类 |
| `status_info/tool_tip/` | `widgets/tool_tip/` | 归入 widgets 分类 |
| `text/font_icon/` | `widgets/font_icon/` | 归入 widgets 分类 |
| `text/image_label/` | `widgets/image_label/` | 归入 widgets 分类 |
| `text/label/` | `widgets/label/` | 归入 widgets 分类 |
| `text/line_edit/` | `widgets/line_edit/` | 归入 widgets 分类 |
| `text/spin_box/` | `widgets/spin_box/` | 归入 widgets 分类 |
| `text/text_browser/` | `widgets/text_browser/` | 归入 widgets 分类 |
| `view/card_widget/` | `widgets/card_widget/` | 归入 widgets 分类 |
| `view/flip_view/` | `widgets/flip_view/` | 归入 widgets 分类 |
| `view/list_view/` | `widgets/list_view/` | 归入 widgets 分类 |
| `view/table_view/` | `widgets/table_view/` | 归入 widgets 分类 |
| `view/tree_view/` | `widgets/tree_view/` | 归入 widgets 分类 |
| `view/tree_widget/` | `widgets/tree_widget/` | 归入 widgets 分类 |
| `window/fluent_widget/` | `widgets/fluent_widget/` | 归入 widgets 分类（窗口组件演示） |
| `window/fluent_window/` | `navigation/fluent_window/` | 导航相关窗口组件 |
| `window/ms_fluent_window/` | `navigation/ms_fluent_window/` | 导航相关窗口组件 |
| `window/split_fluent_window/` | `navigation/split_fluent_window/` | 导航相关窗口组件 |
| `window/navigation1/` | `navigation/navigation_stack/` | 语义化命名 |
| `window/navigation2/` | `navigation/navigation_pivot/` | 语义化命名 |
| `window/navigation3/` | `navigation/navigation_segmented/` | 语义化命名 |
| `window/navigation_bar/` | `navigation/navigation_bar/` | 保留 |
| `window/navigation_header/` | `navigation/navigation_header/` | 保留 |
| `window/navigation_user_card/` | `navigation/navigation_user_card/` | 保留 |
| `window/pivot/` | `navigation/pivot/` | 保留 |
| `window/segmented_tool_widget/` | `navigation/segmented_tool_widget/` | 保留 |
| `window/segmented_widget/` | `navigation/segmented_widget/` | 保留 |
| `window/stacked_widget/` | `navigation/stacked_widget/` | 保留 |
| `window/tab_view/` | `navigation/tab_view/` | 保留 |
| `window/tab_widget/` | `navigation/tab_widget/` | 保留 |
| `gallery/` | `apps/gallery/` | 完整应用归类 |
| `window/clock/` | `apps/clock/` | 完整应用归类 |
| `window/login/` | `apps/login/` | 完整应用归类 |
| `window/settings/` | `apps/settings_app/` | 完整应用归类，改名避免冲突 |
| `window/splash_screen/` | `apps/splash_screen/` | 完整应用归类 |
| `window/web_engine/` | `apps/web_engine/` | 完整应用归类 |

## 5. 验收标准

1. 目录结构符合"目标结构"的定义
2. 所有 `demo.py` 在新路径下仍可正常运行
3. 每个分类目录包含 `README.md`，说明该分类包含的组件
4. 顶层 `examples/README.md` 包含完整的目录索引和说明
5. 没有孤立的空目录或冗余文件
