# coding: utf-8
"""工作流节点组件

提供画布上的节点卡片, 使用 QGraphicsProxyWidget 包装自定义卡片 widget,
支持拖拽移动, 右侧边缘拖拽调整宽度, 端口连接, 主题色适配
"""

from typing import Dict, List, Optional, Union

from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QObject, QSize, QTimer
from PySide6.QtGui import (
    QColor, QPainter, QFont, QIcon, QPainterPath, QPen, QCursor,
    QRadialGradient, QLinearGradient,
)
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsProxyWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QGraphicsSceneMouseEvent, QSizePolicy, QGraphicsDropShadowEffect,
)

from ....common.style_sheet import isDarkTheme, themeColor
from ....common.config import Theme
from ....common.font import setFont
from ....common.icon import FluentIconBase, drawIcon
from ....common.icon import FluentIcon as FIF
from ..button import TransparentToolButton
from ..card_widget import SimpleCardWidget
from ..label import CaptionLabel, StrongBodyLabel
from ..icon_widget import IconWidget
from .workflow_model import NodeData, PortData, PortDirection
from .workflow_port import WorkflowPort
from .workflow_node_registry import resolveNodeType


__all__ = ['WorkflowNode']

# Shadow margin reserved around the card for drop shadow rendering
_SHADOW_MARGIN = 16

# Resize handle width (pixels from right edge)
_RESIZE_HANDLE_WIDTH = 6

# Node width constraints
_MIN_NODE_WIDTH = 160
_MAX_NODE_WIDTH = 600


class _NodeSignals(QObject):
    """节点信号代理 (QGraphicsProxyWidget 不直接发信号)"""

    moved = Signal(str, float, float)       # nodeId, x, y
    closed = Signal(str)                    # nodeId
    selected = Signal(str)                  # nodeId
    resized = Signal(str, float)            # nodeId, newWidth
    doubleClicked = Signal(str)             # nodeId - 双击打开设置面板


def _headerColorForTheme(isDark: bool) -> QColor:
    """根据主题色生成节点标题栏颜色

    Args:
        isDark: 是否暗色主题

    Returns:
        标题栏背景色
    """
    tc = themeColor()
    if isDark:
        h = tc.hsvHue()
        s = max(int(tc.hsvSaturation() * 0.7), 40)
        v = max(int(tc.value() * 0.45), 50)
        return QColor.fromHsv(h, s, v)
    else:
        h = tc.hsvHue()
        s = max(int(tc.hsvSaturation() * 0.85), 60)
        v = max(int(tc.value() * 0.75), 80)
        return QColor.fromHsv(h, s, v)


def _headerColorVariant(baseColor: QColor, isDark: bool, variant: int = 0) -> QColor:
    """生成标题栏颜色变体 (用于区分不同节点类型)

    Args:
        baseColor: 基础主题色 (可为 None)
        isDark:    是否暗色主题
        variant:   变体索引 (0=默认, 1=灰色/中性, 2=强调色)

    Returns:
        标题栏颜色
    """
    if variant == 1:
        # Neutral/gray variant
        if isDark:
            return QColor(55, 55, 58)
        else:
            return QColor(75, 75, 80)
    elif variant == 2:
        # Accent variant - use theme color directly with adjustments
        tc = themeColor()
        if isDark:
            h = tc.hsvHue()
            s = max(int(tc.hsvSaturation() * 0.75), 50)
            v = max(int(tc.value() * 0.5), 60)
            return QColor.fromHsv(h, s, v)
        else:
            h = tc.hsvHue()
            s = max(int(tc.hsvSaturation() * 0.9), 80)
            v = max(int(tc.value() * 0.8), 100)
            return QColor.fromHsv(h, s, v)
    else:
        # Default - theme color based
        return _headerColorForTheme(isDark)


class _WhiteIconWidget(QWidget):
    """始终以白色渲染 FluentIcon 的图标控件

    用于节点标题栏, 无论当前主题如何, 图标始终为白色
    """

    def __init__(self, icon=None, parent=None):
        super().__init__(parent)
        self._icon = icon

    def setIcon(self, icon):
        """设置图标

        Args:
            icon: FluentIconBase, QIcon 或 str
        """
        self._icon = icon
        self.update()

    def paintEvent(self, e):
        if not self._icon:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        if isinstance(self._icon, FluentIconBase):
            # Always render as dark theme (white icon)
            self._icon.render(painter, self.rect(), theme=Theme.DARK)
        else:
            drawIcon(self._icon, painter, self.rect())


