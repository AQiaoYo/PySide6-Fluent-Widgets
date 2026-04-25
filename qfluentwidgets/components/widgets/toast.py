# coding: utf-8
"""Toast 浮动通知组件

Toast: 双层卡片叠放样式——后置强调色卡片相对主体卡片上凸 4px，顶部露出带圆角的纯色条纹；
       不自动关闭，只能手动关闭。
ProgressToast: 无顶部外凸条纹，底部进度条（环形 4px 条带）支持倒计时/不确定动画，到时自动关闭。
"""

import weakref
from enum import Enum

from PySide6.QtCore import (
    Qt, QEvent, QObject, QPoint, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup,
    QRectF, QSize, Signal, Property
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QVBoxLayout, QWidget
)

from ...common.auto_wrap import TextWrap
from ...common.icon import isDarkTheme
from ...common.icon import FluentIcon as FIF
from ...common.style_sheet import FluentStyleSheet, themeColor
from .button import TransparentToolButton
from .info_bar import InfoBarPosition


# ---------------------------------------------------------------------------
# Toast 类型枚举
# ---------------------------------------------------------------------------

class ToastType(Enum):
    """Toast 通知类型枚举

    定义 Toast 顶部装饰色条的颜色主题，与通知的语义类型对应。
    """
    INFO = 'Info'
    SUCCESS = 'Success'
    WARNING = 'Warning'
    ERROR = 'Error'
    CUSTOM = 'Custom'


# ---------------------------------------------------------------------------
# 颜色映射
# ---------------------------------------------------------------------------

_ACCENT_COLORS_LIGHT = {
    ToastType.SUCCESS: QColor('#0F7B0F'),
    ToastType.ERROR:   QColor('#C42B1C'),
    ToastType.WARNING: QColor('#9D5D00'),
    ToastType.INFO:    QColor('#0078D4'),
}

_ACCENT_COLORS_DARK = {
    ToastType.SUCCESS: QColor('#6CCB5F'),
    ToastType.ERROR:   QColor('#FF99A4'),
    ToastType.WARNING: QColor('#FCE100'),
    ToastType.INFO:    QColor('#60CDFF'),
}

_BAR_HEIGHT = 4


def _accentColor(toastType: ToastType) -> QColor:
    """根据当前主题和 Toast 类型返回装饰色。"""
    if toastType == ToastType.CUSTOM:
        return themeColor()
    if isDarkTheme():
        return _ACCENT_COLORS_DARK.get(toastType, themeColor())
    return _ACCENT_COLORS_LIGHT.get(toastType, themeColor())


# ---------------------------------------------------------------------------
# Toast 主体
# ---------------------------------------------------------------------------

