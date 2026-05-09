# coding: utf-8
"""
AgentChatView Demo (Enhanced)

展示内容:
- 用户消息 (气泡式) + Agent 消息 (平铺式) + Markdown / 代码块 / 表格
- 流式追加 (token 级)
- 交错 Agent 运行: think -> tool(read_file) -> think -> tool(bash) -> final answer
  + 顶部 GenerationStatusBar (spinner + 状态 + token 数 + 计时 + Stop)
- 审批闸门: write_file 调用 PENDING_APPROVAL, 用户点 [批准]/[拒绝] 后流程继续
- 特化工具集: 一次性插入 6 种特化工具卡片 (read/write/edit-diff/bash/web/grep)
- 重新生成 / 编辑 / 删除消息 信号
- Token 预估指示器 (上下文数 / 估算 token 数), 跟随输入框文本与历史动态更新
- 亮色 / 暗色主题切换 (FluentWindow Mica 背景适配)

主窗口使用 ``FluentWindow`` (左侧导航 + Mica 标题栏), 切换主题时窗口背景
跟随系统亚克力 / 云母效果一并刷新, 是验证组件主题适配的最直观方式.
"""
import sys
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    AgentChatPanel, AgentChatView, BodyLabel, ChatMessage, ChatRole,
    FluentIcon, FluentWindow, InfoBar, InfoBarPosition, PrimaryPushButton,
    PushButton, Theme, TextSegment, ThinkingSegment, ToolCallSegment,
    ToolCallStatus, ToolTipFilter, ToolTipPosition, setTheme,
)


# ----------------------------------------------------------------------
# 静态文本样本
# ----------------------------------------------------------------------

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


# ---- 交错 Agent: think -> tool(read) -> think -> tool(bash) -> final ----

THINK1_REPLY = """嗯, 用户想让我读 `main.py` 然后在沙箱里跑一下看看输出.

我应该:
1. 调 `read_file` 拿到文件内容
2. 看看代码是不是有副作用 (网络/磁盘 IO 等)
3. 用 `bash` 跑一下, 收集输出
4. 给出结论"""

READ_PREVIEW = """def main() -> None:
    print("Hello, world!")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
"""

THINK2_REPLY = """好, 文件就是个最简版 hello world, 没有外部依赖.

直接 `python main.py` 跑就行, 安全."""

BASH_OUTPUT = """Hello, world!
"""

FINAL_REPLY = """## 结论

`main.py` 是经典的 Python 入口脚本:

- 定义 `main()` 打印 `Hello, world!` 并返回 `0`
- `if __name__ == "__main__"` 包裹 `SystemExit(main())` 作为退出码
- **没有副作用**, 也无外部依赖

实际运行输出:

```text
Hello, world!
```

退出码 `0` (成功).
"""


# ---- 特化工具集 demo 数据 ----

EDIT_OLD = """def add(a, b):
    return a + b


def mul(a, b):
    return a * b
"""

EDIT_NEW = """def add(a: int, b: int) -> int:
    \"\"\"Sum two ints.\"\"\"
    return a + b


def mul(a: int, b: int) -> int:
    \"\"\"Multiply two ints.\"\"\"
    return a * b
"""

WEB_RESULTS = [
    {
        "title": "OpenCode -- agentic coding from your terminal",
        "url": "https://github.com/sst/opencode",
        "snippet": "OpenCode is a TUI for agentic coding, supporting multiple LLM providers and rich tool integrations.",
    },
    {
        "title": "Cherry Studio - Multi-model AI assistant",
        "url": "https://github.com/CherryHQ/cherry-studio",
        "snippet": "Cherry Studio supports cloud LLMs, local models, knowledge bases, and visual painting tools in one client.",
    },
    {
        "title": "Anthropic Claude API documentation",
        "url": "https://docs.anthropic.com",
        "snippet": "Build with Claude. Tool use, extended thinking, vision, prompt caching and more.",
    },
]

