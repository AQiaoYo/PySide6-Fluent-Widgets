# coding: utf-8
"""工作流场景管理

提供 QGraphicsScene 子类, 管理节点和连线的创建/删除/查找,
处理端口拖拽连线交互
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QGraphicsItem

from ....common.style_sheet import isDarkTheme
from .workflow_model import (
    WorkflowData, NodeData, EdgeData, PortData, PortDirection, _new_id
)
from .workflow_node import WorkflowNode
from .workflow_port import WorkflowPort
from .workflow_edge import WorkflowEdge, WorkflowDragEdge
from .workflow_node_registry import resolveNodeType


__all__ = ['WorkflowScene']


class WorkflowScene(QGraphicsScene):
    """工作流场景

    管理所有节点和连线的生命周期, 处理端口拖拽连线交互

    Signals:
        nodeAdded:     节点添加后发射 (nodeId)
        nodeRemoved:   节点移除后发射 (nodeId)
        edgeAdded:     连线添加后发射 (edgeId)
        edgeRemoved:   连线移除后发射 (edgeId)
        nodeMoved:     节点移动后发射 (nodeId, x, y)
    """

    nodeAdded = Signal(str)
    nodeRemoved = Signal(str)
    edgeAdded = Signal(str)
    edgeRemoved = Signal(str)
    nodeMoved = Signal(str, float, float)
    nodeDoubleClicked = Signal(str)         # 节点双击, 参数为 nodeId

    def __init__(self, parent=None):
        """初始化场景

        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self._workflowData: Optional[WorkflowData] = None
        self._nodeItems: Dict[str, WorkflowNode] = {}
        self._edgeItems: Dict[str, WorkflowEdge] = {}

        # Drag edge state
        self._dragEdge: Optional[WorkflowDragEdge] = None
        self._dragSourcePort: Optional[WorkflowPort] = None

        self.setSceneRect(-5000, -5000, 10000, 10000)

    def workflowData(self) -> Optional[WorkflowData]:
        """获取当前工作流数据

        Returns:
            WorkflowData 或 None
        """
        return self._workflowData

    def loadWorkflow(self, data: WorkflowData):
        """加载工作流数据, 创建所有节点和连线

        Args:
            data: 工作流数据
        """
        self.clear()
        self._nodeItems.clear()
        self._edgeItems.clear()
        self._workflowData = data
        self._pendingEdges = list(data.edges)

        # Create nodes
        for nodeData in data.nodes:
            self._createNodeItem(nodeData)

        # Defer edge creation to allow nodes to finish layout (ports use QTimer.singleShot)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._createPendingEdges)

    def _createPendingEdges(self):
        """创建延迟的连线 (等待节点端口就绪)"""
        for edgeData in self._pendingEdges:
            self._createEdgeItem(edgeData)
        self._pendingEdges = []

    def clear(self):
        """清空场景"""
        super().clear()
        self._nodeItems.clear()
        self._edgeItems.clear()
        self._dragEdge = None
        self._dragSourcePort = None

    def addNodeFromData(self, nodeData: NodeData) -> Optional[WorkflowNode]:
        """添加节点

        Args:
            nodeData: 节点数据

        Returns:
            创建的 WorkflowNode 或 None
        """
        if self._workflowData:
            self._workflowData.addNode(nodeData)

        item = self._createNodeItem(nodeData)
        if item:
            self.nodeAdded.emit(nodeData.id)
        return item

    def removeNode(self, nodeId: str):
        """移除节点及其关联连线

        Args:
            nodeId: 节点 ID
        """
        # Remove connected edges first
        edgesToRemove = [
            eid for eid, edge in self._edgeItems.items()
            if edge.edgeData.source_node == nodeId or edge.edgeData.target_node == nodeId
        ]
        for eid in edgesToRemove:
            self.removeEdge(eid)

        # Remove node item
        item = self._nodeItems.pop(nodeId, None)
        if item:
            self.removeItem(item)

        if self._workflowData:
            self._workflowData.removeNode(nodeId)

        self.nodeRemoved.emit(nodeId)

    def addEdgeFromData(self, edgeData: EdgeData) -> Optional[WorkflowEdge]:
        """添加连线

        Args:
            edgeData: 连线数据

        Returns:
            创建的 WorkflowEdge 或 None
        """
        if self._workflowData:
            self._workflowData.addEdge(edgeData)

        item = self._createEdgeItem(edgeData)
        if item:
            self.edgeAdded.emit(edgeData.id)
        return item

    def removeEdge(self, edgeId: str):
        """移除连线

        Args:
            edgeId: 连线 ID
        """
        item = self._edgeItems.pop(edgeId, None)
        if item:
            self.removeItem(item)

        if self._workflowData:
            self._workflowData.removeEdge(edgeId)

        self.edgeRemoved.emit(edgeId)

    def getNodeItem(self, nodeId: str) -> Optional[WorkflowNode]:
        """获取节点 item

        Args:
            nodeId: 节点 ID

        Returns:
            WorkflowNode 或 None
        """
        return self._nodeItems.get(nodeId)

    def getEdgeItem(self, edgeId: str) -> Optional[WorkflowEdge]:
        """获取连线 item

        Args:
            edgeId: 连线 ID

        Returns:
            WorkflowEdge 或 None
        """
        return self._edgeItems.get(edgeId)

    def updateEdgesForNode(self, nodeId: str):
        """更新与指定节点关联的所有连线路径

        Args:
            nodeId: 节点 ID
        """
        for edge in self._edgeItems.values():
            if edge.edgeData.source_node == nodeId or edge.edgeData.target_node == nodeId:
                edge.updatePath()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _createNodeItem(self, nodeData: NodeData) -> Optional[WorkflowNode]:
        """创建节点 item 并添加到场景"""
        node = WorkflowNode(nodeData)
        self.addItem(node)
        self._nodeItems[nodeData.id] = node

        # Connect signals
        node.signals.moved.connect(self._onNodeMoved)
        node.signals.closed.connect(self.removeNode)
        node.signals.doubleClicked.connect(self.nodeDoubleClicked)

        return node

    def _createEdgeItem(self, edgeData: EdgeData) -> Optional[WorkflowEdge]:
        """创建连线 item 并添加到场景"""
        # Find source and target ports
        sourceNode = self._nodeItems.get(edgeData.source_node)
        targetNode = self._nodeItems.get(edgeData.target_node)

        if not sourceNode or not targetNode:
            return None

        sourcePort = sourceNode.getPort(edgeData.source_port)
        targetPort = targetNode.getPort(edgeData.target_port)

        if not sourcePort or not targetPort:
            return None

        edge = WorkflowEdge(edgeData, sourcePort, targetPort)
        self.addItem(edge)
        self._edgeItems[edgeData.id] = edge

        return edge

    def _onNodeMoved(self, nodeId: str, x: float, y: float):
        """节点移动回调"""
        self.nodeMoved.emit(nodeId, x, y)

    # ------------------------------------------------------------------
    # Port drag interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """处理鼠标按下 - 检测端口拖拽"""
        # 优先检测端口 - 遍历所有节点的端口判断点击
        scenePos = event.scenePos()
        port = self._findPortAt(scenePos)

        if port:
            # Start drag edge from port
            self._dragSourcePort = port
            startPos = port.centerInScene()
            self._dragEdge = WorkflowDragEdge(startPos)
            self.addItem(self._dragEdge)
            return

        super().mousePressEvent(event)

    def _findPortAt(self, scenePos: QPointF) -> Optional[WorkflowPort]:
        """在指定场景坐标查找端口

        Args:
            scenePos: 场景坐标

        Returns:
            WorkflowPort 或 None
        """
        hitRadius = WorkflowPort.RADIUS + 4
        for node in self._nodeItems.values():
            for port in node.allPorts():
                portCenter = port.centerInScene()
                dx = scenePos.x() - portCenter.x()
                dy = scenePos.y() - portCenter.y()
                if dx * dx + dy * dy <= hitRadius * hitRadius:
                    return port
        return None

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """处理鼠标移动 - 更新拖拽连线"""
        if self._dragEdge:
            self._dragEdge.setEndPos(event.scenePos())
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """处理鼠标释放 - 完成连线或取消"""
        if self._dragEdge and self._dragSourcePort:
            # Check if released on a port
            port = self._findPortAt(event.scenePos())

            if port and port is not self._dragSourcePort:
                self._tryConnect(self._dragSourcePort, port)

            # Remove drag edge
            self.removeItem(self._dragEdge)
            self._dragEdge = None
            self._dragSourcePort = None
            return

        super().mouseReleaseEvent(event)

    def _tryConnect(self, portA: WorkflowPort, portB: WorkflowPort):
        """尝试连接两个端口

        Args:
            portA: 第一个端口
            portB: 第二个端口
        """
        # Determine source (output) and target (input)
        if portA.direction == PortDirection.OUTPUT and portB.direction == PortDirection.INPUT:
            sourcePort, targetPort = portA, portB
        elif portB.direction == PortDirection.OUTPUT and portA.direction == PortDirection.INPUT:
            sourcePort, targetPort = portB, portA
        else:
            # Same direction - cannot connect
            return

        # Get node IDs
        sourceNode = sourcePort.nodeItem
        targetNode = targetPort.nodeItem

        if not isinstance(sourceNode, WorkflowNode) or not isinstance(targetNode, WorkflowNode):
            return

        # Don't connect to self
        if sourceNode.nodeId == targetNode.nodeId:
            return

        # Check if edge already exists
        for edge in self._edgeItems.values():
            if (edge.edgeData.source_port == sourcePort.portId and
                    edge.edgeData.target_port == targetPort.portId):
                return

        # Create edge
        edgeData = EdgeData(
            id=_new_id(),
            source_node=sourceNode.nodeId,
            source_port=sourcePort.portId,
            target_node=targetNode.nodeId,
            target_port=targetPort.portId,
        )
        self.addEdgeFromData(edgeData)

    def keyPressEvent(self, event):
        """处理键盘事件 - Delete 删除选中项"""
        if event.key() == Qt.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, WorkflowNode):
                    self.removeNode(item.nodeId)
                elif isinstance(item, WorkflowEdge):
                    self.removeEdge(item.edgeId)
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Background grid
    # ------------------------------------------------------------------

    def drawBackground(self, painter, rect):
        """绘制网格背景"""
        super().drawBackground(painter, rect)

        isDark = isDarkTheme()
        gridSize = 20
        largeGridSize = 100

        # Small grid
        smallColor = QColor(50, 50, 50, 40) if isDark else QColor(200, 200, 200, 60)
        painter.setPen(QPen(smallColor, 0.5))

        left = int(rect.left()) - (int(rect.left()) % gridSize)
        top = int(rect.top()) - (int(rect.top()) % gridSize)

        lines = []
        x = left
        while x < rect.right():
            lines.append((x, rect.top(), x, rect.bottom()))
            x += gridSize

        y = top
        while y < rect.bottom():
            lines.append((rect.left(), y, rect.right(), y))
            y += gridSize

        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Large grid
        largeColor = QColor(60, 60, 60, 80) if isDark else QColor(180, 180, 180, 80)
        painter.setPen(QPen(largeColor, 1.0))

        left = int(rect.left()) - (int(rect.left()) % largeGridSize)
        top = int(rect.top()) - (int(rect.top()) % largeGridSize)

        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += largeGridSize

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += largeGridSize
