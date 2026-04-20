# coding: utf-8
"""输入框组件

提供一系列符合 Fluent Design 风格的输入类控件，包括单行输入框、搜索框、密码框、富文本编辑框和纯文本编辑框等
适用于需要用户输入或文本展示的场景，支持圆角样式、焦点动画和补全菜单等特性
"""

from typing import List, Union
from PySide6.QtCore import QSize, Qt, QRectF, Signal, QPoint, QTimer, QEvent, QAbstractItemModel, Property, QModelIndex
from PySide6.QtGui import QPainter, QPainterPath, QIcon, QColor, QAction
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QToolButton, QTextEdit,
                               QPlainTextEdit, QCompleter, QStyle, QWidget, QTextBrowser)


from ...common.style_sheet import FluentStyleSheet, themeColor, updateDynamicStyle
from ...common.icon import isDarkTheme, FluentIconBase, drawIcon
from ...common.icon import FluentIcon as FIF
from ...common.font import setFont
from ...common.color import FluentSystemColor, autoFallbackThemeColor
from .tool_tip import ToolTipFilter
from .menu import LineEditMenu, TextEditMenu, RoundMenu, MenuAnimationType, IndicatorMenuItemDelegate
from .scroll_bar import SmoothScrollDelegate


class LineEditButton(QToolButton):
    """LineEdit 右侧功能按钮
    
    通常用于在输入框尾部添加图标按钮，例如清除内容、搜索或自定义操作按钮
    支持鼠标悬停和点击态的 Fluent 风格样式渲染
    """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], parent=None):
        """初始化按钮
        
        Args:
            icon: 按钮显示的图标，可以是 QIcon、FluentIcon 或 Icon 类型
            parent: 父级窗口部件，通常为 LineEdit 实例，指定后该按钮将随父控件一同销毁
        """
        super().__init__(parent=parent)
        self._icon = icon
        self._action = None
        self.isPressed = False
        self.setFixedSize(31, 23)
        self.setIconSize(QSize(10, 10))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName('lineEditButton')
        FluentStyleSheet.LINE_EDIT.apply(self)

    def setAction(self, action: QAction):
        self._action = action
        self._onActionChanged()

        self.clicked.connect(action.trigger)
        action.toggled.connect(self.setChecked)
        action.changed.connect(self._onActionChanged)

        self.installEventFilter(ToolTipFilter(self, 700))

    def _onActionChanged(self):
        action = self.action()
        self.setIcon(action.icon())
        self.setToolTip(action.toolTip())
        self.setEnabled(action.isEnabled())
        self.setCheckable(action.isCheckable())
        self.setChecked(action.isChecked())

    def action(self):
        return self._action

    def setIcon(self, icon: Union[str, FluentIconBase, QIcon]):
        self._icon = icon
        self.update()

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        iw, ih = self.iconSize().width(), self.iconSize().height()
        w, h = self.width(), self.height()
        rect = QRectF((w - iw)/2, (h - ih)/2, iw, ih)

        if self.isPressed:
            painter.setOpacity(0.7)

        if isDarkTheme():
            drawIcon(self._icon, painter, rect)
        else:
            drawIcon(self._icon, painter, rect, fill='#656565')


