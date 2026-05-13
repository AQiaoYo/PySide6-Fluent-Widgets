# coding: utf-8
"""Slash 命令弹窗 (SlashCommandPopover)

输入 "/" 时浮在输入框上方的命令列表卡片. 不是独立 Popup 窗口,
而是作为输入框的 sibling/child 浮动在上方, 跟 chatGenBarCard 同样的方式.

设计:
- 宽度与输入框等宽
- paintEvent 自绘圆角卡片背景 (跟 DockSurface 同风格)
- 选中项整行浅色高亮
- 命令名左对齐 + 描述右对齐
- 通过 parent widget 的 layout 插入, 不用 Popup flag
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


__all__ = ['SlashCommandPopover']


@dataclass
class _SlashCommand:
    """命令数据."""
    command: str
    description: str
    icon: Optional[Union[QIcon, FluentIconBase]] = None


class _CommandItem(QWidget):
    """单条命令项 (自绘)."""

    clicked = Signal(str)

    _HEIGHT = 36

    def __init__(self, cmd: _SlashCommand, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._cmd = cmd
        self._selected = False
        self._hovered = False
        self.setFixedHeight(self._HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def command(self) -> str:
        return self._cmd.command

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
            self.clicked.emit(self._cmd.command)
        super().mousePressEvent(event)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        isDark = isDarkTheme()
        w = self.width()
        h = self.height()

        # 选中/hover 整行背景
        if self._selected:
            bg = QColor(255, 255, 255, 20) if isDark else QColor(0, 120, 212, 15)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(2, 1, w - 4, h - 2), 4, 4)

            # 左侧主题色指示条
            accent = themeColor()
            painter.setBrush(accent)
            painter.drawRoundedRect(QRectF(4, 8, 3, h - 16), 1.5, 1.5)
        elif self._hovered:
            bg = QColor(255, 255, 255, 10) if isDark else QColor(0, 0, 0, 5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(2, 1, w - 4, h - 2), 4, 4)

        # 图标
        iconX = 12
        iconSize = 16
        iconY = (h - iconSize) // 2
        if self._cmd.icon:
            if isinstance(self._cmd.icon, FluentIconBase):
                self._cmd.icon.icon().paint(painter, iconX, iconY, iconSize, iconSize)
            elif isinstance(self._cmd.icon, QIcon):
                self._cmd.icon.paint(painter, iconX, iconY, iconSize, iconSize)

        # 命令名 (左侧, 半粗)
        textX = iconX + iconSize + 8
        cmdColor = QColor(255, 255, 255, 230) if isDark else QColor(0, 0, 0, 200)
        painter.setPen(cmdColor)
        font = painter.font()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(textX, 0, w // 2, h, Qt.AlignmentFlag.AlignVCenter, self._cmd.command)

        # 描述 (右侧, 弱化)
        descColor = QColor(255, 255, 255, 90) if isDark else QColor(0, 0, 0, 80)
        painter.setPen(descColor)
        font.setWeight(QFont.Weight.Normal)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(w // 2, 0, w // 2 - 12, h,
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         self._cmd.description)


class SlashCommandPopover(QFrame):
    """Slash 命令浮动卡片 (非 Popup, 作为 layout 内 widget 浮在输入框上方)

    Signals:
        commandSelected(str): 用户选中某条命令

    构造函数:
        SlashCommandPopover(parent: QWidget = None)
    """

    commandSelected = Signal(str)
    tabCompleted = Signal(str)

    _MAX_VISIBLE = 6
    _ITEM_HEIGHT = 36
    _RADIUS = 8.0

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("slashCommandPopover")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._commands: List[_SlashCommand] = []
        self._filteredItems: List[_CommandItem] = []
        self._selectedIdx = 0
        self._targetHeight = 0

        # 展开/收起动画
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property
        self._expandAni = QPropertyAnimation(self, b'maximumHeight', self)
        self._expandAni.setDuration(180)
        self._expandAni.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMaximumHeight(0)

        # 外层 layout 只放一个 scrollArea
        outerLayout = QVBoxLayout(self)
        outerLayout.setContentsMargins(6, 6, 6, 6)
        outerLayout.setSpacing(0)

        from PySide6.QtWidgets import QScrollArea
        from PySide6.QtGui import QPalette
        self._scrollArea = QScrollArea(self)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 让 scrollArea 和 viewport 背景透明 (不遮挡父级 paintEvent)
        pal = self._scrollArea.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
        self._scrollArea.setPalette(pal)
        self._scrollArea.viewport().setPalette(pal)
        outerLayout.addWidget(self._scrollArea)

        # 内部容器
        self._container = QWidget(self._scrollArea)
        self._container.setPalette(pal)
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scrollArea.setWidget(self._container)

        self.hide()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addCommand(self, command: str, description: str = "",
                   icon: Optional[Union[QIcon, FluentIconBase]] = None) -> None:
        self._commands.append(_SlashCommand(command, description, icon))

    def removeCommand(self, command: str) -> None:
        self._commands = [c for c in self._commands if c.command != command]

    def clearCommands(self) -> None:
        self._commands.clear()

    def popup(self, filter_text: str = "") -> None:
        """显示弹窗并过滤, 带展开动画."""
        self._rebuild(filter_text)
        if not self._filteredItems:
            self._animateClose()
            return

        # 计算目标高度
        count = min(len(self._filteredItems), self._MAX_VISIBLE)
        self._targetHeight = count * self._ITEM_HEIGHT + 12

        if not self.isVisible():
            self.setMaximumHeight(0)
            self.show()

        # 展开动画
        self._expandAni.stop()
        self._expandAni.setStartValue(self.maximumHeight())
        self._expandAni.setEndValue(self._targetHeight)
        self._expandAni.start()

    def _animateClose(self) -> None:
        """收起动画后隐藏."""
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
        """更新过滤 (已显示时调用)."""
        self._rebuild(text)
        if not self._filteredItems:
            self._animateClose()

    # ------------------------------------------------------------------
    # 键盘处理
    # ------------------------------------------------------------------

    def handleKeyPress(self, event: QKeyEvent) -> bool:
        """处理键盘事件. 返回 True 表示已消费.

        支持:
            - Up/Down: 移动选中项
            - Enter: 确认选中 (触发 commandSelected 信号)
            - Tab: 补全选中命令到输入框 (触发 tabCompleted 信号, 不关闭弹窗)
            - Escape: 关闭弹窗
        """
        if not self.isVisible():
            return False
        key = event.key()
        if key == Qt.Key.Key_Down:
            self._moveSelection(1)
            return True
        elif key == Qt.Key.Key_Up:
            self._moveSelection(-1)
            return True
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirmSelection()
            return True
        elif key == Qt.Key.Key_Tab:
            self._tabComplete()
            return True
        elif key == Qt.Key.Key_Escape:
            self._animateClose()
            return True
        return False

    # ------------------------------------------------------------------
    # 绘制 (卡片背景, 跟 DockSurface 同风格)
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
        for item in self._filteredItems:
            self._layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
        self._filteredItems.clear()

        query = filter_text.lower().lstrip("/")
        for cmd in self._commands:
            if query and query not in cmd.command.lower() and query not in cmd.description.lower():
                continue
            item = _CommandItem(cmd, self)
            item.clicked.connect(self._onItemClicked)
            self._layout.addWidget(item)
            self._filteredItems.append(item)

        self._selectedIdx = 0
        self._updateSelection()

    def _moveSelection(self, delta: int) -> None:
        if not self._filteredItems:
            return
        self._selectedIdx = (self._selectedIdx + delta) % len(self._filteredItems)
        self._updateSelection()

    def _updateSelection(self) -> None:
        for i, item in enumerate(self._filteredItems):
            item.setSelected(i == self._selectedIdx)
        # 确保选中项可见
        if 0 <= self._selectedIdx < len(self._filteredItems):
            self._scrollArea.ensureWidgetVisible(
                self._filteredItems[self._selectedIdx], 0, 0
            )

    def _confirmSelection(self) -> None:
        if 0 <= self._selectedIdx < len(self._filteredItems):
            cmd = self._filteredItems[self._selectedIdx].command()
            self.commandSelected.emit(cmd)
        self._animateClose()

    def _tabComplete(self) -> None:
        """Tab 补全: 把选中命令文本填入输入框, 不关闭弹窗.

        发出 ``tabCompleted(str)`` 信号, 参数为完整命令文本 (如 "/all").
        宿主 (ChatInputEdit) 收到后替换输入框内容.
        """
        if 0 <= self._selectedIdx < len(self._filteredItems):
            cmd = self._filteredItems[self._selectedIdx].command()
            self.tabCompleted.emit(cmd)

    def _onItemClicked(self, command: str) -> None:
        self.commandSelected.emit(command)
        self._animateClose()
