# coding: utf-8
"""自定义颜色设置卡片"""

from typing import Union
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QWidget, QLabel, QButtonGroup, QVBoxLayout, QPushButton, QHBoxLayout

from ..dialog_box import ColorDialog
from .expand_setting_card import ExpandGroupSettingCard
from ..widgets.button import RadioButton
from ...common.config import qconfig, ColorConfigItem
from ...common.icon import FluentIconBase


class CustomColorSettingCard(ExpandGroupSettingCard):
    """自定义颜色设置卡片"""

    colorChanged = Signal(QColor)

    def __init__(self, configItem: ColorConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                 content=None, parent=None, enableAlpha=False):
        """
        初始化自定义颜色设置卡片

        Args:
            configItem: 颜色配置项
            icon: 图标
            title: 标题
            content: 内容
            parent: 父窗口
            enableAlpha: 是否启用透明通道
        """
        super().__init__(icon, title, content, parent=parent)
        self.enableAlpha = enableAlpha
        self.configItem = configItem
        self.defaultColor = QColor(configItem.defaultValue)
        self.customColor = QColor(qconfig.get(configItem))

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('Default color'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('Custom color'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customColorWidget = QWidget(self.view)
        self.customColorLayout = QHBoxLayout(self.customColorWidget)
        self.customLabel = QLabel(
            self.tr('Custom color'), self.customColorWidget)
        self.chooseColorButton = QPushButton(
            self.tr('Choose color'), self.customColorWidget)

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.defaultColor != self.customColor:
            self.customRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(True)
        else:
            self.defaultRadioButton.setChecked(True)
            self.chooseColorButton.setEnabled(False)

        self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.chooseColorButton.setObjectName('chooseColorButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.chooseColorButton.clicked.connect(self.__showColorDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customColorLayout.setContentsMargins(48, 18, 44, 18)
        self.customColorLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customColorLayout.addWidget(self.chooseColorButton, 0, Qt.AlignRight)
        self.customColorLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customColorWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """
        单选按钮点击时的槽函数

        Args:
            button: 被点击的单选按钮
        """
        if button.text() == self.choiceLabel.text():
            return

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            self.chooseColorButton.setDisabled(True)
            qconfig.set(self.configItem, self.defaultColor)
            if self.defaultColor != self.customColor:
                self.colorChanged.emit(self.defaultColor)
        else:
            self.chooseColorButton.setDisabled(False)
            qconfig.set(self.configItem, self.customColor)
            if self.defaultColor != self.customColor:
                self.colorChanged.emit(self.customColor)

    def __showColorDialog(self):
        """显示颜色对话框"""
        w = ColorDialog(
            qconfig.get(self.configItem), self.tr('Choose color'), self.window(), self.enableAlpha)
        w.colorChanged.connect(self.__onCustomColorChanged)
        w.exec()

    def __onCustomColorChanged(self, color):
        """
        自定义颜色改变时的槽函数

        Args:
            color: 颜色值
        """
        qconfig.set(self.configItem, color)
        self.customColor = QColor(color)
        self.colorChanged.emit(color)