# coding: utf-8
"""进度环控件模块
提供 ProgressRing, MultiSegmentProgressRing 和 IndeterminateProgressRing 等环形进度控件, 适用于在紧凑布局中展示任务执行状态
ProgressRing 用于显示可量化的完成百分比, MultiSegmentProgressRing 用于展示存储空间等分段状态, IndeterminateProgressRing 则用于表示正在进行但无法预估剩余时间的后台操作
"""

from typing import Iterable, Tuple, Union

from PySide6.QtCore import (Qt, QRectF, QSize, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup,
                           QSequentialAnimationGroup, Property)
from PySide6.QtGui import QColor, QFontMetrics, QPen, QPainter, QFont
from PySide6.QtWidgets import QProgressBar

from .progress_bar import ProgressBar
from ...common.font import setFont
from ...common.style_sheet import themeColor, isDarkTheme


class ProgressRing(ProgressBar):
    """确定进度的环形进度条
    以环形弧线长度直观展示当前任务完成百分比，相比传统水平进度条更节省横向空间，适合嵌入在按钮、列表项或弹窗中展示可量化的执行进度
    支持通过数值接口实时更新进度，并可调整线宽与方向以适配不同尺寸的界面布局
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
        self._strokeWidth = 6

        self.setTextVisible(False)
        self.setFixedSize(100, 100)
        setFont(self)

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
        self._strokeWidth = w
        self.update()

    def _drawText(self, painter: QPainter, text: str):
        """绘制文本

        Args:
            painter: 绘制器
            text: 文本内容
        """
        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def paintEvent(self, e):
        """绘制进度环

        Args:
            e: 绘制事件
        """
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


class MultiSegmentProgressRing(ProgressRing):
    """分段环形进度条
    以多个连续弧段展示不同类别的进度占比, 适用于存储空间可视化, 资源配额, 多阶段任务完成度等场景.
    每个分段可以设置独立的亮色和暗色主题颜色, 未被分段占用的部分会显示为轨道背景.

    Constructor overloads:
        * MultiSegmentProgressRing(parent: QWidget = None, useAni: bool = True)
    """

    Segment = Tuple[float, QColor, QColor]

    def __init__(self, parent=None, useAni=True):
        """初始化分段环形进度条

        Args:
            parent: 父级控件.
            useAni: 是否使用继承自 ProgressBar 的数值动画.
        """
        super().__init__(parent, useAni=useAni)
        self._segments = []
        self._gapAngle = 4
        self._startAngle = 90
        self._clockwise = True
        self._capStyle = Qt.RoundCap
        self._centerText = ""
        self._trackVisible = True
        self._minSegmentAngle = 0.5

    def segments(self):
        """获取当前分段数据

        Returns:
            分段数据副本, 每项为 (value, lightColor, darkColor).
        """
        return [(value, QColor(light), QColor(dark)) for value, light, dark in self._segments]

    def setSegments(self, segments: Iterable[Union[Tuple[float, Union[str, QColor, Qt.GlobalColor]], Tuple[float, Union[str, QColor, Qt.GlobalColor], Union[str, QColor, Qt.GlobalColor]]]]):
        """设置全部分段

        Args:
            segments: 分段列表, 支持 (value, color) 或 (value, lightColor, darkColor).
        """
        self._segments = [self._normalizeSegment(segment) for segment in segments]
        self._syncValueWithSegments()
        self.update()

    def addSegment(self, value: float, lightColor, darkColor=None):
        """添加一个分段

        Args:
            value: 分段数值.
            lightColor: 亮色主题下的分段颜色, darkColor 为空时同时作为暗色主题颜色.
            darkColor: 暗色主题下的分段颜色, 默认为 None.
        """
        self._segments.append(self._normalizeSegment((value, lightColor, darkColor or lightColor)))
        self._syncValueWithSegments()
        self.update()

    def insertSegment(self, index: int, value: float, lightColor, darkColor=None):
        """在指定位置插入一个分段

        Args:
            index: 插入位置, 负数从末尾计数.
            value: 分段数值.
            lightColor: 亮色主题下的分段颜色.
            darkColor: 暗色主题下的分段颜色, 默认为 None.
        """
        self._segments.insert(index, self._normalizeSegment((value, lightColor, darkColor or lightColor)))
        self._syncValueWithSegments()
        self.update()

    def removeSegment(self, index: int):
        """删除指定索引的分段

        Args:
            index: 要删除的分段索引.
        """
        if -len(self._segments) <= index < len(self._segments):
            del self._segments[index]
            self._syncValueWithSegments()
            self.update()

    def clearSegments(self):
        """清空所有分段"""
        self._segments.clear()
        self.setValue(self.minimum())
        self.update()

    def segmentCount(self):
        """获取分段数量

        Returns:
            当前分段总数.
        """
        return len(self._segments)

    def segmentAt(self, index: int):
        """获取指定索引的分段副本

        Args:
            index: 分段索引.

        Returns:
            (value, lightColor, darkColor) 形式的分段副本.
        """
        value, lightColor, darkColor = self._segments[index]
        return value, QColor(lightColor), QColor(darkColor)

    def setSegmentValue(self, index: int, value: float):
        """修改指定分段的数值

        Args:
            index: 分段索引.
            value: 新的分段数值.
        """
        _, lightColor, darkColor = self._segments[index]
        self._segments[index] = (max(0, float(value)), lightColor, darkColor)
        self._syncValueWithSegments()
        self.update()

    def setSegmentColor(self, index: int, lightColor, darkColor=None):
        """修改指定分段的颜色

        Args:
            index: 分段索引.
            lightColor: 亮色主题颜色.
            darkColor: 暗色主题颜色, 默认与 lightColor 相同.
        """
        value, _, _ = self._segments[index]
        self._segments[index] = (
            value,
            QColor(lightColor),
            QColor(darkColor if darkColor is not None else lightColor),
        )
        self.update()

    def totalValue(self):
        """获取所有分段的数值之和

        Returns:
            所有分段的数值之和.
        """
        return sum(value for value, _, _ in self._segments)

    def _normalizeSegment(self, segment):
        """标准化分段数据

        Args:
            segment: 原始分段数据.
        """
        if len(segment) == 2:
            value, color = segment
            lightColor = darkColor = color
        elif len(segment) == 3:
            value, lightColor, darkColor = segment
        else:
            raise ValueError("segment must be (value, color) or (value, lightColor, darkColor)")

        return max(0, float(value)), QColor(lightColor), QColor(darkColor)

    def _syncValueWithSegments(self):
        """将进度值同步为分段数值总和"""
        total = sum(value for value, _, _ in self._segments)
        value = min(self.maximum(), self.minimum() + int(round(total)))
        super().setValue(value)

    def getGapAngle(self):
        """获取分段间隔角度

        Returns:
            分段间隔角度.
        """
        return self._gapAngle

    def setGapAngle(self, angle: int):
        """设置分段间隔角度

        Args:
            angle: 间隔角度, 单位为度.
        """
        self._gapAngle = max(0, int(angle))
        self.update()

    def getStartAngle(self):
        """获取起始角度

        Returns:
            起始角度.
        """
        return self._startAngle

    def setStartAngle(self, angle: int):
        """设置起始角度

        Args:
            angle: 起始角度, 单位为度.
        """
        self._startAngle = int(angle)
        self.update()

    def isClockwise(self):
        """是否按顺时针方向绘制

        Returns:
            是否顺时针绘制.
        """
        return self._clockwise

    def setClockwise(self, isClockwise: bool):
        """设置绘制方向

        Args:
            isClockwise: 是否顺时针绘制.
        """
        self._clockwise = bool(isClockwise)
        self.update()

    def capStyle(self):
        """获取线帽样式

        Returns:
            线帽样式.
        """
        return self._capStyle

    def setCapStyle(self, style):
        """设置线帽样式

        Args:
            style: Qt.PenCapStyle 线帽样式.
        """
        self._capStyle = style
        self.update()

    def isTrackVisible(self):
        """是否显示背景轨道

        Returns:
            是否显示背景轨道.
        """
        return self._trackVisible

    def setTrackVisible(self, visible: bool):
        """设置是否显示背景轨道

        Args:
            visible: 是否显示轨道, False 时仅绘制分段, 适用于纯分段展示场景.
        """
        self._trackVisible = bool(visible)
        self.update()

    def trackColor(self):
        """获取轨道颜色

        Returns:
            (lightColor, darkColor) 形式的轨道颜色副本.
        """
        return QColor(self.lightBackgroundColor), QColor(self.darkBackgroundColor)

    def setTrackColor(self, light, dark=None):
        """设置轨道颜色

        Args:
            light: 亮色主题下的轨道颜色.
            dark: 暗色主题下的轨道颜色, 默认与 light 相同.
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark if dark is not None else light)
        self.update()

    def getMinSegmentAngle(self):
        """获取分段的最小绘制角度

        Returns:
            最小绘制角度, 决定较小分段是否能以圆点形式可见.
        """
        return self._minSegmentAngle

    def setMinSegmentAngle(self, angle: float):
        """设置分段的最小绘制角度

        Args:
            angle: 最小绘制角度, 单位为度, 取值越小小分段越接近圆点.
        """
        self._minSegmentAngle = max(0.0, float(angle))
        self.update()

    def getCenterText(self):
        """获取中心文本

        Returns:
            中心文本.
        """
        return self._centerText

    def setCenterText(self, text: str):
        """设置中心文本

        Args:
            text: 中心文本, 支持换行.
        """
        self._centerText = str(text)
        self.update()

    def _segmentColor(self, segment: Segment):
        """获取当前主题下的分段颜色

        Args:
            segment: 标准化分段.
        """
        _, lightColor, darkColor = segment
        color = darkColor if isDarkTheme() else lightColor
        fallback = lightColor if lightColor.isValid() else self.barColor()
        return color if color.isValid() else fallback

    def _drawText(self, painter: QPainter, text: str):
        """绘制中心文本

        Args:
            painter: 绘制器.
            text: 文本内容.
        """
        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self._centerText or text)

    def paintEvent(self, e):
        """绘制分段进度环

        Args:
            e: 绘制事件.
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        cw = self._strokeWidth
        side = min(self.height(), self.width()) - cw
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
            painter.drawArc(rc, 0, 360 * 16)

        total = self.maximum() - self.minimum()
        if total > 0:
            angle = float(self._startAngle)
            visibleSegments = [segment for segment in self._segments if segment[0] > 0]

            remaining = total
            for segment in visibleSegments:
                value = min(segment[0], remaining)
                if value <= 0:
                    break

                span = value / total * 360
                gap = min(self._gapAngle, span * 0.45) if len(visibleSegments) > 1 else 0
                drawSpan = max(self._minSegmentAngle, span - gap) if span > 0 else 0

                pen.setColor(self._segmentColor(segment))
                painter.setPen(pen)

                if self._clockwise:
                    painter.drawArc(rc, int(angle * 16), -int(drawSpan * 16))
                    angle -= span
                else:
                    painter.drawArc(rc, int(angle * 16), int(drawSpan * 16))
                    angle += span

                remaining -= value

        if self.isTextVisible():
            self._drawText(painter, self.valText())

    gapAngle = Property(int, getGapAngle, setGapAngle)
    startAngle = Property(int, getStartAngle, setStartAngle)
    clockwise = Property(bool, isClockwise, setClockwise)
    capStyle = Property(Qt.PenCapStyle, capStyle, setCapStyle)
    centerText = Property(str, getCenterText, setCenterText)
    trackVisible = Property(bool, isTrackVisible, setTrackVisible)
    minSegmentAngle = Property(float, getMinSegmentAngle, setMinSegmentAngle)


class IndeterminateProgressRing(QProgressBar):
    """不确定进度的环形进度条
    以循环旋转的动画表示后台任务正在进行，适用于无法预估剩余时间的异步操作（如网络请求、数据查询），避免用户因缺少反馈而重复触发操作
    控件自动播放旋转动画，无需手动更新进度值，可通过控制显隐来提示用户当前操作正在执行
    """

    def __init__(self, parent=None, start=True):
        """构造函数

        Args:
            parent: 父级控件
            start: 是否自动开始动画
        """
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
        """获取起始角度

        Returns:
            起始角度
        """
        return self._startAngle

    @startAngle.setter
    def startAngle(self, angle: int):
        """设置起始角度

        Args:
            angle: 起始角度
        """
        self._startAngle = angle
        self.update()

    @Property(int)
    def spanAngle(self):
        """获取跨度角度

        Returns:
            跨度角度
        """
        return self._spanAngle

    @spanAngle.setter
    def spanAngle(self, angle: int):
        """设置跨度角度

        Args:
            angle: 跨度角度
        """
        self._spanAngle = angle
        self.update()

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
        self._strokeWidth = w
        self.update()

    def start(self):
        """开始动画"""
        self._startAngle = 0
        self._spanAngle = 0
        self.aniGroup.start()

    def stop(self):
        """停止动画"""
        self.aniGroup.stop()
        self.startAngle = 0
        self.spanAngle = 0

    def lightBarColor(self):
        """获取亮色模式下的条颜色

        Returns:
            条颜色
        """
        return self._lightBarColor if self._lightBarColor.isValid() else themeColor()

    def darkBarColor(self):
        """获取暗色模式下的条颜色

        Returns:
            条颜色
        """
        return self._darkBarColor if self._darkBarColor.isValid() else themeColor()

    def setCustomBarColor(self, light, dark):
        """设置自定义条颜色

        Args:
            light (str | Qt.GlobalColor | QColor): 亮色主题下的条颜色
            dark (str | Qt.GlobalColor | QColor): 暗色主题下的条颜色
        """
        self._lightBarColor = QColor(light)
        self._darkBarColor = QColor(dark)
        self.update()

    def setCustomBackgroundColor(self, light, dark):
        """设置自定义背景颜色

        Args:
            light (str | Qt.GlobalColor | QColor): 亮色主题下的背景颜色
            dark (str | Qt.GlobalColor | QColor): 暗色主题下的背景颜色
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        """绘制不确定进度环

        Args:
            e: 绘制事件
        """
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
