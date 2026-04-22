# coding: utf-8
"""日期范围选择器组件

提供 RangeCalendarPicker 组件，用于选择起始日期和结束日期，
点击后弹出支持范围高亮的日历面板。包含以下类:
- RangeFastDayScrollItemDelegate: 日期格子委托，实现范围高亮绘制
- RangeFastDayScrollView: 日期滚动视图，支持悬停预览
- RangeCalendarView: 日历面板，管理两阶段范围选择状态
- RangeCalendarPicker: 触发按钮，显示已选日期范围文本
"""

from typing import Union

from PySide6.QtCore import (
    Qt, Signal, QRectF, QDate, QPoint, QRect, QModelIndex,
    QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QCalendar
)
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QPushButton, QWidget, QHBoxLayout,
    QStackedWidget, QStyle
)

from ...common.style_sheet import FluentStyleSheet, isDarkTheme, themeColor, ThemeColor
from ...common.icon import FluentIcon as FIF
from ...common.screen import getCurrentScreenGeometry
from .calendar_view import CalendarViewBase, YearCalendarView, MonthCalendarView
from .fast_calendar_view import (
    FastDayScrollItemDelegate, FastDayScrollView, FastDayCalendarView,
    FastYearCalendarView, FastMonthCalendarView
)


class RangeFastDayScrollItemDelegate(FastDayScrollItemDelegate):
    """日期范围滚动项委托

    继承自 FastDayScrollItemDelegate，在原有绘制逻辑基础上增加范围高亮:
    - 范围内日期绘制浅灰色矩形背景
    - 起始/结束日绘制主题色空心圆边框
    - 悬停预览时绘制更低透明度的矩形背景
    """

    def __init__(self, min_date: QDate, max_date: QDate):
        """初始化日期范围委托

        Args:
            min_date: 当前页最小日期（用于非本月日期透明度判断）
            max_date: 当前页最大日期
        """
        super().__init__(min_date, max_date)
        self._rangeStart = QDate()
        self._rangeEnd = QDate()
        self._hoverDate = QDate()

    def setSelectedRange(self, startDate: QDate, endDate: QDate):
        """设置已选日期范围

        Args:
            startDate: 范围起始日期
            endDate: 范围结束日期
        """
        self._rangeStart = startDate
        self._rangeEnd = endDate

    def setHoverDate(self, date: QDate):
        """设置悬停预览日期

        Args:
            date: 鼠标悬停的日期，无效日期表示清除预览
        """
        self._hoverDate = date

    # ------------------------------------------------------------------
    # 范围判断辅助
    # ------------------------------------------------------------------

    def _isInRange(self, date: QDate) -> bool:
        """判断日期是否在已选范围内（不含端点）"""
        if not (self._rangeStart.isValid() and self._rangeEnd.isValid()):
            return False
        return self._rangeStart < date < self._rangeEnd

    def _isRangeEndpoint(self, date: QDate) -> bool:
        """判断日期是否为已选范围端点（起始或结束日）"""
        if not self._rangeStart.isValid():
            return False
        if date == self._rangeStart:
            return True
        if self._rangeEnd.isValid() and date == self._rangeEnd:
            return True
        return False

    def _isInPreview(self, date: QDate) -> bool:
        """判断日期是否在悬停预览范围内（不含端点）

        仅在已选起始日但未选结束日时生效。
        """
        if not (self._rangeStart.isValid() and not self._rangeEnd.isValid()):
            return False
        if not self._hoverDate.isValid():
            return False
        lo = min(self._rangeStart, self._hoverDate)
        hi = max(self._rangeStart, self._hoverDate)
        return lo < date < hi

    def _isPreviewEndpoint(self, date: QDate) -> bool:
        """判断日期是否为悬停预览端点（悬停日期本身）

        仅在已选起始日但未选结束日时生效。
        """
        if not (self._rangeStart.isValid() and not self._rangeEnd.isValid()):
            return False
        return self._hoverDate.isValid() and date == self._hoverDate

    # ------------------------------------------------------------------
    # 绘制重写
    # ------------------------------------------------------------------

    def paint(self, painter, option, index):
        """绘制日期格子"""
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        date = index.data(Qt.UserRole)

        # 先绘制范围背景（在圆形背景之下）
        if isinstance(date, QDate) and date.isValid():
            self._drawRangeBackground(painter, option, date)

        self._drawBackground(painter, option, index)
        self._drawText(painter, option, index)

    def _drawRangeBackground(self, painter: QPainter, option, date: QDate):
        """绘制连续范围高亮背景条带

        - 中间格子: 整格宽度矩形，与相邻格子无缝拼接
        - 起始端点: 左侧半圆 + 向右延伸到格子右边缘的矩形
        - 结束端点: 从格子左边缘向左延伸的矩形 + 右侧半圆
        """
        # 确定有效范围（已选或悬停预览）
        if self._rangeStart.isValid() and self._rangeEnd.isValid():
            lo, hi = self._rangeStart, self._rangeEnd
            alpha = 15
        elif (self._rangeStart.isValid() and not self._rangeEnd.isValid()
              and self._hoverDate.isValid()):
            lo = min(self._rangeStart, self._hoverDate)
            hi = max(self._rangeStart, self._hoverDate)
            alpha = 10
        else:
            return

        # 不在范围内（含端点）则不绘制
        if not (lo <= date <= hi):
            return

        is_start = (date == lo)
        is_end = (date == hi)

        # 单日范围不绘制背景条带
        if is_start and is_end:
            return

        painter.save()
        painter.setPen(Qt.NoPen)
        c = 255 if isDarkTheme() else 0
        painter.setBrush(QColor(c, c, c, alpha))

        r = option.rect
        # 上下留 margin，与格子圆形的 itemMargin 保持一致
        m = self._itemMargin()
        top = float(r.top() + m)
        bottom = float(r.bottom() - m)
        h = bottom - top
        left = float(r.left())
        # QRect.right() = left + width - 1，+1 得到真实右边界，消除相邻格子间的 1px 间隙
        right = float(r.right() + 1)
        # 半圆半径 = 条带高度的一半
        radius = h / 2.0

        if is_start:
            # 起始端点: 左侧绘制半圆，右侧直角延伸到格子右边缘
            path = QPainterPath()
            cx = float(r.center().x())
            arc_rect = QRectF(cx - radius, top, radius * 2, h)
            path.moveTo(cx, top)
            path.arcTo(arc_rect, 90, 180)   # 左半圆（从顶部顺时针到底部）
            path.lineTo(right, bottom)
            path.lineTo(right, top)
            path.closeSubpath()
            painter.drawPath(path)

        elif is_end:
            # 结束端点: 左侧直角从格子左边缘延伸，右侧绘制半圆
            path = QPainterPath()
            cx = float(r.center().x())
            arc_rect = QRectF(cx - radius, top, radius * 2, h)
            path.moveTo(cx, top)
            path.lineTo(left, top)
            path.lineTo(left, bottom)
            path.lineTo(cx, bottom)
            path.arcTo(arc_rect, 270, 180)  # 右半圆（从底部顺时针到顶部）
            path.closeSubpath()
            painter.drawPath(path)

        else:
            # 中间格子: 整格宽度矩形，x 方向不留 margin，与相邻格子无缝拼接
            painter.drawRect(QRectF(left, top, right - left, h))

        painter.restore()

    def _drawBackground(self, painter: QPainter, option, index: QModelIndex):
        """重写背景绘制，为范围端点绘制主题色空心圆边框"""
        date = index.data(Qt.UserRole)
        if not isinstance(date, QDate):
            super()._drawBackground(painter, option, index)
            return

        is_endpoint = self._isRangeEndpoint(date) or self._isPreviewEndpoint(date)

        if is_endpoint and date != self.currentDate:
            # 绘制主题色空心圆边框
            painter.save()
            painter.setPen(themeColor())
            painter.setBrush(Qt.transparent)
            m = self._itemMargin()
            painter.drawEllipse(option.rect.adjusted(m, m, -m, -m))
            painter.restore()
        else:
            super()._drawBackground(painter, option, index)

    def _drawText(self, painter: QPainter, option, index: QModelIndex):
        """重写文字绘制，为范围端点使用主题色文字"""
        date = index.data(Qt.UserRole)
        if not isinstance(date, QDate):
            super()._drawText(painter, option, index)
            return

        is_endpoint = self._isRangeEndpoint(date) or self._isPreviewEndpoint(date)
        in_range = self._isInRange(date) or self._isInPreview(date)

        if is_endpoint and date != self.currentDate:
            # 范围端点：主题色文字
            painter.save()
            painter.setFont(self.font)
            painter.setPen(themeColor())
            painter.drawText(option.rect, Qt.AlignCenter, index.data(Qt.DisplayRole))
            painter.restore()
        elif in_range:
            # 范围内日期：正常颜色，不降低透明度
            painter.save()
            painter.setFont(self.font)
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            painter.drawText(option.rect, Qt.AlignCenter, index.data(Qt.DisplayRole))
            painter.restore()
        else:
            super()._drawText(painter, option, index)


