# coding: utf-8
from enum import Enum
from string import Template
import sys
from typing import List, Union
import weakref

from PySide6.QtCore import QFile, QObject, QEvent, QDynamicPropertyChangeEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QApplication, QStyleFactory

from .config import qconfig, Theme, isDarkTheme, QT_VERSION


class StyleSheetManager(QObject):
    """ 样式表 管理器 """

    def __init__(self):
        self.widgets = weakref.WeakKeyDictionary()

    def register(self, source, widget: QWidget, reset=True):
        """ 注册 部件 到 管理器

        参数
        ----------
        source: str | StyleSheetBase
            qss 源, it could be:
            * `str`: qss file path
            * `StyleSheetBase`: 样式表 instance

        widget: QWidget
            部件 到 设置 样式表

        reset: bool
            是否 到 reset qss 源
        """
        if isinstance(source, str):
            source = StyleSheetFile(source)

        if widget not in self.widgets:
            widget.destroyed.connect(lambda: self.deregister(widget))
            widget.installEventFilter(CustomStyleSheetWatcher(widget))
            widget.installEventFilter(DirtyStyleSheetWatcher(widget))
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

        if not reset:
            self.source(widget).add(source)
        else:
            self.widgets[widget] = StyleSheetCompose([source, CustomStyleSheet(widget)])

    def deregister(self, widget: QWidget):
        """ deregister 部件 从 管理器 """
        if widget not in self.widgets:
            return

        self.widgets.pop(widget)

    def items(self):
        return self.widgets.items()

    def source(self, widget: QWidget):
        """ 获取部件的qss 源 """
        return self.widgets.get(widget, StyleSheetCompose([]))


styleSheetManager = StyleSheetManager()


class QssTemplate(Template):
    """ 样式表 template """

    delimiter = '--'


def applyThemeColor(qss: str):
    """ apply 主题 颜色 到 样式表

    参数
    ----------
    qss: str
        样式表 string 到 apply 主题 颜色, substituted variable
        should be equal 到 值 的 `ThemeColor` 和 starts 宽度 `--`, i.e `--ThemeColorPrimary`
    """
    template = QssTemplate(qss)
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    return template.safe_substitute(mappings)


def renderQss(qss: str):
    """ render font 和 主题 颜色 到 样式表

    参数
    ----------
    qss: str
        样式表 string 到 apply 主题 颜色, substituted variable
        should be equal 到 值 的 `ThemeColor` 和 starts 宽度 `--`, i.e `--ThemeColorPrimary`
    """
    template = QssTemplate(qss)
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    mappings["FontFamilies"] = ",".join([f"'{i}'" for i in qconfig.get(qconfig.fontFamilies)])
    return template.safe_substitute(mappings)


class StyleSheetBase:
    """ 样式表 基类 """

    def path(self, theme=Theme.AUTO):
        """ 获取style sheet的path """
        raise NotImplementedError

    def content(self, theme=Theme.AUTO):
        """ 获取style sheet的内容 """
        return getStyleSheetFromFile(self.path(theme))

    def apply(self, widget: QWidget, theme=Theme.AUTO):
        """ apply 样式表 到 部件 """
        setStyleSheet(widget, self, theme)


class FluentStyleSheet(StyleSheetBase, Enum):
    """ Fluent 样式表 """

    MENU = "menu"
    LABEL = "label"
    PIVOT = "pivot"
    BUTTON = "button"
    DIALOG = "dialog"
    SLIDER = "slider"
    INFO_BAR = "info_bar"
    SPIN_BOX = "spin_box"
    TAB_VIEW = "tab_view"
    TOOL_TIP = "tool_tip"
    CHECK_BOX = "check_box"
    COMBO_BOX = "combo_box"
    FLIP_VIEW = "flip_view"
    LINE_EDIT = "line_edit"
    LIST_VIEW = "list_view"
    TREE_VIEW = "tree_view"
    INFO_BADGE = "info_badge"
    PIPS_PAGER = "pips_pager"
    TABLE_VIEW = "table_view"
    CARD_WIDGET = "card_widget"
    TIME_PICKER = "time_picker"
    COLOR_DIALOG = "color_dialog"
    MEDIA_PLAYER = "media_player"
    SETTING_CARD = "setting_card"
    TEACHING_TIP = "teaching_tip"
    FLUENT_WINDOW = "fluent_window"
    SWITCH_BUTTON = "switch_button"
    MESSAGE_DIALOG = "message_dialog"
    STATE_TOOL_TIP = "state_tool_tip"
    CALENDAR_PICKER = "calendar_picker"
    FOLDER_LIST_DIALOG = "folder_list_dialog"
    SETTING_CARD_GROUP = "setting_card_group"
    EXPAND_SETTING_CARD = "expand_setting_card"
    NAVIGATION_INTERFACE = "navigation_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/qfluentwidgets/qss/{theme.value.lower()}/{self.value}.qss"


