# coding:utf-8
"""
WorkflowCanvas 工作流画布演示

展示内容:
- 丰富的预设节点类型 (触发, 大模型, 数据, 流程控制, 输出, 网络)
- 右侧节点面板 (使用包内 WorkflowNodePanel)
- 双击节点打开设置面板 (使用包内 WorkflowNodeSettings)
- 选中节点后底部工具栏显示删除按钮
- 节点拖拽, 连线, 调整宽度交互
"""
import sys
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QHBoxLayout

from qfluentwidgets import (
    setTheme, Theme, BodyLabel, CaptionLabel,
    isDarkTheme, Action, MessageBoxBase, SubtitleLabel,
    LineEdit, ComboBox, SwitchButton, PlainTextEdit,
    FluentWindow,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets.components.widgets.command_bar import CommandBarView
from qfluentwidgets.components.widgets.workflow import (
    WorkflowCanvas, WorkflowScene, WorkflowZoomControl,
    WorkflowNodePanel,
    WorkflowData, NodeData, EdgeData, PortData, PortDirection,
    NodeTypeInfo, NodeSettingsField,
    registerNodeType, resolveNodeType,
)
from qfluentwidgets.components.widgets.workflow.workflow_model import _new_id
from qfluentwidgets.components.widgets.workflow.workflow_node import WorkflowNode
from qfluentwidgets.components.widgets.workflow.workflow_edge import WorkflowEdge


# ============================================================================
# 节点内容 widget 工厂
# ============================================================================

def _makeFieldRow(label: str, value: str, parent: QWidget) -> QWidget:
    """创建字段行: 标签(小字次要色) + 值(正常字号主色)"""
    row = QFrame(parent)
    row.setStyleSheet("QFrame{background:transparent;}")
    ly = QVBoxLayout(row)
    ly.setContentsMargins(0, 0, 0, 0)
    ly.setSpacing(2)

    lbl = CaptionLabel(label, row)
    # setTextColor(light主题色, dark主题色)
    lbl.setTextColor(QColor(110, 110, 115), QColor(150, 150, 155))
    ly.addWidget(lbl)

    val = BodyLabel(value, row)
    val.setTextColor(QColor(30, 30, 30), QColor(230, 230, 235))
    ly.addWidget(val)

    return row


def _contentFactory(fields: List[tuple]):
    """生成节点内容 widget 工厂函数

    Args:
        fields: [(属性key, 标签文本, 默认值), ...]
    """
    def factory(props: dict, parent=None) -> QWidget:
        w = QFrame(parent)
        w.setStyleSheet("QFrame{background:transparent;}")
        ly = QVBoxLayout(w)
        ly.setContentsMargins(12, 10, 12, 6)
        ly.setSpacing(8)
        for key, label, default in fields:
            ly.addWidget(_makeFieldRow(label, str(props.get(key, default)), w))
        return w
    return factory


# 各类型节点的内容工厂
_triggerContent = _contentFactory([('trigger_type', '触发方式', '手动')])
_llmContent = _contentFactory([('model', '模型', 'GPT-4o'), ('temperature', '温度', 0.7)])
_dataContent = _contentFactory([('source', '数据来源', '数据库')])
_condContent = _contentFactory([('condition', '条件', '...')])
_httpContent = _contentFactory([('method', '方法', 'GET'), ('url', 'URL', '')])
_outputContent = _contentFactory([('output_type', '输出类型', '消息')])
_transformContent = _contentFactory([('transform_type', '转换类型', 'JSON')])
_codeContent = _contentFactory([('language', '语言', 'Python')])


# ============================================================================
# 注册预设节点类型
# ============================================================================

def _registerAll():
    """注册所有预设节点类型"""
    types = [
        ('manual_trigger', '手动触发', FIF.PLAY_SOLID, QColor(76,175,80), 'trigger',
         '手动启动工作流', [PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _triggerContent),
        ('schedule_trigger', '定时触发', FIF.DATE_TIME, QColor(76,175,80), 'trigger',
         '按计划定时触发', [PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _triggerContent),
        ('webhook_trigger', 'Webhook', FIF.LINK, QColor(76,175,80), 'trigger',
         'HTTP 回调触发', [PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _triggerContent),
        ('llm_chat', '大模型对话', FIF.CHAT, QColor(233,30,99), 'ai',
         '与大语言模型对话', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _llmContent),
        ('embedding', '文本嵌入', FIF.DICTIONARY, QColor(233,30,99), 'ai',
         '生成文本向量', [
             PortData(id='i', name='文本', direction=PortDirection.INPUT),
             PortData(id='o', name='向量', direction=PortDirection.OUTPUT)], _llmContent),
        ('knowledge_base', '知识库检索', FIF.BOOK_SHELF, QColor(233,30,99), 'ai',
         '检索知识库文档', [
             PortData(id='i', name='查询', direction=PortDirection.INPUT),
             PortData(id='o', name='结果', direction=PortDirection.OUTPUT)], _llmContent),
        ('database_query', '数据库查询', FIF.LIBRARY, QColor(255,152,0), 'data',
         '执行 SQL 查询', [
             PortData(id='i', name='参数', direction=PortDirection.INPUT),
             PortData(id='o', name='结果', direction=PortDirection.OUTPUT)], _dataContent),
        ('file_read', '文件读取', FIF.DOCUMENT, QColor(255,152,0), 'data',
         '读取文件内容', [PortData(id='o', name='内容', direction=PortDirection.OUTPUT)], _dataContent),
        ('variable_store', '变量存储', FIF.TAG, QColor(255,152,0), 'data',
         '存储/读取变量', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _dataContent),
        ('condition', '条件分支', FIF.CARE_RIGHT_SOLID, QColor(0,188,212), 'flow',
         '根据条件分支', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='t', name='是', direction=PortDirection.OUTPUT),
             PortData(id='f', name='否', direction=PortDirection.OUTPUT)], _condContent),
        ('loop', '循环迭代', FIF.SYNC, QColor(0,188,212), 'flow',
         '遍历列表元素', [
             PortData(id='i', name='列表', direction=PortDirection.INPUT),
             PortData(id='b', name='元素', direction=PortDirection.OUTPUT),
             PortData(id='d', name='完成', direction=PortDirection.OUTPUT)], _condContent),
        ('delay', '延时等待', FIF.HISTORY, QColor(0,188,212), 'flow',
         '等待后继续', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _condContent),
        ('http_request', 'HTTP 请求', FIF.GLOBE, QColor(63,81,181), 'network',
         '发送 HTTP 请求', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='响应', direction=PortDirection.OUTPUT)], _httpContent),
        ('email_send', '发送邮件', FIF.MAIL, QColor(63,81,181), 'network',
         'SMTP 发送邮件', [
             PortData(id='i', name='内容', direction=PortDirection.INPUT),
             PortData(id='o', name='状态', direction=PortDirection.OUTPUT)], _httpContent),
        ('json_transform', 'JSON 转换', FIF.CODE, QColor(255,87,34), 'transform',
         '转换 JSON 数据', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _transformContent),
        ('code_exec', '代码执行', FIF.COMMAND_PROMPT, QColor(255,87,34), 'transform',
         '执行自定义代码', [
             PortData(id='i', name='输入', direction=PortDirection.INPUT),
             PortData(id='o', name='输出', direction=PortDirection.OUTPUT)], _codeContent),
        ('text_template', '文本模板', FIF.EDIT, QColor(255,87,34), 'transform',
         '渲染文本模板', [
             PortData(id='i', name='变量', direction=PortDirection.INPUT),
             PortData(id='o', name='文本', direction=PortDirection.OUTPUT)], _transformContent),
        ('message_output', '消息输出', FIF.MESSAGE, QColor(96,125,139), 'output',
         '发送消息', [PortData(id='i', name='输入', direction=PortDirection.INPUT)], _outputContent),
        ('file_write', '文件写入', FIF.SAVE_AS, QColor(96,125,139), 'output',
         '写入文件', [PortData(id='i', name='内容', direction=PortDirection.INPUT)], _outputContent),
    ]
    for kind, title, icon, color, cat, desc, ports, factory in types:
        registerNodeType(NodeTypeInfo(
            kind=kind, title=title, icon=icon, color=color,
            category=cat, description=desc, default_ports=ports,
            widget_factory=factory,
        ))


