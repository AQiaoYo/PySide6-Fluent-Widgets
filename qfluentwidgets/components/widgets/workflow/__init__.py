"""工作流画布组件子包

提供可视化工作流编辑器组件, 支持节点拖拽, 连线交互, 缩放平移,
以及可扩展的节点类型注册机制.

主要类:
    * PortDirection         - 端口方向枚举 (INPUT / OUTPUT)
    * PortData             - 端口数据
    * NodeData             - 节点数据
    * EdgeData             - 连线数据
    * WorkflowData         - 工作流数据 (可序列化)
    * NodeTypeInfo         - 节点类型元信息
    * registerNodeType     - 注册节点类型
    * unregisterNodeType   - 注销节点类型
    * resolveNodeType      - 查找节点类型
    * registeredNodeTypes  - 获取所有已注册节点类型
    * WorkflowPort         - 端口 QGraphicsItem
    * WorkflowEdge         - 连线 QGraphicsItem
    * WorkflowNode         - 节点 QGraphicsWidget
    * WorkflowScene        - 工作流场景
    * WorkflowCanvas       - 工作流画布 (主组件)
    * WorkflowToolBar      - 底部工具栏
    * WorkflowZoomControl  - 缩放控制
    * WorkflowNodePanel    - 右侧节点总览面板
    * WorkflowNodeSettings - 节点设置面板
"""

from .workflow_model import (
    PortDirection, PortData, NodeData, EdgeData, WorkflowData,
)
from .workflow_node_registry import (
    NodeTypeInfo, NodeWidgetFactory,
    registerNodeType, unregisterNodeType,
    resolveNodeType, registeredNodeTypes,
)
from .workflow_port import WorkflowPort
from .workflow_edge import WorkflowEdge, WorkflowDragEdge
from .workflow_node import WorkflowNode
from .workflow_scene import WorkflowScene
from .workflow_canvas import WorkflowCanvas
from .workflow_toolbar import WorkflowToolBar
from .workflow_zoom_control import WorkflowZoomControl
from .workflow_node_panel import WorkflowNodePanel, NodePanelItem
from .workflow_node_settings import (
    WorkflowNodeSettings, NodeSettingsField, NodeSettingsFactory,
)


__all__ = [
    'PortDirection', 'PortData', 'NodeData', 'EdgeData', 'WorkflowData',
    'NodeTypeInfo', 'NodeWidgetFactory',
    'registerNodeType', 'unregisterNodeType',
    'resolveNodeType', 'registeredNodeTypes',
    'WorkflowPort',
    'WorkflowEdge', 'WorkflowDragEdge',
    'WorkflowNode',
    'WorkflowScene',
    'WorkflowCanvas',
    'WorkflowToolBar',
    'WorkflowZoomControl',
    'WorkflowNodePanel', 'NodePanelItem',
    'WorkflowNodeSettings', 'NodeSettingsField', 'NodeSettingsFactory',
]