class StyleSheetFile(StyleSheetBase):
    """ 样式表 file """

    def __init__(self, path: str):
        super().__init__()
        self.filePath = path

    def path(self, theme=Theme.AUTO):
        return self.filePath


class CustomStyleSheet(StyleSheetBase):
    """ 自定义 样式表 """

    DARK_QSS_KEY = 'darkCustomQss'
    LIGHT_QSS_KEY = 'lightCustomQss'

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self._widget = weakref.ref(widget)

    def path(self, theme=Theme.AUTO):
        return ''

    @property
    def widget(self):
        return self._widget()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomStyleSheet):
            return False

        return other.widget is self.widget

    def setCustomStyleSheet(self, lightQss: str, darkQss: str):
        """ 设置 自定义 样式表 中的 亮色 和 暗色主题模式 """
        self.setLightStyleSheet(lightQss)
        self.setDarkStyleSheet(darkQss)
        return self

    def setLightStyleSheet(self, qss: str):
        """ 设置 样式表 中的 亮色 模式 """
        if self.widget:
            self.widget.setProperty(self.LIGHT_QSS_KEY, qss)

        return self

    def setDarkStyleSheet(self, qss: str):
        """ 设置 样式表 中的 暗色 模式 """
        if self.widget:
            self.widget.setProperty(self.DARK_QSS_KEY, qss)

        return self

    def lightStyleSheet(self) -> str:
        if not self.widget:
            return ''

        return self.widget.property(self.LIGHT_QSS_KEY) or ''

    def darkStyleSheet(self) -> str:
        if not self.widget:
            return ''

        return self.widget.property(self.DARK_QSS_KEY) or ''

    def content(self, theme=Theme.AUTO) -> str:
        theme = qconfig.theme if theme == Theme.AUTO else theme

        if theme == Theme.LIGHT:
            return self.lightStyleSheet()

        return self.darkStyleSheet()


class CustomStyleSheetWatcher(QObject):
    """ 自定义 样式表 watcher """

    def eventFilter(self, obj: QWidget, e: QEvent):
        if e.type() != QEvent.DynamicPropertyChange:
            return super().eventFilter(obj, e)

        name = QDynamicPropertyChangeEvent(e).propertyName().data().decode()
        if name in [CustomStyleSheet.LIGHT_QSS_KEY, CustomStyleSheet.DARK_QSS_KEY]:
            addStyleSheet(obj, CustomStyleSheet(obj))

        return super().eventFilter(obj, e)


class DirtyStyleSheetWatcher(QObject):
    """ Dirty 样式表 watcher """

    def eventFilter(self, obj: QWidget, e: QEvent):
        if e.type() != QEvent.Type.Paint or not obj.property('dirty-qss'):
            return super().eventFilter(obj, e)

        obj.setProperty('dirty-qss', False)
        if obj in styleSheetManager.widgets:
            obj.setStyleSheet(getStyleSheet(styleSheetManager.source(obj)))

        return super().eventFilter(obj, e)


class StyleSheetCompose(StyleSheetBase):
    """ 样式表 compose """

    def __init__(self, sources: List[StyleSheetBase]):
        super().__init__()
        self.sources = sources

    def content(self, theme=Theme.AUTO):
        return '\n'.join([i.content(theme) for i in self.sources])

    def add(self, source: StyleSheetBase):
        """ 添加 样式表 源 """
        if source is self or source in self.sources:
            return

        self.sources.append(source)

    def remove(self, source: StyleSheetBase):
        """ 移除 样式表 源 """
        if source not in self.sources:
            return

        self.sources.remove(source)


def getStyleSheetFromFile(file: Union[str, QFile]):
    """ 获取 样式表 从 qss file """
    f = QFile(file)
    f.open(QFile.ReadOnly)
    qss = str(f.readAll(), encoding='utf-8')
    f.close()
    return qss


def getStyleSheet(source: Union[str, StyleSheetBase], theme=Theme.AUTO):
    """ 获取 样式表

    参数
    ----------
    source: str | StyleSheetBase
        qss 源, it could be:
          * `str`: qss file path
          * `StyleSheetBase`: 样式表 instance

    theme: 主题
        主题 的 样式表
    """
    if isinstance(source, str):
        source = StyleSheetFile(source)

    return renderQss(source.content(theme))


def setStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):
    """ 设置部件的style sheet

    参数
    ----------
    widget: QWidget
        部件 到 设置 样式表

    source: str | StyleSheetBase
        qss 源, it could be:
          * `str`: qss file path
          * `StyleSheetBase`: 样式表 instance

    theme: 主题
        主题 的 样式表

    register: bool
        是否 到 注册 部件 到 style 管理器. 如果 `注册=True`, style of
        部件 will be updated automatically 当 主题 changes
    """
    if register:
        styleSheetManager.register(source, widget)

    widget.setStyleSheet(getStyleSheet(source, theme))


def setCustomStyleSheet(widget: QWidget, lightQss: str, darkQss: str):
    """ 设置 自定义 样式表

    参数
    ----------
    widget: QWidget
        部件 到 添加 样式表

    lightQss: str
        样式表 used 中的 亮色主题模式

    darkQss: str
        样式表 used 中的 亮色主题模式
    """
    CustomStyleSheet(widget).setCustomStyleSheet(lightQss, darkQss)


def addStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):
    """ 将style sheet添加到部件

    参数
    ----------
    widget: QWidget
        部件 到 设置 样式表

    source: str | StyleSheetBase
        qss 源, it could be:
          * `str`: qss file path
          * `StyleSheetBase`: 样式表 instance

    theme: 主题
        主题 的 样式表

    register: bool
        是否 到 注册 部件 到 style 管理器. 如果 `注册=True`, style of
        部件 will be updated automatically 当 主题 changes
    """
    if register:
        styleSheetManager.register(source, widget, reset=False)
        qss = getStyleSheet(styleSheetManager.source(widget), theme)
    else:
        qss = widget.styleSheet() + '\n' + getStyleSheet(source, theme)

    if qss.rstrip() != widget.styleSheet().rstrip():
        widget.setStyleSheet(qss)


def updateStyleSheet(lazy=False):
    """ 更新the 样式表 的 all fluent 部件

    参数
    ----------
    lazy: bool
        是否 到 更新 样式表 lazily, 设置 到 `True` will accelerate 主题 switching
    """
    removes = []
    for widget, file in list(styleSheetManager.items()):
        try:
            if not (lazy and widget.visibleRegion().isNull()):
                setStyleSheet(widget, file, qconfig.theme)
            else:
                styleSheetManager.register(file, widget)
                widget.setProperty('dirty-qss', True)
        except RuntimeError:
            removes.append(widget)

    for widget in removes:
        styleSheetManager.deregister(widget)


def setTheme(theme: Theme, save=False, lazy=False):
    """ 设置application的主题

    参数
    ----------
    theme: 主题
        主题 模式

    save: bool
        是否 到 save 更改 到 配置 file

    lazy: bool
        是否 到 更新 样式表 lazily, 设置 到 `True` will accelerate 主题 switching
    """
    qconfig.set(qconfig.themeMode, theme, save)
    updateStyleSheet(lazy)
    qconfig.themeChangedFinished.emit()


def toggleTheme(save=False, lazy=False):
    """ 切换the 主题 的 application

    参数
    ----------
    save: bool
        是否 到 save 更改 到 配置 file

    lazy: bool
        是否 到 更新 样式表 lazily, 设置 到 `True` will accelerate 主题 switching
    """
    theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
    setTheme(theme, save, lazy)


class ThemeColor(Enum):
    """ 主题 颜色 type """

    PRIMARY = "ThemeColorPrimary"
    DARK_1 = "ThemeColorDark1"
    DARK_2 = "ThemeColorDark2"
    DARK_3 = "ThemeColorDark3"
    LIGHT_1 = "ThemeColorLight1"
    LIGHT_2 = "ThemeColorLight2"
    LIGHT_3 = "ThemeColorLight3"

    def name(self):
        return self.color().name()

    def color(self):
        color = qconfig.get(qconfig._cfg.themeColor)  # type:QColor

        # transform 颜色 into hsv space
        h, s, v, _ = color.getHsvF()

        if isDarkTheme():
            s *= 0.84
            v = 1
            if self == self.DARK_1:
                v *= 0.9
            elif self == self.DARK_2:
                s *= 0.977
                v *= 0.82
            elif self == self.DARK_3:
                s *= 0.95
                v *= 0.7
            elif self == self.LIGHT_1:
                s *= 0.92
            elif self == self.LIGHT_2:
                s *= 0.78
            elif self == self.LIGHT_3:
                s *= 0.65
        else:
            if self == self.DARK_1:
                v *= 0.75
            elif self == self.DARK_2:
                s *= 1.05
                v *= 0.5
            elif self == self.DARK_3:
                s *= 1.1
                v *= 0.4
            elif self == self.LIGHT_1:
                v *= 1.05
            elif self == self.LIGHT_2:
                s *= 0.75
                v *= 1.05
            elif self == self.LIGHT_3:
                s *= 0.65
                v *= 1.05

        return QColor.fromHsvF(h, min(s, 1), min(v, 1))


def themeColor():
    """ 获取 主题 颜色 """
    return ThemeColor.PRIMARY.color()


def setThemeColor(color, save=False, lazy=False):
    """ 设置 主题 颜色

    参数
    ----------
    color: QColor | Qt.GlobalColor | str
        主题 颜色

    save: bool
        是否 到 save 到 更改 到 配置 file

    lazy: bool
        是否 到 更新 样式表 lazily
    """
    color = QColor(color)
    qconfig.set(qconfig.themeColor, color, save=save)
    updateStyleSheet(lazy)


def updateDynamicStyle(widget: QWidget):
    """ 更新the dynamic style 的 部件 """
    if sys.platform != "win32" or QT_VERSION < (6, 8, 0):
        widget.setStyle(QApplication.style())
    else:
        widget.setStyle(QStyleFactory.create("windowsvista"))