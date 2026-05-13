# coding: utf-8
"""工作流节点面板

提供右侧节点总览面板, 展示所有已注册的节点类型, 支持搜索和分类筛选,
用户可从面板点击节点类型在画布中创建新节点
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import (
    QColor, QPainter, QFont, QPen, QMouseEvent,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
)

from ....common.style_sheet import isDarkTheme, themeColor
from ....common.font import setFont
from ....common.icon import FluentIcon as FIF, FluentIconBase, drawIcon
from ....common.config import Theme
from ..label import CaptionLabel, StrongBodyLabel, BodyLabel
from ..scroll_area import SmoothScrollArea
from .workflow_node_registry import registeredNodeTypes, NodeTypeInfo


__all__ = ['WorkflowNodePanel', 'NodePanelItem']


class _CategoryBadge(QWidget):
    """节点分类标签

    显示在节点项左侧的实心彩色圆角标识, 白色文字
    """

    def __init__(self, text: str, color: QColor, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = color
        self.setFixedSize(44, 20)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # Solid colored background
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawRoundedRect(self.rect(), 4, 4)

        # White text
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPixelSize(10)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)


class _PanelIconWidget(QWidget):
    """面板图标控件, 自适应主题渲染"""

    def __init__(self, icon=None, parent=None):
        super().__init__(parent)
        self._icon = icon

    def paintEvent(self, e):
        if not self._icon:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        if isinstance(self._icon, FluentIconBase):
            theme = Theme.DARK if isDarkTheme() else Theme.LIGHT
            self._icon.render(painter, self.rect(), theme=theme)
        else:
            drawIcon(self._icon, painter, self.rect())


class NodePanelItem(QFrame):
    """节点面板项

    展示单个节点类型的卡片, 包含分类标签, 标题和描述.
    支持点击发射信号以在画布中创建节点.

    Signals:
        clicked(str): 点击时发射, 参数为节点类型 kind
    """

    clicked = Signal(str)

    def __init__(self, nodeTypeInfo: NodeTypeInfo, category: str = "",
                 categoryColor: QColor = None, parent=None):
        """初始化节点面板项

        Args:
            nodeTypeInfo: 节点类型元信息
            category:     分类名称 (显示在 badge 上)
            categoryColor: 分类颜色
            parent:       父部件
        """
        super().__init__(parent)
        self._info = nodeTypeInfo
        self._category = category
        self._categoryColor = categoryColor or QColor(100, 100, 100)
        self._isHover = False

        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._initLayout()

    def _initLayout(self):
        """初始化布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Category badge (solid color)
        if self._category:
            self._badge = _CategoryBadge(
                self._category, self._categoryColor, self
            )
            layout.addWidget(self._badge)

        # Text area (title + description)
        textLayout = QVBoxLayout()
        textLayout.setContentsMargins(0, 0, 0, 0)
        textLayout.setSpacing(2)

        self._titleLabel = StrongBodyLabel(self._info.title, self)
        setFont(self._titleLabel, 13, QFont.DemiBold)

        desc = getattr(self._info, 'description', '') or self._info.kind
        self._descLabel = CaptionLabel(desc, self)
        # setTextColor(light, dark)
        self._descLabel.setTextColor(
            QColor(100, 100, 105), QColor(150, 150, 155)
        )

        textLayout.addWidget(self._titleLabel)
        textLayout.addWidget(self._descLabel)
        layout.addLayout(textLayout, 1)

    @property
    def kind(self) -> str:
        """节点类型标识"""
        return self._info.kind

    @property
    def nodeTypeInfo(self) -> NodeTypeInfo:
        """节点类型元信息"""
        return self._info

    def setDescription(self, desc: str):
        """设置描述文本

        Args:
            desc: 描述文本
        """
        self._descLabel.setText(desc)

    def enterEvent(self, event):
        self._isHover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._isHover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._info.kind)
        super().mousePressEvent(event)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        r = 6

        if self._isHover:
            bg = QColor(55, 55, 58) if isDark else QColor(0, 0, 0, 15)
        else:
            bg = QColor(0, 0, 0, 0)

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)


