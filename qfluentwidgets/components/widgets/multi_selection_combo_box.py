# coding: utf-8
"""多选组合框组件

提供支持多项勾选的组合框控件，选中项会以 token 标签的形式显示在输入区域内，
适用于标签筛选、角色分配、分类勾选等需要同时选择多个选项的场景
"""

from typing import Iterable, List, Union

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from .button import TransparentToolButton
from .combo_box import ComboItem
from .menu import MenuAnimationType, RoundMenu
from ...common.animation import TranslateYAnimation
from ...common.font import setFont
from ...common.icon import FluentIcon as FIF
from ...common.icon import FluentIconBase, isDarkTheme
from ...common.style_sheet import FluentStyleSheet, addStyleSheet, themeColor


class MultiSelectionComboItem(ComboItem):
    """多选组合框项"""

    def __init__(
        self,
        text: str,
        icon: Union[str, QIcon, FluentIconBase] = None,
        userData=None,
        isEnabled=True,
        isChecked=False,
    ):
        super().__init__(text, icon, userData, isEnabled)
        self.isChecked = isChecked


class MultiSelectionToken(QWidget):
    """组合框已选 token 标签"""

    closed = Signal()
    clicked = Signal()

    def __init__(self, text: str, parent: QWidget = None):
        """初始化 token

        Args:
            text: token 显示文本
            parent: 父控件
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.textLabel = QLabel(text, self)
        self.textLabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        setFont(self.textLabel, 13)

        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.closeButton.setFixedSize(14, 14)
        self.closeButton.setIconSize(QSize(9, 9))
        self.closeButton.clicked.connect(self.closed)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(10, 0, 6, 0)
        self.hBoxLayout.setSpacing(6)
        self.hBoxLayout.addWidget(self.textLabel, 0, Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.closeButton, 0, Qt.AlignVCenter)

        self.setFixedHeight(28)

    def text(self) -> str:
        return self.textLabel.text()

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(28)
        return hint

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and not self.closeButton.geometry().contains(
            e.pos()
        ):
            self.clicked.emit()

        super().mouseReleaseEvent(e)


class MultiSelectionComboMenuItem(QWidget):
    """多选组合框菜单项"""

    toggled = Signal(bool)
    _ITEM_HEIGHT = 40
    _BG_LEFT_MARGIN = 2
    _BG_RIGHT_MARGIN = 2
    _BG_V_MARGIN = 2
    _CONTENT_LEFT = 14
    _CONTENT_RIGHT = 10
    _INDICATOR_SIZE = 18
    _INDICATOR_SPACING = 14

    def __init__(
        self, text: str, checked=False, isEnabled=True, parent: QWidget = None
    ):
        """初始化菜单项

        Args:
            text: 菜单项文本
            checked: 是否选中
            isEnabled: 是否启用
            parent: 父控件
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setCursor(Qt.PointingHandCursor)
        self._text = text
        self._isHover = False
        self._isChecked = checked
        self._isItemEnabled = isEnabled
        setFont(self)
        self.setFixedHeight(self._ITEM_HEIGHT)

    def text(self) -> str:
        return self._text

    def isChecked(self) -> bool:
        return self._isChecked

    def setChecked(self, isChecked: bool):
        if self._isChecked == isChecked:
            return

        self._isChecked = isChecked
        self.update()
        self.toggled.emit(self._isChecked)

    def setEnabled(self, isEnabled: bool):
        super().setEnabled(isEnabled)
        self._isItemEnabled = isEnabled
        self.update()

    def sizeHint(self):
        fm = self.fontMetrics()
        textWidth = fm.boundingRect(self._text).width()
        width = (
            self._BG_LEFT_MARGIN
            + self._BG_RIGHT_MARGIN
            + self._CONTENT_LEFT
            + self._INDICATOR_SIZE
            + self._INDICATOR_SPACING
            + textWidth
            + self._CONTENT_RIGHT
        )
        return QSize(max(220, width), self._ITEM_HEIGHT)

    def _itemBackgroundColor(self):
        if self._isChecked:
            return QColor(255, 255, 255, 28) if isDarkTheme() else QColor(0, 0, 0, 15)
        if self._isHover:
            return QColor(255, 255, 255, 8) if isDarkTheme() else QColor(0, 0, 0, 4)
        return Qt.transparent

    def _indicatorBorderColor(self):
        if self._isChecked:
            return Qt.transparent
        return QColor(255, 255, 255, 120) if isDarkTheme() else QColor(0, 0, 0, 76)

    def _indicatorBrushColor(self):
        if self._isChecked:
            return themeColor()
        if self._isHover:
            return QColor(255, 255, 255, 10) if isDarkTheme() else QColor(0, 0, 0, 4)
        return QColor(0, 0, 0, 0)

    def _textColor(self):
        if not self._isItemEnabled:
            return QColor(255, 255, 255, 92) if isDarkTheme() else QColor(0, 0, 0, 92)
        return QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0)

    def enterEvent(self, e):
        self._isHover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._isHover = False
        self.update()
        super().leaveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._isItemEnabled:
            self.setChecked(not self.isChecked())

        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )

        backgroundRect = self.rect().adjusted(
            self._BG_LEFT_MARGIN,
            self._BG_V_MARGIN,
            -self._BG_RIGHT_MARGIN,
            -self._BG_V_MARGIN,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._itemBackgroundColor())
        painter.drawRoundedRect(backgroundRect, 6, 6)

        indicatorY = (self.height() - self._INDICATOR_SIZE) // 2
        indicatorRect = QRect(
            backgroundRect.x() + self._CONTENT_LEFT,
            indicatorY,
            self._INDICATOR_SIZE,
            self._INDICATOR_SIZE,
        )

        painter.setPen(QPen(self._indicatorBorderColor(), 1))
        painter.setBrush(self._indicatorBrushColor())
        painter.drawRoundedRect(indicatorRect, 5.5, 5.5)

        if self._isChecked:
            FIF.ACCEPT.render(
                painter,
                QRectF(
                    indicatorRect.x() + 4,
                    indicatorRect.y() + 4,
                    indicatorRect.width() - 8,
                    indicatorRect.height() - 8,
                ),
                fill="white",
            )

        textX = indicatorRect.x() + indicatorRect.width() + self._INDICATOR_SPACING
        textRight = backgroundRect.right() - self._CONTENT_RIGHT
        textRect = QRect(textX, 0, max(0, textRight - textX + 1), self.height())
        painter.setPen(self._textColor())
        painter.setFont(self.font())
        painter.drawText(textRect, Qt.AlignVCenter | Qt.AlignLeft, self._text)


