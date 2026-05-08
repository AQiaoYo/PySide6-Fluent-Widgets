# coding: utf-8
"""聊天头像组件

基于 AvatarWidget 扩展, 适配聊天场景:
- 按 ChatRole 提供差异化默认背景色 (USER 紫 / AGENT 蓝 / SYSTEM 灰)
- 默认无图像时显示居中的白色 FluentIcon (替代 AvatarWidget 默认的首字母)
- 自定义图像时退回到 AvatarWidget 的圆形居中裁剪逻辑
"""

from typing import Optional, Union

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget

from ....common.icon import FluentIcon, FluentIconBase
from ..label import AvatarWidget
from .chat_message import ChatRole


__all__ = ['ChatAvatar']


class ChatAvatar(AvatarWidget):
    """聊天头像组件

    继承 AvatarWidget, 圆角矩形外形 + 角色色底 + 居中白色 FluentIcon
    (USER -> PEOPLE, AGENT -> ROBOT). 若通过 ``setAvatar`` 传入自定义
    图像, 则按相同圆角矩形裁剪显示.

    构造函数:
        ChatAvatar(role: ChatRole, size: int = 32, parent: QWidget = None)
    """

    # 角色 -> 默认背景色
    _DEFAULT_BG = {
        ChatRole.USER:   QColor(99, 192, 134),   # 绿 (类参考图用户色)
        ChatRole.AGENT:  QColor(64, 132, 246),   # 蓝
        ChatRole.SYSTEM: QColor(160, 160, 160),  # 灰
    }

    # 圆角半径相对于尺寸的比例 (类似 macOS app icon 的 squircle)
    _CORNER_RATIO = 0.28

    def __init__(self, role: ChatRole, size: int = 32, parent: Optional[QWidget] = None):
        """初始化聊天头像

        Args:
            role:   消息角色, 决定默认图标和背景色
            size:   头像边长 (像素, 正方形), 默认 32
            parent: 父级 QWidget, 默认 None
        """
        super().__init__(parent)
        self._role = role
        self._defaultIcon: FluentIconBase = (
            FluentIcon.ROBOT if role == ChatRole.AGENT else FluentIcon.PEOPLE
        )
        size = max(int(size), 16)
        self.setFixedSize(size, size)
        bg = self._DEFAULT_BG.get(role, QColor(160, 160, 160))
        self.setBackgroundColor(bg, bg)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setAvatar(self, avatar: Optional[Union[QIcon, QImage, QPixmap, str]]):
        """设置自定义头像.

        Args:
            avatar: QIcon / QImage / QPixmap / 图片路径 / None.
                    传 None 时清空图像并恢复默认 FluentIcon 头像.
        """
        # 直接维护 self.image, 不调 super().setImage() 以免它根据图像尺寸
        # 触发 setFixedSize, 破坏头像 32x32 的固定外形.
        if avatar is None:
            self.image = QImage()
        elif isinstance(avatar, QIcon):
            self.image = avatar.pixmap(self.size()).toImage()
        elif isinstance(avatar, QPixmap):
            self.image = avatar.toImage()
        elif isinstance(avatar, QImage):
            self.image = avatar
        elif isinstance(avatar, str):
            self.image = QImage(avatar)
        else:
            self.image = QImage()
        self.update()

    def role(self) -> ChatRole:
        """返回此头像绑定的 ChatRole."""
        return self._role

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        """完全接管: 圆角矩形 squircle + 自定义图像或默认 icon"""
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        painter.setPen(Qt.PenStyle.NoPen)

        # 圆角矩形 path (在 0.5px 内缩, 让边缘抗锯齿不被裁切)
        radius = max(self.width() * self._CORNER_RATIO, 4.0)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # 用 path 裁剪后续绘制 (背景 + icon/image 都自动按圆角矩形裁切)
        painter.setClipPath(path)

        if not self.isNull():
            # 自定义图像: center-crop 到正方形
            self._drawClippedImage(painter)
        else:
            self._drawDefaultIcon(painter)

    def _drawClippedImage(self, painter: QPainter):
        """按 KeepAspectRatioByExpanding 缩放图像并 center crop"""
        target_size = self.size() * self.devicePixelRatioF()
        scaled = self.image.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(self.devicePixelRatioF())
        # 居中绘制
        x = (self.width() - scaled.width() / scaled.devicePixelRatio()) / 2
        y = (self.height() - scaled.height() / scaled.devicePixelRatio()) / 2
        painter.drawImage(QRectF(x, y, scaled.width() / scaled.devicePixelRatio(),
                                 scaled.height() / scaled.devicePixelRatio()), scaled)

    def _drawDefaultIcon(self, painter: QPainter):
        """绘制角色色背景 + 居中白色 FluentIcon"""
        # 1. 背景纯色填充 (path 已裁剪)
        bg = self._DEFAULT_BG.get(self._role, QColor(160, 160, 160))
        painter.fillRect(self.rect(), bg)

        # 2. 居中白色 icon
        # 用 logical 尺寸定位, 让 QIcon.paint 自己处理 DPR
        icon_size = max(int(self.width() * 0.58), 14)
        target = QRect(
            (self.width() - icon_size) // 2,
            (self.height() - icon_size) // 2,
            icon_size, icon_size,
        )
        try:
            qicon = self._defaultIcon.icon(color=QColor(255, 255, 255))
        except TypeError:
            qicon = self._defaultIcon.icon()
        qicon.paint(painter, target, Qt.AlignmentFlag.AlignCenter)
