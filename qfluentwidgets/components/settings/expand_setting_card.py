# coding: utf-8
from typing import List, Union
from PySide6.QtCore import QEvent, Qt, QPropertyAnimation, Property, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QPainter, QIcon, QPainterPath
from PySide6.QtWidgets import QFrame, QWidget, QAbstractButton, QApplication, QScrollArea, QVBoxLayout, QLabel, QHBoxLayout

from ...common.config import isDarkTheme
from ...common.icon import FluentIcon as FIF
from ...common.style_sheet import FluentStyleSheet
from .setting_card import SettingCard, SettingIconWidget
from ..layout.v_box_layout import VBoxLayout


class ExpandButton(QAbstractButton):
    """ 展开按钮 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.__angle = 0
        self.isHover = False
        self.isPressed = False
        self.rotateAni = QPropertyAnimation(self, b'angle', self)
        self.clicked.connect(self.__onClicked)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)

        # 绘制背景
        r = 255 if isDarkTheme() else 0
        color = Qt.transparent

        if self.isEnabled():
            if self.isPressed:
                color = QColor(r, r, r, 10)
            elif self.isHover:
                color = QColor(r, r, r, 14)
        else:
            painter.setOpacity(0.36)

        painter.setBrush(color)
        painter.drawRoundedRect(self.rect(), 4, 4)

        # 绘制图标
        painter.translate(self.width()//2, self.height()//2)
        painter.rotate(self.__angle)
        FIF.ARROW_DOWN.render(painter, QRectF(-5, -5, 9.6, 9.6))

    def enterEvent(self, e):
        self.setHover(True)

    def leaveEvent(self, e):
        self.setHover(False)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.setPressed(True)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.setPressed(False)

    def setHover(self, isHover: bool):
        self.isHover = isHover
        self.update()

    def setPressed(self, isPressed: bool):
        self.isPressed = isPressed
        self.update()

    def __onClicked(self):
        self.setExpand(self.angle < 180)

    def setExpand(self, isExpand: bool):
        self.rotateAni.stop()
        self.rotateAni.setEndValue(180 if isExpand else 0)
        self.rotateAni.setDuration(200)
        self.rotateAni.start()

    def getAngle(self):
        return self.__angle

    def setAngle(self, angle):
        self.__angle = angle
        self.update()

    angle = Property(float, getAngle, setAngle)


class SpaceWidget(QWidget):
    """ Spacing 部件 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(1)


class HeaderSettingCard(SettingCard):
    """ Header setting card """

    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.expandButton = ExpandButton(self)

        self.hBoxLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)

        self.titleLabel.setObjectName("titleLabel")
        self.installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj is self:
            if e.type() == QEvent.Enter:
                self.expandButton.setHover(True)
            elif e.type() == QEvent.Leave:
                self.expandButton.setHover(False)
            elif e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                self.expandButton.setPressed(True)
            elif e.type() == QEvent.MouseButtonRelease and e.button() == Qt.LeftButton:
                self.expandButton.setPressed(False)
                self.expandButton.click()

        return super().eventFilter(obj, e)

    def addWidget(self, widget: QWidget):
        """ 将部件添加到tail """
        N = self.hBoxLayout.count()
        self.hBoxLayout.removeItem(self.hBoxLayout.itemAt(N - 1))
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(19)
        self.hBoxLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))

        p = self.parent()  # type: ExpandSettingCard
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRoundedRect(QRectF(self.rect().adjusted(1, 1, -1, -1)), 6, 6)

        # 设置 bottom 边框 半径 到 0 如果 父部件 is expanded
        if hasattr(p, 'isExpand') and p.isExpand:
            path.addRect(1, self.height() - 8, self.width() - 2, 8)

        painter.drawPath(path.simplified())