# ============================================================================
# 设置字段定义
# ============================================================================

SETTINGS_FIELDS: Dict[str, List[NodeSettingsField]] = {
    'manual_trigger': [
        NodeSettingsField('trigger_type', '触发方式', 'combo', options=['手动', '事件触发', '消息触发']),
    ],
    'schedule_trigger': [
        NodeSettingsField('trigger_type', '计划类型', 'combo', options=['Cron', '固定间隔', '每日']),
        NodeSettingsField('schedule', '表达式', 'text', placeholder='*/5 * * * *', required=True),
    ],
    'webhook_trigger': [
        NodeSettingsField('trigger_type', '方法', 'combo', options=['POST', 'GET', 'PUT']),
        NodeSettingsField('path', '路径', 'text', placeholder='/api/webhook', required=True),
    ],
    'llm_chat': [
        NodeSettingsField('model', '模型', 'combo',
                         options=['GPT-4o', 'GPT-4o-mini', 'Claude-3.5-Sonnet', 'DeepSeek-V3'], required=True),
        NodeSettingsField('temperature', '温度', 'number', placeholder='0.7'),
        NodeSettingsField('system_prompt', '系统提示词', 'textarea', placeholder='你是一个有帮助的助手...'),
        NodeSettingsField('stream', '流式输出', 'switch'),
    ],
    'embedding': [
        NodeSettingsField('model', '模型', 'combo',
                         options=['text-embedding-3-small', 'bge-large-zh-v1.5'], required=True),
    ],
    'knowledge_base': [
        NodeSettingsField('knowledge_base', '知识库', 'combo',
                         options=['默认知识库', '产品文档', '常见问题'], required=True),
        NodeSettingsField('top_k', 'Top-K', 'number', placeholder='5'),
    ],
    'database_query': [
        NodeSettingsField('source', '数据源', 'combo',
                         options=['PostgreSQL', 'MySQL', 'MongoDB'], required=True),
        NodeSettingsField('query', '查询', 'textarea', placeholder='SELECT * FROM ...', required=True),
    ],
    'file_read': [
        NodeSettingsField('source', '来源', 'combo', options=['本地文件', 'S3', 'URL']),
        NodeSettingsField('path', '路径', 'text', placeholder='/data/input.csv', required=True),
    ],
    'variable_store': [
        NodeSettingsField('source', '操作', 'combo', options=['设置', '获取', '删除']),
        NodeSettingsField('variable_name', '变量名', 'text', placeholder='my_var', required=True),
    ],
    'condition': [
        NodeSettingsField('condition', '条件', 'textarea', placeholder='result.ok == true', required=True),
    ],
    'loop': [
        NodeSettingsField('condition', '类型', 'combo', options=['遍历列表', 'While', '计数']),
        NodeSettingsField('max_iterations', '最大次数', 'number', placeholder='100'),
    ],
    'delay': [
        NodeSettingsField('condition', '类型', 'combo', options=['固定', '随机']),
        NodeSettingsField('duration_ms', '时长(ms)', 'number', placeholder='1000', required=True),
    ],
    'http_request': [
        NodeSettingsField('method', '方法', 'combo', options=['GET', 'POST', 'PUT', 'DELETE'], required=True),
        NodeSettingsField('url', 'URL', 'text', placeholder='https://api.example.com', required=True),
        NodeSettingsField('body', '请求体', 'textarea', placeholder='{}'),
    ],
    'email_send': [
        NodeSettingsField('method', '协议', 'combo', options=['SMTP', 'SendGrid', 'SES']),
        NodeSettingsField('url', '收件人', 'text', placeholder='user@example.com', required=True),
    ],
    'json_transform': [
        NodeSettingsField('transform_type', '类型', 'combo', options=['解析', 'JMESPath', '扁平化']),
        NodeSettingsField('expression', '表达式', 'textarea', placeholder='$.data[*].name'),
    ],
    'code_exec': [
        NodeSettingsField('language', '语言', 'combo', options=['Python', 'JavaScript'], required=True),
        NodeSettingsField('code', '代码', 'textarea', placeholder='def main(input):\n    return input', required=True),
    ],
    'text_template': [
        NodeSettingsField('transform_type', '引擎', 'combo', options=['Jinja2', 'Mustache']),
        NodeSettingsField('template', '模板', 'textarea', placeholder='你好 {{name}}', required=True),
    ],
    'message_output': [
        NodeSettingsField('output_type', '类型', 'combo', options=['消息', '通知', '日志'], required=True),
        NodeSettingsField('channel', '频道', 'text', placeholder='#general'),
    ],
    'file_write': [
        NodeSettingsField('output_type', '模式', 'combo', options=['覆盖', '追加']),
        NodeSettingsField('path', '路径', 'text', placeholder='/output/result.json', required=True),
    ],
}


