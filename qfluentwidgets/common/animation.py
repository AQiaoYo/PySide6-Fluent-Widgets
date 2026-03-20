# coding: utf-8
from enum import Enum
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Property, Signal, QPoint, QPointF, QRect, QRectF, QParallelAnimationGroup, QSequentialAnimationGroup, Qt
from PySide6.QtGui import QMouseEvent, QEnterEvent, QColor
from PySide6.QtWidgets import QWidget, QLineEdit, QGraphicsDropShadowEffect

from .config import qconfig


class AnimationBase(QObject):
    """ 动画基类 """

    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        parent.installEventFilter(self)

    def _onHover(self, e: QEnterEvent):
        pass

    def _onLeave(self, e: QEvent):
        pass

    def _onPress(self, e: QMouseEvent):
        pass

    def _onRelease(self, e: QMouseEvent):
        pass

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            if e.type() == QEvent.MouseButtonPress:
                self._onPress(e)
            elif e.type() == QEvent.MouseButtonRelease:
                self._onRelease(e)
            elif e.type() == QEvent.Enter:
                self._onHover(e)
            elif e.type() == QEvent.Leave:
                self._onLeave(e)

        return super().eventFilter(obj, e)


class TranslateYAnimation(AnimationBase):
    """Y 轴位移动画."""

    valueChanged = Signal(float)

    def __init__(self, parent: QWidget, offset=2):
        super().__init__(parent)
        self._y = 0
        self.maxOffset = offset
        self.ani = QPropertyAnimation(self, b'y', self)

    def getY(self):
        return self._y

    def setY(self, y):
        self._y = y
        self.parent().update()
        self.valueChanged.emit(y)

    def _onPress(self, e):
        """ 向下位移 """
        self.ani.setEndValue(self.maxOffset)
        self.ani.setEasingCurve(QEasingCurve.OutQuad)
        self.ani.setDuration(150)
        self.ani.start()

    def _onRelease(self, e):
        """回到初始位置."""
        self.ani.setEndValue(0)
        self.ani.setDuration(500)
        self.ani.setEasingCurve(QEasingCurve.OutElastic)
        self.ani.start()

    y = Property(float, getY, setY)



class BackgroundAnimationWidget:
    """ 带背景动画的部件 """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.isHover = False
        self.isPressed = False
        self.bgColorObject = BackgroundColorObject(self)
        self.backgroundColorAni = QPropertyAnimation(
            self.bgColorObject, b'backgroundColor', self)
        self.backgroundColorAni.setDuration(120)
        self.installEventFilter(self)

        qconfig.themeChanged.connect(self._updateBackgroundColor)

    def eventFilter(self, obj, e):
        if obj is self:
            if e.type() == QEvent.Type.EnabledChange:
                if self.isEnabled():
                    self.setBackgroundColor(self._normalBackgroundColor())
                else:
                    self.setBackgroundColor(self._disabledBackgroundColor())

        return super().eventFilter(obj, e)

    def mousePressEvent(self, e):
        self.isPressed = True
        self._updateBackgroundColor()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self._updateBackgroundColor()
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self._updateBackgroundColor()

    def leaveEvent(self, e):
        self.isHover = False
        self._updateBackgroundColor()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._updateBackgroundColor()

    def _normalBackgroundColor(self):
        return QColor(0, 0, 0, 0)

    def _hoverBackgroundColor(self):
        return self._normalBackgroundColor()

    def _pressedBackgroundColor(self):
        return self._normalBackgroundColor()

    def _focusInBackgroundColor(self):
        return self._normalBackgroundColor()

    def _disabledBackgroundColor(self):
        return self._normalBackgroundColor()

    def _updateBackgroundColor(self):
        if not self.isEnabled():
            color = self._disabledBackgroundColor()
        elif isinstance(self, QLineEdit) and self.hasFocus():
            color = self._focusInBackgroundColor()
        elif self.isPressed:
            color = self._pressedBackgroundColor()
        elif self.isHover:
            color = self._hoverBackgroundColor()
        else:
            color = self._normalBackgroundColor()

        self.backgroundColorAni.stop()
        self.backgroundColorAni.setEndValue(color)
        self.backgroundColorAni.start()

    def getBackgroundColor(self):
        return self.bgColorObject.backgroundColor

    def setBackgroundColor(self, color: QColor):
        self.bgColorObject.backgroundColor = color

    @property
    def backgroundColor(self):
        return self.getBackgroundColor()


