# coding: utf-8
from enum import Enum

from PySide6.QtCore import Qt, QSize, QRectF, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor
from PySide6.QtWidgets import (QSpinBox, QDoubleSpinBox, QToolButton, QHBoxLayout,
                               QDateEdit, QDateTimeEdit, QTimeEdit, QVBoxLayout, QApplication)

from ...common.style_sheet import FluentStyleSheet, themeColor, isDarkTheme
from ...common.icon import FluentIconBase, Theme, getIconColor
from ...common.font import setFont
from ...common.color import FluentSystemColor, autoFallbackThemeColor
from .button import TransparentToolButton
from .line_edit import LineEditMenu
from .flyout import Flyout, FlyoutViewBase, FlyoutAnimationType


class SpinIcon(FluentIconBase, Enum):
    """SpinBox 的图标枚举类
    
    定义了微调框组件中增减按钮与飞出视图中使用的图标类型，
    供 SpinButton 等内部控件使用以保持主题风格一致
    """

    UP = "Up"
    DOWN = "Down"

    def path(self, theme=Theme.AUTO):
        return f':/qfluentwidgets/images/spin_box/{self.value}_{getIconColor(theme)}.svg'



class SpinButton(QToolButton):
    """微调框的增减按钮
    
    提供带图标的上下箭头按钮，通常成对嵌入 SpinBox 中使用，
    点击后发射 clicked 信号用于触发数值的递增或递减操作
    """

    def __init__(self, icon: SpinIcon, parent=None):
        """初始化按钮
        
        Args:
            icon: 按钮显示的图标，类型为 SpinIcon，用于指定显示递增或递减箭头
            parent: 父级控件，默认为 None，传入后按钮将跟随父控件销毁
        """
        super().__init__(parent=parent)
        self.isPressed = False
        self._icon = icon
        self.setFixedSize(31, 23)
        self.setIconSize(QSize(10, 10))
        FluentStyleSheet.SPIN_BOX.apply(self)

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)

        if not self.isEnabled():
            painter.setOpacity(0.36)
        elif self.isPressed:
            painter.setOpacity(0.7)

        self._icon.render(painter, QRectF(10, 6.5, 11, 11))


class CompactSpinButton(QToolButton):
    """紧凑风格的微调框增减按钮
    
    与 SpinButton 功能相同，但尺寸更小、边距更紧凑，
    通常作为 CompactSpinBox 和 CompactDoubleSpinBox 的内部组件使用
    """

    def __init__(self, parent=None):
        """初始化按钮
        
        Args:
            parent: 父级控件，默认为 None
        """
        super().__init__(parent=parent)
        self.setFixedSize(26, 33)
        self.setCursor(Qt.IBeamCursor)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        x = (self.width() - 10) / 2
        s = 9

        SpinIcon.UP.render(painter, QRectF(x, self.height() / 2 - s + 1, s, s))
        SpinIcon.DOWN.render(painter, QRectF(x, self.height() / 2 , s, s))


class SpinFlyoutView(FlyoutViewBase):
    """微调框的飞出视图
    
    在移动端或触控场景下点击 SpinBox 时弹出，
    提供滚轮或按钮形式的选择界面，方便用户快速调整数值
    """

    def __init__(self, parent=None):
        """初始化视图
        
        Args:
            parent: 父级控件，默认为 None
        """
        super().__init__(parent)
        self.upButton = TransparentToolButton(SpinIcon.UP, self)
        self.downButton = TransparentToolButton(SpinIcon.DOWN, self)
        self.vBoxLayout = QVBoxLayout(self)

        self.upButton.setFixedSize(36, 36)
        self.downButton.setFixedSize(36, 36)
        self.upButton.setIconSize(QSize(13, 13))
        self.downButton.setIconSize(QSize(13, 13))

        self.vBoxLayout.setContentsMargins(6, 6, 6, 6)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.upButton)
        self.vBoxLayout.addWidget(self.downButton)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setBrush(
            QColor(46, 46, 46) if isDarkTheme() else QColor(249, 249, 249))
        painter.setPen(
            QColor(0, 0, 0, 51) if isDarkTheme() else QColor(0, 0, 0, 15))

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 8, 8)


