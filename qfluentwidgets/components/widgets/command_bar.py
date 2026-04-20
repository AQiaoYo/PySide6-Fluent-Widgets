# coding: utf-8
"""命令栏组件

提供用于构建命令栏（CommandBar）的一系列控件，包括命令按钮、分隔符和溢出菜单等
通常用于窗口标题栏下方或工具区域，承载页面级的快捷操作入口
"""

from typing import Iterable, List, Tuple, Union

from PySide6.QtCore import Qt, QSize, QRectF, QRect, QPoint, QEvent
from PySide6.QtGui import QAction, QPainter, QColor, QFont, QHoverEvent, QPainterPath
from PySide6.QtWidgets import QLayoutItem, QWidget, QFrame, QHBoxLayout, QApplication

from ...common.font import setFont
from ...common.icon import FluentIcon, Icon, Action
from ...common.style_sheet import isDarkTheme, updateDynamicStyle
from .menu import RoundMenu, MenuAnimationType
from .button import TransparentToggleToolButton
from .tool_tip import ToolTipFilter
from .flyout import FlyoutViewBase, Flyout


class CommandButton(TransparentToggleToolButton):
    """命令按钮
    
    在命令栏中显示带图标和文本的操作按钮，支持点击触发命令和自定义工具提示
    适用于将常用操作以直观方式平铺展示的场景，是 CommandBar 的核心组成元素
    
    构造函数重载:
        * CommandButton(parent: QWidget = None)
        * CommandButton(icon: QIcon | str | FluentIconBase = None, parent: QWidget = None)
    """

    def _postInit(self):
        super()._postInit()
        self.setCheckable(False)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        setFont(self, 12)

        self._text = ''
        self._action = None
        self._isTight = False

    def setTight(self, isTight: bool):
        self._isTight = isTight
        self.update()

    def isTight(self):
        return self._isTight

    def sizeHint(self) -> QSize:
        if self.isIconOnly():
            return QSize(36, 34) if self.isTight() else QSize(48, 34)

        # 获取文本的宽度
        tw = self.fontMetrics().boundingRect(self.text()).width()

        style = self.toolButtonStyle()
        if style == Qt.ToolButtonTextBesideIcon:
            return QSize(tw + 47, 34)
        if style == Qt.ToolButtonTextOnly:
            return QSize(tw + 32, 34)

        return QSize(tw + 32, 50)

    def isIconOnly(self):
        if not self.text():
            return True

        return self.toolButtonStyle() in [Qt.ToolButtonIconOnly, Qt.ToolButtonFollowStyle]

    def _drawIcon(self, icon, painter, rect):
        pass

    def text(self):
        return self._text

    def setText(self, text: str):
        self._text = text
        self.update()

    def setAction(self, action: QAction):
        self._action = action
        self._onActionChanged()

        self.clicked.connect(action.trigger)
        action.toggled.connect(self.setChecked)
        action.changed.connect(self._onActionChanged)

        self.installEventFilter(CommandToolTipFilter(self, 700))

    def _onActionChanged(self):
        action = self.action()
        self.setIcon(action.icon())
        self.setText(action.text())
        self.setToolTip(action.toolTip())
        self.setEnabled(action.isEnabled())
        self.setCheckable(action.isCheckable())
        self.setChecked(action.isChecked())

    def action(self):
        return self._action

    def paintEvent(self, e):
        super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isChecked():
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        else:
            painter.setPen(Qt.black if isDarkTheme() else Qt.white)

        if not self.isEnabled():
            painter.setOpacity(0.43)
        elif self.isPressed:
            painter.setOpacity(0.63)

        # 绘制图标 和 文本
        style = self.toolButtonStyle()
        iw, ih = self.iconSize().width(), self.iconSize().height()

        if self.isIconOnly():
            y = (self.height() - ih) / 2
            x = (self.width() - iw) / 2
            super()._drawIcon(self._icon, painter, QRectF(x, y, iw, ih))
        elif style == Qt.ToolButtonTextOnly:
            painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        elif style == Qt.ToolButtonTextBesideIcon:
            y = (self.height() - ih) / 2
            super()._drawIcon(self._icon, painter, QRectF(11, y, iw, ih))

            rect = QRectF(26, 0, self.width() - 26, self.height())
            painter.drawText(rect, Qt.AlignCenter, self.text())
        elif style == Qt.ToolButtonTextUnderIcon:
            x = (self.width() - iw) / 2
            super()._drawIcon(self._icon, painter, QRectF(x, 9, iw, ih))

            rect = QRectF(0, ih + 13, self.width(), self.height() - ih - 13)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, self.text())


