# coding: utf-8
from enum import Enum

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt, QPropertyAnimation, QModelIndex, QRect
from PySide6.QtGui import QColor, QHelpEvent
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect,
                             QHBoxLayout, QLabel, QWidget, QAbstractItemView, QStyleOptionViewItem,
                             QTableView)

from ...common.font import getFont
from ...common.style_sheet import isDarkTheme
from ...common.screen import getCurrentScreenGeometry


class ToolTipPosition(Enum):
    """定义工具提示相对于目标部件的显示方位
    
     通过枚举值指定 ToolTip 的弹出位置，配合 ToolTipPositionManager 子类实现精准定位
     常用于 ToolTipFilter 和各类视图委托中控制提示气泡的朝向
    """

    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3
    TOP_LEFT = 4
    TOP_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_RIGHT = 7


class ItemViewToolTipType(Enum):
    """定义项视图工具提示的内容展示策略
    
     用于区分项视图中工具提示应显示完整数据、富文本还是仅当文本截断时显示
     配合 ItemViewToolTipDelegate 决定 QListView、QTableView 等控件的提示行为
    """

    LIST = 0
    TABLE = 1


class ToolTip(QFrame):
    """自定义工具提示窗口，支持富文本、阴影与圆角边框
    
     替代原生 QToolTip，提供更美观的视觉效果和更灵活的布局控制
     通常由 ToolTipFilter 或视图委托触发显示，不建议在业务代码中直接实例化
    """

    def __init__(self, text='', parent=None):
        """初始化工具提示
        
        Args:
            text: 工具提示文本
            parent: 父部件
        """
        super().__init__(parent=parent)
        self.__text = text
        self.__duration = 1000

        self.container = self._createContainer()
        self.timer = QTimer(self)

        self.setLayout(QHBoxLayout())
        self.containerLayout = QHBoxLayout(self.container)
        self.label = QLabel(text, self)

        # 设置 布局
        self.layout().setContentsMargins(12, 8, 12, 12)
        self.layout().addWidget(self.container)
        self.containerLayout.addWidget(self.label)
        self.containerLayout.setContentsMargins(8, 6, 8, 6)

        # 添加 opacity effect
        self.opacityAni = QPropertyAnimation(self, b'windowOpacity', self)
        self.opacityAni.setDuration(150)

        # 添加 shadow
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setBlurRadius(25)
        self.shadowEffect.setColor(QColor(0, 0, 0, 50))
        self.shadowEffect.setOffset(0, 5)
        self.container.setGraphicsEffect(self.shadowEffect)

        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

        # 设置 style
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.__setQss()

    def text(self):
        return self.__text

    def setText(self, text):
        """设置工具提示文本"""
        self.__text = text
        self.label.setText(text)
        self.container.adjustSize()
        self.adjustSize()

    def duration(self):
        return self.__duration

    def setDuration(self, duration: int):
        """设置工具提示持续时间
        
        Args:
            duration: 显示时长，单位为毫秒。如果 `duration <= 0`，工具提示不会自动消失
        """
        self.__duration = duration

    def __setQss(self):
        """设置样式表"""
        self.container.setObjectName("container")
        self.label.setObjectName("contentLabel")
        self.label.setFont(getFont(12))
        self.setStyleSheet(self._toolTipQss())
        self.label.adjustSize()
        self.adjustSize()

    def _toolTipQss(self) -> str:
        if isDarkTheme():
            return """
                ToolTip {
                    border-radius: 4px;
                }

                ToolTip > #container {
                    background-color: rgb(43, 43, 43);
                    border: 1px solid rgb(28, 28, 28);
                    border-radius: 4px;
                }

                ToolTip>#container[transparent=true] {
                    background-color: transparent;
                    border: 1px solid rgba(0, 0, 0, 50);
                }

                QLabel#contentLabel {
                    background-color: transparent;
                    color: white;
                    border: none;
                }
            """

        return """
            ToolTip {
                border-radius: 4px;
            }

            ToolTip>#container {
                border: 1px solid rgba(0, 0, 0, 0.06);
                background-color: rgb(249, 249, 249);
                border-radius: 4px;
            }

            ToolTip>#container[transparent=true] {
                background-color: transparent;
            }

            QLabel#contentLabel {
                background-color: transparent;
                border: none;
                color: black;
            }
        """

    def _createContainer(self):
        return QFrame(self)

    def showEvent(self, e):
        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()

        self.timer.stop()
        if self.duration() > 0:
            self.timer.start(self.__duration + self.opacityAni.duration())

        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def adjustPos(self, widget, position: ToolTipPosition):
        """根据部件位置调整工具提示位置"""
        manager = ToolTipPositionManager.make(position)
        self.move(manager.position(self, widget))


