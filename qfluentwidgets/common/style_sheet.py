# coding: utf-8
"""样式表管理模块

提供 QSS 样式表的加载、解析、组合与应用能力，支持主题颜色替换和自定义样式覆盖
该模块是 Fluent Widgets 视觉系统的核心，负责将 Fluent Design 样式应用到各控件
"""

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
    """样式表管理器
    
    负责全局样式表实例的注册、缓存与生命周期管理
    通过统一入口获取样式表内容，避免重复加载与解析，提升渲染性能
    """

    def __init__(self):
        """初始化样式表管理器
        
        Args:
            无
        """
        self.widgets = weakref.WeakKeyDictionary()

    def register(self, source, widget: QWidget, reset=True):
        """注册部件到管理器

        Args:
            source: str | StyleSheetBase
                QSS 源，可以是：
                * `str`: QSS 文件路径
                * `StyleSheetBase`: 样式表实例

            widget: QWidget
                要设置样式表的部件

            reset: bool
                是否重置 QSS 源
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
        """从管理器中注销部件"""
        if widget not in self.widgets:
            return

        self.widgets.pop(widget)

    def items(self):
        return self.widgets.items()

    def source(self, widget: QWidget):
        """获取部件的 QSS 源"""
        return self.widgets.get(widget, StyleSheetCompose([]))


styleSheetManager = StyleSheetManager()


class QssTemplate(Template):
    """QSS 模板
    
    支持基于字符串模板的样式表生成，可替换主题色、尺寸等占位变量
    适用于需要动态注入颜色值或根据状态生成差异化样式的场景
    """

    delimiter = '--'


def applyThemeColor(qss: str):
    """将主题色应用到样式表

    Args:
        qss: str
            需要应用主题色的样式表字符串
            被替换的变量应当与 `ThemeColor` 的值一致，并以 `--` 开头，例如 `--ThemeColorPrimary`
    """
    template = QssTemplate(qss)
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    return template.safe_substitute(mappings)


def renderQss(qss: str):
    """将字体和主题色渲染到样式表

    Args:
        qss: str
            需要渲染字体和主题色的样式表字符串
            被替换的变量应当与 `ThemeColor` 的值一致，并以 `--` 开头，例如 `--ThemeColorPrimary`
    """
    template = QssTemplate(qss)
    mappings = {c.value: c.name() for c in ThemeColor._member_map_.values()}
    mappings["FontFamilies"] = ",".join([f"'{i}'" for i in qconfig.get(qconfig.fontFamilies)])
    return template.safe_substitute(mappings)


class StyleSheetBase:
    """样式表基类
    
    定义样式表内容的统一获取接口，所有具体样式表类均应继承此类
    子类需实现 content 方法以返回有效的 QSS 字符串，供渲染系统消费
    """

    def path(self, theme=Theme.AUTO):
        """获取样式表路径"""
        raise NotImplementedError

    def content(self, theme=Theme.AUTO):
        """获取样式表内容"""
        return getStyleSheetFromFile(self.path(theme))

    def apply(self, widget: QWidget, theme=Theme.AUTO):
        """将样式表应用到部件"""
        setStyleSheet(widget, self, theme)


class FluentStyleSheet(StyleSheetBase, Enum):
    """Fluent 样式表
    
    内置的 Fluent Design 控件样式集合，涵盖按钮、输入框、导航等组件的标准样式
    通常通过枚举值选择对应控件的样式文件路径，配合 StyleSheetCompose 实现主题切换
    """

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
    SUBTITLE_CHECK_BOX = "subtitle_check_box"
    SUBTITLE_RADIO_BUTTON = "subtitle_radio_button"
    COMBO_BOX = "combo_box"
    MULTI_SELECTION_COMBO_BOX = "multi_selection_combo_box"
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
    RANGE_SLIDER = "range_slider"
    RANGE_CALENDAR_PICKER = "range_calendar_picker"
    CALENDAR_TIME_PICKER = "calendar_time_picker"
    TOAST = "toast"
    PROGRESS_TOAST = "progress_toast"
    AGENT_CHAT_VIEW = "agent_chat_view"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/qfluentwidgets/qss/{theme.value.lower()}/{self.value}.qss"


class StyleSheetFile(StyleSheetBase):
    """样式表文件
    
    从本地 QSS 文件加载样式内容，支持相对路径与绝对路径
    适用于需要外置样式文件以便热更新或让用户自定义主题的场景
    """

    def __init__(self, path: str):
        """初始化样式表文件
        
        Args:
            path: QSS 文件路径，可以是相对路径或绝对路径，文件应包含有效的 QSS 内容
        """
        super().__init__()
        self.filePath = path

    def path(self, theme=Theme.AUTO):
        return self.filePath


class CustomStyleSheet(StyleSheetBase):
    """自定义样式表
    
    允许为指定控件附加额外的 QSS 规则，实现局部样式覆盖而不影响全局主题
    常用于对特定实例进行个性化调整，如修改边距、背景图或字体颜色
    """

    DARK_QSS_KEY = 'darkCustomQss'
    LIGHT_QSS_KEY = 'lightCustomQss'

    def __init__(self, widget: QWidget) -> None:
        """初始化自定义样式表
        
        Args:
            widget: 目标控件实例，自定义样式将应用于此控件，需为 QWidget 或其子类
        """
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
        """设置自定义样式表的亮色和暗色主题

        Args:
            lightQss: str
                亮色主题模式下的样式表

            darkQss: str
                暗色主题模式下的样式表
        """
        self.setLightStyleSheet(lightQss)
        self.setDarkStyleSheet(darkQss)
        return self

    def setLightStyleSheet(self, qss: str):
        """设置亮色模式样式表

        Args:
            qss: str
                亮色主题模式下的样式表
        """
        if self.widget:
            self.widget.setProperty(self.LIGHT_QSS_KEY, qss)

        return self

    def setDarkStyleSheet(self, qss: str):
        """设置暗色模式样式表

        Args:
            qss: str
                暗色主题模式下的样式表
        """
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
    """自定义样式表监听器
    
    监听目标控件的自定义样式属性变化，在规则更新时自动触发重绘
    通常作为事件过滤器安装到控件上，确保样式修改能及时反映到界面
    """

    def eventFilter(self, obj: QWidget, e: QEvent):
        if e.type() != QEvent.DynamicPropertyChange:
            return super().eventFilter(obj, e)

        name = QDynamicPropertyChangeEvent(e).propertyName().data().decode()
        if name in [CustomStyleSheet.LIGHT_QSS_KEY, CustomStyleSheet.DARK_QSS_KEY]:
            addStyleSheet(obj, CustomStyleSheet(obj))

        return super().eventFilter(obj, e)


class DirtyStyleSheetWatcher(QObject):
    """脏样式表监听器
    
    追踪控件样式表的脏标记状态，当样式需要重新计算或应用时通知更新系统
    适用于批量样式修改场景，可避免频繁的重复刷新，提升界面更新效率
    """

    def eventFilter(self, obj: QWidget, e: QEvent):
        if e.type() != QEvent.Type.Paint or not obj.property('dirty-qss'):
            return super().eventFilter(obj, e)

        obj.setProperty('dirty-qss', False)
        if obj in styleSheetManager.widgets:
            obj.setStyleSheet(getStyleSheet(styleSheetManager.source(obj)))

        return super().eventFilter(obj, e)


class StyleSheetCompose(StyleSheetBase):
    """样式表组合器
    
    将多个 StyleSheetBase 子类实例按优先级叠加合并，生成最终的 QSS 字符串
    支持主题层、基础层与自定义层的分层组合，后传入的源会覆盖前者同名规则
    """

    def __init__(self, sources: List[StyleSheetBase]):
        """初始化样式表组合器
        
        Args:
            sources: 样式表源列表，元素应为 StyleSheetBase 的子类实例，列表顺序决定叠加优先级，后者覆盖前者
        """
        super().__init__()
        self.sources = sources

    def content(self, theme=Theme.AUTO):
        return '\n'.join([i.content(theme) for i in self.sources])

    def add(self, source: StyleSheetBase):
        """添加样式表源"""
        if source is self or source in self.sources:
            return

        self.sources.append(source)

    def remove(self, source: StyleSheetBase):
        """移除样式表源"""
        if source not in self.sources:
            return

        self.sources.remove(source)


def getStyleSheetFromFile(file: Union[str, QFile]):
    """从 QSS 文件获取样式表"""
    f = QFile(file)
    f.open(QFile.ReadOnly)
    qss = str(f.readAll(), encoding='utf-8')
    f.close()
    return qss


def getStyleSheet(source: Union[str, StyleSheetBase], theme=Theme.AUTO):
    """获取样式表

    Args:
        source: str | StyleSheetBase
            QSS 源，可以是：
            * `str`: QSS 文件路径
            * `StyleSheetBase`: 样式表实例

        theme: Theme
            主题模式
    """
    if isinstance(source, str):
        source = StyleSheetFile(source)

    return renderQss(source.content(theme))


def setStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):
    """设置部件的样式表

    Args:
        widget: QWidget
            要设置样式表的部件

        source: str | StyleSheetBase
            QSS 源，可以是：
            * `str`: QSS 文件路径
            * `StyleSheetBase`: 样式表实例

        theme: Theme
            主题模式

        register: bool
            是否将部件注册到样式管理器，如果为 `True`，部件样式会在主题切换时自动更新
    """
    if register:
        styleSheetManager.register(source, widget)

    widget.setStyleSheet(getStyleSheet(source, theme))


def setCustomStyleSheet(widget: QWidget, lightQss: str, darkQss: str):
    """设置自定义样式表

    Args:
        widget: QWidget
            要添加样式表的部件

        lightQss: str
            亮色主题模式下使用的样式表

        darkQss: str
            暗色主题模式下使用的样式表
    """
    CustomStyleSheet(widget).setCustomStyleSheet(lightQss, darkQss)


def addStyleSheet(widget: QWidget, source: Union[str, StyleSheetBase], theme=Theme.AUTO, register=True):
    """为部件追加样式表

    Args:
        widget: QWidget
            要设置样式表的部件

        source: str | StyleSheetBase
            QSS 源，可以是：
            * `str`: QSS 文件路径
            * `StyleSheetBase`: 样式表实例

        theme: Theme
            主题模式

        register: bool
            是否将部件注册到样式管理器，如果为 `True`，部件样式会在主题切换时自动更新
    """
    if register:
        styleSheetManager.register(source, widget, reset=False)
        qss = getStyleSheet(styleSheetManager.source(widget), theme)
    else:
        qss = widget.styleSheet() + '\n' + getStyleSheet(source, theme)

    if qss.rstrip() != widget.styleSheet().rstrip():
        widget.setStyleSheet(qss)


def updateStyleSheet(lazy=False):
    """更新所有 Fluent 部件的样式表

    Args:
        lazy: bool
            是否延迟更新样式表，设为 `True` 可加快主题切换速度
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
    """设置应用主题

    Args:
        theme: Theme
            主题模式

        save: bool
            是否将更改保存到配置文件

        lazy: bool
            是否延迟更新样式表，设为 `True` 可加快主题切换速度
    """
    qconfig.set(qconfig.themeMode, theme, save)
    updateStyleSheet(lazy)
    qconfig.themeChangedFinished.emit()