# ============================================================================
# 节点设置对话框 (MessageBoxBase)
# ============================================================================

class NodeSettingsBox(MessageBoxBase):
    """节点设置对话框"""

    def __init__(self, nodeData: NodeData, fields: List[NodeSettingsField], parent=None):
        super().__init__(parent)
        self._nodeData = nodeData
        self._properties = dict(nodeData.properties)
        self._widgets: Dict[str, QWidget] = {}

        typeInfo = resolveNodeType(nodeData.kind)

        self.titleLabel = SubtitleLabel(nodeData.title, self)
        self.viewLayout.addWidget(self.titleLabel)

        if typeInfo and typeInfo.description:
            desc = CaptionLabel(typeInfo.description, self)
            desc.setTextColor(QColor(120, 120, 125), QColor(160, 160, 165))
            self.viewLayout.addWidget(desc)

        self.viewLayout.addSpacing(8)

        for f in fields:
            lbl = CaptionLabel(f.label + (' *' if f.required else ''), self)
            lbl.setTextColor(QColor(100, 100, 105), QColor(160, 160, 165))
            self.viewLayout.addWidget(lbl)
            w = self._makeField(f, self._properties.get(f.key))
            if w:
                self.viewLayout.addWidget(w)
                self._widgets[f.key] = w
            self.viewLayout.addSpacing(4)

        self.yesButton.setText('保存')
        self.cancelButton.setText('取消')
        self.widget.setMinimumWidth(400)

    def _makeField(self, f: NodeSettingsField, value):
        if f.field_type == 'text':
            e = LineEdit(self)
            e.setPlaceholderText(f.placeholder)
            if value is not None:
                e.setText(str(value))
            return e
        elif f.field_type == 'textarea':
            e = PlainTextEdit(self)
            e.setPlaceholderText(f.placeholder)
            if value is not None:
                e.setPlainText(str(value))
            e.setFixedHeight(80)
            return e
        elif f.field_type == 'combo':
            c = ComboBox(self)
            c.addItems(f.options)
            if value and str(value) in f.options:
                c.setCurrentText(str(value))
            return c
        elif f.field_type == 'switch':
            from PySide6.QtWidgets import QHBoxLayout as _HLy
            container = QWidget(self)
            ly = _HLy(container)
            ly.setContentsMargins(0, 0, 0, 0)
            sw = SwitchButton(container)
            sw.setChecked(bool(value) if value is not None else False)
            ly.addWidget(sw)
            ly.addStretch(1)
            return container
        elif f.field_type == 'number':
            e = LineEdit(self)
            e.setPlaceholderText(f.placeholder or '0')
            if value is not None:
                e.setText(str(value))
            return e
        return None

    def getProperties(self) -> Dict:
        fields = SETTINGS_FIELDS.get(self._nodeData.kind, [])
        for f in fields:
            w = self._widgets.get(f.key)
            if not w:
                continue
            if f.field_type in ('text', 'number'):
                self._properties[f.key] = w.text()
            elif f.field_type == 'textarea':
                self._properties[f.key] = w.toPlainText()
            elif f.field_type == 'combo':
                self._properties[f.key] = w.currentText()
            elif f.field_type == 'switch':
                sw = w.layout().itemAt(0).widget()
                self._properties[f.key] = sw.isChecked()
        return self._properties


