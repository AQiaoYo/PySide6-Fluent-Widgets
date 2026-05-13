# coding: utf-8
"""附件预览区 (AttachmentPreview)

在 ChatInputEdit 上方显示一排附件缩略图卡片, 视觉上是输入框向上延伸的一部分.
每个附件是一个小卡片: 图片类型显示缩略图, 文件类型显示图标+文件名.
hover 时右上角出现 x 删除按钮.

设计要点:
- 整体有卡片背景 (与输入框共圆角, 视觉一体)
- 缩略图 48x48, 圆角 6px
- 文件卡片: 图标 + 文件名, 固定宽度
- 水平排列, 超出可滚动
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from uuid import uuid4

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ....common.style_sheet import isDarkTheme
from ..button import TransparentToolButton


__all__ = ['AttachmentPreview', 'AttachmentItem']


@dataclass
class AttachmentItem:
    """附件数据."""
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    name: str = ""
    pixmap: Optional[QPixmap] = None
    file_path: Optional[str] = None
    is_image: bool = True


class _ImageThumb(QWidget):
    """图片缩略图 (48x48 圆角)."""

    removeClicked = Signal(str)

    _SIZE = 48
    _RADIUS = 6.0
    _CLOSE_SIZE = 16

    def __init__(self, item: AttachmentItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._item = item
        self.setFixedSize(self._SIZE, self._SIZE)

        self._closeBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self._closeBtn.setFixedSize(self._CLOSE_SIZE, self._CLOSE_SIZE)
        self._closeBtn.setIconSize(QSize(8, 8))
        self._closeBtn.move(self._SIZE - self._CLOSE_SIZE, 0)
        self._closeBtn.clicked.connect(lambda: self.removeClicked.emit(self._item.id))
        self._closeBtn.hide()

    def enterEvent(self, event):
        super().enterEvent(event)
        self._closeBtn.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._closeBtn.hide()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )

        rect = QRectF(0, 0, self._SIZE, self._SIZE)
        path = QPainterPath()
        path.addRoundedRect(rect, self._RADIUS, self._RADIUS)
        painter.setClipPath(path)

        if self._item.pixmap and not self._item.pixmap.isNull():
            scaled = self._item.pixmap.scaled(
                QSize(self._SIZE, self._SIZE) * self.devicePixelRatioF(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self._SIZE - scaled.width() / max(1, scaled.devicePixelRatioF())) / 2
            y = (self._SIZE - scaled.height() / max(1, scaled.devicePixelRatioF())) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            bg = QColor(60, 60, 64) if isDarkTheme() else QColor(235, 235, 240)
            painter.fillRect(self.rect(), bg)

        # 边框
        painter.setClipping(False)
        borderColor = QColor(255, 255, 255, 25) if isDarkTheme() else QColor(0, 0, 0, 15)
        painter.setPen(QPen(borderColor, 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), self._RADIUS, self._RADIUS)


class _FileThumb(QWidget):
    """文件缩略图卡片 (图标 + 文件名)."""

    removeClicked = Signal(str)

    _HEIGHT = 48
    _WIDTH = 140
    _RADIUS = 6.0
    _CLOSE_SIZE = 16

    def __init__(self, item: AttachmentItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._item = item
        self.setFixedSize(self._WIDTH, self._HEIGHT)

        self._closeBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self._closeBtn.setFixedSize(self._CLOSE_SIZE, self._CLOSE_SIZE)
        self._closeBtn.setIconSize(QSize(8, 8))
        self._closeBtn.move(self._WIDTH - self._CLOSE_SIZE, 0)
        self._closeBtn.clicked.connect(lambda: self.removeClicked.emit(self._item.id))
        self._closeBtn.hide()

    def enterEvent(self, event):
        super().enterEvent(event)
        self._closeBtn.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._closeBtn.hide()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        isDark = isDarkTheme()
        bg = QColor(50, 50, 54) if isDark else QColor(245, 245, 248)
        border = QColor(255, 255, 255, 20) if isDark else QColor(0, 0, 0, 10)

        rect = QRectF(0.5, 0.5, self._WIDTH - 1, self._HEIGHT - 1)
        painter.setPen(QPen(border, 1.0))
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, self._RADIUS, self._RADIUS)

        # 文件图标
        iconSize = 20
        iconX = 12
        iconY = (self._HEIGHT - iconSize) // 2
        icon = FluentIcon.DOCUMENT.icon()
        icon.paint(painter, iconX, iconY, iconSize, iconSize)

        # 文件名
        textColor = QColor(255, 255, 255, 200) if isDark else QColor(0, 0, 0, 180)
        painter.setPen(textColor)
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        textX = iconX + iconSize + 8
        textW = self._WIDTH - textX - self._CLOSE_SIZE - 4
        fm = QFontMetrics(font)
        name = fm.elidedText(self._item.name or "file", Qt.TextElideMode.ElideMiddle, textW)
        painter.drawText(textX, iconY, textW, iconSize, Qt.AlignmentFlag.AlignVCenter, name)


class AttachmentPreview(QWidget):
    """附件预览区 (卡片式, 与输入框视觉一体)

    Signals:
        itemRemoved(str): 用户删除某个附件, 参数为 item_id
        changed():        附件列表变化时发出

    构造函数:
        AttachmentPreview(parent: QWidget = None)
    """

    itemRemoved = Signal(str)
    changed = Signal()

    _HEIGHT = 64
    _RADIUS = 8.0

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("attachmentPreview")
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._items: List[AttachmentItem] = []
        self._thumbs: Dict[str, QWidget] = {}

        # 内部水平布局
        self._hLayout = QHBoxLayout(self)
        self._hLayout.setContentsMargins(12, 8, 12, 8)
        self._hLayout.setSpacing(8)
        self._hLayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.hide()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addImage(self, image: Union[QPixmap, QImage, str], name: str = "") -> str:
        """添加图片附件.

        Args:
            image: QPixmap, QImage, 或图片文件路径
            name:  显示名称

        Returns:
            附件 ID
        """
        if isinstance(image, str):
            pixmap = QPixmap(image)
            if not name:
                import os
                name = os.path.basename(image)
        elif isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        else:
            pixmap = image

        item = AttachmentItem(name=name or "image", pixmap=pixmap, is_image=True)
        self._addItem(item)
        return item.id

    def addFile(self, file_path: str, name: str = "") -> str:
        """添加文件附件.

        Args:
            file_path: 文件路径
            name:      显示名称

        Returns:
            附件 ID
        """
        if not name:
            import os
            name = os.path.basename(file_path)
        item = AttachmentItem(name=name, file_path=file_path, is_image=False)
        self._addItem(item)
        return item.id

    def removeAttachment(self, item_id: str) -> None:
        """移除一个附件."""
        thumb = self._thumbs.pop(item_id, None)
        if thumb is None:
            return
        self._items = [it for it in self._items if it.id != item_id]
        self._hLayout.removeWidget(thumb)
        thumb.setParent(None)
        thumb.deleteLater()
        self.itemRemoved.emit(item_id)
        self.changed.emit()
        if not self._items:
            self.hide()

    def clear(self) -> None:
        """清空所有附件."""
        for thumb in list(self._thumbs.values()):
            self._hLayout.removeWidget(thumb)
            thumb.setParent(None)
            thumb.deleteLater()
        self._thumbs.clear()
        self._items.clear()
        self.changed.emit()
        self.hide()

    def attachments(self) -> List[AttachmentItem]:
        """返回当前附件列表."""
        return list(self._items)

    def count(self) -> int:
        return len(self._items)

    # ------------------------------------------------------------------
    # 绘制 (卡片背景)
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        isDark = isDarkTheme()
        bg = QColor(44, 44, 48, 245) if isDark else QColor(250, 250, 252, 245)
        border = QColor(255, 255, 255, 15) if isDark else QColor(0, 0, 0, 8)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(border, 1.0))
        painter.setBrush(bg)
        painter.drawRoundedRect(rect, self._RADIUS, self._RADIUS)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _addItem(self, item: AttachmentItem) -> None:
        self._items.append(item)
        if item.is_image:
            thumb = _ImageThumb(item, self)
        else:
            thumb = _FileThumb(item, self)
        thumb.removeClicked.connect(self.removeAttachment)
        self._hLayout.addWidget(thumb)
        self._thumbs[item.id] = thumb
        self.changed.emit()
        if not self.isVisible():
            self.show()
