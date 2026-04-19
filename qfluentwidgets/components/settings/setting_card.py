# coding: utf-8
"""设置卡片组件"""

from typing import Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QPushButton
from PySide6.QtSvgWidgets import QSvgWidget

from ..dialog_box.color_dialog import ColorDialog
from ..widgets.combo_box import ComboBox
from ..widgets.switch_button import SwitchButton, IndicatorPosition
from ..widgets.slider import Slider
from ..widgets.icon_widget import IconWidget
from ..widgets.button import HyperlinkButton
from ...common.style_sheet import FluentStyleSheet
from ...common.config import qconfig, isDarkTheme, ConfigItem, OptionsConfigItem
from ...common.icon import FluentIconBase, drawIcon


class SettingIconWidget(IconWidget):
    """设置图标控件"""

    def paintEvent(self, e):
        """绘制设置图标"""
        painter = QPainter(self)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())



class SettingCard(QFrame):
    """设置卡片"""

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """初始化设置卡片

        Args:
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            parent: QWidget
                父部件
        """
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content or '', self)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        if not content:
            self.contentLabel.hide()

        self.setFixedHeight(70 if content else 50)
        self.iconLabel.setFixedSize(16, 16)

        # 初始化布局
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.SETTING_CARD.apply(self)

    def setTitle(self, title: str):
        """设置卡片的标题

        Args:
            title: 标题文本
        """
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        """设置卡片的内容

        Args:
            content: 内容文本
        """
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setValue(self, value):
        """设置配置项的值

        Args:
            value: 配置值
        """
        pass

    def setIconSize(self, width: int, height: int):
        """设置图标的固定大小

        Args:
            width: 图标宽度
            height: 图标高度
        """
        self.iconLabel.setFixedSize(width, height)

    def paintEvent(self, e):
        """绘制设置卡片"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)



class SwitchSettingCard(SettingCard):
    """使用开关按钮的设置卡片"""

    checkedChanged = Signal(bool)

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 configItem: ConfigItem = None, parent=None):
        """初始化开关设置卡片

        Args:
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            configItem: ConfigItem
                由卡片操作的配置项
            parent: QWidget
                父部件
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.switchButton = SwitchButton(
            self.tr('Off'), self, IndicatorPosition.RIGHT)

        if configItem:
            self.setValue(qconfig.get(configItem))
            configItem.valueChanged.connect(self.setValue)

        # 将开关按钮添加到布局.
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, isChecked: bool):
        """开关按钮选中状态变化时的槽函数

        Args:
            isChecked: 是否选中
        """
        self.setValue(isChecked)
        self.checkedChanged.emit(isChecked)

    def setValue(self, isChecked: bool):
        """设置开关状态

        Args:
            isChecked: 是否选中
        """
        if self.configItem:
            qconfig.set(self.configItem, isChecked)

        self.switchButton.setChecked(isChecked)
        self.switchButton.setText(
            self.tr('On') if isChecked else self.tr('Off'))

    def setChecked(self, isChecked: bool):
        """设置开关为选中状态

        Args:
            isChecked: 是否选中
        """
        self.setValue(isChecked)

    def isChecked(self):
        """获取开关是否选中

        Returns:
            bool: 是否选中
        """
        return self.switchButton.isChecked()


