# coding: utf-8
"""Markdown 渲染视图

将一段 markdown 文本切分成「文本段 + fenced 代码段」交替的块序列, 文本段
使用 QTextBrowser + QTextDocument.setMarkdown (GFM 方言) 渲染, 代码段交给
独立的 CodeBlock 卡片渲染. 支持流式追加 (appendMarkdown) 与节流重渲.
"""

import re
from typing import List, Tuple

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QFont, QFontMetrics, QTextCursor, QTextDocument,
)
from PySide6.QtWidgets import (
    QFrame, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget,
)

from ....common.font import FontManager
from ....common.style_sheet import FluentStyleSheet, isDarkTheme
from ._md_inline_code import InlineCodeRenderMixin
from ._md_table import TableRenderMixin
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

# inline code 与 fenced code 场景使用的等宽字体栈 + CJK fallback.
# - 首位是 FontManager 内嵌的 JBMaple (含 6500 规范汉字), 保证 inline code
#   里的 Latin 和常用 CJK 都用同一字体, 不会仅 Latin 部分跳字体.
# - 其余是系统 Latin 等宽回退 (Cascadia / JBMono / Consolas, 均无 CJK).
# - 末尾跟系统 CJK (YaHei UI / PingFang SC / Noto Sans CJK SC), 覆盖
#   JBMaple 没收录的生僻字, 避免方块豆腐.
# 注: 正文 (非 code) **不**走这个栈 — 走系统默认 (Segoe UI / YaHei UI),
# 跟 chat 气泡 / 工具栏 等其他 UI 元素文本跟一致的比例字形.
def _codeFontStack() -> List[str]:
    return FontManager.code_font_families() + [
        "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC",
    ]


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

