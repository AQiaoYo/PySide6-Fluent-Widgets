# coding: utf-8
"""
日历选择器组件
"""

from typing import Union

from PySide6.QtCore import Qt, Signal, QRectF, QDate, QPoint, Property
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QPushButton, QApplication

from ...common.style_sheet import FluentStyleSheet
from ...common.icon import FluentIcon as FIF
from ..widgets.flyout import Flyout, FlyoutAnimationType
from .calendar_view import CalendarView
from .fast_calendar_view import FastCalendarView


class CalendarPicker(QPushButton):
    """日历选择器

    用于选择日期的按钮组件，点击后弹出日历视图
    """

    dateChanged = Signal(QDate)

    def __init__(self, parent=None):
        """初始化日历选择器

        Args:
            parent: 父组件，默认为 None
        """
        super().__init__(parent=parent)
        self._date = QDate()
        self._dateFormat = Qt.DateFormat.ISODate
        self._isResetEnabled = False

        self.setText(self.tr('Pick a date'))
        FluentStyleSheet.CALENDAR_PICKER.apply(self)

        self.clicked.connect(self._showCalendarView)

    def getDate(self):
        """获取当前选中的日期

        Returns:
            当前选中的 QDate 对象
        """
        return self._date

    def setDate(self, date: QDate):
        """设置选中的日期

        Args:
            date: 要设置的日期
        """
        self._onDateChanged(date)

    def reset(self):
        """重置日期为未选中状态"""
        self._date = QDate()
        self.setText(self.tr('Pick a date'))
        self.setProperty('hasDate', False)
        self.setStyle(QApplication.style())
        self.update()

    def getDateFormat(self):
        """获取日期显示格式

        Returns:
            日期显示格式
        """
        return self._dateFormat

    def setDateFormat(self, format: Union[Qt.DateFormat, str]):
        """设置日期显示格式

        Args:
            format: 日期格式，可为 Qt.DateFormat 或字符串
        """
        self._dateFormat = format
        if self.date.isValid():
            self.setText(self.date.toString(self.dateFormat))

    def isRestEnabled(self):
        """获取重置功能是否可用

        Returns:
            重置功能是否可用
        """
        return self._isResetEnabled

    def setResetEnabled(self, isEnabled: bool):
        """设置重置按钮的可用性

        Args:
            isEnabled: 是否启用重置功能
        """
        self._isResetEnabled = isEnabled

    def _showCalendarView(self):
        """显示日历视图弹窗"""
        view = CalendarView(self.window())
        view.setResetEnabled(self.isRestEnabled())

        view.resetted.connect(self.reset)
        view.dateChanged.connect(self._onDateChanged)

        if self.date.isValid():
            view.setDate(self.date)

        x = int(self.width()/2 - view.sizeHint().width()/2)
        y = self.height()
        view.exec(self.mapToGlobal(QPoint(x, y)))

    def _onDateChanged(self, date: QDate):
        """日期改变时的回调

        Args:
            date: 新的日期
        """
        self._date = QDate(date)
        self.setText(date.toString(self.dateFormat))
        self.setProperty('hasDate', True)
        self.setStyle(QApplication.style())
        self.update()

        self.dateChanged.emit(date)

    def paintEvent(self, e):
        """绘制事件

        Args:
            e: 绘制事件
        """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.property('hasDate'):
            painter.setOpacity(0.6)

        w = 12
        rect = QRectF(self.width() - 23, self.height()/2 - w/2, w, w)
        FIF.CALENDAR.render(painter, rect)

    date = Property(QDate, getDate, setDate)
    dateFormat = Property(Qt.DateFormat, getDateFormat, setDateFormat)


class FastCalendarPicker(CalendarPicker):
    """快速日历选择器

    支持下拉动画的日历选择器
    """

    def __init__(self, parent=None):
        """初始化快速日历选择器

        Args:
            parent: 父组件，默认为 None
        """
        super().__init__(parent=parent)
        self.flyoutAnimationType = FlyoutAnimationType.DROP_DOWN

    def setFlyoutAnimationType(self, aniType: FlyoutAnimationType):
        """设置弹出动画类型

        Args:
            aniType: 弹出动画类型
        """
        self.flyoutAnimationType = aniType

    def _showCalendarView(self):
        """显示快速日历视图弹窗"""
        view = FastCalendarView(self.window())
        view.setResetEnabled(self.isRestEnabled())

        view.resetted.connect(self.reset)
        view.dateChanged.connect(self._onDateChanged)

        if self.date.isValid():
            view.setDate(self.date)

        flyout = Flyout.make(view, self, self.window(), self.flyoutAnimationType)
        view.dateChanged.connect(flyout.close)