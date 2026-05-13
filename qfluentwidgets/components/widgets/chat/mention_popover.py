# coding: utf-8
"""@ Mention 弹窗 (MentionPopover)

输入 "@" 时浮在输入框上方的候选列表卡片.
跟 SlashCommandPopover 同样的方式: 非 Popup, 作为 layout 内 widget.

设计:
- 宽度由 layout 撑满 (跟输入框等宽)
- paintEvent 自绘圆角卡片背景
- 选中项整行高亮
- 文件名 + 右侧类别标签
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor, QFont, QIcon, QKeyEvent,
    QPainter, QPainterPath, QPen,
)
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget

from ....common.icon import FluentIcon, FluentIconBase
from ....common.style_sheet import isDarkTheme, themeColor


__all__ = ['MentionPopover', 'MentionItem']


@dataclass
class MentionItem:
    """Mention 候选项数据."""
    text: str
    category: str = ""
    icon: Optional[Union[QIcon, FluentIconBase]] = None
    data: Optional[object] = None


class _MentionRow(QWidget):
    """单条 mention 候选项 (自绘)."""

    clicked = Signal(int)

    _HEIGHT = 30

    def __init__(self, item: MentionItem, index: int,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._item = item
        self._index = index
        self._selected = False
        self._hovered = False
        self.setFixedHeight(self._HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def item(self) -> MentionItem:
        return self._item

    def setSelected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._index)
        super().mousePressEvent(event)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        isDark = isDarkTheme()
        w = self.width()
        h = self.height()

        if self._selected:
            bg = QColor(255, 255, 255, 20) if isDark else QColor(0, 120, 212, 15)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(2, 1, w - 4, h - 2), 4, 4)
        elif self._hovered:
            bg = QColor(255, 255, 255, 10) if isDark else QColor(0, 0, 0, 5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(2, 1, w - 4, h - 2), 4, 4)

        # 图标
        iconX = 12
        iconSize = 14
        iconY = (h - iconSize) // 2
        if self._item.icon:
            if isinstance(self._item.icon, FluentIconBase):
                self._item.icon.icon().paint(painter, iconX, iconY, iconSize, iconSize)
            elif isinstance(self._item.icon, QIcon):
                self._item.icon.paint(painter, iconX, iconY, iconSize, iconSize)

        # 文本
        textX = iconX + iconSize + 8
        textColor = QColor(255, 255, 255, 220) if isDark else QColor(0, 0, 0, 190)
        painter.setPen(textColor)
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(textX, 0, w - textX - 60, h, Qt.AlignmentFlag.AlignVCenter, self._item.text)

        # 类别 (右侧弱化)
        if self._item.category:
            catColor = QColor(255, 255, 255, 80) if isDark else QColor(0, 0, 0, 70)
            painter.setPen(catColor)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(w - 56, 0, 48, h,
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                             self._item.category)


class MentionPopover(QFrame):
    """@ Mention 浮动卡片 (非 Popup, layout 内 widget)

    Signals:
        itemSelected(object): 用户选中某个候选项 (MentionItem)

    构造函数:
        MentionPopover(parent: QWidget = None)
    """

    itemSelected = Signal(object)

    _MAX_VISIBLE = 6
    _ITEM_HEIGHT = 30
    _RADIUS = 8.0

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("mentionPopover")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._allItems: List[MentionItem] = []
        self._rows: List[_MentionRow] = []
        self._selectedIdx = 0
        self._targetHeight = 0

        # 展开/收起动画
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve
        self._expandAni = QPropertyAnimation(self, b'maximumHeight', self)
        self._expandAni.setDuration(180)
        self._expandAni.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMaximumHeight(0)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(0)

        self.hide()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setItems(self, items: List[MentionItem]) -> None:
        self._allItems = list(items)

    def addItem(self, item: MentionItem) -> None:
        self._allItems.append(item)

    def clearItems(self) -> None:
        self._allItems.clear()

    def popup(self, filter_text: str = "") -> None:
        """显示弹窗并过滤, 带展开动画."""
        self._rebuild(filter_text)
        if not self._rows:
            self._animateClose()
            return

        count = min(len(self._rows), self._MAX_VISIBLE)
        self._targetHeight = count * self._ITEM_HEIGHT + 12

        if not self.isVisible():
            self.setMaximumHeight(0)
            self.show()

        self._expandAni.stop()
        self._expandAni.setStartValue(self.maximumHeight())
        self._expandAni.setEndValue(self._targetHeight)
        self._expandAni.start()

    def _animateClose(self) -> None:
        if not self.isVisible():
            return
        self._expandAni.stop()
        self._expandAni.setStartValue(self.maximumHeight())
        self._expandAni.setEndValue(0)
        self._expandAni.finished.connect(self._onCloseFinished)
        self._expandAni.start()

    def _onCloseFinished(self) -> None:
        self._expandAni.finished.disconnect(self._onCloseFinished)
        self.hide()
        self.setMaximumHeight(0)

    def filter(self, text: str) -> None:
        self._rebuild(text)
        if not self._rows:
            self._animateClose()

    # ------------------------------------------------------------------
    # 键盘处理
    # ------------------------------------------------------------------

    def handleKeyPress(self, event: QKeyEvent) -> bool:
        if not self.isVisible():
            return False
        key = event.key()
        if key == Qt.Key.Key_Down:
            self._moveSelection(1)
            return True
        elif key == Qt.Key.Key_Up:
            self._moveSelection(-1)
            return True
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self._confirmSelection()
            return True
        elif key == Qt.Key.Key_Escape:
            self._animateClose()
            return True
        return False

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        isDark = isDarkTheme()
        bg = QColor(44, 44, 48, 250) if isDark else QColor(255, 255, 255, 250)
        border = QColor(255, 255, 255, 20) if isDark else QColor(0, 0, 0, 20)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(border, 1.0))
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, self._RADIUS, self._RADIUS)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _rebuild(self, filter_text: str) -> None:
        for row in self._rows:
            self._layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        query = filter_text.lower().lstrip("@")
        for item in self._allItems:
            if query and query not in item.text.lower() and query not in item.category.lower():
                continue
            row = _MentionRow(item, len(self._rows), self)
            row.clicked.connect(self._onRowClicked)
            self._layout.addWidget(row)
            self._rows.append(row)

        self._selectedIdx = 0
        self._updateSelection()

    def _moveSelection(self, delta: int) -> None:
        if not self._rows:
            return
        self._selectedIdx = (self._selectedIdx + delta) % len(self._rows)
        self._updateSelection()

    def _updateSelection(self) -> None:
        for i, row in enumerate(self._rows):
            row.setSelected(i == self._selectedIdx)

    def _confirmSelection(self) -> None:
        if 0 <= self._selectedIdx < len(self._rows):
            item = self._rows[self._selectedIdx].item()
            self.itemSelected.emit(item)
        self._animateClose()

    def _onRowClicked(self, index: int) -> None:
        if 0 <= index < len(self._rows):
            item = self._rows[index].item()
            self.itemSelected.emit(item)
        self._animateClose()
