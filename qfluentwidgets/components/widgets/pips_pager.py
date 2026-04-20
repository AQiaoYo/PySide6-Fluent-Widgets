# coding: utf-8
"""Pips 分页导航组件模块

提供基于圆点（Pips）的分页导航控件集合，常用于图片轮播、多页向导、滑动视图等场景
通过圆点的高亮状态直观展示当前页码与总页数，支持水平与垂直两种布局方向
"""

from enum import Enum
from PySide6.QtCore import Qt, Signal, QModelIndex, QPoint, Property, QSize, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import (QStyleOptionViewItem, QStyle, QListWidget, QListWidgetItem, QStyledItemDelegate,
                             QToolButton)

from ...common.overload import singledispatchmethod
from ...common.icon import FluentIcon, drawIcon
from ...common.style_sheet import isDarkTheme, FluentStyleSheet
from .button import ToolButton
from .tool_tip import ToolTipFilter, ToolTipPosition
from .scroll_bar import SmoothScrollBar


class PipsScrollButtonDisplayMode(Enum):
    """PipsPager 滚动按钮的显示模式
    
    用于控制分页导航器两侧滚动按钮的显隐策略，可根据页面数量或容器尺寸自动调整
    通常在页面总数超出可视区域时启用，帮助用户快速跳转到相邻分页
    """
    ALWAYS = 0
    ON_HOVER = 1
    NEVER = 2


class ScrollButton(ToolButton):
    """PipsPager 的滚动按钮
    
    提供圆点分页器两侧的方向按钮，用于在页面较多时逐页滚动浏览
    按钮会在鼠标悬停或特定显示模式下出现，点击后切换到相邻页面
    """

    def _postInit(self):
        self.setFixedSize(12, 12)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if isDarkTheme():
            color = QColor(255, 255, 255)
            painter.setOpacity(0.773 if self.isHover or self.isPressed else 0.541)
        else:
            color = QColor(0, 0, 0)
            painter.setOpacity(0.616 if self.isHover or self.isPressed else 0.45)

        if self.isPressed:
            rect = QRectF(3, 3, 6, 6)
        else:
            rect = QRectF(2, 2, 8, 8)

        drawIcon(self._icon, painter, rect, fill=color.name())


class PipsDelegate(QStyledItemDelegate):
    """PipsPager 的列表项委托
    
    负责绘制圆点指示器的视觉样式，包括选中状态、悬停状态及尺寸计算
    通过委托模式将视图逻辑与绘制逻辑分离，便于自定义圆点外观
    """

    def __init__(self, parent=None):
        """初始化委托
        
        Args:
            parent (QWidget): 父对象，通常由 PipsPager 传入。默认为 None
        """
        super().__init__(parent=parent)
        self.hoveredRow = -1
        self.pressedRow = -1

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        isHover = index.row() == self.hoveredRow
        isPressed = index.row() == self.pressedRow

        # 绘制pip
        if isDarkTheme():
            if isHover or isPressed:
                color = QColor(255, 255, 255, 197)
            else:
                color = QColor(255, 255, 255, 138)
        else:
            if isHover or isPressed:
                color = QColor(0, 0, 0, 157)
            else:
                color = QColor(0, 0, 0, 114)

        painter.setBrush(color)

        if option.state & QStyle.State_Selected or (isHover and not isPressed):
            r = 3
        else:
            r = 2

        x = option.rect.x() + 6 - r
        y = option.rect.y() + 6 - r
        painter.drawEllipse(QRectF(x, y, 2*r, 2*r))

        painter.restore()

    def setPressedRow(self, row: int):
        self.pressedRow = row
        self.parent().viewport().update()

    def setHoveredRow(self, row: bool):
        self.hoveredRow = row
        self.parent().viewport().update()


