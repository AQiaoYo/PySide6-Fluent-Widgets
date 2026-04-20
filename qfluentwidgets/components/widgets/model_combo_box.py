# coding: utf-8
"""模型组合框组件

提供基于数据模型的组合框控件，支持通过自定义 model 管理下拉选项的展示与选择
适用于选项数据结构复杂、需要动态更新列表或与其他数据视图保持同步的场景
"""

import sys
from typing import Union, List, Iterable

from PySide6.QtCore import Qt, Signal, QRectF, QPoint, QObject, QEvent, QModelIndex, QAbstractItemModel
from PySide6.QtGui import QPainter, QCursor, QIcon, QStandardItemModel, QStandardItem, QAction
from PySide6.QtWidgets import QPushButton, QApplication

from .menu import RoundMenu, MenuAnimationType, IndicatorMenuItemDelegate
from .line_edit import LineEdit, LineEditButton
from .combo_box import ComboBoxMenu
from ...common.animation import TranslateYAnimation
from ...common.icon import FluentIconBase, isDarkTheme
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont
from ...common.style_sheet import FluentStyleSheet


class ModelComboBoxBase:
    """模型组合框的抽象基类
    
    定义了支持自定义数据模型的组合框基础接口与行为，提供模型绑定和数据同步的通用能力
    子类可继承此类以扩展特定交互行为，实现下拉列表与 QAbstractItemModel 的联动更新
    """

    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)
    activated = Signal(int)
    textActivated = Signal(str)

    def __init__(self, parent=None, **kwargs):
        """初始化抽象模型组合框
        
        Args:
            parent (QWidget): 父控件，用于确定控件在界面中的层级关系
            **kwargs: 额外的关键字参数，将传递给父类的初始化方法
        """
        pass

    def _setUpUi(self):
        self.isHover = False
        self.isPressed = False
        self._currentIndex = -1
        self._maxVisibleItems = -1
        self.dropMenu = None
        self._placeholderText = ""
        self._model = None  # type: QAbstractItemModel

        self.setModel(QStandardItemModel(self))

        FluentStyleSheet.COMBO_BOX.apply(self)
        self.installEventFilter(self)

    def setModel(self, model: QAbstractItemModel):
        if self._model:
            self._model.disconnect(self)

        self._model = model
        model.rowsInserted.connect(self._onModelRowInserted)
        model.dataChanged.connect(self._onModelDataChanged)
        model.rowsRemoved.connect(self._onRowsRemoved)

    def model(self) -> QAbstractItemModel:
        return self._model

    def _onModelRowInserted(self, parentIndex: QModelIndex, first: int, last: int):
        if first <= self.currentIndex():
            self.setCurrentIndex(self.currentIndex() + last - first + 1)

    def _onRowsRemoved(self, parentIndex: QModelIndex, first: int, last: int):
        if last < self.currentIndex():
            self.setCurrentIndex(self.currentIndex() - (last - first + 1))
        elif first < self.currentIndex() <= last:
            self.setCurrentIndex(max(first - 1, 0))

        if self.count() == 0:
            self.clear()

    def _onModelDataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles):
        if Qt.ItemDataRole.EditRole in roles:
            for row in range(topLeft.row(), bottomRight.row() + 1):
                self.setItemText(row, self.itemText(row))
        if Qt.ItemDataRole.DecorationRole in roles:
            for row in range(topLeft.row(), bottomRight.row() + 1):
                self.setItemIcon(row, self.itemIcon(row))

    def eventFilter(self, obj, e: QEvent):
        if obj is self:
            if e.type() == QEvent.Type.MouseButtonPress:
                self.isPressed = True
            elif e.type() == QEvent.Type.MouseButtonRelease:
                self.isPressed = False
            elif e.type() == QEvent.Type.Enter:
                self.isHover = True
            elif e.type() == QEvent.Type.Leave:
                self.isHover = False

        return super().eventFilter(obj, e)

    def insertItem(self, index: int, text: str, userData=None, icon: QIcon = None):
        """在给定索引处插入项

        Args:
            index: 项索引
            text: 项文本
            userData: 用户自定义数据，默认为 None
            icon: 项图标，默认为 None

        Returns:
            插入项的模型索引
        """
        values = {}
        values[Qt.ItemDataRole.EditRole] = text

        if icon:
            values[Qt.ItemDataRole.DecorationRole] = icon

        if userData:
            values[Qt.ItemDataRole.UserRole] = userData

        modelIndex = self._insertItemFromValues(index, values)

        if index <= self.currentIndex():
            self.setCurrentIndex(self.currentIndex() + 1)

        return modelIndex

    def insertItems(self, index: int, texts: Iterable[str]):
        """从给定索引开始批量插入项

        Args:
            index: 起始项索引
            texts: 项文本可迭代对象
        """
        self.blockSignals(True)

        row = index
        for text in texts:
            values = {}
            values[Qt.ItemDataRole.EditRole] = text
            self._insertItemFromValues(index, values)
            row += 1

        self.blockSignals(False)

        if index <= self.currentIndex():
            self.setCurrentIndex(self.currentIndex() + row - index)

    def _insertItemFromValues(self, row: int, values: dict) -> QModelIndex:
        ret = QModelIndex()

        self.model().blockSignals(True)

        row = min(max(0, row), self.model().rowCount())
        if isinstance(self.model(), QStandardItemModel):
            item = QStandardItem()
            for role, value in values.items():
                item.setData(value, role)

            self.model().insertRow(row, item)
            ret = item.index()
        elif self.model().insertRows(row, 1):
            ret = self.model().index(row, 0)
            if values:
                self.model().setItemData(ret, values)

        self.model().blockSignals(False)
        return ret

    def addItem(self, text: str, userData=None, icon: QIcon = None):
        """添加项

        Args:
            text: 项文本
            userData: 用户自定义数据，默认为 None
            icon: 项图标，支持 QIcon 和 FluentIconBase，默认为 None
        """
        self.insertItem(self.model().rowCount(), text, icon, userData)
        if self.count() == 1:
            self.setCurrentIndex(0)

    def addItems(self, texts: Iterable[str]):
        """添加多个项

        Args:
            texts: 项文本可迭代对象
        """
        for text in texts:
            self.addItem(text)

    def removeItem(self, index: int):
        """移除给定索引处的项

        如果移除了当前项，会同步更新当前索引

        Args:
            index: 项索引
        """
        if not self._isValidIndex(index):
            return

        self.model().blockSignals(True)
        self.model().removeRow(index)
        self.model().blockSignals(False)

        if index < self.currentIndex():
            self.setCurrentIndex(self._currentIndex - 1)
        elif index == self.currentIndex():
            if index > 0:
                self.setCurrentIndex(self._currentIndex - 1)
            else:
                self.setText(self.itemText(0))
                self.currentTextChanged.emit(self.currentText())
                self.currentIndexChanged.emit(0)

        if self.count() == 0:
            self.clear()

    def currentIndex(self):
        return self._currentIndex

    def setCurrentIndex(self, index: int):
        """设置当前索引

        Args:
            index: 当前索引
        """
        if not self._isValidIndex(index) or index == self.currentIndex():
            return

        oldText = self.currentText()

        self._currentIndex = index
        self.setText(self.itemText(index))

        if oldText != self.currentText():
            self.currentTextChanged.emit(self.currentText())

        self.currentIndexChanged.emit(index)

    def setText(self, text: str):
        super().setText(text)
        self.adjustSize()

    def currentText(self):
        return self.itemText(self.currentIndex())

    def currentData(self):
        return self.itemData(self.currentIndex())

    def setCurrentText(self, text):
        """设置组合框当前显示的文本

        文本应存在于项列表中

        Args:
            text: 组合框中显示的文本
        """
        if text == self.currentText():
            return

        index = self.findText(text)
        if index >= 0:
            self.setCurrentIndex(index)

    def setItemText(self, index: int, text: str):
        """设置项的文本

        Args:
            index: 项索引
            text: 新项文本
        """
        if not self._isValidIndex(index):
            return

        oldText = self.text()
        self.setItemData(index, text, Qt.ItemDataRole.EditRole)
        if self.currentIndex() == index:
            self.setText(text)
            if oldText != text:
                self.currentTextChanged.emit(text)

    def itemData(self, index: int):
        """返回给定索引处的用户数据

        Args:
            index: 项索引

        Returns:
            给定索引处的用户数据
        """
        return self.model().data(self.model().index(index, 0), Qt.ItemDataRole.UserRole)

    def itemText(self, index: int):
        """返回给定索引处的文本

        Args:
            index: 项索引

        Returns:
            给定索引处的文本
        """
        return self.model().data(self.model().index(index, 0), Qt.ItemDataRole.EditRole) or ""

    def itemIcon(self, index: int):
        """返回给定索引处的图标

        Args:
            index: 项索引

        Returns:
            给定索引处的图标
        """
        return self.model().data(self.model().index(index, 0), Qt.ItemDataRole.DecorationRole) or QIcon()

    def setItemData(self, index: int, value, role=Qt.ItemDataRole.UserRole):
        if self._isValidIndex(index):
            self.model().setData(self.model().index(index, 0), value, role)

    def setItemIcon(self, index: int, icon: Union[str, QIcon, FluentIconBase]):
        """设置给定索引处项的图标

        Args:
            index: 项索引
            icon: 项图标，支持字符串路径、QIcon 或 FluentIconBase
        """
        self.setItemData(index, icon, Qt.ItemDataRole.DecorationRole)

    def _isValidIndex(self, index: int):
        return 0 <= index < self.count()

    def findData(self, data, role=Qt.ItemDataRole.UserRole, flags=Qt.MatchFlag.MatchExactly) -> int:
        """返回包含给定数据的项索引

        Args:
            data: 要查找的数据
            role: 数据角色，默认为 UserRole
            flags: 匹配标志，默认为 MatchExactly

        Returns:
            包含给定数据的项索引，不存在则返回 -1
        """
        mi = self.model().index(0, 0)
        result = self.model().match(mi, role, data, -1, flags | Qt.MatchFlag.MatchRecursive)
        for i in result:
            return i.row()

        return -1

    def findText(self, text: str, flags=Qt.MatchFlag.MatchExactly):
        """返回包含给定文本的项索引

        Args:
            text: 要查找的文本
            flags: 匹配标志，默认为 MatchExactly

        Returns:
            包含给定文本的项索引，不存在则返回 -1
        """
        return self.findData(text, Qt.ItemDataRole.EditRole, flags)

    def clear(self):
        """清空组合框中的所有项"""
        if self.currentIndex() >= 0:
            self.setText('')

        self.model().blockSignals(True)
        self.model().clear()
        self._currentIndex = -1
        self.model().blockSignals(False)

    def count(self):
        """返回组合框中的项数

        Returns:
            组合框中的项数
        """
        return self.model().rowCount()

    def setMaxVisibleItems(self, num: int):
        """设置下拉菜单中可见项的最大数量

        Args:
            num: 可见项的最大数量
        """
        self._maxVisibleItems = num

    def maxVisibleItems(self):
        """返回下拉菜单中可见项的最大数量

        Returns:
            可见项的最大数量
        """
        return self._maxVisibleItems

    def _closeComboMenu(self):
        if not self.dropMenu:
            return

        # drop 菜单 could be deleted before this method
        try:
            self.dropMenu.close()
        except:
            pass

        self.dropMenu = None

    def _onDropMenuClosed(self):
        if sys.platform != "win32":
            self.dropMenu = None
        else:
            pos = self.mapFromGlobal(QCursor.pos())
            if not self.rect().contains(pos):
                self.dropMenu = None

    def _createComboMenu(self):
        return ComboBoxMenu(self)

    def _showComboMenu(self):
        if self.count() == 0:
            return

        menu = self._createComboMenu()
        for i in range(self.count()):
            action = QAction(self.itemIcon(i), self.itemText(i),
                             triggered=lambda c=True, x=i: self._onItemClicked(x))
            menu.addAction(action)

        if menu.view.width() < self.width():
            menu.view.setMinimumWidth(self.width())
            menu.adjustSize()

        menu.setMaxVisibleItems(self.maxVisibleItems())
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        menu.closedSignal.connect(self._onDropMenuClosed)
        self.dropMenu = menu

        # 设置 选中项
        if self.currentIndex() >= 0:
            menu.setDefaultAction(menu.actions()[self.currentIndex()])

        # 根据可用高度选择动画类型.
        x = -menu.width()//2 + menu.layout().contentsMargins().left() + self.width()//2
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def _toggleComboMenu(self):
        if self.dropMenu:
            self._closeComboMenu()
        else:
            self._showComboMenu()

    def _onItemClicked(self, index):
        if index != self.currentIndex():
            self.setCurrentIndex(index)

        self.activated.emit(index)
        self.textActivated.emit(self.currentText())


