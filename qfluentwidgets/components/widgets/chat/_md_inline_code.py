# coding: utf-8
"""Inline code 胶囊渲染 mixin.

把 ``markdown_view._TextBlock`` 中"识别 inline code 段 + 替换字体 + 注入
间距 + 复制时清理 thin space + paint 圆角药丸背景"这一组逻辑抽到独立的
mixin, 让 ``_TextBlock`` 主类不再混杂 ~155 行 inline code 视觉细节.

依赖 (consumer 类必须提供, ``QTextBrowser`` 子类天然满足):
    self.document() -> QTextDocument
    self.viewport() -> QWidget
    self.cursorRect(cursor) -> QRect
    self.font() -> QFont
    self._fontMetrics: QFontMetrics 缓存 (consumer 在 init / changeEvent
        里维护)
    self._inlineCodeRanges: List[Tuple[int, int]]  (mixin 写, paint 读)

类级常量 ``_PILL_*`` / ``_INLINE_CODE_FONT_PX`` 由 mixin 自带, 子类可覆盖.
"""

import re
from typing import List, Tuple

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QTextCharFormat, QTextCursor,
)

from ....common.style_sheet import isDarkTheme


# ----------------------------------------------------------------------
# 模块级常量与正则
# ----------------------------------------------------------------------

# 单反引号包裹的 inline code (跨行 ` 不算)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+?)`")

# inline code 两侧注入的实体空格 (U+2009 THIN SPACE, ~3px).
# Qt QTextDocument 不支持 inline padding/margin, paintEvent 也只能画背景
# 推不动字符. 唯一能让 inline code 与相邻字之间有真实布局间距的手段就是
# 注入字符. 复制时由 ``_InlineCodeRenderMixin.createMimeDataFromSelection``
# 把它们剥除, 用户拿到干净文本.
_INLINE_CODE_SPACE = "\u2009"

# Qt markdown importer 给 inline code 段设的 fontFamilies 占位白名单.
# 精确匹配 (字面量, 不做子串) 跨平台稳定:
#   Linux / offscreen     -> ['monospace']
#   Windows (DirectWrite) -> ['Courier New']
#   macOS   (CoreText)    -> ['Courier']
# 不要改用 fontFixedPitch: 当正文是等宽字体, 该属性会传染整段被误判.
_INLINE_CODE_MARKER_FAMILIES = frozenset(
    {"monospace", "courier", "courier new"}
)


__all__ = ['InlineCodeRenderMixin', 'INLINE_CODE_SPACE']

INLINE_CODE_SPACE = _INLINE_CODE_SPACE  # public alias for callers


