# coding: utf-8
"""导航栏组件模块"""

from typing import Union, List

from PySide6.QtCore import (Qt, Signal, QRect, QRectF, QPropertyAnimation, Property, QMargins,
                          QEasingCurve, QPoint, QEvent, QParallelAnimationGroup)
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QCursor, QFont, QBrush, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout
from collections import deque

from ...common.config import isDarkTheme
from ...common.style_sheet import themeColor
from ...common.icon import drawIcon, toQIcon
from ...common.icon import FluentIcon as FIF
from ...common.color import autoFallbackThemeColor
from ...common.font import setFont, getFont
from ...common.animation import ScaleSlideAnimation
from ..widgets.scroll_area import ScrollArea
from ..widgets.info_badge import InfoBadgeManager, InfoBadgePosition


class NavigationWidget(QWidget):
    """导航栏组件基类"""

    clicked = Signal(bool)  # 是否 triggered by user
    selectedChanged = Signal(bool)
    EXPAND_WIDTH = 312

    def __init__(self, isSelectable: bool, parent=None):
        super().__init__(parent)
        self.isCompacted = True
        self.isSelected = False
        self.isPressed = False
        self.isEnter = False
        self.isAboutSelected = False
        self.isSelectable = isSelectable
        self.treeParent = None
        self.nodeDepth = 0

        # 文本颜色
        self.lightTextColor = QColor(0, 0, 0)
        self.darkTextColor = QColor(255, 255, 255)

        # 指示器 颜色
        self.lightIndicatorColor = QColor()
        self.darkIndicatorColor = QColor()

        self.setFixedSize(40, 36)

    def enterEvent(self, e):
        self.isEnter = True
        self.update()

    def leaveEvent(self, e):
        self.isEnter = False
        self.isPressed = False
        self.update()

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.isPressed = True
        self.update()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.isPressed = False
        self.update()
        self.clicked.emit(True)

    def click(self):
        self.clicked.emit(True)

    def setCompacted(self, isCompacted: bool):
        """设置组件是否为紧凑模式

        Args:
            isCompacted: 是否为紧凑模式
        """
        if isCompacted == self.isCompacted:
            return

        self.isCompacted = isCompacted
        if isCompacted:
            self.setFixedSize(40, 36)
        else:
            self.setFixedSize(self.EXPAND_WIDTH, 36)

        self.update()

    def setSelected(self, isSelected: bool):
        """设置按钮是否被选中

        Args:
            isSelected: 是否被选中
        """
        if not self.isSelectable:
            return

        self.isSelected = isSelected
        self.isAboutSelected = False
        self.update()
        self.selectedChanged.emit(isSelected)

    def textColor(self):
        return self.darkTextColor if isDarkTheme() else self.lightTextColor

    def setLightTextColor(self, color):
        """设置亮色主题下的文本颜色

        Args:
            color: 文本颜色
        """
        self.lightTextColor = QColor(color)
        self.update()

    def setDarkTextColor(self, color):
        """设置暗色主题下的文本颜色

        Args:
            color: 文本颜色
        """
        self.darkTextColor = QColor(color)
        self.update()

    def setTextColor(self, light, dark):
        """设置亮色/暗色主题下的文本颜色

        Args:
            light: 亮色主题下的文本颜色
            dark: 暗色主题下的文本颜色
        """
        self.setLightTextColor(light)
        self.setDarkTextColor(dark)

    def setAboutSelected(self, selected: bool):
        self.isAboutSelected = selected
        self.update()

    def _margins(self):
        return QMargins(0, 0, 0, 0)

    def indicatorRect(self):
        """获取指示器的几何区域"""
        m = self._margins()
        return QRectF(m.left(), 10, 3, 16)

    def setIndicatorColor(self, light, dark):
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.update()