# ============================================================================
# 构建示例工作流
# ============================================================================

def _buildSampleWorkflow() -> WorkflowData:
    trigger_id, llm_id, cond_id, http_id, out_id = (
        'n_trigger', 'n_llm', 'n_cond', 'n_http', 'n_out')

    nodes = [
        NodeData(id=trigger_id, kind='manual_trigger', title='开始',
                 x=50, y=150, width=220, properties={'trigger_type': '手动'},
                 ports=[PortData(id='p1', name='输出', direction=PortDirection.OUTPUT)]),
        NodeData(id=llm_id, kind='llm_chat', title='AI 分析',
                 x=380, y=100, width=260,
                 properties={'model': 'GPT-4o', 'temperature': 0.7,
                             'system_prompt': '分析输入数据', 'stream': False},
                 ports=[PortData(id='p2', name='输入', direction=PortDirection.INPUT),
                        PortData(id='p3', name='输出', direction=PortDirection.OUTPUT)]),
        NodeData(id=cond_id, kind='condition', title='检查结果',
                 x=750, y=120, width=240,
                 properties={'condition': 'result.confidence > 0.8'},
                 ports=[PortData(id='p4', name='输入', direction=PortDirection.INPUT),
                        PortData(id='p5', name='是', direction=PortDirection.OUTPUT),
                        PortData(id='p6', name='否', direction=PortDirection.OUTPUT)]),
        NodeData(id=http_id, kind='http_request', title='通知 API',
                 x=1100, y=50, width=240,
                 properties={'method': 'POST', 'url': 'https://api.notify.io/send'},
                 ports=[PortData(id='p7', name='输入', direction=PortDirection.INPUT),
                        PortData(id='p8', name='响应', direction=PortDirection.OUTPUT)]),
        NodeData(id=out_id, kind='message_output', title='发送结果',
                 x=1100, y=280, width=220,
                 properties={'output_type': '消息', 'channel': '#results'},
                 ports=[PortData(id='p9', name='输入', direction=PortDirection.INPUT)]),
    ]
    edges = [
        EdgeData(id='e1', source_node=trigger_id, source_port='p1',
                 target_node=llm_id, target_port='p2'),
        EdgeData(id='e2', source_node=llm_id, source_port='p3',
                 target_node=cond_id, target_port='p4'),
        EdgeData(id='e3', source_node=cond_id, source_port='p5',
                 target_node=http_id, target_port='p7'),
        EdgeData(id='e4', source_node=cond_id, source_port='p6',
                 target_node=out_id, target_port='p9'),
    ]
    return WorkflowData(id='demo', name='AI 分析流水线', nodes=nodes, edges=edges)


