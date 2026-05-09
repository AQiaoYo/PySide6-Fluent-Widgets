# coding: utf-8
"""工具调用特化渲染器 + 注册表

把 ``ToolCallSegment`` 渲染成针对具体工具语义优化的卡片. 注册表机制允许
宿主在运行时为自定义工具名注入渲染器.

内置渲染器 (chat 子包导入时自动注册):

- ``read_file`` / ``read``                          -> ``FileReadCard``
- ``write_file`` / ``write``                        -> ``FileWriteCard``
- ``edit_file`` / ``edit`` / ``str_replace_based_edit_tool`` -> ``FileEditCard``
- ``bash`` / ``run_command`` / ``shell``            -> ``BashCard``
- ``web_search`` / ``search_web``                   -> ``WebSearchCard``
- ``grep_search`` / ``grep`` / ``rg``               -> ``GrepSearchCard``

未匹配的工具名 fallback 到 ``GenericToolCallCard``.

每个特化渲染器都按 ``ToolCallSegment.metadata`` 中的字段做容错降级, 缺失
任何字段都不会崩, 而是退化到 GenericToolCallCard 风格 (参数 + 结果).
"""

import os
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QUrl

from ....common.icon import FluentIcon
from ....common.style_sheet import FluentStyleSheet
from ..icon_widget import IconWidget
from ..label import BodyLabel, CaptionLabel, StrongBodyLabel
from .chat_message import ToolCallSegment, ToolCallStatus
from .code_block import CodeBlock
from .diff_view import DiffView
from .markdown_view import MarkdownView
from .tool_call_card import GenericToolCallCard, ToolCallCardBase


__all__ = [
    'ToolCardFactory',
    'registerToolRenderer', 'unregisterToolRenderer',
    'resolveToolRenderer', 'registeredToolNames',
    'FileReadCard', 'FileWriteCard', 'FileEditCard',
    'BashCard', 'WebSearchCard', 'GrepSearchCard',
]


# ----------------------------------------------------------------------
# 注册表
# ----------------------------------------------------------------------

ToolCardFactory = Callable[[Optional[QWidget]], ToolCallCardBase]

_RENDERERS: Dict[str, ToolCardFactory] = {}


def registerToolRenderer(tool_name: str, factory: ToolCardFactory) -> None:
    """注册一个工具名 -> 卡片工厂.

    Args:
        tool_name: 工具名 (大小写敏感).
        factory:   接受 ``parent: Optional[QWidget]`` 返回 ``ToolCallCardBase``
                   实例的可调用 (通常就是子类本身).

    覆盖已存在的同名注册.
    """
    if not tool_name:
        return
    _RENDERERS[tool_name] = factory


def unregisterToolRenderer(tool_name: str) -> None:
    """注销一个工具名 (无则忽略)."""
    _RENDERERS.pop(tool_name, None)


def resolveToolRenderer(tool_name: str) -> ToolCardFactory:
    """返回匹配的工厂; 未注册时 fallback 到 ``GenericToolCallCard``."""
    if tool_name and tool_name in _RENDERERS:
        return _RENDERERS[tool_name]
    return GenericToolCallCard


def registeredToolNames() -> List[str]:
    """返回当前所有已注册的工具名 (按字母序)."""
    return sorted(_RENDERERS.keys())


# ----------------------------------------------------------------------
# 内部工具
# ----------------------------------------------------------------------

_LANG_BY_EXT = {
    "py": "python", "pyi": "python",
    "js": "javascript", "jsx": "javascript",
    "mjs": "javascript", "cjs": "javascript",
    "ts": "typescript", "tsx": "typescript",
    "rb": "ruby", "rs": "rust", "go": "go",
    "java": "java", "kt": "kotlin", "swift": "swift",
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "hpp": "cpp", "hh": "cpp",
    "cs": "csharp",
    "md": "markdown", "markdown": "markdown",
    "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml",
    "html": "html", "htm": "html", "css": "css", "scss": "scss",
    "sh": "bash", "bash": "bash", "zsh": "bash",
    "ps1": "powershell", "psm1": "powershell",
    "sql": "sql", "xml": "xml", "ini": "ini", "cfg": "ini",
    "qss": "css", "ui": "xml", "qrc": "xml",
}


