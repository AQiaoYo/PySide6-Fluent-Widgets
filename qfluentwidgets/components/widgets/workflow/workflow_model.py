# coding: utf-8
"""工作流数据模型

定义工作流的节点, 端口, 连线和整体工作流的纯数据结构,
不依赖任何 UI 组件, 便于序列化 / 反序列化为 JSON.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


__all__ = [
    'PortDirection',
    'PortData',
    'NodeData',
    'EdgeData',
    'WorkflowData',
]


def _new_id() -> str:
    """生成唯一 ID (uuid4 hex 前 12 位)."""
    return uuid4().hex[:12]


class PortDirection(Enum):
    """端口方向枚举

    INPUT:  输入端口, 接收来自上游节点的数据
    OUTPUT: 输出端口, 向下游节点发送数据
    """

    INPUT = "input"
    OUTPUT = "output"


@dataclass
class PortData:
    """端口数据

    Attributes:
        id:        端口唯一标识
        name:      端口显示名称
        direction: 端口方向 (INPUT / OUTPUT)
        data_type: 数据类型标识, 用于连线兼容性校验
    """

    id: str = field(default_factory=_new_id)
    name: str = ""
    direction: PortDirection = PortDirection.OUTPUT
    data_type: str = "any"


@dataclass
class NodeData:
    """节点数据

    Attributes:
        id:         节点唯一标识
        kind:       节点类型标识 (对应注册表 key, 如 "trigger" / "llm" / "output")
        title:      节点标题
        x:          画布 x 坐标
        y:          画布 y 坐标
        width:      节点宽度
        properties: 节点属性字典 (表单字段值, 如 {"model": "gpt-5.4"})
        ports:      端口列表
    """

    id: str = field(default_factory=_new_id)
    kind: str = ""
    title: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 240.0
    properties: Dict[str, Any] = field(default_factory=dict)
    ports: List[PortData] = field(default_factory=list)


@dataclass
class EdgeData:
    """连线数据

    Attributes:
        id:          连线唯一标识
        source_node: 源节点 ID
        source_port: 源端口 ID
        target_node: 目标节点 ID
        target_port: 目标端口 ID
    """

    id: str = field(default_factory=_new_id)
    source_node: str = ""
    source_port: str = ""
    target_node: str = ""
    target_port: str = ""


@dataclass
class WorkflowData:
    """工作流数据 (可序列化为 JSON)

    Attributes:
        id:          工作流唯一标识
        name:        工作流名称
        description: 工作流描述
        nodes:       节点列表
        edges:       连线列表
    """

    id: str = field(default_factory=_new_id)
    name: str = ""
    description: str = ""
    nodes: List[NodeData] = field(default_factory=list)
    edges: List[EdgeData] = field(default_factory=list)

    def findNode(self, nodeId: str) -> Optional[NodeData]:
        """按 ID 查找节点

        Args:
            nodeId: 节点 ID

        Returns:
            NodeData 或 None
        """
        for node in self.nodes:
            if node.id == nodeId:
                return node
        return None

    def findEdge(self, edgeId: str) -> Optional[EdgeData]:
        """按 ID 查找连线

        Args:
            edgeId: 连线 ID

        Returns:
            EdgeData 或 None
        """
        for edge in self.edges:
            if edge.id == edgeId:
                return edge
        return None

    def addNode(self, node: NodeData) -> None:
        """添加节点

        Args:
            node: 节点数据
        """
        self.nodes.append(node)

    def removeNode(self, nodeId: str) -> None:
        """移除节点及其关联连线

        Args:
            nodeId: 节点 ID
        """
        self.nodes = [n for n in self.nodes if n.id != nodeId]
        self.edges = [
            e for e in self.edges
            if e.source_node != nodeId and e.target_node != nodeId
        ]

    def addEdge(self, edge: EdgeData) -> None:
        """添加连线

        Args:
            edge: 连线数据
        """
        self.edges.append(edge)

    def removeEdge(self, edgeId: str) -> None:
        """移除连线

        Args:
            edgeId: 连线 ID
        """
        self.edges = [e for e in self.edges if e.id != edgeId]

    def toDict(self) -> Dict[str, Any]:
        """序列化为字典

        Returns:
            可 JSON 序列化的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [
                {
                    "id": n.id,
                    "kind": n.kind,
                    "title": n.title,
                    "x": n.x,
                    "y": n.y,
                    "width": n.width,
                    "properties": n.properties,
                    "ports": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "direction": p.direction.value,
                            "data_type": p.data_type,
                        }
                        for p in n.ports
                    ],
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_node": e.source_node,
                    "source_port": e.source_port,
                    "target_node": e.target_node,
                    "target_port": e.target_port,
                }
                for e in self.edges
            ],
        }

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "WorkflowData":
        """从字典反序列化

        Args:
            data: JSON 解析后的字典

        Returns:
            WorkflowData 实例
        """
        nodes = []
        for nd in data.get("nodes", []):
            ports = [
                PortData(
                    id=p["id"],
                    name=p.get("name", ""),
                    direction=PortDirection(p["direction"]),
                    data_type=p.get("data_type", "any"),
                )
                for p in nd.get("ports", [])
            ]
            nodes.append(NodeData(
                id=nd["id"],
                kind=nd["kind"],
                title=nd.get("title", ""),
                x=nd.get("x", 0),
                y=nd.get("y", 0),
                width=nd.get("width", 240),
                properties=nd.get("properties", {}),
                ports=ports,
            ))

        edges = [
            EdgeData(
                id=ed["id"],
                source_node=ed["source_node"],
                source_port=ed["source_port"],
                target_node=ed["target_node"],
                target_port=ed["target_port"],
            )
            for ed in data.get("edges", [])
        ]

        return cls(
            id=data.get("id", _new_id()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            nodes=nodes,
            edges=edges,
        )