def toggleTheme(save=False, lazy=False):
    """切换应用主题

    Args:
        save: bool
            是否将更改保存到配置文件

        lazy: bool
            是否延迟更新样式表，设为 `True` 可加快主题切换速度
    """
    theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
    setTheme(theme, save, lazy)


class ThemeColor(Enum):
    """主题颜色
    
    提供当前活动主题下的主色、辅助色与强调色获取接口，并支持 QSS 变量替换
    颜色值会随全局主题切换自动更新，常用于动态生成跟随主题变化的样式规则
    """

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
    """获取主题颜色"""
    return ThemeColor.PRIMARY.color()


def setThemeColor(color, save=False, lazy=False):
    """设置主题颜色

    Args:
        color: QColor | Qt.GlobalColor | str
            主题颜色

        save: bool
            是否将更改保存到配置文件

        lazy: bool
            是否延迟更新样式表
    """
    color = QColor(color)
    qconfig.set(qconfig.themeColor, color, save=save)
    updateStyleSheet(lazy)


def updateDynamicStyle(widget: QWidget):
    """更新部件的动态样式"""
    if sys.platform != "win32" or QT_VERSION < (6, 8, 0):
        widget.setStyle(QApplication.style())
    else:
        widget.setStyle(QStyleFactory.create("windowsvista"))