def _guess_language(path: Optional[str], explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    if not path:
        return "text"
    _, ext = os.path.splitext(path)
    if not ext:
        return "text"
    return _LANG_BY_EXT.get(ext.lstrip(".").lower(), "text")


def _short(text: str, n: int) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


# ----------------------------------------------------------------------
# FileReadCard
# ----------------------------------------------------------------------

class FileReadCard(ToolCallCardBase):
    """``read_file`` 工具卡片.

    Header 形如 ``[doc] read_file <path>``. 展开内容显示行范围 + 文件内容
    CodeBlock (语言由 ``metadata.language`` 或文件后缀推断).

    支持 metadata 字段:
        path:            文件路径 (用于 header 和语言推断)
        start_line:      起始行号 (1-based, 显示用)
        end_line:        结束行号
        language:        显式语言名 (覆盖按后缀推断)
        preview_content: 优先用这个文本作为代码块内容 (否则用 segment.result)
    """

    def _displayIcon(self, segment):
        return FluentIcon.DOCUMENT

    def _displayName(self, segment):
        if segment is None:
            return self.tr("read_file")
        path = (segment.metadata or {}).get("path")
        name = segment.tool_name or "read_file"
        return f"{name}  {path}" if path else name

    def _buildContent(self, parent):
        self._rangeLabel = CaptionLabel("", parent)
        self._rangeLabel.setObjectName("lineRangeLabel")
        self._rangeLabel.hide()

        self._codeBlock = CodeBlock("", "text", parent)

        self._contentLayout.addWidget(self._rangeLabel)
        self._contentLayout.addWidget(self._codeBlock)

    def _onSegmentChanged(self, seg):
        if seg is None:
            self._rangeLabel.hide()
            self._codeBlock.setCode("")
            return

        meta = seg.metadata or {}
        path = meta.get("path")
        start = meta.get("start_line")
        end = meta.get("end_line")

        if start is not None and end is not None:
            self._rangeLabel.setText(self.tr("行 {0} .. {1}").format(start, end))
            self._rangeLabel.show()
        elif start is not None:
            self._rangeLabel.setText(self.tr("行 {0} 起").format(start))
            self._rangeLabel.show()
        else:
            self._rangeLabel.hide()

        lang = _guess_language(path, meta.get("language"))
        if self._codeBlock.language() != lang:
            self._codeBlock.setLanguage(lang)

        text = meta.get("preview_content")
        if text is None:
            text = seg.result or ""
        if self._codeBlock._code != text:
            self._codeBlock.setCode(text)

    def appendResultDelta(self, delta):
        if not delta:
            return
        super().appendResultDelta(delta)
        if self._segment is not None:
            meta = self._segment.metadata or {}
            # 仅当没有 preview_content 时才把 result 同步到 codeblock
            if meta.get("preview_content") is None:
                self._codeBlock.setCode(self._segment.result)

    def setCodeBlockMaxVisibleLines(self, n):
        super().setCodeBlockMaxVisibleLines(n)
        self._codeBlock.setMaxVisibleLines(n)


# ----------------------------------------------------------------------
# FileWriteCard
# ----------------------------------------------------------------------

class FileWriteCard(ToolCallCardBase):
    """``write_file`` 工具卡片.

    Header 形如 ``write_file <path>``. 展开内容显示完整新内容代码块.

    支持 metadata 字段:
        path:     文件路径
        language: 显式语言名 (默认按后缀推断)
        content:  优先使用这个文本作为代码块内容 (否则 segment.result)
    """

    def _displayIcon(self, segment):
        return FluentIcon.SAVE

    def _displayName(self, segment):
        if segment is None:
            return self.tr("write_file")
        path = (segment.metadata or {}).get("path")
        name = segment.tool_name or "write_file"
        return f"{name}  {path}" if path else name

    def _buildContent(self, parent):
        self._codeBlock = CodeBlock("", "text", parent)
        self._contentLayout.addWidget(self._codeBlock)

    def _onSegmentChanged(self, seg):
        if seg is None:
            self._codeBlock.setCode("")
            return

        meta = seg.metadata or {}
        lang = _guess_language(meta.get("path"), meta.get("language"))
        if self._codeBlock.language() != lang:
            self._codeBlock.setLanguage(lang)

        text = meta.get("content")
        if text is None:
            text = seg.result or seg.arguments or ""
        if self._codeBlock._code != text:
            self._codeBlock.setCode(text)

    def appendResultDelta(self, delta):
        if not delta:
            return
        super().appendResultDelta(delta)
        if self._segment is not None:
            meta = self._segment.metadata or {}
            if meta.get("content") is None:
                self._codeBlock.setCode(self._segment.result)

    def setCodeBlockMaxVisibleLines(self, n):
        super().setCodeBlockMaxVisibleLines(n)
        self._codeBlock.setMaxVisibleLines(n)


# ----------------------------------------------------------------------
# FileEditCard
# ----------------------------------------------------------------------

class FileEditCard(ToolCallCardBase):
    """``edit_file`` / ``str_replace_based_edit_tool`` 工具卡片.

    Header 形如 ``edit_file <path>``. 展开内容渲染行级 diff (红 = 删除,
    绿 = 新增).

    支持 metadata 字段:
        path:          文件路径
        old:           编辑前文本 (与 new 配套使用 -> ndiff)
        new:           编辑后文本
        unified_diff:  unified_diff 文本 (优先于 old/new); 直接渲染
    """

    def _displayIcon(self, segment):
        return FluentIcon.EDIT

    def _displayName(self, segment):
        if segment is None:
            return self.tr("edit_file")
        path = (segment.metadata or {}).get("path")
        name = segment.tool_name or "edit_file"
        return f"{name}  {path}" if path else name

    def _buildContent(self, parent):
        self._diff = DiffView(parent)
        self._fallbackLabel = CaptionLabel(
            self.tr("(没有 diff 数据, 显示原始结果)"), parent,
        )
        self._fallbackLabel.setObjectName("toolCallSectionLabel")
        self._fallbackLabel.hide()
        self._fallbackView = MarkdownView("", parent)
        self._fallbackView.hide()

        self._contentLayout.addWidget(self._diff)
        self._contentLayout.addWidget(self._fallbackLabel)
        self._contentLayout.addWidget(self._fallbackView)

    def _onSegmentChanged(self, seg):
        if seg is None:
            self._diff.clear()
            self._fallbackView.setMarkdown("")
            self._fallbackLabel.hide()
            self._fallbackView.hide()
            self._diff.show()
            return

        meta = seg.metadata or {}
        unified = meta.get("unified_diff")
        old = meta.get("old")
        new = meta.get("new")

        if unified:
            self._diff.setUnifiedDiff(unified)
            self._diff.show()
            self._fallbackLabel.hide()
            self._fallbackView.hide()
        elif old is not None or new is not None:
            self._diff.setOldNew(old or "", new or "")
            self._diff.show()
            self._fallbackLabel.hide()
            self._fallbackView.hide()
        else:
            # 没 diff 数据, 退化到 markdown 展示 result
            self._diff.clear()
            self._diff.hide()
            self._fallbackLabel.show()
            self._fallbackView.show()
            self._fallbackView.setMarkdown(seg.result or "")

    def appendResultDelta(self, delta):
        if not delta:
            return
        super().appendResultDelta(delta)
        # diff 数据通常一次性给, 流式 result 走 fallback
        meta = (self._segment.metadata or {}) if self._segment else {}
        if not meta.get("unified_diff") and meta.get("old") is None and meta.get("new") is None:
            self._fallbackView.appendMarkdown(delta)

    def setCodeBlockMaxVisibleLines(self, n):
        super().setCodeBlockMaxVisibleLines(n)
        self._fallbackView.setCodeBlockMaxVisibleLines(n)


# ----------------------------------------------------------------------
# BashCard
# ----------------------------------------------------------------------

class _BashOutputView(QFrame):
    """终端样式输出区: 输出文本 + 右下角退出码徽章, 都在同一个圆角框内.

    布局策略: 用 QVBoxLayout 把 [输出文本] + [stretch] + [徽章行] 三段从上
    到下排列, 让徽章 row 自动靠在底部. 旧版用 ``move()`` 浮动定位会被
    layout 系统覆盖, 出现徽章跑到 (0,0) 与文本重叠 (用户在 issue #1 中观察
    到的现象).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("bashOutputView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self._label = QLabel("", self)
        self._label.setObjectName("bashOutputText")
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )
        self._label.setWordWrap(True)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        layout.addWidget(self._label, 0)

        # 徽章行: stretch + badge, 让徽章靠右. row 本身在 layout 末尾,
        # setSizePolicy(Maximum) 时会贴在 frame 内容底部.
        self._badgeRow = QWidget(self)
        self._badgeRow.setObjectName("bashBadgeRow")
        badgeLayout = QHBoxLayout(self._badgeRow)
        badgeLayout.setContentsMargins(0, 0, 0, 0)
        badgeLayout.setSpacing(0)
        badgeLayout.addStretch(1)

        self._exitBadge = CaptionLabel("", self._badgeRow)
        self._exitBadge.setObjectName("bashExitBadge")
        self._exitBadge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        badgeLayout.addWidget(self._exitBadge)

        # 默认隐藏整个 row (徽章 + 行), 这样无 exit_code 的 segment 不会
        # 留下一条空白行.
        self._badgeRow.hide()
        layout.addWidget(self._badgeRow, 0)

    def setText(self, text: str) -> None:
        self._label.setText(text or "")

    def appendText(self, delta: str) -> None:
        if not delta:
            return
        self._label.setText((self._label.text() or "") + delta)

    def setExitCode(self, code: Optional[int]) -> None:
        """设置退出码并显示右下角徽章. ``None`` 隐藏徽章行."""
        if code is None:
            self._badgeRow.hide()
            return
        ok = code == 0
        self._exitBadge.setText(self.tr("退出码 {0}").format(code))
        self._exitBadge.setProperty("ok", "true" if ok else "false")
        # 触发 QSS 属性选择器重新匹配
        self._exitBadge.style().unpolish(self._exitBadge)
        self._exitBadge.style().polish(self._exitBadge)
        self._badgeRow.show()


class BashCard(ToolCallCardBase):
    """``bash`` / ``run_command`` 工具卡片.

    Header 形如 ``$ <短命令>``. 展开内容显示终端样式输出 + 末尾退出码徽章.

    支持 metadata 字段:
        command:    命令字符串 (优先于 segment.arguments 用作 header 标题)
        exit_code:  退出码 (int, 0 -> 绿色徽章, 非 0 -> 红色徽章)
    """

    def _displayIcon(self, segment):
        return FluentIcon.COMMAND_PROMPT

    def _displayName(self, segment):
        if segment is None:
            return self.tr("bash")
        meta = segment.metadata or {}
        cmd = meta.get("command") or segment.arguments or ""
        cmd_short = _short(cmd, 80)
        if cmd_short:
            return f"$ {cmd_short}"
        return segment.tool_name or "bash"

    def _buildContent(self, parent):
        # 终端框: 单一 _BashOutputView, 退出码徽章直接浮在它的右下 (不再
        # 单独占一行). 视觉上像一个真终端窗口的状态条.
        self._output = _BashOutputView(parent)
        self._contentLayout.addWidget(self._output)

    def _onSegmentChanged(self, seg):
        if seg is None:
            self._output.setText("")
            self._output.setExitCode(None)
            return

        self._output.setText(seg.result or "")
        meta = seg.metadata or {}
        if "exit_code" in meta:
            ec = meta.get("exit_code")
            try:
                ec_int = int(ec)
            except (TypeError, ValueError):
                ec_int = -1
            self._output.setExitCode(ec_int)
        else:
            self._output.setExitCode(None)

    def appendResultDelta(self, delta):
        if not delta:
            return
        super().appendResultDelta(delta)
        self._output.appendText(delta)


# ----------------------------------------------------------------------
# WebSearchCard
# ----------------------------------------------------------------------

class _ResultRow(QFrame):
    """单条 web 搜索结果行: 标题 (粗) + URL (灰) + 摘要 (BodyLabel).

    标题点击发出 ``clicked()`` 信号 (上层连到 QDesktopServices.openUrl).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("webResultRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._titleLabel = StrongBodyLabel("", self)
        self._titleLabel.setObjectName("webResultTitle")
        self._titleLabel.setTextFormat(Qt.TextFormat.PlainText)
        self._titleLabel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._titleLabel.setWordWrap(True)

        self._urlLabel = CaptionLabel("", self)
        self._urlLabel.setObjectName("webResultUrl")
        self._urlLabel.setTextFormat(Qt.TextFormat.PlainText)
        self._urlLabel.setWordWrap(True)

        self._snippetLabel = BodyLabel("", self)
        self._snippetLabel.setObjectName("webResultSnippet")
        self._snippetLabel.setTextFormat(Qt.TextFormat.PlainText)
        self._snippetLabel.setWordWrap(True)

        layout.addWidget(self._titleLabel)
        layout.addWidget(self._urlLabel)
        layout.addWidget(self._snippetLabel)

        self._url: str = ""

    def setData(self, title: str, url: str, snippet: str) -> None:
        self._titleLabel.setText(title or self.tr("(无标题)"))
        self._urlLabel.setText(url or "")
        self._urlLabel.setVisible(bool(url))
        self._snippetLabel.setText(snippet or "")
        self._snippetLabel.setVisible(bool(snippet))
        self._url = url or ""

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._url:
            QDesktopServices.openUrl(QUrl(self._url))
        super().mousePressEvent(e)


class WebSearchCard(ToolCallCardBase):
    """``web_search`` / ``search_web`` 工具卡片.

    Header 形如 ``web_search "<query>"``. 展开内容显示结果列表 (每条:
    标题 + URL + 摘要).

    支持 metadata 字段:
        query:    搜索查询 (优先于 segment.arguments 解析)
        results:  ``List[Dict[str, str]]``, 每项必须含 ``title`` / ``url``,
                  可选 ``snippet``. 缺失时 fallback 到 GenericToolCallCard.
    """

    def _displayIcon(self, segment):
        return FluentIcon.SEARCH

    def _displayName(self, segment):
        if segment is None:
            return self.tr("web_search")
        meta = segment.metadata or {}
        query = meta.get("query") or ""
        if not query:
            # 尝试从 arguments 解析 JSON {query: "..."}
            query = self._tryParseQuery(segment.arguments)
        name = segment.tool_name or "web_search"
        if query:
            return f'{name}  "{_short(query, 60)}"'
        return name

    @staticmethod
    def _tryParseQuery(arguments: str) -> str:
        if not arguments:
            return ""
        import json
        try:
            obj = json.loads(arguments)
            if isinstance(obj, dict):
                return str(obj.get("query") or obj.get("q") or "")
        except (ValueError, TypeError):
            pass
        return ""

    def _buildContent(self, parent):
        self._listWrap = QFrame(parent)
        self._listWrap.setObjectName("webResultList")
        self._listWrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._listLayout = QVBoxLayout(self._listWrap)
        self._listLayout.setContentsMargins(0, 0, 0, 0)
        self._listLayout.setSpacing(10)

        self._emptyLabel = CaptionLabel(self.tr("(没有结果数据)"), parent)
        self._emptyLabel.setObjectName("toolCallSectionLabel")
        self._emptyLabel.hide()

        self._contentLayout.addWidget(self._listWrap)
        self._contentLayout.addWidget(self._emptyLabel)

        self._rows: List[_ResultRow] = []

    def _onSegmentChanged(self, seg):
        # 清空已有 rows
        for r in self._rows:
            self._listLayout.removeWidget(r)
            r.setParent(None)
            r.deleteLater()
        self._rows.clear()

        if seg is None:
            self._emptyLabel.show()
            self._listWrap.hide()
            return

        meta = seg.metadata or {}
        results = meta.get("results")
        if not isinstance(results, list) or not results:
            self._emptyLabel.show()
            self._listWrap.hide()
            return

        self._emptyLabel.hide()
        self._listWrap.show()
        for item in results:
            if not isinstance(item, dict):
                continue
            row = _ResultRow(self._listWrap)
            row.setData(
                title=str(item.get("title") or ""),
                url=str(item.get("url") or ""),
                snippet=str(item.get("snippet") or ""),
            )
            self._listLayout.addWidget(row)
            self._rows.append(row)


# ----------------------------------------------------------------------
# GrepSearchCard
# ----------------------------------------------------------------------

class _GrepHitRow(QFrame):
    """单条 grep 命中行: 一张带 1px 边框的小卡片, 含 [icon path:line] 头部
    + 命中行预览正文 (等宽), 视觉上一条命中 = 一张独立卡片, 而不是 path /
    preview 两块脱节的内容.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("grepHitRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(3)

        # 头部: [文件图标] [path:line]
        headerRow = QHBoxLayout()
        headerRow.setContentsMargins(0, 0, 0, 0)
        headerRow.setSpacing(6)

        self._fileIcon = IconWidget(FluentIcon.DOCUMENT, self)
        self._fileIcon.setFixedSize(12, 12)

        self._pathLabel = CaptionLabel("", self)
        self._pathLabel.setObjectName("grepHitPath")
        self._pathLabel.setTextFormat(Qt.TextFormat.PlainText)
        self._pathLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )

        headerRow.addWidget(self._fileIcon, 0, Qt.AlignmentFlag.AlignVCenter)
        headerRow.addWidget(self._pathLabel, 1, Qt.AlignmentFlag.AlignVCenter)

        # 正文: 命中行预览
        self._previewLabel = QLabel("", self)
        self._previewLabel.setObjectName("grepHitPreview")
        self._previewLabel.setTextFormat(Qt.TextFormat.PlainText)
        self._previewLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )
        self._previewLabel.setWordWrap(False)

        layout.addLayout(headerRow)
        layout.addWidget(self._previewLabel)

    def setData(self, path: str, line: int, preview: str) -> None:
        self._pathLabel.setText(f"{path}:{line}" if line else (path or ""))
        self._previewLabel.setText(preview or "")


class GrepSearchCard(ToolCallCardBase):
    """``grep_search`` / ``rg`` 工具卡片.

    Header 形如 ``grep "<query>"``. 展开内容显示命中列表
    (每条: ``path:line`` + 命中行预览).

    支持 metadata 字段:
        query:  搜索关键词 (优先于 arguments 解析)
        hits:   ``List[Dict[str, Any]]``, 每项含 ``path``,
                可选 ``line`` (int) 与 ``preview`` (str).
    """

    def _displayIcon(self, segment):
        return FluentIcon.SEARCH

    def _displayName(self, segment):
        if segment is None:
            return self.tr("grep_search")
        meta = segment.metadata or {}
        query = meta.get("query") or ""
        if not query:
            query = WebSearchCard._tryParseQuery(segment.arguments)
        name = segment.tool_name or "grep_search"
        if query:
            return f'{name}  "{_short(query, 60)}"'
        return name

    def _buildContent(self, parent):
        self._listWrap = QFrame(parent)
        self._listWrap.setObjectName("grepHitList")
        self._listWrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._listLayout = QVBoxLayout(self._listWrap)
        self._listLayout.setContentsMargins(0, 0, 0, 0)
        self._listLayout.setSpacing(6)

        self._emptyLabel = CaptionLabel(self.tr("(没有命中数据)"), parent)
        self._emptyLabel.setObjectName("toolCallSectionLabel")
        self._emptyLabel.hide()

        self._summaryLabel = CaptionLabel("", parent)
        self._summaryLabel.setObjectName("toolCallSectionLabel")
        self._summaryLabel.hide()

        self._contentLayout.addWidget(self._summaryLabel)
        self._contentLayout.addWidget(self._listWrap)
        self._contentLayout.addWidget(self._emptyLabel)

        self._rows: List[_GrepHitRow] = []

    def _onSegmentChanged(self, seg):
        for r in self._rows:
            self._listLayout.removeWidget(r)
            r.setParent(None)
            r.deleteLater()
        self._rows.clear()

        if seg is None:
            self._emptyLabel.show()
            self._listWrap.hide()
            self._summaryLabel.hide()
            return

        meta = seg.metadata or {}
        hits = meta.get("hits")
        if not isinstance(hits, list) or not hits:
            self._emptyLabel.show()
            self._listWrap.hide()
            self._summaryLabel.hide()
            return

        self._emptyLabel.hide()
        self._listWrap.show()
        self._summaryLabel.setText(
            self.tr("命中 {0} 条").format(len(hits))
        )
        self._summaryLabel.show()
        for item in hits:
            if not isinstance(item, dict):
                continue
            row = _GrepHitRow(self._listWrap)
            try:
                ln = int(item.get("line")) if item.get("line") is not None else 0
            except (TypeError, ValueError):
                ln = 0
            row.setData(
                path=str(item.get("path") or ""),
                line=ln,
                preview=str(item.get("preview") or ""),
            )
            self._listLayout.addWidget(row)
            self._rows.append(row)


# ----------------------------------------------------------------------
# 默认注册
# ----------------------------------------------------------------------

def _register_default_renderers() -> None:
    defaults: Dict[str, ToolCardFactory] = {
        "read_file": FileReadCard,
        "read": FileReadCard,
        "write_file": FileWriteCard,
        "write": FileWriteCard,
        "edit_file": FileEditCard,
        "edit": FileEditCard,
        "str_replace_based_edit_tool": FileEditCard,
        "bash": BashCard,
        "run_command": BashCard,
        "shell": BashCard,
        "web_search": WebSearchCard,
        "search_web": WebSearchCard,
        "grep_search": GrepSearchCard,
        "grep": GrepSearchCard,
        "rg": GrepSearchCard,
    }
    for name, factory in defaults.items():
        registerToolRenderer(name, factory)


_register_default_renderers()
