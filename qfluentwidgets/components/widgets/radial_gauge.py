# coding: utf-8
"""径向仪表盘控件模块
提供 RadialGauge 控件，用于显示速度、进度或其他可以用角度表示的度量
"""

from PySide6.QtCore import Qt, QRectF, Property, QSize
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen

from .progress_bar import ProgressBar
from ...common.font import setFont
from ...common.style_sheet import isDarkTheme


class RadialGauge(ProgressBar):
    """径向仪表盘
    可以用来显示一系列的数据，比如速度、进度或者其他可以用角度来表示的度量
    """

    def __init__(self, parent=None, useAni=True):
        """构造函数

        Args:
            parent: 父级控件
            useAni: 是否使用动画
        """
        super().__init__(parent, useAni=useAni)
        self.lightBackgroundColor = QColor(0, 0, 0, 34)
        self.darkBackgroundColor = QColor(255, 255, 255, 34)
        self._strokeWidth = 16
        self._strokeScaleFactor = 0.1
        self._startAngle = 225
        self._spanAngle = -270
        self._capStyle = Qt.RoundCap
        self._trackVisible = True
        self._autoTextSize = True
        self._textScaleFactor = 0.18
        self._minTextSize = 10
        self._maxTextSize = 28

        self.setTextVisible(True)
        self.setFixedSize(160, 160)
        setFont(self, 28)

    def sizeHint(self):
        return QSize(160, 160)

    def getStrokeWidth(self):
        """获取描边宽度

        Returns:
            描边宽度
        """
        return self._strokeWidth

    def setStrokeWidth(self, w: int):
        """设置描边宽度

        Args:
            w: 描边宽度
        """
        self._strokeWidth = max(1, int(w))
        self.update()

    def getStrokeScaleFactor(self):
        return self._strokeScaleFactor

    def setStrokeScaleFactor(self, factor: float):
        self._strokeScaleFactor = max(0.01, float(factor))
        self._strokeWidth = max(1, round(min(self.width(), self.height()) * self._strokeScaleFactor))
        self.update()

    def thickness(self):
        return self.getStrokeWidth()

    def setThickness(self, w: int):
        self.setStrokeWidth(w)

    def thicknessRatio(self):
        return self.getStrokeScaleFactor()

    def setThicknessRatio(self, ratio: float):
        self.setStrokeScaleFactor(ratio)

    def getStartAngle(self):
        """获取起始角度

        Returns:
            起始角度
        """
        return self._startAngle

    def setStartAngle(self, angle: int):
        """设置起始角度

        Args:
            angle: 起始角度
        """
        self._startAngle = int(angle)
        self.update()

    def getSpanAngle(self):
        """获取跨度角度

        Returns:
            跨度角度
        """
        return self._spanAngle

    def setSpanAngle(self, angle: int):
        """设置跨度角度

        Args:
            angle: 跨度角度
        """
        self._spanAngle = int(angle)
        self.update()

    def setArcRange(self, startAngle: int, spanAngle: int):
        self._startAngle = int(startAngle)
        self._spanAngle = int(spanAngle)
        self.update()

    def capStyle(self):
        return self._capStyle

    def setCapStyle(self, style):
        self._capStyle = style
        self.update()

    def isTrackVisible(self):
        return self._trackVisible

    def setTrackVisible(self, visible: bool):
        self._trackVisible = bool(visible)
        self.update()

    def setTrackColor(self, light, dark):
        self.setCustomBackgroundColor(light, dark)

    def setProgressColor(self, light, dark):
        self.setCustomBarColor(light, dark)

    def setGaugeColor(self, progressLight, progressDark, trackLight=None, trackDark=None):
        self.setProgressColor(progressLight, progressDark)
        if trackLight is not None and trackDark is not None:
            self.setTrackColor(trackLight, trackDark)

    def setGaugeStyle(
        self,
        thickness: int = None,
        thicknessRatio: float = None,
        startAngle: int = None,
        spanAngle: int = None,
        capStyle=None,
        trackVisible: bool = None,
    ):
        if thicknessRatio is not None:
            self.setThicknessRatio(thicknessRatio)

        if thickness is not None:
            self.setThickness(thickness)

        if startAngle is not None:
            self._startAngle = int(startAngle)

        if spanAngle is not None:
            self._spanAngle = int(spanAngle)

        if capStyle is not None:
            self._capStyle = capStyle

        if trackVisible is not None:
            self._trackVisible = bool(trackVisible)

        self.update()

    def isAutoTextSize(self):
        return self._autoTextSize

    def setAutoTextSize(self, isAuto: bool):
        self._autoTextSize = bool(isAuto)
        self.update()

    def getTextScaleFactor(self):
        return self._textScaleFactor

    def setTextScaleFactor(self, factor: float):
        self._textScaleFactor = max(0.01, float(factor))
        self.update()

    def textSizeRange(self):
        return self._minTextSize, self._maxTextSize

    def setTextSizeRange(self, minimum: int, maximum: int):
        minimum = max(1, int(minimum))
        maximum = max(minimum, int(maximum))
        self._minTextSize = minimum
        self._maxTextSize = maximum
        self.update()

    def setGaugeSize(self, size: int, strokeWidth: int = None):
        size = max(1, int(size))
        self.setFixedSize(size, size)
        self.setStrokeWidth(
            strokeWidth if strokeWidth is not None else round(size * self._strokeScaleFactor)
        )

    def _autoFont(self, text: str):
        font = self.font()
        side = min(self.width(), self.height())
        targetSize = int(side * self._textScaleFactor)
        targetSize = max(self._minTextSize, min(self._maxTextSize, targetSize))

        available = max(1, side - self._strokeWidth * 2 - 12)
        for size in range(targetSize, self._minTextSize - 1, -1):
            font.setPixelSize(size)
            fm = QFontMetrics(font)
            if fm.horizontalAdvance(text) <= available and fm.height() <= available:
                return font

        font.setPixelSize(self._minTextSize)
        return font

    def _drawText(self, painter: QPainter, text: str):
        """绘制文本

        Args:
            painter: 绘制器
            text: 文本内容
        """
        painter.setFont(self._autoFont(text) if self._autoTextSize else self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def paintEvent(self, e):
        """绘制径向仪表盘

        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        side = min(self.width(), self.height()) - cw
        if side <= 0:
            return

        rc = QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2,
            side,
            side,
        )

        bc = self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor
        pen = QPen(bc, cw, Qt.SolidLine, self._capStyle, Qt.RoundJoin)
        if self._trackVisible:
            painter.setPen(pen)
            painter.drawArc(rc, self._startAngle * 16, self._spanAngle * 16)

        total = self.maximum() - self.minimum()
        if total > 0:
            ratio = (self.val - self.minimum()) / total
            ratio = max(0, min(1, ratio))
            span = int(self._spanAngle * ratio)
            if span:
                pen.setColor(self.barColor())
                painter.setPen(pen)
                painter.drawArc(rc, self._startAngle * 16, span * 16)

        if self.isTextVisible():
            self._drawText(painter, self.valText())

    strokeWidth = Property(int, getStrokeWidth, setStrokeWidth)
    strokeScaleFactor = Property(float, getStrokeScaleFactor, setStrokeScaleFactor)
    thickness = Property(int, thickness, setThickness)
    thicknessRatio = Property(float, thicknessRatio, setThicknessRatio)
    startAngle = Property(int, getStartAngle, setStartAngle)
    spanAngle = Property(int, getSpanAngle, setSpanAngle)
    capStyle = Property(Qt.PenCapStyle, capStyle, setCapStyle)
    trackVisible = Property(bool, isTrackVisible, setTrackVisible)
    autoTextSize = Property(bool, isAutoTextSize, setAutoTextSize)
    textScaleFactor = Property(float, getTextScaleFactor, setTextScaleFactor)
