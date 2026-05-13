# coding: utf-8
"""工作流节点设置面板

提供节点的二级设置面板, 双击节点时弹出, 允许用户调整节点的详细参数.
面板以覆盖层形式展示在画布上方, 包含标题, 描述, 表单字段等.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import (
    QColor, QPainter, QFont, QPainterPath, QPen, QMouseEvent,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout,
    QScrollArea, QSizePolicy, QStackedWidget,
)

from ....common.style_sheet import isDarkTheme, themeColor
from ....common.font import setFont
from ....common.icon import FluentIcon as FIF, FluentIconBase
from ..button import TransparentToolButton, PushButton, PrimaryPushButton
from ..label import (
    CaptionLabel, StrongBodyLabel, BodyLabel, SubtitleLabel,
)
from ..line_edit import LineEdit
from ..combo_box import ComboBox
from ..switch_button import SwitchButton
from ..line_edit import PlainTextEdit
from ..scroll_area import SmoothScrollArea
from .workflow_model import NodeData
from .workflow_node_registry import resolveNodeType, NodeTypeInfo


__all__ = [
    'WorkflowNodeSettings',
    'NodeSettingsField',
    'NodeSettingsFactory',
]


# 设置字段工厂函数签名: (fieldDef, value, parent) -> QWidget
NodeSettingsFactory = Callable[[dict, Any, Optional[QWidget]], QWidget]


class NodeSettingsField:
    """节点设置字段定义

    Attributes:
        key:         属性键名
        label:       显示标签
        field_type:  字段类型 (text, textarea, combo, switch, number)
        options:     下拉选项列表 (combo 类型)
        placeholder: 占位文本
        required:    是否必填
        description: 字段描述
    """

    def __init__(self, key: str, label: str, field_type: str = 'text',
                 options: List[str] = None, placeholder: str = '',
                 required: bool = False, description: str = ''):
        self.key = key
        self.label = label
        self.field_type = field_type
        self.options = options or []
        self.placeholder = placeholder
        self.required = required
        self.description = description


class _SettingsFieldWidget(QFrame):
    """单个设置字段的容器 widget"""

    valueChanged = Signal(str, object)  # key, value

    def __init__(self, fieldDef: NodeSettingsField, value: Any = None, parent=None):
        super().__init__(parent)
        self._field = fieldDef
        self._value = value
        self._initLayout()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        # Label
        labelText = self._field.label
        if self._field.required:
            labelText += ' *'

        self._label = CaptionLabel(labelText, self)
        if self._field.required:
            self._label.setTextColor(QColor(200, 50, 50), QColor(255, 100, 100))
        else:
            self._label.setTextColor(QColor(120, 120, 120), QColor(160, 160, 160))
        layout.addWidget(self._label)

        # Description
        if self._field.description:
            descLabel = CaptionLabel(self._field.description, self)
            descLabel.setTextColor(QColor(100, 100, 100), QColor(140, 140, 140))
            layout.addWidget(descLabel)

        # Field widget
        self._fieldWidget = self._createFieldWidget()
        if self._fieldWidget:
            layout.addWidget(self._fieldWidget)

    def _createFieldWidget(self) -> Optional[QWidget]:
        ft = self._field.field_type

        if ft == 'text':
            edit = LineEdit(self)
            edit.setPlaceholderText(self._field.placeholder)
            if self._value is not None:
                edit.setText(str(self._value))
            edit.textChanged.connect(
                lambda t: self.valueChanged.emit(self._field.key, t)
            )
            return edit

        elif ft == 'textarea':
            edit = PlainTextEdit(self)
            edit.setPlaceholderText(self._field.placeholder)
            if self._value is not None:
                edit.setPlainText(str(self._value))
            edit.setFixedHeight(100)
            edit.textChanged.connect(
                lambda: self.valueChanged.emit(
                    self._field.key, edit.toPlainText()
                )
            )
            return edit

        elif ft == 'combo':
            combo = ComboBox(self)
            combo.addItems(self._field.options)
            if self._value and str(self._value) in self._field.options:
                combo.setCurrentText(str(self._value))
            combo.currentTextChanged.connect(
                lambda t: self.valueChanged.emit(self._field.key, t)
            )
            return combo

        elif ft == 'switch':
            switchLayout = QHBoxLayout()
            switchLayout.setContentsMargins(0, 0, 0, 0)
            switch = SwitchButton(self)
            switch.setChecked(bool(self._value) if self._value is not None else False)
            switch.checkedChanged.connect(
                lambda c: self.valueChanged.emit(self._field.key, c)
            )
            container = QWidget(self)
            container.setLayout(switchLayout)
            switchLayout.addWidget(switch)
            switchLayout.addStretch(1)
            return container

        elif ft == 'number':
            edit = LineEdit(self)
            edit.setPlaceholderText(self._field.placeholder or '0')
            if self._value is not None:
                edit.setText(str(self._value))
            edit.textChanged.connect(
                lambda t: self._emitNumber(t)
            )
            return edit

        return None

    def _emitNumber(self, text: str):
        try:
            val = float(text) if '.' in text else int(text)
        except (ValueError, TypeError):
            val = 0
        self.valueChanged.emit(self._field.key, val)

    def value(self) -> Any:
        return self._value


class WorkflowNodeSettings(QFrame):
    """工作流节点设置面板

    以覆盖层形式展示在画布上方, 提供节点的详细参数设置.
    支持自定义字段定义和工厂函数.

    Signals:
        closed:                    面板关闭
        settingChanged(str, str, object): nodeId, key, value
        saved(str, dict):          保存按钮点击, nodeId, properties
    """

    closed = Signal()
    settingChanged = Signal(str, str, object)
    saved = Signal(str, dict)

    def __init__(self, parent: QWidget = None):
        """初始化设置面板

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self._nodeData: Optional[NodeData] = None
        self._nodeTypeInfo: Optional[NodeTypeInfo] = None
        self._fields: List[NodeSettingsField] = []
        self._fieldWidgets: List[_SettingsFieldWidget] = []
        self._customFactory: Optional[NodeSettingsFactory] = None
        self._properties: Dict[str, Any] = {}

        # Settings field definitions per node kind
        self._fieldDefinitions: Dict[str, List[NodeSettingsField]] = {}

        self.setMinimumWidth(500)
        self.setMaximumWidth(700)
        self.hide()
        self._initLayout()

    def _initLayout(self):
        """初始化布局"""
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(24, 20, 24, 20)
        self.mainLayout.setSpacing(12)

        # Header
        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(12)

        self._titleLabel = SubtitleLabel("节点设置", self)
        headerLayout.addWidget(self._titleLabel, 1)

        self._closeBtn = TransparentToolButton(FIF.CLOSE, self)
        self._closeBtn.setFixedSize(32, 32)
        self._closeBtn.setIconSize(QSize(12, 12))
        self._closeBtn.clicked.connect(self.close)
        headerLayout.addWidget(self._closeBtn)

        self.mainLayout.addLayout(headerLayout)

        # Description
        self._descLabel = BodyLabel("", self)
        self._descLabel.setWordWrap(True)
        self._descLabel.setTextColor(QColor(140, 140, 140), QColor(180, 180, 180))
        self.mainLayout.addWidget(self._descLabel)

        # Scroll area for fields
        self._scrollArea = SmoothScrollArea(self)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setStyleSheet(
            "SmoothScrollArea { background: transparent; border: none; }"
            "QScrollArea { background: transparent; border: none; }"
        )

        self._scrollContent = QWidget()
        self._scrollContent.setStyleSheet("background: transparent;")
        self._fieldsLayout = QVBoxLayout(self._scrollContent)
        self._fieldsLayout.setContentsMargins(0, 0, 0, 0)
        self._fieldsLayout.setSpacing(8)
        self._fieldsLayout.addStretch(1)

        self._scrollArea.setWidget(self._scrollContent)
        self.mainLayout.addWidget(self._scrollArea, 1)

        # Bottom buttons
        btnLayout = QHBoxLayout()
        btnLayout.setContentsMargins(0, 8, 0, 0)
        btnLayout.addStretch(1)

        self._cancelBtn = PushButton("取消", self)
        self._cancelBtn.setFixedWidth(80)
        self._cancelBtn.clicked.connect(self.close)
        btnLayout.addWidget(self._cancelBtn)

        self._saveBtn = PrimaryPushButton("保存", self)
        self._saveBtn.setFixedWidth(80)
        self._saveBtn.clicked.connect(self._onSave)
        btnLayout.addWidget(self._saveBtn)

        self.mainLayout.addLayout(btnLayout)

    def registerFields(self, kind: str, fields: List[NodeSettingsField]):
        """为指定节点类型注册设置字段定义

        Args:
            kind:   节点类型标识
            fields: 字段定义列表
        """
        self._fieldDefinitions[kind] = fields

    def openForNode(self, nodeData: NodeData):
        """打开设置面板, 展示指定节点的设置

        Args:
            nodeData: 节点数据
        """
        self._nodeData = nodeData
        self._nodeTypeInfo = resolveNodeType(nodeData.kind)
        self._properties = dict(nodeData.properties)

        # Update header
        title = f"节点设置: {nodeData.title}"
        self._titleLabel.setText(title)

        desc = ""
        if self._nodeTypeInfo and hasattr(self._nodeTypeInfo, 'description'):
            desc = getattr(self._nodeTypeInfo, 'description', '')
        self._descLabel.setText(desc)
        self._descLabel.setVisible(bool(desc))

        # Clear existing fields
        self._clearFields()

        # Build fields
        fields = self._fieldDefinitions.get(nodeData.kind, [])
        if fields:
            self._buildFields(fields)
        else:
            # Auto-generate fields from properties
            self._buildAutoFields()

        self.show()
        self.raise_()

    def close(self):
        """关闭面板"""
        self.hide()
        self.closed.emit()

    def _clearFields(self):
        """清空字段 widgets"""
        for fw in self._fieldWidgets:
            self._fieldsLayout.removeWidget(fw)
            fw.deleteLater()
        self._fieldWidgets.clear()

    def _buildFields(self, fields: List[NodeSettingsField]):
        """根据字段定义构建表单

        Args:
            fields: 字段定义列表
        """
        for fieldDef in fields:
            value = self._properties.get(fieldDef.key)
            fw = _SettingsFieldWidget(fieldDef, value, self._scrollContent)
            fw.valueChanged.connect(self._onFieldChanged)
            self._fieldWidgets.append(fw)
            # Insert before stretch
            self._fieldsLayout.insertWidget(
                self._fieldsLayout.count() - 1, fw
            )

    def _buildAutoFields(self):
        """从 properties 自动生成字段"""
        if not self._properties:
            return

        for key, value in self._properties.items():
            # Infer field type
            if isinstance(value, bool):
                ft = 'switch'
            elif isinstance(value, (int, float)):
                ft = 'number'
            elif isinstance(value, str) and len(value) > 50:
                ft = 'textarea'
            else:
                ft = 'text'

            fieldDef = NodeSettingsField(
                key=key,
                label=key.replace('_', ' ').title(),
                field_type=ft,
            )
            fw = _SettingsFieldWidget(fieldDef, value, self._scrollContent)
            fw.valueChanged.connect(self._onFieldChanged)
            self._fieldWidgets.append(fw)
            self._fieldsLayout.insertWidget(
                self._fieldsLayout.count() - 1, fw
            )

    def _onFieldChanged(self, key: str, value: Any):
        """字段值变化回调"""
        self._properties[key] = value
        if self._nodeData:
            self.settingChanged.emit(self._nodeData.id, key, value)

    def _onSave(self):
        """保存按钮点击"""
        if self._nodeData:
            self._nodeData.properties.update(self._properties)
            self.saved.emit(self._nodeData.id, self._properties)
        self.close()

    def paintEvent(self, e):
        """绘制面板背景"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        r = 12

        # Background
        bgColor = QColor(38, 38, 38, 250) if isDark else QColor(255, 255, 255, 250)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(self.rect(), r, r)

        # Border
        borderColor = QColor(70, 70, 70, 150) if isDark else QColor(0, 0, 0, 25)
        painter.setPen(QPen(borderColor, 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), r, r)