class Toast(QFrame):
    """Toast 浮动通知（双层卡片：主体卡片前置，顶部露出一条"同尺寸"的强调色卡片）

    视觉上像两片吐司叠在一起：后置强调色卡片相对主体卡片向上偏移 ``ACCENT_OFFSET``，
    在顶部露出一道带左右圆角的纯色条纹；不自动关闭，只能手动关闭。

    构造函数:
        Toast(toastType, title, content, position, parent)

    静态工厂方法:
        Toast.info / Toast.success / Toast.warning / Toast.error / Toast.new
    """

    closedSignal = Signal()

    # 双层卡片相关常量
    ACCENT_OFFSET = 4       # 强调色卡片相对主体卡片向上外凸的像素数
    CARD_RADIUS = 8.0       # 卡片圆角半径（需与 QSS 中 border-radius 保持一致）

    # 主体卡片默认配色（与 QSS 中 Toast 选择器一致，便于无样式时直接绘制）
    _LIGHT_CARD_BG = QColor(249, 249, 249)
    _LIGHT_CARD_BORDER = QColor(229, 229, 229)
    _DARK_CARD_BG = QColor(44, 44, 44)
    _DARK_CARD_BORDER = QColor(29, 29, 29)

    def __init__(
        self,
        toastType: ToastType = ToastType.INFO,
        title: str = '',
        content: str = '',
        position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
        parent: QWidget = None,
    ):
        """构造 Toast 实例。

        Args:
            toastType: Toast 类型，决定顶部装饰色条颜色
            title: 通知标题
            content: 通知内容
            position: 弹出位置，复用 InfoBarPosition 枚举
            parent: 父部件
        """
        super().__init__(parent=parent)
        self.toastType = toastType
        self.title = title
        self.content = content
        self.position = position

        self.titleLabel = QLabel(self)
        self.contentLabel = QLabel(self)
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)

        self._fadeAni = None

        self.lightBackgroundColor = None
        self.darkBackgroundColor = None

        self._initWidget()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _initWidget(self):
        # 背景由 paintEvent 绘制；声明透明背景，避免 Qt 因为圆角外 4 个未绘制像素
        # 反复重绘父控件，导致明显的卡顿。
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.closeButton.setFixedSize(28, 28)
        self.closeButton.setIconSize(QSize(12, 12))
        self.closeButton.setCursor(Qt.PointingHandCursor)
        self.closeButton.clicked.connect(self.close)

        self._setQss()
        self._initLayout()

    def _initLayout(self):
        # 顶层垂直布局：顶部预留 ACCENT_OFFSET 给后置强调色卡片露出的条纹
        self._outerLayout = QVBoxLayout(self)
        self._outerLayout.setContentsMargins(0, self.ACCENT_OFFSET, 0, 0)
        self._outerLayout.setSpacing(0)

        # 内容区水平布局（位于主体卡片内部；保持透明，背景由 paintEvent 绘制）
        self._contentWidget = QWidget(self)
        self._contentWidget.setObjectName('toastContentWidget')
        self._hLayout = QHBoxLayout(self._contentWidget)
        self._hLayout.setContentsMargins(16, 8, 8, 8)
        self._hLayout.setSpacing(0)

        # 文字垂直布局
        self._textLayout = QVBoxLayout()
        self._textLayout.setSpacing(2)
        self._textLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')
        self.titleLabel.setVisible(bool(self.title))
        self.contentLabel.setVisible(bool(self.content))
        self.titleLabel.setWordWrap(True)
        self.contentLabel.setWordWrap(True)

        self._textLayout.addWidget(self.titleLabel)
        self._textLayout.addWidget(self.contentLabel)

        self._hLayout.addLayout(self._textLayout, 1)
        self._hLayout.addSpacing(4)
        self._hLayout.addWidget(self.closeButton, 0, Qt.AlignTop | Qt.AlignRight)

        # 额外部件区（addWidget 追加到此处）
        self._extraLayout = QVBoxLayout()
        self._extraLayout.setContentsMargins(16, 0, 16, 4)
        self._extraLayout.setSpacing(6)

        self._outerLayout.addWidget(self._contentWidget)
        self._outerLayout.addLayout(self._extraLayout)

        self._adjustText()

    def _setQss(self):
        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.TOAST.apply(self)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def addWidget(self, widget: QWidget, stretch: int = 0):
        """在内容区域底部添加自定义部件。"""
        self._extraLayout.addWidget(widget, stretch)

    def setCustomBackgroundColor(self, light, dark):
        """设置自定义背景色。"""
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _drawBottomAccent(self, painter: QPainter, rect: QRectF, radius: float, cardPath: QPainterPath):
        pass

    def _adjustText(self):
        w = 360 if not self.parent() else min(self.parent().width() - 50, 360)
        chars = max(min(w / 9, 60), 20)
        self.titleLabel.setText(TextWrap.wrap(self.title, chars, False)[0])
        self.contentLabel.setText(TextWrap.wrap(self.content, chars, False)[0])
        self.adjustSize()

    def _fadeOut(self):
        """淡出并关闭 Toast。"""
        try:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
            self._fadeAni = QPropertyAnimation(effect, b'opacity', self)
            self._fadeAni.setDuration(200)
            self._fadeAni.setStartValue(1.0)
            self._fadeAni.setEndValue(0.0)
            self._fadeAni.finished.connect(self.close)
            self._fadeAni.start()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------
    # 事件重写
    # ------------------------------------------------------------------

    def showEvent(self, e):
        self._adjustText()
        super().showEvent(e)

        if self.position != InfoBarPosition.NONE:
            manager = ToastManager.make(self.position)
            manager.add(self)

        if self.parent():
            self.parent().installEventFilter(self)

    def closeEvent(self, e):
        self.closedSignal.emit()
        self.deleteLater()
        e.ignore()

    def eventFilter(self, obj, e: QEvent):
        if obj is self.parent():
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                self._adjustText()
        return super().eventFilter(obj, e)

    def paintEvent(self, e):
        # 跳过 super().paintEvent()：由本方法负责绘制 Toast 自身背景
        # （QSS 中 Toast 的 background/border 已改为透明；子 Label 的 QSS 仍然生效）
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        w, h = self.width(), self.height()
        R = self.CARD_RADIUS
        offset = self.ACCENT_OFFSET
        mainHeight = max(0, h - offset)
        dark = isDarkTheme()

        # 1) 后置强调色卡片：整体相对主体卡片向上外凸 offset，露出顶部一条带圆角条纹
        if offset > 0 and mainHeight > 0:
            painter.setBrush(_accentColor(self.toastType))
            painter.drawRoundedRect(QRectF(0, 0, w, mainHeight), R, R)

        # 2) 主体卡片：带 1px 描边的圆角矩形，位于下层强调卡片之上
        if self.lightBackgroundColor is not None:
            bg = self.darkBackgroundColor if dark else self.lightBackgroundColor
            border = None
        else:
            bg = self._DARK_CARD_BG if dark else self._LIGHT_CARD_BG
            border = self._DARK_CARD_BORDER if dark else self._LIGHT_CARD_BORDER

        main_rect = QRectF(0, offset, w, mainHeight)
        main_path = QPainterPath()
        main_path.addRoundedRect(main_rect, R, R)

        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        painter.drawPath(main_path)

        self._drawBottomAccent(painter, main_rect, R, main_path)

        if border is not None:
            painter.setBrush(Qt.NoBrush)
            pen = QPen(border, 1)
            painter.setPen(pen)
            # 1px 描边需向内缩 0.5px，避免抗锯齿溢出卡片外沿
            border_path = QPainterPath()
            border_path.addRoundedRect(main_rect.adjusted(0.5, 0.5, -0.5, -0.5), R, R)
            painter.drawPath(border_path)

    # ------------------------------------------------------------------
    # 静态工厂方法
    # ------------------------------------------------------------------

    @classmethod
    def new(cls, toastType: ToastType, title: str, content: str,
            position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
            parent: QWidget = None) -> 'Toast':
        """创建并显示 Toast。"""
        w = cls(toastType, title, content, position, parent)
        w.show()
        return w

    @classmethod
    def info(cls, title: str, content: str,
             position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
             parent: QWidget = None) -> 'Toast':
        """创建信息类型 Toast。"""
        return cls.new(ToastType.INFO, title, content, position, parent)

    @classmethod
    def success(cls, title: str, content: str,
                position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
                parent: QWidget = None) -> 'Toast':
        """创建成功类型 Toast。"""
        return cls.new(ToastType.SUCCESS, title, content, position, parent)

    @classmethod
    def warning(cls, title: str, content: str,
                position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
                parent: QWidget = None) -> 'Toast':
        """创建警告类型 Toast。"""
        return cls.new(ToastType.WARNING, title, content, position, parent)

    @classmethod
    def error(cls, title: str, content: str,
              position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
              parent: QWidget = None) -> 'Toast':
        """创建错误类型 Toast。"""
        return cls.new(ToastType.ERROR, title, content, position, parent)


