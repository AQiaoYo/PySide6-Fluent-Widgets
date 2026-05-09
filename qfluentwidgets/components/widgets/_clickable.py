# coding: utf-8
"""共享的可点击容器 widget.

聊天 / 工具卡片 / 输入框内嵌指示器等场景反复需要 "鼠标进入显手型 + 左键
触发 ``clicked`` 信号" 的轻量容器. 此前每个 caller 都各自维护一份 (chat 子
包内有 3 处副本), 现统一抽到这里.

提供两个变体:

* :class:`ClickableFrame` -- 继承 ``QFrame``, 适合卡片 header 这类 "我自己
  就是带边框/背景的视觉元素" 场景.
* :class:`ClickableWidget` -- 继承 ``QWidget``, 适合 "我只是套个透明的事件
  接收层" 场景 (如输入框内嵌 token 指示器).

设计上两者点击语义一致: 左键按下时 emit ``clicked`` + ``event.accept()`` +
不再向父级传播. 这样可以避免点击穿透到父 widget (例如点击 token 指示器时
触发 ``ChatInputEdit`` 取焦).

使用注意: 这两个类被多个内部子包共用, 不进 ``components/widgets``
公共 ``__all__``, 当作模块内部 utility.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import QFrame, QWidget


__all__ = ['ClickableFrame', 'ClickableWidget']


class ClickableFrame(QFrame):
    """左键点击发出 ``clicked`` 信号, hover 显手型的 ``QFrame``.

    构造函数:
        ClickableFrame(parent: QWidget = None)

    Signals:
        clicked(): 左键按下时发出 (后续不再传播给父级).
    """

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class ClickableWidget(QWidget):
    """左键点击发出 ``clicked`` 信号, hover 显手型的透明 ``QWidget``.

    与 :class:`ClickableFrame` 行为一致, 区别仅在基类: 这里继承 ``QWidget``,
    不带 frame border 默认绘制, 适合用作纯事件接收层.

    构造函数:
        ClickableWidget(parent: QWidget = None)

    Signals:
        clicked(): 左键按下时发出 (后续不再传播给父级).
    """

    clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)
