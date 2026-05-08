# coding: utf-8
"""代码块卡片组件

独立卡片化展示 markdown 中的 fenced code block, 顶部显示语言名 + 复制按钮,
下方为只读代码区. 若已安装 pygments, 自动按语言进行语法高亮; 未安装时
降级为仅等宽字体的纯文本.
"""

from typing import Dict, Optional

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QClipboard, QColor, QFont, QFontDatabase, QFontMetrics,
    QGuiApplication, QPainter, QPainterPath, QPen, QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon, FluentIconBase
from ....common.style_sheet import FluentStyleSheet, isDarkTheme
from ..button import TransparentToolButton
from ..icon_widget import IconWidget
from ..label import BodyLabel


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

    优先级: Cascadia Code > JetBrains Mono > Consolas > Courier New > 系统默认等宽.
    """
    families = QFontDatabase.families()
    for name in ("Cascadia Code", "JetBrains Mono", "Consolas", "Courier New"):
        if name in families:
            f = QFont(name, size)
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

    _COPY_FEEDBACK_MS = 1200
    _MAX_VISIBLE_LINES = 24
    _MIN_WIDTH = 560

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

        self._setupUi()
        self._setupHighlighter()
        FluentStyleSheet.CHAT_VIEW.apply(self)
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
        self._languageLabel.setFont(_monospace_font(12))

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
        self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._editor.setFont(_monospace_font(13))
        self._editor.setTabStopDistance(QFontMetrics(self._editor.font()).horizontalAdvance(' ') * 4)
        self._editor.setContentsMargins(14, 10, 14, 10)
        self._editor.setStyleSheet("QPlainTextEdit { padding: 10px 14px; }")
        self._editor.textChanged.connect(self._adjustHeight)

        self._mainLayout.addWidget(self._header)
        self._mainLayout.addWidget(self._editor)

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
        """根据内容行数自适应代码区高度"""
        doc = self._editor.document()
        line_count = max(1, doc.blockCount())
        line_count = min(line_count, self._MAX_VISIBLE_LINES)
        line_height = QFontMetrics(self._editor.font()).lineSpacing()
        # 上下 padding 共 20, 边框/滚动条留 6
        height = line_height * line_count + 26
        self._editor.setFixedHeight(int(height))

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
