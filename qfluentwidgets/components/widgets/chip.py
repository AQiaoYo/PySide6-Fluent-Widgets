# coding: utf-8
"""标签和芯片组件模块

提供 Tag 和 Chip 组件，用于信息展示和标签选择。
Tag 用于显示图标和文本，根据信息级别可显示不同的背景色和前景色，
基于 PushButton 实现，使用方式和 QPushButton 完全相同；
Chip 在 ToggleButton 基础上增加了删除按钮，可作为标签供用户选择，
使用方式和 QPushButton 完全相同。
"""

from enum import Enum
from typing import Union

from PySide6.QtCore import Qt, Signal, QRectF, QSize, QRect
from PySide6.QtGui import QColor, QPainter, QIcon
from PySide6.QtWidgets import QSizePolicy

from ...common.icon import FluentIconBase, drawIcon, isDarkTheme, Theme, Icon
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont
from ...common.style_sheet import themeColor, ThemeColor
from ...common.overload import singledispatchmethod
from .button import PushButton, ToggleButton


class TagColor(Enum):
    """标签颜色变体

    用于 Tag 组件的信息级别展示
    """

    GRAY = "gray"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    BLUE = "blue"


def _tagColorSet(color: TagColor, isDark: bool):
    """返回指定颜色主题的 (背景色, 文字色, 边框色)

    Args:
        color: 颜色变体
        isDark: 是否为深色主题

    Returns:
        tuple[QColor, QColor, QColor]
    """
    sets = {
        TagColor.GRAY: {
            True: (
                QColor(255, 255, 255, 20),
                QColor(255, 255, 255, 220),
                QColor(255, 255, 255, 35),
            ),
            False: (QColor(245, 245, 245), QColor(97, 97, 97), QColor(224, 224, 224)),
        },
        TagColor.GREEN: {
            True: (
                QColor(76, 175, 80, 40),
                QColor(129, 199, 132),
                QColor(76, 175, 80, 80),
            ),
            False: (QColor(232, 245, 233), QColor(46, 125, 50), QColor(165, 214, 167)),
        },
        TagColor.YELLOW: {
            True: (
                QColor(255, 193, 7, 40),
                QColor(255, 213, 79),
                QColor(255, 193, 7, 80),
            ),
            False: (QColor(255, 253, 231), QColor(245, 176, 0), QColor(255, 236, 179)),
        },
        TagColor.RED: {
            True: (
                QColor(239, 83, 80, 40),
                QColor(239, 154, 154),
                QColor(239, 83, 80, 80),
            ),
            False: (QColor(255, 235, 238), QColor(198, 40, 40), QColor(239, 154, 154)),
        },
        TagColor.BLUE: {
            True: (
                QColor(66, 165, 245, 40),
                QColor(144, 202, 249),
                QColor(66, 165, 245, 80),
            ),
            False: (QColor(227, 242, 253), QColor(21, 101, 192), QColor(144, 202, 249)),
        },
    }
    return sets[color][isDark]


def _tagColors(color: TagColor, isDark: bool, isPressed: bool, isHover: bool):
    """获取当前状态的绘制颜色

    Args:
        color: 颜色变体
        isDark: 是否为深色主题
        isPressed: 是否按下
        isHover: 是否悬停

    Returns:
        tuple[QColor, QColor, QColor]: (背景色, 文字色, 边框色)
    """
    bg, text, border = _tagColorSet(color, isDark)

    if isPressed:
        if isDark:
            bg = QColor(bg.red(), bg.green(), bg.blue(), max(0, bg.alpha() - 10))
        else:
            bg = QColor(
                max(0, bg.red() - 20),
                max(0, bg.green() - 20),
                max(0, bg.blue() - 20),
                bg.alpha(),
            )
    elif isHover:
        if isDark:
            bg = QColor(bg.red(), bg.green(), bg.blue(), min(255, bg.alpha() + 15))
        else:
            bg = QColor(
                max(0, bg.red() - 10),
                max(0, bg.green() - 10),
                max(0, bg.blue() - 10),
                bg.alpha(),
            )

    return bg, text, border