class _NodeTagBadge(QWidget):
    """节点标签 (底部右下角的节点 ID 标识)

    使用等宽字体, 低对比度, 不抢占视觉焦点
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self.setFixedHeight(16)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setText(self, text: str):
        """设置标签文本"""
        self._text = text
        from PySide6.QtGui import QFontMetrics, QFont as QF
        font = QF("Consolas", 9)
        fm = QFontMetrics(font)
        textWidth = fm.horizontalAdvance(text)
        self.setFixedWidth(textWidth + 4)
        self.update()

    def text(self) -> str:
        return self._text

    def paintEvent(self, e):
        if not self._text:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()

        # Draw text with moderate opacity - readable but not dominant
        textColor = QColor(255, 255, 255, 90) if isDark else QColor(0, 0, 0, 100)
        painter.setPen(textColor)
        font = painter.font()
        font.setFamily("Consolas")
        font.setPixelSize(10)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignRight | Qt.AlignVCenter, self._text)


class _NodeCardWidget(QWidget):
    """节点内部卡片 widget

    自定义绘制卡片, 提供标题栏 + 内容区域的布局, 带阴影边距.
    支持通过 setCardWidth() 调整卡片宽度.
    """

    def __init__(self, nodeData: NodeData, parent=None):
        super().__init__(parent)
        self.nodeData = nodeData
        self._headerColor = QColor(96, 96, 96)
        self._headerVariant = 0
        self._icon = None
        self._borderRadius = 8
        self._cardWidth = int(nodeData.width)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self._initLayout()

    def _initLayout(self):
        """初始化布局"""
        # Outer layout with shadow margin
        self.outerLayout = QVBoxLayout(self)
        self.outerLayout.setContentsMargins(
            _SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN, _SHADOW_MARGIN
        )
        self.outerLayout.setSpacing(0)

        # Card container (actual card area)
        self.cardFrame = QFrame(self)
        self.cardFrame.setObjectName('nodeCardFrame')
        self.cardFrame.setStyleSheet(
            "QFrame#nodeCardFrame { background: transparent; border: none; }"
        )
        self.cardFrame.setFixedWidth(self._cardWidth)
        self.cardLayout = QVBoxLayout(self.cardFrame)
        self.cardLayout.setContentsMargins(0, 0, 0, 6)
        self.cardLayout.setSpacing(0)

        # Header
        self.headerWidget = QFrame(self.cardFrame)
        self.headerWidget.setFixedHeight(40)
        self.headerWidget.setStyleSheet("background: transparent;")
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(12, 0, 6, 0)
        self.headerLayout.setSpacing(8)

        # Header icon - always white
        self.iconWidget = _WhiteIconWidget(None, self.headerWidget)
        self.iconWidget.setFixedSize(18, 18)
        self.headerLayout.addWidget(self.iconWidget)

        # Header title
        self.titleLabel = StrongBodyLabel(self.nodeData.title, self.headerWidget)
        self.titleLabel.setTextColor(Qt.white, Qt.white)
        setFont(self.titleLabel, 13, QFont.DemiBold)
        self.headerLayout.addWidget(self.titleLabel, 1)

        # Close button - TransparentToolButton with CLOSE icon
        self.closeButton = TransparentToolButton(FIF.CLOSE, self.headerWidget)
        self.closeButton.setFixedSize(26, 26)
        self.closeButton.setIconSize(QSize(10, 10))
        self.headerLayout.addWidget(self.closeButton)

        self.cardLayout.addWidget(self.headerWidget)

        # Content area
        self.contentWidget = QFrame(self.cardFrame)
        self.contentWidget.setStyleSheet("background: transparent;")
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(0, 4, 0, 0)
        self.contentLayout.setSpacing(0)
        self.cardLayout.addWidget(self.contentWidget, 1)

        # Node tag - subtle monospace label at bottom-right
        self.tagWidget = _NodeTagBadge(self.cardFrame)
        tagLayout = QHBoxLayout()
        tagLayout.setContentsMargins(0, 2, 10, 0)
        tagLayout.addStretch(1)
        tagLayout.addWidget(self.tagWidget)
        self.cardLayout.addLayout(tagLayout)

        self.outerLayout.addWidget(self.cardFrame)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def cardWidth(self) -> int:
        """获取卡片内容区域宽度 (不含阴影)"""
        return self._cardWidth

    def setCardWidth(self, width: int):
        """设置卡片内容区域宽度

        Args:
            width: 宽度像素值, 会被限制在 [_MIN_NODE_WIDTH, _MAX_NODE_WIDTH]
        """
        width = max(_MIN_NODE_WIDTH, min(_MAX_NODE_WIDTH, width))
        if width == self._cardWidth:
            return

        self._cardWidth = width
        self.cardFrame.setFixedWidth(width)
        self.adjustSize()
        self.update()

    def setHeaderColor(self, color: QColor):
        """设置标题栏颜色 (直接指定)

        Args:
            color: 标题栏背景色
        """
        self._headerColor = color
        self.update()

    def setHeaderVariant(self, variant: int):
        """设置标题栏颜色变体 (基于主题色)

        Args:
            variant: 0=主题色, 1=中性灰, 2=强调色
        """
        self._headerVariant = variant
        self.update()

    def headerColor(self) -> QColor:
        """获取当前标题栏颜色"""
        return self._headerColor

    def setNodeIcon(self, icon):
        """设置节点图标 (始终白色渲染)

        Args:
            icon: FluentIconBase, QIcon, str 或 None
        """
        self._icon = icon
        if icon:
            self.iconWidget.setIcon(icon)
            self.iconWidget.show()
        else:
            self.iconWidget.hide()

    def setContentWidget(self, widget: QWidget):
        """设置内容 widget

        Args:
            widget: 内容 QWidget, 传 None 清空
        """
        while self.contentLayout.count():
            item = self.contentLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if widget:
            self.contentLayout.addWidget(widget)

    def setTag(self, tag: str):
        """设置节点底部标签文本

        Args:
            tag: 标签文本
        """
        self.tagWidget.setText(tag)

    def cardRect(self) -> QRectF:
        """获取卡片区域 (不含阴影边距)"""
        return QRectF(self.cardFrame.geometry())

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, e):
        """绘制卡片背景和阴影"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        isDark = isDarkTheme()
        r = self._borderRadius
        cardGeo = self.cardFrame.geometry()
        cardRect = QRectF(cardGeo)

        # Draw smooth shadow
        self._drawSmoothShadow(painter, cardRect, r, isDark)

        # Draw card background
        bgColor = QColor(43, 43, 43) if isDark else QColor(255, 255, 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bgColor)
        painter.drawRoundedRect(cardRect, r, r)

        # Draw border
        borderColor = QColor(60, 60, 60, 120) if isDark else QColor(0, 0, 0, 20)
        painter.setPen(QPen(borderColor, 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cardRect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

        # Draw header background with rounded top corners
        headerRect = QRectF(
            cardRect.x(), cardRect.y(),
            cardRect.width(), self.headerWidget.height()
        )
        headerPath = QPainterPath()
        headerPath.setFillRule(Qt.WindingFill)
        headerPath.addRoundedRect(headerRect, r, r)
        # Fill bottom corners to make them square
        bottomRect = QRectF(
            headerRect.x(), headerRect.bottom() - r,
            headerRect.width(), r
        )
        headerPath.addRect(bottomRect)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self._headerColor)
        painter.drawPath(headerPath.simplified())

    def _drawSmoothShadow(self, painter: QPainter, cardRect: QRectF, radius: int, isDark: bool):
        """绘制平滑阴影

        Args:
            painter:  画笔
            cardRect: 卡片矩形
            radius:   圆角半径
            isDark:   是否暗色主题
        """
        shadowMargin = _SHADOW_MARGIN
        if isDark:
            shadowColor = QColor(0, 0, 0, 80)
            shadowOpacity = 0.35
        else:
            shadowColor = QColor(0, 0, 0, 50)
            shadowOpacity = 0.2

        painter.setPen(Qt.NoPen)

        steps = 8
        for i in range(steps):
            t = (i + 1) / steps
            alpha = int(shadowColor.alpha() * (1.0 - t * t) * shadowOpacity)
            if alpha <= 0:
                continue

            expand = shadowMargin * t
            r = radius + expand * 0.5
            rect = cardRect.adjusted(-expand, -expand + 2, expand, expand + 2)

            c = QColor(0, 0, 0, alpha)
            painter.setBrush(c)
            painter.drawRoundedRect(rect, r, r)



class WorkflowNode(QGraphicsProxyWidget):
    """工作流节点

    画布上的可拖拽节点卡片, 使用 QGraphicsProxyWidget 包装 _NodeCardWidget.
    支持标题栏拖拽移动, 右侧边缘拖拽调整宽度, 端口连接.

    Signals (通过 signals 属性访问):
        moved(nodeId, x, y):     节点移动后发射
        closed(nodeId):          关闭按钮点击后发射
        selected(nodeId):        节点被选中后发射
        resized(nodeId, width):  节点宽度调整后发射

    Constructor overloads:
        * WorkflowNode(nodeData: NodeData, parent=None)
    """

    def __init__(self, nodeData: NodeData, parent=None):
        """初始化节点

        Args:
            nodeData: 节点数据
            parent:   父 item
        """
        super().__init__(parent)
        self.nodeData = nodeData
        self.signals = _NodeSignals()
        self._ports: Dict[str, WorkflowPort] = {}
        self._portsBuilt = False

        # Drag state
        self._isDragging = False
        self._dragStartPos = QPointF()

        # Resize state
        self._isResizing = False
        self._resizeStartX = 0.0
        self._resizeStartWidth = 0

        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemClipsToShape, False)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self._initCard()
        self._initFromData()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def nodeId(self) -> str:
        """节点唯一标识"""
        return self.nodeData.id

    @property
    def kind(self) -> str:
        """节点类型标识"""
        return self.nodeData.kind

    @property
    def title(self) -> str:
        """节点标题"""
        return self.nodeData.title

    @title.setter
    def title(self, value: str):
        self.nodeData.title = value
        self._card.titleLabel.setText(value)

    @property
    def nodeWidth(self) -> float:
        """节点卡片宽度 (不含阴影)"""
        return self.nodeData.width

    @nodeWidth.setter
    def nodeWidth(self, value: float):
        self.setNodeWidth(value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def setNodeWidth(self, width: float):
        """设置节点卡片宽度

        Args:
            width: 宽度像素值, 会被限制在 [160, 600]
        """
        width = max(_MIN_NODE_WIDTH, min(_MAX_NODE_WIDTH, width))
        self.nodeData.width = width
        self._card.setCardWidth(int(width))
        # Invalidate cache and rebuild ports
        self.setCacheMode(QGraphicsItem.NoCache)
        QTimer.singleShot(0, self._afterResize)

    def setTitle(self, title: str):
        """设置节点标题

        Args:
            title: 标题文本
        """
        self.title = title

    def setHeaderColor(self, color: QColor):
        """设置标题栏颜色

        Args:
            color: 标题栏背景色
        """
        self._card.setHeaderColor(color)

    def setNodeIcon(self, icon: Union[FluentIconBase, QIcon, str, None]):
        """设置节点图标

        Args:
            icon: 图标, 始终以白色渲染
        """
        self._card.setNodeIcon(icon)

    def setTag(self, tag: str):
        """设置节点底部标签

        Args:
            tag: 标签文本
        """
        self._card.setTag(tag)

    def setContentWidget(self, widget: QWidget):
        """设置节点内容 widget

        Args:
            widget: 内容 QWidget
        """
        self._card.setContentWidget(widget)
        self._card.adjustSize()
        QTimer.singleShot(0, self._rebuildPorts)

    def properties(self) -> dict:
        """获取节点属性字典

        Returns:
            属性字典引用
        """
        return self.nodeData.properties

    def setProperty_(self, key: str, value):
        """设置节点属性

        Args:
            key:   属性键
            value: 属性值
        """
        self.nodeData.properties[key] = value

    def getPort(self, portId: str) -> Optional[WorkflowPort]:
        """获取端口 item

        Args:
            portId: 端口 ID

        Returns:
            WorkflowPort 或 None
        """
        return self._ports.get(portId)

    def allPorts(self) -> List[WorkflowPort]:
        """获取所有端口

        Returns:
            端口列表
        """
        return list(self._ports.values())

    # ------------------------------------------------------------------
    # Internal init
    # ------------------------------------------------------------------

    def _initCard(self):
        """创建并设置卡片 widget"""
        self._card = _NodeCardWidget(self.nodeData)
        self.setWidget(self._card)

        self._card.closeButton.clicked.connect(
            lambda: self.signals.closed.emit(self.nodeId)
        )

    def _initFromData(self):
        """根据 nodeData 初始化节点外观和端口"""
        typeInfo = resolveNodeType(self.nodeData.kind)

        if typeInfo:
            isDark = isDarkTheme()
            if typeInfo.color.lightness() < 80:
                headerColor = _headerColorVariant(typeInfo.color, isDark, variant=1)
            else:
                headerColor = _headerColorVariant(typeInfo.color, isDark, variant=2)
            self._card.setHeaderColor(headerColor)
            self._card.setNodeIcon(typeInfo.icon)

            if typeInfo.widget_factory:
                contentWidget = typeInfo.widget_factory(self.nodeData.properties, None)
                if contentWidget:
                    self._card.setContentWidget(contentWidget)
        else:
            isDark = isDarkTheme()
            self._card.setHeaderColor(_headerColorVariant(None, isDark, variant=1))

        self._card.setTag(f"node-{self.nodeData.id[:6]}")
        self.setPos(self.nodeData.x, self.nodeData.y)

        self._card.adjustSize()
        QTimer.singleShot(0, self._rebuildPorts)

    # ------------------------------------------------------------------
    # Interaction: drag & resize
    # ------------------------------------------------------------------

    def _isInHeaderArea(self, localPos: QPointF) -> bool:
        """判断坐标是否在标题栏区域 (排除关闭按钮)"""
        cardFrame = self._card.cardFrame
        if not cardFrame:
            return False

        cardGeo = cardFrame.geometry()
        headerH = self._card.headerWidget.height()
        headerTop = cardGeo.y()
        headerBottom = headerTop + headerH
        headerLeft = cardGeo.x()
        headerRight = cardGeo.x() + cardGeo.width()

        if not (headerLeft <= localPos.x() <= headerRight and
                headerTop <= localPos.y() <= headerBottom):
            return False

        # 排除关闭按钮区域 (右侧 32px)
        closeBtn = self._card.closeButton
        if closeBtn:
            closeBtnRight = headerRight
            closeBtnLeft = closeBtnRight - closeBtn.width() - 6
            if localPos.x() >= closeBtnLeft:
                return False

        return True

    def _isInResizeArea(self, localPos: QPointF) -> bool:
        """判断坐标是否在卡片右侧边缘的调整宽度区域

        在卡片右侧边缘 8px 范围内触发, 排除标题栏关闭按钮区域
        """
        cardFrame = self._card.cardFrame
        if not cardFrame:
            return False

        cardGeo = cardFrame.geometry()
        rightEdge = cardGeo.x() + cardGeo.width()
        top = cardGeo.y()
        bottom = cardGeo.y() + cardGeo.height()

        # 在卡片右侧边缘 8px 范围内响应
        return (rightEdge - 8 <= localPos.x() <= rightEdge + 3 and
                top <= localPos.y() <= bottom)

    def hoverMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """悬停移动 - 更新光标形状"""
        localPos = self.mapFromScene(event.scenePos())

        if self._isInResizeArea(localPos):
            self.setCursor(Qt.SizeHorCursor)
        elif self._isInHeaderArea(localPos):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        """悬停离开 - 恢复光标"""
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标按下 - 判断拖拽/调整宽度/传递给内部 widget

        端口区域的点击不拦截, 交由场景处理连线逻辑
        """
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        localPos = self.mapFromScene(event.scenePos())

        # 检查是否点击在端口上 - 如果是则不拦截, 让场景处理
        for port in self._ports.values():
            portCenter = port.pos()
            dx = localPos.x() - portCenter.x()
            dy = localPos.y() - portCenter.y()
            if dx * dx + dy * dy <= (WorkflowPort.RADIUS + 4) ** 2:
                # 点击在端口上, 不拦截事件
                event.ignore()
                return

        # Priority: resize > header drag > widget interaction
        if self._isInResizeArea(localPos):
            self._isResizing = True
            self._resizeStartX = event.scenePos().x()
            self._resizeStartWidth = self._card.cardWidth()
            self.setCursor(Qt.SizeHorCursor)
            event.accept()
            return

        if self._isInHeaderArea(localPos):
            self._isDragging = True
            self._dragStartPos = event.scenePos() - self.pos()
            self.setSelected(True)
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标移动 - 拖拽节点或调整宽度"""
        if self._isResizing:
            dx = event.scenePos().x() - self._resizeStartX
            newWidth = self._resizeStartWidth + dx
            self.setNodeWidth(newWidth)
            event.accept()
            return

        if self._isDragging:
            newPos = event.scenePos() - self._dragStartPos
            self.setPos(newPos)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标释放 - 结束拖拽/调整"""
        if self._isResizing:
            self._isResizing = False
            self.setCursor(Qt.ArrowCursor)
            self.signals.resized.emit(self.nodeId, self.nodeData.width)
            event.accept()
            return

        if self._isDragging:
            self._isDragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标双击 - 在卡片任意位置双击打开设置面板"""
        if event.button() == Qt.LeftButton:
            localPos = self.mapFromScene(event.scenePos())
            if self._isInCardArea(localPos):
                self.signals.doubleClicked.emit(self.nodeId)
                event.accept()
                return

        super().mouseDoubleClickEvent(event)

    def _isInCardArea(self, localPos: QPointF) -> bool:
        """判断坐标是否在卡片区域内"""
        cardFrame = self._card.cardFrame
        if not cardFrame:
            return False

        cardGeo = cardFrame.geometry()
        return (cardGeo.x() <= localPos.x() <= cardGeo.x() + cardGeo.width() and
                cardGeo.y() <= localPos.y() <= cardGeo.y() + cardGeo.height())

    # ------------------------------------------------------------------
    # Port management
    # ------------------------------------------------------------------

    def _afterResize(self):
        """调整宽度后重建端口并恢复缓存"""
        self._rebuildPorts()
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def _rebuildPorts(self):
        """重建端口, 使用卡片实际几何尺寸定位"""
        for port in self._ports.values():
            if port.scene():
                port.scene().removeItem(port)
        self._ports.clear()

        inputPorts = [p for p in self.nodeData.ports if p.direction == PortDirection.INPUT]
        outputPorts = [p for p in self.nodeData.ports if p.direction == PortDirection.OUTPUT]

        cardFrame = self._card.cardFrame
        cardRect = cardFrame.geometry()
        cardHeight = cardRect.height()
        cardWidth = cardRect.width()
        offsetX = cardRect.x()
        offsetY = cardRect.y()
        headerH = self._card.headerWidget.height()

        if inputPorts:
            contentH = cardHeight - headerH
            spacing = contentH / (len(inputPorts) + 1)
            for i, portData in enumerate(inputPorts):
                port = WorkflowPort(portData, self)
                y = offsetY + headerH + spacing * (i + 1)
                port.setPos(offsetX, y)
                self._ports[portData.id] = port

        if outputPorts:
            contentH = cardHeight - headerH
            spacing = contentH / (len(outputPorts) + 1)
            for i, portData in enumerate(outputPorts):
                port = WorkflowPort(portData, self)
                y = offsetY + headerH + spacing * (i + 1)
                port.setPos(offsetX + cardWidth, y)
                self._ports[portData.id] = port

        self._portsBuilt = True

        scene = self.scene()
        if scene and hasattr(scene, 'updateEdgesForNode'):
            scene.updateEdgesForNode(self.nodeId)

    # ------------------------------------------------------------------
    # Item change
    # ------------------------------------------------------------------

    def itemChange(self, change, value):
        """处理位置变化, 通知连线更新"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = value
            self.nodeData.x = pos.x()
            self.nodeData.y = pos.y()
            self.signals.moved.emit(self.nodeId, pos.x(), pos.y())
            scene = self.scene()
            if scene and hasattr(scene, 'updateEdgesForNode'):
                scene.updateEdgesForNode(self.nodeId)

        return super().itemChange(change, value)