class MultiSelectionComboBoxMenu(RoundMenu):
    """多选组合框菜单"""

    itemToggled = Signal(int, bool)

    def __init__(self, parent: QWidget = None):
        """初始化菜单

        Args:
            parent: 父控件
        """
        super().__init__("", parent)
        self._itemWidgets = []
        self._items = []

        self.hBoxLayout.setContentsMargins(3, 6, 3, 6)
        self.view.setViewportMargins(0, 4, 0, 4)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setObjectName("comboListWidget")
        self.setItemHeight(40)
        self.setShadowEffect(blurRadius=20, offset=(0, 6), color=QColor(0, 0, 0, 28))
        addStyleSheet(self, FluentStyleSheet.MULTI_SELECTION_COMBO_BOX)

    def addCheckItem(self, index: int, text: str, checked=False, isEnabled=True):
        """添加可勾选菜单项

        Args:
            index: 项索引
            text: 项文本
            checked: 是否选中
            isEnabled: 是否启用
        """
        widget = MultiSelectionComboMenuItem(text, checked, isEnabled, self)
        widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        widget.toggled.connect(lambda state, x=index: self.itemToggled.emit(x, state))

        self.addWidget(widget, selectable=False)

        item = self.view.item(self.view.count() - 1)
        if item:
            item.setSizeHint(widget.sizeHint())

        self._itemWidgets.append(widget)
        self._items.append(item)

    def setItemWidth(self, width: int):
        """统一设置菜单项宽度

        Args:
            width: 目标宽度 (含菜单 contentsMargins)
        """
        margins = self.layout().contentsMargins()
        viewWidth = max(1, width - margins.left() - margins.right())

        self.view.setMinimumWidth(viewWidth)

        for item, widget in zip(self._items, self._itemWidgets):
            if not item or not widget:
                continue

            hint = widget.sizeHint()
            item.setSizeHint(QSize(max(viewWidth, hint.width()), hint.height()))

        self.view.adjustSize()
        self.adjustSize()

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        self.view.adjustSize(pos, aniType)
        self.adjustSize()
        return super().exec(pos, ani, aniType)