class CommandToolTipFilter(ToolTipFilter):
    """命令按钮工具提示过滤器
    
    为 CommandButton 提供增强的工具提示行为，当按钮文本被截断时自动显示完整内容
    一般在按钮文本长度超出显示区域时触发，避免用户无法识别被省略的命令名称
    """

    def _canShowToolTip(self) -> bool:
        return super()._canShowToolTip() and self.parent().isIconOnly()


class MoreActionsButton(CommandButton):
    """更多操作按钮
    
    当命令栏空间不足时，用于展开被折叠命令的溢出菜单按钮
    通常由 CommandBar 内部自动创建和管理，无需手动添加到界面中
    """

    def _postInit(self):
        super()._postInit()
        self.setIcon(FluentIcon.MORE)

    def sizeHint(self):
        return QSize(40, 34)

    def clearState(self):
        self.setAttribute(Qt.WA_UnderMouse, False)
        e = QHoverEvent(QEvent.HoverLeave, QPoint(-1, -1), QPoint())
        QApplication.sendEvent(self, e)


class CommandSeparator(QWidget):
    """命令分隔符
    
    在命令栏中用于视觉上分隔不同功能分组的竖线或横线
    适合将同类命令聚合并与其他组区隔，提升命令栏的可读性和结构层次
    """

    def __init__(self, parent=None):
        """初始化命令分隔符
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__(parent)
        self.setFixedSize(9, 34)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255, 21)
                       if isDarkTheme() else QColor(0, 0, 0, 15))
        painter.drawLine(5, 2, 5, self.height() - 2)


class CommandMenu(RoundMenu):
    """命令菜单按钮
    
    在命令栏中显示带下拉箭头的按钮，点击后弹出选项菜单以承载二级命令
    适合命令数量较多或需要分组展示的场景，可作为 CommandButton 的补充形式
    """

    def __init__(self, parent=None):
        """初始化命令菜单
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__("", parent)
        self.setItemHeight(32)
        self.view.setIconSize(QSize(16, 16))

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)


