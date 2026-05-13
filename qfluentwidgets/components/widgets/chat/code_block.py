# coding: utf-8
"""代码块卡片组件

独立卡片化展示 markdown 中的 fenced code block, 顶部显示语言名 + 复制按钮,
下方为只读代码区. 若已安装 pygments, 自动按语言进行语法高亮; 未安装时
降级为仅等宽字体的纯文本.
"""

from typing import Dict, Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, QTimer,
    Signal,
)
from PySide6.QtGui import (
    QClipboard, QColor, QFont, QFontDatabase, QFontMetrics,
    QGuiApplication, QPainter, QPainterPath, QPen, QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ....common.font import FontManager
from ....common.icon import FluentIcon, FluentIconBase
from ....common.style_sheet import FluentStyleSheet, isDarkTheme
from ..button import TransparentToolButton
from ..icon_widget import IconWidget
from ..label import BodyLabel
from ..scroll_bar import SmoothScrollDelegate
from ._collapse_anim import (
    animations_enabled_root, begin_layout_animation, end_layout_animation,
)


__all__ = ['CodeBlock']


# ----------------------------------------------------------------------
# pygments 可选依赖检测
# ----------------------------------------------------------------------

try:  # pragma: no cover - 依赖检测
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token
    from pygments.util import ClassNotFound
    _PYGMENTS_OK = True
except Exception:  # pragma: no cover - 缺失时优雅降级
    _PYGMENTS_OK = False


# ----------------------------------------------------------------------
# 等宽字体探测
# ----------------------------------------------------------------------

def _monospace_font(size: int = 13) -> QFont:
    """按优先级返回可用的等宽字体.

    优先级: FontManager 内嵌字体 > Cascadia Code > JetBrains Mono > Consolas > Courier New > 系统默认等宽.
    """
    code_families = FontManager.code_font_families()
    if code_families:
        f = QFont(code_families[0], size)
        f.setFamilies(code_families)
        f.setStyleHint(QFont.StyleHint.Monospace)
        return f
    f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    f.setPointSize(size)
    return f


# ----------------------------------------------------------------------
# pygments 高亮器
# ----------------------------------------------------------------------

class _PygmentsHighlighter(QSyntaxHighlighter):
    """基于 pygments lex 的 Qt 语法高亮器

    仅在 pygments 可用时生效. 颜色映射根据当前主题在 light / dark 两套色板
    之间切换, 切换主题时调用 ``setDark(True/False)`` + ``rehighlight()`` 即可.
    """

    LIGHT_COLORS: Dict[str, str] = {
        "keyword":    "#d73a49",
        "name.class": "#6f42c1",
        "name.function": "#6f42c1",
        "name.builtin": "#005cc5",
        "name.decorator": "#6f42c1",
        "string":     "#22863a",
        "number":     "#005cc5",
        "comment":    "#6a737d",
        "operator":   "#d73a49",
        "punctuation": "#24292e",
        "text":       "#24292e",
        "literal":    "#005cc5",
        "error":      "#b31d28",
    }

    DARK_COLORS: Dict[str, str] = {
        "keyword":    "#ff7b72",
        "name.class": "#d2a8ff",
        "name.function": "#d2a8ff",
        "name.builtin": "#79c0ff",
        "name.decorator": "#d2a8ff",
        "string":     "#a5d6ff",
        "number":     "#79c0ff",
        "comment":    "#8b949e",
        "operator":   "#ff7b72",
        "punctuation": "#c9d1d9",
        "text":       "#c9d1d9",
        "literal":    "#79c0ff",
        "error":      "#ffa198",
    }

    def __init__(self, document, language: str, dark: bool):
        super().__init__(document)
        self._dark = dark
        self._lexer = self._resolveLexer(language)

    @staticmethod
    def _resolveLexer(language: str):
        if not _PYGMENTS_OK:
            return None
        lang = (language or "").strip().lower()
        if not lang or lang in ("plaintext", "text", "txt"):
            return None
        try:
            return get_lexer_by_name(lang, stripnl=False, stripall=False, ensurenl=False)
        except ClassNotFound:
            return None

    def setDark(self, dark: bool):
        if self._dark != dark:
            self._dark = dark
            self.rehighlight()

    def setLanguage(self, language: str):
        self._lexer = self._resolveLexer(language)
        self.rehighlight()

    # pygments 的 token 类型可与字符串前缀比较, 我们做最长前缀匹配
    def _formatFor(self, token_type) -> Optional[QTextCharFormat]:
        if not _PYGMENTS_OK:
            return None
        palette = self.DARK_COLORS if self._dark else self.LIGHT_COLORS
        # 自上而下尝试 token 在层级中的所有父类型, 取最贴合的颜色
        for tt in token_type.split():
            key = str(tt)
            if key.startswith("Token."):
                key = key[len("Token."):]
            key = key.lower()
            if key in palette:
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(palette[key]))
                if "comment" in key:
                    fmt.setFontItalic(True)
                return fmt
        return None

    def highlightBlock(self, text: str):
        if self._lexer is None or not text:
            return
        try:
            tokens = list(self._lexer.get_tokens_unprocessed(text))
        except Exception:
            return
        for index, ttype, value in tokens:
            if not value:
                continue
            fmt = self._formatFor(ttype)
            if fmt is not None:
                self.setFormat(index, len(value), fmt)