# ============================================================================
# Demo 主窗口
# ============================================================================

class _WorkflowPage(QWidget):
    """工作流画布页面 (作为 FluentWindow 的子界面)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('workflowPage')

        self._selectedNodeId: Optional[str] = None

        self._initLayout()
        self._initToolbar()
        self._initZoomControl()
        self._initNodePanel()
        self._initSettingsPanel()
        self._loadSample()
        self._connectSignals()

    def _initLayout(self):
        """初始化布局 - 画布全屏"""
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self._canvas = WorkflowCanvas(self)
        self.mainLayout.addWidget(self._canvas)

    def _initToolbar(self):
        """初始化底部工具栏"""
        self._toolbar = CommandBarView(self)
        self._toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toolbar.setButtonTight(False)
        self._toolbar.setIconSize(QSize(16, 16))

        self._saveAction = Action(FIF.SAVE, '保存', self)
        self._undoAction = Action(FIF.RETURN, '撤销', self)
        self._redoAction = Action(FIF.SYNC, '重做', self)
        self._previewAction = Action(FIF.PLAY, '预览', self)
        self._deleteAction = Action(FIF.DELETE, '删除选中', self)
        self._deleteAction.setVisible(False)

        self._toolbar.addAction(self._saveAction)
        self._toolbar.addAction(self._undoAction)
        self._toolbar.addAction(self._redoAction)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._previewAction)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._deleteAction)

        self._toolbar.resizeToSuitableWidth()
        self._toolbar.setFixedWidth(self._toolbar.suitableWidth() + 12)

        self._saveAction.triggered.connect(self._onSave)
        self._previewAction.triggered.connect(self._onPreview)
        self._deleteAction.triggered.connect(self._onDelete)

    def _initZoomControl(self):
        """初始化缩放控制"""
        self._zoomControl = WorkflowZoomControl(self)
        self._zoomControl.zoomInClicked.connect(self._canvas.zoomIn)
        self._zoomControl.zoomOutClicked.connect(self._canvas.zoomOut)
        self._zoomControl.fitClicked.connect(self._canvas.zoomToFit)
        self._zoomControl.resetClicked.connect(self._canvas.resetZoom)

    def _initNodePanel(self):
        """初始化右侧节点面板 (使用包内 WorkflowNodePanel)"""
        self._nodePanel = WorkflowNodePanel(self)

        nodes = [
            ('manual_trigger', 'trigger', '手动启动工作流'),
            ('schedule_trigger', 'trigger', '按计划定时触发'),
            ('webhook_trigger', 'trigger', 'HTTP 回调触发'),
            ('llm_chat', 'ai', '与大语言模型对话'),
            ('embedding', 'ai', '生成文本向量'),
            ('knowledge_base', 'ai', '检索知识库文档'),
            ('database_query', 'data', '执行 SQL 查询'),
            ('file_read', 'data', '读取文件内容'),
            ('variable_store', 'data', '存储/读取变量'),
            ('condition', 'flow', '根据条件分支'),
            ('loop', 'flow', '遍历列表元素'),
            ('delay', 'flow', '等待后继续'),
            ('http_request', 'network', '发送 HTTP 请求'),
            ('email_send', 'network', 'SMTP 发送邮件'),
            ('json_transform', 'transform', '转换 JSON 数据'),
            ('code_exec', 'transform', '执行自定义代码'),
            ('text_template', 'transform', '渲染文本模板'),
            ('message_output', 'output', '发送消息'),
            ('file_write', 'output', '写入文件'),
        ]
        for kind, cat, desc in nodes:
            self._nodePanel.addNodeType(kind, cat, desc)

        self._nodePanel.nodeTypeClicked.connect(self._onAddNode)

    def _initSettingsPanel(self):
        """设置字段已在 SETTINGS_FIELDS 中定义, 双击时用 MessageBox 弹出"""
        pass

    def _loadSample(self):
        self._canvas.loadWorkflow(_buildSampleWorkflow())

    def _connectSignals(self):
        """连接场景信号"""
        scene = self._canvas.workflowScene()
        scene.nodeDoubleClicked.connect(self._onNodeDoubleClicked)
        scene.selectionChanged.connect(self._onSelectionChanged)

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _onSelectionChanged(self):
        """选中项变化"""
        scene = self._canvas.workflowScene()
        selected = scene.selectedItems()

        hasSelection = False
        self._selectedNodeId = None

        for item in selected:
            if isinstance(item, WorkflowNode):
                self._selectedNodeId = item.nodeId
                hasSelection = True
                break
            elif isinstance(item, WorkflowEdge):
                hasSelection = True
                break

        self._deleteAction.setVisible(hasSelection)
        self._toolbar.resizeToSuitableWidth()
        self._toolbar.setFixedWidth(self._toolbar.suitableWidth() + 12)
        self._repositionOverlays()

    def _onDelete(self):
        """删除选中的节点或连线"""
        scene = self._canvas.workflowScene()
        for item in list(scene.selectedItems()):
            if isinstance(item, WorkflowNode):
                scene.removeNode(item.nodeId)
            elif isinstance(item, WorkflowEdge):
                scene.removeEdge(item.edgeId)

        self._deleteAction.setVisible(False)
        self._toolbar.resizeToSuitableWidth()
        self._toolbar.setFixedWidth(self._toolbar.suitableWidth() + 12)
        self._repositionOverlays()

    def _onAddNode(self, kind: str):
        """面板点击 - 添加新节点"""
        typeInfo = resolveNodeType(kind)
        if not typeInfo:
            return

        ports = [
            PortData(id=_new_id(), name=p.name,
                     direction=p.direction, data_type=p.data_type)
            for p in typeInfo.default_ports
        ]
        nodeData = NodeData(
            id=_new_id(), kind=kind, title=typeInfo.title,
            x=400, y=300, width=240, properties={}, ports=ports,
        )
        self._canvas.workflowScene().addNodeFromData(nodeData)

    def _onNodeDoubleClicked(self, nodeId: str):
        """双击节点 - 打开 MessageBox 设置对话框"""
        scene = self._canvas.workflowScene()
        data = scene.workflowData()
        if not data:
            return
        nodeData = data.findNode(nodeId)
        if not nodeData:
            return

        fields = SETTINGS_FIELDS.get(nodeData.kind, [])
        if not fields:
            return

        box = NodeSettingsBox(nodeData, fields, self)
        if box.exec():
            newProps = box.getProperties()
            nodeData.properties.update(newProps)
            print(f"[已保存] {nodeData.title}: {newProps}")

    def _onSave(self):
        scene = self._canvas.workflowScene()
        data = scene.workflowData()
        if data:
            import json
            print(f"[已保存]\n{json.dumps(data.toDict(), indent=2, ensure_ascii=False)[:500]}...")

    def _onPreview(self):
        print("[预览] 工作流预览已触发")

    # ------------------------------------------------------------------
    # 布局
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._repositionOverlays()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self._repositionOverlays)

    def _repositionOverlays(self):
        """定位浮动组件"""
        w = self.width()
        h = self.height()

        # 节点面板 - 右侧浮动卡片
        panelW = 280
        panelH = h - 40
        self._nodePanel.setFixedSize(panelW, panelH)
        self._nodePanel.move(w - panelW - 16, 20)
        self._nodePanel.raise_()

        # 工具栏 - 底部居中
        tw = self._toolbar.width()
        th = self._toolbar.height()
        self._toolbar.move((w - tw) // 2, h - th - 20)
        self._toolbar.raise_()

        # 缩放 - 左下角
        self._zoomControl.move(16, h - self._zoomControl.height() - 20)
        self._zoomControl.raise_()


class Demo(FluentWindow):
    """WorkflowCanvas 演示窗口 (FluentWindow)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('WorkflowCanvas - 工作流画布演示')
        self.resize(1400, 850)

        _registerAll()

        # 添加工作流页面
        self._workflowPage = _WorkflowPage(self)
        self.addSubInterface(
            self._workflowPage, FIF.DEVELOPER_TOOLS, '工作流',
            isTransparent=True,
        )

        # 隐藏导航栏 (单页面演示)
        self.navigationInterface.hide()
        self.widgetLayout.setContentsMargins(0, 48, 0, 0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