class BackgroundColorObject(QObject):
    """ 背景色对象 """

    def __init__(self, parent: BackgroundAnimationWidget):
        super().__init__(parent)
        self._backgroundColor = parent._normalBackgroundColor()

    @Property(QColor)
    def backgroundColor(self):
        return self._backgroundColor

    @backgroundColor.setter
    def backgroundColor(self, color: QColor):
        self._backgroundColor = color
        self.parent().update()

class DropShadowAnimation(QPropertyAnimation):
    """ 阴影动画 """

    def __init__(self, parent: QWidget, normalColor=QColor(0, 0, 0, 0), hoverColor=QColor(0, 0, 0, 75)):
        super().__init__(parent=parent)
        self.normalColor = normalColor
        self.hoverColor = hoverColor
        self.offset = QPoint(0, 0)
        self.blurRadius = 38
        self.isHover = False

        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setColor(self.normalColor)

        parent.installEventFilter(self)

    def setBlurRadius(self, radius: int):
        self.blurRadius = radius

    def setOffset(self, dx: int, dy: int):
        self.offset = QPoint(dx, dy)

    def setNormalColor(self, color: QColor):
        self.normalColor = color

    def setHoverColor(self, color: QColor):
        self.hoverColor = color

    def setColor(self, color):
        pass

    def _createShadowEffect(self):
        self.shadowEffect = QGraphicsDropShadowEffect(self)
        self.shadowEffect.setOffset(self.offset)
        self.shadowEffect.setBlurRadius(self.blurRadius)
        self.shadowEffect.setColor(self.normalColor)

        self.setTargetObject(self.shadowEffect)
        self.setStartValue(self.shadowEffect.color())
        self.setPropertyName(b'color')
        self.setDuration(150)

        return self.shadowEffect

    def eventFilter(self, obj, e):
        if obj is self.parent() and self.parent().isEnabled():
            if e.type() in [QEvent.Type.Enter]:
                self.isHover = True

                if self.state() != QPropertyAnimation.State.Running:
                    self.parent().setGraphicsEffect(self._createShadowEffect())

                self.setEndValue(self.hoverColor)
                self.start()
            elif e.type() in [QEvent.Type.Leave, QEvent.Type.MouseButtonPress]:
                self.isHover = False
                if self.parent().graphicsEffect():
                    self.finished.connect(self._onAniFinished)
                    self.setEndValue(self.normalColor)
                    self.start()

        return super().eventFilter(obj, e)

    def _onAniFinished(self):
        self.finished.disconnect()
        self.shadowEffect = None
        self.parent().setGraphicsEffect(None)


class FluentAnimationSpeed(Enum):
    """Fluent 动画速度."""
    FAST = 0
    MEDIUM = 1
    SLOW = 2


class FluentAnimationType(Enum):
    """Fluent 动画类型."""
    FAST_INVOKE = 0
    STRONG_INVOKE = 1
    FAST_DISMISS = 2
    SOFT_DISMISS = 3
    POINT_TO_POINT = 4
    FADE_IN_OUT = 5


class FluentAnimationProperty(Enum):
    """Fluent 动画属性."""
    POSITION = "position"
    SCALE = "scale"
    ANGLE = "angle"
    OPACITY = "opacity"