class PipsPager(QListWidget):
    """Pips 分页导航控件
    
    用于在多个页面或内容块之间进行切换，以圆点形式展示当前所在位置
    支持自定义圆点间距、按钮显示策略以及方向布局，适用于轮播图、引导页等场景
    
    构造函数重载:
        * PipsPager(parent: QWidget = None)
        * PipsPager(orientation: Qt.Orientation, parent: QWidget = None)
    """

    currentIndexChanged = Signal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化分页导航控件
        
        Args:
            parent (QWidget): 父控件，默认为 None。传入后该分页器将被嵌入到父控件的布局中
        """
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        self._visibleNumber = 5
        self.isHover = False

        self.delegate = PipsDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(500)
        self.scrollBar.setForceHidden(True)

        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setGridSize(QSize(12, 12))
        self.setItemDelegate(self.delegate)
        self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        FluentStyleSheet.PIPS_PAGER.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.setViewportMargins(15, 0, 15, 0)
            self.preButton = ScrollButton(FluentIcon.CARE_LEFT_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_RIGHT_SOLID, self)
            self.setFixedHeight(12)

            self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.LEFT))
            self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.RIGHT))

        else:
            self.setViewportMargins(0, 15, 0, 15)
            self.preButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
            self.setFixedWidth(12)

            self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.TOP))
            self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.BOTTOM))

        self.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.NEVER)
        self.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.NEVER)
        self.preButton.setToolTip(self.tr('Previous Page'))
        self.nextButton.setToolTip(self.tr('Next Page'))

        # 连接信号与槽函数
        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)
        self.itemPressed.connect(self._setPressedItem)
        self.itemEntered.connect(self._setHoveredItem)

    def _setPressedItem(self, item: QListWidgetItem):
        self.delegate.setPressedRow(self.row(item))
        self.setCurrentIndex(self.row(item))

    def _setHoveredItem(self, item: QListWidgetItem):
        self.delegate.setHoveredRow(self.row(item))

    def setPageNumber(self, n: int):
        """设置页面数量

        Args:
            n: 页面数量
        """
        self.clear()
        self.addItems(['15555'] * n)

        for i in range(n):
            item = self.item(i)
            item.setData(Qt.UserRole, i + 1)
            item.setSizeHint(self.gridSize())

        self.setCurrentIndex(0)
        self.adjustSize()

    def getPageNumber(self):
        """获取页面数量

        Returns:
            页面数量
        """
        return self.count()

    def getVisibleNumber(self):
        """获取可见 pip 的数量

        Returns:
            可见 pip 的数量
        """
        return self._visibleNumber

    def setVisibleNumber(self, n: int):
        self._visibleNumber = n
        self.adjustSize()

    def scrollNext(self):
        """向后滚动一项"""
        self.setCurrentIndex(self.currentIndex() + 1)

    def scrollPrevious(self):
        """向前滚动一项"""
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollToItem(self, item: QListWidgetItem, hint=QListWidget.PositionAtCenter):
        """滚动到指定项

        Args:
            item: 目标列表项
            hint: 滚动位置提示
        """
        # 滚动 到 center 位置
        index = self.row(item)
        size = item.sizeHint()
        s = size.width() if self.isHorizontal() else size.height()
        self.scrollBar.scrollTo(s * (index - self.visibleNumber // 2))

        # 清空selection
        self.clearSelection()
        item.setSelected(False)

        self.currentIndexChanged.emit(index)

    def adjustSize(self) -> None:
        m = self.viewportMargins()

        if self.isHorizontal():
            w = self.visibleNumber * self.gridSize().width() + m.left() + m.right()
            self.setFixedWidth(w)
        else:
            h = self.visibleNumber * self.gridSize().height() + m.top() + m.bottom()
            self.setFixedHeight(h)

    def isHorizontal(self):
        return self.orientation == Qt.Horizontal

    def setCurrentIndex(self, index: int):
        """设置当前索引

        Args:
            index: 目标索引
        """
        if not 0 <= index < self.count():
            return

        item = self.item(index)
        self.scrollToItem(item)
        super().setCurrentItem(item)

        self._updateScrollButtonVisibility()

    def isPreviousButtonVisible(self):
        if self.currentIndex() <= 0 or self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER:
            return False

        if self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def isNextButtonVisible(self):
        if self.currentIndex() >= self.count() - 1 or self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER:
            return False

        if self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def currentIndex(self):
        return super().currentIndex().row()

    def setPreviousButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode):
        """设置上一页按钮的显示模式

        Args:
            mode: 显示模式
        """
        self.previousButtonDisplayMode = mode
        self.preButton.setVisible(self.isPreviousButtonVisible())

    def setNextButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode):
        """设置下一页按钮的显示模式

        Args:
            mode: 显示模式
        """
        self.nextButtonDisplayMode = mode
        self.nextButton.setVisible(self.isNextButtonVisible())

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.delegate.setPressedRow(-1)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True
        self._updateScrollButtonVisibility()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        self.delegate.setHoveredRow(-1)
        self._updateScrollButtonVisibility()

    def _updateScrollButtonVisibility(self):
        self.preButton.setVisible(self.isPreviousButtonVisible())
        self.nextButton.setVisible(self.isNextButtonVisible())

    def wheelEvent(self, e):
        pass

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        bw, bh = self.preButton.width(), self.preButton.height()

        if self.isHorizontal():
            self.preButton.move(0, int(h/2 - bh/2))
            self.nextButton.move(w - bw, int(h/2 - bh/2))
        else:
            self.preButton.move(int(w/2-bw/2), 0)
            self.nextButton.move(int(w/2-bw/2), h-bh)

    visibleNumber = Property(int, getVisibleNumber, setVisibleNumber)
    pageNumber = Property(int, getPageNumber, setPageNumber)


class HorizontalPipsPager(PipsPager):
    """水平方向 Pips 分页导航控件
    
    圆点沿水平方向排列，适用于横向轮播图、步骤条等场景
    作为 PipsPager 的便捷子类，默认使用水平布局，无需手动指定方向参数
    """

    def __init__(self, parent=None):
        """初始化水平分页导航控件
        
        Args:
            parent (QWidget): 父控件，默认为 None。传入后该分页器将以水平布局嵌入父控件
        """
        super().__init__(Qt.Horizontal, parent)


class VerticalPipsPager(PipsPager):
    """垂直方向 Pips 分页导航控件
    
    圆点沿垂直方向排列，适用于纵向滚动视图、侧边步骤导航等场景
    作为 PipsPager 的便捷子类，默认使用垂直布局，无需手动指定方向参数
    """

    def __init__(self, parent=None):
        """初始化垂直分页导航控件
        
        Args:
            parent (QWidget): 父控件，默认为 None。传入后该分页器将以垂直布局嵌入父控件
        """
        super().__init__(Qt.Vertical, parent)