class LineEdit(QLineEdit):
    """单行文本输入框
    
    支持圆角边框、聚焦高亮动画和占位符文本，可配合 CompleterMenu 实现自动补全功能
    适用于表单填写、关键词输入等需要单行文本的场景
    """

    def __init__(self, parent=None):
        """初始化输入框
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent=parent)
        self._isClearButtonEnabled = False
        self._completer = None  # type: QCompleter
        self._completerMenu = None  # type: CompleterMenu
        self._isError = False
        self.lightFocusedBorderColor = QColor()
        self.darkFocusedBorderColor = QColor()

        self.leftButtons = []   # type: 列表[LineEditButton]
        self.rightButtons = []  # type: 列表[LineEditButton]

        self.setProperty("transparent", True)
        FluentStyleSheet.LINE_EDIT.apply(self)
        self.setFixedHeight(33)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        setFont(self)

        self.hBoxLayout = QHBoxLayout(self)
        self.clearButton = LineEditButton(FIF.CLOSE, self)

        self.clearButton.setFixedSize(29, 25)
        self.clearButton.hide()

        self.hBoxLayout.setSpacing(3)
        self.hBoxLayout.setContentsMargins(4, 4, 4, 4)
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.hBoxLayout.addWidget(self.clearButton, 0, Qt.AlignRight)

        self.clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.__onTextChanged)
        self.textEdited.connect(self.__onTextEdited)

    def isError(self):
        return self._isError

    def setError(self, isError: bool):
        """设置错误状态"""
        if isError == self.isError():
            return

        self._isError = isError
        self.update()

    def setCustomFocusedBorderColor(self, light, dark):
        """设置聚焦时的边框颜色

        Args:
            light: 亮色主题下的边框颜色，可以是 str、QColor 或 Qt.GlobalColor
            dark: 暗色主题下的边框颜色，可以是 str、QColor 或 Qt.GlobalColor
        """
        self.lightFocusedBorderColor = QColor(light)
        self.darkFocusedBorderColor = QColor(dark)
        self.update()

    def focusedBorderColor(self):
        if self.isError():
            return FluentSystemColor.CRITICAL_FOREGROUND.color()

        return autoFallbackThemeColor(self.lightFocusedBorderColor, self.darkFocusedBorderColor)

    def setClearButtonEnabled(self, enable: bool):
        self._isClearButtonEnabled = enable
        self._adjustTextMargins()

    def isClearButtonEnabled(self) -> bool:
        return self._isClearButtonEnabled

    def setCompleter(self, completer: QCompleter):
        self._completer = completer

    def completer(self):
        return self._completer

    def addAction(self, action: QAction, position=QLineEdit.ActionPosition.TrailingPosition):
        QWidget.addAction(self, action)

        button = LineEditButton(action.icon())
        button.setAction(action)
        button.setFixedWidth(29)

        if position == QLineEdit.ActionPosition.LeadingPosition:
            self.hBoxLayout.insertWidget(len(self.leftButtons), button, 0, Qt.AlignLeading)
            if not self.leftButtons:
                self.hBoxLayout.insertStretch(1, 1)

            self.leftButtons.append(button)
        else:
            self.rightButtons.append(button)
            self.hBoxLayout.addWidget(button, 0, Qt.AlignRight)

        self._adjustTextMargins()

    def addActions(self, actions, position=QLineEdit.ActionPosition.TrailingPosition):
        for action in actions:
            self.addAction(action, position)

    def _adjustTextMargins(self):
        left = len(self.leftButtons) * 30
        right = len(self.rightButtons) * 30 + 28 * self.isClearButtonEnabled()
        m = self.textMargins()
        self.setTextMargins(left, m.top(), right, m.bottom())

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.clearButton.hide()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        if self.isClearButtonEnabled():
            self.clearButton.setVisible(bool(self.text()))

    def __onTextChanged(self, text):
        """文本改变时的槽函数"""
        if self.isClearButtonEnabled():
            self.clearButton.setVisible(bool(text) and self.hasFocus())

    def __onTextEdited(self, text):
        if not self.completer():
            return

        if self.text():
            QTimer.singleShot(50, self._showCompleterMenu)
        elif self._completerMenu:
            self._completerMenu.close()

    def setCompleterMenu(self, menu):
        """设置补全菜单

        Args:
            menu: CompleterMenu 实例
        """
        menu.activated.connect(self._completer.activated)
        menu.indexActivated.connect(lambda idx: self._completer.activated[QModelIndex].emit(idx))
        self._completerMenu = menu

    def _showCompleterMenu(self):
        if not self.completer() or not self.text():
            return

        # 创建菜单
        if not self._completerMenu:
            self.setCompleterMenu(CompleterMenu(self))

        # 添加 菜单 项
        self.completer().setCompletionPrefix(self.text())
        changed = self._completerMenu.setCompletion(self.completer().completionModel(), self.completer().completionColumn())
        self._completerMenu.setMaxVisibleItems(self.completer().maxVisibleItems())

        # 显示菜单
        if changed:
            self._completerMenu.popup()

    def contextMenuEvent(self, e):
        menu = LineEditMenu(self)
        menu.exec(e.globalPos(), ani=True)

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self.hasFocus():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        m = self.contentsMargins()
        path = QPainterPath()
        w, h = self.width()-m.left()-m.right(), self.height()
        path.addRoundedRect(QRectF(m.left(), h-10, w, 10), 5, 5)

        rectPath = QPainterPath()
        rectPath.addRect(m.left(), h-10, w, 8)
        path = path.subtracted(rectPath)

        painter.fillPath(path, self.focusedBorderColor())


class CompleterMenu(RoundMenu):
    """输入补全菜单
    
    在 LineEdit 输入时弹出，提供匹配的候选词列表，支持键盘上下选择和回车确认
    适用于搜索建议、历史记录补全等需要快速输入的场景
    """

    activated = Signal(str)
    indexActivated = Signal(QModelIndex)

    def __init__(self, lineEdit: LineEdit):
        """初始化补全菜单
        
        Args:
            lineEdit: 关联的 LineEdit 实例，用于获取当前文本和插入补全结果，菜单将跟随该输入框定位
        """
        super().__init__()
        self.items = []
        self.indexes = []
        self.lineEdit = lineEdit

        self.view.setViewportMargins(0, 2, 0, 6)
        self.view.setObjectName('completerListWidget')
        self.view.setItemDelegate(IndicatorMenuItemDelegate())
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.installEventFilter(self)
        self.setItemHeight(33)

    def setCompletion(self, model: QAbstractItemModel, column=0):
        """设置补全模型"""
        items = []
        self.indexes.clear()
        for i in range(model.rowCount()):
            items.append(model.data(model.index(i, column)))
            self.indexes.append(model.index(i, column))

        if self.items == items and self.isVisible():
            return False

        self.setItems(items)
        return True

    def setItems(self, items: List[str]):
        """设置补全项"""
        self.view.clear()

        self.items = items
        self.view.addItems(items)

        for i in range(self.view.count()):
            item = self.view.item(i)
            item.setSizeHint(QSize(1, self.itemHeight))

    def _onItemClicked(self, item):
        self._hideMenu(False)
        self._onCompletionItemSelected(item.text(), self.view.row(item))

    def eventFilter(self, obj, e: QEvent):
        if e.type() != QEvent.KeyPress:
            return super().eventFilter(obj, e)

        # redirect input 到 行编辑器
        self.lineEdit.event(e)
        self.view.event(e)

        if e.key() == Qt.Key_Escape:
            self.close()
        if e.key() in [Qt.Key_Enter, Qt.Key_Return] and self.view.currentRow() >= 0:
            self._onCompletionItemSelected(self.view.currentItem().text(), self.view.currentRow())
            self.close()

        return super().eventFilter(obj, e)

    def _onCompletionItemSelected(self, text, row):
        self.lineEdit.setText(text)
        self.activated.emit(text)

        if 0 <= row < len(self.indexes):
            self.indexActivated.emit(self.indexes[row])

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)

    def popup(self):
        """显示菜单"""
        if not self.items:
            return self.close()

        # 调整菜单 大小
        p = self.lineEdit
        if self.view.width() < p.width():
            self.view.setMinimumWidth(p.width())
            self.adjustSize()

        # 根据可用高度选择动画类型.
        x = -self.width()//2 + self.layout().contentsMargins().left() + p.width()//2
        y = p.height() - self.layout().contentsMargins().top() + 2
        pd = p.mapToGlobal(QPoint(x, y))
        hd = self.view.heightForAnimation(pd, MenuAnimationType.FADE_IN_DROP_DOWN)

        pu = p.mapToGlobal(QPoint(x, 7))
        hu = self.view.heightForAnimation(pu, MenuAnimationType.FADE_IN_PULL_UP)

        if hd >= hu:
            pos = pd
            aniType = MenuAnimationType.FADE_IN_DROP_DOWN
        else:
            pos = pu
            aniType = MenuAnimationType.FADE_IN_PULL_UP

        self.view.adjustSize(pos, aniType)

        # 更新边框 style
        self.view.setProperty('dropDown', aniType == MenuAnimationType.FADE_IN_DROP_DOWN)
        updateDynamicStyle(self.view)

        self.adjustSize()
        self.exec(pos, aniType=aniType)

        # 移除 焦点 的 菜单
        self.view.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.NoFocus)
        p.setFocus()


class SearchLineEdit(LineEdit):
    """搜索输入框
    
    内置搜索图标和清除按钮，支持占位符文本和自动补全，专为搜索场景优化
    适用于工具栏搜索、列表过滤等需要即时查询的界面
    """

    searchSignal = Signal(str)
    clearSignal = Signal()

    def __init__(self, parent=None):
        """初始化搜索框
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent)
        self.searchButton = LineEditButton(FIF.SEARCH, self)

        self.hBoxLayout.addWidget(self.searchButton, 0, Qt.AlignRight)
        self.setClearButtonEnabled(True)
        self.setTextMargins(0, 0, 59, 0)

        self.searchButton.clicked.connect(self.search)
        self.clearButton.clicked.connect(self.clearSignal)

    def search(self):
        """发射搜索信号"""
        text = self.text().strip()
        if text:
            self.searchSignal.emit(text)
        else:
            self.clearSignal.emit()

    def setClearButtonEnabled(self, enable: bool):
        self._isClearButtonEnabled = enable
        self.setTextMargins(0, 0, 28*enable+30, 0)


