# coding: utf-8
from typing import Iterable, List

from PySide6.QtCore import Qt, Signal, QSize, QRectF, QPoint, QPropertyAnimation, QEasingCurve, QObject
from PySide6.QtGui import QColor, QPainter, QCursor, QRegion
from PySide6.QtWidgets import (QApplication, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                             QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QListWidgetItem)

from ..widgets.cycle_list_widget import CycleListWidget
from ..widgets.button import TransparentToolButton
from ...common.icon import FluentIcon
from ...common.screen import getCurrentScreenGeometry
from ...common.style_sheet import FluentStyleSheet, themeColor, isDarkTheme
from ...common.color import autoFallbackThemeColor


class SeparatorWidget(QWidget):
    """分隔符部件"""

    def __init__(self, orient: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        if orient == Qt.Horizontal:
            self.setFixedHeight(1)
        else:
            self.setFixedWidth(1)

        self.setAttribute(Qt.WA_StyledBackground)
        FluentStyleSheet.TIME_PICKER.apply(self)


class ItemMaskWidget(QWidget):
    """项遮罩部件"""

    def __init__(self, listWidgets: List[CycleListWidget], parent=None):
        super().__init__(parent=parent)
        self.listWidgets = listWidgets
        self.setFixedHeight(37)
        self.lightBackgroundColor = QColor()
        self.darkBackgroundColor = QColor()
        FluentStyleSheet.TIME_PICKER.apply(self)

    def setCustomBackgroundColor(self, light, dark):
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing)

        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(autoFallbackThemeColor(self.lightBackgroundColor, self.darkBackgroundColor))
        painter.drawRoundedRect(self.rect().adjusted(4, 0, -3, 0), 5, 5)

        # 绘制文本
        painter.setPen(Qt.black if isDarkTheme() else Qt.white)
        painter.setFont(self.font())
        w, h = 0, self.height()
        for i, p in enumerate(self.listWidgets):
            painter.save()

            # 绘制first 项's 文本
            x = p.itemSize.width()//2 + 4 + self.x()
            item1 = p.itemAt(QPoint(x, self.y() + 6))
            if not item1:
                painter.restore()
                continue

            iw = item1.sizeHint().width()
            y = p.visualItemRect(item1).y()
            painter.translate(w, y - self.y() + 7)
            self._drawText(item1, painter, 0)

            # 绘制秒 项's 文本
            item2 = p.itemAt(self.pos() + QPoint(x, h - 6))
            self._drawText(item2, painter, h)

            painter.restore()
            w += (iw + 8)  # margin: 0 4px;

    def _drawText(self, item: QListWidgetItem, painter: QPainter, y: int):
        align = item.textAlignment()
        w, h = item.sizeHint().width(), item.sizeHint().height()
        if align & Qt.AlignLeft:
            rect = QRectF(15, y, w, h)      # padding-left: 11px
        elif align & Qt.AlignRight:
            rect = QRectF(4, y, w-15, h)    # padding-right: 11px
        elif align & Qt.AlignCenter:
            rect = QRectF(4, y, w, h)

        painter.drawText(rect, align, item.text())


class PickerColumnFormatter(QObject):
    """ Picker 列 formatter """

    def __init__(self):
        super().__init__()

    def encode(self, value):
        """将原始值转换为格式化值"""
        return str(value)

    def decode(self, value: str):
        """将格式化值转换为原始值"""
        return str(value)


class DigitFormatter(PickerColumnFormatter):
    """数字 formatter"""

    def decode(self, value):
        return int(value)