# ---------------------------------------------------------------------------
# ToastManager — 独立单例，不与 InfoBarManager 共享队列
# ---------------------------------------------------------------------------

class ToastManager(QObject):
    """Toast 位置管理器基类

    负责管理特定显示位置上所有 Toast 的队列与布局，确保多个 Toast 有序堆叠不重叠。
    不同位置的管理器以单例形式运行，Toast 在显示时自动注册到对应位置的管理器。
    """

    _instance = None
    managers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        self.spacing = 12
        self.margin = 20
        self.toasts = weakref.WeakKeyDictionary()
        self.aniGroups = weakref.WeakKeyDictionary()
        self.slideAnis = []
        self.dropAnis = []
        self.__initialized = True

    def add(self, toast: Toast):
        """添加 Toast 到管理器。

        Args:
            toast: 要添加的 Toast 实例
        """
        p = toast.parent()
        if not p:
            return

        if p not in self.toasts:
            p.installEventFilter(self)
            self.toasts[p] = []
            self.aniGroups[p] = QParallelAnimationGroup(self)

        if toast in self.toasts[p]:
            return

        # drop 动画（已有 Toast 向下/上移动）
        if self.toasts[p]:
            dropAni = QPropertyAnimation(toast, b'pos')
            dropAni.setDuration(200)
            self.aniGroups[p].addAnimation(dropAni)
            self.dropAnis.append(dropAni)
            toast.setProperty('dropAni', dropAni)

        self.toasts[p].append(toast)
        slideAni = self._createSlideAni(toast)
        self.slideAnis.append(slideAni)
        toast.setProperty('slideAni', slideAni)
        toast.closedSignal.connect(lambda: self.remove(toast))
        slideAni.start()

    def remove(self, toast: Toast):
        """从管理器中移除 Toast。

        Args:
            toast: 要移除的 Toast 实例
        """
        p = toast.parent()
        if p not in self.toasts:
            return
        if toast not in self.toasts[p]:
            return

        self.toasts[p].remove(toast)

        dropAni = toast.property('dropAni')
        if dropAni:
            self.aniGroups[p].removeAnimation(dropAni)
            self.dropAnis.remove(dropAni)

        slideAni = toast.property('slideAni')
        if slideAni and slideAni in self.slideAnis:
            self.slideAnis.remove(slideAni)

        self._updateDropAni(p)
        self.aniGroups[p].start()

    def _createSlideAni(self, toast: Toast) -> QPropertyAnimation:
        ani = QPropertyAnimation(toast, b'pos')
        ani.setEasingCurve(QEasingCurve.OutQuad)
        ani.setDuration(200)
        ani.setStartValue(self._slideStartPos(toast))
        ani.setEndValue(self._pos(toast))
        return ani

    def _updateDropAni(self, parent):
        for t in self.toasts[parent]:
            ani = t.property('dropAni')
            if not ani:
                continue
            ani.setStartValue(t.pos())
            ani.setEndValue(self._pos(t))

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        raise NotImplementedError

    def _slideStartPos(self, toast: Toast) -> QPoint:
        raise NotImplementedError

    def eventFilter(self, obj, e: QEvent):
        try:
            if obj not in self.toasts:
                return False
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                size = e.size() if e.type() == QEvent.Resize else None
                for t in self.toasts[obj]:
                    t.move(self._pos(t, size))
            return super().eventFilter(obj, e)
        except Exception:
            return False

    @classmethod
    def register(cls, name):
        """注册 Toast 位置管理器。

        Args:
            name: InfoBarPosition 枚举值，作为注册键
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager
            return Manager
        return wrapper

    @classmethod
    def make(cls, position: InfoBarPosition) -> 'ToastManager':
        """根据显示位置获取对应的 ToastManager 实例。

        Args:
            position: InfoBarPosition 枚举值

        Returns:
            对应位置的 ToastManager 实例

        Raises:
            ValueError: 如果 position 无效
        """
        if position not in cls.managers:
            raise ValueError(f'`{position}` is an invalid Toast position.')
        return cls.managers[position]()


@ToastManager.register(InfoBarPosition.TOP)
class TopToastManager(ToastManager):
    """顶部居中 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = (parentSize.width() - toast.width()) // 2
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        pos = self._pos(toast)
        return QPoint(pos.x(), pos.y() - 16)


