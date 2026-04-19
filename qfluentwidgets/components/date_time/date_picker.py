# coding: utf-8
"""日期时间选择器组件"""

from PySide6.QtCore import Qt, Signal, QDate, QCalendar, Property

from .picker_base import PickerBase, PickerPanel, PickerColumnFormatter, DigitFormatter


class DatePickerBase(PickerBase):
    """日期选择器基类"""

    dateChanged = Signal(QDate)

    def __init__(self, parent=None):
        """构造函数

        Args:
            parent: 父部件，默认为 None
        """
        super().__init__(parent)
        self._date = QDate()
        self.calendar = QCalendar()
        self._yearFormatter = None
        self._monthFormatter = None
        self._dayFormatter = None

    def getDate(self):
        """获取当前日期

        Returns:
            QDate: 当前日期
        """
        return self._date

    def setDate(self, date: QDate):
        """设置当前日期

        Args:
            date: 要设置的日期
        """
        raise NotImplementedError

    def setYearFormatter(self, formatter: PickerColumnFormatter):
        """设置年份列的格式化器

        Args:
            formatter: 年份列格式化器
        """
        self._yearFormatter = formatter

    def setMonthFormatter(self, formatter: PickerColumnFormatter):
        """设置月份列的格式化器

        Args:
            formatter: 月份列格式化器
        """
        self._monthFormatter = formatter

    def setDayFormatter(self, formatter: PickerColumnFormatter):
        """设置日期列的格式化器

        Args:
            formatter: 日期列格式化器
        """
        self._dayFormatter = formatter

    def yearFormatter(self):
        """获取年份列的格式化器

        Returns:
            PickerColumnFormatter: 年份列格式化器，若未设置则返回 DigitFormatter
        """
        return self._yearFormatter or DigitFormatter()

    def dayFormatter(self):
        """获取日期列的格式化器

        Returns:
            PickerColumnFormatter: 日期列格式化器，若未设置则返回 DigitFormatter
        """
        return self._dayFormatter or DigitFormatter()

    def monthFormatter(self):
        """获取月份列的格式化器

        Returns:
            PickerColumnFormatter: 月份列格式化器，若未设置则返回 MonthFormatter
        """
        return self._monthFormatter or MonthFormatter()


class MonthFormatter(PickerColumnFormatter):
    """月份格式化器"""

    def __init__(self):
        """构造函数"""
        super().__init__()
        self.months = [
            self.tr('January'), self.tr('February'), self.tr('March'),
            self.tr('April'), self.tr('May'), self.tr('June'),
            self.tr('July'), self.tr('August'), self.tr('September'),
            self.tr('October'), self.tr('November'), self.tr('December')
        ]

    def encode(self, month):
        """将月份数字编码为名称

        Args:
            month: 月份数字（1-12）

        Returns:
            str: 月份名称
        """
        return self.months[int(month) - 1]

    def decode(self, value):
        """将月份名称解码为数字

        Args:
            value: 月份名称

        Returns:
            int: 月份数字（1-12）
        """
        return self.months.index(value) + 1