class RangeFastDayScrollView(FastDayScrollView):
    """日期范围滚动视图

    继承自 FastDayScrollView，使用 RangeFastDayScrollItemDelegate 实现范围高亮，
    并添加鼠标悬停预览逻辑。
    """

    hoverDateChanged = Signal(QDate)

    def __init__(self, parent=None):
        """初始化日期范围滚动视图"""
        super().__init__(parent)
        # 替换为范围委托（父类已在 __init__ 中创建了 FastDayScrollItemDelegate）
        # 用父类委托的 min/max 初始化，保证非本月日期透明度正确
        old = self.delegate
        lo, hi = self.currentPageRange()
        self.rangeDelegate = RangeFastDayScrollItemDelegate(lo, hi)
        self.rangeDelegate.setCurrentDate(old.currentDate)
        self.setItemDelegate(self.rangeDelegate)
        self.delegate = self.rangeDelegate
        self.setMouseTracking(True)

    def setSelectedRange(self, startDate: QDate, endDate: QDate):
        """设置已选日期范围，触发重绘"""
        self.rangeDelegate.setSelectedRange(startDate, endDate)
        self.viewport().update()

    def setHoverDate(self, date: QDate):
        """设置悬停预览日期，触发重绘"""
        self.rangeDelegate.setHoverDate(date)
        self.viewport().update()

    def mouseMoveEvent(self, e):
        """鼠标移动事件，更新悬停预览日期"""
        super().mouseMoveEvent(e)
        index = self.indexAt(e.pos())
        if index.isValid():
            date = index.data(Qt.UserRole)
            if isinstance(date, QDate) and date.isValid():
                self.hoverDateChanged.emit(date)
                return
        self.hoverDateChanged.emit(QDate())

    def leaveEvent(self, e):
        """鼠标离开事件，清除悬停预览"""
        super().leaveEvent(e)
        self.hoverDateChanged.emit(QDate())