class _TextBlock(InlineCodeRenderMixin, TableRenderMixin, QTextBrowser):
    """高度自适应的 markdown 文本段.

    背景透明、无边框、不出滚动条, 高度跟随文档内容自动伸缩.

    字体策略: 正文走系统默认字体 (Segoe UI / YaHei UI), 跟 chat 气泡 /
    工具栏 等其他 UI 元素一致 (可读性优于"代码编辑器感"). inline code /
    fenced code 路径 在 ``_upgradeInlineCodeFont`` 里单独切到 ``_codeFontStack()``
    (内嵌 JBMaple 等宽) 以达到 "代码区块等宽" 的视觉区分.

    具体 inline code / 表格视觉细节由 mixin 实现:

    * :class:`_md_inline_code.InlineCodeRenderMixin` -- ``_injectInlineCodeSpacing``
      / ``createMimeDataFromSelection`` / ``_upgradeInlineCodeFont`` /
      ``_paintInlineCodeBackgrounds`` 与相关常量 (``_PILL_*``,
      ``_INLINE_CODE_FONT_PX``)
    * :class:`_md_table.TableRenderMixin` -- ``_styleTables`` /
      ``_tableRectInViewport`` / ``_paintTableHeaderBackgrounds`` /
      ``_paintTableBorders`` 与相关常量 (``_TABLE_*``)
    """

    # 正文字号: Fluent bodyLarge (16px)
    _BODY_FONT_PX = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        # **先初始化所有实例状态**, 再调 setFont / setSizePolicy 等.
        # 后者会触发 FontChange / StyleChange 事件, ``changeEvent`` 里要访
        # 问 ``self._markdownSource``, 实例属性必须先就位.
        #
        # 行内代码字符位置缓存; 在 paintEvent 阶段通过 cursorRect 计算
        # 视觉矩形并画带圆角的"药丸"背景
        self._inlineCodeRanges: List[Tuple[int, int]] = []
        # 缓存最近一次 ``setMarkdown`` 的原始 markdown 源文 (未注入 thin space).
        # 主题切换 / 字体变化 (``changeEvent``) 时用它重渲, 避开 Qt
        # ``toMarkdown()`` 的 lossy 往返: 当正文字体是等宽 (JBMaple) 时,
        # toMarkdown 看到 fontFixedPitch=True 的 fragment 会把整段用反引号
        # 包成 inline code, 下一次 setMarkdown 时整段正文被识别为
        # inline code, 被罩上胶囊背景.
        self._markdownSource: str = ""
        # 缓存 widget 字体的 ``QFontMetrics`` 供 ``_paintInlineCodeBackgrounds``
        # 使用, 避免在 paint 热路径上每帧重建. 字体变化时 ``changeEvent``
        # 会刷新这份缓存.
        self._fontMetrics: "QFontMetrics | None" = None

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setOpenExternalLinks(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 横向 Preferred (按 sizeHint 显示, 受父级 maxWidth 限制),
        # 而非 Expanding (会强行吃满父容器, 与 user 气泡按内容收缩冲突)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # 正文只设字号不设 family — 让 family 走 widget 默认 (继承父层 /
        # QApplication.font(), 在 Fluent 应用里默认 = qconfig.fontFamilies =
        # ['Segoe UI', 'Microsoft YaHei', 'PingFang SC']). 不走 ``_codeFontStack``
        # (代码字体栈) 让正文中文以比例字形渲染, 不要代码块那种等宽方块感.
        #
        # ``setHintingPreference(PreferNoHinting)``: 让 Windows ClearType 完全
        # 接管渲染, 跳过 Qt 自己的 hinting 逻辑 — 这是 Chrome / Edge 默
        # 认渲染中文的路径, 视觉上最柔顺、与浏览器一致. 代价: 笔画起
        # 点位置可能跳动 1px (Qt grid fitting 不介入, 笔画位置是浮点精度).
        # 之前试过 ``PreferFullHinting`` (锁死像素但中文反者糊) 和
        # ``PreferVerticalHinting`` (中道方案) 都不够清晰; ``NoHinting`` 是
        # 最接近浏览器质感的选择.
        # 不显式设 styleStrategy: 让 DirectWrite 默认启用 ClearType. 之前
        # ``PreferAntialias`` 会强制走灰阶 AA 关掉 ClearType 子像素 RGB,
        # 视觉反而退化, 不要加回去.
        body_font = QFont()
        body_font.setPixelSize(self._BODY_FONT_PX)
        body_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self.setFont(body_font)
        self.document().setDefaultFont(body_font)
        self.document().setDocumentMargin(0)
        self._fontMetrics = QFontMetrics(body_font)
        self._applyDocStyleSheet()
        # 注意: 不连 document().contentsChanged.
        # setMarkdown(text) 内部会先清空再插入, 中间会触发若干次 contentsChanged,
        # 每次都跑 _adjustHeight + updateGeometry 会让高度在 [4, target] 之间反复
        # 跳变, 父 layout 跟着抖动. 高度更新统一由 setMarkdown / resizeEvent 控制.

    def _applyDocStyleSheet(self):
        """给 QTextDocument 设置 inline code / 链接的颜色样式

        QTextDocument 仅支持 CSS2 子集:
        * ``code { font-size / font-family }``  **不响应** — 字号 / 字体只能
          走 ``_upgradeInlineCodeFont`` 通过 QTextCharFormat.setFont 写到
          char format
        * ``code { background-color }``  响应但做不出圆角 — 由 ``paintEvent``
          自己画带圆角的"药丸"代替

        所以这里只管 ``color``.
        """
        if isDarkTheme():
            inline_color = "#ff9580"   # 柔和珊瑚, 与暗色正文区分但不刺眼
            link_color = "#7cc2ff"
        else:
            inline_color = "#a4365c"   # 比 Bootstrap 老粉柔和, 接近 GitHub catppuccin
            link_color = "#0067c0"
        css = f"""
            code {{ color: {inline_color}; }}
            a {{ color: {link_color}; text-decoration: none; }}
            pre, pre code {{ background: transparent; }}
        """
        self.document().setDefaultStyleSheet(css)

    def setMarkdown(self, text: str):
        # MarkdownDialectGitHub 在 Qt6 中支持表格、删除线、任务列表等.
        # 屏蔽 document 信号: setMarkdown 内部 (清空 + 插入) 会触发多次
        # contentsChanged / undoCommandAdded, 不屏蔽会引起短暂 layout 抖动.
        #
        # 注意: 曾尝试过 "新文本 = 旧源 + 纯文本 tail 时走 QTextCursor.insertText"
        # 的增量快通道, 以为能跳过 GFM parse 提速. 实测 (5000 字符, 1000 次
        # 追加) 反而慢 50%: QTextCursor.insertText 会写 undo stack + 触发
        # per-character layout 重排, 开销不比 Qt C++ markdown parser 小; 而
        # parser 对无语法纯文本非常快 (~2ms / 5000 字). streaming 节流是
        # 33ms/次, 单次 setMarkdown < 3ms 用户无感. 故不做.
        self._markdownSource = text or ""
        text = self._injectInlineCodeSpacing(self._markdownSource)
        doc = self.document()
        was_blocked = doc.blockSignals(True)
        try:
            doc.setMarkdown(
                text, QTextDocument.MarkdownFeature.MarkdownDialectGitHub
            )
            # P2b: inline code 识别 + 字体升级 + 表格样式都走 mixin
            self._inlineCodeRanges = self._upgradeInlineCodeFont(
                _codeFontStack(),
            )
            self._styleTables()
            self._normalizeBlockSpacing()
        finally:
            doc.blockSignals(was_blocked)
        self._adjustHeight()
        self.updateGeometry()  # 通知父 layout 重新计算 sizeHint
        self.viewport().update()

    # --- block 间距 (统一 _TextBlock 内部 markdown block 间距, 与外层
    # QVBoxLayout setSpacing 节奏接近, 避免出现 "代码块周围间距大 / 段落
    # 列表表格挤一起" 的视觉割裂感) ---
    _BLOCK_TOP_MARGIN = 8       # 段落 / 标题 等普通 block top margin
    _LIST_ITEM_TOP_MARGIN = 2   # 列表项内 / 列表项之间紧凑

    def _normalizeBlockSpacing(self):
        """统一 _TextBlock 内部各 markdown block 间距, 与外层 QVBoxLayout
        ``setSpacing`` 节奏接近.

        Qt markdown importer 给 block 默认 ``topMargin / bottomMargin``
        偏小且不一致 (paragraph ≈ 4px, list-item ≈ 0, heading 较大),
        与 ``MarkdownView._layout.setSpacing(10)`` 的外层节奏不一致 —
        视觉上 "代码块周围间距大 / 段落 ↔ 列表 ↔ 表格 之间挤一起",
        节奏割裂.

        策略:
        - 第一个 block: ``topMargin = 0`` 避免顶部空白, 让 _TextBlock
          紧贴上方 widget (由外层 QVBoxLayout spacing 提供间距)
        - 列表项 (``block.textList()`` 非 None): ``topMargin = 2`` 保持
          列表内紧凑
        - 其他 (paragraph / heading 等): ``topMargin = 8`` 接近外层 10
          视觉节奏
        - 全部 ``bottomMargin = 0`` 避免上下叠加
        - 跳过 table 内的 block (table 自己 cell padding 控间距)
        """
        doc = self.document()
        cursor = QTextCursor(doc)
        block = doc.firstBlock()
        is_first = True
        while block.isValid():
            # 跳过 table 内的 block — table 由 cellPadding 控制布局,
            # 改 block margin 会破坏 table 内部对齐
            probe = QTextCursor(doc)
            probe.setPosition(block.position())
            if probe.currentTable() is not None:
                is_first = False
                block = block.next()
                continue

            if is_first:
                top = 0
            elif block.textList() is not None:
                top = self._LIST_ITEM_TOP_MARGIN
            else:
                top = self._BLOCK_TOP_MARGIN

            fmt = block.blockFormat()
            if fmt.topMargin() != top or fmt.bottomMargin() != 0:
                fmt.setTopMargin(top)
                fmt.setBottomMargin(0)
                cursor.setPosition(block.position())
                cursor.setBlockFormat(fmt)

            is_first = False
            block = block.next()

    def paintEvent(self, event):
        # paint 顺序 (从下往上叠):
        #   1. inline code 胶囊背景 (super 之前, 让文字在胶囊上)
        #   2. 表格表头浅灰背景 (super 之前, 让文字在背景上, 同时 clip
        #      到外圆角内, 自然贴合圆角)
        #   3. super: Qt 默认渲染文字 + 行分隔线
        #   4. 表格外圆角描边 (super 之后, 覆盖 cell 矩形边沿)
        if self._inlineCodeRanges:
            self._paintInlineCodeBackgrounds()
        self._paintTableHeaderBackgrounds()
        super().paintEvent(event)
        self._paintTableBorders()

    def changeEvent(self, event):
        super().changeEvent(event)
        ev_name = event.type().name
        if ev_name == "FontChange":
            # 字体变了, 刷新 paint 热路径用的 QFontMetrics 缓存
            self._fontMetrics = QFontMetrics(self.font())
        if ev_name in ("StyleChange", "PaletteChange", "FontChange"):
            self._applyDocStyleSheet()
            # 重新解析以应用新 stylesheet + 重新打 inline code 视觉样式.
            # **必须用 ``self._markdownSource`` 而不是 ``toMarkdown()`` 回转**:
            # ``QTextDocument.toMarkdown`` 是 lossy 转换 — 它根据当前 char
            # format 反推 markdown 语法, 任何被 ``_upgradeInlineCodeFont`` 升
            # 级过 family / 设了 fixedPitch 的段都会被它**重新**用反引号包
            # 成 inline code, 累积下来 inline code 段会嵌套, 反引号越打越多.
            # 用缓存的原始源文重渲就完全绕开这个转换, 是稳的.
            if self._markdownSource:
                self.setMarkdown(self._markdownSource)

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

        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

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
