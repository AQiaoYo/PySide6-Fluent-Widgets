# coding: utf-8
"""行级红绿 diff 视图组件

供 ``FileEditCard`` / ``FileWriteCard`` 使用. 渲染规则:

- ``+`` 开头: 新增行 (绿色背景, ``#diffLineAdd``)
- ``-`` 开头: 删除行 (红色背景, ``#diffLineRemove``)
- 其它   : 上下文行 (透明, ``#diffLineContext``)

数据输入两种:

- ``setOldNew(old, new)``: 内部走 ``difflib.ndiff`` 生成行级标记
- ``setUnifiedDiff(text)``: 直接接受 ``unified_diff`` 输出, 解析 ``+`` /
  ``-`` / 上下文行

具体颜色由 QSS 控制, 主题切换时无需重新计算.
"""

import difflib
from typing import Iterable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ....common.style_sheet import FluentStyleSheet


__all__ = ['DiffView']


class DiffView(QFrame):
    """行级红绿 diff 视图.

    构造函数:
        DiffView(parent: QWidget = None)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("diffView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum,
        )

        self._lines: List[QLabel] = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        FluentStyleSheet.AGENT_CHAT_VIEW.apply(self)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setOldNew(self, old: str, new: str) -> None:
        """从 (old, new) 完整文本生成 diff."""
        old_lines = old.splitlines() if old else []
        new_lines = new.splitlines() if new else []
        diff_iter = difflib.ndiff(old_lines, new_lines)
        self._renderNdiff(diff_iter)

    def setUnifiedDiff(self, text: str) -> None:
        """接受 unified_diff 输出 (跳过 ---/+++/@@ 头), 按首字符上色."""
        if not text:
            self._clear()
            return
        self._renderUnified(text.splitlines())

    def setLines(self, lines: Iterable[str]) -> None:
        """直接接受预处理后的行列表 (每行第一字符 ``+`` / ``-`` / 空格).

        高级 API, 一般用 setOldNew / setUnifiedDiff 即可.
        """
        self._renderUnified(list(lines))

    def clear(self) -> None:
        self._clear()

    def lineCount(self) -> int:
        return len(self._lines)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        for lab in self._lines:
            self._layout.removeWidget(lab)
            lab.setParent(None)
            lab.deleteLater()
        self._lines.clear()

    def _renderNdiff(self, line_iter: Iterable[str]) -> None:
        """ndiff 输出格式: ``+ line`` / ``- line`` / ``  line`` / ``? hint``."""
        self._clear()
        for raw in line_iter:
            if not raw:
                continue
            if raw.startswith("? "):
                continue
            head = raw[:2]
            text = raw[2:]
            if head == "+ ":
                obj = "diffLineAdd"
            elif head == "- ":
                obj = "diffLineRemove"
            else:
                obj = "diffLineContext"
            self._appendLine(text, obj)

    def _renderUnified(self, lines: List[str]) -> None:
        """unified diff: 按首字符 ``+`` / ``-`` / 空格分类, 跳过文件头."""
        self._clear()
        for raw in lines:
            if not raw:
                self._appendLine(" ", "diffLineContext")
                continue
            if raw.startswith("---") or raw.startswith("+++"):
                continue
            if raw.startswith("@@"):
                # hunk 头, 弱化展示
                self._appendLine(raw, "diffLineHunk")
                continue
            first = raw[0]
            text = raw[1:]
            if first == "+":
                obj = "diffLineAdd"
            elif first == "-":
                obj = "diffLineRemove"
            elif first == " ":
                obj = "diffLineContext"
            elif first == "\\":
                # "\ No newline at end of file"
                continue
            else:
                obj = "diffLineContext"
                text = raw
            self._appendLine(text, obj)

    def _appendLine(self, text: str, object_name: str) -> None:
        # 空行用一个空格保留行高
        if text == "":
            text = " "
        lab = QLabel(text, self)
        lab.setObjectName(object_name)
        lab.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lab.setTextFormat(Qt.TextFormat.PlainText)
        lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lab.setWordWrap(False)
        self._layout.addWidget(lab)
        self._lines.append(lab)