class RangeFastDayCalendarView(FastDayCalendarView):
    """日期范围日历视图（日视图层）

    继承自 FastDayCalendarView，替换内部滚动视图为 RangeFastDayScrollView。
    """

    def __init__(self, parent=None):
        """初始化"""
        # 调用 CalendarViewBase.__init__，跳过 FastDayCalendarView.__init__ 中的 setScrollView
        CalendarViewBase.__init__(self, parent)
        self.setScrollView(RangeFastDayScrollView(self))

    @property
    def rangeScrollView(self) -> RangeFastDayScrollView:
        """返回内部范围滚动视图"""
        return self.scrollView  # type: ignore


class RangeCalendarView(QWidget):
    """日期范围日历视图（弹出面板）

    弹出式日历面板，支持两阶段范围选择:
    1. 第一次点击设置起始日期
    2. 第二次点击设置结束日期并关闭面板

    鼠标悬停时实时预览从起始日到悬停日期的范围高亮。
    若结束日期早于起始日期，自动交换两者。
    """

    dateRangeChanged = Signal(QDate, QDate)

    def __init__(self, parent=None):
        """初始化日期范围日历视图"""
        super().__init__(parent)

        self._startDate = QDate()
        self._endDate = QDate()
        self._isSelectingEnd = False

        self.stackedWidget = QStackedWidget(self)
        self.dayView = RangeFastDayCalendarView(self)
        self.monthView = FastMonthCalendarView(self)
        self.yearView = FastYearCalendarView(self)

        self.stackedWidget.addWidget(self.dayView)
        self.stackedWidget.addWidget(self.monthView)
        self.stackedWidget.addWidget(self.yearView)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.stackedWidget)

        self.opacityAni = QPropertyAnimation(self, b'windowOpacity', self)
        self.slideAni = QPropertyAnimation(self, b'geometry', self)
        self.aniGroup = QParallelAnimationGroup(self)
        self.aniGroup.addAnimation(self.opacityAni)
        self.aniGroup.addAnimation(self.slideAni)

        self.__initWidget()

    def __initWidget(self):
        """初始化组件属性和信号连接"""
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self._setShadowEffect()

        self.dayView.setDate(QDate.currentDate())

        self.dayView.titleClicked.connect(self._onDayViewTitleClicked)
        self.monthView.titleClicked.connect(self._onMonthTitleClicked)
        self.monthView.itemClicked.connect(self._onMonthItemClicked)
        self.yearView.itemClicked.connect(self._onYearItemClicked)
        self.dayView.itemClicked.connect(self._onDayItemClicked)

        # 连接悬停信号
        self.dayView.rangeScrollView.hoverDateChanged.connect(self._onHoverDateChanged)

    def _setShadowEffect(self, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        """设置阴影效果"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        self.shadowEffect = QGraphicsDropShadowEffect(self.stackedWidget)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.stackedWidget.setGraphicsEffect(self.shadowEffect)

    def _onHoverDateChanged(self, date: QDate):
        """鼠标悬停日期变化时更新预览"""
        if not self._isSelectingEnd:
            return
        self.dayView.rangeScrollView.setHoverDate(date)

    def _onDayViewTitleClicked(self):
        """点击日视图标题，切换到月视图"""
        self.stackedWidget.setCurrentWidget(self.monthView)
        self.monthView.setDate(self.dayView.currentPageDate())

    def _onMonthTitleClicked(self):
        """点击月视图标题，切换到年视图"""
        self.stackedWidget.setCurrentWidget(self.yearView)
        self.yearView.setDate(self.monthView.currentPageDate())

    def _onMonthItemClicked(self, date: QDate):
        """点击月份项，切换到日视图"""
        self.stackedWidget.setCurrentWidget(self.dayView)
        self.dayView.scrollToDate(date)

    def _onYearItemClicked(self, date: QDate):
        """点击年份项，切换到月视图"""
        self.stackedWidget.setCurrentWidget(self.monthView)
        self.monthView.setDate(date)

    def _onDayItemClicked(self, date: QDate):
        """处理日期点击，实现两阶段范围选择

        第一次点击设置起始日期，第二次点击设置结束日期并关闭面板。
        若结束日期早于起始日期，自动交换。
        """
        scroll = self.dayView.rangeScrollView

        if not self._isSelectingEnd:
            # 第一阶段：设置起始日期
            self._startDate = QDate(date)
            self._endDate = QDate()
            self._isSelectingEnd = True
            scroll.setSelectedRange(self._startDate, self._endDate)
            scroll.setHoverDate(QDate())
        else:
            # 第二阶段：设置结束日期
            end = QDate(date)
            if end < self._startDate:
                self._startDate, end = end, self._startDate

            self._endDate = end
            self._isSelectingEnd = False
            scroll.setSelectedRange(self._startDate, self._endDate)
            scroll.setHoverDate(QDate())

            self.dateRangeChanged.emit(self._startDate, self._endDate)
            self.close()

    def setDateRange(self, startDate: QDate, endDate: QDate):
        """程序化设置日期范围"""
        if endDate.isValid() and startDate.isValid() and endDate < startDate:
            startDate, endDate = endDate, startDate

        self._startDate = QDate(startDate)
        self._endDate = QDate(endDate)
        self._isSelectingEnd = False

        self.dayView.rangeScrollView.setSelectedRange(self._startDate, self._endDate)

        if startDate.isValid():
            self.dayView.setDate(startDate)

    def exec(self, pos: QPoint, ani=True):
        """显示日历视图

        Args:
            pos: 显示位置（全局坐标）
            ani: 是否使用动画效果
        """
        if self.isVisible():
            return

        rect = getCurrentScreenGeometry()
        w, h = self.sizeHint().width() + 5, self.sizeHint().height()
        pos.setX(max(rect.left(), min(pos.x(), rect.right() - w)))
        pos.setY(max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5)))
        self.move(pos)

        if not ani:
            return self.show()

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.setEasingCurve(QEasingCurve.OutQuad)

        self.slideAni.setStartValue(QRect(pos - QPoint(0, 8), self.sizeHint()))
        self.slideAni.setEndValue(QRect(pos, self.sizeHint()))
        self.slideAni.setDuration(150)
        self.slideAni.setEasingCurve(QEasingCurve.OutQuad)
        self.aniGroup.start()

        self.show()


class RangeCalendarPicker(QPushButton):
    """日期范围选择器

    用于选择日期范围（起始日期和结束日期）的按钮组件，
    点击后弹出支持范围高亮的日历面板。

    用法示例::

        picker = RangeCalendarPicker(parent)
        picker.dateRangeChanged.connect(lambda s, e: print(s, e))
        picker.setDateRange(QDate(2024, 3, 13), QDate(2024, 3, 21))
    """

    dateRangeChanged = Signal(QDate, QDate)

    def __init__(self, parent=None):
        """初始化日期范围选择器"""
        super().__init__(parent=parent)
        self._startDate = QDate()
        self._endDate = QDate()
        self._dateFormat = Qt.DateFormat.ISODate

        self.setText(self.tr('Pick a date range'))
        FluentStyleSheet.RANGE_CALENDAR_PICKER.apply(self)

        self.clicked.connect(self._showCalendarView)

    def getStartDate(self) -> QDate:
        """获取范围起始日期"""
        return self._startDate

    def getEndDate(self) -> QDate:
        """获取范围结束日期"""
        return self._endDate

    def setDateRange(self, startDate: QDate, endDate: QDate):
        """程序化设置日期范围

        若结束日期早于起始日期，自动交换。
        """
        if endDate.isValid() and startDate.isValid() and endDate < startDate:
            startDate, endDate = endDate, startDate

        self._startDate = QDate(startDate)
        self._endDate = QDate(endDate)
        self._updateText()
        self.dateRangeChanged.emit(self._startDate, self._endDate)

    def reset(self):
        """重置为未选择状态"""
        self._startDate = QDate()
        self._endDate = QDate()
        self.setText(self.tr('Pick a date range'))
        self.setProperty('hasDate', False)
        self.setStyle(QApplication.style())
        self.update()

    def getDateFormat(self) -> Union[Qt.DateFormat, str]:
        """获取日期显示格式"""
        return self._dateFormat

    def setDateFormat(self, fmt: Union[Qt.DateFormat, str]):
        """设置日期显示格式"""
        self._dateFormat = fmt
        self._updateText()

    def _updateText(self):
        """根据当前选择状态更新按钮显示文本"""
        if not self._startDate.isValid():
            self.setText(self.tr('Pick a date range'))
            self.setProperty('hasDate', False)
        elif not self._endDate.isValid():
            start = self._startDate.toString(self._dateFormat)
            self.setText(f"{start} - ...")
            self.setProperty('hasDate', True)
        else:
            start = self._startDate.toString(self._dateFormat)
            end = self._endDate.toString(self._dateFormat)
            self.setText(f"{start} - {end}")
            self.setProperty('hasDate', True)

        self.setStyle(QApplication.style())
        self.update()

    def _showCalendarView(self):
        """显示日期范围日历视图弹窗"""
        view = RangeCalendarView(self.window())

        if self._startDate.isValid() and self._endDate.isValid():
            view.setDateRange(self._startDate, self._endDate)
        elif self._startDate.isValid():
            view.dayView.setDate(self._startDate)

        view.dateRangeChanged.connect(self._onDateRangeChanged)

        x = int(self.width() / 2 - view.sizeHint().width() / 2)
        y = self.height()
        view.exec(self.mapToGlobal(QPoint(x, y)))

    def _onDateRangeChanged(self, startDate: QDate, endDate: QDate):
        """日期范围改变时的回调"""
        self._startDate = QDate(startDate)
        self._endDate = QDate(endDate)
        self._updateText()
        self.dateRangeChanged.emit(startDate, endDate)

    def paintEvent(self, e):
        """绘制事件，在按钮右侧绘制日历图标"""
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.property('hasDate'):
            painter.setOpacity(0.6)

        w = 12
        rect = QRectF(self.width() - 23, self.height() / 2 - w / 2, w, w)
        FIF.CALENDAR.render(painter, rect)
