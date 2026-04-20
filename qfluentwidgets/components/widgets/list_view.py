# coding: utf-8
"""提供列表视图相关组件，包括 ListView、ListWidget 及其基类和项委托

这些组件适用于需要以单列形式展示数据并支持用户选择的场景，
内置 Fluent Design 风格的悬停高亮、圆角和选中动效，可无缝融入现代界面
"""

from typing import List, Union

from PySide6.QtCore import Qt, QModelIndex, Property
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStyleOptionViewItem, QListView, QListView, QListWidget, QWidget

from .scroll_bar import SmoothScrollDelegate
from .table_view import TableItemDelegate
from ...common.style_sheet import FluentStyleSheet, themeColor
from ...common.color import autoFallbackThemeColor


class ListItemDelegate(TableItemDelegate):
    """负责列表项绘制与外观定制的委托类
    
    该类通过重载绘制方法为列表项提供 Fluent Design 风格的视觉效果，
    包括悬停高亮、选中态指示器及圆角裁剪，通常由 ListView 或 ListWidget 内部自动创建与绑定
    """

    def __init__(self, parent: QListView):
        """初始化委托实例
        
        Args:
            parent: 父对象实例，通常为 QListView 或 QListWidget，负责该委托的生命周期管理
        """
        super().__init__(parent)

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.drawRoundedRect(option.rect, 5, 5)

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        y, h = option.rect.y(), option.rect.height()
        ph = round(0.35*h if self.pressedRow == index.row() else 0.257*h)
        painter.setBrush(autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor))
        painter.drawRoundedRect(0, ph + y, 3, h - 2*ph, 1.5, 1.5)


class ListBase:
    """列表组件的抽象基类，为 ListWidget 和 ListView 提供通用行为与样式支持
    
    该类封装了列表视图的公共交互逻辑和视觉配置，包括滚动条样式、项高亮策略及背景绘制，
    一般不由用户直接实例化，如需扩展自定义列表组件可继承此类并重写相关方法
    """

    def __init__(self, *args, **kwargs):
        """初始化列表基类实例
        
        Args:
            *args: 可变位置参数，透传至父类构造方法以支持多种构造方式
            **kwargs: 可变关键字参数，透传至父类构造方法以支持属性配置
        """
        super().__init__(*args, **kwargs)
        self.delegate = ListItemDelegate(self)
        self.scrollDelegate = SmoothScrollDelegate(self)
        self._isSelectRightClickedRow = False

        FluentStyleSheet.LIST_VIEW.apply(self)
        self.setItemDelegate(self.delegate)
        self.setMouseTracking(True)

        self.entered.connect(lambda i: self._setHoverRow(i.row()))
        self.pressed.connect(lambda i: self._setPressedRow(i.row()))

    def _setHoverRow(self, row: int):
        """设置悬停行"""
        self.delegate.setHoverRow(row)
        self.viewport().update()

    def _setPressedRow(self, row: int):
        """设置按下行"""
        if self.selectionMode() == QListView.SelectionMode.NoSelection:
            return

        self.delegate.setPressedRow(row)
        self.viewport().update()

    def _setSelectedRows(self, indexes: List[QModelIndex]):
        if self.selectionMode() ==  QListView.SelectionMode.NoSelection:
            return

        self.delegate.setSelectedRows(indexes)
        self.viewport().update()

    def leaveEvent(self, e):
        QListView.leaveEvent(self, e)
        self._setHoverRow(-1)

    def resizeEvent(self, e):
        QListView.resizeEvent(self, e)
        self.viewport().update()

    def keyPressEvent(self, e):
        QListView.keyPressEvent(self, e)
        self.updateSelectedRows()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton or self._isSelectRightClickedRow:
            return QListView.mousePressEvent(self, e)

        index = self.indexAt(e.pos())
        if index.isValid():
            self._setPressedRow(index.row())

        QWidget.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        QListView.mouseReleaseEvent(self, e)
        self.updateSelectedRows()

        if self.indexAt(e.pos()).row() < 0 or e.button() == Qt.RightButton:
            self._setPressedRow(-1)

    def setItemDelegate(self, delegate: ListItemDelegate):
        self.delegate = delegate
        super().setItemDelegate(delegate)

    def clearSelection(self):
        QListView.clearSelection(self)
        self.updateSelectedRows()

    def setCurrentIndex(self, index: QModelIndex):
        QListView.setCurrentIndex(self, index)
        self.updateSelectedRows()

    def updateSelectedRows(self):
        self._setSelectedRows(self.selectedIndexes())

    def setCheckedColor(self, light, dark):
        """设置选中状态的颜色

        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的颜色
        """
        self.delegate.setCheckedColor(light, dark)


class ListWidget(ListBase, QListWidget):
    """基于 QListWidget 的 Fluent Design 风格列表部件
    
    ListWidget 适用于项数量相对固定、需要直接通过 QListWidgetItem 进行增删改查的场景，
    支持图标、文本及自定义部件嵌入，并自动应用悬停高亮与选中动效
    """

    def __init__(self, parent=None):
        """初始化列表部件
        
        Args:
            parent: 父级窗口或部件，默认为 None。传入非 None 值后，该列表将随父对象一起释放
        """
        super().__init__(parent)

    def setCurrentItem(self, item, command=None):
        self.setCurrentRow(self.row(item), command)

    def setCurrentRow(self, row: int, command=None):
        if not command:
            super().setCurrentRow(row)
        else:
            super().setCurrentRow(row, command)

        self.updateSelectedRows()

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(bool, isSelectRightClickedRow, setSelectRightClickedRow)


class ListView(ListBase, QListView):
    """基于 QListView 的 Fluent Design 风格列表视图
    
    ListView 采用 Model/View 架构，适用于数据层与表现层需要分离的场景，
    支持绑定自定义 QAbstractItemModel 实现海量数据的高效展示，并内置 Fluent 风格的项高亮与选中效果
    """

    def __init__(self, parent=None):
        """初始化列表视图
        
        Args:
            parent: 父级窗口或部件，默认为 None。传入非 None 值后，该视图将随父对象一起释放
        """
        super().__init__(parent)

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(bool, isSelectRightClickedRow, setSelectRightClickedRow)