class NavigationPushButton(NavigationWidget):
    """导航栏推送按钮"""

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        """
        Args:
            icon: 图标
            text: 按钮文本
            isSelectable: 是否可选中
            parent: 父组件
        """
        super().__init__(isSelectable=isSelectable, parent=parent)

        self._icon = icon
        self._text = text

        setFont(self)

    def text(self):
        return self._text

    def setText(self, text: str):
        self._text = text
        self.update()

    def icon(self):
        return toQIcon(self._icon)

    def setIcon(self, icon: Union[str, QIcon, FIF]):
        self._icon = icon
        self.update()

    def _canDrawIndicator(self):
        return self.isSelected

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        # 绘制背景
        c = 255 if isDarkTheme() else 0
        m = self._margins()
        pl, pr = m.left(), m.right()
        globalRect = QRect(self.mapToGlobal(QPoint()), self.size())

        if self._canDrawIndicator():
            painter.setBrush(QColor(c, c, c, 6 if self.isEnter else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

            # 绘制指示器
            painter.setBrush(autoFallbackThemeColor(self.lightIndicatorColor, self.darkIndicatorColor))
            painter.drawRoundedRect(self.indicatorRect(), 1.5, 1.5)
        elif ((self.isEnter and globalRect.contains(QCursor.pos())) or self.isAboutSelected) and self.isEnabled():
            painter.setBrush(QColor(c, c, c, 6 if self.isAboutSelected else 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        drawIcon(self._icon, painter, QRectF(11.5+pl, 10, 16, 16))

        # 绘制文本
        if self.isCompacted:
            return

        painter.setFont(self.font())
        painter.setPen(self.textColor())

        left = 44 + pl if not self.icon().isNull() else pl + 16
        painter.drawText(QRectF(left, 0, self.width()-13-left-pr, self.height()), Qt.AlignVCenter, self.text())


class NavigationToolButton(NavigationPushButton):
    """导航栏工具按钮"""

    def __init__(self, icon: Union[str, QIcon, FIF], parent=None):
        super().__init__(icon, '', False, parent)

    def setCompacted(self, isCompacted: bool):
        self.setFixedSize(40, 36)


class NavigationSeparator(NavigationWidget):
    """导航栏分隔符"""

    def __init__(self, parent=None):
        super().__init__(False, parent=parent)
        self.setCompacted(True)

    def setCompacted(self, isCompacted: bool):
        if isCompacted:
            self.setFixedSize(48, 3)
        else:
            self.setFixedSize(self.EXPAND_WIDTH + 10, 3)

        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        c = 255 if isDarkTheme() else 0
        pen = QPen(QColor(c, c, c, 15))
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(0, 1, self.width(), 1)


class NavigationItemHeader(NavigationWidget):
    """导航栏项标题，用于对项进行分组"""

    def __init__(self, text: str, parent=None):
        super().__init__(False, parent=parent)
        self._text = text
        self._targetHeight = 30
        setFont(self, 12)  # smaller font 大小 用于 header

        # 重写 文本 颜色 用于 header style
        self.lightTextColor = QColor(96, 96, 96)  # 灰度 中的 亮色 模式
        self.darkTextColor = QColor(160, 160, 160)  # 亮色 灰度 中的 暗色 模式

        # 动画 用于 smooth 高度 transition
        self.heightAni = QPropertyAnimation(self, b'maximumHeight', self)
        self.heightAni.setDuration(150)
        self.heightAni.setEasingCurve(QEasingCurve.OutQuad)
        self.heightAni.valueChanged.connect(self._onHeightChanged)

        self.setCursor(Qt.ArrowCursor)  # 常规 cursor, not hand cursor

        # 初始化to hidden state
        self.setFixedHeight(0)

    def text(self):
        return self._text

    def setText(self, text: str):
        self._text = text
        self.update()

    def setCompacted(self, isCompacted: bool):
        """设置组件是否为紧凑模式

        Args:
            isCompacted: 是否为紧凑模式
        """
        self.isCompacted = isCompacted

        # 停止any running 动画
        self.heightAni.stop()

        if isCompacted:
            # in 紧凑 模式, animate 到 高度 0
            self.setFixedWidth(40)
            self.heightAni.setStartValue(self.height())
            self.heightAni.setEndValue(0)
        else:
            # in 展开 模式, animate 到 full 高度
            self.setFixedWidth(self.EXPAND_WIDTH)
            self.setVisible(True)  # ensure 可见 before expanding
            self.heightAni.setStartValue(self.height())
            self.heightAni.setEndValue(self._targetHeight)

        self.heightAni.start()
        self.update()

    def _onCollapseFinished(self):
        """折叠动画完成时调用"""
        if not self.isCompacted:
            self.setVisible(False)

    def _onHeightChanged(self, value):
        """高度动画数值变化时调用

        Args:
            value: 高度数值
        """
        self.setFixedHeight(value)

    def mousePressEvent(self, e):
        # do not 处理 mouse press - header is not clickable
        e.ignore()

    def mouseReleaseEvent(self, e):
        # do not 处理 mouse release - header is not clickable
        e.ignore()

    def enterEvent(self, e):
        # do not 显示 悬停 effect
        pass

    def leaveEvent(self, e):
        # do not 显示 悬停 effect
        pass

    def paintEvent(self, e):
        if self.height() == 0 or not self.isVisible():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        # 根据高度计算透明度, 用于淡入效果.
        opacity = min(1.0, self.height() / max(1, self._targetHeight))
        painter.setOpacity(opacity)

        if not self.isCompacted:
            # 绘制header 文本 中的 展开 模式
            painter.setFont(self.font())
            painter.setPen(self.textColor())
            painter.drawText(QRectF(16, 0, self.width() - 16, self.height()),
                           Qt.AlignLeft | Qt.AlignVCenter, self.text())


class NavigationTreeItem(NavigationPushButton):
    """导航栏树形项组件"""

    itemClicked = Signal(bool, bool)    # triggerByUser, clickArrow

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        super().__init__(icon, text, isSelectable, parent)
        self._arrowAngle = 0
        self.rotateAni = QPropertyAnimation(self, b'arrowAngle', self)

    def setExpanded(self, isExpanded: bool):
        self.rotateAni.stop()
        self.rotateAni.setEndValue(180 if isExpanded else 0)
        self.rotateAni.setDuration(150)
        self.rotateAni.start()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        clickArrow = QRectF(self.width()-30, 8, 20, 20).contains(e.pos())
        self.itemClicked.emit(True, clickArrow and not self.treeWidget().isLeaf())
        self.update()

    def _canDrawIndicator(self):
        p = self.treeWidget()   # type: NavigationTreeWidget
        if p.isLeaf() or p.isSelected:
            return p.isSelected

        for child in p.treeChildren:
            if child.itemWidget._canDrawIndicator() and not child.isVisible():
                return True

        return False

    def _margins(self):
        p = self.treeWidget()   # type: NavigationTreeWidget
        return QMargins(p.nodeDepth*28, 0, 20*bool(p.treeChildren), 0)

    def paintEvent(self, e):
        super().paintEvent(e)
        self._drawDropDownArrow()

    def _drawDropDownArrow(self):
        # 仅为非叶子节点且非紧凑模式项绘制箭头.
        if self.isCompacted or self.treeWidget().isLeaf():
            return

        # 绘制下拉箭头.
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        painter.translate(self.width() - 20, 18)
        painter.rotate(self.arrowAngle)
        FIF.ARROW_DOWN.render(painter, QRectF(-5, -5, 9.6, 9.6))

    def treeWidget(self) -> 'NavigationTreeWidget':
        return self.parent()

    def getArrowAngle(self):
        return self._arrowAngle

    def setArrowAngle(self, angle):
        self._arrowAngle = angle
        self.update()

    arrowAngle = Property(float, getArrowAngle, setArrowAngle)


class NavigationTreeWidgetBase(NavigationWidget):
    """导航栏树形组件基类"""

    def addChild(self, child):
        """添加子节点

        Args:
            child: 子节点组件
        """
        raise NotImplementedError

    def insertChild(self, index: int, child: NavigationWidget):
        """插入子节点

        Args:
            index: 插入位置索引
            child: 子节点组件
        """
        raise NotImplementedError

    def removeChild(self, child: NavigationWidget):
        """移除子节点

        Args:
            child: 子节点组件
        """
        raise NotImplementedError

    def isRoot(self):
        """是否为根节点"""
        return True

    def isLeaf(self):
        """是否为叶子节点"""
        return True

    def setExpanded(self, isExpanded: bool):
        """设置节点的展开状态

        Args:
            isExpanded: 是否展开当前节点
        """
        raise NotImplementedError

    def childItems(self) -> list:
        """返回子项列表"""
        raise NotImplementedError

    def setRememberExpandState(self, remember: bool):
        """设置是否记住展开状态

        Args:
            remember: 是否记住展开状态
        """
        raise NotImplementedError

    def saveExpandState(self):
        """保存当前展开状态"""
        raise NotImplementedError

    def restoreExpandState(self, ani=True):
        """恢复保存的展开状态

        Args:
            ani: 是否使用动画
        """
        raise NotImplementedError


class NavigationTreeWidget(NavigationTreeWidgetBase):
    """导航栏树形组件"""

    expanded = Signal()

    def __init__(self, icon: Union[str, QIcon, FIF], text: str, isSelectable: bool, parent=None):
        super().__init__(isSelectable, parent)

        self.treeChildren = []  # type: 列表[NavigationTreeWidget]
        self.isExpanded = False
        self._icon = icon
        self._rememberExpandState = False
        self._wasExpanded = False

        self.itemWidget = NavigationTreeItem(icon, text, isSelectable, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.expandAni = QPropertyAnimation(self, b'geometry', self)

        self.__initWidget()

    def __initWidget(self):
        self.vBoxLayout.setSpacing(4)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.itemWidget, 0, Qt.AlignTop)

        self.itemWidget.itemClicked.connect(self._onClicked)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.expandAni.valueChanged.connect(lambda g: self.setFixedSize(g.size()))
        self.expandAni.valueChanged.connect(self.expanded)
        self.expandAni.finished.connect(self.parentWidget().layout().invalidate)

    def _margins(self):
        return self.itemWidget._margins()

    def addChild(self, child):
        self.insertChild(-1, child)

    def text(self):
        return self.itemWidget.text()

    def icon(self):
        return self.itemWidget.icon()

    def setText(self, text):
        self.itemWidget.setText(text)

    def setIcon(self, icon: Union[str, QIcon, FIF]):
        self.itemWidget.setIcon(icon)

    def textColor(self):
        return self.itemWidget.textColor()

    def setLightTextColor(self, color):
        """设置亮色主题下的文本颜色"""
        self.itemWidget.setLightTextColor(color)

    def setDarkTextColor(self, color):
        """设置暗色主题下的文本颜色"""
        self.itemWidget.setDarkTextColor(color)

    def setTextColor(self, light, dark):
        """设置亮色/暗色主题下的文本颜色"""
        self.lightTextColor = QColor(light)
        self.darkTextColor = QColor(dark)
        self.itemWidget.setTextColor(light, dark)

    def setIndicatorColor(self, light, dark):
        """设置亮色/暗色主题下的指示器颜色"""
        self.lightIndicatorColor = QColor(light)
        self.darkIndicatorColor = QColor(dark)
        self.itemWidget.setIndicatorColor(light, dark)

    def setFont(self, font: QFont):
        super().setFont(font)
        self.itemWidget.setFont(font)

    def clone(self):
        root = NavigationTreeWidget(self._icon, self.text(), self.isSelectable, self.parent())
        root.setSelected(self.isSelected)
        root.setFixedSize(self.size())
        root.setTextColor(self.lightTextColor, self.darkTextColor)
        root.setIndicatorColor(self.itemWidget.lightIndicatorColor, self.itemWidget.darkIndicatorColor)
        root.nodeDepth = self.nodeDepth

        root.clicked.connect(self.clicked)
        self.selectedChanged.connect(root.setSelected)

        for child in self.treeChildren:
            root.addChild(child.clone())

        return root

    def suitableWidth(self):
        m = self.itemWidget._margins()
        left = 57 + m.left() if not self.icon().isNull() else m.left() + 29
        tw = self.itemWidget.fontMetrics().boundingRect(self.text()).width()
        return left + tw + m.right()

    def insertChild(self, index, child):
        if child in self.treeChildren:
            return

        child.treeParent = self
        child.nodeDepth = self.nodeDepth + 1
        child.setVisible(self.isExpanded)
        child.expandAni.valueChanged.connect(lambda: self.setFixedSize(self.sizeHint()))
        child.expandAni.valueChanged.connect(self.expanded)

        # 连接高度 changed 信号与父部件 recursively
        p = self.treeParent
        while p:
            child.expandAni.valueChanged.connect(lambda v, p=p: p.setFixedSize(p.sizeHint()))
            p = p.treeParent

        if index < 0:
            index = len(self.treeChildren)

        index += 1  # 项 部件 should always be first
        self.treeChildren.insert(index, child)
        self.vBoxLayout.insertWidget(index, child, 0, Qt.AlignTop)

        # 调整高度
        if self.isExpanded:
            self.setFixedHeight(self.height() + child.height() + self.vBoxLayout.spacing())

            p = self.treeParent
            while p:
                p.setFixedSize(p.sizeHint())
                p = p.treeParent

        self.update()

    def removeChild(self, child):
        self.treeChildren.remove(child)
        self.vBoxLayout.removeWidget(child)
        self.setFixedHeight(self.sizeHint().height())

    def childItems(self) -> list:
        return self.treeChildren

    def setExpanded(self, isExpanded: bool, ani=False):
        """设置展开状态

        Args:
            isExpanded: 是否展开
            ani: 是否使用动画
        """
        if isExpanded == self.isExpanded:
            return

        self.isExpanded = isExpanded
        self.itemWidget.setExpanded(isExpanded)

        for child in self.treeChildren:
            child.setVisible(isExpanded)
            child.setFixedSize(child.sizeHint())

        if ani:
            self.expandAni.stop()
            self.expandAni.setStartValue(self.geometry())
            self.expandAni.setEndValue(QRect(self.pos(), self.sizeHint()))
            self.expandAni.setDuration(120)
            self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
            self.expandAni.start()
        else:
            self.setFixedSize(self.sizeHint())

    def isRoot(self):
        return self.treeParent is None

    def isLeaf(self):
        return len(self.treeChildren) == 0

    def setSelected(self, isSelected: bool):
        super().setSelected(isSelected)
        self.itemWidget.setSelected(isSelected)

    def mouseReleaseEvent(self, e):
        pass

    def setCompacted(self, isCompacted: bool):
        super().setCompacted(isCompacted)
        self.itemWidget.setCompacted(isCompacted)

    def setAboutSelected(self, selected: bool):
        self.isAboutSelected = selected
        self.itemWidget.setAboutSelected(selected)

    def _onClicked(self, triggerByUser, clickArrow):
        if not self.isCompacted:
            if self.isSelectable and not self.isSelected and not clickArrow:
                self.setExpanded(True, ani=True)
            else:
                self.setExpanded(not self.isExpanded, ani=True)

        if not clickArrow or self.isCompacted:
            self.clicked.emit(triggerByUser)

    def setRememberExpandState(self, remember: bool):
        self._rememberExpandState = remember

    def saveExpandState(self):
        self._wasExpanded = self.isExpanded if self._rememberExpandState else False

    def restoreExpandState(self, ani=True):
        if self._wasExpanded:
            self.setExpanded(True, ani)


class NavigationAvatarWidget(NavigationWidget):
    """用户头像组件"""

    def __init__(self, name: str, avatar: Union[str, QPixmap, QImage] = None, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        from ..widgets.label import AvatarWidget

        self.name = name
        self.avatar = AvatarWidget(self)

        self.avatar.setRadius(12)
        self.avatar.setText(name)
        self.avatar.move(8, 6)
        setFont(self)

        if avatar:
            self.setAvatar(avatar)

    def setName(self, name: str):
        self.name = name
        self.avatar.setText(name)
        self.update()

    def setAvatar(self, avatar: Union[str, QPixmap, QImage]):
        self.avatar.setImage(avatar)
        self.avatar.setRadius(12)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        if self.isPressed:
            painter.setOpacity(0.7)

        self._drawBackground(painter)
        self._drawText(painter)

    def _drawText(self, painter: QPainter):
        if self.isCompacted:
            return

        painter.setPen(self.textColor())
        painter.setFont(self.font())
        painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, self.name)

    def _drawBackground(self, painter):
        if not self.isEnter:
            return

        c = 255 if isDarkTheme() else 0
        painter.setBrush(QColor(c, c, c, 10))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)


@InfoBadgeManager.register(InfoBadgePosition.NAVIGATION_ITEM)
class NavigationItemInfoBadgeManager(InfoBadgeManager):
    """导航栏项信息徽标管理器"""

    def eventFilter(self, obj, e: QEvent):
        if obj is self.target:
            if e.type() == QEvent.Show:
                self.badge.show()

        return super().eventFilter(obj, e)

    def position(self):
        target = self.target
        self.badge.setVisible(target.isVisible())

        if target.isCompacted:
            return target.geometry().topRight() - QPoint(self.badge.width() + 2, -2)

        if isinstance(target, NavigationTreeWidget):
            dx = 10 if target.isLeaf() else 35
            x = target.geometry().right() - self.badge.width() - dx
            y = target.y() + 18 - self.badge.height() // 2
        else:
            x = target.geometry().right() - self.badge.width() - 10
            y = target.geometry().center().y() - self.badge.height() // 2

        return QPoint(x, y)


class NavigationFlyoutMenu(ScrollArea):
    """导航栏浮出菜单"""

    expanded = Signal()

    def __init__(self, tree: NavigationTreeWidget, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self.treeWidget = tree
        self.treeChildren = []

        self.vBoxLayout = QVBoxLayout(self.view)

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enableTransparentBackground()

        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(5, 8, 5, 8)

        # 将nodes添加到菜单
        for child in tree.treeChildren:
            node = child.clone()
            node.expanded.connect(self._adjustViewSize)

            self.treeChildren.append(node)
            self.vBoxLayout.addWidget(node)

        self._initNode(self)
        self._adjustViewSize(False)

    def _initNode(self, root: NavigationTreeWidget):
        for c in root.treeChildren:
            c.nodeDepth -= 1
            c.setCompacted(False)

            if c.isLeaf():
                c.clicked.connect(self.window().fadeOut)

            self._initNode(c)

    def _adjustViewSize(self, emit=True):
        w = self._suitableWidth()

        # 调整the 宽度 的 node
        for node in self.visibleTreeNodes():
            node.setFixedWidth(w - 10)
            node.itemWidget.setFixedWidth(w - 10)

        self.view.setFixedSize(w, self.view.sizeHint().height())

        h = min(self.window().parent().height() - 48, self.view.height())

        self.setFixedSize(w, h)

        if emit:
            self.expanded.emit()

    def _suitableWidth(self):
        w = 0

        for node in self.visibleTreeNodes():
            if not node.isHidden():
                w = max(w, node.suitableWidth() + 10)

        window = self.window().parent()  # type: QWidget
        return min(window.width() // 2 - 25, w) + 10

    def visibleTreeNodes(self):
        nodes = []
        queue = deque()
        queue.extend(self.treeChildren)

        while queue:
            node = queue.popleft()  # type: NavigationTreeWidget
            nodes.append(node)
            queue.extend([i for i in node.treeChildren if not i.isHidden()])

        return nodes


class NavigationUserCard(NavigationAvatarWidget):
    """导航栏用户卡片组件"""

    def __init__(self, parent=None):
        super().__init__(name="", parent=parent)

        # 文本 properties
        self._title = ""
        self._subtitle = ""
        self._titleSize = 14
        self._subtitleSize = 12
        self._subtitleColor = None  # type: QColor

        # 动画 properties
        self._textOpacity = 0.0
        self._animationDuration = 250
        self._animationGroup = QParallelAnimationGroup(self)

        # avatar 大小 动画
        self._radiusAni = QPropertyAnimation(self.avatar, b"radius", self)
        self._radiusAni.setDuration(self._animationDuration)
        self._radiusAni.setEasingCurve(QEasingCurve.OutCubic)
        self._radiusAni.valueChanged.connect(self._updateAvatarPosition)

        # 文本 opacity 动画
        self._opacityAni = QPropertyAnimation(self, b"textOpacity", self)
        self._opacityAni.setDuration(int(self._animationDuration * 0.8))
        self._opacityAni.setEasingCurve(QEasingCurve.InOutQuad)

        self._animationGroup.addAnimation(self._radiusAni)
        self._animationGroup.addAnimation(self._opacityAni)
        self._animationGroup.finished.connect(self.update)

        # initial 大小
        self.setFixedSize(40, 36)

    def setAvatarIcon(self, icon: FIF):
        """设置头像图标，用于未设置图像时

        Args:
            icon: 头像图标
        """
        self.avatar.setImage(toQIcon(icon).pixmap(64, 64))
        self.update()

    def setAvatarBackgroundColor(self, light: QColor, dark: QColor):
        """设置亮色/暗色主题下的头像背景色

        Args:
            light: 亮色主题下的背景色
            dark: 暗色主题下的背景色
        """
        self.avatar.setBackgroundColor(light, dark)
        self.update()

    def title(self):
        """返回用户卡片标题"""
        return self._title

    def setTitle(self, title: str):
        """设置用户卡片标题

        Args:
            title: 标题文本
        """
        self._title = title
        self.setName(title)
        self.update()

    def subtitle(self):
        """返回用户卡片副标题"""
        return self._subtitle

    def setSubtitle(self, subtitle: str):
        """设置用户卡片副标题

        Args:
            subtitle: 副标题文本
        """
        self._subtitle = subtitle
        self.update()

    def setTitleFontSize(self, size: int):
        """设置标题字体大小

        Args:
            size: 字体大小
        """
        self._titleSize = size
        self.update()

    def setSubtitleFontSize(self, size: int):
        """设置副标题字体大小

        Args:
            size: 字体大小
        """
        self._subtitleSize = size
        self.update()

    def setAnimationDuration(self, duration: int):
        """设置动画持续时间

        Args:
            duration: 持续时间，单位为毫秒
        """
        self._animationDuration = duration
        self._radiusAni.setDuration(duration)
        self._opacityAni.setDuration(int(duration * 0.8))

    def setCompacted(self, isCompacted: bool):
        """设置组件是否为紧凑模式

        Args:
            isCompacted: 是否为紧凑模式
        """
        if isCompacted == self.isCompacted:
            return

        self.isCompacted = isCompacted

        if isCompacted:
            # 紧凑 mode: 24x24 avatar like NavigationAvatarWidget
            self.setFixedSize(40, 36)
            self._radiusAni.setStartValue(self.avatar.radius)
            self._radiusAni.setEndValue(12)  # 24px diameter
            self._opacityAni.setStartValue(self._textOpacity)
            self._opacityAni.setEndValue(0.0)
        else:
            # expanded mode: large avatar 使用 文本
            self.setFixedSize(self.EXPAND_WIDTH, 80)
            self._radiusAni.setStartValue(self.avatar.radius)
            self._radiusAni.setEndValue(32)  # 64px diameter
            self._opacityAni.setStartValue(self._textOpacity)
            self._opacityAni.setEndValue(1.0)

        self._animationGroup.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing | QPainter.TextAntialiasing
        )

        if self.isPressed:
            painter.setOpacity(0.7)

        # 绘制悬停 背景
        self._drawBackground(painter)

        # 绘制文本 中的 expanded 模式
        if not self.isCompacted and self._textOpacity > 0:
            self._drawText(painter)

    def _drawText(self, painter: QPainter):
        """绘制标题和副标题"""
        textX = 16 + int(self.avatar.radius * 2) + 12
        textWidth = self.width() - textX - 16

        # 绘制标题
        painter.setFont(getFont(self._titleSize, QFont.Bold))
        c = self.textColor()
        c.setAlpha(int(255 * self._textOpacity))
        painter.setPen(c)

        titleY = self.height() // 2 - 2
        painter.drawText(QRectF(textX, 0, textWidth, titleY),
                         Qt.AlignLeft | Qt.AlignBottom,
                         self._title)

        # 绘制subtitle 使用 semi-transparent 颜色
        if self._subtitle:
            painter.setFont(getFont(self._subtitleSize))

            c = self.subtitleColor or self.textColor()
            c.setAlpha(int(150 * self._textOpacity))
            painter.setPen(c)

            subtitleY = self.height() // 2 + 2
            painter.drawText(QRectF(textX, subtitleY, textWidth, self.height() - subtitleY),
                             Qt.AlignLeft | Qt.AlignTop,
                             self._subtitle)

    def _updateAvatarPosition(self):
        """根据当前尺寸更新头像位置"""
        if self.isCompacted:
            self.avatar.move(8, 6)
        else:
            self.avatar.move(16, (self.height() - self.avatar.height()) // 2)

    # properties
    @Property(float)
    def textOpacity(self):
        return self._textOpacity

    @textOpacity.setter
    def textOpacity(self, value: float):
        self._textOpacity = value
        self.update()

    @Property(QColor)
    def subtitleColor(self):
        return self._subtitleColor

    @subtitleColor.setter
    def subtitleColor(self, color: QColor):
        self._subtitleColor = color
        self.update()


class NavigationIndicator(QWidget):
    """导航栏指示器"""

    aniFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lightColor = QColor()
        self.darkColor = QColor()

        self.scaleSlideAni = ScaleSlideAnimation(self, Qt.Orientation.Vertical)

        self.resize(3, 16)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        self.scaleSlideAni.valueChanged.connect(lambda g: self.setGeometry(g.toRect()))
        self.scaleSlideAni.finished.connect(self.aniFinished)

    def startAnimation(self, startRect: QRectF, endRect: QRectF, useCrossFade=False):
        """启动指示器动画

        Args:
            startRect: 起始几何区域
            endRect: 结束几何区域
            useCrossFade: 是否使用交叉淡化动画
        """
        self.setGeometry(startRect.toRect())
        self.show()

        self.scaleSlideAni.setGeometry(startRect)
        self.scaleSlideAni.startAnimation(endRect, useCrossFade)

    def stopAnimation(self):
        """停止动画"""
        self.scaleSlideAni.stopAnimation()
        self.hide()

    def setIndicatorColor(self, light, dark):
        self.lightColor = QColor(light)
        self.darkColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightColor, self.darkColor))
        painter.drawRoundedRect(self.rect(), 1.5, 1.5)