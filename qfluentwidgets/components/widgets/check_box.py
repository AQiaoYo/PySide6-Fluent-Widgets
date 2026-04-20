# coding: utf-8
"""提供 Fluent Design 风格的复选框组件及相关辅助类

该模块包含 CheckBox 控件及其内部使用的图标绘制类 CheckBoxIcon 和状态枚举 CheckBoxState，
用于在应用程序中构建支持多选、三态切换的现代化复选框界面
"""
from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton, QWidget

from ...common.icon import FluentIconBase, Theme, getIconColor
from ...common.style_sheet import FluentStyleSheet, isDarkTheme, ThemeColor, themeColor, setCustomStyleSheet
from ...common.overload import singledispatchmethod
from ...common.color import fallbackThemeColor, validColor
from ...common.font import setFont


class CheckBoxIcon(FluentIconBase, Enum):
    """复选框图标绘制控件
    
    负责根据 CheckBox 的当前状态绘制勾选、未勾选或部分勾选的图标效果，
    通常由 CheckBox 内部自动创建和管理，无需单独实例化使用
    """

    ACCEPT = "Accept"
    PARTIAL_ACCEPT = "PartialAccept"

    def path(self, theme=Theme.AUTO):
        c = getIconColor(theme, reverse=True)
        return f':/qfluentwidgets/images/check_box/{self.value}_{c}.svg'


class CheckBoxState(Enum):
    """复选框状态枚举
    
    定义复选框可选中的状态类型，包括未选中、选中和部分选中三种状态，
    常用于需要支持三态逻辑的业务场景，如树形控件中的级联选择
    """

    NORMAL = 0
    HOVER = 1
    PRESSED = 2
    CHECKED = 3
    CHECKED_HOVER = 4
    CHECKED_PRESSED = 5
    DISABLED = 6
    CHECKED_DISABLED = 7