class CommandBar(QFrame):
    """命令栏
    
    水平排列命令按钮和分隔符的容器控件，支持根据可用宽度自动折叠溢出命令到更多菜单
    常用于窗口顶部、工具面板或标题栏区域，为页面提供一组高频操作的快捷入口
    """

    def __init__(self, parent=None):
        """初始化命令栏
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__(parent=parent)
        self._widgets = []  # type: 列表[QWidget]
        self._hiddenWidgets = []  # type: 列表[QWidget]
        self._hiddenActions = []  # type: 列表[QAction]

        self._menuAnimation = MenuAnimationType.DROP_DOWN
        self._toolButtonStyle = Qt.ToolButtonIconOnly
        self._iconSize = QSize(16, 16)
        self._isButtonTight = False
        self._spacing = 4

        self.moreButton = MoreActionsButton(self)
        self.moreButton.clicked.connect(self._showMoreActionsMenu)
        self.moreButton.hide()

        setFont(self, 12)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setSpaing(self, spacing: int):
        if spacing == self._spacing:
            return

        self._spacing = spacing
        self.updateGeometry()

    def spacing(self):
        return self._spacing

    def addAction(self, action: QAction):
        """添加 action

        Args:
            action: 要添加的 action
        """
        if action in self.actions():
            return

        button = self._createButton(action)
        self._insertWidgetToLayout(-1, button)
        super().addAction(action)
        return button

    def addActions(self, actions: Iterable[QAction]):
        for action in actions:
            self.addAction(action)

    def addHiddenAction(self, action: QAction):
        """添加 hidden action

        Args:
            action: 要添加的 hidden action
        """
        if action in self.actions():
            return

        self._hiddenActions.append(action)
        self.updateGeometry()
        super().addAction(action)

    def addHiddenActions(self, actions: List[QAction]):
        """添加 hidden action

        Args:
            actions: 要添加的 hidden action 列表
        """
        for action in actions:
            self.addHiddenAction(action)

    def insertAction(self, before: QAction, action: QAction):
        if before not in self.actions():
            return

        index = self.actions().index(before)
        button = self._createButton(action)
        self._insertWidgetToLayout(index, button)
        super().insertAction(before, action)
        return button

    def addSeparator(self):
        self.insertSeparator(-1)

    def insertSeparator(self, index: int):
        self._insertWidgetToLayout(index, CommandSeparator(self))

    def addWidget(self, widget: QWidget):
        """将部件添加到 command 栏

        Args:
            widget: 要添加的部件
        """
        self._insertWidgetToLayout(-1, widget)

    def removeAction(self, action: QAction):
        if action not in self.actions():
            return

        for w in self.commandButtons:
            if w.action() is action:
                self._widgets.remove(w)
                w.hide()
                w.deleteLater()
                break

        self.updateGeometry()

    def removeWidget(self, widget: QWidget):
        if widget not in self._widgets:
            return

        self._widgets.remove(widget)
        self.updateGeometry()

    def removeHiddenAction(self, action: QAction):
        if action in self._hiddenActions:
            self._hiddenActions.remove(action)

    def setToolButtonStyle(self, style: Qt.ToolButtonStyle):
        """设置 tool 按钮的 style

        Args:
            style: 工具按钮样式
        """
        if self.toolButtonStyle() == style:
            return

        self._toolButtonStyle = style
        for w in self.commandButtons:
            w.setToolButtonStyle(style)

    def toolButtonStyle(self):
        return self._toolButtonStyle

    def setButtonTight(self, isTight: bool):
        if self.isButtonTight() == isTight:
            return

        self._isButtonTight = isTight

        for w in self.commandButtons:
            w.setTight(isTight)

        self.updateGeometry()

    def isButtonTight(self):
        return self._isButtonTight

    def setIconSize(self, size: QSize):
        if size == self._iconSize:
            return

        self._iconSize = size
        for w in self.commandButtons:
            w.setIconSize(size)

    def iconSize(self):
        return self._iconSize

    def resizeEvent(self, e):
        self.updateGeometry()

    def _createButton(self, action: QAction):
        """创建 command 按钮

        Args:
            action: 关联的 action

        Returns:
            创建的 CommandButton
        """
        button = CommandButton(self)
        button.setAction(action)
        button.setToolButtonStyle(self.toolButtonStyle())
        button.setTight(self.isButtonTight())
        button.setIconSize(self.iconSize())
        button.setFont(self.font())
        return button

    def _insertWidgetToLayout(self, index: int, widget: QWidget):
        """将部件添加到布局

        Args:
            index: 插入位置
            widget: 要添加的部件
        """
        widget.setParent(self)
        widget.show()

        if index < 0:
            self._widgets.append(widget)
        else:
            self._widgets.insert(index, widget)

        self.setFixedHeight(max(w.height() for w in self._widgets))
        self.updateGeometry()

    def minimumSizeHint(self) -> QSize:
        return self.moreButton.size()

    def updateGeometry(self):
        self._hiddenWidgets.clear()
        self.moreButton.hide()

        visibles = self._visibleWidgets()
        x = self.contentsMargins().left()
        h = self.height()

        for widget in visibles:
            widget.show()
            widget.move(x, (h - widget.height()) // 2)
            x += (widget.width() + self.spacing())

        # 显示more actions 按钮
        if self._hiddenActions or len(visibles) < len(self._widgets):
            self.moreButton.show()
            self.moreButton.move(x, (h - self.moreButton.height()) // 2)

        for widget in self._widgets[len(visibles):]:
            widget.hide()
            self._hiddenWidgets.append(widget)

    def _visibleWidgets(self) -> List[QWidget]:
        """返回可见的布局部件

        Returns:
            可见部件列表
        """
        # have enough spacing 到 显示 all 部件
        if self.suitableWidth() <= self.width():
            return self._widgets

        w = self.moreButton.width()
        for index, widget in enumerate(self._widgets):
            w += widget.width()
            if index > 0:
                w += self.spacing()

            if w > self.width():
                break

        return self._widgets[:index]

    def suitableWidth(self):
        widths = [w.width() for w in self._widgets]
        if self._hiddenActions:
            widths.append(self.moreButton.width())

        return sum(widths) + self.spacing() * max(len(widths) - 1, 0)

    def resizeToSuitableWidth(self):
        self.setFixedWidth(self.suitableWidth())

    def setFont(self, font: QFont):
        super().setFont(font)
        for button in self.commandButtons:
            button.setFont(font)

    @property
    def commandButtons(self):
        return [w for w in self._widgets if isinstance(w, CommandButton)]

    def setMenuDropDown(self, down: bool):
        """设置 more actions 菜单的动画方向

        Args:
            down: 是否向下展开
        """
        if down:
            self._menuAnimation = MenuAnimationType.DROP_DOWN
        else:
            self._menuAnimation = MenuAnimationType.PULL_UP

    def isMenuDropDown(self):
        return self._menuAnimation == MenuAnimationType.DROP_DOWN

    def _showMoreActionsMenu(self):
        """显示 more actions 菜单"""
        self.moreButton.clearState()

        actions = self._hiddenActions.copy()

        for w in reversed(self._hiddenWidgets):
            if isinstance(w, CommandButton):
                actions.insert(0, w.action())

        menu = CommandMenu(self)
        menu.addActions(actions)

        x = -menu.width() + menu.layout().contentsMargins().right() + \
            self.moreButton.width() + 18
        if self._menuAnimation == MenuAnimationType.DROP_DOWN:
            y = self.moreButton.height()
        else:
            y = -5

        pos = self.moreButton.mapToGlobal(QPoint(x, y))
        menu.exec(pos, aniType=self._menuAnimation)


class CommandViewMenu(CommandMenu):
    """命令视图菜单
    
    在命令栏视图（CommandBarView）中使用的下拉菜单，用于展示被折叠或收起的命令项
    一般与 CommandViewBar 配合使用，实现弹出层内的命令分组展示
    """

    def __init__(self, parent=None):
        """初始化命令视图菜单
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__(parent)
        self.view.setObjectName('commandListWidget')

    def setDropDown(self, down: bool, long=False):
        self.view.setProperty('dropDown', down)
        self.view.setProperty('long', long)
        updateDynamicStyle(self.view)

    def exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        return super().exec(pos, ani, aniType)


