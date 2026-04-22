# coding: utf-8
"""日历时间选择器组件

提供 CalendarTimePicker 组件，继承自 QPushButton，点击后弹出左侧日历视图
与右侧时间滚轮的联合面板，允许用户同时选择日期和时间，确认后通过
dateTimeChanged 信号通知外部。包含以下类:
- CalendarTimePickerView: 弹出面板，管理日历视图与时间滚轮的布局和交互
- CalendarTimePicker: 触发按钮，显示已选日期时间文本
"""

from typing import Union

from PySide6.QtCore import Qt, Signal, QRectF, QDate, QTime, QDateTime, QPoint, QSize, QModelIndex, Property
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStyle, QStyleOptionViewItem,
    QGraphicsDropShadowEffect
)

from ...common.icon import FluentIcon
from ...common.screen import getCurrentScreenGeometry
from ...common.style_sheet import FluentStyleSheet, setCustomStyleSheet, isDarkTheme, themeColor, ThemeColor
from ..widgets.cycle_list_widget import CycleListWidget
from .calendar_view import DayCalendarView, DayScrollItemDelegate
from .picker_base import ItemMaskWidget, SeparatorWidget, PickerToolButton


class CalendarTimePickerDayDelegate(DayScrollItemDelegate):
    """CalendarTimePicker 专用的日期委托

    与基类差异：
    - 今天 (currentIndex) 渲染为主题色描边圆（空心）
    - 用户选中 (selectedIndex) 渲染为主题色实心圆
    - 文字颜色相应调整
    仅在 CalendarTimePicker 面板内使用，不影响其他日历组件。
    """

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        if index == self.selectedIndex:
            painter.setPen(Qt.NoPen)
            if index == self.pressedIndex:
                painter.setBrush(ThemeColor.LIGHT_2.color())
            elif option.state & QStyle.State_MouseOver:
                painter.setBrush(ThemeColor.LIGHT_1.color())
            else:
                painter.setBrush(themeColor())
        elif index == self.currentIndex:
            painter.setPen(QPen(themeColor(), 1))
            c = 255 if isDarkTheme() else 0
            if index == self.pressedIndex:
                painter.setBrush(QColor(c, c, c, 7))
            elif option.state & QStyle.State_MouseOver:
                painter.setBrush(QColor(c, c, c, 9))
            else:
                painter.setBrush(Qt.transparent)
        else:
            painter.setPen(Qt.NoPen)
            c = 255 if isDarkTheme() else 0
            if index == self.pressedIndex:
                painter.setBrush(QColor(c, c, c, 7))
            elif option.state & QStyle.State_MouseOver:
                painter.setBrush(QColor(c, c, c, 9))
            else:
                painter.setBrush(Qt.transparent)

        m = self._itemMargin()
        painter.drawEllipse(option.rect.adjusted(m, m, -m, -m))
        painter.restore()

    def _drawText(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setFont(self.font)

        if index == self.selectedIndex:
            c = 0 if isDarkTheme() else 255
            painter.setPen(QColor(c, c, c))
        elif index == self.currentIndex:
            painter.setPen(themeColor())
        else:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            if not (self.min <= index.data(Qt.UserRole) <= self.max or option.state & QStyle.State_MouseOver) or \
                    index == self.pressedIndex:
                painter.setOpacity(0.6)

        text = index.data(Qt.DisplayRole)
        painter.drawText(option.rect, Qt.AlignCenter, text)
        painter.restore()


class CalendarTimePickerView(QWidget):
    """日历时间选择器弹出面板

    布局结构（与 Pro 版截图一致，三段式）::

        ┌──────────────────────────────────────────────────────┐  ← view (QFrame)
        │  ┌──────────────────────┐ │ ┌──────────────────────┐ │  ← topLayout
        │  │  DayCalendarView     │ │ │  wheelContainer      │ │    (calendar | vSep | wheels)
        │  │                      │ │ │  ┌──┬──┬──┐          │ │
        │  │                      │ │ │  │HH│MM│SS│          │ │
        │  │                      │ │ │  └──┴──┴──┘          │ │
        │  └──────────────────────┘ │ └──────────────────────┘ │
        ├──────────────────────────────────────────────────────┤  ← timeSeparator (full width)
        │            ✓            |            ×               │  ← bottomLayout
        └──────────────────────────────────────────────────────┘

    关键设计：
    - wheelContainer 是三列滚轮的专属容器，ItemMaskWidget 也以它为父
    - 这样 mask.x() 很小（=2），p.x()=0（列从容器左边开始），坐标系天然一致
    - ItemMaskWidget.paintEvent 中 self.x()=2，x = COL_W//2+4+2，在列宽范围内
    - ✓ 在左侧日历底部，× 在右侧时间区域底部
    """

    confirmed = Signal(QDate, QTime)

    ITEM_HEIGHT = 37
    HIGHLIGHT_ROW = 4
    # 列宽 96px，固定宽度 = 96+8 = 104px，三列共 312px ≈ 左侧日历 314px
    COL_W = 96

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.view = QFrame(self)
        self.view.setObjectName('view')

        # ── 左侧 ──
        self.calendarView = DayCalendarView(self.view)
        self.calendarSeparator = SeparatorWidget(Qt.Horizontal, self.view)
        self.calendarSeparator.setProperty('orientation', 'horizontal')
        self.yesButton = PickerToolButton(FluentIcon.ACCEPT, self.view)

        # ── 竖向分隔线 ──
        self.vSeparator = SeparatorWidget(Qt.Vertical, self.view)
        self.vSeparator.setProperty('orientation', 'vertical')

        # ── 右侧：wheelContainer 是三列滚轮的专属容器 ──
        # ItemMaskWidget 也以 wheelContainer 为父，坐标系天然一致
        self.wheelContainer = QWidget(self.view)

        # ── 列间分隔线（时-分、分-秒之间） ──
        self.colSep1 = SeparatorWidget(Qt.Vertical, self.wheelContainer)
        self.colSep1.setProperty('orientation', 'vertical')
        self.colSep2 = SeparatorWidget(Qt.Vertical, self.wheelContainer)
        self.colSep2.setProperty('orientation', 'vertical')

        self.hourWidget = CycleListWidget(
            [str(i) for i in range(24)],
            QSize(self.COL_W, self.ITEM_HEIGHT),
            Qt.AlignCenter,
            self.wheelContainer
        )
        self.minuteWidget = CycleListWidget(
            [str(i) for i in range(60)],
            QSize(self.COL_W, self.ITEM_HEIGHT),
            Qt.AlignCenter,
            self.wheelContainer
        )
        self.secondWidget = CycleListWidget(
            [str(i) for i in range(60)],
            QSize(self.COL_W, self.ITEM_HEIGHT),
            Qt.AlignCenter,
            self.wheelContainer
        )
        self.listWidgets = [self.hourWidget, self.minuteWidget, self.secondWidget]

        # ItemMaskWidget 父组件 = wheelContainer
        # mask.x()=2（很小），p.x()=0（列从容器左边开始）
        # paintEvent 中 x = COL_W//2+4+self.x() = 48+4+2 = 54，在列宽[0,104]内
        self.itemMaskWidget = ItemMaskWidget(self.listWidgets, self.wheelContainer)

        # ── 右侧底部 ──
        self.timeSeparator = SeparatorWidget(Qt.Horizontal, self.view)
        self.timeSeparator.setProperty('orientation', 'horizontal')
        self.cancelButton = PickerToolButton(FluentIcon.CLOSE, self.view)

        # ── 布局 ──
        self.outerLayout = QHBoxLayout(self)
        self.viewLayout = QVBoxLayout(self.view)
        self.topLayout = QHBoxLayout()
        self.bottomLayout = QHBoxLayout()
        self.wheelLayout = QHBoxLayout(self.wheelContainer)

        self.__initWidget()

    def __initWidget(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._setShadowEffect()

        self.yesButton.setIconSize(QSize(16, 16))
        self.cancelButton.setIconSize(QSize(13, 13))
        self.yesButton.setFixedHeight(33)
        self.cancelButton.setFixedHeight(33)
        self.yesButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cancelButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # calendarSeparator 不再使用（改为统一的全宽 timeSeparator）
        self.calendarSeparator.setVisible(False)

        # wheelContainer 固定宽度 = 3 列 + 2 条分隔线(各1px)
        # (COL_W+8)*3 + 2 = 314
        self.wheelContainer.setFixedWidth((self.COL_W + 8) * 3 + 2)

        # wheelContainer 内部布局：三列并排 + 列间分隔线，无间距
        self.wheelLayout.setSpacing(0)
        self.wheelLayout.setContentsMargins(0, 0, 0, 0)
        self.wheelLayout.addWidget(self.hourWidget)

        # 分隔线包裹在 VBox 中，上下留 20px 间距，两端不顶到头
        sep1Layout = QVBoxLayout()
        sep1Layout.setContentsMargins(0, 20, 0, 20)
        sep1Layout.addWidget(self.colSep1)
        self.wheelLayout.addLayout(sep1Layout)

        self.wheelLayout.addWidget(self.minuteWidget)

        sep2Layout = QVBoxLayout()
        sep2Layout.setContentsMargins(0, 20, 0, 20)
        sep2Layout.addWidget(self.colSep2)
        self.wheelLayout.addLayout(sep2Layout)

        self.wheelLayout.addWidget(self.secondWidget)

        # 顶部行：日历 | 竖分隔线 | 时间滚轮
        # vSeparator 仅在此行，不会延伸到底部按钮区域
        self.topLayout.setSpacing(0)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.calendarView)
        self.topLayout.addWidget(self.vSeparator)
        self.topLayout.addWidget(self.wheelContainer)

        # 底部按钮行：✓ | ✗（等宽，天然同一水平线）
        self.bottomLayout.setSpacing(0)
        self.bottomLayout.setContentsMargins(3, 3, 3, 3)
        self.bottomLayout.addWidget(self.yesButton)
        self.bottomLayout.addWidget(self.cancelButton)

        # 面板主布局：顶部行 + 单条全宽水平分隔线 + 底部按钮行
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.addLayout(self.topLayout)
        self.viewLayout.addWidget(self.timeSeparator)
        self.viewLayout.addLayout(self.bottomLayout)

        # 外层布局（为阴影留边距）
        self.outerLayout.setContentsMargins(12, 8, 12, 20)
        self.outerLayout.addWidget(self.view)

        # 样式
        FluentStyleSheet.CALENDAR_PICKER.apply(self.calendarView)
        FluentStyleSheet.TIME_PICKER.apply(self.hourWidget)
        FluentStyleSheet.TIME_PICKER.apply(self.minuteWidget)
        FluentStyleSheet.TIME_PICKER.apply(self.secondWidget)
        FluentStyleSheet.TIME_PICKER.apply(self.itemMaskWidget)
        FluentStyleSheet.CALENDAR_TIME_PICKER.apply(self)

        # 覆盖 CalendarViewBase 的边框（calendar_picker.qss 直接应用到 calendarView，
        # 优先级高于 CalendarTimePickerView CalendarViewBase 选择器，需在 Python 里覆盖）
        setCustomStyleSheet(
            self.calendarView,
            'CalendarViewBase { border: none; border-radius: 0px; background-color: transparent; }',
            'CalendarViewBase { border: none; border-radius: 0px; background-color: transparent; }'
        )

        # 仅替换本面板内 DayScrollView 的 delegate 和星期标签，不影响其他日历组件
        self._applyLocalCalendarStyle()

        for w in self.listWidgets:
            w.vScrollBar.valueChanged.connect(self.itemMaskWidget.update)

        self.yesButton.clicked.connect(self._onConfirmed)
        self.cancelButton.clicked.connect(self._fadeOut)

    def _applyLocalCalendarStyle(self):
        """局部替换 DayScrollView 的 delegate 和星期标签

        仅对本面板内的 DayCalendarView 生效，不影响全局 CalendarPicker 等组件。
        """
        scrollView = self.calendarView.scrollView

        # 1) 替换 delegate：保留原有 currentIndex / selectedIndex / range 状态
        oldDelegate = scrollView.delegate
        newDelegate = CalendarTimePickerDayDelegate(oldDelegate.min, oldDelegate.max)
        newDelegate.setCurrentIndex(oldDelegate.currentIndex)
        newDelegate.setSelectedIndex(oldDelegate.selectedIndex)
        scrollView.delegate = newDelegate
        scrollView.setItemDelegate(newDelegate)
        scrollView.viewport().update()

        # 2) 星期标签改为中文（一二三四五六日）
        zhWeekDays = ['一', '二', '三', '四', '五', '六', '日']
        labels = scrollView.weekDayGroup.findChildren(QLabel)
        for label, text in zip(labels, zhWeekDays):
            label.setText(text)

    def _setShadowEffect(self, blurRadius=30, offset=(0, 8), color=QColor(0, 0, 0, 30)):
        self.shadowEffect = QGraphicsDropShadowEffect(self.view)
        self.shadowEffect.setBlurRadius(blurRadius)
        self.shadowEffect.setOffset(*offset)
        self.shadowEffect.setColor(color)
        self.view.setGraphicsEffect(None)
        self.view.setGraphicsEffect(self.shadowEffect)

    def setDateTime(self, dt: QDateTime):
        """预填充日历和时间滚轮"""
        if not dt.isValid():
            return
        self.calendarView.setDate(dt.date())
        self.hourWidget.setSelectedItem(str(dt.time().hour()))
        self.minuteWidget.setSelectedItem(str(dt.time().minute()))
        self.secondWidget.setSelectedItem(str(dt.time().second()))

    def resizeEvent(self, e):
        """定位 ItemMaskWidget（相对于 wheelContainer）

        mask 和 listWidgets 的父组件都是 wheelContainer，坐标系完全一致。
        - mask.x() = 2（很小），p.x() = 0（列从容器左边开始）
        - paintEvent 中 x = COL_W//2+4+2 = 54，在列宽[0,104]内，能找到 item
        - mask.y() = ITEM_HEIGHT * HIGHLIGHT_ROW（相对于 wheelContainer）
        """
        super().resizeEvent(e)
        self._updateMaskGeometry()

    def showEvent(self, e):
        """面板显示时重新定位 mask，确保布局已完成"""
        super().showEvent(e)
        self._updateMaskGeometry()

    def _updateMaskGeometry(self):
        """更新 ItemMaskWidget 的位置和尺寸"""
        # wheelContainer 宽度 = (COL_W+8)*3 + 2(分隔线) = 314
        maskW = (self.COL_W + 8) * 3 + 2 - 3
        # paintEvent 中 painter.translate(w, y - self.y() + 7)
        # y = visualItemRect.y() = ITEM_HEIGHT * HIGHLIGHT_ROW（item 在 listWidget 中的 y）
        # self.y() = mask 在 wheelContainer 中的 y
        # 为使文字对齐 mask 顶部：y - self.y() + 7 = 0  →  self.y() = y + 7
        maskY = self.ITEM_HEIGHT * self.HIGHLIGHT_ROW + 7
        self.itemMaskWidget.resize(maskW, self.ITEM_HEIGHT)
        self.itemMaskWidget.move(0, maskY)
        self.itemMaskWidget.raise_()

        # 滚动按钮宽度 = item 宽度（COL_W），居中于 CycleListWidget
        for w in self.listWidgets:
            btnW = self.COL_W
            offsetX = (w.width() - btnW) // 2
            for btn in (w.upButton, w.downButton):
                btn.resize(btnW, btn.height())
                btn.move(offsetX, btn.y())

    def _onConfirmed(self):
        scrollView = self.calendarView.scrollView
        item = scrollView.currentItem()
        date = item.data(Qt.UserRole) if item is not None else None
        if not isinstance(date, QDate) or not date.isValid():
            date = QDate.currentDate()

        h = int(self.hourWidget.currentItem().text())
        m = int(self.minuteWidget.currentItem().text())
        s = int(self.secondWidget.currentItem().text())

        self.confirmed.emit(date, QTime(h, m, s))
        self._fadeOut()

    def _fadeOut(self):
        self.close()

    def exec(self, pos: QPoint, ani=False):
        if self.isVisible():
            return
        self.show()
        rect = getCurrentScreenGeometry()
        w, h = self.width() + 5, self.height()
        m = self.outerLayout.contentsMargins()
        pos.setX(max(rect.left(), min(pos.x() - m.left(), rect.right() - w)))
        pos.setY(max(rect.top(), min(pos.y() - 4, rect.bottom() - h + 5)))
        self.move(pos)


class CalendarTimePicker(QPushButton):
    """日历时间选择器

    继承自 QPushButton，点击后弹出左侧日历视图与右侧时间滚轮的联合面板，
    允许用户同时选择日期和时间，确认后通过 dateTimeChanged 信号通知外部。

    用法示例::

        picker = CalendarTimePicker(parent)
        picker.dateTimeChanged.connect(lambda dt: print(dt.toString()))
        picker.setDateTime(QDateTime.currentDateTime())
    """

    dateTimeChanged = Signal(QDateTime)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._dateTime = QDateTime()
        self._dateTimeFormat = 'yyyy-MM-dd HH:mm:ss'

        self.setText(self.tr('Pick a date and time'))
        FluentStyleSheet.CALENDAR_TIME_PICKER.apply(self)
        self.clicked.connect(self._showPanel)

    def getDateTime(self) -> QDateTime:
        return self._dateTime

    def setDateTime(self, dt: QDateTime):
        if not dt.isValid():
            return
        self._onDateTimeChanged(dt)

    def reset(self):
        self._dateTime = QDateTime()
        self.setText(self.tr('Pick a date and time'))
        self.setProperty('hasDateTime', False)
        self.setStyle(QApplication.style())
        self.update()

    def getDateFormat(self) -> str:
        return self._dateTimeFormat

    def setDateFormat(self, fmt: Union[str, 'Qt.DateFormat']):
        self._dateTimeFormat = fmt
        if self._dateTime.isValid():
            self.setText(self._dateTime.toString(self._dateTimeFormat))

    def _showPanel(self):
        panel = CalendarTimePickerView(self.window())
        dt = self._dateTime if self._dateTime.isValid() else QDateTime.currentDateTime()
        panel.setDateTime(dt)
        panel.confirmed.connect(self._onPanelConfirmed)

        x = int(self.width() / 2 - panel.sizeHint().width() / 2)
        y = self.height()
        panel.exec(self.mapToGlobal(QPoint(x, y)))

    def _onPanelConfirmed(self, date: QDate, time: QTime):
        self._onDateTimeChanged(QDateTime(date, time))

    def _onDateTimeChanged(self, dt: QDateTime):
        self._dateTime = QDateTime(dt)
        self.setText(dt.toString(self._dateTimeFormat))
        self.setProperty('hasDateTime', True)
        self.setStyle(QApplication.style())
        self.update()
        self.dateTimeChanged.emit(dt)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if not self.property('hasDateTime'):
            painter.setOpacity(0.6)
        w = 12
        rect = QRectF(self.width() - 23, self.height() / 2 - w / 2, w, w)
        FluentIcon.CALENDAR.render(painter, rect)

    dateTime = Property(QDateTime, getDateTime, setDateTime)
    dateFormat = Property(str, getDateFormat, setDateFormat)