GREP_HITS = [
    {"path": "qfluentwidgets/components/widgets/chat/__init__.py",
     "line": 36, "preview": "from .diff_view import DiffView"},
    {"path": "qfluentwidgets/components/widgets/chat/agent_chat_view.py",
     "line": 71, "preview": "    toolCallApprovalRequested = Signal(str, str)"},
    {"path": "qfluentwidgets/components/widgets/chat/tool_renderers.py",
     "line": 84, "preview": "def resolveToolRenderer(tool_name: str) -> ToolCardFactory:"},
    {"path": "qfluentwidgets/components/widgets/chat/chat_bubble.py",
     "line": 71, "preview": "    regenerateClicked = Signal(str)"},
    {"path": "qfluentwidgets/components/widgets/chat/diff_view.py",
     "line": 38, "preview": "class DiffView(QFrame):"},
]


# ----------------------------------------------------------------------
# Demo 主窗
# ----------------------------------------------------------------------

# Token 预估上限 (demo 用, 真实场景应根据模型 context window 配置)
DEMO_MAX_CONTEXT = 20      # 上下文最多 20 条消息
DEMO_MAX_TOKENS = 8000     # 模型 context window


class ChatInterface(QWidget):
    """聊天主界面 — 顶部工具栏 + 描述行 + AgentChatPanel.

    作为 ``FluentWindow`` 的子界面挂载, 组件库窗口提供 Mica 背景、自定义
    标题栏与导航栏, 主题切换时窗口整体随之刷新.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("agentChatInterface")

        # --- 工具栏: 各按钮统一安装 Fluent ToolTipFilter ---
        self.streamBtn = self._mkToolbarBtn(
            PrimaryPushButton, FluentIcon.SEND, "流式回复",
            tip="模拟一次 token 级流式输出",
        )
        self.agentBtn = self._mkToolbarBtn(
            PushButton, FluentIcon.ROBOT, "交错 Agent 运行",
            tip="演示 think -> tool -> think -> tool -> answer 完整链路",
        )
        self.approvalBtn = self._mkToolbarBtn(
            PushButton, FluentIcon.ACCEPT, "审批闸门",
            tip="演示 write_file 工具的批准 / 拒绝交互",
        )
        self.toolsBtn = self._mkToolbarBtn(
            PushButton, FluentIcon.DEVELOPER_TOOLS, "特化工具集",
            tip="一次性插入 6 种特化工具卡片 (read/write/edit-diff/bash/web/grep)",
        )
        self.clearBtn = self._mkToolbarBtn(
            PushButton, FluentIcon.DELETE, "清空",
            tip="重置消息流, 还原到初始示例",
        )
        self.themeBtn = self._mkToolbarBtn(
            PushButton, FluentIcon.CONSTRACT, "切换主题",
            tip="在亮色 / 暗色主题之间切换, 验证组件主题适配",
        )

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addWidget(self.streamBtn)
        toolbar.addWidget(self.agentBtn)
        toolbar.addWidget(self.approvalBtn)
        toolbar.addWidget(self.toolsBtn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.clearBtn)
        toolbar.addWidget(self.themeBtn)

        # --- AgentChatPanel: 消息流 + 输入区 一体化 ---
        # ``chatPanel`` 是面向应用方的容器, ``chatPanel.chatView()`` 拿到
        # 内部的 AgentChatView. 下方所有 ``self.chat.xxx`` 调用沿用之前
        # 的代码, 不需改动.
        self.chatPanel = AgentChatPanel(self)
        self.chat: AgentChatView = self.chatPanel.chatView()
        self.chat.setAgentDisplayName("DeepSeek V4")
        self.chat.setUserDisplayName("您")
        self.chat.setRegenerateEnabled(True)
        self.chat.requireApproval("write_file", "edit_file", "bash")
        self.chatPanel.setInputPlaceholder("输入消息... (Enter 发送, Shift+Enter 换行)")
        self.chatPanel.sendRequested.connect(self._onUserSent)
        # 输入框文本变化 -> 实时刷新 token 预估指示器
        self.chatPanel.inputEdit().textChanged.connect(self._refreshTokenInfo)

        # --- 信号 ---
        self.chat.messageCopied.connect(self._onCopied)
        self.chat.messageDeleteRequested.connect(self.chat.removeMessage)
        self.chat.messageEditRequested.connect(self._onEditRequested)
        self.chat.regenerateRequested.connect(self._onRegenerateRequested)
        self.chat.stopRequested.connect(self._onStopRequested)
        self.chat.toolCallApprovalRequested.connect(self._onApprovalRequested)
        self.chat.toolCallApproved.connect(self._onToolApproved)
        self.chat.toolCallRejected.connect(self._onToolRejected)
        # 消息流变化 -> 刷新 token 预估
        self.chat.lastMessageChanged.connect(self._refreshTokenInfo)
        self.chat.messageRemoved.connect(lambda _mid: self._refreshTokenInfo())
        self.chat.messagesCleared.connect(self._refreshTokenInfo)

        self.streamBtn.clicked.connect(self._startStreaming)
        self.agentBtn.clicked.connect(self._startInterleavedAgent)
        self.approvalBtn.clicked.connect(self._startApprovalDemo)
        self.toolsBtn.clicked.connect(self._showSpecializedTools)
        self.clearBtn.clicked.connect(self._reset)
        self.themeBtn.clicked.connect(self._toggleTheme)

        # --- 布局 ---
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(20, 20, 20, 20)
        rootLayout.setSpacing(12)
        rootLayout.addLayout(toolbar)
        rootLayout.addWidget(BodyLabel(
            "AgentChatView 增强 Demo: Segment 化数据模型, 交错 think/tool/think, "
            "生成状态条 + Stop, 审批闸门 + 特化工具卡片",
            self,
        ))
        rootLayout.addWidget(self.chatPanel, 1)

        # --- 流式状态 ---
        self._streamTimer = QTimer(self)
        self._streamTimer.timeout.connect(self._streamTick)
        self._streamTokens: List[str] = []
        self._streamMsgId: str = ""

        self._isDark = False
        self._populate()
        self._refreshTokenInfo()

    # ------------------------------------------------------------------
    # 工具栏构造工具
    # ------------------------------------------------------------------

    def _mkToolbarBtn(self, cls, icon, text: str, tip: str):
        """构造工具栏按钮 + 安装 Fluent ToolTipFilter (TOP 方位).

        Args:
            cls: 按钮类 (``PushButton`` / ``PrimaryPushButton`` 等)
            icon: ``FluentIcon`` 实例
            text: 按钮文本
            tip: 工具提示文本 (悬停 ~300ms 后显示, 顶部弹出)
        """
        btn = cls(icon, text, self)
        btn.setToolTip(tip)
        btn.installEventFilter(
            ToolTipFilter(btn, showDelay=300, position=ToolTipPosition.TOP)
        )
        return btn

    # ------------------------------------------------------------------
    # 用户输入处理
    # ------------------------------------------------------------------

    def _onUserSent(self, text: str):
        """用户在 AgentChatPanel 输入框按 Enter / 点发送 触发.

        真实应用里应该把 ``text`` 提交给后端 LLM, 拿流式 token 通过
        ``self.chat.appendDelta(msg_id, token)`` 增量追加. 这里 demo
        用一个简单的 echo 模拟.
        """
        # 1. 把用户消息加入流
        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER, content=text,
            subtitle="刚刚",
        ))

        # 2. 创建空的 agent 消息, 准备流式追加
        agent = ChatMessage(
            role=ChatRole.AGENT, content="",
            sender_name="DeepSeek V4",
            subtitle="刚刚",
        )
        self.chat.addMessage(agent)

        # 3. 模拟 200ms 后开始流式追加 echo 回复
        reply = (
            f"收到: **{text}**\n\n"
            f"这是 demo 的 echo 回复. 真实应用里这里应该接 LLM 流式 API:\n\n"
            f"```python\n"
            f"async for token in llm.stream(text):\n"
            f"    chat.appendDelta(msg_id, token)\n"
            f"```\n"
        )
        tokens = self._chunk(reply, 2, 4)
        timer = QTimer(self)
        timer.setInterval(40)

        def tick():
            if not tokens:
                timer.stop()
                timer.deleteLater()
                return
            self.chat.appendDelta(agent.id, tokens.pop(0))

        timer.timeout.connect(tick)
        timer.start()

    # ------------------------------------------------------------------
    # 内容填充
    # ------------------------------------------------------------------

    def _populate(self):
        self.chat.clear()
        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER, content=SAMPLE_USER,
            subtitle="Tokens: 18  |  05/09 15:00",
        ))
        self.chat.addMessage(ChatMessage(
            role=ChatRole.AGENT, content=SAMPLE_AGENT,
            subtitle="05/09 15:00  |  Tokens: 1432 ↑128 ↓1304",
        ))

    def _reset(self):
        self._streamTimer.stop()
        self._streamTokens = []
        self._streamMsgId = ""
        if hasattr(self, "_agentTimer"):
            self._agentTimer.stop()
        self._populate()

    # ------------------------------------------------------------------
    # 1) 流式回复
    # ------------------------------------------------------------------

    def _startStreaming(self):
        if self._streamTimer.isActive():
            return

        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content="给我演示一下流式输出, 并解释一下递归.",
        ))
        agent = ChatMessage(
            role=ChatRole.AGENT, content="",
            sender_name="GPT-4o", subtitle="OpenAI",
        )
        self.chat.addMessage(agent)
        self._streamMsgId = agent.id

        self._streamTokens = self._chunk(STREAM_REPLY, 2, 3)
        self._streamTimer.start(35)

    def _streamTick(self):
        if not self._streamTokens:
            self._streamTimer.stop()
            return
        token = self._streamTokens.pop(0)
        self.chat.appendDelta(self._streamMsgId, token)

    # ------------------------------------------------------------------
    # 2) 交错 Agent 运行 (think -> tool -> think -> tool -> answer)
    # ------------------------------------------------------------------

    def _startInterleavedAgent(self):
        if self._anyTimerActive():
            return

        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content="读一下 `main.py` 然后跑一下看看输出.",
        ))
        agent = ChatMessage(
            role=ChatRole.AGENT, content="",
            sender_name="DeepSeek-R1", subtitle="深度求索 · 推理模式",
        )
        self.chat.addMessage(agent)
        self._iaMsgId = agent.id
        self._iaTokens = 0
        self._iaPhase = 0
        self._iaCallId = None  # 当前活跃 tool call id

        # 切片所有流式片段
        self._iaThink1 = self._chunk(THINK1_REPLY, 2, 4)
        self._iaThink2 = self._chunk(THINK2_REPLY, 2, 4)
        self._iaFinal = self._chunk(FINAL_REPLY, 2, 4)
        self._iaToolReadChunks = self._chunk(READ_PREVIEW, 4, 8)
        self._iaToolBashChunks = self._chunk(BASH_OUTPUT, 4, 8)

        self.chat.beginGeneration(self._iaMsgId, "正在思考...")

        if not hasattr(self, "_agentTimer"):
            self._agentTimer = QTimer(self)
            self._agentTimer.timeout.connect(self._iaTick)
        self._agentTimer.start(35)

    def _iaTick(self):
        # 状态机: 0=think1, 1=endThink1, 2=tool1 launch, 3=tool1 stream,
        # 4=tool1 done, 5=think2, 6=endThink2, 7=tool2 launch,
        # 8=tool2 stream, 9=tool2 done, 10=final, 11=stop
        ph = self._iaPhase
        mid = self._iaMsgId

        if ph == 0:  # thinking 1
            if self._iaThink1:
                ck = self._iaThink1.pop(0)
                self.chat.appendThinkingDelta(mid, ck)
                self._bumpTokens(len(ck))
                self.chat.setGenerationStatus(mid, "正在思考 (1/2)...")
                return
            self._iaPhase = 1
            return

        if ph == 1:  # end thinking 1
            self.chat.endThinking(mid, duration_ms=2300)
            self._iaPhase = 2
            return

        if ph == 2:  # launch tool 1 (read_file with metadata)
            self.chat.setGenerationStatus(mid, "正在调用 read_file...")
            self._iaCallId = self.chat.addToolCall(
                mid, tool_name="read_file",
                arguments='{\n  "path": "main.py"\n}',
                metadata={
                    "path": "main.py", "language": "python",
                    "start_line": 1, "end_line": 6,
                    "preview_content": READ_PREVIEW,
                },
                requires_approval=False,  # read 安全, 不审批
            )
            self._iaPhase = 3
            return

        if ph == 3:  # tool 1 stream (本演示用 metadata.preview_content, 此处 noop)
            # 模拟 1 拍的耗时
            self._iaPhase = 4
            return

        if ph == 4:  # tool 1 done
            self.chat.setToolCallStatus(
                mid, self._iaCallId, ToolCallStatus.SUCCESS, 420,
            )
            self._iaCallId = None
            self._iaPhase = 5
            return

        if ph == 5:  # thinking 2 (新 ThinkingSegment, 与 thinking 1 并存)
            if self._iaThink2:
                ck = self._iaThink2.pop(0)
                self.chat.appendThinkingDelta(mid, ck)
                self._bumpTokens(len(ck))
                self.chat.setGenerationStatus(mid, "正在思考 (2/2)...")
                return
            self._iaPhase = 6
            return

        if ph == 6:
            self.chat.endThinking(mid, duration_ms=850)
            self._iaPhase = 7
            return

        if ph == 7:  # launch tool 2 (bash with metadata)
            self.chat.setGenerationStatus(mid, "正在调用 bash...")
            self._iaCallId = self.chat.addToolCall(
                mid, tool_name="bash",
                arguments="python main.py",
                metadata={
                    "command": "python main.py",
                    "exit_code": 0,
                },
                requires_approval=False,  # 在 demo 里直接放过
            )
            self._iaPhase = 8
            return

        if ph == 8:  # tool 2 stream
            if self._iaToolBashChunks:
                ck = self._iaToolBashChunks.pop(0)
                self.chat.appendToolCallResult(mid, self._iaCallId, ck)
                self._bumpTokens(len(ck))
                return
            self._iaPhase = 9
            return

        if ph == 9:
            self.chat.setToolCallStatus(
                mid, self._iaCallId, ToolCallStatus.SUCCESS, 180,
            )
            self._iaCallId = None
            self._iaPhase = 10
            self.chat.setGenerationStatus(mid, "正在生成回答...")
            return

        if ph == 10:  # final answer streaming
            if self._iaFinal:
                ck = self._iaFinal.pop(0)
                self.chat.appendDelta(mid, ck)
                self._bumpTokens(len(ck))
                return
            self._iaPhase = 11
            return

        # ph >= 11: 收尾
        self._agentTimer.stop()
        self.chat.endGeneration(mid)

    def _bumpTokens(self, char_count: int):
        # 粗略: 4 字符 ~= 1 token
        self._iaTokens += max(1, char_count // 3)
        self.chat.setGenerationTokens(
            self._iaMsgId, self._iaTokens, rate=20.0,
        )

    # ------------------------------------------------------------------
    # 3) 审批闸门
    # ------------------------------------------------------------------

    def _startApprovalDemo(self):
        if self._anyTimerActive():
            return

        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content="把 `print('hi')` 写到 `a.py` 里.",
        ))
        agent = ChatMessage(
            role=ChatRole.AGENT, content="",
            sender_name="DeepSeek V4", subtitle="深度求索",
        )
        self.chat.addMessage(agent)

        # 先来一段 markdown 介绍意图
        self.chat.appendDelta(
            agent.id,
            "我准备把这一行写到 `a.py`. 这次操作会创建文件, 需要你的批准.\n\n",
        )

        # 触发 write_file 工具调用 (走全局策略, 因为已 requireApproval)
        cid = self.chat.addToolCall(
            agent.id, tool_name="write_file",
            arguments='{"path":"a.py","content":"print(\\"hi\\")\\n"}',
            metadata={
                "path": "a.py", "language": "python",
                "content": "print('hi')\n",
            },
        )
        # cid 不为 None 时表示 PENDING_APPROVAL 已就位
        self._approvalCallId = cid
        self._approvalMsgId = agent.id

    def _onApprovalRequested(self, message_id: str, call_id: str):
        InfoBar.warning(
            title="等待审批",
            content=f"工具 write_file 等待批准 (call={call_id[:6]}...)",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
        )

    def _onToolApproved(self, message_id: str, call_id: str):
        # 模拟工具实际执行: 0.3s 后返回结果
        InfoBar.success(
            title="已批准",
            content="开始执行 write_file...",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
        )

        def _finish():
            self.chat.appendToolCallResult(
                message_id, call_id, "wrote 13 bytes to a.py",
            )
            self.chat.setToolCallStatus(
                message_id, call_id, ToolCallStatus.SUCCESS, 320,
            )
            self.chat.appendDelta(
                message_id,
                "\n\n已写入 `a.py`. 文件内容:\n\n```python\nprint('hi')\n```\n",
            )

        QTimer.singleShot(300, _finish)

    def _onToolRejected(self, message_id: str, call_id: str):
        InfoBar.error(
            title="已拒绝",
            content="操作已被拒绝, 不会写入文件",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
        )
        self.chat.appendDelta(
            message_id,
            "\n\n好的, 已取消写入. 你可以让我尝试其它方式.",
        )

    # ------------------------------------------------------------------
    # 4) 特化工具集 (一次性插入 6 张卡片)
    # ------------------------------------------------------------------

    def _showSpecializedTools(self):
        if self._anyTimerActive():
            return

        self.chat.addMessage(ChatMessage(
            role=ChatRole.USER,
            content="演示一下各种特化工具卡片的视觉效果.",
        ))

        # 用 segments 列表一次性构造一条 AGENT 消息, 包含 6 个 ToolCallSegment
        # + 一个 final TextSegment
        segs = [
            TextSegment(
                content="这是 6 种内置特化工具卡片的静态展示, 全部已 SUCCESS:\n\n",
            ),
            ToolCallSegment(
                tool_name="read_file",
                arguments='{"path":"main.py"}',
                result=READ_PREVIEW,
                status=ToolCallStatus.SUCCESS,
                duration_ms=420,
                metadata={
                    "path": "main.py", "language": "python",
                    "start_line": 1, "end_line": 6,
                    "preview_content": READ_PREVIEW,
                },
            ),
            ToolCallSegment(
                tool_name="write_file",
                arguments='{"path":"a.py"}',
                result="wrote 13 bytes",
                status=ToolCallStatus.SUCCESS,
                duration_ms=180,
                metadata={
                    "path": "a.py", "language": "python",
                    "content": "print('hi')\n",
                },
            ),
            ToolCallSegment(
                tool_name="edit_file",
                arguments='{"path":"util.py"}',
                result="patched",
                status=ToolCallStatus.SUCCESS,
                duration_ms=210,
                metadata={
                    "path": "util.py",
                    "old": EDIT_OLD,
                    "new": EDIT_NEW,
                },
            ),
            ToolCallSegment(
                tool_name="bash",
                arguments="python main.py",
                result=BASH_OUTPUT,
                status=ToolCallStatus.SUCCESS,
                duration_ms=180,
                metadata={
                    "command": "python main.py",
                    "exit_code": 0,
                },
            ),
            ToolCallSegment(
                tool_name="web_search",
                arguments='{"query":"agent chat ui frameworks"}',
                result="3 results",
                status=ToolCallStatus.SUCCESS,
                duration_ms=890,
                metadata={
                    "query": "agent chat ui frameworks",
                    "results": WEB_RESULTS,
                },
            ),
            ToolCallSegment(
                tool_name="grep_search",
                arguments='{"query":"Signal"}',
                result="5 hits",
                status=ToolCallStatus.SUCCESS,
                duration_ms=130,
                metadata={
                    "query": "Signal",
                    "hits": GREP_HITS,
                },
            ),
            TextSegment(
                content=(
                    "\n\n上面 6 张卡片分别由 `FileReadCard` / `FileWriteCard` / "
                    "`FileEditCard` (DiffView) / `BashCard` (终端样式 + 退出码) / "
                    "`WebSearchCard` (链接) / `GrepSearchCard` (path:line + 预览) "
                    "渲染, 全部由 `tool_renderers` 注册表自动解析."
                ),
            ),
        ]

        agent = ChatMessage(
            role=ChatRole.AGENT,
            sender_name="Agent (Tool Showcase)",
            subtitle="特化渲染器静态展示",
            segments=segs,
        )
        self.chat.addMessage(agent)
        # 默认所有卡片折叠; 用户点击展开. (不主动 setExpanded, 让 UI 干净)

    # ------------------------------------------------------------------
    # 信号回调
    # ------------------------------------------------------------------

    def _onCopied(self, message_id: str):
        InfoBar.success(
            title="已复制",
            content=f"消息 {message_id[:8]}... 已复制到剪贴板",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
        )

    def _onEditRequested(self, message_id: str):
        InfoBar.info(
            title="编辑请求",
            content=f"宿主应在此弹出编辑 UI (id={message_id[:8]}...)",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1800,
        )

    def _onRegenerateRequested(self, message_id: str):
        InfoBar.info(
            title="重新生成",
            content=f"宿主应在此重新调用 LLM (id={message_id[:8]}...)",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1800,
        )

    def _onStopRequested(self, message_id: str):
        # 立即停止 timer, 然后告诉 view 终止生成 (stopped=True 显示已停止)
        if hasattr(self, "_agentTimer"):
            self._agentTimer.stop()
        self.chat.endGeneration(message_id, stopped=True)
        InfoBar.warning(
            title="已停止",
            content="生成已被用户中断",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=1500,
        )

    # ------------------------------------------------------------------
    # 主题切换
    # ------------------------------------------------------------------

    def _toggleTheme(self):
        self._isDark = not self._isDark
        setTheme(Theme.DARK if self._isDark else Theme.LIGHT)

    # ------------------------------------------------------------------
    # Token 预估
    # ------------------------------------------------------------------

    def _refreshTokenInfo(self):
        """根据当前消息流 + 输入框文本刷新 token 预估指示器.

        粗略估算: 4 字符 ~= 1 token (英文常用比例; 中文实际约 1.5-2 字符/token).
        真实应用应调用 LLM 提供的 tokenizer (如 ``tiktoken``).
        """
        # 上下文条数 = 当前 chatView 中所有消息数
        ctx_used = len(self.chat.messages())

        # 估算 token 数: 累加所有消息 content + 输入框文本, 除以 4
        char_count = 0
        for msg in self.chat.messages():
            char_count += len(msg.content or "")
            for seg in msg.segments:
                if isinstance(seg, TextSegment):
                    char_count += len(seg.content or "")
                elif isinstance(seg, ThinkingSegment):
                    char_count += len(seg.content or "")
                elif isinstance(seg, ToolCallSegment):
                    char_count += len(seg.arguments or "") + len(seg.result or "")
        char_count += len(self.chatPanel.inputText())
        tokens_used = max(0, char_count // 4)

        self.chatPanel.setTokenInfo(
            context_used=ctx_used, context_max=DEMO_MAX_CONTEXT,
            tokens_used=tokens_used, tokens_max=DEMO_MAX_TOKENS,
        )

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    def _anyTimerActive(self) -> bool:
        if self._streamTimer.isActive():
            return True
        t = getattr(self, "_agentTimer", None)
        return bool(t and t.isActive())

    @staticmethod
    def _chunk(text: str, lo: int, hi: int) -> List[str]:
        out, i = [], 0
        n = len(text)
        while i < n:
            step = lo if (i // 7) % 2 == 0 else hi
            out.append(text[i:i + step])
            i += step
        return out


class Demo(FluentWindow):
    """AgentChatView 增强 Demo 主窗 (FluentWindow + 单一聊天子界面).

    选择 ``FluentWindow`` 而非裸 ``QWidget`` 是为了:

    1. 启用 Mica / 亚克力背景, 主题切换 (``setTheme(Theme.DARK / LIGHT)``)
       时窗口背景颜色 + 标题栏会立即跟随刷新, 是验证组件库整体主题适配
       最直观的方式.
    2. 提供自定义标题栏 (无菜单/最小化/关闭按钮均带 hover 反馈).
    3. 默认带左侧导航视图, 之后想扩展多个 demo 子界面只需 ``addSubInterface``
       多调几次, 不必另起 main.py.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgentChatView - Enhanced Demo")
        self.resize(1180, 820)
        self.setMinimumSize(880, 620)

        # 单一子界面: 把全部 demo 内容放进 ChatInterface
        self.chatInterface = ChatInterface(self)
        self.addSubInterface(
            self.chatInterface, FluentIcon.CHAT, self.tr("Agent Chat"),
        )


if __name__ == '__main__':
    # 在 QApplication 创建**之前**设 HiDPI 缩放策略.
    # Qt 6 默认 ``Round`` 把非整数 DPR (例如 Win11 的 1.5x) 四舍五入到 1x,
    # 导致整个 UI 按 1x 像素绘制再被 Windows 拉伸 1.5x, 中文 / 图标视觉模糊.
    # ``PassThrough`` 让 Qt 直接用原始小数倍 DPR 绘制, 与 Chrome / Edge 等
    # Per-Monitor V2 DPI aware 应用一致, 文字边缘锐利.
    from PySide6.QtGui import QGuiApplication
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    sys.exit(app.exec())