class CommandViewBar(CommandBar):
    """命令视图栏
    
    命令栏弹出视图中的水平命令容器，用于在 Flyout 或弹层中承载一组操作按钮
    适合在右键菜单、悬浮面板等临时视图中快速嵌入命令操作区域
    """

    def __init__(self, parent=None):
        """初始化命令视图栏
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__(parent)
        self.setMenuDropDown(True)

    def setMenuDropDown(self, down: bool):
        """设置 more actions 菜单的动画方向

        Args:
            down: 是否向下展开
        """
        if down:
            self._menuAnimation = MenuAnimationType.FADE_IN_DROP_DOWN
        else:
            self._menuAnimation = MenuAnimationType.FADE_IN_PULL_UP

    def isMenuDropDown(self):
        return self._menuAnimation == MenuAnimationType.FADE_IN_DROP_DOWN

    def _showMoreActionsMenu(self):
        self.moreButton.clearState()

        actions = self._hiddenActions.copy()

        for w in reversed(self._hiddenWidgets):
            if isinstance(w, CommandButton):
                actions.insert(0, w.action())

        menu = CommandViewMenu(self)
        menu.addActions(actions)

        # 调整视图形状.
        view = self.parent()  # type: CommandBarView
        view.setMenuVisible(True)

        # 调整菜单形状.
        menu.closedSignal.connect(lambda: view.setMenuVisible(False))
        menu.setDropDown(self.isMenuDropDown(), menu.view.width() > view.width()+5)

        # 调整菜单 大小
        if menu.view.width() < view.width():
            menu.view.setFixedWidth(view.width())
            menu.adjustSize()

        x = -menu.width() + menu.layout().contentsMargins().right() + \
            self.moreButton.width() + 18
        if self.isMenuDropDown():
            y = self.moreButton.height()
        else:
            y = -13
            menu.setShadowEffect(0, (0, 0), QColor(0, 0, 0, 0))
            menu.layout().setContentsMargins(12, 20, 12, 8)

        pos = self.moreButton.mapToGlobal(QPoint(x, y))
        menu.exec(pos, aniType=self._menuAnimation)


class CommandBarView(FlyoutViewBase):
    """命令栏视图
    
    以弹出层形式展示的命令栏容器，可在任意位置悬浮显示一组命令按钮
    常用于右键上下文菜单、详情页操作浮层等需要临时展示操作入口的场景
    """

    def __init__(self, parent=None):
        """初始化命令栏视图
        
        Args:
            parent: 父级 QWidget，默认为 None
        """
        super().__init__(parent=parent)
        self.bar = CommandViewBar(self)
        self.hBoxLayout = QHBoxLayout(self)

        self.hBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.hBoxLayout.addWidget(self.bar)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinAndMaxSize)

        self.setButtonTight(True)
        self.setIconSize(QSize(14, 14))

        self._isMenuVisible = False

    def setMenuVisible(self, isVisible):
        self._isMenuVisible = isVisible
        self.update()

    def addWidget(self, widget: QWidget):
        self.bar.addWidget(widget)

    def setSpaing(self, spacing: int):
        self.bar.setSpaing(spacing)

    def spacing(self):
        return self.bar.spacing()

    def addAction(self, action: QAction):
        return self.bar.addAction(action)

    def addActions(self, actions: Iterable[QAction]):
        self.bar.addActions(actions)

    def addHiddenAction(self, action: QAction):
        self.bar.addHiddenAction(action)

    def addHiddenActions(self, actions: List[QAction]):
        self.bar.addHiddenActions(actions)

    def insertAction(self, before: QAction, action: QAction):
        return self.bar.insertAction(before, action)

    def addSeparator(self):
        self.bar.addSeparator()

    def insertSeparator(self, index: int):
        self.bar.insertSeparator(index)

    def removeAction(self, action: QAction):
        self.bar.removeAction(action)

    def removeWidget(self, widget: QWidget):
        self.bar.removeWidget(widget)

    def removeHiddenAction(self, action: QAction):
        self.bar.removeAction(action)

    def setToolButtonStyle(self, style: Qt.ToolButtonStyle):
        self.bar.setToolButtonStyle(style)

    def toolButtonStyle(self):
        return self.bar.toolButtonStyle()

    def setButtonTight(self, isTight: bool):
        self.bar.setButtonTight(isTight)

    def isButtonTight(self):
        return self.bar.isButtonTight()

    def setIconSize(self, size: QSize):
        self.bar.setIconSize(size)

    def iconSize(self):
        return self.bar.iconSize()

    def setFont(self, font: QFont):
        self.bar.setFont(font)

    def setMenuDropDown(self, down: bool):
        self.bar.setMenuDropDown(down)

    def suitableWidth(self):
        m = self.contentsMargins()
        return m.left() + m.right() + self.bar.suitableWidth()

    def resizeToSuitableWidth(self):
        self.bar.resizeToSuitableWidth()
        self.setFixedWidth(self.suitableWidth())

    def actions(self):
        return self.bar.actions()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 8, 8)

        if self._isMenuVisible:
            y = self.height() - 10 if self.bar.isMenuDropDown() else 1
            path.addRect(1, y, self.width() - 2, 9)

        painter.setBrush(
            QColor(40, 40, 40) if isDarkTheme() else QColor(248, 248, 248))
        painter.setPen(
            QColor(56, 56, 56) if isDarkTheme() else QColor(233, 233, 233))
        painter.drawPath(path.simplified())