# coding: utf-8
"""设置卡片分组"""

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from ...common.style_sheet import FluentStyleSheet
from ...common.font import setFont
from ..layout.expand_layout import ExpandLayout


class SettingCardGroup(QWidget):
    """设置卡片分组"""

    def __init__(self, title: str, parent=None):
        """初始化设置卡片分组

        Args:
            title: 分组标题
            parent: 父级控件，默认为 None
        """
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()

    def addSettingCard(self, card: QWidget):
        """添加设置卡片到分组

        Args:
            card: 要添加的设置卡片
        """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addSettingCards(self, cards: List[QWidget]):
        """批量添加设置卡片到分组

        Args:
            cards: 要添加的设置卡片列表
        """
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self):
        """调整控件大小以适应内容"""
        h = self.cardLayout.heightForWidth(self.width()) + 46
        return self.resize(self.width(), h)