# coding: utf-8
"""Markdown 渲染视图

将一段 markdown 文本切分成「文本段 + fenced 代码段」交替的块序列, 文本段
使用 QTextBrowser + QTextDocument.setMarkdown (GFM 方言) 渲染, 代码段交给
独立的 CodeBlock 卡片渲染. 支持流式追加 (appendMarkdown) 与节流重渲.
"""

import re
from typing import List, Tuple

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QFrame, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget,
)

from ....common.font import getFont
from ....common.style_sheet import FluentStyleSheet, isDarkTheme
from .code_block import CodeBlock


__all__ = ['MarkdownView']


# fenced code block 切片正则: 支持 ``` 与 ~~~ 两种围栏, 可选语言名
# 不支持四空格缩进式代码块 (markdown 已经过时, 大模型几乎只用 fenced)
_FENCE_RE = re.compile(
    r"^(?P<fence>```|~~~)[ \t]*(?P<lang>[\w+\-.#]*)[ \t]*\n"
    r"(?P<body>.*?)"
    r"^(?P=fence)[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


def _split_markdown(text: str) -> List[Tuple[str, str, str]]:
    """切分 markdown 为块列表

    Returns:
        list of (kind, language, content):
            * kind in {"text", "code"}
            * language 仅 code 块有效, text 块为空字符串
            * content 为该块原始字符串
    """
    blocks: List[Tuple[str, str, str]] = []
    cursor = 0
    for m in _FENCE_RE.finditer(text):
        start, end = m.span()
        if start > cursor:
            seg = text[cursor:start]
            if seg.strip():
                blocks.append(("text", "", seg))
        lang = (m.group("lang") or "").strip() or "plaintext"
        body = m.group("body").rstrip("\n")
        blocks.append(("code", lang, body))
        cursor = end
    if cursor < len(text):
        seg = text[cursor:]
        if seg.strip():
            blocks.append(("text", "", seg))
    return blocks


# ----------------------------------------------------------------------
# 文本段: 高度自适应的 QTextBrowser
# ----------------------------------------------------------------------

class _TextBlock(QTextBrowser):
    """高度自适应的 markdown 文本段

    背景透明、无边框、不出滚动条, 高度跟随文档内容自动伸缩.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setOpenExternalLinks(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 横向 Preferred (按 sizeHint 显示, 受父级 maxWidth 限制),
        # 而非 Expanding (会强行吃满父容器, 与 user 气泡按内容收缩冲突)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # 与 BodyLabel 一致的 14pt 字体, 否则 QTextBrowser 默认走系统 9pt 显得太小
        self.setFont(getFont(14))
        self.document().setDefaultFont(getFont(14))
        self.document().setDocumentMargin(0)
        self._applyDocStyleSheet()
        # 注意: 不连 document().contentsChanged.
        # setMarkdown(text) 内部会先清空再插入, 中间会触发若干次 contentsChanged,
        # 每次都跑 _adjustHeight + updateGeometry 会让高度在 [4, target] 之间反复
        # 跳变, 父 layout 跟着抖动. 高度更新统一由 setMarkdown / resizeEvent 控制.

    def _applyDocStyleSheet(self):
        """给 QTextDocument 设置 inline code / 链接的默认样式

        QTextDocument 仅支持 CSS2 子集且对 inline padding 不友好;
        这里只能用 background-color + font-family + color 在视觉上区分行内代码.
        """
        if isDarkTheme():
            inline_bg = "rgba(255, 255, 255, 0.10)"
            inline_color = "#ffb4a8"
            link_color = "#7cc2ff"
        else:
            inline_bg = "rgba(0, 0, 0, 0.07)"
            inline_color = "#c7254e"
            link_color = "#0067c0"
        css = f"""
            code {{
                background-color: {inline_bg};
                color: {inline_color};
                font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace;
            }}
            a {{ color: {link_color}; text-decoration: none; }}
            pre, pre code {{ background: transparent; }}
        """
        self.document().setDefaultStyleSheet(css)

    def setMarkdown(self, text: str):
        # MarkdownDialectGitHub 在 Qt6 中支持表格、删除线、任务列表等.
        # 屏蔽 document 信号: setMarkdown 内部 (清空 + 插入) 会触发多次
        # contentsChanged / undoCommandAdded, 不屏蔽会引起短暂 layout 抖动.
        doc = self.document()
        was_blocked = doc.blockSignals(True)
        try:
            doc.setMarkdown(
                text, QTextDocument.MarkdownFeature.MarkdownDialectGitHub
            )
        finally:
            doc.blockSignals(was_blocked)
        self._adjustHeight()
        self.updateGeometry()  # 通知父 layout 重新计算 sizeHint

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type().name in ("StyleChange", "PaletteChange"):
            self._applyDocStyleSheet()
            # 重新解析以应用新 stylesheet
            md = self.document().toMarkdown(QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
            if md:
                self.document().setMarkdown(
                    md, QTextDocument.MarkdownFeature.MarkdownDialectGitHub
                )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 文档宽度跟随视口, 否则换行计算不准
        self.document().setTextWidth(self.viewport().width())
        self._adjustHeight()

    def _adjustHeight(self):
        self.document().setTextWidth(self.viewport().width())
        h = max(int(self.document().size().height()) + 4, 18)
        # 仅在高度真的变化时才调 setFixedHeight, 避免无谓 geometry 通知
        if self.height() != h:
            self.setFixedHeight(h)

    def _idealContentWidth(self) -> int:
        """计算文档不换行时的真实宽度.

        idealWidth() 受当前 textWidth 影响, 直接调可能返回换行后的宽度.
        临时取消 textWidth 限制后再读取, 然后立即还原.
        """
        doc = self.document()
        saved = doc.textWidth()
        doc.setTextWidth(-1)
        ideal = int(doc.idealWidth())
        doc.setTextWidth(saved)
        return ideal

    def sizeHint(self) -> QSize:
        """根据文档内容计算自然宽高, 替代 QTextEdit 默认的 256x192.

        宽: 文本不换行时所需宽度 (短消息小, 长消息按需) + 2px 余量
        高: 当前 textWidth 下的文档高度 (跟随父级 resize 动态调整)
        """
        ideal = self._idealContentWidth() + 2
        h = int(self.document().size().height()) + 4
        return QSize(max(ideal, 24), max(h, 18))

    def minimumSizeHint(self) -> QSize:
        # 允许收缩 (agent 长段落需要换行); user 短消息由 sizeHint 决定上限
        return QSize(0, 18)


# ----------------------------------------------------------------------
# MarkdownView 主体
# ----------------------------------------------------------------------

class MarkdownView(QWidget):
    """Markdown 渲染视图

    将 markdown 文本分块渲染为「文本段 + 独立代码块卡片」交替的垂直序列.
    支持流式追加 (appendMarkdown), 内部对重渲做了 50ms 节流以应对高频
    token 流场景.

    Attributes:
        contentChanged: 内容渲染完成后发出 (流式追加每次刷新也会发出)

    构造函数重载:
        * MarkdownView(parent: QWidget = None)
        * MarkdownView(text: str, parent: QWidget = None)
    """

    contentChanged = Signal()

    # 流式重渲节流间隔. 短一点 (~一帧) 让 token 视觉上连续追加;
    # 真正防抖靠 setMarkdown 的 blockSignals 与 _adjustHeight 的 idempotent 守卫.
    _RERENDER_DELAY_MS = 33

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)

        self._raw = ""
        self._blockWidgets: List[QWidget] = []
        # 上一次渲染时各 block 的 (kind, lang, content) 元数据
        # 用于判断结构是否变化, 决定增量更新还是全重建
        self._blocksMeta: List[Tuple[str, str, str]] = []
        # 内部 CodeBlock 的最大可见行数 (默认 10); 通过
        # ``setCodeBlockMaxVisibleLines`` 修改, 新创建及现有 CodeBlock 都会同步
        self._codeMaxVisibleLines = CodeBlock._DEFAULT_MAX_VISIBLE_LINES

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        self._renderTimer = QTimer(self)
        self._renderTimer.setSingleShot(True)
        self._renderTimer.timeout.connect(self._renderNow)

        FluentStyleSheet.CHAT_VIEW.apply(self)

        if text:
            self.setMarkdown(text)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setMarkdown(self, text: str):
        """设置完整 markdown 文本 (覆盖现有内容)"""
        self._raw = text or ""
        self._scheduleRender(immediate=True)

    def markdown(self) -> str:
        """获取当前完整 markdown 文本"""
        return self._raw

    def appendMarkdown(self, delta: str):
        """流式追加 markdown 文本

        参数 ``delta`` 会被拼接到现有内容尾部, 触发节流重渲.
        """
        if not delta:
            return
        self._raw += delta
        self._scheduleRender(immediate=False)

    def clear(self):
        """清空内容"""
        self._raw = ""
        self._scheduleRender(immediate=True)

    def codeBlockMaxVisibleLines(self) -> int:
        """获取内部 CodeBlock 的最大可见行数."""
        return self._codeMaxVisibleLines

    def setCodeBlockMaxVisibleLines(self, n: int):
        """设置内部 CodeBlock 的最大可见行数.

        新创建的 CodeBlock 以此为初值; 已存在的 CodeBlock 同步更新.

        Args:
            n: 最大可见行数 (≥ 1). 详见 ``CodeBlock.setMaxVisibleLines``.
        """
        n = max(1, int(n))
        if n == self._codeMaxVisibleLines:
            return
        self._codeMaxVisibleLines = n
        for w in self._blockWidgets:
            if isinstance(w, CodeBlock):
                w.setMaxVisibleLines(n)

    # ------------------------------------------------------------------
    # 渲染流程
    # ------------------------------------------------------------------

    def _scheduleRender(self, immediate: bool):
        if immediate:
            self._renderTimer.stop()
            self._renderNow()
        elif not self._renderTimer.isActive():
            self._renderTimer.start(self._RERENDER_DELAY_MS)

    def _clearBlocks(self):
        for w in self._blockWidgets:
            self._layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self._blockWidgets.clear()
        self._blocksMeta.clear()

    def _createBlockWidget(self, kind: str, lang: str, content: str) -> QWidget:
        if kind == "code":
            cb = CodeBlock(content, lang, self)
            cb.setMaxVisibleLines(self._codeMaxVisibleLines)
            return cb
        w = _TextBlock(self)
        w.setMarkdown(content)
        return w

    def _renderNow(self):
        """增量渲染.

        流式 token 高频追加场景下, 完整重建会导致 sizeHint 反复变化、滚动条
        max 频繁跳动, 视觉上呈现"上下抖动". 改用增量策略:

        1. 切分新 markdown 得到 blocks 列表
        2. 与上次渲染的 _blocksMeta 比较:
           * 块数不变 + 每个块的 (kind, lang) 一致 -> 仅对内容变化的块
             调用 setMarkdown / setCode, 复用现有 widget (不抖)
           * 否则 (块数变了或类型变了) -> 全量重建 (低频, 仅在新增/闭合
             代码围栏时发生)
        3. 缓存最新 meta
        """
        new_blocks = _split_markdown(self._raw)

        same_struct = (
            len(new_blocks) == len(self._blocksMeta)
            and all(
                nb[0] == ob[0] and nb[1] == ob[1]
                for nb, ob in zip(new_blocks, self._blocksMeta)
            )
        )

        if same_struct and self._blockWidgets:
            # 增量路径: 只更新内容变化的块
            for i, (kind, lang, content) in enumerate(new_blocks):
                old_content = self._blocksMeta[i][2]
                if content == old_content:
                    continue
                w = self._blockWidgets[i]
                if kind == "code":
                    w.setCode(content)
                else:
                    w.setMarkdown(content)
        else:
            # 全量路径: 结构变化时重建
            self._clearBlocks()
            for kind, lang, content in new_blocks:
                w = self._createBlockWidget(kind, lang, content)
                self._layout.addWidget(w)
                self._blockWidgets.append(w)

        self._blocksMeta = list(new_blocks)
        self.contentChanged.emit()
