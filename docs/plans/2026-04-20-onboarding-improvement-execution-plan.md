---
date: 2026-04-20
topic: 优化学习引导体验
requirement: docs/requirements/2026-04-20-onboarding-improvement.md
grade: L
---

# 执行计划：优化学习引导体验

## 内部等级：L（串行执行）

本任务为文档层优化，无复杂代码改动，各交付物有轻微依赖关系，采用串行波次执行。

## Wave 1：信息收集（10 min）

**目标**：生成完整的组件分类清单，作为后续文档的数据源。

- [ ] W1.1 扫描 `examples/` 目录，提取所有 demo 的分类和组件名
- [ ] W1.2 扫描 `qfluentwidgets/components/` 各子包，确认与示例的对应关系
- [ ] W1.3 记录每个分类的组件数量，用于 COMPONENTS.md 表格

**产出**：组件分类清单（内存中，不持久化）

## Wave 2：核心文档编写（30 min）

### W2.1 COMPONENTS.md — 组件索引

**路径**：`docs/COMPONENTS.md`

**结构**：
```
# 组件索引

## 快速查找
按分类浏览或搜索组件名...

## 基础组件（widgets）
| 组件 | 说明 | 示例 |
|------|------|------|
| PushButton | 标准推送按钮 | examples/widgets/button/demo.py |
...

## 导航组件（navigation）
...

## 对话框（dialog_box）
...

## 布局（layout）
...

## 日期时间（date_time）
...

## 材质效果（material）
...

## 设置卡片（settings）
...

## 完整应用（apps）
...
```

**要求**：
- 每个组件一行说明（从源码类 docstring 第一行提取或手写）
- 链接到对应 demo 路径（相对路径，GitHub 上可点击）
- 表格末尾标注"共 X 个组件"

### W2.2 TUTORIAL.md — 入门教程

**路径**：`docs/TUTORIAL.md`

**章节**：
1. **准备工作**：安装（uv/pip）+ 克隆仓库
2. **第一个窗口**：运行 gallery demo，看到效果
3. **写一个简单界面**：从 PushButton + SwitchButton 开始，50 行代码
4. **切换主题**：一行代码 setTheme()
5. **使用导航组件**：构建一个带侧边栏的多页面应用（基于 gallery 结构简化）
6. **下一步**：推荐阅读 COMPONENTS.md、查看对应 demo、查阅源码 docstring

**要求**：
- 所有代码可直接复制运行
- 代码有中文注释
- 每节有"本节目标"和"关键概念"小结

## Wave 3：表层修复与整合（15 min）

### W3.1 README.md 修复

- [ ] 修正 `examples/gallery/demo.py` → `examples/apps/gallery/demo.py`
- [ ] 在"Run Example"部分添加 COMPONENTS.md 和 TUTORIAL.md 的链接提示
- [ ] 确保中英文 README 同步更新

### W3.2 Sphinx 文档更新

- [ ] `docs/source/index.rst`：标题改为 `PySide6-Fluent-Widgets-Qiao`
- [ ] `docs/source/index.rst`：toctree 添加 `components` 和 `tutorial`（指向 COMPONENTS.md 和 TUTORIAL.md）
- [ ] `docs/source/quick-start.rst`：补充中文引导文字，说明如何找到组件示例

## Wave 4：验证与清理（10 min）

- [ ] V4.1 检查所有新增/修改文档的 Markdown 语法
- [ ] V4.2 验证 README 中的路径在实际文件系统中存在
- [ ] V4.3 验证 COMPONENTS.md 中所有 demo 路径存在
- [ ] V4.4 运行 `python examples/apps/gallery/demo.py` 确认正常（如果 GUI 环境可用）
- [ ] V4.5 git diff 审查，确保没有意外修改源码
- [ ] V4.6 清理临时文件

## 回滚规则

- 所有改动均为文档层，可随时 `git checkout -- <file>` 回滚单个文件
- 若某交付物质量不达标，单独 revert，不影响其他交付物

## 阶段清理预期

- 删除过程中可能产生的临时草稿文件
- 保留最终交付物：README.md（修改）、docs/COMPONENTS.md、docs/TUTORIAL.md、docs/source/*.rst（修改）
- 提交时打 `docs:` 前缀标签

## 完成标准

所有验收标准（见需求文档）逐一验证通过，方可声明完成。