# ----------------------------------------------------------------------
# CodeBlock 主体
# ----------------------------------------------------------------------

class CodeBlock(QFrame):
    """代码块卡片

    顶部条显示语言名和复制按钮, 下方为只读代码区. 若已安装 pygments,
    则自动按语言进行语法高亮; 未安装时降级为仅等宽字体的纯文本展示.

    Attributes:
        copied: 复制完成时发出, 参数为已复制的纯代码文本

    构造函数重载:
        * CodeBlock(parent: QWidget = None)
        * CodeBlock(code: str, language: str = "", parent: QWidget = None)
    """

    copied = Signal(str)
    expandedChanged = Signal(bool)
    # 展开动画 finish 后发出, 请求宿主 (AgentChatView 等) 滚到 self.header 顶部
    requestScrollIntoView = Signal(QWidget)

    _COPY_FEEDBACK_MS = 1200
    _DEFAULT_MAX_VISIBLE_LINES = 5
    _MIN_WIDTH = 560
    # 展开 / 折叠动画时长
    _EXPAND_ANIM_MS = 220

    # 语言名 -> FluentIcon 映射. 未命中时 fallback 到 CODE.
    _LANGUAGE_ICONS = {
        # shell 类
        "powershell": FluentIcon.COMMAND_PROMPT,
        "pwsh":       FluentIcon.COMMAND_PROMPT,
        "ps1":        FluentIcon.COMMAND_PROMPT,
        "bash":       FluentIcon.COMMAND_PROMPT,
        "sh":         FluentIcon.COMMAND_PROMPT,
        "shell":      FluentIcon.COMMAND_PROMPT,
        "zsh":        FluentIcon.COMMAND_PROMPT,
        "fish":       FluentIcon.COMMAND_PROMPT,
        "cmd":        FluentIcon.COMMAND_PROMPT,
        "bat":        FluentIcon.COMMAND_PROMPT,
        "console":    FluentIcon.COMMAND_PROMPT,
        # 配置 / 数据
        "json":       FluentIcon.DOCUMENT,
        "yaml":       FluentIcon.DOCUMENT,
        "yml":        FluentIcon.DOCUMENT,
        "toml":       FluentIcon.DOCUMENT,
        "ini":        FluentIcon.DOCUMENT,
        "xml":        FluentIcon.DOCUMENT,
        "markdown":   FluentIcon.DOCUMENT,
        "md":         FluentIcon.DOCUMENT,
        "plaintext":  FluentIcon.DOCUMENT,
        "text":       FluentIcon.DOCUMENT,
        "txt":        FluentIcon.DOCUMENT,
        # web
        "html":       FluentIcon.GLOBE,
        "vue":        FluentIcon.GLOBE,
        "svelte":     FluentIcon.GLOBE,
        # 样式 / 工具
        "css":        FluentIcon.DEVELOPER_TOOLS,
        "scss":       FluentIcon.DEVELOPER_TOOLS,
        "less":       FluentIcon.DEVELOPER_TOOLS,
        "sql":        FluentIcon.DEVELOPER_TOOLS,
        "graphql":    FluentIcon.DEVELOPER_TOOLS,
        "regex":      FluentIcon.DEVELOPER_TOOLS,
        # docker / embed
        "dockerfile": FluentIcon.EMBED,
        "docker":     FluentIcon.EMBED,
    }

    @classmethod
    def _iconForLanguage(cls, language: str) -> FluentIconBase:
        """根据语言名返回对应的 FluentIcon, 未命中时 fallback 到 CODE."""
        key = (language or "").strip().lower()
        return cls._LANGUAGE_ICONS.get(key, FluentIcon.CODE)

    def __init__(self, code: str = "", language: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._code = code
        self._language = language or "plaintext"
        # 代码区最大可见行数; 实际行数超过此值时:
        #   - 折叠态: 高度卡在 maxLines 行 + 垂直滚动条 + 底部展开按钮
        #   - 展开态: 全部代码可见 + 底部折叠按钮
        # 实际行数 ≤ maxLines: 完全展开, 无滚动条, 无展开按钮.
        self._maxVisibleLines = self._DEFAULT_MAX_VISIBLE_LINES
        self._expanded = False  # 展开按钮的状态
        # 展开 / 折叠动画状态
        self._expandAnim: Optional[QPropertyAnimation] = None
        self._expandAnimEnabled: bool = True
        # layout 动画会席 (动画期间 ancestor view 冻结 viewport 贴底)
        self._layoutAnimHost: Optional[QWidget] = None

        self._setupUi()
        self._setupHighlighter()
        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)
        self._applyCode()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _setupUi(self):
        self.setObjectName("codeBlock")
        # 卡片背景由 paintEvent 直接绘制 (避免 QSS 选择器在嵌套场景失效).
        # 不再需要 WA_StyledBackground; QFrame 默认 NoFrame.
        # 给一个最小宽度, 防止父级用 Maximum sizePolicy 时被收缩到 QTextEdit 默认 256
        self.setMinimumWidth(self._MIN_WIDTH)

        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._mainLayout.setSpacing(0)

        # 顶部条
        self._header = QWidget(self)
        self._header.setObjectName("codeHeader")
        self._header.setFixedHeight(34)
        headerLayout = QHBoxLayout(self._header)
        headerLayout.setContentsMargins(10, 0, 6, 0)
        headerLayout.setSpacing(8)

        # 左侧: 语言图标 + 语言名
        self._languageIcon = IconWidget(self._iconForLanguage(self._language), self._header)
        self._languageIcon.setFixedSize(16, 16)

        self._languageLabel = BodyLabel(self._language, self._header)
        self._languageLabel.setObjectName("codeLanguage")
        # 语言名: 等宽 12pt, 不加粗 (粗细由 QSS 控制)
        self._languageLabel.setFont(_monospace_font(11))

        # 右侧: 工具按钮组 (换行切换 + 复制)
        self._wrapButton = TransparentToolButton(FluentIcon.ALIGNMENT, self._header)
        self._wrapButton.setFixedSize(24, 24)
        self._wrapButton.setIconSize(QSize(14, 14))
        self._wrapButton.setToolTip(self.tr("切换自动换行"))
        self._wrapButton.setCheckable(True)
        self._wrapButton.toggled.connect(self._onWrapToggled)

        self._copyButton = TransparentToolButton(FluentIcon.COPY, self._header)
        self._copyButton.setFixedSize(24, 24)
        self._copyButton.setIconSize(QSize(14, 14))
        self._copyButton.setToolTip(self.tr("复制代码"))
        self._copyButton.clicked.connect(self._onCopyClicked)

        headerLayout.addWidget(self._languageIcon, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._languageLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addStretch(1)
        headerLayout.addWidget(self._wrapButton, 0, Qt.AlignmentFlag.AlignVCenter)
        headerLayout.addWidget(self._copyButton, 0, Qt.AlignmentFlag.AlignVCenter)

        # 代码区
        self._editor = QPlainTextEdit(self)
        self._editor.setReadOnly(True)
        self._editor.setFrameShape(QFrame.Shape.NoFrame)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._editor.setFont(_monospace_font(12))
        self._editor.setTabStopDistance(QFontMetrics(self._editor.font()).horizontalAdvance(' ') * 4)
        self._editor.setContentsMargins(14, 10, 14, 10)
        self._editor.setStyleSheet("QPlainTextEdit { padding: 10px 14px; }")
        self._editor.textChanged.connect(self._adjustHeight)

        # 用 fluent 风格 SmoothScrollBar 替换原生 QScrollBar (圆角、半透明、
        # hover 动画), 保持与组件库整体设计语言一致.
        # 注意: SmoothScrollDelegate 会 monkey-patch
        # _editor.setHorizontalScrollBarPolicy / setVerticalScrollBarPolicy,
        # 因此 policy 设定必须放在 delegate 创建之后, 否则不会同步到
        # SmoothScrollBar 的 forceHidden 状态.
        self._scrollDelegate = SmoothScrollDelegate(self._editor)
        # SmoothScrollBar 默认在 hover 时 fadeIn 显示一个偏白的 groove + 两端
        # 箭头按钮, 这套样式针对纯色背景的 QScrollArea 设计, 出现在 CodeBlock
        # 浅灰卡片背景上会显得突兀. 这里:
        # 1) 把 groove 背景色改透明 -> hover 时也不会出现白底
        # 2) 隐藏 upButton / downButton -> 只保留 3px handle 细线
        # 这样既保留了 fluent 风格滚动 (handle 可见 + smooth 动画), 又跟
        # CodeBlock 卡片融为一体.
        for sb in (self._scrollDelegate.hScrollBar, self._scrollDelegate.vScrollBar):
            sb.groove.setLightBackgroundColor(QColor(0, 0, 0, 0))
            sb.groove.setDarkBackgroundColor(QColor(255, 255, 255, 0))
            sb.groove.upButton.hide()
            sb.groove.downButton.hide()
        self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 垂直滚动条: 行数 ≤ maxVisibleLines 时由 _adjustHeight 关闭,
        # 超过时由 _adjustHeight 切回 AsNeeded.
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 底部展开/折叠行 (溢出时才显示)
        self._expandRow = QWidget(self)
        self._expandRow.setObjectName("codeExpandRow")
        exLayout = QHBoxLayout(self._expandRow)
        exLayout.setContentsMargins(0, 0, 0, 4)
        exLayout.setSpacing(0)

        self._expandButton = TransparentToolButton(
            FluentIcon.CHEVRON_DOWN_MED, self._expandRow,
        )
        self._expandButton.setObjectName("codeExpandButton")
        self._expandButton.setFixedSize(72, 24)
        self._expandButton.setIconSize(QSize(14, 14))
        self._expandButton.setToolTip(self.tr("展开"))
        self._expandButton.clicked.connect(self.toggleExpanded)

        exLayout.addStretch(1)
        exLayout.addWidget(self._expandButton)
        exLayout.addStretch(1)
        self._expandRow.hide()

        self._mainLayout.addWidget(self._header)
        self._mainLayout.addWidget(self._editor)
        self._mainLayout.addWidget(self._expandRow)

        self._copyResetTimer = QTimer(self)
        self._copyResetTimer.setSingleShot(True)
        self._copyResetTimer.timeout.connect(self._resetCopyIcon)

    def _setupHighlighter(self):
        self._highlighter = _PygmentsHighlighter(
            self._editor.document(), self._language, isDarkTheme()
        ) if _PYGMENTS_OK else None

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setCode(self, code: str, language: Optional[str] = None):
        """设置代码内容

        Args:
            code:     代码原文
            language: 可选, 切换语言; 留空则保持当前语言
        """
        self._code = code
        if language is not None:
            self.setLanguage(language)
        else:
            self._applyCode()

    def code(self) -> str:
        """获取代码原文"""
        return self._code

    def setLanguage(self, language: str):
        """设置语言名 (同时刷新左侧图标、标签和高亮器)"""
        self._language = language or "plaintext"
        self._languageLabel.setText(self._language)
        self._languageIcon.setIcon(self._iconForLanguage(self._language))
        if self._highlighter is not None:
            self._highlighter.setLanguage(self._language)
        self._applyCode()

    def language(self) -> str:
        """获取当前语言名"""
        return self._language

    # ------------------------------------------------------------------
    # 内部行为
    # ------------------------------------------------------------------

    def _applyCode(self):
        self._editor.setPlainText(self._code)
        if self._highlighter is not None:
            self._highlighter.rehighlight()
        self._adjustHeight()

    def _adjustHeight(self):
        """根据内容行数 + 展开状态自适应代码区高度, 同步底部按钮显隐.

        三种情况:

        - 实际行数 ≤ ``maxVisibleLines`` (不溢出): 按实际行数铺开,
          关闭垂直滚动条, 底部按钮隐藏.
        - 实际行数 > ``maxVisibleLines``  (溢出, 折叠态): 高度卡在
          maxVisibleLines 行, 垂直滚动条 AsNeeded, 底部显示 ↓ 展开按钮.
        - 实际行数 > ``maxVisibleLines``  (溢出, 展开态): 全部代码铺开,
          关闭垂直滚动条, 底部显示 ↑ 折叠按钮.

        高度算式考虑了横向滚动条占用 (lineWrapMode=NoWrap 时长行可能触发):
        预留 hscrollbar.sizeHint().height() 避免挤压垂直空间产生意外滚动.
        """
        doc = self._editor.document()
        actual_lines = max(1, doc.blockCount())
        max_lines = max(1, self._maxVisibleLines)
        overflow = actual_lines > max_lines

        if not overflow:
            visible_lines = actual_lines
        elif self._expanded:
            visible_lines = actual_lines
        else:
            visible_lines = max_lines

        line_height = QFontMetrics(self._editor.font()).lineSpacing()
        # 上下 padding 共 20 (qss padding: 10px 14px)
        height = line_height * visible_lines + 20
        # 不换行时长行会触发横向滚动条, 预留其高度避免内容被挤压
        if self._editor.lineWrapMode() == QPlainTextEdit.LineWrapMode.NoWrap:
            height += self._editor.horizontalScrollBar().sizeHint().height()
        self._editor.setFixedHeight(int(height))

        # 垂直滚动条: 仅折叠态溢出时启用
        if overflow and not self._expanded:
            new_v = Qt.ScrollBarPolicy.ScrollBarAsNeeded
        else:
            new_v = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        if self._editor.verticalScrollBarPolicy() != new_v:
            self._editor.setVerticalScrollBarPolicy(new_v)

        # 底部按钮显隐 + 图标方向
        self._expandRow.setVisible(overflow)
        if overflow:
            icon = FluentIcon.UP if self._expanded else FluentIcon.CHEVRON_DOWN_MED
            self._expandButton.setIcon(icon)
            self._expandButton.setToolTip(
                self.tr("折叠") if self._expanded else self.tr("展开")
            )

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def maxVisibleLines(self) -> int:
        """获取代码区最大可见行数. 默认 5."""
        return self._maxVisibleLines

    def setMaxVisibleLines(self, n: int):
        """设置代码区最大可见行数.

        Args:
            n: 最大可见行数 (≥ 1). 实际行数 > n 时:
               - 折叠态: 高度卡在 n 行, 垂直滚动条 + 底部展开按钮
               - 展开态: 全部代码铺开, 底部折叠按钮
               实际行数 ≤ n: 完全展开, 无滚动条, 无按钮.
        """
        n = max(1, int(n))
        if n == self._maxVisibleLines:
            return
        self._maxVisibleLines = n
        self._adjustHeight()

    def isExpanded(self) -> bool:
        """是否处于展开态 (仅在溢出时有意义)."""
        return self._expanded

    def setExpanded(self, expanded: bool):
        """显式设置展开 / 折叠状态.

        实际行数未溢出 (≤ maxVisibleLines) 时此方法仍会更新内部状态,
        但视觉上不会出现展开按钮. 状态变化时发出 ``expandedChanged``.

        动画路径 (当 ``_expandAnimEnabled`` + view 级总开关均 True 时):
            editor.height 从当前值插值到目标 (220ms OutCubic).
            展开动画 finish 后 emit ``requestScrollIntoView(self)``,
            宿主 (AgentChatView) 接不接由其决定.
        瞬时路径: 合起重走 ``_adjustHeight`` (与原行为一致).
        """
        expanded = bool(expanded)
        if expanded == self._expanded:
            return
        self._expanded = expanded

        if not self._shouldAnimateExpand():
            self._adjustHeight()
            self.expandedChanged.emit(expanded)
            return

        # 走动画路径.
        # 1. 先计算目标 editor 高度 + 刷新除高度外的副作用 (滚动条
        #    policy / 底部按钮显隐 / chevron 图标).
        target_h = self._refreshLayoutNonHeight()
        start_h = self._editor.height()

        # 2. 取消上一轮动画 (避免堆叠).
        if (self._expandAnim is not None
                and self._expandAnim.state() == QPropertyAnimation.State.Running):
            self._expandAnim.stop()
            # 如果上一轮动画还拿着 layout 动画会席 (host), 先释放避免泄漏.
            if self._layoutAnimHost is not None:
                end_layout_animation(self._layoutAnimHost)
                self._layoutAnimHost = None

        # 3. 获取 layout 动画会席 —— 动画期间 ancestor view 会冻结 viewport 瞬间
        # 贴底, 避免每帧 setValue(maximum) 引起视觉抖动.
        self._layoutAnimHost = begin_layout_animation(self)

        anim = QPropertyAnimation(self, b"editorHeight", self)
        anim.setDuration(self._EXPAND_ANIM_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(int(start_h))
        anim.setEndValue(int(target_h))
        # 两个方向都需要在 finished 时释放 layout 会席. 展开额外调 emit
        # 信号 + ancestor 滚到 widget header.
        anim.finished.connect(self._onExpandAnimFinishedAll)
        self._expandAnim = anim
        anim.start()
        self.expandedChanged.emit(expanded)

    def _onExpandAnimFinishedAll(self) -> None:
        """动画结束统一入口: 释放 layout 会席, 再走展开后锁的默认滚动.

        顺序重要: 先调 ``end_layout_animation`` 让 view 计数器归 0 并 schedule
        ``_catchUpToBottomIfNeeded``; 然后调 ``_onExpandAnimFinished`` 启动滚
        到 widget header 的动画. catch-up 在 schedule 的 timer 里检查
        ``_programmaticScroll == True`` 会跳过, 不会取消本卡启动的 widget
        header 滚动.
        """
        end_layout_animation(self._layoutAnimHost)
        self._layoutAnimHost = None
        if self._expanded:
            self._onExpandAnimFinished()

    def _onExpandAnimFinished(self) -> None:
        """展开动画自然结束: emit 信号 + duck-type 调 ancestor 滚动."""
        # 信号面: 宿主可以 connect ``requestScrollIntoView`` 做自己的定制逻辑.
        self.requestScrollIntoView.emit(self)
        # 默认路径: 沿 parent 链向上找提供 ``_smoothScrollWidgetToTop``
        # 的 ancestor (一般是 AgentChatView), 让其滚到本卡 header 顶部.
        # 找不到就不滚, 保证 demo / 独立使用 CodeBlock 也不会报错.
        w = self.parentWidget()
        while w is not None:
            fn = getattr(w, '_smoothScrollWidgetToTop', None)
            if callable(fn):
                try:
                    fn(self)
                except Exception:
                    # 宿主异常不能破坏动画收尾路径, 静默吞.
                    pass
                return
            w = w.parentWidget()

    def toggleExpanded(self):
        """切换展开 / 折叠. 由底部按钮 click 调用, 也可外部手动调."""
        self.setExpanded(not self._expanded)

    # ------------------------------------------------------------------
    # 动画控制
    # ------------------------------------------------------------------

    def setExpandAnimationEnabled(self, enabled: bool) -> None:
        """设置展开 / 折叠动画是否启用 (默认 ``True``).

        关闭后 ``setExpanded`` / ``toggleExpanded`` 退化为瞬间 setFixedHeight,
        与本期改造前行为等价. 主动调该方法后如果动画正在跑, 会被允许
        跑完 (不中途被打断).
        """
        self._expandAnimEnabled = bool(enabled)

    def expandAnimationEnabled(self) -> bool:
        return self._expandAnimEnabled

    def _shouldAnimateExpand(self) -> bool:
        """综合本卡开关 + 宿主总开关 + visible 状态 决定是否走动画."""
        if not self._expandAnimEnabled:
            return False
        if not self.isVisible():
            return False
        # 沿 parent 链查 view-level 总开关.
        if not animations_enabled_root(self):
            return False
        return True

    def _refreshLayoutNonHeight(self) -> int:
        """刷新除 editor.height 外的副作用, 返回该为 editor 设的目标高度.

        从 ``_adjustHeight`` 抽出, 让动画路径可以在不接手 setFixedHeight
        的前提下, 仅同步 scrollbar policy / expandRow 显隐 / chevron 图标.
        """
        doc = self._editor.document()
        actual_lines = max(1, doc.blockCount())
        max_lines = max(1, self._maxVisibleLines)
        overflow = actual_lines > max_lines

        if not overflow:
            visible_lines = actual_lines
        elif self._expanded:
            visible_lines = actual_lines
        else:
            visible_lines = max_lines

        line_height = QFontMetrics(self._editor.font()).lineSpacing()
        height = line_height * visible_lines + 20
        if self._editor.lineWrapMode() == QPlainTextEdit.LineWrapMode.NoWrap:
            height += self._editor.horizontalScrollBar().sizeHint().height()

        if overflow and not self._expanded:
            new_v = Qt.ScrollBarPolicy.ScrollBarAsNeeded
        else:
            new_v = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        if self._editor.verticalScrollBarPolicy() != new_v:
            self._editor.setVerticalScrollBarPolicy(new_v)

        self._expandRow.setVisible(overflow)
        if overflow:
            icon = FluentIcon.UP if self._expanded else FluentIcon.CHEVRON_DOWN_MED
            self._expandButton.setIcon(icon)
            self._expandButton.setToolTip(
                self.tr("折叠") if self._expanded else self.tr("展开")
            )
        return int(height)

    # 动画驱动的 editor 高度 property: 供 ``QPropertyAnimation`` 调用
    def _getEditorHeight(self) -> int:
        return self._editor.height()

    def _setEditorHeight(self, h: int) -> None:
        self._editor.setFixedHeight(int(h))

    editorHeight = Property(int, _getEditorHeight, _setEditorHeight)

    def _onCopyClicked(self):
        clipboard: QClipboard = QGuiApplication.clipboard()
        clipboard.setText(self._code)
        self._copyButton.setIcon(FluentIcon.ACCEPT)
        self._copyResetTimer.start(self._COPY_FEEDBACK_MS)
        self.copied.emit(self._code)

    def _resetCopyIcon(self):
        self._copyButton.setIcon(FluentIcon.COPY)

    def _onWrapToggled(self, wrap: bool):
        """切换代码区是否自动换行"""
        if wrap:
            self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._adjustHeight()

    # ------------------------------------------------------------------
    # 主题切换
    # ------------------------------------------------------------------

    def changeEvent(self, event):
        super().changeEvent(event)
        # FluentStyleSheet 的主题切换会触发 StyleChange / PaletteChange
        if event.type().name in ("StyleChange", "PaletteChange"):
            if self._highlighter is not None:
                self._highlighter.setDark(isDarkTheme())
            self.update()  # 重绘卡片背景以反映主题色

    # ------------------------------------------------------------------
    # 绘制卡片背景 (不依赖 QSS, 保证亮/暗主题下都有清晰可见的卡片轮廓)
    # ------------------------------------------------------------------

    # 卡片视觉常量
    _CARD_RADIUS = 8
    _BORDER_PX = 1

    def paintEvent(self, event):
        is_dark = isDarkTheme()
        if is_dark:
            bg = QColor(0, 0, 0, 82)              # rgba(0,0,0,0.32)
            border = QColor(255, 255, 255, 26)    # rgba(255,255,255,0.10)
            sep = QColor(255, 255, 255, 15)       # rgba(255,255,255,0.06)
        else:
            bg = QColor(0, 0, 0, 14)              # rgba(0,0,0,0.055)
            border = QColor(0, 0, 0, 33)          # rgba(0,0,0,0.13)
            sep = QColor(0, 0, 0, 15)             # rgba(0,0,0,0.06)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 留 0.5px 给边框 stroke 居中, 防止裁切
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        path = QPainterPath()
        path.addRoundedRect(rect, self._CARD_RADIUS, self._CARD_RADIUS)
        painter.fillPath(path, bg)

        painter.setPen(QPen(border, self._BORDER_PX))
        painter.drawPath(path)

        # header / body 之间的极淡分割线
        if hasattr(self, "_header"):
            y = self._header.geometry().bottom() + 0.5
            painter.setPen(QPen(sep, 1))
            painter.drawLine(int(rect.left() + 1), int(y), int(rect.right() - 1), int(y))

        # 不调 super().paintEvent: 父类 QFrame 默认不画 frame, 子组件自己 paint
