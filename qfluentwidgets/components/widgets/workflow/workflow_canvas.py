# coding: utf-8
"""工作流画布组件

提供基于 QGraphicsView 的工作流画布, 支持平移, 缩放, 节点拖拽和连线交互,
适用于可视化工作流编辑器场景
"""

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QGraphicsView, QWidget, QGraphicsProxyWidget

from ....common.style_sheet import FluentStyleSheet
from .workflow_scene import WorkflowScene
from .workflow_model import WorkflowData


__all__ = ['WorkflowCanvas']


class WorkflowCanvas(QGraphicsView):
    """工作流画布

    基于 QGraphicsView 的可视化工作流编辑器画布, 支持:
    - 鼠标中键 / 空格+左键拖拽平移
    - 滚轮缩放
    - 节点拖拽移动
    - 端口拖拽连线
    - Delete 键删除选中项

    Constructor overloads:
        * WorkflowCanvas(parent: QWidget = None)
    """

    zoomChanged = Signal(float)     # 缩放比例变化

    # Zoom limits
    _MIN_ZOOM = 0.2
    _MAX_ZOOM = 3.0
    _ZOOM_STEP = 1.15

    def __init__(self, parent: QWidget = None):
        """初始化画布

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self._scene = WorkflowScene(self)
        self.setScene(self._scene)

        self._isPanning = False
        self._panStartPos = QPointF()
        self._currentZoom = 1.0
        self._needsCenterOnShow = False

        self._initView()

    def _initView(self):
        """初始化视图设置"""
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)

        FluentStyleSheet.WORKFLOW_CANVAS.apply(self)

    def workflowScene(self) -> WorkflowScene:
        """获取工作流场景

        Returns:
            WorkflowScene 实例
        """
        return self._scene

    def loadWorkflow(self, data: WorkflowData):
        """加载工作流数据

        Args:
            data: 工作流数据
        """
        self._scene.loadWorkflow(data)
        # Defer centering until after nodes have finished layout and edges are created
        self._needsCenterOnShow = True

    def currentZoom(self) -> float:
        """获取当前缩放比例

        Returns:
            缩放比例 (1.0 = 100%)
        """
        return self._currentZoom

    def setZoom(self, factor: float):
        """设置缩放比例

        Args:
            factor: 缩放比例 (0.2 ~ 3.0)
        """
        factor = max(self._MIN_ZOOM, min(self._MAX_ZOOM, factor))
        scale = factor / self._currentZoom
        self.scale(scale, scale)
        self._currentZoom = factor
        self.zoomChanged.emit(self._currentZoom)

    def zoomIn(self):
        """放大"""
        self.setZoom(self._currentZoom * self._ZOOM_STEP)

    def zoomOut(self):
        """缩小"""
        self.setZoom(self._currentZoom / self._ZOOM_STEP)

    def zoomToFit(self):
        """缩放到适应所有内容"""
        items = self._scene.items()
        if not items:
            return

        rect = self._scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        self.fitInView(rect, Qt.KeepAspectRatio)

        # Update current zoom
        transform = self.transform()
        self._currentZoom = transform.m11()
        self.zoomChanged.emit(self._currentZoom)

    def resetZoom(self):
        """重置缩放到 100%"""
        self.setZoom(1.0)

    def centerOnContent(self):
        """将视图中心对准所有节点的几何中心 (不改变缩放)"""
        items = self._scene.items()
        if not items:
            return

        rect = self._scene.itemsBoundingRect()
        self.centerOn(rect.center())

    def showEvent(self, event):
        """首次显示时重新居中 (此时 viewport 尺寸已确定)"""
        super().showEvent(event)
        if self._needsCenterOnShow:
            self._needsCenterOnShow = False
            # Defer centering to ensure all deferred operations (port build, edge creation) complete
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, self._deferredCenter)

    def _deferredCenter(self):
        """延迟居中, 确保节点和连线都已就绪"""
        self.centerOnContent()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent):
        """滚轮事件 - 以鼠标位置为锚点缩放

        如果鼠标位于节点内部的可滚动控件上, 则传递给该控件处理滚动.
        """
        # Check if the item under cursor is a proxy widget with scrollable content
        scenePos = self.mapToScene(event.position().toPoint())
        item = self.scene().itemAt(scenePos, self.transform())

        if isinstance(item, QGraphicsProxyWidget):
            widget = item.widget()
            if widget:
                localPos = item.mapFromScene(scenePos).toPoint()
                childWidget = widget.childAt(localPos)
                if childWidget and self._isScrollableWidget(childWidget):
                    super().wheelEvent(event)
                    return

        # 以鼠标位置为锚点缩放
        delta = event.angleDelta().y()
        if delta == 0:
            return

        # 记录鼠标在场景中的位置
        oldScenePos = self.mapToScene(event.position().toPoint())

        # 执行缩放
        if delta > 0:
            factor = min(self._currentZoom * self._ZOOM_STEP, self._MAX_ZOOM)
        else:
            factor = max(self._currentZoom / self._ZOOM_STEP, self._MIN_ZOOM)

        scale = factor / self._currentZoom
        self.scale(scale, scale)
        self._currentZoom = factor
        self.zoomChanged.emit(self._currentZoom)

        # 将鼠标位置对应的场景点移回鼠标下方
        newScenePos = self.mapToScene(event.position().toPoint())
        delta_pos = newScenePos - oldScenePos
        self.translate(delta_pos.x(), delta_pos.y())

    def _isScrollableWidget(self, widget) -> bool:
        """判断 widget 是否为可滚动控件

        Args:
            widget: 待检测的 widget

        Returns:
            是否可滚动
        """
        from PySide6.QtWidgets import (
            QAbstractScrollArea, QComboBox, QSpinBox, QAbstractSlider
        )
        # Walk up the parent chain to find scrollable ancestors
        w = widget
        while w:
            if isinstance(w, (QAbstractScrollArea, QComboBox, QSpinBox, QAbstractSlider)):
                return True
            w = w.parentWidget()
        return False

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下 - 中键开始平移"""
        if event.button() == Qt.MiddleButton:
            self._isPanning = True
            self._panStartPos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动 - 平移画布"""
        if self._isPanning:
            delta = event.position() - self._panStartPos
            self._panStartPos = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放 - 结束平移"""
        if event.button() == Qt.MiddleButton:
            self._isPanning = False
            self.setCursor(Qt.ArrowCursor)
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件 - 空格键切换平移模式"""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """键盘释放 - 退出平移模式"""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.NoDrag)
            return

        super().keyReleaseEvent(event)
