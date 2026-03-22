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
    """ 信息栏位置 """

    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3
    TOP_LEFT = 4
    TOP_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_RIGHT = 7


class ItemViewToolTipType(Enum):
    """ 信息栏位置 """

    LIST = 0
    TABLE = 1


class ToolTip(QFrame):
    """ 工具提示 """

    def __init__(self, text='', parent=None):
        """
        参数
        ----------
        text: str
            工具提示文本.

        parent: QWidget
            父部件.
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
        """设置工具提示文本."""
        self.__text = text
        self.label.setText(text)
        self.container.adjustSize()
        self.adjustSize()

    def duration(self):
        return self.__duration

    def setDuration(self, duration: int):
        """设置工具提示持续时间.

        参数
        ----------
        duration: int
            显示时长, 单位为毫秒. 如果 `持续时间 <= 0`, 工具提示不会自动消失.
        """
        self.__duration = duration

    def __setQss(self):
        """ 设置样式表 """
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
        """根据部件位置调整工具提示位置."""
        manager = ToolTipPositionManager.make(position)
        self.move(manager.position(self, widget))


class ToolTipPositionManager:
    """工具提示位置管理器."""

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
        """根据显示位置创建工具提示管理器."""
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
    """顶部工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget):
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class BottomToolTipManager(ToolTipPositionManager):
    """底部工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()//2 - tooltip.width()//2
        y = pos.y() + parent.height()
        return QPoint(x, y)


class LeftToolTipManager(ToolTipPositionManager):
    """左侧工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.width()
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)


class RightToolTipManager(ToolTipPositionManager):
    """右侧工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width()
        y = pos.y() + (parent.height() - tooltip.height()) // 2
        return QPoint(x, y)


class TopRightToolTipManager(ToolTipPositionManager):
    """右上工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width() - tooltip.width() + \
            tooltip.layout().contentsMargins().right()
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class TopLeftToolTipManager(ToolTipPositionManager):
    """左上工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.layout().contentsMargins().left()
        y = pos.y() - tooltip.height()
        return QPoint(x, y)


class BottomRightToolTipManager(ToolTipPositionManager):
    """右下工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() + parent.width() - tooltip.width() + \
            tooltip.layout().contentsMargins().right()
        y = pos.y() + parent.height()
        return QPoint(x, y)


class BottomLeftToolTipManager(ToolTipPositionManager):
    """左下工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, parent: QWidget) -> QPoint:
        pos = parent.mapToGlobal(QPoint())
        x = pos.x() - tooltip.layout().contentsMargins().left()
        y = pos.y() + parent.height()
        return QPoint(x, y)


class ItemViewToolTipManager(ToolTipPositionManager):
    """项视图工具提示位置管理器."""

    def __init__(self, itemRect=QRect()):
        super().__init__()
        self.itemRect = itemRect

    def _pos(self, tooltip: ToolTip, view: QAbstractItemView) -> QPoint:
        pos = view.mapToGlobal(self.itemRect.topLeft())
        x = pos.x()
        y = pos.y() - tooltip.height() + 10
        return QPoint(x, y)

    @staticmethod
    def make(tipType: ItemViewToolTipType, itemRect: QRect):
        """根据显示类型创建项视图工具提示管理器."""
        managers = {
            ItemViewToolTipType.LIST: ItemViewToolTipManager,
            ItemViewToolTipType.TABLE: TableItemToolTipManager,
        }

        if tipType not in managers:
            raise ValueError(f'`{tipType}` is an invalid info bar tipType.')

        return managers[tipType](itemRect)


class TableItemToolTipManager(ItemViewToolTipManager):
    """表格项工具提示位置管理器."""

    def _pos(self, tooltip: ToolTip, view: QTableView) -> QPoint:
        pos = view.mapToGlobal(self.itemRect.topLeft())
        x = pos.x() + view.verticalHeader().isVisible() * view.verticalHeader().width()
        y = pos.y() - tooltip.height() + view.horizontalHeader().isVisible() * view.horizontalHeader().height() + 10
        return QPoint(x, y)



class ToolTipFilter(QObject):
    """为部件提供工具提示过滤器."""

    def __init__(self, parent: QWidget, showDelay=300, position=ToolTipPosition.TOP):
        """
        参数
        ----------
        parent: QWidget
            要安装工具提示的部件.

        showDelay: int
            鼠标悬停多久后显示工具提示, 单位为毫秒.

        position: TooltipPosition
            工具提示显示位置.
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
        """ 隐藏tool tip """
        self.isEnter = False
        self.timer.stop()
        if self._tooltip:
            self._tooltip.hide()

    def showToolTip(self):
        """ 显示工具提示 """
        if not self.isEnter:
            return

        parent = self.parent()  # type: QWidget
        self._tooltip.setText(parent.toolTip())
        self._tooltip.adjustPos(parent, self.position)
        self._tooltip.show()

    def setToolTipDelay(self, delay: int):
        """ 设置tool tip的delay """
        self._tooltipDelay = delay

    def _canShowToolTip(self) -> bool:
        parent = self.parent()  # type: QWidget
        return parent.isWidgetType() and parent.toolTip() and parent.isEnabled()


class ItemViewToolTip(ToolTip):
    """ 项视图工具提示 """

    def adjustPos(self, view: QAbstractItemView, itemRect: QRect, tooltipType: ItemViewToolTipType):
        manager = ItemViewToolTipManager.make(tooltipType, itemRect)
        self.move(manager.position(self, view))



class ItemViewToolTipDelegate(ToolTipFilter):
    """ 项视图工具提示 """

    def __init__(self, parent: QAbstractItemView, showDelay=300, tooltipType=ItemViewToolTipType.TABLE):
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
        """ 显示工具提示 """
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