class EditLayer(QWidget):
    """单元格编辑层
    
    通常用于表格或列表的单元格就地编辑，提供覆盖于单元格之上的编辑交互层
    支持双击进入编辑模式和焦点丢失自动提交修改
    """

    def __init__(self, parent):
        """初始化编辑层
        
        Args:
            parent: 父级窗口部件，通常为表格或列表控件，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        parent.installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj is self.parent() and e.type() == QEvent.Resize:
            self.resize(e.size())

        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        if not self.parent().hasFocus():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        m = self.contentsMargins()
        path = QPainterPath()
        w, h = self.width()-m.left()-m.right(), self.height()
        path.addRoundedRect(QRectF(m.left(), h-10, w, 10), 5, 5)

        rectPath = QPainterPath()
        rectPath.addRect(m.left(), h-10, w, 7.5)
        path = path.subtracted(rectPath)

        painter.fillPath(path, themeColor())


class TextEdit(QTextEdit):
    """富文本编辑框
    
    支持 HTML 格式、图片插入和多种文本样式设置，基于 QTextEdit 提供 Fluent 风格样式
    适用于需要富文本排版、图文混排的内容编辑场景
    """

    def __init__(self, parent=None):
        """初始化文本编辑框
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent=parent)
        self.layer = EditLayer(self)
        self.scrollDelegate = SmoothScrollDelegate(self)
        FluentStyleSheet.LINE_EDIT.apply(self)
        updateDynamicStyle(self)
        setFont(self)

    def contextMenuEvent(self, e):
        menu = TextEditMenu(self)
        menu.exec(e.globalPos(), ani=True)


