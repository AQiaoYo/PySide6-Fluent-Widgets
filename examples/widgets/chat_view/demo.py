# coding: utf-8
"""
ChatView Demo

展示内容:
- 用户消息 (气泡式, 右对齐) + Agent 消息 (平铺式, 头像+名称+markdown)
- Agent 顶部显示 sender_name + subtitle (如 "DeepSeek V4 | 深度求索")
- Markdown 段落、列表、加粗、链接、表格正确渲染
- 多个 fenced 代码块独立卡片显示 (含语言图标 / 换行 / 复制)
- 流式追加: QTimer 模拟逐 token 输出 Agent 消息
- 复制 / 编辑 / 删除消息信号
- 亮色 / 暗色主题切换
"""
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel, ChatMessage, ChatRole, ChatView, FluentIcon, InfoBar,
    InfoBarPosition, PrimaryPushButton, PushButton, Theme, setTheme,
)


SAMPLE_USER = "用 python 写一个 hello world 程序"


SAMPLE_AGENT = """以下是一个简单的 Python "Hello World" 程序：

```python
# 打印 Hello World
print("Hello World!")
```

或者你也可以使用变量：

```python
# 使用变量
message = "Hello World!"
print(message)
```

运行这个程序会在控制台输出：

```plaintext
Hello World!
```

这是学习任何编程语言时最基础的程序，用于验证开发环境是否正确配置。

**支持的 Markdown 元素**:

- 段落、列表、加粗、斜体、`行内代码`
- [外部链接](https://github.com)
- 表格 (GFM):

| 语言 | 出现年份 | 创造者 |
|------|---------|-------|
| Python | 1991 | Guido van Rossum |
| JavaScript | 1995 | Brendan Eich |
| Rust | 2010 | Graydon Hoare |
"""


STREAM_REPLY = """让我详细解释一下:

```python
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

这是经典的递归实现, 但效率较低. 推荐使用 **动态规划** 优化."""


class Demo(QWidget):
    """ChatView 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ChatView - Demo')
        self.resize(960, 720)

        # --- 工具栏 ---
        self.streamBtn = PrimaryPushButton(FluentIcon.SEND, "模拟流式回复", self)
        self.clearBtn = PushButton(FluentIcon.DELETE, "清空", self)
        self.themeBtn = PushButton(FluentIcon.CONSTRACT, "切换主题", self)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.streamBtn)
        toolbar.addWidget(self.clearBtn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.themeBtn)

        # --- ChatView ---
        self.chat = ChatView(self)
        # 头像: 不显式设置, 使用内置默认 (Agent=蓝色圆底+机器人, User=紫色圆底+人形)
        # 实际项目可调用 self.chat.setAgentAvatar("path/to/logo.png") 替换
        # 注册默认显示名 (单条消息可通过 ChatMessage.sender_name 覆盖)
        self.chat.setAgentDisplayName("DeepSeek V4")
        self.chat.setUserDisplayName("您")

        # --- 信号 ---
        self.chat.messageCopied.connect(self._onCopied)
        self.chat.messageDeleteRequested.connect(self.chat.removeMessage)
        self.chat.messageEditRequested.connect(self._onEditRequested)

        self.streamBtn.clicked.connect(self._startStreaming)
        self.clearBtn.clicked.connect(self._reset)
        self.themeBtn.clicked.connect(self._toggleTheme)

        # --- 布局 ---
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(20, 20, 20, 20)
        rootLayout.setSpacing(12)
        rootLayout.addLayout(toolbar)
        rootLayout.addWidget(BodyLabel("聊天消息组件 (ChatView): 支持 Markdown 渲染、独立代码块卡片、流式追加", self))
        rootLayout.addWidget(self.chat, 1)

        # --- 流式状态 ---
        self._streamTimer = QTimer(self)
        self._streamTimer.timeout.connect(self._streamTick)
        self._streamTokens: list = []
        self._streamMsgId: str = ""

        self._isDark = False
        self._populate()

    # ------------------------------------------------------------------
    # 内容填充
    # ------------------------------------------------------------------

    def _populate(self):
        self.chat.clear()
        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content=SAMPLE_USER,
            subtitle="Tokens: 18  |  05/08 23:00",
        ))
        self.chat.addMessage(ChatMessage(
            role=ChatRole.AGENT,
            content=SAMPLE_AGENT,
            subtitle="05/08 23:00  |  Tokens: 1432 ↑128 ↓1304",
        ))

    def _reset(self):
        self._streamTimer.stop()
        self._streamTokens = []
        self._streamMsgId = ""
        self._populate()

    # ------------------------------------------------------------------
    # 流式模拟
    # ------------------------------------------------------------------

    def _startStreaming(self):
        if self._streamTimer.isActive():
            return

        # 先追加一条用户消息和一条空的 Agent 消息
        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content="给我演示一下流式输出, 并解释一下递归.",
        ))
        # 流式回复用一个不同的模型名演示 sender_name 字段优先级
        agent = ChatMessage(
            role=ChatRole.AGENT, content="",
            sender_name="GPT-4o", subtitle="OpenAI",
        )
        self.chat.addMessage(agent)
        self._streamMsgId = agent.id

        # 把回复切成 1-3 字符的 chunk, 模拟 token 流
        text = STREAM_REPLY
        chunks = []
        i = 0
        while i < len(text):
            step = 2 if (i // 5) % 2 == 0 else 3
            chunks.append(text[i:i + step])
            i += step
        self._streamTokens = chunks
        self._streamTimer.start(35)

    def _streamTick(self):
        if not self._streamTokens:
            self._streamTimer.stop()
            return
        token = self._streamTokens.pop(0)
        self.chat.appendDelta(self._streamMsgId, token)

    # ------------------------------------------------------------------
    # 信号回调
    # ------------------------------------------------------------------

    def _onCopied(self, message_id: str):
        InfoBar.success(
            title="已复制",
            content=f"消息 {message_id} 已复制到剪贴板",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
        )

    def _onEditRequested(self, message_id: str):
        InfoBar.info(
            title="编辑请求",
            content=f"宿主应在此弹出编辑 UI (id={message_id})",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1800,
        )

    # ------------------------------------------------------------------
    # 主题切换
    # ------------------------------------------------------------------

    def _toggleTheme(self):
        self._isDark = not self._isDark
        setTheme(Theme.DARK if self._isDark else Theme.LIGHT)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    sys.exit(app.exec())
