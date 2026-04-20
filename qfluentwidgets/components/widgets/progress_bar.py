# coding: utf-8
"""提供进度条相关控件，用于在界面中直观展示任务处理进度

适用于需要向用户反馈当前完成度的各类场景，包括文件下载、软件安装和数据加载等，支持确定与不确定两种进度显示模式
"""

from math import floor

from PySide6.QtCore import (QEasingCurve, Qt, QPropertyAnimation, Property,
                          QParallelAnimationGroup, QSequentialAnimationGroup, QLocale)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QProgressBar

from ...common.style_sheet import themeColor, isDarkTheme



class ProgressBar(QProgressBar):
    """用于展示已知完成百分比的水平进度条控件
    
    适用于能够精确计算当前任务进度的场景，例如文件下载、视频转码或批量数据处理，可通过 setValue() 方法实时更新进度值以反馈最新状态
    """

    def __init__(self, parent=None, useAni=True):
        """初始化进度条

        Args:
            parent: 父窗口，默认为 None
            useAni: 是否使用动画效果，默认为 True
        """
        super().__init__(parent)
        self._val = 0
        self.setFixedHeight(4)

        self._useAni = useAni
        self.lightBackgroundColor = QColor(0, 0, 0, 155)
        self.darkBackgroundColor = QColor(255, 255, 255, 155)
        self._lightBarColor = QColor()
        self._darkBarColor = QColor()
        self.ani = QPropertyAnimation(self, b'val', self)

        self._isPaused = False
        self._isError = False
        self.valueChanged.connect(self._onValueChanged)
        self.setValue(0)

    def getVal(self):
        """获取当前值

        Returns:
            当前进度值
        """
        return self._val

    def setVal(self, v: float):
        """设置当前值

        Args:
            v: 进度值
        """
        self._val = v
        self.update()

    def isUseAni(self):
        """是否使用动画效果

        Returns:
            是否使用动画
        """
        return self._useAni

    def setUseAni(self, isUSe: bool):
        """设置是否使用动画效果

        Args:
            isUSe: 是否使用动画
        """
        self._useAni = isUSe

    def _onValueChanged(self, value):
        """数值变化时的回调

        Args:
            value: 新的进度值
        """
        if not self.useAni:
            self._val = value
            return

        self.ani.stop()
        self.ani.setEndValue(value)
        self.ani.setDuration(150)
        self.ani.start()
        super().setValue(value)

    def lightBarColor(self):
        """获取亮色主题下的条形颜色

        Returns:
            亮色主题条形颜色
        """
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        """获取暗色主题下的条形颜色

        Returns:
            暗色主题条形颜色
        """
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """设置自定义条形颜色

        Args:
            light: 亮色主题下的条形颜色，可为 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的条形颜色，可为 str、Qt.GlobalColor 或 QColor
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    def setCustomBackgroundColor(self, light, dark):
        """设置自定义背景颜色

        Args:
            light: 亮色主题下的背景颜色，可为 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的背景颜色，可为 str、Qt.GlobalColor 或 QColor
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def resume(self):
        """恢复进度条"""
        self._isPaused = False
        self._isError = False
        self.update()

    def pause(self):
        """暂停进度条"""
        self._isPaused = True
        self.update()

    def setPaused(self, isPaused: bool):
        """设置暂停状态

        Args:
            isPaused: 是否暂停
        """
        self._isPaused = isPaused
        self.update()

    def isPaused(self):
        """是否处于暂停状态

        Returns:
            是否暂停
        """
        return self._isPaused

    def error(self):
        """设置为错误状态"""
        self._isError = True
        self.update()

    def setError(self, isError: bool):
        """设置错误状态

        Args:
            isError: 是否为错误状态
        """
        self._isError = isError
        if isError:
            self.error()
        else:
            self.resume()

    def isError(self):
        """是否处于错误状态

        Returns:
            是否错误
        """
        return self._isError

    def barColor(self):
        """获取当前条形颜色

        Returns:
            当前主题下的条形颜色
        """
        if self.isPaused():
            return QColor(252, 225, 0) if isDarkTheme() else QColor(157, 93, 0)

        if self.isError():
            return QColor(255, 153, 164) if isDarkTheme() else QColor(196, 43, 28)

        return self.darkBarColor() if isDarkTheme() else self.lightBarColor()

    def valText(self):
        """获取当前值的文本表示

        Returns:
            格式化的进度文本
        """
        if self.maximum() <= self.minimum():
            return ""

        total = self.maximum() - self.minimum()
        result = self.format()
        locale = self.locale()
        locale.setNumberOptions(locale.numberOptions()
                                | QLocale.OmitGroupSeparator)
        result = result.replace("%m", locale.toString(total))
        result = result.replace("%v", locale.toString(self.val))

        if total == 0:
            return result.replace("%p", locale.toString(100))

        progress = int((self.val - self.minimum()) * 100 / total)
        return result.replace("%p", locale.toString(progress))

    def paintEvent(self, e):
        """绘制进度条

        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制背景
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        painter.setPen(bc)
        y =  floor(self.height() / 2)
        painter.drawLine(0, y, self.width(), y)

        if self.minimum() >= self.maximum():
            return

        # 绘制栏
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.barColor())
        w = int(self.val / (self.maximum() - self.minimum()) * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(0, 0, w, self.height(), r, r)

    useAni = Property(bool, isUseAni, setUseAni)
    val = Property(float, getVal, setVal)


class IndeterminateProgressBar(QProgressBar):
    """用于展示未知完成度的循环动画进度条控件
    
    适用于无法预估剩余时间或完成比例的场景，例如网络请求等待、后台同步或数据库查询，通过无限循环动画提示用户当前正处于处理中
    """

    def __init__(self, parent=None, start=True):
        """初始化不确定进度条

        Args:
            parent: 父窗口，默认为 None
            start: 是否自动开始动画，默认为 True
        """
        super().__init__(parent=parent)
        self._shortPos = 0
        self._longPos = 0
        self.shortBarAni = QPropertyAnimation(self, b'shortPos', self)
        self.longBarAni = QPropertyAnimation(self, b'longPos', self)

        self._lightBarColor = QColor()
        self._darkBarColor = QColor()

        self._isError = False

        self.aniGroup = QParallelAnimationGroup(self)
        self.longBarAniGroup = QSequentialAnimationGroup(self)

        self.shortBarAni.setDuration(833)
        self.longBarAni.setDuration(1167)
        self.shortBarAni.setStartValue(0)
        self.longBarAni.setStartValue(0)
        self.shortBarAni.setEndValue(1.45)
        self.longBarAni.setEndValue(1.75)
        self.longBarAni.setEasingCurve(QEasingCurve.OutQuad)

        self.aniGroup.addAnimation(self.shortBarAni)
        self.longBarAniGroup.addPause(785)
        self.longBarAniGroup.addAnimation(self.longBarAni)
        self.aniGroup.addAnimation(self.longBarAniGroup)
        self.aniGroup.setLoopCount(-1)

        self.setFixedHeight(4)

        if start:
            self.start()

    def lightBarColor(self):
        """获取亮色主题下的条形颜色

        Returns:
            亮色主题条形颜色
        """
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        """获取暗色主题下的条形颜色

        Returns:
            暗色主题条形颜色
        """
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """设置自定义条形颜色

        Args:
            light: 亮色主题下的条形颜色，可为 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的条形颜色，可为 str、Qt.GlobalColor 或 QColor
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    @Property(float)
    def shortPos(self):
        """获取短条位置

        Returns:
            短条当前位置
        """
        return self._shortPos

    @shortPos.setter
    def shortPos(self, p):
        """设置短条位置

        Args:
            p: 位置值
        """
        self._shortPos = p
        self.update()

    @Property(float)
    def longPos(self):
        """获取长条位置

        Returns:
            长条当前位置
        """
        return self._longPos

    @longPos.setter
    def longPos(self, p):
        """设置长条位置

        Args:
            p: 位置值
        """
        self._longPos = p
        self.update()

    def start(self):
        """开始动画"""
        self.shortPos = 0
        self.longPos = 0
        self.aniGroup.start()
        self.update()

    def stop(self):
        """停止动画"""
        self.aniGroup.stop()
        self.shortPos = 0
        self.longPos = 0
        self.update()

    def isStarted(self):
        """动画是否已开始

        Returns:
            动画是否处于运行状态
        """
        return self.aniGroup.state() == QParallelAnimationGroup.Running

    def pause(self):
        """暂停动画"""
        self.aniGroup.pause()
        self.update()

    def resume(self):
        """恢复动画"""
        self.aniGroup.resume()
        self.update()

    def setPaused(self, isPaused: bool):
        """设置动画暂停状态

        Args:
            isPaused: 是否暂停
        """
        self.aniGroup.setPaused(isPaused)
        self.update()

    def isPaused(self):
        """动画是否已暂停

        Returns:
            是否处于暂停状态
        """
        return self.aniGroup.state() == QParallelAnimationGroup.Paused

    def error(self):
        """设置为错误状态并停止动画"""
        self._isError = True
        self.aniGroup.stop()
        self.update()

    def setError(self, isError: bool):
        """设置错误状态

        Args:
            isError: 是否为错误状态
        """
        self._isError = isError
        if isError:
            self.error()
        else:
            self.start()

    def isError(self):
        """是否处于错误状态

        Returns:
            是否错误
        """
        return self._isError

    def barColor(self):
        """获取当前条形颜色

        Returns:
            当前主题下的条形颜色
        """
        if self.isError():
            return QColor(255, 153, 164) if isDarkTheme() else QColor(196, 43, 28)

        if self.isPaused():
            return QColor(252, 225, 0) if isDarkTheme() else QColor(157, 93, 0)

        return self.darkBarColor() if isDarkTheme() else self.lightBarColor()

    def paintEvent(self, e):
        """绘制不确定进度条

        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.barColor())

        # 绘制short 栏
        x = int((self.shortPos - 0.4) * self.width())
        w = int(0.4 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)

        # 绘制long 栏
        x = int((self.longPos - 0.6) * self.width())
        w = int(0.6 * self.width())
        r = self.height() / 2
        painter.drawRoundedRect(x, 0, w, self.height(), r, r)