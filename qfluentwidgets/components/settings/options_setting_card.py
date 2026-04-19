# coding: utf-8
"""选项设置卡片"""

from typing import Union
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QLabel

from ...common.config import OptionsConfigItem, qconfig
from ...common.icon import FluentIconBase
from ..widgets.button import RadioButton
from .expand_setting_card import ExpandSettingCard


class OptionsSettingCard(ExpandSettingCard):
    """选项设置卡片"""

    optionChanged = Signal(OptionsConfigItem)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None, parent=None):
        """初始化选项设置卡片

        Args:
            configItem: options 配置项
            icon: 图标
            title: 标题
            content: 内容，默认为 None
            texts: 单选按钮文本列表，默认为 None
            parent: 父组件，默认为 None
        """
        super().__init__(icon, title, content, parent)
        self.texts = texts or []
        self.configItem = configItem
        self.configName = configItem.name
        self.choiceLabel = QLabel(self)
        self.buttonGroup = QButtonGroup(self)

        self.choiceLabel.setObjectName("titleLabel")
        self.addWidget(self.choiceLabel)

        # 创建按钮
        self.viewLayout.setSpacing(19)
        self.viewLayout.setContentsMargins(48, 18, 0, 18)
        for text, option in zip(texts, configItem.options):
            button = RadioButton(text, self.view)
            self.buttonGroup.addButton(button)
            self.viewLayout.addWidget(button)
            button.setProperty(self.configName, option)

        self._adjustViewSize()
        self.setValue(qconfig.get(self.configItem))
        configItem.valueChanged.connect(self.setValue)
        self.buttonGroup.buttonClicked.connect(self.__onButtonClicked)

    def __onButtonClicked(self, button: RadioButton):
        """处理按钮点击事件

        Args:
            button: 被点击的按钮
        """
        if button.text() == self.choiceLabel.text():
            return

        value = button.property(self.configName)
        qconfig.set(self.configItem, value)

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()
        self.optionChanged.emit(self.configItem)

    def setValue(self, value):
        """根据值选中对应按钮

        Args:
            value: 要设置的值
        """
        qconfig.set(self.configItem, value)

        for button in self.buttonGroup.buttons():
            isChecked = button.property(self.configName) == value
            button.setChecked(isChecked)

            if isChecked:
                self.choiceLabel.setText(button.text())
                self.choiceLabel.adjustSize()