class SpinBoxBase:
    """微调框基类
    
    封装了数值范围校验、步长控制、按钮响应和焦点处理等通用逻辑，
    派生类可通过重写相关方法实现整数、浮点数、时间、日期等不同数据类型的输入
    """

    def __init__(self, parent=None):
        """初始化基类
        
        Args:
            parent: 父级控件，默认为 None
        """
        super().__init__(parent=parent)
        self._isError = False
        self.lightFocusedBorderColor = QColor()
        self.darkFocusedBorderColor = QColor()

        self.hBoxLayout = QHBoxLayout(self)

        self.setProperty('transparent', True)
        FluentStyleSheet.SPIN_BOX.apply(self)
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.setFixedHeight(33)
        setFont(self)

        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)

    def isError(self):
        return self._isError

    def setError(self, isError: bool):
        """设置错误状态
        
        Args:
            isError: 是否为错误状态
        """
        if isError == self.isError():
            return

        self._isError = isError
        self.update()

    def setReadOnly(self, isReadOnly: bool):
        super().setReadOnly(isReadOnly)
        self.setSymbolVisible(not isReadOnly)

    def setSymbolVisible(self, isVisible: bool):
        """设置 symbol 是否可见
        
        Args:
            isVisible: symbol 是否可见
        """
        self.setProperty("symbolVisible", isVisible)
        self.setStyle(QApplication.style())

    def setCustomFocusedBorderColor(self, light, dark):
        """设置自定义聚焦边框颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的边框颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的边框颜色
        """
        self.lightFocusedBorderColor = QColor(light)
        self.darkFocusedBorderColor = QColor(dark)
        self.update()

    def focusedBorderColor(self):
        if self.isError():
            return FluentSystemColor.CRITICAL_FOREGROUND.color()

        return autoFallbackThemeColor(self.lightFocusedBorderColor, self.darkFocusedBorderColor)

    def _showContextMenu(self, pos):
        menu = LineEditMenu(self.lineEdit())
        menu.exec_(self.mapToGlobal(pos))

    def _drawBorderBottom(self):
        if not self.hasFocus():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.addRoundedRect(QRectF(0, h-10, w, 10), 5, 5)

        rectPath = QPainterPath()
        rectPath.addRect(0, h-10, w, 8)
        path = path.subtracted(rectPath)

        painter.fillPath(path, self.focusedBorderColor())

    def paintEvent(self, e):
        super().paintEvent(e)
        self._drawBorderBottom()