class WorkflowNodePanel(QFrame):
    """工作流节点总览面板

    右侧面板, 展示所有已注册的节点类型, 支持搜索和分类筛选.
    用户点击节点项可在画布中创建对应类型的节点.
    不透明背景, 带左侧边框线.

    Signals:
        nodeTypeClicked(str): 节点类型被点击, 参数为 kind
    """

    nodeTypeClicked = Signal(str)

    # 预定义分类及颜色
    CATEGORIES = {
        'trigger': ('触发', QColor(76, 175, 80)),
        'bot': ('机器人', QColor(33, 150, 243)),
        'custom': ('自定义', QColor(156, 39, 176)),
        'data': ('数据', QColor(255, 152, 0)),
        'flow': ('流程', QColor(0, 188, 212)),
        'ai': ('大模型', QColor(233, 30, 99)),
        'network': ('网络', QColor(63, 81, 181)),
        'output': ('输出', QColor(96, 125, 139)),
        'input': ('输入', QColor(139, 195, 74)),
        'transform': ('转换', QColor(255, 87, 34)),
    }

    def __init__(self, parent: QWidget = None):
        """初始化节点面板

        Args:
            parent: 父部件
        """
        super().__init__(parent)
        self._items: List[NodePanelItem] = []
        self._categoryMap: Dict[str, str] = {}  # kind -> category key

        self.setFixedWidth(280)
        self._initLayout()

    def _initLayout(self):
        """初始化布局"""
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 16, 10, 12)
        self.mainLayout.setSpacing(10)

        # Title
        self._titleLabel = StrongBodyLabel("添加节点", self)
        setFont(self._titleLabel, 14, QFont.DemiBold)
        self.mainLayout.addWidget(self._titleLabel)

        # Scroll area for node items
        self._scrollArea = SmoothScrollArea(self)
        self._scrollArea.setWidgetResizable(True)
        self._scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scrollArea.setStyleSheet(
            "SmoothScrollArea{background:transparent;border:none;}"
            "QScrollArea{background:transparent;border:none;}"
            "QWidget#nodePanelScrollContent{background:transparent;}"
        )

        self._scrollContent = QWidget()
        self._scrollContent.setObjectName("nodePanelScrollContent")
        self._scrollLayout = QVBoxLayout(self._scrollContent)
        self._scrollLayout.setContentsMargins(0, 0, 0, 0)
        self._scrollLayout.setSpacing(4)
        self._scrollLayout.addStretch(1)

        self._scrollArea.setWidget(self._scrollContent)
        self.mainLayout.addWidget(self._scrollArea, 1)

    def setTitle(self, title: str):
        """设置面板标题

        Args:
            title: 标题文本
        """
        self._titleLabel.setText(title)

    def refresh(self):
        """刷新面板, 重新从注册表加载所有节点类型"""
        for item in self._items:
            self._scrollLayout.removeWidget(item)
            item.deleteLater()
        self._items.clear()

        registry = registeredNodeTypes()
        for kind, info in registry.items():
            catKey = self._categoryMap.get(kind, '')
            catName = ''
            catColor = QColor(100, 100, 100)

            if catKey and catKey in self.CATEGORIES:
                catName, catColor = self.CATEGORIES[catKey]

            item = NodePanelItem(info, catName, catColor, self._scrollContent)
            item.clicked.connect(self._onItemClicked)
            self._items.append(item)
            self._scrollLayout.insertWidget(
                self._scrollLayout.count() - 1, item
            )

    def addNodeType(self, kind: str, category: str = '', description: str = ''):
        """添加节点类型到面板 (需已在注册表中注册)

        Args:
            kind:        节点类型标识
            category:    分类键 (对应 CATEGORIES 字典)
            description: 描述文本
        """
        self._categoryMap[kind] = category

        from .workflow_node_registry import resolveNodeType
        info = resolveNodeType(kind)
        if not info:
            return

        catName = ''
        catColor = QColor(100, 100, 100)
        if category and category in self.CATEGORIES:
            catName, catColor = self.CATEGORIES[category]

        item = NodePanelItem(info, catName, catColor, self._scrollContent)
        if description:
            item.setDescription(description)
        item.clicked.connect(self._onItemClicked)
        self._items.append(item)
        self._scrollLayout.insertWidget(
            self._scrollLayout.count() - 1, item
        )

    def setCategoryForKind(self, kind: str, category: str):
        """设置节点类型的分类

        Args:
            kind:     节点类型标识
            category: 分类键
        """
        self._categoryMap[kind] = category

    def _onItemClicked(self, kind: str):
        """节点项点击回调"""
        self.nodeTypeClicked.emit(kind)

    def paintEvent(self, e):
        """绘制浮动卡片背景 (不透明, 圆角, 带阴影边框)"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        r = 10

        # Opaque rounded background
        bgColor = QColor(32, 32, 34) if isDark else QColor(255, 255, 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)

        # Border
        borderColor = QColor(60, 60, 60, 100) if isDark else QColor(0, 0, 0, 20)
        painter.setPen(QPen(borderColor, 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)
