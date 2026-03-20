# coding: utf-8
from PySide6.QtCore import Qt, Signal, QTime, Property

from .picker_base import PickerBase, PickerColumnFormatter, DigitFormatter


class TimePickerBase(PickerBase):
    """ 时间选择器 基类 """

    timeChanged = Signal(QTime)

    def __init__(self, parent=None, showSeconds=False):
        super().__init__(parent=parent)
        self._isSecondVisible = showSeconds
        self._time = QTime()

    def getTime(self):
        return self._time

    def setTime(self, time: QTime):
        """ 设置 当前 时间

        参数
        ----------
        time: QTime
            当前 时间
        """
        raise NotImplementedError

    def isSecondVisible(self):
        return self._isSecondVisible

    def setSecondVisible(self, isVisible: bool):
        """ 设置seconds 列的可见性 """
        raise NotImplementedError


class MiniuteFormatter(DigitFormatter):
    """ 分钟 formatter """

    def encode(self, minute):
        return str(minute).zfill(2)


class AMHourFormatter(DigitFormatter):
    """ AM/PM 小时 formatter """

    def encode(self, hour):
        hour = int(hour)
        if hour in [0, 12]:
            return "12"

        return str(hour % 12)


class AMPMFormatter(PickerColumnFormatter):
    """ AM/PM formatter """

    def __init__(self):
        super().__init__()
        self.AM = self.tr('AM')
        self.PM = self.tr('PM')

    def encode(self, hour):
        if not str(hour).isdigit():
            return str(hour)

        hour = int(hour)
        return self.AM if hour < 12 else self.PM


class TimePicker(TimePickerBase):
    """ 24 hours 时间选择器 """

    def __init__(self, parent=None, showSeconds=False):
        super().__init__(parent, showSeconds)
        # 添加 小时 列
        w = 80 if showSeconds else 120
        self.addColumn(self.tr('hour'), range(0, 24),
                       w, formatter=DigitFormatter())

        # 添加 分钟 列
        self.addColumn(self.tr('minute'), range(0, 60),
                       w, formatter=MiniuteFormatter())

        # 添加 seconds 列
        self.addColumn(self.tr('second'), range(0, 60),
                       w, formatter=MiniuteFormatter())
        self.setColumnVisible(2, showSeconds)

    def setTime(self, time):
        if not time.isValid() or time.isNull():
            return

        self._time = time
        self.setColumnValue(0, time.hour())
        self.setColumnValue(1, time.minute())
        self.setColumnValue(2, time.second())

    def setSecondVisible(self, isVisible: bool):
        self._isSecondVisible = isVisible
        self.setColumnVisible(2, isVisible)

        w = 80 if isVisible else 120
        for button in self.columns:
            button.setFixedWidth(w)

    def _onConfirmed(self, value: list):
        super()._onConfirmed(value)
        h = self.decodeValue(0, value[0])
        m = self.decodeValue(1, value[1])
        s = 0 if len(value) == 2 else self.decodeValue(2, value[2])

        time = QTime(h, m, s)
        ot = self.time
        self.setTime(time)

        if ot != time:
            self.timeChanged.emit(time)

    def panelInitialValue(self):
        if any(self.value()):
            return self.value()

        time = QTime.currentTime()
        h = self.encodeValue(0, time.hour())
        m = self.encodeValue(1, time.minute())
        s = self.encodeValue(2, time.second())
        return [h, m, s] if self.isSecondVisible() else [h, m]

    def getTime(self):
        return self._time

    def isSecondVisible(self):
        return self._isSecondVisible

    time = Property(QTime, getTime, setTime)
    secondVisible = Property(bool, isSecondVisible, setSecondVisible)


class AMTimePicker(TimePickerBase):
    """ AM/PM 时间选择器 """

    def __init__(self, parent=None, showSeconds=False):
        super().__init__(parent, showSeconds)
        self.AM = self.tr('AM')
        self.PM = self.tr('PM')

        # 添加 小时 列
        self.addColumn(self.tr('hour'), range(1, 13),
                       80, formatter=AMHourFormatter())

        # 添加 分钟 列
        self.addColumn(self.tr('minute'), range(0, 60),
                       80, formatter=MiniuteFormatter())

        # 添加 秒 列
        self.addColumn(self.tr('second'), range(0, 60),
                       80, formatter=MiniuteFormatter())
        self.setColumnVisible(2, showSeconds)

        # 添加 AM/PM 列
        self.addColumn(self.AM, [self.AM, self.PM],
                       80, formatter=AMPMFormatter())

    def setSecondVisible(self, isVisible: bool):
        self._isSecondVisible = isVisible
        self.setColumnVisible(2, isVisible)

    def setTime(self, time):
        if not time.isValid() or time.isNull():
            return

        self._time = time
        self.setColumnValue(0, time.hour())
        self.setColumnValue(1, time.minute())
        self.setColumnValue(2, time.second())
        self.setColumnValue(3, time.hour())

    def _onConfirmed(self, value: list):
        super()._onConfirmed(value)

        if len(value) == 3:
            h, m, p = value
            s = 0
        else:
            h, m, s, p = value
            s = self.decodeValue(2, s)

        h = self.decodeValue(0, h)
        m = self.decodeValue(1, m)

        if p == self.AM:
            h = 0 if h == 12 else h
        elif p == self.PM:
            h = h if h == 12 else h + 12

        time = QTime(h, m, s)
        ot = self.time
        self.setTime(time)

        if ot != time:
            self.timeChanged.emit(time)

    def panelInitialValue(self):
        if any(self.value()):
            return self.value()

        time = QTime.currentTime()
        h = self.encodeValue(0, time.hour())
        m = self.encodeValue(1, time.minute())
        s = self.encodeValue(2, time.second())
        p = self.encodeValue(3, time.hour())
        return [h, m, s, p] if self.isSecondVisible() else [h, m, p]

    def getTime(self):
        return self._time

    def isSecondVisible(self):
        return self._isSecondVisible

    time = Property(QTime, getTime, setTime)
    secondVisible = Property(bool, isSecondVisible, setSecondVisible)
