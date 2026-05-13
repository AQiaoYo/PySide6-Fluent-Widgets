# coding: utf-8
"""工作流端口组件

提供节点上的输入/输出连接端口, 支持鼠标拖拽创建连线
"""

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsItem, QGraphicsSceneMouseEvent
)

from ....common.style_sheet import isDarkTheme
from .workflow_model import PortData, PortDirection


__all__ = ['WorkflowPort']


class WorkflowPort(QGraphicsEllipseItem):
    """工作流端口

    节点上的连接点, 支持拖拽创建连线.
    输出端口在节点右侧, 输入端口在节点左侧.

    Attributes:
        portData: 端口数据
        nodeItem: 所属节点 item
    """

    RADIUS = 6

    def __init__(self, portData: PortData, nodeItem: QGraphicsItem = None):
        """初始化端口

        Args:
            portData: 端口数据
            nodeItem: 所属节点 QGraphicsItem
        """
        r = self.RADIUS
        super().__init__(-r, -r, 2 * r, 2 * r, nodeItem)
        self.portData = portData
        self.nodeItem = nodeItem
        self._isHover = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setCursor(Qt.CrossCursor)
        self.setZValue(10)

        self._updateAppearance()

    @property
    def portId(self) -> str:
        return self.portData.id

    @property
    def direction(self) -> PortDirection:
        return self.portData.direction

    def centerInScene(self) -> QPointF:
        """获取端口在场景坐标系中的中心点

        Returns:
            场景坐标中心点
        """
        return self.scenePos()

    def hoverEnterEvent(self, event):
        self._isHover = True
        self._updateAppearance()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._isHover = False
        self._updateAppearance()
        super().hoverLeaveEvent(event)

    def _updateAppearance(self):
        """更新端口外观"""
        isDark = isDarkTheme()

        if self._isHover:
            borderColor = QColor(0, 120, 212) if not isDark else QColor(96, 205, 255)
            fillColor = QColor(0, 120, 212, 120) if not isDark else QColor(96, 205, 255, 120)
            # 悬停时放大端口
            r = self.RADIUS + 2
            self.setRect(-r, -r, 2 * r, 2 * r)
        else:
            borderColor = QColor(120, 120, 120) if not isDark else QColor(160, 160, 160)
            fillColor = QColor(255, 255, 255) if not isDark else QColor(45, 45, 45)
            r = self.RADIUS
            self.setRect(-r, -r, 2 * r, 2 * r)

        self.setPen(QPen(borderColor, 2.0))
        self.setBrush(QBrush(fillColor))