class ToolTipPositionManager:
    """计算工具提示窗口显示坐标的抽象基类
    
     根据目标部件几何信息和工具提示尺寸，推算出不超出屏幕且避让鼠标的最佳位置
     子类需实现 position() 方法以提供具体方位策略
    """

    def position(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = self._pos(tooltip, parent)
        x, y = pos.x(), pos.y()

        rect = getCurrentScreenGeometry()
        x = max(rect.left(), min(pos.x(), rect.right() - tooltip.width() - 4))
        y = max(rect.top(), min(pos.y(), rect.bottom() - tooltip.height() - 4))

        return QPoint(x, y)

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        raise NotImplementedError

    @staticmethod
    def make(position: ToolTipPosition):
        """根据显示位置创建工具提示管理器"""
        managers = {
            ToolTipPosition.TOP: TopToolTipManager,
            ToolTipPosition.BOTTOM: BottomToolTipManager,
            ToolTipPosition.LEFT: LeftToolTipManager,
            ToolTipPosition.RIGHT: RightToolTipManager,
            ToolTipPosition.TOP_RIGHT: TopRightToolTipManager,
            ToolTipPosition.BOTTOM_RIGHT: BottomRightToolTipManager,
            ToolTipPosition.TOP_LEFT: TopLeftToolTipManager,
            ToolTipPosition.BOTTOM_LEFT: BottomLeftToolTipManager,
        }

        if position not in managers:
            raise ValueError(f'`{position}` is an invalid info bar position.')

        return managers[position]()


class TopToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件上方的位置策略
    
     当垂直空间充足时优先置于目标顶部，若顶部空间不足则自动回退到其他方位
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget):
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class BottomToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件下方的位置策略
    
     适用于目标上方空间受限或希望提示向下延展的场景，会自动检测底部边界
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        y = pos.y() + parent.height()
        return QPoint(x, y)


class LeftToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件左侧的位置策略
    
     适用于横向空间充裕且目标右侧有重要内容需要避让的界面布局
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.width()
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)


class RightToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件右侧的位置策略
    
     为默认的横向弹出策略，适合阅读顺序从左到右的提示内容展示
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)


class TopRightToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件右上方的位置策略
    
     兼顾顶部与右侧空间，适用于目标左下角存在关联控件或需跟随鼠标偏右的场景
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width() - tooltip.width() + \
            tooltip.layout().contentsMargins().right()
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class TopLeftToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件左上方的位置策略
    
     适用于目标右侧被其他面板占据，或希望提示与目标左边缘对齐的界面布局
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.layout().contentsMargins().left()
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class BottomRightToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件右下方的位置策略
    
     当目标上方及左侧空间均受限时，可将提示置于右下角以充分利用剩余视口
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width() - tooltip.width() + \
            tooltip.layout().contentsMargins().right()
        y = pos.y() + parent.height()
        return QPoint(x, y)


class BottomLeftToolTipManager(ToolTipPositionManager):
    """将工具提示显示在目标部件左下方的位置策略
    
     适合目标上方空间不足且右侧存在重要交互区域时的提示定位
    """

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.layout().contentsMargins().left()
        y = pos.y() + parent.height()
        return QPoint(x, y)