@ToastManager.register(InfoBarPosition.TOP_RIGHT)
class TopRightToastManager(ToastManager):
    """右上角 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = parentSize.width() - toast.width() - self.margin
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        return QPoint(toast.parent().width(), self._pos(toast).y())


@ToastManager.register(InfoBarPosition.TOP_LEFT)
class TopLeftToastManager(ToastManager):
    """左上角 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(self.margin, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        return QPoint(-toast.width(), self._pos(toast).y())


@ToastManager.register(InfoBarPosition.BOTTOM_RIGHT)
class BottomRightToastManager(ToastManager):
    """右下角 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = parentSize.width() - toast.width() - self.margin
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        return QPoint(toast.parent().width(), self._pos(toast).y())


@ToastManager.register(InfoBarPosition.BOTTOM_LEFT)
class BottomLeftToastManager(ToastManager):
    """左下角 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(self.margin, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        return QPoint(-toast.width(), self._pos(toast).y())


@ToastManager.register(InfoBarPosition.BOTTOM)
class BottomToastManager(ToastManager):
    """底部居中 Toast 管理器"""

    def _pos(self, toast: Toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = (parentSize.width() - toast.width()) // 2
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast: Toast) -> QPoint:
        pos = self._pos(toast)
        return QPoint(pos.x(), pos.y() + 16)


# ---------------------------------------------------------------------------
# ProgressToast — 带底部进度条，支持倒计时/不确定动画，时间到自动关闭
# ---------------------------------------------------------------------------

class ProgressToast(Toast):
    """带底部进度条的 Toast 通知

    继承 Toast，但**不显示顶部双层卡片的外凸条纹**，只显示底部 4px 进度条。
    - duration > 0：底部进度条从满到空倒计时，结束后淡出关闭
    - duration < 0：底部不确定进度动画（循环光带），不自动关闭
    - duration = 0：无底部进度条，不自动关闭

    构造函数:
        ProgressToast(toastType, title, content, duration, position, parent)

    静态工厂方法:
        ProgressToast.info / .success / .warning / .error / .new
    """

    # 进度条本身承担底部视觉焦点，因此不再需要顶部外凸条纹
    ACCENT_OFFSET = 0

    def _getProgress(self) -> float:
        return self._progress

    def _setProgress(self, value: float):
        self._progress = max(0.0, min(1.0, value))
        self.update()

    progress = Property(float, _getProgress, _setProgress)

    def _getIndeterminateOffset(self) -> float:
        return self._indeterminateOffset

    def _setIndeterminateOffset(self, value: float):
        self._indeterminateOffset = value % 1.0
        self.update()

    indeterminateOffset = Property(float, _getIndeterminateOffset, _setIndeterminateOffset)

    def __init__(
        self,
        toastType: ToastType = ToastType.INFO,
        title: str = '',
        content: str = '',
        duration: int = 4000,
        position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
        parent: QWidget = None,
    ):
        """构造 ProgressToast 实例。

        Args:
            toastType: Toast 类型，决定底部进度条颜色（不显示顶部装饰色条）
            title: 通知标题
            content: 通知内容
            duration: 显示时长（毫秒），> 0 倒计时自动关闭，< 0 不确定动画不关闭，= 0 无进度条
            position: 弹出位置
            parent: 父部件
        """
        self.duration = duration
        self._progress = 1.0
        self._indeterminateOffset = 0.0

        self._progressAni = None
        self._indeterminateAni = None

        super().__init__(toastType, title, content, position, parent)

    def _setQss(self):
        # 只应用 PROGRESS_TOAST 的 QSS，不调用父类 _setQss（避免 TOAST QSS 冲突）
        FluentStyleSheet.PROGRESS_TOAST.apply(self)

    def _drawBottomAccent(self, painter: QPainter, rect: QRectF, radius: float, cardPath: QPainterPath):
        if self.duration == 0:
            return

        painter.setBrush(_accentColor(self.toastType))

        painter.save()
        painter.setClipPath(cardPath)

        # 2) 再裁剪到底部条带（与卡片圆角取交集）
        painter.setClipRect(
            QRectF(rect.x() - 1, rect.bottom() - _BAR_HEIGHT - 0.5, rect.width() + 2, _BAR_HEIGHT + 1.5),
            Qt.IntersectClip,
        )

        # 用足够高的矩形填色，由双重裁剪决定最终形状，避免圆角处出现缝隙
        if self.duration < 0:
            bandWidth = rect.width() * 0.35
            startX = rect.x() + (rect.width() + bandWidth) * self._indeterminateOffset - bandWidth
            painter.fillRect(QRectF(startX - 1, rect.bottom() - radius, bandWidth + 2, radius + 1), painter.brush())
            painter.restore()
            return

        width = rect.width() * self._progress
        if width > 0:
            painter.fillRect(QRectF(rect.x() - 1, rect.bottom() - radius, width + 1, radius + 1), painter.brush())

        painter.restore()

    # ------------------------------------------------------------------
    # 进度条动画
    # ------------------------------------------------------------------

    def _startProgressAnimation(self):
        """根据 duration 启动对应的底部进度条动画。"""
        if self.duration == 0:
            return

        if self.duration > 0:
            self._progressAni = QPropertyAnimation(self, b'progress', self)
            self._progressAni.setDuration(self.duration)
            self._progressAni.setStartValue(1.0)
            self._progressAni.setEndValue(0.0)
            self._progressAni.setEasingCurve(QEasingCurve.Linear)
            self._progressAni.finished.connect(self._fadeOut)
            self._progressAni.start()
        else:
            # 不确定进度：循环光带
            self._indeterminateAni = QPropertyAnimation(self, b'indeterminateOffset', self)
            self._indeterminateAni.setDuration(1200)
            self._indeterminateAni.setStartValue(0.0)
            self._indeterminateAni.setEndValue(1.0)
            self._indeterminateAni.setLoopCount(-1)
            self._indeterminateAni.start()

    # ------------------------------------------------------------------
    # 事件重写
    # ------------------------------------------------------------------

    def showEvent(self, e):
        self._adjustText()
        # 调用 QFrame.showEvent，跳过 Toast.showEvent 中的 manager 注册
        QFrame.showEvent(self, e)

        self._startProgressAnimation()

        if self.position != InfoBarPosition.NONE:
            manager = ProgressToastManager.make(self.position)
            manager.add(self)

        if self.parent():
            self.parent().installEventFilter(self)

    # ------------------------------------------------------------------
    # 静态工厂方法（覆盖 Toast 的工厂方法，加入 duration 参数）
    # ------------------------------------------------------------------

    @classmethod
    def new(cls, toastType: ToastType, title: str, content: str,
            duration: int = 4000,
            position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
            parent: QWidget = None) -> 'ProgressToast':
        """创建并显示 ProgressToast。"""
        w = cls(toastType, title, content, duration, position, parent)
        w.show()
        return w

    @classmethod
    def info(cls, title: str, content: str, duration: int = 4000,
             position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
             parent: QWidget = None) -> 'ProgressToast':
        """创建信息类型 ProgressToast。"""
        return cls.new(ToastType.INFO, title, content, duration, position, parent)

    @classmethod
    def success(cls, title: str, content: str, duration: int = 4000,
                position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
                parent: QWidget = None) -> 'ProgressToast':
        """创建成功类型 ProgressToast。"""
        return cls.new(ToastType.SUCCESS, title, content, duration, position, parent)

    @classmethod
    def warning(cls, title: str, content: str, duration: int = 4000,
                position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
                parent: QWidget = None) -> 'ProgressToast':
        """创建警告类型 ProgressToast。"""
        return cls.new(ToastType.WARNING, title, content, duration, position, parent)

    @classmethod
    def error(cls, title: str, content: str, duration: int = 4000,
              position: InfoBarPosition = InfoBarPosition.BOTTOM_RIGHT,
              parent: QWidget = None) -> 'ProgressToast':
        """创建错误类型 ProgressToast。"""
        return cls.new(ToastType.ERROR, title, content, duration, position, parent)


# ---------------------------------------------------------------------------
# ProgressToastManager — 独立单例，管理 ProgressToast 的位置与堆叠
# ---------------------------------------------------------------------------

class ProgressToastManager(QObject):
    """ProgressToast 位置管理器基类（与 ToastManager 逻辑相同，但单例独立）"""

    _instance = None
    managers = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        self.spacing = 12
        self.margin = 20
        self.toasts = weakref.WeakKeyDictionary()
        self.aniGroups = weakref.WeakKeyDictionary()
        self.slideAnis = []
        self.dropAnis = []
        self.__initialized = True

    def add(self, toast: ProgressToast):
        p = toast.parent()
        if not p:
            return

        if p not in self.toasts:
            p.installEventFilter(self)
            self.toasts[p] = []
            self.aniGroups[p] = QParallelAnimationGroup(self)

        if toast in self.toasts[p]:
            return

        if self.toasts[p]:
            dropAni = QPropertyAnimation(toast, b'pos')
            dropAni.setDuration(200)
            self.aniGroups[p].addAnimation(dropAni)
            self.dropAnis.append(dropAni)
            toast.setProperty('dropAni', dropAni)

        self.toasts[p].append(toast)
        slideAni = self._createSlideAni(toast)
        self.slideAnis.append(slideAni)
        toast.setProperty('slideAni', slideAni)
        toast.closedSignal.connect(lambda: self.remove(toast))
        slideAni.start()

    def remove(self, toast: ProgressToast):
        p = toast.parent()
        if p not in self.toasts:
            return
        if toast not in self.toasts[p]:
            return

        self.toasts[p].remove(toast)

        dropAni = toast.property('dropAni')
        if dropAni:
            self.aniGroups[p].removeAnimation(dropAni)
            self.dropAnis.remove(dropAni)

        slideAni = toast.property('slideAni')
        if slideAni and slideAni in self.slideAnis:
            self.slideAnis.remove(slideAni)

        self._updateDropAni(p)
        self.aniGroups[p].start()

    def _createSlideAni(self, toast: ProgressToast) -> QPropertyAnimation:
        ani = QPropertyAnimation(toast, b'pos')
        ani.setEasingCurve(QEasingCurve.OutQuad)
        ani.setDuration(200)
        ani.setStartValue(self._slideStartPos(toast))
        ani.setEndValue(self._pos(toast))
        return ani

    def _updateDropAni(self, parent):
        for t in self.toasts[parent]:
            ani = t.property('dropAni')
            if not ani:
                continue
            ani.setStartValue(t.pos())
            ani.setEndValue(self._pos(t))

    def _pos(self, toast: ProgressToast, parentSize=None) -> QPoint:
        raise NotImplementedError

    def _slideStartPos(self, toast: ProgressToast) -> QPoint:
        raise NotImplementedError

    def eventFilter(self, obj, e: QEvent):
        try:
            if obj not in self.toasts:
                return False
            if e.type() in [QEvent.Resize, QEvent.WindowStateChange]:
                size = e.size() if e.type() == QEvent.Resize else None
                for t in self.toasts[obj]:
                    t.move(self._pos(t, size))
            return super().eventFilter(obj, e)
        except Exception:
            return False

    @classmethod
    def register(cls, name):
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager
            return Manager
        return wrapper

    @classmethod
    def make(cls, position: InfoBarPosition) -> 'ProgressToastManager':
        if position not in cls.managers:
            raise ValueError(f'`{position}` is an invalid ProgressToast position.')
        return cls.managers[position]()


@ProgressToastManager.register(InfoBarPosition.TOP)
class TopProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = (parentSize.width() - toast.width()) // 2
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast) -> QPoint:
        pos = self._pos(toast)
        return QPoint(pos.x(), pos.y() - 16)


@ProgressToastManager.register(InfoBarPosition.TOP_RIGHT)
class TopRightProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = parentSize.width() - toast.width() - self.margin
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast) -> QPoint:
        return QPoint(toast.parent().width(), self._pos(toast).y())