class ExpandBorderWidget(QWidget):
    """ 展开setting card 边框 部件 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        parent.installEventFilter(self)

    def eventFilter(self, obj, e):
        if obj is self.parent() and e.type() == QEvent.Resize:
            self.resize(e.size())

        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)

        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setPen(QColor(0, 0, 0, 19))

        p = self.parent()  # type: ExpandSettingCard
        r, d = 6, 12
        ch, h, w = p.card.height(), self.height(), self.width()

        # 仅 绘制 rounded 区域 如果 父部件 is not expanded
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)

        # 绘制卡片下方的分隔线.
        if ch < h:
            painter.drawLine(1, ch, w - 1, ch)




class ExpandSettingCard(QScrollArea):
    """可展开的设置卡片."""

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        super().__init__(parent=parent)
        self.isExpand = False

        self.scrollWidget = QFrame(self)
        self.view = QFrame(self.scrollWidget)
        self.card = HeaderSettingCard(icon, title, content, self)

        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.viewLayout = QVBoxLayout(self.view)
        self.spaceWidget = SpaceWidget(self.scrollWidget)
        self.borderWidget = ExpandBorderWidget(self)

        # 展开动画
        self.expandAni = QPropertyAnimation(self.verticalScrollBar(), b'value', self)

        self.__initWidget()

    def __initWidget(self):
        """ 初始化部件 """
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setFixedHeight(self.card.height())
        self.setViewportMargins(0, self.card.height(), 0, 0)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 初始化布局
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(0)
        self.scrollLayout.addWidget(self.view)
        self.scrollLayout.addWidget(self.spaceWidget)

        # 初始化展开 动画
        self.expandAni.setEasingCurve(QEasingCurve.OutQuad)
        self.expandAni.setDuration(200)

        # 初始化样式表.
        self.view.setObjectName('view')
        self.scrollWidget.setObjectName('scrollWidget')
        self.setProperty('isExpand', False)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self.card)
        FluentStyleSheet.EXPAND_SETTING_CARD.apply(self)

        self.card.installEventFilter(self)
        self.expandAni.valueChanged.connect(self._onExpandValueChanged)
        self.card.expandButton.clicked.connect(self.toggleExpand)

    def addWidget(self, widget: QWidget):
        """将部件添加到尾部区域."""
        self.card.addWidget(widget)
        self._adjustViewSize()

    def wheelEvent(self, e):
        e.ignore()

    def setExpand(self, isExpand: bool):
        """设置卡片的展开状态."""
        if self.isExpand == isExpand:
            return

        self._adjustViewSize()

        # 更新样式表.
        self.isExpand = isExpand
        self.setProperty('isExpand', isExpand)
        self.setStyle(QApplication.style())

        # 开始展开 动画
        if isExpand:
            h = self.viewLayout.sizeHint().height()
            self.verticalScrollBar().setValue(h)
            self.expandAni.setStartValue(h)
            self.expandAni.setEndValue(0)
        else:
            self.expandAni.setStartValue(0)
            self.expandAni.setEndValue(self.verticalScrollBar().maximum())

        self.expandAni.start()
        self.card.expandButton.setExpand(isExpand)

    def toggleExpand(self):
        """ 切换展开 状态 """
        self.setExpand(not self.isExpand)

    def resizeEvent(self, e):
        self.card.resize(self.width(), self.card.height())
        self.scrollWidget.resize(self.width(), self.scrollWidget.height())

    def _onExpandValueChanged(self):
        vh = self.viewLayout.sizeHint().height()
        h = self.viewportMargins().top()
        self.setFixedHeight(max(h + vh - self.verticalScrollBar().value(), h))

    def _adjustViewSize(self):
        """ 调整视图 大小 """
        h = self.viewLayout.sizeHint().height()
        self.spaceWidget.setFixedHeight(h)

        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)

    def setValue(self, value):
        """ 设置配置 项的值 """
        pass



class GroupSeparator(QWidget):
    """分组分隔符."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(3)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawLine(0, 1, self.width(), 1)


class GroupWidget(QWidget):

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str, widget: QWidget, stretch=0, parent=None):
        super().__init__(parent=parent)
        self.iconWidget = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content, self)
        self.widget = widget

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        if not content:
            self.contentLabel.hide()

        self.iconWidget.setFixedSize(16, 16)
        self.setMinimumHeight(60)
        self.setIcon(icon)

        # 初始化布局
        self.hBoxLayout.setSpacing(16)
        self.hBoxLayout.setContentsMargins(48, 12, 48, 12)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignLeft)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(widget, stretch)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setIconSize(self, width: int, height: int):
        """ 设置 图标 固定大小 """
        self.iconWidget.setFixedSize(width, height)

    def setIcon(self, icon: Union[str, QIcon, FIF]):
        self.iconWidget.setIcon(icon)
        self.iconWidget.setHidden(self.iconWidget.icon.isNull())



class ExpandGroupSettingCard(ExpandSettingCard):
    """可展开的分组设置卡片."""

    def __init__(self, icon: Union[str, QIcon, FIF], title: str, content: str = None, parent=None):
        super().__init__(icon, title, content, parent)
        self.widgets = []   # type: 列表[QWidget]

        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

    def addGroupWidget(self, widget: QWidget):
        """向分组中添加部件."""
        # 添加分隔符.
        if self.viewLayout.count() >= 1:
            self.viewLayout.addWidget(GroupSeparator(self.view))

        widget.setParent(self.view)
        self.widgets.append(widget)
        self.viewLayout.addWidget(widget)
        self._adjustViewSize()

    def addGroup(self, icon: Union[str, QIcon, FIF], title: str, content: str, widget: QWidget, stretch=0) -> GroupWidget:
        """添加分组.

        参数
        ----------
        icon: str | QIcon | FluentIconBase
            分组图标.

        title: str
            分组标题.

        content: str
            分组描述.

        widget: str
            分组对应的部件.

        stretch: int
            部件的拉伸系数.
        """
        group = GroupWidget(icon, title, content, widget, stretch)
        self.addGroupWidget(group)
        return group

    def removeGroupWidget(self, widget: QWidget):
        """从卡片中移除分组."""
        if widget not in self.widgets:
            return

        layoutIndex = self.viewLayout.indexOf(widget)
        index = self.widgets.index(widget)

        self.viewLayout.removeWidget(widget)
        self.widgets.remove(widget)

        if not self.widgets:
            return self._adjustViewSize()

        # 移除分隔符.
        if layoutIndex >= 1:
            separator = self.viewLayout.itemAt(layoutIndex - 1).widget()
            separator.deleteLater()
            self.viewLayout.removeWidget(separator)
        elif index == 0:
            separator = self.viewLayout.itemAt(0).widget()
            separator.deleteLater()
            self.viewLayout.removeWidget(separator)

        self._adjustViewSize()

    def _adjustViewSize(self):
        """调整视图大小."""
        h = sum(w.sizeHint().height() + 3 for w in self.widgets)
        self.spaceWidget.setFixedHeight(h)

        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)


class SimpleExpandGroupSettingCard(ExpandGroupSettingCard):
    """简易可展开分组设置卡片."""

    def _adjustViewSize(self):
        """调整视图大小."""
        h = self.viewLayout.sizeHint().height()
        self.spaceWidget.setFixedHeight(h)

        if self.isExpand:
            self.setFixedHeight(self.card.height()+h)