class ItemViewToolTipManager(ToolTipPositionManager):
    """为 QListView、QTableView 等项视图定制的工具提示位置管理器
    
     根据单元格或列表项的矩形区域计算提示位置，确保提示与目标项精准对齐
     支持在视图滚动时动态更新坐标，避免提示偏离对应数据项
    """

    def __init__(self, itemRect=QRect()):
        """初始化项视图工具提示位置管理器
        
         Args:
             itemRect: 目标项在视图中的矩形区域，用于计算提示基准坐标
        """
        super().__init__()
        self.itemRect = itemRect

    def _pos(self, tooltip: ToolTip, view: QAbstractItemView) -> QPoint:
        pos = view.mapToGlobal(self.itemRect.topLeft())
        x = pos.x()
        y = pos.y() - tooltip.height() + 10
        return QPoint(x, y)

    @staticmethod
    def make(tipType: ItemViewToolTipType, itemRect: QRect):
        """根据显示类型创建项视图工具提示管理器
        
        Args:
            tipType: 项视图工具提示类型
            itemRect: 项矩形区域
        """
        managers = {
            ItemViewToolTipType.LIST: ItemViewToolTipManager,
            ItemViewToolTipType.TABLE: TableItemToolTipManager,
        }

        if tipType not in managers:
            raise ValueError(f'`{tipType}` is an invalid info bar tipType.')

        return managers[tipType](itemRect)


class TableItemToolTipManager(ItemViewToolTipManager):
    """为 QTableWidget 单元格定制的工具提示位置管理器
    
     继承自 ItemViewToolTipManager，针对表格行列特性优化了边界检测逻辑
     在单元格文本被截断时自动计算最佳提示位置，避免遮挡相邻编辑单元格
    """

    def _pos(self, tooltip: ToolTip, view: QTableView) -> QPoint:
        pos = view.mapToGlobal(self.itemRect.topLeft())
        x = pos.x() + view.verticalHeader().isVisible() * view.verticalHeader().width()
        y = pos.y() - tooltip.height() + view.horizontalHeader().isVisible() * view.horizontalHeader().height() + 10
        return QPoint(x, y)



class ToolTipFilter(QObject):
    """为任意 QWidget 提供悬停显示自定义 ToolTip 的事件过滤器
    
     安装到目标部件后，自动拦截 enter、leave 和 mouse move 事件来控制提示的显隐与时序
     支持通过 showDelay、hideDelay 等参数精细化控制提示的弹出与消失行为
    """

    def __init__(self, parent: QWidget, showDelay=300, position=ToolTipPosition.TOP):
        """初始化工具提示过滤器
        
        Args:
            parent: 要安装工具提示的部件
            showDelay: 鼠标悬停多久后显示工具提示，单位为毫秒
            position: 工具提示显示位置
        """
        super().__init__(parent=parent)
        self.isEnter = False
        self._tooltip = None
        self._tooltipDelay = showDelay
        self.position = position
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.showToolTip)

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        if e.type() == QEvent.ToolTip:
            return True
        elif e.type() in [QEvent.Hide, QEvent.Leave]:
            self.hideToolTip()
        elif e.type() == QEvent.Enter:
            self.isEnter = True
            parent = self.parent()  # type: QWidget
            if self._canShowToolTip():
                if self._tooltip is None:
                    self._tooltip = self._createToolTip()

                t = parent.toolTipDuration() if parent.toolTipDuration() > 0 else -1
                self._tooltip.setDuration(t)

                # 延迟显示工具提示.
                self.timer.start(self._tooltipDelay)
        elif e.type() == QEvent.MouseButtonPress:
            self.hideToolTip()

        return super().eventFilter(obj, e)

    def _createToolTip(self):
        return ToolTip(self.parent().toolTip(), self.parent().window())

    def hideToolTip(self):
        """隐藏工具提示"""
        self.isEnter = False
        self.timer.stop()
        if self._tooltip:
            self._tooltip.hide()

    def showToolTip(self):
        """显示工具提示"""
        if not self.isEnter:
            return

        parent = self.parent()  # type: QWidget
        self._tooltip.setText(parent.toolTip())
        self._tooltip.adjustPos(parent, self.position)
        self._tooltip.show()

    def setToolTipDelay(self, delay: int):
        """设置工具提示显示延迟"""
        self._tooltipDelay = delay

    def _canShowToolTip(self) -> bool:
        parent = self.parent()  # type: QWidget
        return parent.isWidgetType() and parent.toolTip() and parent.isEnabled()