@ProgressToastManager.register(InfoBarPosition.TOP_LEFT)
class TopLeftProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        y = self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y += t.height() + self.spacing
        return QPoint(self.margin, y)

    def _slideStartPos(self, toast) -> QPoint:
        return QPoint(-toast.width(), self._pos(toast).y())


@ProgressToastManager.register(InfoBarPosition.BOTTOM_RIGHT)
class BottomRightProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = parentSize.width() - toast.width() - self.margin
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast) -> QPoint:
        return QPoint(toast.parent().width(), self._pos(toast).y())


@ProgressToastManager.register(InfoBarPosition.BOTTOM_LEFT)
class BottomLeftProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(self.margin, y)

    def _slideStartPos(self, toast) -> QPoint:
        return QPoint(-toast.width(), self._pos(toast).y())


@ProgressToastManager.register(InfoBarPosition.BOTTOM)
class BottomProgressToastManager(ProgressToastManager):
    def _pos(self, toast, parentSize=None) -> QPoint:
        p = toast.parent()
        parentSize = parentSize or p.size()
        x = (parentSize.width() - toast.width()) // 2
        y = parentSize.height() - toast.height() - self.margin
        idx = self.toasts[p].index(toast)
        for t in self.toasts[p][:idx]:
            y -= t.height() + self.spacing
        return QPoint(x, y)

    def _slideStartPos(self, toast) -> QPoint:
        pos = self._pos(toast)
        return QPoint(pos.x(), pos.y() + 16)