class MultiSelectionComboBox(QWidget):
    """多选组合框，用于同时选择多个选项

    选中项会以 token 标签形式显示在控件内部，适用于需要在有限空间内展示多选结果的场景，
    如筛选器、标签选择器和角色分配界面

    构造函数重载:
        * MultiSelectionComboBox(parent: QWidget = None)
    """

    itemSelectionChanged = Signal(int, bool)
    checkedIndexesChanged = Signal(list)
    checkedTextsChanged = Signal(list)
    checkedDataChanged = Signal(list)

    def __init__(self, parent: QWidget = None):
        """初始化多选组合框

        Args:
            parent: 父控件
        """
        super().__init__(parent)
        self.items = []  # type: List[MultiSelectionComboItem]
        self.dropMenu = None
        self._maxVisibleItems = 8
        self._placeholderText = ""
        self._contentHeight = 28
        self.isHover = False
        self.isPressed = False
        self.arrowAni = TranslateYAnimation(self)

        self.setAttribute(Qt.WA_StyledBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        FluentStyleSheet.MULTI_SELECTION_COMBO_BOX.apply(self)
        setFont(self)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(False)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.tokenContainer = QWidget(self.scrollArea)
        self.tokenContainer.setFixedHeight(self._contentHeight)
        self.tokenLayout = QHBoxLayout(self.tokenContainer)
        self.tokenLayout.setContentsMargins(0, 0, 0, 0)
        self.tokenLayout.setSpacing(6)
        self.tokenLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scrollArea.setWidget(self.tokenContainer)

        self.scrollArea.setObjectName("tokenScrollArea")
        self.tokenContainer.setObjectName("tokenContainer")

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(8, 5, 32, 5)
        self.hBoxLayout.addWidget(self.scrollArea, 1)

        self.scrollArea.viewport().installEventFilter(self)
        self.tokenContainer.installEventFilter(self)

        self._refreshTokens()

    def eventFilter(self, obj, e):
        if obj in [self.scrollArea.viewport(), self.tokenContainer]:
            if e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                self.isPressed = True
                self._updateStyleState()
            elif e.type() == QEvent.MouseButtonRelease and e.button() == Qt.LeftButton:
                self.isPressed = False
                self._updateStyleState()
                self._toggleComboMenu()
                return True

        return super().eventFilter(obj, e)

    def enterEvent(self, e):
        self.isHover = True
        self._updateStyleState()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.isHover = False
        self.isPressed = False
        self._updateStyleState()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.isPressed = True
            self._updateStyleState()

        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.isPressed = False
            self._updateStyleState()
            self._toggleComboMenu()

        super().mouseReleaseEvent(e)

    def _updateStyleState(self):
        self.setProperty("isHover", self.isHover)
        self.setProperty("isPressed", self.isPressed)
        self.setStyle(QApplication.style())
        self.update()

    def _clearTokenWidgets(self):
        while self.tokenLayout.count():
            item = self.tokenLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _refreshTokens(self):
        self._clearTokenWidgets()

        indexes = self.checkedIndexes()
        if not indexes:
            self.setProperty("isPlaceholderText", True)
        else:
            self.setProperty("isPlaceholderText", False)
            for index in indexes:
                token = MultiSelectionToken(self.items[index].text, self.tokenContainer)
                token.closed.connect(lambda x=index: self.setItemChecked(x, False))
                token.clicked.connect(self._toggleComboMenu)
                self.tokenLayout.addWidget(token, 0, Qt.AlignVCenter)
                token.show()

        self.tokenContainer.adjustSize()
        self.tokenContainer.resize(
            self.tokenContainer.sizeHint().width(), self._contentHeight
        )
        self.tokenContainer.show()
        self.setStyle(QApplication.style())

    def paintEvent(self, e):
        QWidget.paintEvent(self, e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isHover:
            painter.setOpacity(0.8)
        elif self.isPressed:
            painter.setOpacity(0.7)

        rect = QRectF(
            self.width() - 22, self.height() / 2 - 5 + self.arrowAni.y, 10, 10
        )
        if isDarkTheme():
            FIF.ARROW_DOWN.render(painter, rect)
        else:
            FIF.ARROW_DOWN.render(painter, rect, fill="#646464")

        if self.property("isPlaceholderText") and self._placeholderText:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)
            painter.setFont(self.font())
            painter.setPen(
                Qt.GlobalColor.white if isDarkTheme() else Qt.GlobalColor.black
            )
            painter.setOpacity(0.6063)
            textRect = self.rect().adjusted(12, 0, -32, 0)
            painter.drawText(
                textRect, Qt.AlignVCenter | Qt.AlignLeft, self._placeholderText
            )
            painter.restore()

    def addItem(
        self,
        text,
        icon: Union[str, QIcon, FluentIconBase] = None,
        userData=None,
        isEnabled=True,
    ):
        """添加项

        Args:
            text: 项文本
            icon: 项图标
            userData: 用户数据
            isEnabled: 是否启用
        """
        self.items.append(MultiSelectionComboItem(text, icon, userData, isEnabled))
        self._refreshTokens()

    def addItems(self, texts: Iterable[str]):
        """添加多个项

        Args:
            texts: 项文本列表
        """
        for text in texts:
            self.addItem(text)

    def insertItem(
        self,
        index: int,
        text: str,
        icon: Union[str, QIcon, FluentIconBase] = None,
        userData=None,
        isEnabled=True,
    ):
        """插入项

        Args:
            index: 项索引
            text: 项文本
            icon: 项图标
            userData: 用户数据
            isEnabled: 是否启用
        """
        index = min(max(0, index), len(self.items))
        self.items.insert(
            index, MultiSelectionComboItem(text, icon, userData, isEnabled)
        )
        self._refreshTokens()

    def removeItem(self, index: int):
        """移除项

        Args:
            index: 项索引
        """
        if not 0 <= index < len(self.items):
            return

        changed = self.items[index].isChecked
        self.items.pop(index)
        self._refreshTokens()
        if changed:
            self._emitSelectionSignals()

    def clear(self):
        """清空所有项"""
        self.items.clear()
        self._refreshTokens()
        self._emitSelectionSignals()

    def count(self):
        """返回项数"""
        return len(self.items)

    def itemText(self, index: int):
        """返回项文本"""
        if not 0 <= index < len(self.items):
            return ""

        return self.items[index].text

    def itemData(self, index: int):
        """返回项数据"""
        if not 0 <= index < len(self.items):
            return None

        return self.items[index].userData

    def itemIcon(self, index: int):
        """返回项图标"""
        if not 0 <= index < len(self.items):
            return QIcon()

        return self.items[index].icon

    def setItemText(self, index: int, text: str):
        """设置项文本

        Args:
            index: 项索引
            text: 新文本
        """
        if not 0 <= index < len(self.items):
            return

        self.items[index].text = text
        self._refreshTokens()

    def setItemData(self, index: int, value):
        """设置项数据

        Args:
            index: 项索引
            value: 用户数据
        """
        if 0 <= index < len(self.items):
            self.items[index].userData = value

    def setItemIcon(self, index: int, icon: Union[str, QIcon, FluentIconBase]):
        """设置项图标

        Args:
            index: 项索引
            icon: 图标
        """
        if 0 <= index < len(self.items):
            self.items[index].icon = icon

    def setItemEnabled(self, index: int, isEnabled: bool):
        """设置项启用状态

        Args:
            index: 项索引
            isEnabled: 是否启用
        """
        if 0 <= index < len(self.items):
            self.items[index].isEnabled = isEnabled

    def isItemChecked(self, index: int) -> bool:
        """返回项是否选中"""
        if not 0 <= index < len(self.items):
            return False

        return self.items[index].isChecked

    def setItemChecked(self, index: int, isChecked: bool):
        """设置项选中状态

        Args:
            index: 项索引
            isChecked: 是否选中
        """
        if not 0 <= index < len(self.items):
            return

        item = self.items[index]
        if item.isChecked == isChecked or (isChecked and not item.isEnabled):
            return

        item.isChecked = isChecked
        self._refreshTokens()
        self.itemSelectionChanged.emit(index, isChecked)
        self._emitSelectionSignals()

    def checkedIndexes(self) -> List[int]:
        """返回已选索引列表"""
        return [i for i, item in enumerate(self.items) if item.isChecked]

    def checkedTexts(self) -> List[str]:
        """返回已选文本列表"""
        return [self.items[i].text for i in self.checkedIndexes()]

    def checkedData(self) -> List[object]:
        """返回已选数据列表"""
        return [self.items[i].userData for i in self.checkedIndexes()]

    def setCheckedIndexes(self, indexes: Iterable[int]):
        """批量设置已选索引

        Args:
            indexes: 已选索引列表
        """
        selected = set(i for i in indexes if 0 <= i < len(self.items))
        changed = False

        for i, item in enumerate(self.items):
            checked = i in selected and item.isEnabled
            if item.isChecked != checked:
                item.isChecked = checked
                self.itemSelectionChanged.emit(i, checked)
                changed = True

        if not changed:
            return

        self._refreshTokens()
        self._emitSelectionSignals()

    def setCheckedTexts(self, texts: Iterable[str]):
        """按文本批量设置已选项

        Args:
            texts: 已选文本列表
        """
        selected = set(texts)
        self.setCheckedIndexes(
            [i for i, item in enumerate(self.items) if item.text in selected]
        )

    def clearChecked(self):
        """清空已选项"""
        self.setCheckedIndexes([])

    def findText(self, text: str):
        """查找文本对应索引"""
        for i, item in enumerate(self.items):
            if item.text == text:
                return i

        return -1

    def findData(self, data):
        """查找数据对应索引"""
        for i, item in enumerate(self.items):
            if item.userData == data:
                return i

        return -1

    def setPlaceholderText(self, text: str):
        """设置占位文本

        Args:
            text: 占位文本
        """
        self._placeholderText = text
        self._refreshTokens()

    def placeholderText(self) -> str:
        """返回占位文本"""
        return self._placeholderText

    def setMaxVisibleItems(self, num: int):
        """设置菜单最大可见项数

        Args:
            num: 最大可见项数
        """
        self._maxVisibleItems = num

    def maxVisibleItems(self):
        """返回菜单最大可见项数"""
        return self._maxVisibleItems

    def _emitSelectionSignals(self):
        self.checkedIndexesChanged.emit(self.checkedIndexes())
        self.checkedTextsChanged.emit(self.checkedTexts())
        self.checkedDataChanged.emit(self.checkedData())

    def _closeComboMenu(self):
        if not self.dropMenu:
            return

        try:
            self.dropMenu.close()
        except:
            pass

        self.dropMenu = None

    def _onDropMenuClosed(self):
        pos = self.mapFromGlobal(QCursor.pos())
        if not self.rect().contains(pos):
            self.dropMenu = None

    def _createComboMenu(self):
        return MultiSelectionComboBoxMenu(self)

    def _showComboMenu(self):
        if not self.items:
            return

        menu = self._createComboMenu()
        for i, item in enumerate(self.items):
            menu.addCheckItem(i, item.text, item.isChecked, item.isEnabled)

        menu.setMaxVisibleItems(self.maxVisibleItems())
        menu.setAttribute(Qt.WA_DeleteOnClose)
        menu.closedSignal.connect(self._onDropMenuClosed)
        menu.itemToggled.connect(self._onMenuItemToggled)
        self.dropMenu = menu

        menu.setItemWidth(self.width())

        x = (
            -menu.width() // 2
            + menu.layout().contentsMargins().left()
            + self.width() // 2
        )
        pd = self.mapToGlobal(QPoint(x, self.height() + 6))
        pu = self.mapToGlobal(QPoint(x, 0))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)
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

    def _onMenuItemToggled(self, index: int, isChecked: bool):
        self.setItemChecked(index, isChecked)
