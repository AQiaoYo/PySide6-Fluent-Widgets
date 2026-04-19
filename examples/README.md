# Examples

PySide6-Fluent-Widgets 示例集合，按组件分类组织，与 `qfluentwidgets.components` 子包结构对齐。

## 目录结构

```
examples/
  widgets/          # 基础组件（对应 components/widgets/）
  date_time/        # 日期时间组件（对应 components/date_time/）
  dialog_box/       # 对话框组件（对应 components/dialog_box/）
  layout/           # 布局组件（对应 components/layout/）
  material/         # 材质组件（对应 components/material/）
  navigation/       # 导航组件（对应 components/navigation/）
  settings/         # 设置卡片组件（对应 components/settings/）
  apps/             # 完整应用示例
```

## 快速开始

### 运行单个组件示例

```bash
# 按钮示例
python examples/widgets/button/demo.py

# 导航窗口示例
python examples/navigation/fluent_window/demo.py

# 对话框示例
python examples/dialog_box/dialog/demo.py
```

### 运行完整应用

```bash
# 组件画廊（浏览所有组件）
python examples/apps/gallery/demo.py

# 时钟应用
python examples/apps/clock/demo.py

# 登录界面
python examples/apps/login/demo.py
```

## 分类说明

| 分类 | 说明 | 组件数 |
|------|------|--------|
| [widgets](widgets/) | 基础 UI 组件：按钮、输入框、标签、数据视图等 | 36 |
| [date_time](date_time/) | 日期时间选择器 | 3 |
| [dialog_box](dialog_box/) | 对话框和消息框 | 5 |
| [layout](layout/) | 布局容器 | 1 |
| [material](material/) | 亚克力材质效果组件 | 8 |
| [navigation](navigation/) | 导航组件和窗口 | 16 |
| [settings](settings/) | 设置卡片（预留） | 0 |
| [apps](apps/) | 完整应用示例 | 6 |

## 与 Preview 工具的关系

- `examples/`：面向框架使用者，展示**代码怎么写**（布局、交互、参数配置）
- `devtools/preview`：面向组件开发者，快速**查看组件外观**

两者互补，examples 中的 demo 代码可以直接复制到项目中使用。

## 注意事项

- 所有示例需要 GUI 环境，建议在本地运行
- 部分示例（如 `gallery`）依赖项目根目录的 `qfluentwidgets` 包
- 运行前确保已安装依赖：`pip install -e .`
