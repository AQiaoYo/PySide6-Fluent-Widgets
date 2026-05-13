# coding: utf-8
"""工作流节点类型注册表

提供可扩展的节点类型注册机制, 允许用户注册自定义节点类型,
每种节点类型包含元信息 (图标/颜色/默认端口) 和内容 widget 工厂函数.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QWidget

from ....common.icon import FluentIconBase
from .workflow_model import PortData, PortDirection


__all__ = [
    'NodeTypeInfo',
    'NodeWidgetFactory',
    'registerNodeType',
    'unregisterNodeType',
    'resolveNodeType',
    'registeredNodeTypes',
]


# 工厂函数签名: (properties: dict, parent: QWidget) -> QWidget
NodeWidgetFactory = Callable[[dict, Optional[QWidget]], QWidget]


@dataclass
class NodeTypeInfo:
    """节点类型元信息

    Attributes:
        kind:           类型标识 (如 "trigger", "llm", "output")
        title:          默认标题
        icon:           节点图标
        color:          标题栏强调色
        default_ports:  默认端口配置
        widget_factory: 创建节点内容 widget 的工厂函数
        category:       分类标识 (如 "trigger", "bot", "ai", "data", "flow")
        description:    节点功能描述
    """

    kind: str = ""
    title: str = ""
    icon: Union[FluentIconBase, QIcon, str, None] = None
    color: QColor = field(default_factory=lambda: QColor(96, 96, 96))
    default_ports: List[PortData] = field(default_factory=list)
    widget_factory: Optional[NodeWidgetFactory] = None
    category: str = ""
    description: str = ""


_REGISTRY: Dict[str, NodeTypeInfo] = {}


def registerNodeType(info: NodeTypeInfo) -> None:
    """注册节点类型, 同 kind 重复注册会覆盖前者

    Args:
        info: 节点类型元信息
    """
    _REGISTRY[info.kind] = info


def unregisterNodeType(kind: str) -> None:
    """从注册表中移除节点类型, 未注册的 kind 静默忽略

    Args:
        kind: 节点类型标识
    """
    _REGISTRY.pop(kind, None)


def resolveNodeType(kind: str) -> Optional[NodeTypeInfo]:
    """查找节点类型, 未注册时返回 None

    Args:
        kind: 节点类型标识

    Returns:
        NodeTypeInfo 或 None
    """
    return _REGISTRY.get(kind)


def registeredNodeTypes() -> Dict[str, NodeTypeInfo]:
    """返回当前注册表副本 (供调试 / 遍历用)

    Returns:
        注册表字典副本
    """
    return dict(_REGISTRY)