class PickerColumnButton(QPushButton):
    """Picker 列按钮"""

    def __init__(self, name: str, items: Iterable, width: int, align=Qt.AlignLeft, formatter=None, parent=None):
        super().__init__(text=name, parent=parent)
        self._name = name
        self._value = None   # type: str

        self.setItems(items)
        self.setAlignment(align)
        self.setFormatter(formatter)
        self.setFixedSize(width, 30)
        self.setObjectName('pickerButton')
        self.setProperty('hasBorder', False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def align(self):
        return self._align

    def setAlignment(self, align=Qt.AlignCenter):
        """设置文本 alignment"""
        if align == Qt.AlignLeft:
            self.setProperty('align', 'left')
        elif align == Qt.AlignRight:
            self.setProperty('align', 'right')
        else:
            self.setProperty('align', 'center')

        self._align = align
        self.setStyle(QApplication.style())

    def value(self) -> str:
        if self._value is None:
            return None

        return self.formatter().encode(self._value)

    def setValue(self, v):
        self._value = v
        if v is None:
            self.setText(self.name())
            self.setProperty('hasValue', False)
        else:
            self.setText(self.value())
            self.setProperty('hasValue', True)

        self.setStyle(QApplication.style())

    def items(self):
        return [self._formatter.encode(i) for i in self._items]

    def setItems(self, items: Iterable):
        self._items = list(items)

    def formatter(self):
        return self._formatter

    def setFormatter(self, formatter):
        self._formatter = formatter or PickerColumnFormatter()

    def name(self):
        return self._name

    def setName(self, name: str):
        if self.text() == self.name():
            self.setText(name)

        self._name = name


def checkColumnIndex(func):
    """检查列索引是否超出范围"""

    def wrapper(picker, index: int, *args, **kwargs):
        if not 0 <= index < len(picker.columns):
            return

        return func(picker, index, *args, **kwargs)

    return wrapper


class PickerBase(QPushButton):
    """ Picker 基类 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.columns = []   # type: 列表[PickerColumnButton]

        self.lightSelectedBackgroundColor = QColor()
        self.darkSelectedBackgroundColor = QColor()

        self._isResetEnabled = False
        self.hBoxLayout = QHBoxLayout(self)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._isScrollButtonRepeatEnabled = True

        FluentStyleSheet.TIME_PICKER.apply(self)
        self.clicked.connect(self._showPanel)

    def setSelectedBackgroundColor(self, light, dark):
        """设置选中行的背景颜色"""
        self.lightSelectedBackgroundColor = QColor(light)
        self.darkSelectedBackgroundColor = QColor(dark)

    def addColumn(self, name: str, items: Iterable, width: int, align=Qt.AlignCenter,
                  formatter: PickerColumnFormatter = None):
        """添加列
        
                Args:
                    name: 列的名称
                    items: 列的项
                    width: 列的宽度
                    align: 按钮的文本 alignment
                    formatter: 列的 formatter
        """
        # 创建列 按钮
        button = PickerColumnButton(name, items, width, align, formatter, self)
        self.columns.append(button)

        self.hBoxLayout.addWidget(button, 0, Qt.AlignLeft)

        # 更新按钮样式.
        for btn in self.columns[:-1]:
            btn.setProperty('hasBorder', True)
            btn.setStyle(QApplication.style())

    @checkColumnIndex
    def setColumnAlignment(self, index: int, align=Qt.AlignCenter):
        """设置指定列的文本 alignment"""
        self.columns[index].setAlignment(align)

    @checkColumnIndex
    def setColumnWidth(self, index: int, width: int):
        """设置指定列的宽度"""
        self.columns[index].setFixedWidth(width)

    @checkColumnIndex
    def setColumnTight(self, index: int):
        """设置指定列为紧凑"""
        fm = self.fontMetrics()
        w = max(fm.width(i) for i in self.columns[index].items) + 30
        self.setColumnWidth(index, w)

    @checkColumnIndex
    def setColumnVisible(self, index: int, isVisible: bool):
        """设置指定列的可见性"""
        self.columns[index].setVisible(isVisible)

    def value(self):
        return [c.value() for c in self.columns if c.isVisible()]

    def initialValue(self):
        return [c.initialValue() for c in self.columns if c.isVisible()]

    @checkColumnIndex
    def setColumnValue(self, index: int, value):
        self.columns[index].setValue(value)

    @checkColumnIndex
    def setColumnInitialValue(self, index: int, value):
        self.columns[index].setInitialValue(value)

    @checkColumnIndex
    def setColumnFormatter(self, index: int, formatter: PickerColumnFormatter):
        self.columns[index].setFormatter(formatter)

    @checkColumnIndex
    def setColumnItems(self, index: int, items: Iterable):
        self.columns[index].setItems(items)

    @checkColumnIndex
    def encodeValue(self, index: int, value):
        """将原始值转换为格式化值"""
        return self.columns[index].formatter().encode(value)

    @checkColumnIndex
    def decodeValue(self, index: int, value):
        """将格式化值转换为原始值"""
        return self.columns[index].formatter().decode(value)

    @checkColumnIndex
    def setColumn(self, index: int, name: str, items: Iterable, width: int, align=Qt.AlignCenter):
        """设置列
        
                Args:
                    index: 列的索引
                    name: 列的名称
                    items: 列的项
                    width: 列的宽度
                    align: 按钮的文本 alignment
        """
        button = self.columns[index]
        button.setText(name)
        button.setFixedWidth(width)
        button.setAlignment(align)

    def clearColumns(self):
        """清空所有列"""
        while self.columns:
            btn = self.columns.pop()
            self.hBoxLayout.removeWidget(btn)
            # 需要显式断开父子关系, 才能移除对父部件的引用.
            # 否则对象可能会一直存活到父部件生命周期结束才被回收.
            btn.setParent(None)
            btn.deleteLater()

    def enterEvent(self, e):
        self._setButtonProperty('enter', True)

    def leaveEvent(self, e):
        self._setButtonProperty('enter', False)

    def mousePressEvent(self, e):
        self._setButtonProperty('pressed', True)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._setButtonProperty('pressed', False)
        super().mouseReleaseEvent(e)

    def _setButtonProperty(self, name, value):
        """设置 picker 按钮的属性"""
        for button in self.columns:
            button.setProperty(name, value)
            button.setStyle(QApplication.style())

    def panelInitialValue(self):
        """返回面板的初始值"""
        return self.value()

    def setScrollButtonRepeatEnabled(self, isEnabled: bool):
        """设置是否启用滚动按钮自动重复"""
        self._isScrollButtonRepeatEnabled = isEnabled

    def _showPanel(self):
        """ 显示面板 """
        panel = PickerPanel(self)
        for column in self.columns:
            if column.isVisible():
                panel.addColumn(column.items(), column.width(), column.align())

        panel.setValue(self.panelInitialValue())
        panel.setResetEnabled(self.isRestEnabled())
        panel.setScrollButtonRepeatEnabled(self._isScrollButtonRepeatEnabled)
        panel.setSelectedBackgroundColor(
            self.lightSelectedBackgroundColor, self.darkSelectedBackgroundColor)

        panel.confirmed.connect(self._onConfirmed)
        panel.resetted.connect(self.reset)
        panel.columnValueChanged.connect(
            lambda i, v: self._onColumnValueChanged(panel, i, v))

        w = panel.vBoxLayout.sizeHint().width() - self.width()
        panel.exec(self.mapToGlobal(QPoint(-w//2, -37 * 4)))

    def _onConfirmed(self, value: list):
        for i, v in enumerate(value):
            self.setColumnValue(i, v)

    def reset(self):
        for i in range(len(self.columns)):
            self.setColumnValue(i, None)

    def _onColumnValueChanged(self, panel, index: int, value: str):
        """列值改变的槽函数"""
        pass

    def isRestEnabled(self):
        return self._isResetEnabled

    def setResetEnabled(self, isEnabled: bool):
        """设置是否启用重置按钮"""
        self._isResetEnabled = isEnabled


class PickerToolButton(TransparentToolButton):
    """ Picker 工具按钮 """

    def _drawIcon(self, icon, painter, rect):
        if self.isPressed:
            painter.setOpacity(1)

        super()._drawIcon(icon, painter, rect)


class PickerPanel(QWidget):
    """Picker 面板"""

    confirmed = Signal(list)
    resetted = Signal()
    columnValueChanged = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.itemHeight = 37
        self.listWidgets = []   # type: 列表[CycleListWidget]

        self.view = QFrame(self)
        self.itemMaskWidget = ItemMaskWidget(self.listWidgets, self)
        self.hSeparatorWidget = SeparatorWidget(Qt.Horizontal, self.view)
        self.yesButton = PickerToolButton(FluentIcon.ACCEPT, self.view)
        self.resetButton = PickerToolButton(FluentIcon.CANCEL, self.view)
        self.cancelButton = PickerToolButton(FluentIcon.CLOSE, self.view)

        self.hBoxLayout = QHBoxLayout(self)
        self.listLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout(self.view)

        self.scrollButtonRepeatEnabled = True

        self.__initWidget()

    def __initWidget(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint |
                            Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setShadowEffect()
        self.yesButton.setIconSize(QSize(16, 16))
        self.resetButton.setIconSize(QSize(16, 16))
        self.cancelButton.setIconSize(QSize(13, 13))
        self.yesButton.setFixedHeight(33)
        self.cancelButton.setFixedHeight(33)
        self.resetButton.setFixedHeight(33)

        self.hBoxLayout.setContentsMargins(12, 8, 12, 20)
        self.hBoxLayout.addWidget(self.view, 1, Qt.AlignCenter)
        self.hBoxLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.listLayout, 1)
        self.vBoxLayout.addWidget(self.hSeparatorWidget)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.buttonLayout.setSpacing(6)
        self.buttonLayout.setContentsMargins(3, 3, 3, 3)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.resetButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.yesButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resetButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cancelButton.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.yesButton.clicked.connect(self._fadeOut)
        self.yesButton.clicked.connect(
            lambda: self.confirmed.emit(self.value()))
        self.cancelButton.clicked.connect(self._fadeOut)
        self.resetButton.clicked.connect(self.resetted)
        self.resetButton.clicked.connect(self._fadeOut)

        self.setResetEnabled(False)

        self.view.setObjectName('view')
        FluentStyleSheet.TIME_PICKER.apply(self)

    def setShadowEffect(self, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        """添加阴影效果到对话框"""
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def setResetEnabled(self, isEnabled: bool):
        """设置是否启用重置按钮"""
        self.resetButton.setVisible(isEnabled)

    def setScrollButtonRepeatEnabled(self, isEnabled: bool):
        """设置是否启用滚动按钮自动重复"""
        self.scrollButtonRepeatEnabled = isEnabled
        for widget in self.listWidgets:
            widget.setScrollButtonRepeatEnabled(isEnabled)

    def setSelectedBackgroundColor(self, light, dark):
        self.itemMaskWidget.setCustomBackgroundColor(light, dark)

    def isResetEnabled(self):
        return self.resetButton.isVisible()

    def addColumn(self, items: Iterable, width: int, align=Qt.AlignCenter):
        """将一列添加到视图
        
                Args:
                    items: 要添加的项
                    width: 项的宽度
                    align: 项的文本 alignment
        """
        if self.listWidgets:
            self.listLayout.addWidget(SeparatorWidget(Qt.Vertical))

        w = CycleListWidget(items, QSize(width, self.itemHeight), align, self)
        w.setScrollButtonRepeatEnabled(self.scrollButtonRepeatEnabled)
        w.vScrollBar.valueChanged.connect(self.itemMaskWidget.update)

        N = len(self.listWidgets)
        w.currentItemChanged.connect(
            lambda i, n=N: self.columnValueChanged.emit(n, i.text()))

        self.listWidgets.append(w)
        self.listLayout.addWidget(w)

    def resizeEvent(self, e):
        self.itemMaskWidget.resize(self.view.width()-3, self.itemHeight)
        m = self.hBoxLayout.contentsMargins()
        self.itemMaskWidget.move(m.left()+2, m.top() + 148)

    def value(self):
        """返回列的值"""
        return [i.currentItem().text() for i in self.listWidgets]

    def setValue(self, value: list):
        """设置列的值"""
        if len(value) != len(self.listWidgets):
            return

        for v, w in zip(value, self.listWidgets):
            w.setSelectedItem(v)

    def columnValue(self, index: int) -> str:
        """返回指定列的值"""
        if not 0 <= index < len(self.listWidgets):
            return

        return self.listWidgets[index].currentItem().text()

    def setColumnValue(self, index: int, value: str):
        """设置指定列的值"""
        if not 0 <= index < len(self.listWidgets):
            return

        self.listWidgets[index].setSelectedItem(value)

    def column(self, index: int):
        """返回指定列的列表部件"""
        return self.listWidgets[index]

    def exec(self, pos, ani=True):
        """显示面板
        
                Args:
                    pos: 弹出位置
                    ani: 是否显示弹出动画
        """
        if self.isVisible():
            return

        # 显示before running 动画, 或 高度 calculation will be wrong
        self.show()

        rect = getCurrentScreenGeometry()
        w, h = self.width() + 5, self.height()
        pos.setX(
            min(pos.x() - self.layout().contentsMargins().left(), rect.right() - w))
        pos.setY(max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5)))
        self.move(pos)

        if not ani:
            return

        self.isExpanded = False
        self.ani = QPropertyAnimation(self.view, b'windowOpacity', self)
        self.ani.valueChanged.connect(self._onAniValueChanged)
        self.ani.setStartValue(0)
        self.ani.setEndValue(1)
        self.ani.setDuration(150)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.ani.start()

    def _onAniValueChanged(self, opacity):
        m = self.layout().contentsMargins()
        w = self.view.width() + m.left() + m.right() + 120
        h = self.view.height() + m.top() + m.bottom() + 12
        if not self.isExpanded:
            y = int(h / 2 * (1 - opacity))
            self.setMask(QRegion(0, y, w, h-y*2))
        else:
            y = int(h / 3 * (1 - opacity))
            self.setMask(QRegion(0, y, w, h-y*2))

    def _fadeOut(self):
        self.isExpanded = True
        self.ani = QPropertyAnimation(self, b'windowOpacity', self)
        self.ani.valueChanged.connect(self._onAniValueChanged)
        self.ani.finished.connect(self.deleteLater)
        self.ani.setStartValue(1)
        self.ani.setEndValue(0)
        self.ani.setDuration(150)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.ani.start()