class FluentAnimationProperObject(QObject):
    """Fluent 动画属性对象."""

    objects = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def getValue(self):
        return 0

    def setValue(self):
        pass

    @classmethod
    def register(cls, name):
        """注册动画属性对象.

        参数
        ----------
        name: Any
            属性对象名称,必须唯一.
        """
        def wrapper(Manager):
            if name not in cls.objects:
                cls.objects[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def create(cls, propertyType: FluentAnimationProperty, parent=None) -> 'FluentAnimationProperObject':
        if propertyType not in cls.objects:
            raise ValueError(f"`{propertyType}` has not been registered")

        return cls.objects[propertyType](parent)


@FluentAnimationProperObject.register(FluentAnimationProperty.POSITION)
class PositionObject(FluentAnimationProperObject):
    """ 位置 对象 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._position = QPoint()

    def getValue(self):
        return self._position

    def setValue(self, pos: QPoint):
        self._position = pos
        self.parent().update()

    position = Property(QPoint, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.SCALE)
class ScaleObject(FluentAnimationProperObject):
    """缩放对象."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1

    def getValue(self):
        return self._scale

    def setValue(self, scale: float):
        self._scale = scale
        self.parent().update()

    scale = Property(float, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.ANGLE)
class AngleObject(FluentAnimationProperObject):
    """角度对象."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0

    def getValue(self):
        return self._angle

    def setValue(self, angle: float):
        self._angle = angle
        self.parent().update()

    angle = Property(float, getValue, setValue)


@FluentAnimationProperObject.register(FluentAnimationProperty.OPACITY)
class OpacityObject(FluentAnimationProperObject):
    """透明度对象."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 0

    def getValue(self):
        return self._opacity

    def setValue(self, opacity: float):
        self._opacity = opacity
        self.parent().update()

    opacity = Property(float, getValue, setValue)


class FluentAnimation(QPropertyAnimation):
    """Fluent 动画基类."""

    animations = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSpeed(FluentAnimationSpeed.FAST)
        self.setEasingCurve(self.curve())

    @classmethod
    def createBezierCurve(cls, x1, y1, x2, y2):
        curve = QEasingCurve(QEasingCurve.BezierSpline)
        curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))
        return curve

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0, 0, 1, 1)

    def setSpeed(self, speed: FluentAnimationSpeed):
        """设置动画速度."""
        self.setDuration(self.speedToDuration(speed))

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 100

    def startAnimation(self, endValue, startValue=None):
        self.stop()

        if startValue is None:
            self.setStartValue(self.value())
        else:
            self.setStartValue(startValue)

        self.setEndValue(endValue)
        self.start()

    def value(self):
        return self.targetObject().getValue()

    def setValue(self, value):
        self.targetObject().setValue(value)

    @classmethod
    def register(cls, name):
        """注册动画管理器.

        参数
        ----------
        name: Any
            动画类型名称,必须唯一.
        """
        def wrapper(Manager):
            if name not in cls.animations:
                cls.animations[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def create(cls, aniType: FluentAnimationType, propertyType: FluentAnimationProperty,
               speed=FluentAnimationSpeed.FAST, value=None, parent=None) -> "FluentAnimation":
        if aniType not in cls.animations:
            raise ValueError(f"`{aniType}` has not been registered.")

        obj = FluentAnimationProperObject.create(propertyType, parent)
        ani = cls.animations[aniType](parent)

        ani.setSpeed(speed)
        ani.setTargetObject(obj)
        ani.setPropertyName(propertyType.value.encode())

        if value is not None:
            ani.setValue(value)

        return ani


@FluentAnimation.register(FluentAnimationType.FAST_INVOKE)
class FastInvokeAnimation(FluentAnimation):
    """快速调用动画."""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0, 0, 0, 1)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        if speed == FluentAnimationSpeed.FAST:
            return 187
        if speed == FluentAnimationSpeed.MEDIUM:
            return 333

        return 500


@FluentAnimation.register(FluentAnimationType.STRONG_INVOKE)
class StrongInvokeAnimation(FluentAnimation):
    """强调用动画."""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.13, 1.62, 0, 0.92)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 667


@FluentAnimation.register(FluentAnimationType.FAST_DISMISS)
class FastDismissAnimation(FastInvokeAnimation):
    """快速消失动画."""


@FluentAnimation.register(FluentAnimationType.SOFT_DISMISS)
class SoftDismissAnimation(FluentAnimation):
    """柔和消失动画."""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(1, 0, 1, 1)

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 167


