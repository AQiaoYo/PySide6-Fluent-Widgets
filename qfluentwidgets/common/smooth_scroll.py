# coding: utf-8
from collections import deque
from enum import Enum
from math import cos, pi, ceil

from PySide6.QtCore import QDateTime, Qt, QTimer, QPoint, QObject, QElapsedTimer, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication, QScrollArea, QAbstractScrollArea


class SmoothScroll:
    """ 滚动 smoothly """

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical, dynamicEngineEnabled=True):
        """
        参数
        ----------
        widget: QScrollArea
            滚动区域 到 滚动 smoothly

        orient: Orientation
            滚动 orientation

        dynamicEngineEnabled: bool
            是否 到 choose 滚动 engine dynamically based 上的 屏幕 dpi
        """
        self.widget = widget
        self.orient = orient

        self.dynamicEngineEnabled = dynamicEngineEnabled
        self.widthThreshold = 2560

        self.smoothMode = SmoothMode(SmoothMode.LINEAR)
        self.fixedStepScrollEngine = FixedStepSmoothScrollEngine(widget, orient)
        self.adaptiveScrollEngine = AdaptiveSmoothScrollEngine(widget, orient)

    def setDynamicEngineEnabled(self, isEnabled: bool):
        """ 设置 是否 到 use dynamic engine """
        self.dynamicEngineEnabled = isEnabled

    def setSmoothMode(self, smoothMode):
        """ 设置 平滑模式 """
        self.smoothMode = smoothMode
        self.fixedStepScrollEngine.setSmoothMode(smoothMode)
        self.adaptiveScrollEngine.setSmoothMode(smoothMode)

    def wheelEvent(self, e):
        # 仅 process wheel 事件 triggered by mouse, 修复 issue #75
        delta = e.angleDelta().y() if e.angleDelta().y() != 0 else e.angleDelta().x()
        if self.smoothMode == SmoothMode.NO_SMOOTH or abs(delta) % 120 != 0:
            QAbstractScrollArea.wheelEvent(self.widget, e)
            return

        engine = self._chooseScrollEngine()
        engine.wheelEvent(e, delta)

    def _chooseScrollEngine(self) -> "SmoothScrollEngineBase":
        """ choose 滚动 engine """
        # ellapse 时间 driven adaptive 滚动 engine 用于 HiDPI 屏幕
        if self.dynamicEngineEnabled and self.widget.width()*self.widget.devicePixelRatioF() > self.widthThreshold:
            return self.adaptiveScrollEngine

        return self.fixedStepScrollEngine


class SmoothMode(Enum):
    """ 平滑模式 """
    NO_SMOOTH = 0
    CONSTANT = 1
    LINEAR = 2
    QUADRATI = 3
    COSINE = 4


class SmoothScrollEngineBase(QObject):

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical):
        super().__init__(widget)
        self.widget = widget
        self.orient = orient
        self.fps = 60
        self.duration = 400
        self.stepsTotal = 0
        self.stepRatio = 1.5
        self.acceleration = 1
        self.lastWheelEvent = None
        self.lastWheelPos = QPointF()
        self.lastWheelGlobalPos = QPointF()
        self.scrollStamps = deque()
        self.stepsLeftQueue = deque()
        self.smoothMoveTimer = QTimer(widget)
        self.smoothMode = SmoothMode(SmoothMode.LINEAR)
        self.smoothMoveTimer.timeout.connect(self._smoothMove)

    def setSmoothMode(self, smoothMode):
        """ 设置 平滑模式 """
        self.smoothMode = smoothMode

    def wheelEvent(self, e: QWheelEvent, delta: int):
        raise NotImplementedError

    def _smoothMove(self):
        if not self.stepsLeftQueue:
            return

        # send interpolated 滚动 事件 到 滚动条
        totalDelta = self._getTotalDelta()
        self.sendScrollEventToScrollBar(totalDelta)

        # 停止scrolling 如果 queque is empty
        if not self.stepsLeftQueue:
            self.smoothMoveTimer.stop()

    def _getTotalDelta(self) -> float:
        raise NotImplementedError

    def sendScrollEventToScrollBar(self, totalDelta):
        # construct wheel 事件
        if self.orient == Qt.Vertical:
            pixelDelta = QPoint(round(totalDelta), 0)
            bar = self.widget.verticalScrollBar()
        else:
            pixelDelta = QPoint(0, round(totalDelta))
            bar = self.widget.horizontalScrollBar()

        e = QWheelEvent(
            self.lastWheelPos,
            self.lastWheelGlobalPos,
            pixelDelta,
            QPoint(round(totalDelta), 0),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollBegin,
            False,
        )

        # send wheel 事件 到 app
        QApplication.sendEvent(bar, e)


