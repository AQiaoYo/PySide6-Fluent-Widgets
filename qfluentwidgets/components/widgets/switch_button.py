# coding: utf-8
from enum import Enum

from PySide6.QtCore import Qt, QTimer, Property, Signal, QEvent, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QHoverEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QToolButton, QWidget

from ...common.style_sheet import FluentStyleSheet, themeColor, ThemeColor, isDarkTheme, setCustomStyleSheet
from ...common.overload import singledispatchmethod
from ...common.color import fallbackThemeColor, validColor
from .button import ToolButton


class Indicator(ToolButton):
    """负责绘制开关按钮的圆形滑块并处理位置切换动画
    
    该类通常由 SwitchButton 内部自动创建和管理，一般不需要在外部直接实例化。指示器会在开关状态变化时通过动画平滑移动到目标位置，并提供悬停和按下等视觉反馈
    """

    checkedChanged = Signal(bool)

    def __init__(self, parent):
        """初始化指示器实例
        
        Args:
            parent: 父级控件，通常为 SwitchButton 实例
        """
        super().__init__(parent=parent)
        self.setCheckable(True)
        self.setFixedSize(42, 22)
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()

        self._sliderX = 5
        self.slideAni = QPropertyAnimation(self, b'sliderX', self)
        self.slideAni.setDuration(120)

        self.toggled.connect(self._toggleSlider)

    def mouseReleaseEvent(self, e):
        """鼠标释放时切换选中状态
        
        Args:
            e: 鼠标事件
        """
        super().mouseReleaseEvent(e)
        self.checkedChanged.emit(self.isChecked())

    def _toggleSlider(self):
        self.slideAni.setEndValue(25 if self.isChecked() else 5)
        self.slideAni.start()

    def toggle(self):
        self.setChecked(not self.isChecked())

    def setDown(self, isDown: bool):
        self.isPressed = isDown
        super().setDown(isDown)

    def setHover(self, isHover: bool):
        self.isHover = isHover
        self.update()

    def setCheckedColor(self, light, dark):
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        """绘制指示器
        
        Args:
            e: 绘制事件
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        self._drawBackground(painter)
        self._drawCircle(painter)

    def _drawBackground(self, painter: QPainter):
        r = self.height() / 2
        painter.setPen(self._borderColor())
        painter.setBrush(self._backgroundColor())
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)

    def _drawCircle(self, painter: QPainter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._sliderColor())
        painter.drawEllipse(int(self.sliderX), 5, 12, 12)

    def _backgroundColor(self):
        isDark = isDarkTheme()

        if self.isChecked():
            color = self.darkCheckedColor if isDark else self.lightCheckedColor
            if not self.isEnabled():
                return QColor(255, 255, 255, 41) if isDark else QColor(0, 0, 0, 56)
            if self.isPressed:
                return validColor(color, ThemeColor.LIGHT_2.color())
            elif self.isHover:
                return validColor(color, ThemeColor.LIGHT_1.color())

            return fallbackThemeColor(color)
        else:
            if not self.isEnabled():
                return QColor(0, 0, 0, 0)
            if self.isPressed:
                return QColor(255, 255, 255, 18) if isDark else QColor(0, 0, 0, 23)
            elif self.isHover:
                return QColor(255, 255, 255, 10) if isDark else QColor(0, 0, 0, 15)

            return QColor(0, 0, 0, 0)

    def _borderColor(self):
        isDark = isDarkTheme()

        if self.isChecked():
            return self._backgroundColor() if self.isEnabled() else QColor(0, 0, 0, 0)
        else:
            if self.isEnabled():
                return QColor(255, 255, 255, 153) if isDark else QColor(0, 0, 0, 133)

            return QColor(255, 255, 255, 41) if isDark else QColor(0, 0, 0, 56)

    def _sliderColor(self):
        isDark = isDarkTheme()

        if self.isChecked():
            if self.isEnabled():
                return QColor(Qt.black if isDark else Qt.white)

            return QColor(255, 255, 255, 77) if isDark else QColor(255, 255, 255)
        else:
            if self.isEnabled():
                return QColor(255, 255, 255, 201) if isDark else QColor(0, 0, 0, 156)

            return QColor(255, 255, 255, 96) if isDark else QColor(0, 0, 0, 91)

    def getSliderX(self):
        return self._sliderX

    def setSliderX(self, x):
        self._sliderX = max(x, 5)
        self.update()

    sliderX = Property(float, getSliderX, setSliderX)


class IndicatorPosition(Enum):
    """开关按钮指示器的位置枚举
    
    用于指定 SwitchButton 中圆形指示器相对于文本标签的摆放位置，可选左侧或右侧。在创建 SwitchButton 时通过 indicatorPos 参数传入以改变布局
    """
    LEFT = 0
    RIGHT = 1


class SwitchButton(QWidget):
    """具有流畅设计风格的开关按钮控件，用于在两种互斥状态间切换
    
    适用于设置项的启用/禁用、功能的打开/关闭等需要即时反馈的二元选项场景。支持自定义开关文本、指示器位置以及状态切换动画，状态改变时会触发相应信号
    
    构造函数重载:
        * SwitchButton(parent: QWidget = None)
        * SwitchButton(text: str = "Off", parent: QWidget = None, indicatorPos=IndicatorPosition.LEFT)
    """

    checkedChanged = Signal(bool)

    @singledispatchmethod
    def __init__(self, parent: QWidget = None, indicatorPos=IndicatorPosition.LEFT):
        """Args:
            parent (QWidget): 父部件
            indicatorPos (IndicatorPosition): 指示器位置
        """
        super().__init__(parent=parent)
        self._text = self.tr('Off')
        self._offText =  self.tr('Off')
        self._onText =  self.tr('On')
        self.__spacing = 12
        self.lightTextColor = QColor(0, 0, 0)
        self.darkTextColor = QColor(255, 255, 255)

        self.indicatorPos = indicatorPos
        self.hBox = QHBoxLayout(self)
        self.indicator = Indicator(self)
        self.label = QLabel(self._text, self)

        self.__initWidget()

    @__init__.register
    def _(self, text: str = 'Off', parent: QWidget = None, indicatorPos=IndicatorPosition.LEFT):
        """Args:
            text (str): 开关按钮文本
            parent (QWidget): 父部件
            indicatorPos (IndicatorPosition): 指示器位置
        """
        self.__init__(parent, indicatorPos)
        self._offText = text
        self.setText(text)

    def __initWidget(self):
        """ 初始化部件 """
        self.setAttribute(Qt.WA_StyledBackground)
        self.installEventFilter(self)
        self.setFixedHeight(22)

        # 设置 布局
        self.hBox.setSpacing(self.__spacing)
        self.hBox.setContentsMargins(2, 0, 0, 0)

        if self.indicatorPos == IndicatorPosition.LEFT:
            self.hBox.addWidget(self.indicator)
            self.hBox.addWidget(self.label)
            self.hBox.setAlignment(Qt.AlignLeft)
        else:
            self.hBox.addWidget(self.label, 0, Qt.AlignRight)
            self.hBox.addWidget(self.indicator, 0, Qt.AlignRight)
            self.hBox.setAlignment(Qt.AlignRight)

        # 设置 default 样式表
        FluentStyleSheet.SWITCH_BUTTON.apply(self)
        FluentStyleSheet.SWITCH_BUTTON.apply(self.label)

        # 连接信号与槽函数
        self.indicator.toggled.connect(self._updateText)
        self.indicator.toggled.connect(self.checkedChanged)

    def eventFilter(self, obj, e: QEvent):
        if obj is self and self.isEnabled():
            if e.type() == QEvent.MouseButtonPress:
                self.indicator.setDown(True)
            elif e.type() == QEvent.MouseButtonRelease:
                self.indicator.setDown(False)
                self.indicator.toggle()
            elif e.type() == QEvent.Enter:
                self.indicator.setHover(True)
            elif e.type() == QEvent.Leave:
                self.indicator.setHover(False)

        return super().eventFilter(obj, e)

    def isChecked(self):
        return self.indicator.isChecked()

    def setChecked(self, isChecked):
        """设置选中状态
        
        Args:
            isChecked: 选中状态
        """
        self._updateText()
        self.indicator.setChecked(isChecked)

    def setTextColor(self, light, dark):
        """设置文本颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的文本颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的文本颜色
        """
        self.lightTextColor = QColor(light)
        self.darkTextColor = QColor(dark)

        setCustomStyleSheet(
            self.label,
            f"SwitchButton>QLabel{{color:{self.lightTextColor.name(QColor.NameFormat.HexArgb)}}}",
            f"SwitchButton>QLabel{{color:{self.darkTextColor.name(QColor.NameFormat.HexArgb)}}}"
        )

    def setCheckedIndicatorColor(self, light, dark):
        """设置选中状态下指示器的颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的指示器颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的指示器颜色
        """
        self.indicator.setCheckedColor(light, dark)

    def toggleChecked(self):
        """切换选中状态"""
        self.indicator.setChecked(not self.indicator.isChecked())

    def _updateText(self):
        self.setText(self.onText if self.isChecked() else self.offText)
        self.adjustSize()

    def getText(self):
        return self._text

    def setText(self, text):
        self._text = text
        self.label.setText(text)
        self.adjustSize()

    def getSpacing(self):
        return self.__spacing

    def setSpacing(self, spacing):
        self.__spacing = spacing
        self.hBox.setSpacing(spacing)
        self.update()

    def getOnText(self):
        return self._onText

    def setOnText(self, text):
        self._onText = text
        self._updateText()

    def getOffText(self):
        return self._offText

    def setOffText(self, text):
        self._offText = text
        self._updateText()

    spacing = Property(int, getSpacing, setSpacing)
    checked = Property(bool, isChecked, setChecked)
    text = Property(str, getText, setText)
    onText = Property(str, getOnText, setOnText)
    offText = Property(str, getOffText, setOffText)