class RangeSettingCard(SettingCard):
    """使用滑动条的设置卡片"""

    valueChanged = Signal(int)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """初始化范围设置卡片

        Args:
            configItem: RangeConfigItem
                由卡片操作的配置项
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            parent: QWidget
                父部件
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.slider = Slider(Qt.Horizontal, self)
        self.valueLabel = QLabel(self)
        self.slider.setMinimumWidth(268)

        self.slider.setSingleStep(1)
        self.slider.setRange(*configItem.range)
        self.slider.setValue(configItem.value)
        self.valueLabel.setNum(configItem.value)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(6)
        self.hBoxLayout.addWidget(self.slider, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.valueLabel.setObjectName('valueLabel')
        configItem.valueChanged.connect(self.setValue)
        self.slider.valueChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value: int):
        """滑动条数值变化时的槽函数

        Args:
            value: 当前数值
        """
        self.setValue(value)
        self.valueChanged.emit(value)

    def setValue(self, value):
        """设置滑动条的值

        Args:
            value: 数值
        """
        qconfig.set(self.configItem, value)
        self.valueLabel.setNum(value)
        self.valueLabel.adjustSize()
        self.slider.setValue(value)


class PushSettingCard(SettingCard):
    """使用按钮的设置卡片"""

    clicked = Signal()

    def __init__(self, text, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """初始化按钮设置卡片

        Args:
            text: str
                按钮文本
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            parent: QWidget
                父部件
        """
        super().__init__(icon, title, content, parent)
        self.button = QPushButton(text, self)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.button.clicked.connect(self.clicked)


class PrimaryPushSettingCard(PushSettingCard):
    """使用主题色按钮的设置卡片"""

    def __init__(self, text, icon, title, content=None, parent=None):
        """初始化主题色按钮设置卡片

        Args:
            text: 按钮文本
            icon: 图标
            title: 卡片标题
            content: 卡片内容
            parent: 父部件
        """
        super().__init__(text, icon, title, content, parent)
        self.button.setObjectName('primaryButton')


class HyperlinkCard(SettingCard):
    """超链接设置卡片"""

    def __init__(self, url, text, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """初始化超链接卡片

        Args:
            url: str
                要打开的链接地址
            text: str
                链接文本
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            parent: QWidget
                父部件
        """
        super().__init__(icon, title, content, parent)
        self.linkButton = HyperlinkButton(url, text, self)
        self.hBoxLayout.addWidget(self.linkButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)


class ColorPickerButton(QToolButton):
    """颜色拾取按钮"""

    colorChanged = Signal(QColor)

    def __init__(self, color: QColor, title: str, parent=None, enableAlpha=False):
        """初始化颜色拾取按钮

        Args:
            color: QColor
                初始颜色
            title: str
                标题文本
            parent: QWidget
                父部件
            enableAlpha: bool
                是否启用透明通道
        """
        super().__init__(parent=parent)
        self.title = title
        self.enableAlpha = enableAlpha
        self.setFixedSize(96, 32)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setColor(color)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.__showColorDialog)

    def __showColorDialog(self):
        """显示颜色对话框"""
        w = ColorDialog(self.color, self.tr(
            'Choose ')+self.title, self.window(), self.enableAlpha)
        w.colorChanged.connect(self.__onColorChanged)
        w.exec()

    def __onColorChanged(self, color):
        """颜色变化时的槽函数"""
        self.setColor(color)
        self.colorChanged.emit(color)

    def setColor(self, color):
        """设置颜色"""
        self.color = QColor(color)
        self.update()

    def paintEvent(self, e):
        """绘制颜色拾取按钮"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        pc = QColor(255, 255, 255, 10) if isDarkTheme() else QColor(234, 234, 234)
        painter.setPen(pc)

        color = QColor(self.color)
        if not self.enableAlpha:
            color.setAlpha(255)

        painter.setBrush(color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 5, 5)


class ColorSettingCard(SettingCard):
    """使用颜色拾取器的设置卡片"""

    colorChanged = Signal(QColor)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase],
                 title: str, content: str = None, parent=None, enableAlpha=False):
        """初始化颜色设置卡片

        Args:
            configItem: ConfigItem
                由卡片操作的配置项
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            parent: QWidget
                父部件
            enableAlpha: bool
                是否启用透明通道
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.colorPicker = ColorPickerButton(
            qconfig.get(configItem), title, self, enableAlpha)
        self.hBoxLayout.addWidget(self.colorPicker, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.colorPicker.colorChanged.connect(self.__onColorChanged)
        configItem.valueChanged.connect(self.setValue)

    def __onColorChanged(self, color: QColor):
        """颜色变化时的处理函数

        Args:
            color: 当前颜色
        """
        qconfig.set(self.configItem, color)
        self.colorChanged.emit(color)

    def setValue(self, color: QColor):
        """设置颜色值

        Args:
            color: 颜色值
        """
        self.colorPicker.setColor(color)
        qconfig.set(self.configItem, color)


class ComboBoxSettingCard(SettingCard):
    """使用组合框的设置卡片"""

    def __init__(self, configItem: OptionsConfigItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None, parent=None):
        """初始化组合框设置卡片

        Args:
            configItem: OptionsConfigItem
                由卡片操作的配置项
            icon: str | QIcon | FluentIconBase
                要绘制的图标
            title: str
                卡片标题
            content: str
                卡片内容
            texts: list[str]
                选项文本列表
            parent: QWidget
                父部件
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.optionToText = {o: t for o, t in zip(configItem.options, texts)}
        for text, option in zip(texts, configItem.options):
            self.comboBox.addItem(text, userData=option)

        self.comboBox.setCurrentText(self.optionToText[qconfig.get(configItem)])
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)
        configItem.valueChanged.connect(self.setValue)

    def _onCurrentIndexChanged(self, index: int):
        """当前选项索引变化时的处理函数

        Args:
            index: 当前索引
        """
        qconfig.set(self.configItem, self.comboBox.itemData(index))

    def setValue(self, value):
        """设置当前选中的值

        Args:
            value: 选项值
        """
        if value not in self.optionToText:
            return

        self.comboBox.setCurrentText(self.optionToText[value])
        qconfig.set(self.configItem, value)