class InlineSpinBoxBase(SpinBoxBase):
    """内联微调框基类
    
    在 SpinBoxBase 基础上采用内联编辑风格，编辑区与按钮布局更为紧凑，
    适用于需要在列表或表格等狭窄空间内嵌入数值输入的场景
    """

    def __init__(self, parent=None):
        """初始化基类
        
        Args:
            parent: 父级控件，默认为 None
        """
        super().__init__(parent)
        self.upButton = SpinButton(SpinIcon.UP, self)
        self.downButton = SpinButton(SpinIcon.DOWN, self)

        self.hBoxLayout.setContentsMargins(0, 4, 4, 4)
        self.hBoxLayout.setSpacing(5)
        self.hBoxLayout.addWidget(self.upButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.downButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.upButton.clicked.connect(self.stepUp)
        self.downButton.clicked.connect(self.stepDown)

    def setSymbolVisible(self, isVisible: bool):
        super().setSymbolVisible(isVisible)
        self.upButton.setVisible(isVisible)
        self.downButton.setVisible(isVisible)

    def setAccelerated(self, on: bool):
        super().setAccelerated(on)
        self.upButton.setAutoRepeat(on)
        self.downButton.setAutoRepeat(on)


class CompactSpinBoxBase(SpinBoxBase):
    """紧凑微调框基类
    
    在 SpinBoxBase 基础上缩小了控件尺寸和边距，按钮使用 CompactSpinButton，
    适用于工具栏、状态栏或高密度表单等对空间要求严格的界面布局
    """

    def __init__(self, parent=None):
        """初始化基类
        
        Args:
            parent: 父级控件，默认为 None
        """
        super().__init__(parent)
        self.compactSpinButton = CompactSpinButton(self)
        self.spinFlyoutView = SpinFlyoutView(self)
        self.spinFlyout = Flyout(self.spinFlyoutView, self, False)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.compactSpinButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.compactSpinButton.clicked.connect(self._showFlyout)
        self.spinFlyoutView.upButton.clicked.connect(self.stepUp)
        self.spinFlyoutView.downButton.clicked.connect(self.stepDown)

        self.spinFlyout.hide()

    def setAccelerated(self, on: bool):
        super().setAccelerated(on)
        self.spinFlyoutView.upButton.setAutoRepeat(on)
        self.spinFlyoutView.downButton.setAutoRepeat(on)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self._showFlyout()

    def setSymbolVisible(self, isVisible: bool):
        super().setSymbolVisible(isVisible)
        self.compactSpinButton.setVisible(isVisible)

    def _showFlyout(self):
        if self.spinFlyout.isVisible() or self.isReadOnly():
            return

        y = int(self.compactSpinButton.height() / 2 - 46)
        pos = self.compactSpinButton.mapToGlobal(QPoint(-12, y))

        self.spinFlyout.exec(pos, FlyoutAnimationType.FADE_IN)


class SpinBox(InlineSpinBoxBase, QSpinBox):
    """整数微调框
    
    提供带上下箭头的数值输入控件，支持设置最小值、最大值、步长和前缀后缀，
    适用于需要精确输入整数的场景，如数量选择、页码跳转等
    """


class CompactSpinBox(CompactSpinBoxBase, QSpinBox):
    """紧凑整数微调框
    
    功能与 SpinBox 一致，但控件整体尺寸更小，按钮和文本边距更紧凑，
    适合嵌入工具栏或空间受限的表单中使用
    """


class DoubleSpinBox(InlineSpinBoxBase, QDoubleSpinBox):
    """浮点数微调框
    
    提供带上下箭头的浮点数输入控件，支持设置小数精度、最小值、最大值和步长，
    适用于需要精确输入小数的场景，如参数调节、比例设置等
    """


class CompactDoubleSpinBox(CompactSpinBoxBase, QDoubleSpinBox):
    """紧凑浮点数微调框
    
    功能与 DoubleSpinBox 一致，但控件整体尺寸更小，按钮和文本边距更紧凑，
    适合嵌入工具栏或空间受限的表单中使用
    """


class TimeEdit(InlineSpinBoxBase, QTimeEdit):
    """时间编辑框
    
    提供带上下箭头的时间选择控件，支持时、分、秒的输入与调节，
    适用于需要设置或显示具体时刻的场景，如闹钟设置、日程安排等
    """


class CompactTimeEdit(CompactSpinBoxBase, QTimeEdit):
    """紧凑时间编辑框
    
    功能与 TimeEdit 一致，但控件整体尺寸更小，按钮和文本边距更紧凑，
    适合嵌入工具栏或空间受限的表单中使用
    """


class DateTimeEdit(InlineSpinBoxBase, QDateTimeEdit):
    """日期时间编辑框
    
    提供带上下箭头的日期和时间选择控件，支持同时编辑年月日与时、分、秒，
    适用于需要精确到秒的时间点选择场景，如日志筛选、预约设置等
    """


class CompactDateTimeEdit(CompactSpinBoxBase, QDateTimeEdit):
    """紧凑日期时间编辑框
    
    功能与 DateTimeEdit 一致，但控件整体尺寸更小，按钮和文本边距更紧凑，
    适合嵌入工具栏或空间受限的表单中使用
    """


class DateEdit(InlineSpinBoxBase, QDateEdit):
    """日期编辑框
    
    提供带上下箭头的日期选择控件，支持年、月、日的输入与调节，
    适用于需要选择或显示日期的场景，如生日填写、截止日期设置等
    """


class CompactDateEdit(CompactSpinBoxBase, QDateEdit):
    """紧凑日期编辑框
    
    功能与 DateEdit 一致，但控件整体尺寸更小，按钮和文本边距更紧凑，
    适合嵌入工具栏或空间受限的表单中使用
    """