class InlineCodeRenderMixin:
    """混入 ``QTextBrowser`` 子类的 inline code 视觉处理.

    使用方法::

        class _TextBlock(InlineCodeRenderMixin, QTextBrowser):
            def setMarkdown(self, text):
                # 1. 注入 thin space
                doc_text = self._injectInlineCodeSpacing(text)
                self.document().setMarkdown(doc_text, ...)
                # 2. 升级 inline code 字体, 收集 ranges
                self._inlineCodeRanges = self._upgradeInlineCodeFont(
                    code_font_families=...
                )
                ...

            def paintEvent(self, e):
                if self._inlineCodeRanges:
                    self._paintInlineCodeBackgrounds()
                super().paintEvent(e)
    """

    # 视觉参数 (子类可覆盖)
    _INLINE_CODE_FONT_PX = 12
    _PILL_PAD_X = 4
    _PILL_RADIUS = 6
    _PILL_EXTRA_H = 0
    _PILL_OPTICAL_DY = 1

    # 子类应在 __init__ 早期赋值
    _inlineCodeRanges: List[Tuple[int, int]]
    _fontMetrics: "QFontMetrics | None"

    # ------------------------------------------------------------------
    # 文本预处理 + 复制时清理
    # ------------------------------------------------------------------

    @staticmethod
    def _injectInlineCodeSpacing(text: str) -> str:
        """在 inline code 两侧注入 THIN SPACE 作为实体布局间距.

        仅处理单反引号 inline code; fenced code 已在外层 ``MarkdownView``
        切走, 不会走到这里.
        """
        if not text or "`" not in text:
            return text
        return _INLINE_CODE_RE.sub(
            lambda m: f"{_INLINE_CODE_SPACE}`{m.group(1)}`{_INLINE_CODE_SPACE}",
            text,
        )

    def createMimeDataFromSelection(self):  # type: ignore[override]
        """复制选区时去掉视觉用 thin space, text/plain 与 text/html 都处理."""
        mime = super().createMimeDataFromSelection()  # type: ignore[misc]
        if mime is None:
            return mime
        if mime.hasText():
            mime.setText(mime.text().replace(_INLINE_CODE_SPACE, ""))
        if mime.hasHtml():
            mime.setHtml(mime.html().replace(_INLINE_CODE_SPACE, ""))
        return mime

    # ------------------------------------------------------------------
    # 解析 doc 的 char format 找 inline code 段, 替换字体并收集 ranges
    # ------------------------------------------------------------------

    def _upgradeInlineCodeFont(
        self, code_font_families: List[str],
    ) -> List[Tuple[int, int]]:
        """识别所有 inline code 字段, 把字体替换成 ``code_font_families`` +
        小字号, 同时返回所有片段的 (start, end) 列表给 paint 用.

        识别条件: ``QTextCharFormat.fontFamilies()`` 命中
        ``_INLINE_CODE_MARKER_FAMILIES`` 任一. 字体替换走
        ``QTextCharFormat.setFont(font, FontPropertiesSpecifiedOnly)``,
        只覆盖 family + pixelSize 两项.

        Args:
            code_font_families: inline code 应使用的字体栈 (内嵌 + 系统
                CJK fallback). consumer 决定 (避免 mixin 与 FontManager
                耦合).

        Returns:
            inline code 片段的 (start_position, end_position) 列表.
        """
        code_font = QFont()
        code_font.setFamilies(code_font_families)
        code_font.setPixelSize(self._INLINE_CODE_FONT_PX)
        code_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting,
        )
        try:
            inherit = QTextCharFormat.FontPropertiesInheritanceBehavior.FontPropertiesSpecifiedOnly
        except AttributeError:
            # 老 PySide6 未提供 enum 全路径
            inherit = QTextCharFormat.FontPropertiesSpecifiedOnly

        ranges: List[Tuple[int, int]] = []
        doc = self.document()
        cursor = QTextCursor(doc)
        block = doc.firstBlock()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    families = frag.charFormat().fontFamilies() or []
                    if isinstance(families, str):
                        families = [families]
                    lowered = {str(f).strip().lower() for f in families}
                    if lowered & _INLINE_CODE_MARKER_FAMILIES:
                        start = frag.position()
                        end = start + frag.length()
                        ranges.append((start, end))
                        new_fmt = QTextCharFormat()
                        new_fmt.setFont(code_font, inherit)
                        cursor.setPosition(start)
                        cursor.setPosition(
                            end, QTextCursor.MoveMode.KeepAnchor,
                        )
                        cursor.mergeCharFormat(new_fmt)
                it += 1
            block = block.next()
        return ranges

    # ------------------------------------------------------------------
    # paint: 圆角药丸背景
    # ------------------------------------------------------------------

    def _paintInlineCodeBackgrounds(self) -> None:
        """画 inline code 圆角药丸背景. 必须在 ``super().paintEvent`` **之前**
        调, 这样 Qt 默认渲染文字时就画在我们的背景上面.
        """
        # 颜色参考 GitHub: 浅灰半透 / 中灰半透
        if isDarkTheme():
            bg = QColor(110, 118, 129, 102)   # rgba(110,118,129,0.4)
        else:
            bg = QColor(175, 184, 193, 56)    # rgba(175,184,193,0.22)
        painter = QPainter(self.viewport())
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)

            # 胶囊高度 = 字身高 (ascent + descent) + EXTRA_H
            # 胶囊中心 = 字身中点 (不是行中点, 后者含 leading 多行间距时偏)
            fm = self._fontMetrics or QFontMetrics(self.font())
            char_h = fm.ascent() + fm.descent()
            pill_h = char_h + self._PILL_EXTRA_H
            pad_x = self._PILL_PAD_X
            radius = self._PILL_RADIUS
            optical_dy = self._PILL_OPTICAL_DY

            doc = self.document()
            for start, end in self._inlineCodeRanges:
                if end <= start:
                    continue
                cs = QTextCursor(doc)
                cs.setPosition(start)
                ce = QTextCursor(doc)
                ce.setPosition(end)
                rs = self.cursorRect(cs)
                re_ = self.cursorRect(ce)
                cy = rs.top() + char_h // 2 + optical_dy

                if rs.top() == re_.top():
                    # 单行: 一个圆角药丸
                    rect = QRect(
                        rs.left() - pad_x,
                        cy - pill_h // 2,
                        (re_.right() - rs.left()) + pad_x * 2,
                        pill_h,
                    )
                    painter.drawRoundedRect(rect, radius, radius)
                else:
                    # 跨行: 拆成首尾两段药丸 (中间整行情况极少)
                    vp_w = self.viewport().width()
                    first = QRect(
                        rs.left() - pad_x,
                        cy - pill_h // 2,
                        vp_w - rs.left() - pad_x,
                        pill_h,
                    )
                    painter.drawRoundedRect(first, radius, radius)
                    cy2 = re_.top() + re_.height() // 2 + optical_dy
                    last = QRect(
                        0,
                        cy2 - pill_h // 2,
                        re_.right() + pad_x,
                        pill_h,
                    )
                    painter.drawRoundedRect(last, radius, radius)
        finally:
            painter.end()
