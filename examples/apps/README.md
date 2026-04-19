# Apps 示例

完整应用示例，展示如何在实际项目中组合使用多个组件。

## 应用列表

- [gallery](gallery/) - 组件画廊。浏览所有组件，支持搜索、分类查看、主题切换
- [clock](clock/) - 时钟应用。包含专注计时器和秒表功能
- [login](login/) - 登录界面示例
- [settings_app](settings_app/) - 设置界面示例，展示 SettingCard 系列组件的实际使用
- [splash_screen](splash_screen/) - 启动画面示例
- [web_engine](web_engine/) - Web 引擎集成示例

## 运行方式

```bash
python examples/apps/<应用名>/demo.py
```

## 与组件示例的区别

| | 组件示例 (widgets/ 等) | 完整应用 (apps/) |
|--|------------------------|------------------|
| 目标 | 展示单个组件的用法 | 展示组件的组合使用 |
| 代码量 | 少，聚焦单一功能 | 多，包含完整业务逻辑 |
| 可直接复用 | 是 | 需要适配 |
| 学习价值 | API 和参数 | 架构和交互设计 |
