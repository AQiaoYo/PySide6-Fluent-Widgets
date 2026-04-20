# coding: utf-8
from typing import List, Union

from PySide6.QtCore import Qt, QMargins, QModelIndex, QItemSelectionModel, Property, QRectF, QEvent
from PySide6.QtGui import QHelpEvent, QPainter, QColor, QKeyEvent, QPalette, QBrush
from PySide6.QtWidgets import (QAbstractItemView, QStyledItemDelegate, QApplication, QStyleOptionViewItem,
                             QTableView, QTableWidget, QWidget, QTableWidgetItem, QStyle,
                             QStyleOptionButton, QStyleFactory)

from .check_box import CheckBoxIcon
from ...common.font import getFont
from ...common.color import autoFallbackThemeColor
from ...common.style_sheet import isDarkTheme, FluentStyleSheet, updateDynamicStyle, setCustomStyleSheet
from .line_edit import LineEdit
from .scroll_bar import SmoothScrollDelegate
from .tool_tip import ItemViewToolTipDelegate, ItemViewToolTipType


class TableItemDelegate(QStyledItemDelegate):
    """Table 单元格委托类，负责控制单元格的绘制、编辑和交互行为
    
    在 TableView 或 TableWidget 中使用，提供 Fluent 风格的单元格视觉效果，
    包括圆角、悬停高亮、选中状态以及自定义编辑控件等
    """

    def __init__(self, parent: QTableView):
        """初始化委托实例
        
        Args:
            parent: 父对象，通常为关联的表格视图实例
        """
        super().__init__(parent)
        self.margin = 2
        self.hoverRow = -1
        self.pressedRow = -1
        self.selectedRows = set()
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()

        if isinstance(parent, QTableView):
            self.tooltipDelegate = ItemViewToolTipDelegate(parent, 100, ItemViewToolTipType.TABLE)
        else:
            self.tooltipDelegate = ItemViewToolTipDelegate(parent, 100, ItemViewToolTipType.LIST)

    def setHoverRow(self, row: int):
        self.hoverRow = row

    def setPressedRow(self, row: int):
        self.pressedRow = row

    def setSelectedRows(self, indexes: List[QModelIndex]):
        self.selectedRows.clear()
        for index in indexes:
            self.selectedRows.add(index.row())
            if index.row() == self.pressedRow:
                self.pressedRow = -1

    def sizeHint(self, option, index):
        # increase original sizeHint 到 accommodate space needed 用于 边框
        size = super().sizeHint(option, index)
        size = size.grownBy(QMargins(0, self.margin, 0, self.margin))
        return size

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        lineEdit = LineEdit(parent)
        lineEdit.setProperty("transparent", False)
        lineEdit.setStyle(QApplication.style())
        lineEdit.setText(option.text)
        lineEdit.setClearButtonEnabled(True)
        return lineEdit

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2
        x, w = max(8, rect.x()), rect.width()
        if index.column() == 0:
            w -= 8

        editor.setGeometry(x, y, w, rect.height())

    def setCheckedColor(self, light, dark):
        """设置指示器选中状态的颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的颜色
        """
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.parent().viewport().update()

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """绘制行背景
        
        Args:
            painter: 绘制器
            option: 样式选项
            index: 模型索引
        """
        r = 5
        if index.column() == 0:
            rect = option.rect.adjusted(4, 0, r + 1, 0)
            painter.drawRoundedRect(rect, r, r)
        elif index.column() == index.model().columnCount(index.parent()) - 1:
            rect = option.rect.adjusted(-r - 1, 0, -4, 0)
            painter.drawRoundedRect(rect, r, r)
        else:
            rect = option.rect.adjusted(-1, 0, 1, 0)
            painter.drawRect(rect)

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """绘制指示器
        
        Args:
            painter: 绘制器
            option: 样式选项
            index: 模型索引
        """
        y, h = option.rect.y(), option.rect.height()
        ph = round(0.35*h if self.pressedRow == index.row() else 0.257*h)
        painter.setBrush(autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor))
        painter.drawRoundedRect(4, ph + y, 3, h - 2*ph, 1.5, 1.5)

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        super().initStyleOption(option, index)

        # font
        option.font = index.data(Qt.FontRole) or getFont(13)

        # 文本颜色
        textColor = Qt.white if isDarkTheme() else Qt.black
        textBrush = index.data(Qt.ForegroundRole)   # type: QBrush
        if textBrush is not None:
            textColor = QBrush(textBrush).color()

        option.palette.setColor(QPalette.Text, textColor)
        option.palette.setColor(QPalette.HighlightedText, textColor)

    def paint(self, painter, option, index):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置 clipping 区域 的 painter 到 avoid painting outside borders
        painter.setClipping(True)
        painter.setClipRect(option.rect)

        # call original 绘制 method where option.区域 is adjusted 到 account 用于 边框
        option.rect.adjust(0, self.margin, 0, -self.margin)

        # 绘制highlight 背景
        isHover = self.hoverRow == index.row()
        isPressed = self.pressedRow == index.row()
        isAlternate = index.row() % 2 == 0 and self.parent().alternatingRowColors()
        isDark = isDarkTheme()

        c = 255 if isDark else 0
        alpha = 0

        if index.row() not in self.selectedRows:
            if isPressed:
                alpha = 9 if isDark else 6
            elif isHover:
                alpha = 12
            elif isAlternate:
                alpha = 5
        else:
            if isPressed:
                alpha = 15 if isDark else 9
            elif isHover:
                alpha = 25
            else:
                alpha = 17

        if index.data(Qt.ItemDataRole.BackgroundRole):
            painter.setBrush(index.data(Qt.ItemDataRole.BackgroundRole))
        else:
            painter.setBrush(QColor(c, c, c, alpha))

        self._drawBackground(painter, option, index)

        # 绘制指示器
        if index.row() in self.selectedRows and index.column() == 0 and self.parent().horizontalScrollBar().value() == 0:
            self._drawIndicator(painter, option, index)

        if index.data(Qt.CheckStateRole) is not None:
            self._drawCheckBox(painter, option, index)

        painter.restore()
        super().paint(painter, option, index)

    def _drawCheckBox(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        checkState = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))

        isDark = isDarkTheme()

        r = 4.5
        x = option.rect.x() + 15
        y = option.rect.center().y() - 9.5
        rect = QRectF(x, y, 19, 19)

        if checkState == Qt.CheckState.Unchecked:
            painter.setBrush(QColor(0, 0, 0, 26) if isDark else QColor(0, 0, 0, 6))
            painter.setPen(QColor(255, 255, 255, 142) if isDark else QColor(0, 0, 0, 122))
            painter.drawRoundedRect(rect, r, r)
        else:
            color = autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor)
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, r, r)

            if checkState == Qt.CheckState.Checked:
                CheckBoxIcon.ACCEPT.render(painter, rect)
            else:
                CheckBoxIcon.PARTIAL_ACCEPT.render(painter, rect)

        painter.restore()

    def helpEvent(self, event: QHelpEvent, view: QAbstractItemView, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        return self.tooltipDelegate.helpEvent(event, view, option, index)



class TableBase:
    """Table 基类，提供 Fluent 风格表格的通用功能和样式基础设施
    
    封装了 TableView 和 TableWidget 共有的行为，包括滚动条样式、网格线渲染、
    选中策略及主题适配等，通常作为抽象基类使用，建议直接使用 TableWidget 或 TableView
    """

    def __init__(self, *args, **kwargs):
        """初始化表格基类
        
        Args:
            *args: 传递给父类构造方法的位置参数
            **kwargs: 传递给父类构造方法的关键字参数
        """
        super().__init__(*args, **kwargs)
        self.delegate = TableItemDelegate(self)
        self.scrollDelagate = SmoothScrollDelegate(self)
        self._isSelectRightClickedRow = False

        # 设置样式表
        FluentStyleSheet.TABLE_VIEW.apply(self)

        self.setShowGrid(False)
        self.setMouseTracking(True)
        self.setAlternatingRowColors(True)
        self.setItemDelegate(self.delegate)
        self.setSelectionBehavior(TableWidget.SelectRows)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setDefaultSectionSize(38)

        self.entered.connect(lambda i: self._setHoverRow(i.row()))
        self.pressed.connect(lambda i: self._setPressedRow(i.row()))
        self.verticalHeader().sectionClicked.connect(self.selectRow)

    def setBorderVisible(self, isVisible: bool):
        """设置边框的可见性
        
        Args:
            isVisible: 是否显示边框
        """
        self.setProperty("isBorderVisible", isVisible)
        updateDynamicStyle(self)

    def setBorderRadius(self, radius: int):
        """设置边框的半径
        
        Args:
            radius: 圆角半径
        """
        qss = f"QTableView{{border-radius: {radius}px}}"
        setCustomStyleSheet(self, qss, qss)

    def setCheckedColor(self, light, dark):
        """设置选中状态的颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的颜色
        """
        self.delegate.setCheckedColor(light, dark)

    def _setHoverRow(self, row: int):
        """设置悬停行
        
        Args:
            row: 行号
        """
        self.delegate.setHoverRow(row)
        self.viewport().update()

    def _setPressedRow(self, row: int):
        """设置按下行
        
        Args:
            row: 行号
        """
        if self.selectionMode() == QTableView.SelectionMode.NoSelection:
            return

        self.delegate.setPressedRow(row)
        self.viewport().update()

    def _setSelectedRows(self, indexes: List[QModelIndex]):
        if self.selectionMode() == QTableView.SelectionMode.NoSelection:
            return

        self.delegate.setSelectedRows(indexes)
        self.viewport().update()

    def leaveEvent(self, e):
        QTableView.leaveEvent(self, e)
        self._setHoverRow(-1)

    def resizeEvent(self, e):
        QTableView.resizeEvent(self, e)
        self.viewport().update()

    def keyPressEvent(self, e: QKeyEvent):
        QTableView.keyPressEvent(self, e)
        self.updateSelectedRows()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton or self._isSelectRightClickedRow:
            return QTableView.mousePressEvent(self, e)

        index = self.indexAt(e.pos())
        if index.isValid():
            self._setPressedRow(index.row())

        QWidget.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        QTableView.mouseReleaseEvent(self, e)
        self.updateSelectedRows()

        if self.indexAt(e.pos()).row() < 0 or e.button() == Qt.RightButton:
            self._setPressedRow(-1)

    def setItemDelegate(self, delegate: TableItemDelegate):
        self.delegate = delegate
        super().setItemDelegate(delegate)

    def selectAll(self):
        QTableView.selectAll(self)
        self.updateSelectedRows()

    def selectRow(self, row: int):
        QTableView.selectRow(self, row)
        self.updateSelectedRows()

    def clearSelection(self):
        QTableView.clearSelection(self)
        self.updateSelectedRows()

    def setCurrentIndex(self, index: QModelIndex):
        QTableView.setCurrentIndex(self, index)
        self.updateSelectedRows()

    def updateSelectedRows(self):
        self._setSelectedRows(self.selectedIndexes())


class TableWidget(TableBase, QTableWidget):
    """基于项的 Table 部件，提供即用的 Fluent 风格表格
    
    继承 QTableWidget 的便捷接口，适合通过 QTableWidgetItem 直接操作单元格数据、
    表头和行列结构的场景，无需自定义数据模型，适用于数据量较小、需要快速搭建的表格界面
    """

    def __init__(self, parent=None):
        """初始化 Table 部件
        
        Args:
            parent: 父窗口部件，指定父级可确保部件随父窗口一起释放
        """
        super().__init__(parent)
        updateDynamicStyle(self)

    def setCurrentCell(self, row: int, column: int, command=None):
        self.setCurrentItem(self.item(row, column), command)

    def setCurrentItem(self, item: QTableWidgetItem, command=None):
        if not command:
            super().setCurrentItem(item)
        else:
            super().setCurrentItem(item, command)

        self.updateSelectedRows()

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(bool, isSelectRightClickedRow, setSelectRightClickedRow)


class TableView(TableBase, QTableView):
    """基于模型的 Table 视图，支持自定义数据源的 Fluent 风格表格
    
    与 QAbstractTableModel 及其子类配合使用，实现数据与视图的分离，适合处理
    大规模数据、需要自定义数据逻辑或支持动态刷新的复杂表格场景
    """

    def __init__(self, parent=None):
        """初始化 Table 视图
        
        Args:
            parent: 父窗口部件，指定父级可确保部件随父窗口一起释放
        """
        super().__init__(parent)
        updateDynamicStyle(self)

    def isSelectRightClickedRow(self):
        return self._isSelectRightClickedRow

    def setSelectRightClickedRow(self, isSelect: bool):
        self._isSelectRightClickedRow = isSelect

    selectRightClickedRow = Property(bool, isSelectRightClickedRow, setSelectRightClickedRow)