class DatePicker(DatePickerBase):
    """日期选择器"""

    MM_DD_YYYY = 0
    YYYY_MM_DD = 1

    def __init__(self, parent=None, format=MM_DD_YYYY, isMonthTight=True):
        """构造函数

        Args:
            parent: 父部件，默认为 None
            format: 日期格式，可选 DatePicker.MM_DD_YYYY 或 DatePicker.YYYY_MM_DD
            isMonthTight: 月份列是否使用紧凑布局
        """
        super().__init__(parent=parent)
        self.MONTH = self.tr('month')
        self.YEAR = self.tr('year')
        self.DAY = self.tr('day')

        self.isMonthTight = isMonthTight
        self.setDateFormat(format)

    def setDateFormat(self, format: int):
        """设置日期格式

        Args:
            format: 日期格式，可选 DatePicker.MM_DD_YYYY 或 DatePicker.YYYY_MM_DD
        """
        self.clearColumns()
        y = QDate.currentDate().year()
        self.dateFormat = format

        if format == self.MM_DD_YYYY:
            self.monthIndex = 0
            self.dayIndex = 1
            self.yearIndex = 2

            self.addColumn(self.MONTH, range(1, 13),
                           80, Qt.AlignLeft, self.monthFormatter())
            self.addColumn(self.DAY, range(1, 32),
                           80, formatter=self.dayFormatter())
            self.addColumn(self.YEAR, range(y-100, y+101),
                           80, formatter=self.yearFormatter())
        elif format == self.YYYY_MM_DD:
            self.yearIndex = 0
            self.monthIndex = 1
            self.dayIndex = 2

            self.addColumn(self.YEAR, range(y-100, y+101),
                           80, formatter=self.yearFormatter())
            self.addColumn(self.MONTH, range(1, 13),
                           80, formatter=self.monthFormatter())
            self.addColumn(self.DAY, range(1, 32), 80,
                           formatter=self.dayFormatter())

        self.setColumnWidth(self.monthIndex, self._monthColumnWidth())

    def panelInitialValue(self):
        """获取面板初始值

        Returns:
            list: 面板的初始日期值列表
        """
        if any(self.value()):
            return self.value()

        date = QDate.currentDate()
        y = self.encodeValue(self.yearIndex, date.year())
        m = self.encodeValue(self.monthIndex, date.month())
        d = self.encodeValue(self.dayIndex, date.day())
        return [y, m, d] if self.dateFormat == self.YYYY_MM_DD else [m, d, y]

    def setMonthTight(self, isTight: bool):
        """设置月份列是否使用紧凑布局

        Args:
            isTight: 是否使用紧凑布局
        """
        if self.isMonthTight == isTight:
            return

        self.isMonthTight = isTight
        self.setColumnWidth(self.monthIndex, self._monthColumnWidth())

    def _monthColumnWidth(self):
        fm = self.fontMetrics()
        wm = max(fm.boundingRect(i).width()
                 for i in self.columns[self.monthIndex].items()) + 20

        # don't use tight 布局 用于 english
        if self.MONTH == 'month':
            return wm + 49

        return max(80, wm) if self.isMonthTight else wm + 49

    def _onColumnValueChanged(self, panel: PickerPanel, index, value):
        if index == self.dayIndex:
            return

        # 获取 days number 中的 月份
        month = self.decodeValue(
            self.monthIndex, panel.columnValue(self.monthIndex))
        year = self.decodeValue(
            self.yearIndex, panel.columnValue(self.yearIndex))
        days = self.calendar.daysInMonth(month, year)

        # 更新days
        c = panel.column(self.dayIndex)
        day = c.currentItem().text()
        self.setColumnItems(self.dayIndex, range(1, days + 1))

        c.setItems(self.columns[self.dayIndex].items())
        c.setSelectedItem(day)

    def _onConfirmed(self, value: list):
        year = self.decodeValue(self.yearIndex, value[self.yearIndex])
        month = self.decodeValue(self.monthIndex, value[self.monthIndex])
        day = self.decodeValue(self.dayIndex, value[self.dayIndex])

        date, od = QDate(year, month, day), self.date
        self.setDate(date)

        if od != date:
            self.dateChanged.emit(date)

    def getDate(self):
        """获取当前日期

        Returns:
            QDate: 当前日期
        """
        return self._date

    def setDate(self, date: QDate):
        """设置当前日期

        Args:
            date: 要设置的日期
        """
        if not date.isValid() or date.isNull():
            return

        self._date = date
        self.setColumnValue(self.monthIndex, date.month())
        self.setColumnValue(self.dayIndex, date.day())
        self.setColumnValue(self.yearIndex, date.year())
        self.setColumnItems(self.dayIndex, range(1, date.daysInMonth() + 1))

    date = Property(QDate, getDate, setDate)


class ZhFormatter(PickerColumnFormatter):
    """中文日期格式化器"""

    suffix = ""

    def encode(self, value):
        """将数值编码为带后缀的字符串

        Args:
            value: 数值

        Returns:
            str: 带后缀的字符串
        """
        return str(value) + self.suffix

    def decode(self, value: str):
        """将带后缀的字符串解码为数值

        Args:
            value: 带后缀的字符串

        Returns:
            int: 数值
        """
        return int(value[:-1])


class ZhYearFormatter(ZhFormatter):
    """中文年份格式化器"""

    suffix = "年"


class ZhMonthFormatter(ZhFormatter):
    """中文月份格式化器"""

    suffix = "月"


class ZhDayFormatter(ZhFormatter):
    """中文日期格式化器"""

    suffix = "日"


class ZhDatePicker(DatePicker):
    """中文日期选择器"""

    def __init__(self, parent=None):
        """构造函数

        Args:
            parent: 父部件，默认为 None
        """
        super().__init__(parent, DatePicker.YYYY_MM_DD)
        self.MONTH = "月"
        self.YEAR = "年"
        self.DAY = "日"
        self.setDayFormatter(ZhDayFormatter())
        self.setYearFormatter(ZhYearFormatter())
        self.setMonthFormatter(ZhMonthFormatter())
        self.setDateFormat(self.YYYY_MM_DD)