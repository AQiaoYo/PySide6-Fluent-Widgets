# coding: utf-8
"""单组件快速预览窗口"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame

from qfluentwidgets import (
    setTheme, Theme, toggleTheme, isDarkTheme,
    FluentIcon as FIF, ToolButton, ToolTipFilter, CaptionLabel,
    TitleLabel, BodyLabel, ScrollArea,
)

from ._factories import FACTORIES, all_widget_classes, try_instantiate


class PreviewWindow(QWidget):

    def __init__(self, component_name: str, dark: bool = False):
        super().__init__()
        self._cards: list[QFrame] = []
        if dark:
            setTheme(Theme.DARK)

        self.setWindowTitle(f'Preview: {component_name}')
        self.setAttribute(Qt.WA_StyledBackground)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        self._toolbar = QWidget(self)
        self._toolbar.setFixedHeight(56)
        tb = QHBoxLayout(self._toolbar)
        tb.setContentsMargins(20, 0, 20, 0)
        tb.addWidget(TitleLabel(component_name, self._toolbar))
        tb.addStretch()
        btn = ToolButton(FIF.CONSTRACT, self._toolbar)
        btn.setToolTip('Toggle theme')
        btn.installEventFilter(ToolTipFilter(btn))
        btn.clicked.connect(self._toggle_theme)
        tb.addWidget(btn)
        root.addWidget(self._toolbar)

        # 内容区
        self._scroll = ScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content = QWidget()
        self._content.setObjectName('scrollContent')
        self._layout = QVBoxLayout(self._content)
        self._layout.setSpacing(24)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setAlignment(Qt.AlignTop)
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll)

        self._populate(component_name)
        self._apply_theme()
        self.resize(520, 600)

    def _apply_theme(self):
        dark = isDarkTheme()
        bg = '#202020' if dark else '#f5f5f5'
        card_bg = '#2d2d2d' if dark else 'white'
        card_border = '#3d3d3d' if dark else '#e0e0e0'
        self.setStyleSheet(f'PreviewWindow{{background:{bg}}}#scrollContent{{background:transparent}}')
        self._scroll.setStyleSheet('QScrollArea{background:transparent;border:none}'
                                   'QScrollArea>QWidget>QWidget{background:transparent}')
        self._toolbar.setStyleSheet(f'QWidget{{background:{bg}}}')
        qss = f'#exampleCard{{background:{card_bg};border-radius:8px;border:1px solid {card_border}}}'
        for c in self._cards:
            c.setStyleSheet(qss)

    def _toggle_theme(self):
        toggleTheme(True)
        self._apply_theme()

    def _populate(self, name):
        factory = FACTORIES.get(name)
        if factory:
            for w, desc in factory(self):
                self._add_card(w, desc)
            return

        cls = all_widget_classes().get(name)
        if cls is None:
            self._layout.addWidget(BodyLabel(f'"{name}" 不是可预览的组件', self))
            return
        w = try_instantiate(cls, name, self)
        if w:
            self._add_card(w, name)
        else:
            self._layout.addWidget(BodyLabel(f'"{name}" 无法自动实例化', self))

    def _add_card(self, widget, description):
        card = QFrame(self)
        card.setObjectName('exampleCard')
        self._cards.append(card)
        lo = QVBoxLayout(card)
        lo.setContentsMargins(16, 16, 16, 16)
        lo.setSpacing(12)
        lbl = CaptionLabel(description, card)
        lbl.setTextColor('#888888', '#999999')
        lo.addWidget(lbl)
        widget.setParent(card)
        lo.addWidget(widget)
        self._layout.addWidget(card)