class ItemViewToolTip(ToolTip):
    """用于项视图控件的富文本工具提示窗口
    
     在 QListView、QTreeView 等控件中替代系统默认提示，支持显示样式化的多行文本
     通常由 ItemViewToolTipDelegate 创建和管理，跟随当前数据项移动
    """

    def adjustPos(self, view: QAbstractItemView, itemRect: QRect, tooltipType: ItemViewToolTipType):
        manager = ItemViewToolTipManager.make(tooltipType, itemRect)
        self.move(manager.position(self, view))



class ItemViewToolTipDelegate(ToolTipFilter):
    """为项视图提供自定义工具提示支持的委托基类
    
     继承自 QStyledItemDelegate，在保持原有绘制逻辑的同时增强提示能力
     支持根据 ItemViewToolTipType 策略决定何时以及如何展示 ItemViewToolTip
    """

    def __init__(self, parent: QAbstractItemView, showDelay=300, tooltipType=ItemViewToolTipType.TABLE):
        """初始化项视图工具提示委托
        
         Args:
             parent: 委托的父对象，通常为对应的项视图控件
             showDelay: 鼠标悬停后延迟显示的毫秒数，控制提示响应灵敏度
             tooltipType: 工具提示类型，决定提示内容的生成策略与展示方式
        """
        super().__init__(parent, showDelay, ToolTipPosition.TOP)
        self.text = ""
        self.currentIndex = None
        self.tooltipDuration = -1
        self.tooltipType = tooltipType
        self.viewport = parent.viewport()

        parent.installEventFilter(self)
        parent.viewport().installEventFilter(self)
        parent.horizontalScrollBar().valueChanged.connect(self.hideToolTip)
        parent.verticalScrollBar().valueChanged.connect(self.hideToolTip)

    def eventFilter(self, obj: QObject, e: QEvent) -> bool:
        if obj is self.parent():
            if e.type() in [QEvent.Type.Hide, QEvent.Type.Leave]:
                self.hideToolTip()
            elif e.type() == QEvent.Type.Enter:
                self.isEnter = True
        elif obj is self.viewport:
            if e.type() == QEvent.Type.MouseButtonPress:
                self.hideToolTip()

        return QObject.eventFilter(self, obj, e)

    def _createToolTip(self):
        return ItemViewToolTip(self.text, self.parent().window())

    def showToolTip(self):
        """显示工具提示"""
        if not self._tooltip:
            self._tooltip = self._createToolTip()

        view = self.parent()  # type: QAbstractItemView
        self._tooltip.setText(self.text)

        if self.currentIndex:
            rect = view.visualRect(self.currentIndex)
        else:
            rect = QRect()

        self._tooltip.adjustPos(view, rect, self.tooltipType)
        self._tooltip.show()

    def _canShowToolTip(self) -> bool:
        return True

    def setText(self, text: str):
        self.text = text
        if self._tooltip:
            self._tooltip.setText(text)

    def setToolTipDuration(self, duration):
        self.tooltipDuration = duration
        if self._tooltip:
            self._tooltip.setDuration(duration)

    def helpEvent(self, event: QHelpEvent, view: QAbstractItemView, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        if not event or not view:
            return False

        if event.type() == QEvent.Type.ToolTip:
            text = index.data(Qt.ItemDataRole.ToolTipRole)
            if not text:
                self.hideToolTip()
                return False

            self.text = text
            self.currentIndex = index

            if not self._tooltip:
                self._tooltip = self._createToolTip()
                self._tooltip.setDuration(self.tooltipDuration)

            # 延迟显示工具提示.
            self.timer.start(self._tooltipDelay)

        return True