class ModelComboBox(QPushButton, ModelComboBoxBase):
    """标准模型组合框
    
    支持绑定自定义数据模型的下拉选择控件，可通过 setModel 将数据模型与下拉列表关联
    适用于数据与视图分离的场景，可配合 QListView、QTableView 等实现多视图数据共享
    """

    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)
    activated = Signal(int)
    textActivated = Signal(str)

    def __init__(self, parent=None):
        """初始化模型组合框
        
        Args:
            parent (QWidget): 父控件，用于确定控件在界面中的层级关系
        """
        super().__init__(parent=parent)
        self._isIconVisible = True
        self.arrowAni = TranslateYAnimation(self)
        self._setUpUi()
        setFont(self)

    def setIconVisible(self, isVisible: bool):
        if isVisible == self._isIconVisible or self.currentIndex() < 0:
            return

        self._isIconVisible = isVisible

        if isVisible:
            self._updateIcon()
        else:
            self.setIcon(QIcon())

    def isIconVisible(self):
        return self._isIconVisible

    def _updateIcon(self):
        if not self._isIconVisible:
            return

        icon = self.itemIcon(self.currentIndex())
        if icon and not icon.isNull():
            self.setIcon(icon)
        else:
            self.setIcon(QIcon())

    def setPlaceholderText(self, text: str):
        self._placeholderText = text

        if self.currentIndex() <= 0:
            self._updateTextState(True)
            self.setText(text)

    def setCurrentIndex(self, index: int):
        if index < 0:
            self._currentIndex = -1
            self.setPlaceholderText(self._placeholderText)
        elif self._isValidIndex(index):
            self._updateTextState(False)
            super().setCurrentIndex(index)

        self._updateIcon()

    def clear(self):
        super().clear()
        self.setCurrentIndex(-1)

    def setItemIcon(self, index, icon):
        super().setItemIcon(index, icon)
        if index == self.currentIndex() and self.isIconVisible():
            self.setIcon(icon)

    def _updateTextState(self, isPlaceholder):
        if self.property("isPlaceholderText") == isPlaceholder:
            return

        self.setProperty("isPlaceholderText", isPlaceholder)
        self.setStyle(QApplication.style())

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._toggleComboMenu()

    def paintEvent(self, e):
        QPushButton.paintEvent(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(self.width()-22, self.height()/2-5+self.arrowAni.y, 10, 10)
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")


class EditableModelComboBox(LineEdit, ModelComboBoxBase):
    """可编辑模型组合框
    
    在标准模型组合框基础上增加文本编辑功能，允许用户直接输入内容或从下拉列表选择
    适用于既需要提供预设选项又允许自定义输入的交互场景，如搜索框或标签输入
    """

    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)
    activated = Signal(int)
    textActivated = Signal(str)

    def __init__(self, parent=None):
        """初始化可编辑模型组合框
        
        Args:
            parent (QWidget): 父控件，用于确定控件在界面中的层级关系
        """
        super().__init__(parent=parent)
        self.dropButton = LineEditButton(FIF.ARROW_DOWN, self)
        self._setUpUi()

        self.setTextMargins(0, 0, 29, 0)
        self.dropButton.setFixedSize(30, 25)
        self.hBoxLayout.addWidget(self.dropButton, 0, Qt.AlignmentFlag.AlignRight)

        self.dropButton.clicked.connect(self._toggleComboMenu)
        self.textChanged.connect(self._onComboTextChanged)
        self.returnPressed.connect(self._onReturnPressed)

        FluentStyleSheet.LINE_EDIT.apply(self)

        self.clearButton.clicked.disconnect()
        self.clearButton.clicked.connect(self._onClearButtonClicked)

    def setCompleterMenu(self, menu):
        super().setCompleterMenu(menu)
        menu.activated.connect(self.__onActivated)

    def __onActivated(self, text):
        index = self.findText(text)
        if index >= 0:
            self.setCurrentIndex(index)

    def currentText(self):
        return self.text()

    def setCurrentIndex(self, index: int):
        if index >= self.count() or index == self.currentIndex():
            return

        if index < 0:
            self._currentIndex = -1
            self.setText("")
            self.setPlaceholderText(self._placeholderText)
        else:
            self._currentIndex = index
            self.setText(self.itemText(index))

    def clear(self):
        ModelComboBoxBase.clear(self)

    def setPlaceholderText(self, text: str):
        self._placeholderText = text
        super().setPlaceholderText(text)

    def _onReturnPressed(self):
        if not self.text():
            return

        index = self.findText(self.text())
        if index >= 0 and index != self.currentIndex():
            self._currentIndex = index
            self.currentIndexChanged.emit(index)
        elif index == -1:
            self.addItem(self.text())
            self.setCurrentIndex(self.count() - 1)

    def _onComboTextChanged(self, text: str):
        self._currentIndex = -1
        self.currentTextChanged.emit(text)

        index = self.findText(text)
        if index >= 0:
            self._currentIndex = index
            self.currentIndexChanged.emit(index)

    def _onDropMenuClosed(self):
        self.dropMenu = None

    def _onClearButtonClicked(self):
        LineEdit.clear(self)
        self._currentIndex = -1