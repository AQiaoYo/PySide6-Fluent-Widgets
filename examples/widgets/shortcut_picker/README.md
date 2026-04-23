# ShortcutPicker 快捷键选择器

基于 PySide6-Fluent-Widgets 的快捷键选择器组件，复刻 Pro 版本的功能。

## 功能特点

- **卡片式UI**: 使用 SimpleCardWidget 作为基础，支持悬停效果和点击交互
- **模态对话框**: 点击卡片弹出 MaskDialogBase 实现的模态对话框
- **键盘监听**: 使用 `grabKeyboard()` 捕获所有键盘输入
- **防抖处理**: 150ms 防抖定时器避免误触发
- **按键过滤**: 自动过滤单独的修饰键（Ctrl/Shift/Alt/Meta）
- **自适应宽度**: 按键按钮根据文字长度自适应宽度

## 使用示例

### 基本用法

```python
from qfluentwidgets import ShortcutPicker

# 创建带默认快捷键的选择器
picker = ShortcutPicker("Ctrl+Shift+A", parent)

# 监听快捷键变化
picker.shortcutChanged.connect(
    lambda seq: print(f"新快捷键: {seq.toString()}")
)
```

### 在设置卡片中使用

```python
from qfluentwidgets import HeaderCardWidget, ShortcutPicker

# 创建卡片
card = HeaderCardWidget("快捷键设置", parent)

# 添加快捷键选择器
picker = ShortcutPicker("Ctrl+C", card)
card.viewLayout.addWidget(picker)
```

### 获取和设置快捷键

```python
# 获取当前快捷键
seq = picker.shortcut()
print(seq.toString())  # "Ctrl+Shift+A"

# 设置新快捷键
picker.setShortcut(QKeySequence("Ctrl+V"))

# 重置为默认值
picker.resetToDefault()
```

## 组件结构

```
ShortcutPicker (卡片)
├── keyButtons[0-2] (ShortcutKeyButton - 显示快捷键按键)
├── editIcon (QLabel - 编辑图标)
└── clicked → ShortcutPickerDialog (弹出对话框)

ShortcutPickerDialog (模态对话框)
├── titleLabel (标题)
├── hintLabel (说明文字)
├── keyButtons[0-2] (ShortcutKeyButton - 显示输入的快捷键)
├── saveButton (PrimaryPushButton - 保存)
├── resetButton (PushButton - 重置)
└── cancelButton (PushButton - 取消)
```

## API 参考

### ShortcutPicker

**构造函数:**
- `ShortcutPicker(parent=None)` - 空快捷键
- `ShortcutPicker(shortcut: QKeySequence, parent=None)` - 带默认快捷键
- `ShortcutPicker(shortcut: str, parent=None)` - 使用字符串如 "Ctrl+Shift+A"

**方法:**
- `setShortcut(shortcut: QKeySequence)` - 设置显示的快捷键
- `shortcut() -> QKeySequence` - 获取当前快捷键
- `getDefaultShortcut() -> QKeySequence` - 获取默认快捷键
- `resetToDefault()` - 重置为默认快捷键

**信号:**
- `shortcutChanged(QKeySequence)` - 快捷键被修改时触发

### ShortcutPickerDialog

**构造函数:**
- `ShortcutPickerDialog(parent=None, currentShortcut: QKeySequence=None)`

**方法:**
- `setShortcut(shortcut: QKeySequence)` - 设置当前显示的快捷键
- `getShortcut() -> QKeySequence` - 获取设置的快捷键

**信号:**
- `shortcutSaved(QKeySequence)` - 用户点击保存时触发

## 防抖处理说明

对话框使用 QTimer 实现防抖:
- **按键按下**: 150ms 防抖后确认快捷键
- **按键释放**: 100ms 防抖处理连续按键

这样可以避免用户在快速按键时产生冲突。
