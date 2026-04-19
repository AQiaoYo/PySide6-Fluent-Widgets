# coding: utf-8
"""FluentWindow 全组件浏览器"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication

from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, ScrollArea, NavigationItemPosition,
    CaptionLabel, SimpleCardWidget, toggleTheme, isDarkTheme,
)

from ._factories import (
    FACTORIES, all_widget_classes, try_instantiate,
    discover_subcategories,
)


class CategoryPage(ScrollArea):
    """单个分类的组件展示页面"""

    def __init__(self, title: str, widget_names: list[str], parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.view)

        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)

        # 透明背景，让 FluentWindow 的主题背景色穿透
        self.setStyleSheet('QScrollArea{background:transparent;border:none}')
        self.view.setStyleSheet('QWidget{background:transparent}')

        self._populate(widget_names)

    def _populate(self, widget_names):
        seen_factories = set()
        all_cls = all_widget_classes()

        for name in widget_names:
            factory = FACTORIES.get(name)
            if factory:
                if id(factory) in seen_factories:
                    continue
                seen_factories.add(id(factory))
                try:
                    for w, desc in factory(self.view):
                        self._add_card(w, desc)
                except Exception:
                    pass
            else:
                cls = all_cls.get(name)
                if cls:
                    w = try_instantiate(cls, name, self.view)
                    if w:
                        self._add_card(w, name)

    def _add_card(self, widget, description):
        card = SimpleCardWidget(self.view)

        lo = QVBoxLayout(card)
        lo.setContentsMargins(16, 16, 16, 16)
        lo.setSpacing(10)

        lbl = CaptionLabel(description, card)
        lbl.setTextColor('#888888', '#999999')
        lo.addWidget(lbl)

        widget.setParent(card)
        lo.addWidget(widget)

        self.vBoxLayout.addWidget(card)


class GalleryWindow(FluentWindow):
    """全组件浏览器，使用 FluentWindow 提供侧边导航"""

    def __init__(self, dark: bool = False):
        super().__init__()
        self.initWindow()
        self.initNavigation()

    def initWindow(self):
        self.setWindowTitle('PySide6-Fluent-Widgets Preview')
        self.resize(960, 700)
        self.setMinimumWidth(700)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def initNavigation(self):
        subcats = discover_subcategories()

        for display_name, icon, widget_names in subcats:
            page = CategoryPage(display_name, widget_names, self)
            obj_name = display_name.replace(' ', '_').replace('&', 'And')
            page.setObjectName(obj_name)
            self.addSubInterface(
                page, icon, display_name,
                position=NavigationItemPosition.SCROLL,
                isTransparent=True,
            )

        self.navigationInterface.addItem(
            routeKey='theme_toggle',
            icon=FIF.CONSTRACT,
            text='Toggle Theme',
            onClick=lambda: toggleTheme(True),
            selectable=False,
            tooltip='Toggle Theme',
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setAcrylicEnabled(True)