@FluentAnimation.register(FluentAnimationType.POINT_TO_POINT)
class PointToPointAnimation(FastDismissAnimation):
    """点到点动画."""

    @classmethod
    def curve(cls):
        return cls.createBezierCurve(0.55, 0.55, 0, 1)


@FluentAnimation.register(FluentAnimationType.FADE_IN_OUT)
class FadeInOutAnimation(FluentAnimation):
    """淡入淡出动画."""

    def speedToDuration(self, speed: FluentAnimationSpeed):
        return 83



class ScaleSlideAnimation(QObject):
    """缩放与滑移动画."""

    valueChanged = Signal(QRectF)
    finished = Signal()

    def __init__(self, parent=None, orient=Qt.Orientation.Horizontal):
        super().__init__(parent)
        self.orient = orient
        self._geometry = QRectF(0, 0, 16, 3) if self.isHorizontal() else QRectF(0, 0, 3, 16)

        self.slideAniGroup = QParallelAnimationGroup(self)
        self.crossAniGroup = QParallelAnimationGroup(self)
        self.currentAni = self.slideAniGroup

        self.slidePosAni1 = QPropertyAnimation(self, b"pos", self)
        self.slidePosAni2 = QPropertyAnimation(self, b"pos", self)
        self.slideLengthAni1 = QPropertyAnimation(self, b"length", self)
        self.slideLengthAni2 = QPropertyAnimation(self, b"length", self)
        self.seqSlidePosAniGroup = QSequentialAnimationGroup(self)
        self.seqLengthAniGroup = QSequentialAnimationGroup(self)

        self.crossLenAni = QPropertyAnimation(self, b"length", self)
        self.crossPosAni = QPropertyAnimation(self, b"pos", self)

        self.seqSlidePosAniGroup.addAnimation(self.slidePosAni1)
        self.seqSlidePosAniGroup.addAnimation(self.slidePosAni2)
        self.seqLengthAniGroup.addAnimation(self.slideLengthAni1)
        self.seqLengthAniGroup.addAnimation(self.slideLengthAni2)
        self.slideAniGroup.addAnimation(self.seqSlidePosAniGroup)
        self.slideAniGroup.addAnimation(self.seqLengthAniGroup)

        self.crossAniGroup.addAnimation(self.crossLenAni)
        self.crossAniGroup.addAnimation(self.crossPosAni)

        self.slideAniGroup.finished.connect(self.finished)
        self.crossAniGroup.finished.connect(self.finished)

    def startAnimation(self, endRect: QRectF, useCrossFade=False):
        self.stopAnimation()

        startRect = QRectF(self.geometry)

        # 判断新旧指示器是否位于同一层级.
        if self.isHorizontal():
            sameLevel = abs(startRect.y() - endRect.y()) < 1
            dim = startRect.width()
            start = startRect.x()
            end = endRect.x()
        else:
            sameLevel = abs(startRect.x() - endRect.x()) < 1
            dim = startRect.height()
            start = startRect.y()
            end = endRect.y()

        if sameLevel and not useCrossFade:
            self._startSlideAnimation(startRect, endRect, start, end, dim)
        else:
            self._startCrossFadeAnimation(startRect, endRect)

    def stopAnimation(self):
        self.slideAniGroup.stop()
        self.crossAniGroup.stop()

    def _startSlideAnimation(self, startRect, endRect, from_, to, dimension):
        """使用 WinUI 3 的拉伸逻辑为指示器执行滑移动画."""
        self.currentAni = self.slideAniGroup
        self.slidePosAni1.setDuration(200)
        self.slidePosAni2.setDuration(400)
        self.slidePosAni1.setEasingCurve(FluentAnimation.createBezierCurve(0.9, 0.1, 1, 0.2))
        self.slidePosAni2.setEasingCurve(FluentAnimation.createBezierCurve(0.1, 0.9, 0.2, 1.0))

        self.slideLengthAni1.setDuration(200)
        self.slideLengthAni2.setDuration(400)
        self.slideLengthAni1.setEasingCurve(FluentAnimation.createBezierCurve(0.9, 0.1, 1, 0.2))
        self.slideLengthAni2.setEasingCurve(FluentAnimation.createBezierCurve(0.1, 0.9, 0.2, 1.0))

        dist = abs(to - from_)
        midLength = dist + dimension
        isForward = to > from_

        startPos = startRect.topLeft()
        endPos = endRect.topLeft()

        if isForward:
            # 前进方向:先拉长,再把起点移动到目标位置.
            self.slidePosAni1.setStartValue(startPos)
            self.slidePosAni1.setEndValue(startPos)
            self.slideLengthAni1.setStartValue(dimension)
            self.slideLengthAni1.setEndValue(midLength)

            self.slidePosAni2.setStartValue(startPos)
            self.slidePosAni2.setEndValue(endPos)
            self.slideLengthAni2.setStartValue(midLength)
            self.slideLengthAni2.setEndValue(dimension)
        else:
            # 后退方向:先向前扩展到中间态,再收缩回目标长度.
            self.slidePosAni1.setStartValue(startPos)
            self.slidePosAni1.setEndValue(endPos)
            self.slideLengthAni1.setStartValue(dimension)
            self.slideLengthAni1.setEndValue(midLength)

            self.slidePosAni2.setStartValue(endPos)
            self.slidePosAni2.setEndValue(endPos)
            self.slideLengthAni2.setStartValue(midLength)
            self.slideLengthAni2.setEndValue(dimension)

        self.slideAniGroup.start()

    def _startCrossFadeAnimation(self, startRect, endRect):
        self.currentAni = self.crossAniGroup
        self.setGeometry(endRect)

        # 根据相对位置判断扩张方向,保持与 WinUI 3 一致的生长效果.
        isNextBelow = endRect.y() > startRect.y() if not self.isHorizontal() else endRect.x() > startRect.x()

        if self.isHorizontal():
            dim = endRect.width()
            startGeo = QRectF(
                endRect.x() + (0 if isNextBelow else dim), endRect.y(), 0, endRect.height())
        else:
            dim = endRect.height()
            startGeo = QRectF(endRect.x(), endRect.y() +
                              (0 if isNextBelow else dim), endRect.width(), 0)

        self.setGeometry(startGeo)

        self.crossLenAni.setDuration(600)
        self.crossLenAni.setStartValue(0)
        self.crossLenAni.setEndValue(dim)
        self.crossLenAni.setEasingCurve(QEasingCurve.OutQuint)

        self.crossPosAni.setDuration(600)
        self.crossPosAni.setStartValue(startGeo.topLeft())
        self.crossPosAni.setEndValue(endRect.topLeft())
        self.crossPosAni.setEasingCurve(QEasingCurve.OutQuint)

        self.crossAniGroup.start()

    def stop(self):
        self.stopAnimation()

    def state(self):
        return self.currentAni.state()

    def isHorizontal(self):
        return self.orient == Qt.Orientation.Horizontal

    def getPos(self):
        return QPointF(self.geometry.topLeft())

    def setPos(self, pos: QPointF):
        self._geometry.moveTopLeft(pos)
        self.valueChanged.emit(self.geometry)

    def getLength(self):
        return self.geometry.width() if self.isHorizontal() else self.geometry.height()

    def setLength(self, length):
        if self.isHorizontal():
            self._geometry.setWidth(length)
        else:
            self._geometry.setHeight(length)

        self.valueChanged.emit(self.geometry)

    def getGeometry(self) -> QRectF:
        return self._geometry

    def setGeometry(self, rect: QRectF):
        self._geometry = rect

    def moveLeft(self, x):
        self._geometry.moveLeft(x)
        self.valueChanged.emit(self.geometry)

    def setValue(self, rect):
        self.setGeometry(rect)

    pos = Property(QPointF, getPos, setPos)
    length = Property(float, getLength, setLength)
    geometry = Property(QRectF, getGeometry, setGeometry)