def _drawTagContent(
    painter: QPainter, widget, textColor: QColor, iconSize: QSize, rightMargin: int = 10
):
    """绘制 Tag/Chip 的图标和文字

    Args:
        painter: 绘图对象
        widget: 目标控件（Tag 或 Chip）
        textColor: 文字/图标颜色
        iconSize: 图标尺寸
        rightMargin: 右侧留空宽度，Chip 需要为关闭按钮留空间
    """
    x = 10
    h = widget.height()
    rawIcon = getattr(widget, "_icon", None)

    # 图标 — 颜色跟随标签主题色（textColor）
    if rawIcon and not widget.icon().isNull():
        iw, ih = iconSize.width(), iconSize.height()
        iy = (h - ih) / 2
        iconRect = QRectF(x, iy, iw, ih)

        fluentIcon = None
        if isinstance(rawIcon, FluentIconBase):
            fluentIcon = rawIcon
        elif isinstance(rawIcon, Icon) and rawIcon.fluentIcon:
            fluentIcon = rawIcon.fluentIcon

        if fluentIcon:
            coloredIcon = fluentIcon.icon(color=textColor)
            coloredIcon.paint(painter, iconRect.toRect(), Qt.AlignCenter)
        else:
            drawIcon(rawIcon, painter, iconRect)

        x += iw + 4

    # 文字
    text = widget.text()
    if text:
        painter.setPen(textColor)
        painter.setFont(widget.font())
        tw = max(0, widget.width() - int(x) - rightMargin)
        painter.drawText(int(x), 0, tw, h, Qt.AlignVCenter, text)


class Tag(PushButton):
    """标签组件，用于显示图标和文本

    根据信息级别可显示不同的背景色和前景色，使用方式和 QPushButton 完全相同。
    基于 PushButton 实现，适用于信息分类、状态标识等场景

    构造函数重载:
        * Tag(parent: QWidget = None)
        * Tag(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * Tag(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化标签

        Args:
            parent: 父控件，默认为 None
        """
        super().__init__(parent)
        self._color = TagColor.GRAY
        self.setIconSize(QSize(16, 16))
        setFont(self, 14)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    @__init__.register
    def _(self, text: str, parent=None, icon: Union[QIcon, str, FluentIconBase] = None):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent=None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent=None):
        self.__init__(text, parent, icon)

    def getColor(self):
        """获取当前颜色

        Returns:
            TagColor 颜色变体
        """
        return self._color

    def setColor(self, color: TagColor):
        """设置颜色变体

        Args:
            color: 颜色变体
        """
        self._color = color
        self.update()

    color = property(getColor, setColor)

    def sizeHint(self):
        """获取推荐尺寸"""
        fm = self.fontMetrics()
        tw = fm.horizontalAdvance(self.text()) if self.text() else 0
        iw = self.iconSize().width() if not self.icon().isNull() else 0
        gap = 4 if not self.icon().isNull() and self.text() else 0
        w = 10 + iw + gap + tw + 10
        return QSize(w, 32)

    def minimumSizeHint(self):
        """获取最小尺寸"""
        return self.sizeHint()

    def paintEvent(self, e):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        isDark = isDarkTheme()
        bg, textColor, border = _tagColors(
            self._color, isDark, self.isPressed, self.isHover
        )

        # 绘制背景
        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 4
        painter.setPen(border)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, r, r)

        # 绘制内容
        _drawTagContent(painter, self, textColor, self.iconSize())