class FixedStepSmoothScrollEngine(SmoothScrollEngineBase):
    """ 滚动 smoothly (fixed step) """

    def wheelEvent(self, e: QWheelEvent, delta: int):
        # push 当前 时间 到 queque
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)
        while now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        # 调整the acceration ratio based 上的 unprocessed 事件
        accerationRatio = min(len(self.scrollStamps) / 15, 1)
        self.lastWheelPos = e.position()
        self.lastWheelGlobalPos = e.globalPosition()

        # 获取steps的number
        self.stepsTotal = self.fps * self.duration / 1000

        # 获取 moving distance corresponding 到 each 事件
        delta = delta * self.stepRatio
        if self.acceleration > 0:
            delta += delta * self.acceleration * accerationRatio

        # form 列表 的 moving distances 和 steps, 和 插入 it into 队列 用于 processing.
        self.stepsLeftQueue.append([delta, self.stepsTotal])

        # 溢出 时间 的 timer: 1000ms/frames
        self.smoothMoveTimer.start(int(1000 / self.fps))

    def _getTotalDelta(self):
        """ 滚动 smoothly 当 定时器 时间 out """
        totalDelta = 0

        # 计算the scrolling distance 的 all unprocessed 事件,
        # 定时器 will reduce number 的 steps by 1 each 时间 it overflows.
        for i in self.stepsLeftQueue:
            totalDelta += self._subDelta(i[0], i[1])
            i[1] -= 1

        # If 事件 has been processed, move it out 的 队列
        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] == 0:
            self.stepsLeftQueue.popleft()

        return totalDelta

    def _subDelta(self, delta, stepsLeft):
        """ 获取 interpolation 用于 each step """
        m = self.stepsTotal / 2
        x = abs(self.stepsTotal - stepsLeft - m)

        res = 0
        if self.smoothMode == SmoothMode.NO_SMOOTH:
            res = 0
        elif self.smoothMode == SmoothMode.CONSTANT:
            res = delta / self.stepsTotal
        elif self.smoothMode == SmoothMode.LINEAR:
            res = 2 * delta / self.stepsTotal * (m - x) / m
        elif self.smoothMode == SmoothMode.QUADRATI:
            res = 3 / 4 / m * (1 - x * x / m / m) * delta
        elif self.smoothMode == SmoothMode.COSINE:
            res = (cos(x * pi / m) + 1) / (2 * m) * delta

        return res


class AdaptiveSmoothScrollEngine(SmoothScrollEngineBase):
    """ 滚动 smoothly (time-based, adaptive, HiDPI friendly) """

    def __init__(self, widget: QScrollArea, orient=Qt.Vertical):
        super().__init__(widget, orient)
        self.elapsedTimer = QElapsedTimer()
        self.maxQueueSize = 3
        self.minDuration = 120

    def setSmoothMode(self, smoothMode):
        """ 设置 平滑模式 """
        self.smoothMode = smoothMode

    def wheelEvent(self, e, delta: int):
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.scrollStamps.append(now)
        while self.scrollStamps and now - self.scrollStamps[0] > 500:
            self.scrollStamps.popleft()

        accelerationRatio = min(len(self.scrollStamps) / 15, 1)

        self.lastWheelPos = e.position()
        self.lastWheelGlobalPos = e.globalPosition()

        # 计算adaptive 持续时间 based 上的 队列 pressure
        queuePressure = len(self.stepsLeftQueue)
        pressureRatio = min(queuePressure / self.maxQueueSize, 1)

        effectiveDuration = self.duration * (1 - 0.6 * pressureRatio)
        effectiveDuration = max(self.minDuration, effectiveDuration)

        # 计算delta
        delta = delta * self.stepRatio
        if self.acceleration > 0:
            delta += delta * self.acceleration * accelerationRatio

        # Merge 事件 如果 队列 is full
        if len(self.stepsLeftQueue) >= self.maxQueueSize:
            last = self.stepsLeftQueue[-1]
            last[0] += delta
            last[1] = max(last[1], effectiveDuration)
        else:
            self.stepsLeftQueue.append([delta, effectiveDuration])

        if not self.elapsedTimer.isValid():
            self.elapsedTimer.start()
        else:
            self.elapsedTimer.restart()

        # 开始定时器 使用 adaptive fps
        self.smoothMoveTimer.start(int(1000 / self.fps))

    def _getTotalDelta(self):
        dt = self.elapsedTimer.restart()  # elapsed 时间 中的 ms
        totalDelta = 0.0

        for item in self.stepsLeftQueue:
            remainingDelta, remainingTime = item

            if remainingTime <= 0:
                continue

            consumeTime = min(dt, remainingTime)
            ratio = consumeTime / remainingTime
            subDelta = self._subDelta(remainingDelta, ratio)

            item[0] -= subDelta
            item[1] -= consumeTime
            totalDelta += subDelta

        # 移除 finished 项
        while self.stepsLeftQueue and self.stepsLeftQueue[0][1] <= 0:
            self.stepsLeftQueue.popleft()

        return totalDelta

    def _subDelta(self, delta, ratio):
        """ 计算interpolated delta 用于 当前 frame """
        if self.smoothMode == SmoothMode.CONSTANT:
            return delta * ratio
        if self.smoothMode == SmoothMode.LINEAR:
            return delta * ratio
        if self.smoothMode == SmoothMode.QUADRATI:
            return delta * (1 - (1 - ratio) ** 2)
        if self.smoothMode == SmoothMode.COSINE:
            return delta * (1 - cos(ratio * pi)) / 2

        return delta * ratio
