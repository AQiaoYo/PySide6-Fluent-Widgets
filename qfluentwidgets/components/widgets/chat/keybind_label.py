# coding: utf-8
"""快捷键标签组件 (KeybindLabel)

显示一个快捷键组合, 如 "Ctrl+K" 或 "Shift+Enter".
每个按键用圆角小方块包裹, 视觉上类似键盘按键.
"""

from typing import List, Optional

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from ....common.font import setFont
from ....common.style_sheet import isDarkTheme


__all__ = ['KeybindLabel']


class KeybindLabel(QWidget):
    """快捷键标签组件

    显示快捷键组合, 每个按键用圆角方块包裹.
    例如 "Ctrl+K" 显示为 [Ctrl] + [K].

    构造函数:
        KeybindLabel(keys: str = "", parent: QWidget = None)
    """

    _KEY_PADDING_H = 6    # 按键方块内水平 padding
    _KEY_PADDING_V = 3    # 按键方块内垂直 padding
    _KEY_SPACING = 4      # 按键之间的间距
    _KEY_RADIUS = 4.0     # 按键方块圆角
    _PLUS_WIDTH = 12      # "+" 分隔符宽度

    def __init__(self, keys: str = "", parent: Optional[QWidget] = None):
        """初始化

        Args:
            keys: 快捷键字符串, 用 "+" 分隔, 如 "Ctrl+K", "Shift+Enter"
            parent: 父级 QWidget
        """
        super().__init__(parent)
        self._keys: List[str] = []
        self._keysText = ""

        setFont(self)
        # 用稍小的字号
        font = self.font()
        font.setPointSize(max(8, font.pointSize() - 1))
        self.setFont(font)

        if keys:
            self.setKeys(keys)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setKeys(self, keys: str) -> None:
        """设置快捷键字符串.

        Args:
            keys: 如 "Ctrl+K", "Shift+Enter", "Alt+F4"
        """
        self._keysText = keys
        self._keys = [k.strip() for k in keys.split("+") if k.strip()]
        self._adjustSize()
        self.update()

    def keys(self) -> str:
        return self._keysText

    def keyList(self) -> List[str]:
        return list(self._keys)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())

        isDark = isDarkTheme()
        textColor = QColor(255, 255, 255, 200) if isDark else QColor(0, 0, 0, 180)
        bgColor = QColor(255, 255, 255, 20) if isDark else QColor(0, 0, 0, 13)
        borderColor = QColor(255, 255, 255, 40) if isDark else QColor(0, 0, 0, 30)
        plusColor = QColor(255, 255, 255, 100) if isDark else QColor(0, 0, 0, 100)

        fm = QFontMetrics(self.font())
        x = 0.0
        h = self.height()

        for i, key in enumerate(self._keys):
            if i > 0:
                # 画 "+" 分隔符
                painter.setPen(plusColor)
                painter.drawText(
                    QRectF(x, 0, self._PLUS_WIDTH, h),
                    Qt.AlignmentFlag.AlignCenter, "+",
                )
                x += self._PLUS_WIDTH

            # 计算按键方块尺寸
            keyW = fm.horizontalAdvance(key) + self._KEY_PADDING_H * 2
            keyH = fm.height() + self._KEY_PADDING_V * 2
            keyY = (h - keyH) / 2

            # 画按键背景
            keyRect = QRectF(x, keyY, keyW, keyH)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bgColor)
            painter.drawRoundedRect(keyRect, self._KEY_RADIUS, self._KEY_RADIUS)

            # 画按键边框
            pen = QPen(borderColor, 1.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(keyRect, self._KEY_RADIUS, self._KEY_RADIUS)

            # 画按键文字
            painter.setPen(textColor)
            painter.drawText(keyRect, Qt.AlignmentFlag.AlignCenter, key)

            x += keyW + self._KEY_SPACING

    def sizeHint(self):
        return self._calcSize()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _calcSize(self) -> QSize:
        if not self._keys:
            return QSize(0, 0)
        fm = QFontMetrics(self.font())
        w = 0.0
        for i, key in enumerate(self._keys):
            if i > 0:
                w += self._PLUS_WIDTH
            w += fm.horizontalAdvance(key) + self._KEY_PADDING_H * 2 + self._KEY_SPACING
        w -= self._KEY_SPACING  # 最后一个不需要 spacing
        h = fm.height() + self._KEY_PADDING_V * 2 + 4
        return QSize(int(w) + 2, int(h))

    def _adjustSize(self) -> None:
        size = self._calcSize()
        self.setFixedSize(size)