class PlainTextEdit(QPlainTextEdit):
    """纯文本编辑框
    
    仅支持纯文本内容的编辑和显示，不支持富文本格式，基于 QPlainTextEdit 实现
    适用于代码编辑、日志查看或大文本量处理等注重性能的场景
    """

    def __init__(self, parent=None):
        """初始化纯文本编辑框
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent=parent)
        self.layer = EditLayer(self)
        self.scrollDelegate = SmoothScrollDelegate(self)
        FluentStyleSheet.LINE_EDIT.apply(self)
        updateDynamicStyle(self)
        setFont(self)

    def contextMenuEvent(self, e):
        menu = TextEditMenu(self)
        menu.exec(e.globalPos())


class TextBrowser(QTextBrowser):
    """文本浏览器
    
    支持富文本渲染、超链接跳转和文本搜索功能，通常用于只读或轻度交互的文本展示
    适用于帮助文档、消息记录和只读内容展示等场景
    """

    def __init__(self, parent=None):
        """初始化文本浏览器
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent)
        self.layer = EditLayer(self)
        self.scrollDelegate = SmoothScrollDelegate(self)
        FluentStyleSheet.LINE_EDIT.apply(self)
        updateDynamicStyle(self)
        setFont(self)

    def contextMenuEvent(self, e):
        menu = TextEditMenu(self)
        menu.exec(e.globalPos())


class PasswordLineEdit(LineEdit):
    """密码输入框
    
    提供密码掩码显示和可见性切换按钮，支持自定义掩码字符
    适用于登录表单、敏感信息输入等需要隐私保护的场景
    """

    def __init__(self, parent=None):
        """初始化密码输入框
        
        Args:
            parent: 父级窗口部件，默认为 None，指定后该组件将随父控件一同销毁
        """
        super().__init__(parent)
        self.viewButton = LineEditButton(FIF.VIEW, self)

        self.setEchoMode(QLineEdit.Password)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.hBoxLayout.addWidget(self.viewButton, 0, Qt.AlignRight)
        self.setClearButtonEnabled(False)

        self.viewButton.installEventFilter(self)
        self.viewButton.setIconSize(QSize(13, 13))
        self.viewButton.setFixedSize(29, 25)

    def setPasswordVisible(self, isVisible: bool):
        """设置密码可见性"""
        if isVisible:
            self.setEchoMode(QLineEdit.Normal)
        else:
            self.setEchoMode(QLineEdit.Password)

    def isPasswordVisible(self):
        return self.echoMode() == QLineEdit.Normal

    def setClearButtonEnabled(self, enable: bool):
        self._isClearButtonEnabled = enable

        if self.viewButton.isHidden():
            self.setTextMargins(0, 0, 28*enable, 0)
        else:
            self.setTextMargins(0, 0, 28*enable + 30, 0)

    def setViewPasswordButtonVisible(self, isVisible: bool):
        """设置密码可见按钮的可见性"""
        self.viewButton.setVisible(isVisible)

    def eventFilter(self, obj, e):
        if obj is not self.viewButton or not self.isEnabled():
            return super().eventFilter(obj, e)

        if e.type() == QEvent.MouseButtonPress:
            self.setPasswordVisible(True)
        elif e.type() == QEvent.MouseButtonRelease:
            self.setPasswordVisible(False)

        return super().eventFilter(obj, e)

    def inputMethodQuery(self, query: Qt.InputMethodQuery):
        # 禁用IME 用于 PasswordLineEdit
        if query == Qt.InputMethodQuery.ImEnabled:
            return False
        else:
            return super().inputMethodQuery(query)

    passwordVisible = Property(bool, isPasswordVisible, setPasswordVisible)