class Chip(ToggleButton):
    """芯片标签组件，带有删除按钮，可作为标签供用户选择

    用于显示图标和文本，带有删除按钮，点击主体可切换选中状态，
    点击删除按钮可移除标签。使用方式和 QPushButton 完全相同。
    基于 ToggleButton 实现，天然支持 checked/unchecked 状态切换

    构造函数重载:
        * Chip(parent: QWidget = None)
        * Chip(text: str, parent: QWidget = None, icon: QIcon | str | FluentIconBase = None)
        * Chip(icon: QIcon | FluentIconBase, text: str, parent: QWidget = None)
    """

    closed = Signal()
    selectedChanged = Signal(bool)

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化芯片标签

        Args:
            parent: 父控件，默认为 None
        """
        super().__init__(parent)
        self._closable = True
        self.setIconSize(QSize(16, 16))
        setFont(self, 14)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggled.connect(self.selectedChanged.emit)

    @__init__.register
    def _(self, text: str, parent=None, icon: Union[QIcon, str, FluentIconBase] = None):
        self.__init__(parent)
        self.setText(text)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, text: str, parent=None):
        self.__init__(text, parent, icon)

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent=None):
        self.__init__(text, parent, icon)

    def isClosable(self) -> bool:
        """获取是否可关闭

        Returns:
            是否显示关闭按钮
        """
        return self._closable

    def setClosable(self, closable: bool):
        """设置是否可关闭

        Args:
            closable: 是否显示关闭按钮
        """
        if self._closable != closable:
            self._closable = closable
            self.updateGeometry()
            self.update()

    closable = property(isClosable, setClosable)

    def _closeButtonRect(self):
        """获取关闭按钮点击区域

        Returns:
            QRect 关闭按钮区域
        """
        btnSize = 16
        x = self.width() - 6 - btnSize + (btnSize - 10) // 2
        y = (self.height() - btnSize) // 2
        return QRect(int(x), int(y), btnSize, btnSize)

    def sizeHint(self):
        """获取推荐尺寸"""
        fm = self.fontMetrics()
        tw = fm.horizontalAdvance(self.text()) if self.text() else 0
        iw = self.iconSize().width() if not self.icon().isNull() else 0
        gap = 4 if not self.icon().isNull() and self.text() else 0
        w = 10 + iw + gap + tw + 10
        if self._closable:
            w += 6 + 10
        return QSize(w, 32)

    def minimumSizeHint(self):
        """获取最小尺寸"""
        return self.sizeHint()

    def paintEvent(self, e):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        isDark = isDarkTheme()

        if self.isChecked():
            tc = themeColor()
            if self.isPressed:
                tc = ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color()
            elif self.isHover:
                tc = ThemeColor.DARK_1.color() if isDark else ThemeColor.LIGHT_1.color()
            bg, textColor, border = tc, QColor(255, 255, 255), Qt.transparent
        else:
            bg, textColor, border = _tagColors(
                TagColor.GRAY, isDark, self.isPressed, self.isHover
            )

        # 绘制背景
        rect = self.rect().adjusted(1, 1, -1, -1)
        r = 4
        painter.setPen(border)
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, r, r)

        # 绘制内容
        rightMargin = 10 + 6 + 10 if self._closable else 10
        _drawTagContent(painter, self, textColor, self.iconSize(), rightMargin=rightMargin)

        # 绘制关闭按钮
        if self._closable:
            closeRect = QRectF(self.width() - 6 - 10, (self.height() - 10) / 2, 10, 10)

            if self.isChecked():
                # 选中状态：关闭按钮为纯白色
                closeIcon = FIF.CLOSE.icon(Theme.DARK)
            else:
                # 未选中状态：关闭按钮跟随文字颜色
                closeIcon = FIF.CLOSE.icon(color=textColor)

            drawIcon(closeIcon, painter, closeRect)

    def mouseReleaseEvent(self, e):
        """鼠标释放事件

        点击关闭按钮区域时发射 closed 信号，不触发选中状态切换；
        点击主体区域时由 ToggleButton 处理状态切换
        """
        if self._closable and self._closeButtonRect().contains(e.pos()):
            self.isPressed = False
            self.update()
            self.closed.emit()
            return

        super().mouseReleaseEvent(e)
