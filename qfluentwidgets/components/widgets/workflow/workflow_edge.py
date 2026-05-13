# coding: utf-8
"""工作流连线组件

提供节点之间的贝塞尔曲线连接线, 支持箭头指示方向
"""

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QPolygonF
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem

from ....common.style_sheet import isDarkTheme
from .workflow_model import EdgeData


__all__ = ['WorkflowEdge', 'WorkflowDragEdge']


class WorkflowEdge(QGraphicsPathItem):
    """工作流连线

    使用贝塞尔曲线连接两个端口, 带箭头指示数据流向

    Attributes:
        edgeData:   连线数据
        sourcePort: 源端口 item
        targetPort: 目标端口 item
    """

    def __init__(self, edgeData: EdgeData, sourcePort=None, targetPort=None, parent=None):
        """初始化连线

        Args:
            edgeData:   连线数据
            sourcePort: 源端口 WorkflowPort
            targetPort: 目标端口 WorkflowPort
            parent:     父 item
        """
        super().__init__(parent)
        self.edgeData = edgeData
        self.sourcePort = sourcePort
        self.targetPort = targetPort
        self._isHover = False
        self._isSelected = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)

        self.updatePath()

    @property
    def edgeId(self) -> str:
        return self.edgeData.id

    def updatePath(self):
        """根据源/目标端口位置更新贝塞尔曲线路径"""
        if not self.sourcePort or not self.targetPort:
            return

        src = self.sourcePort.centerInScene()
        dst = self.targetPort.centerInScene()
        self._buildPath(src, dst)

    def _buildPath(self, src: QPointF, dst: QPointF):
        """构建贝塞尔曲线路径

        Args:
            src: 起点坐标
            dst: 终点坐标
        """
        path = QPainterPath(src)

        dx = abs(dst.x() - src.x())
        offset = max(dx * 0.5, 50)

        ctrl1 = QPointF(src.x() + offset, src.y())
        ctrl2 = QPointF(dst.x() - offset, dst.y())

        path.cubicTo(ctrl1, ctrl2, dst)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        """绘制连线和箭头"""
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        isSelected = self.isSelected() or self._isHover

        if isSelected:
            color = QColor(0, 120, 212) if not isDark else QColor(96, 205, 255)
            width = 2.5
        else:
            color = QColor(140, 140, 140) if not isDark else QColor(160, 160, 160)
            width = 2.0

        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

        # Draw arrow at midpoint
        self._drawArrow(painter, color)

    def _drawArrow(self, painter: QPainter, color: QColor):
        """在连线中点绘制箭头

        Args:
            painter: 画笔
            color:   箭头颜色
        """
        path = self.path()
        if path.isEmpty():
            return

        # Get midpoint and tangent
        t = 0.5
        midPoint = path.pointAtPercent(t)
        angle = path.angleAtPercent(t)

        # Arrow size
        arrowSize = 8

        # Calculate arrow points
        import math
        rad = math.radians(-angle)
        p1 = QPointF(
            midPoint.x() - arrowSize * math.cos(rad - math.pi / 6),
            midPoint.y() - arrowSize * math.sin(rad - math.pi / 6),
        )
        p2 = QPointF(
            midPoint.x() - arrowSize * math.cos(rad + math.pi / 6),
            midPoint.y() - arrowSize * math.sin(rad + math.pi / 6),
        )

        arrow = QPolygonF([midPoint, p1, p2])
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(arrow)

    def hoverEnterEvent(self, event):
        self._isHover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._isHover = False
        self.update()
        super().hoverLeaveEvent(event)

    def boundingRect(self) -> QRectF:
        """扩展边界矩形以包含箭头"""
        return super().boundingRect().adjusted(-10, -10, 10, 10)

    def shape(self):
        """扩展碰撞区域使连线更容易点击选中"""
        from PySide6.QtGui import QPainterPathStroker

        stroker = QPainterPathStroker()
        stroker.setWidth(16)
        return stroker.createStroke(self.path())


class WorkflowDragEdge(QGraphicsPathItem):
    """拖拽中的临时连线

    用户从端口拖出时显示的临时连线, 跟随鼠标移动
    """

    def __init__(self, startPos: QPointF, parent=None):
        """初始化拖拽连线

        Args:
            startPos: 起始点坐标
            parent:   父 item
        """
        super().__init__(parent)
        self._startPos = startPos
        self._endPos = startPos
        self.setZValue(100)
        self._updatePath()

    def setEndPos(self, pos: QPointF):
        """更新终点位置

        Args:
            pos: 终点坐标
        """
        self._endPos = pos
        self._updatePath()

    def _updatePath(self):
        """更新路径"""
        src = self._startPos
        dst = self._endPos

        path = QPainterPath(src)
        dx = abs(dst.x() - src.x())
        offset = max(dx * 0.5, 50)

        ctrl1 = QPointF(src.x() + offset, src.y())
        ctrl2 = QPointF(dst.x() - offset, dst.y())
        path.cubicTo(ctrl1, ctrl2, dst)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        """绘制临时连线 (虚线)"""
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        color = QColor(0, 120, 212) if not isDark else QColor(96, 205, 255)

        pen = QPen(color, 2.0, Qt.DashLine)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())
