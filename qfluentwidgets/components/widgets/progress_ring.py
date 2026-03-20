# coding: utf-8
from PySide6.QtCore import (Qt, QRectF, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup,
                          QSequentialAnimationGroup, Property)
from PySide6.QtGui import QColor, QPen, QPainter, QFont
from PySide6.QtWidgets import QProgressBar

from .progress_bar import ProgressBar
from ...common.font import setFont
from ...common.style_sheet import themeColor, isDarkTheme


class ProgressRing(ProgressBar):
    """ 进度环 """

    def __init__(self, parent=None, useAni=True):
        super().__init__(parent, useAni=useAni)
        self.lightBackgroundColor = QColor(0, 0, 0, 34)
        self.darkBackgroundColor = QColor(255, 255, 255, 34)
        self._strokeWidth = 6

        self.setTextVisible(False)
        self.setFixedSize(100, 100)
        setFont(self)

    def getStrokeWidth(self):
        return self._strokeWidth

    def setStrokeWidth(self, w: int):
        self._strokeWidth = w
        self.update()

    def _drawText(self, painter: QPainter, text: str):
        """ 绘制文本 """
        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth    # circle thickness
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw/2, self.height()/2 - w/2, w, w)

        # 绘制背景
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360*16)

        if self.maximum() <= self.minimum():
            return

        # 绘制栏
        pen.setColor(self.barColor())
        painter.setPen(pen)
        degree = int(self.val / (self.maximum() - self.minimum()) * 360)
        painter.drawArc(rc, 90*16, -degree*16)

        # 绘制文本
        if self.isTextVisible():
            self._drawText(painter, self.valText())

    strokeWidth = Property(int, getStrokeWidth, setStrokeWidth)


class IndeterminateProgressRing(QProgressBar):
    """ Indeterminate 进度环 """

    def __init__(self, parent=None, start=True):
        super().__init__(parent=parent)
        self.lightBackgroundColor = QColor(0, 0, 0, 0)
        self.darkBackgroundColor = QColor(255, 255, 255, 0)
        self._lightBarColor = QColor()
        self._darkBarColor = QColor()
        self._strokeWidth = 6

        self._startAngle = -180
        self._spanAngle = 0

        self.startAngleAni1 = QPropertyAnimation(self, b'startAngle', self)
        self.startAngleAni2 = QPropertyAnimation(self, b'startAngle', self)
        self.spanAngleAni1 = QPropertyAnimation(self, b'spanAngle', self)
        self.spanAngleAni2 = QPropertyAnimation(self, b'spanAngle', self)

        self.startAngleAniGroup = QSequentialAnimationGroup(self)
        self.spanAngleAniGroup = QSequentialAnimationGroup(self)
        self.aniGroup = QParallelAnimationGroup(self)

        # 初始化开始 angle 动画
        self.startAngleAni1.setDuration(1000)
        self.startAngleAni1.setStartValue(0)
        self.startAngleAni1.setEndValue(450)

        self.startAngleAni2.setDuration(1000)
        self.startAngleAni2.setStartValue(450)
        self.startAngleAni2.setEndValue(1080)

        self.startAngleAniGroup.addAnimation(self.startAngleAni1)
        self.startAngleAniGroup.addAnimation(self.startAngleAni2)

        # 初始化span angle 动画
        self.spanAngleAni1.setDuration(1000)
        self.spanAngleAni1.setStartValue(0)
        self.spanAngleAni1.setEndValue(180)

        self.spanAngleAni2.setDuration(1000)
        self.spanAngleAni2.setStartValue(180)
        self.spanAngleAni2.setEndValue(0)

        self.spanAngleAniGroup.addAnimation(self.spanAngleAni1)
        self.spanAngleAniGroup.addAnimation(self.spanAngleAni2)

        self.aniGroup.addAnimation(self.startAngleAniGroup)
        self.aniGroup.addAnimation(self.spanAngleAniGroup)
        self.aniGroup.setLoopCount(-1)

        self.setFixedSize(80, 80)

        if start:
            self.start()

    @Property(int)
    def startAngle(self):
        return self._startAngle

    @startAngle.setter
    def startAngle(self, angle: int):
        self._startAngle = angle
        self.update()

    @Property(int)
    def spanAngle(self):
        return self._spanAngle

    @spanAngle.setter
    def spanAngle(self, angle: int):
        self._spanAngle = angle
        self.update()

    def getStrokeWidth(self):
        return self._strokeWidth

    def setStrokeWidth(self, w: int):
        self._strokeWidth = w
        self.update()

    def start(self):
        """ 开始spin """
        self._startAngle = 0
        self._spanAngle = 0
        self.aniGroup.start()

    def stop(self):
        """ 停止spin """
        self.aniGroup.stop()
        self.startAngle = 0
        self.spanAngle = 0

    def lightBarColor(self):
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """ 设置 自定义 条颜色

        参数
        ----------
        亮色, dark: str | Qt.GlobalColor | QColor
            条颜色 中的 亮色/暗色主题模式
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    def setCustomBackgroundColor(self, light, dark):
        """ 设置 自定义 背景色

        参数
        ----------
        亮色, dark: str | Qt.GlobalColor | QColor
            背景色 中的 亮色/暗色主题模式
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        w = min(self.height(), self.width()) - cw
        rc = QRectF(cw/2, self.height()/2 - w/2, w, w)

        # 绘制背景
        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawArc(rc, 0, 360*16)

        # 绘制栏
        pen.setColor(self.darkBarColor() if isDarkTheme() else self.lightBarColor())
        painter.setPen(pen)

        startAngle = -self.startAngle + 180
        painter.drawArc(rc, (startAngle % 360)*16, -self.spanAngle*16)

    strokeWidth = Property(int, getStrokeWidth, setStrokeWidth)