class CheckBox(QCheckBox):
    """Fluent Design 风格的复选框控件
    
    支持显示文本标签和三种勾选状态，适用于表单、设置面板等需要用户进行多项选择的场景，
    可响应点击事件并自动切换选中状态，同时提供状态变化信号供外部监听
    
    构造函数重载:
    * CheckBox(parent: QWidget = None)
    * CheckBox(text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化图标控件
        
        Args:
            parent (QWidget): 父控件实例，用于管理该图标控件的显示层级和生命周期；传 None 时图标将作为独立窗口显示，通常应传入所属的 CheckBox 实例
        """
        super().__init__(parent)
        setFont(self)
        FluentStyleSheet.CHECK_BOX.apply(self)
        self.isPressed = False
        self.isHover = False
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()
        self.lightTextColor = QColor(0, 0, 0)
        self.darkTextColor = QColor(255, 255, 255)

        self._states = {}

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def mousePressEvent(self, e):
        self.isPressed = True
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        super().mouseReleaseEvent(e)

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()

    def setCheckedColor(self, light, dark):
        """设置指示器选中状态的颜色

        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的指示器颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的指示器颜色
        """
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.update()

    def setTextColor(self, light, dark):
        """设置文本颜色

        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的文本颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的文本颜色
        """
        self.lightTextColor = QColor(light)
        self.darkTextColor = QColor(dark)

        setCustomStyleSheet(
            self,
            f"CheckBox{{color:{self.lightTextColor.name(QColor.NameFormat.HexArgb)}}}",
            f"CheckBox{{color:{self.darkTextColor.name(QColor.NameFormat.HexArgb)}}}"
        )

    def _borderColor(self):
        if isDarkTheme():
            map = {
                CheckBoxState.NORMAL: QColor(255, 255, 255, 141),
                CheckBoxState.HOVER: QColor(255, 255, 255, 141),
                CheckBoxState.PRESSED: QColor(255, 255, 255, 40),
                CheckBoxState.CHECKED : fallbackThemeColor(self.darkCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.darkCheckedColor, ThemeColor.DARK_1.color()),
                CheckBoxState.CHECKED_PRESSED : validColor(self.darkCheckedColor, ThemeColor.DARK_2.color()),
                CheckBoxState.DISABLED : QColor(255, 255, 255, 41),
                CheckBoxState.CHECKED_DISABLED : QColor(0, 0, 0, 0)
            }
        else:
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 122),
                CheckBoxState.HOVER: QColor(0, 0, 0, 143),
                CheckBoxState.PRESSED: QColor(0, 0, 0, 69),
                CheckBoxState.CHECKED : fallbackThemeColor(self.lightCheckedColor),
                CheckBoxState.CHECKED_HOVER : validColor(self.lightCheckedColor, ThemeColor.LIGHT_1.color()),
                CheckBoxState.CHECKED_PRESSED : validColor(self.lightCheckedColor, ThemeColor.LIGHT_2.color()),
                CheckBoxState.DISABLED : QColor(0, 0, 0, 56),
                CheckBoxState.CHECKED_DISABLED : QColor(0, 0, 0, 0)
            }

        return map[self._state()]

    def _backgroundColor(self):
        if isDarkTheme():
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 26),
                CheckBoxState.HOVER: QColor(255, 255, 255, 11),
                CheckBoxState.PRESSED: QColor(255, 255, 255, 18),
                CheckBoxState.CHECKED: fallbackThemeColor(self.darkCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.darkCheckedColor, ThemeColor.DARK_1.color()),
                CheckBoxState.CHECKED_PRESSED: validColor(self.darkCheckedColor, ThemeColor.DARK_2.color()),
                CheckBoxState.DISABLED: QColor(0, 0, 0, 0),
                CheckBoxState.CHECKED_DISABLED: QColor(255, 255, 255, 41)
            }
        else:
            map = {
                CheckBoxState.NORMAL: QColor(0, 0, 0, 6),
                CheckBoxState.HOVER: QColor(0, 0, 0, 13),
                CheckBoxState.PRESSED: QColor(0, 0, 0, 31),
                CheckBoxState.CHECKED: fallbackThemeColor(self.lightCheckedColor),
                CheckBoxState.CHECKED_HOVER: validColor(self.lightCheckedColor, ThemeColor.LIGHT_1.color()),
                CheckBoxState.CHECKED_PRESSED: validColor(self.lightCheckedColor, ThemeColor.LIGHT_2.color()),
                CheckBoxState.DISABLED: QColor(0, 0, 0, 0),
                CheckBoxState.CHECKED_DISABLED: QColor(0, 0, 0, 56)
            }

        return map[self._state()]

    def _state(self):
        if not self.isEnabled():
            return CheckBoxState.CHECKED_DISABLED if self.isChecked() else CheckBoxState.DISABLED

        if self.isChecked():
            if self.isPressed:
                return CheckBoxState.CHECKED_PRESSED
            if self.isHover:
                return CheckBoxState.CHECKED_HOVER

            return CheckBoxState.CHECKED
        else:
            if self.isPressed:
                return CheckBoxState.PRESSED
            if self.isHover:
                return CheckBoxState.HOVER

            return CheckBoxState.NORMAL

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        # 获取指示器的区域
        opt = QStyleOptionButton()
        opt.initFrom(self)
        rect = self.style().subElementRect(QStyle.SE_CheckBoxIndicator, opt, self)

        # 绘制shape
        painter.setPen(self._borderColor())
        painter.setBrush(self._backgroundColor())
        painter.drawRoundedRect(rect, 4.5, 4.5)

        if not self.isEnabled():
            painter.setOpacity(0.8)

        # 绘制图标
        if self.checkState() == Qt.Checked:
            CheckBoxIcon.ACCEPT.render(painter, rect)
        elif self.checkState() == Qt.PartiallyChecked:
            CheckBoxIcon.PARTIAL_ACCEPT.render(painter, rect)