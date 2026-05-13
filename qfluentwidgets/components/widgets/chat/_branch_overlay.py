# coding: utf-8
"""分支切换的截图过渡组件

参考 NapCatQQ-Desktop-V1 ``src/ui/components/stacked_widget.py`` 中的
``_SnapshotOverlay`` + ``TransparentStackedWidget`` 模式: 切换瞬间抓取当前
内容截图, 落到一个轻量遮罩上, 立即让底层切到新内容; 再在遮罩上跑
``opacity 1->0`` + ``offset_y 0->-8`` 的并行动画, 旧截图淡出并轻微上飘,
新分支内容浮现.

核心好处: opacity 调的是 *遮罩* 的 opacity (一张普通 ``QPixmap``), 不是被
切换的 ``_inner`` / 各 ``ChatBubble`` 内容本体. 不会和 chat 模块已有的
hover-fade / theme transition / actions actions-always-visible 等策略打架.
"""

from typing import Optional

from PySide6.QtCore import (
    Property, QEasingCurve, QObject, QParallelAnimationGroup,
    QPropertyAnimation, Qt, Signal,
)
from PySide6.QtGui import QPainter, QPaintEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QWidget


__all__ = ["BranchSnapshotPlayer"]


class _BranchSnapshotOverlay(QWidget):
    """纯渲染层. 在 paintEvent 里把缓存的 pixmap 按当前 opacity / offset 画出.

    属性 ``opacity`` / ``offset_x`` / ``offset_y`` 通过 ``Property(float, ...)``
    暴露给 ``QPropertyAnimation`` 驱动.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._opacity = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

        # 截图遮罩不接收鼠标 (穿透到底层 view, 用户的滚轮 / 拖拽不被打断),
        # 同时背景透明, 仅 paintEvent 内绘制 pixmap.
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    # ------------------------------------------------------------------
    # 动画属性
    # ------------------------------------------------------------------

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = max(0.0, min(float(value), 1.0))
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def get_offset_x(self) -> float:
        return self._offset_x

    def set_offset_x(self, value: float) -> None:
        self._offset_x = float(value)
        self.update()

    offset_x = Property(float, get_offset_x, set_offset_x)

    def get_offset_y(self) -> float:
        return self._offset_y

    def set_offset_y(self, value: float) -> None:
        self._offset_y = float(value)
        self.update()

    offset_y = Property(float, get_offset_y, set_offset_y)

    # ------------------------------------------------------------------
    # 截图管理
    # ------------------------------------------------------------------

    def set_snapshot(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._offset_x = 0.0
        self._offset_y = 0.0
        self.update()

    def clear_snapshot(self) -> None:
        self._pixmap = QPixmap()
        self._offset_x = 0.0
        self._offset_y = 0.0
        self.update()

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(
            self.rect().translated(int(self._offset_x), int(self._offset_y)),
            self._pixmap,
        )
        painter.end()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        # parent 尺寸变化时由外部 player 同步调 setGeometry, 这里仅触发重绘.
        self.update()


class BranchSnapshotPlayer(QObject):
    """高层 facade. 给 :class:`AgentChatView` 调用.

    用法:

    .. code-block:: python

        player = BranchSnapshotPlayer(view)
        snapshot = view._inner.grab()
        if not snapshot.isNull():
            player.play(view.viewport(), snapshot, duration=220, offset_y=-8)

    Attributes:
        animationStarted: 动画开始时发出.
        animationFinished: 动画完成 / 取消时发出.
    """

    animationStarted = Signal()
    animationFinished = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._overlay: Optional[_BranchSnapshotOverlay] = None
        self._group: Optional[QParallelAnimationGroup] = None

    def is_playing(self) -> bool:
        if self._group is None:
            return False
        return self._group.state() == QPropertyAnimation.State.Running

    def cancel(self) -> None:
        """立即终止当前动画, overlay 隐藏 + 销毁."""
        if self._group is not None and self.is_playing():
            self._group.stop()
        self._cleanup()

    def play(
        self,
        parent_widget: QWidget,
        snapshot: QPixmap,
        duration: int = 220,
        offset_y: int = -8,
        offset_x: int = 0,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> None:
        """启动一次截图过渡动画.

        Args:
            parent_widget: 遮罩的 parent (一般是 ``view.viewport()``).
                           overlay 几何会铺满 parent.
            snapshot:      要淡出的截图. 调用方在切换内容**之前**用
                           ``widget.grab()`` 抓取.
            duration:      动画时长, 毫秒. 默认 220.
            offset_y:      纵向漂移目标值 (像素). 默认 -8 (向上飘).
            offset_x:      横向漂移目标值 (像素). 默认 0.
            easing:        easing curve, 默认 ``OutCubic``.
        """
        if snapshot.isNull():
            return

        # 上一次动画还在跑: 立刻收尾, 避免堆叠.
        if self.is_playing():
            self.cancel()

        overlay = _BranchSnapshotOverlay(parent_widget)
        overlay.setGeometry(parent_widget.rect())
        overlay.set_snapshot(snapshot)
        overlay.set_opacity(1.0)
        overlay.set_offset_x(0.0)
        overlay.set_offset_y(0.0)
        overlay.show()
        overlay.raise_()
        self._overlay = overlay

        fade = QPropertyAnimation(overlay, b"opacity", self)
        fade.setDuration(int(duration))
        fade.setEasingCurve(easing)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)

        oy = QPropertyAnimation(overlay, b"offset_y", self)
        oy.setDuration(int(duration))
        oy.setEasingCurve(easing)
        oy.setStartValue(0.0)
        oy.setEndValue(float(offset_y))

        ox = QPropertyAnimation(overlay, b"offset_x", self)
        ox.setDuration(int(duration))
        ox.setEasingCurve(easing)
        ox.setStartValue(0.0)
        ox.setEndValue(float(offset_x))

        group = QParallelAnimationGroup(self)
        group.addAnimation(fade)
        group.addAnimation(oy)
        group.addAnimation(ox)
        group.finished.connect(self._on_group_finished)
        self._group = group

        self.animationStarted.emit()
        group.start()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _on_group_finished(self) -> None:
        self._cleanup()
        self.animationFinished.emit()

    def _cleanup(self) -> None:
        if self._overlay is not None:
            self._overlay.hide()
            self._overlay.clear_snapshot()
            self._overlay.deleteLater()
            self._overlay = None
        if self._group is not None:
            # group 是 QObject, parent=self, 留给 Qt 父子树自然回收.
            # 这里仅清引用, 避免 is_playing 误判.
            self._group = None
