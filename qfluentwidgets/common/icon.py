# coding: utf-8
"""图标相关工具模块
提供 Fluent 图标、SVG 图标、字体图标等多种图标引擎与图标类，用于在 PyQt/PySide 应用中绘制、管理和切换图标资源，支持自动适配明暗主题
"""

from enum import Enum
from typing import Union
import json

from PySide6.QtXml import QDomDocument
from PySide6.QtCore import QRectF, Qt, QFile, QObject, QRect
from PySide6.QtGui import QIcon, QIconEngine, QColor, QPixmap, QImage, QPainter, QFontDatabase, QFont, QAction, QPainterPath
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from .config import isDarkTheme, Theme
from .overload import singledispatchmethod


class FluentIconEngine(QIconEngine):
    """Fluent 图标引擎
    负责将 FluentIconBase 渲染为 QIcon，支持根据主题自动切换图标颜色，通常作为内部引擎在设置按钮、菜单项或工具栏图标时使用
    """

    def __init__(self, icon, reverse=False):
        """初始化 Fluent 图标 engine

        Args:
            icon: 要绘制的图标，类型为 QIcon、Icon 或 FluentIconBase
            reverse: 是否反转图标主题
        """
        super().__init__()
        self.icon = icon
        self.isThemeReversed = reverse

    def paint(self, painter, rect, mode, state):
        painter.save()

        if mode == QIcon.Disabled:
            painter.setOpacity(0.5)
        elif mode == QIcon.Selected:
            painter.setOpacity(0.7)

        # 更改图标 颜色 根据 主题
        icon = self.icon

        if not self.isThemeReversed:
            theme = Theme.AUTO
        else:
            theme = Theme.LIGHT if isDarkTheme() else Theme.DARK

        if isinstance(self.icon, Icon):
            icon = self.icon.fluentIcon.icon(theme)
        elif isinstance(self.icon, FluentIconBase):
            icon = self.icon.icon(theme)

        if rect.x() == 19:
            rect = rect.adjusted(-1, 0, 0, 0)

        icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, state)
        painter.restore()

    def clone(self) -> QIconEngine:
        return FluentIconEngine(self.icon, self.isThemeReversed)

    def pixmap(self, size, mode, state):
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        try:
            self.paint(painter, rect, mode, state)
        finally:
            painter.end()
        return pixmap


class SvgIconEngine(QIconEngine):
    """Svg 图标引擎
    基于 SVG 数据渲染矢量图标，支持任意缩放且保持清晰，适用于工具栏、状态栏等需要高分辨率图标的场景
    """

    def __init__(self, svg: str):
        """初始化图标引擎
        Args:
            svg: SVG 字符串或 QByteArray 数据，作为图标绘制源
        """
        super().__init__()
        self.svg = svg

    def paint(self, painter, rect, mode, state):
        drawSvgIcon(self.svg.encode(), painter, rect)

    def clone(self) -> QIconEngine:
        return SvgIconEngine(self.svg)

    def pixmap(self, size, mode, state):
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        try:
            self.paint(painter, rect, mode, state)
        finally:
            painter.end()
        return pixmap


class FontIconEngine(QIconEngine):
    """Font 图标引擎
    使用字体族中的指定字符渲染图标，支持自定义颜色和粗体样式，适用于需要通过字体文件加载单色图标的轻量级场景
    """

    def __init__(self, fontFamily: str, char: str, color, isBold):
        """初始化字体图标引擎
        Args:
            fontFamily: 字体族名称，用于指定图标所在字体
            char: 图标对应的字符或 Unicode 编码
            color: 图标颜色，可以是 QColor、Qt.GlobalColor 或十六进制颜色字符串
            isBold: 是否使用粗体样式绘制图标
        """
        super().__init__()
        self.color = color
        self.char = char
        self.fontFamily = fontFamily
        self.isBold = isBold

    def paint(self, painter, rect, mode, state):
        font = QFont(self.fontFamily)
        font.setBold(self.isBold)
        font.setPixelSize(round(rect.height()))
        painter.setFont(font)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.color)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        path = QPainterPath()
        path.addText(rect.x(), rect.y() + rect.height(), font, self.char)
        painter.drawPath(path)


    def clone(self) -> QIconEngine:
        return FontIconEngine(self.fontFamily, self.char, self.color, self.isBold)

    def pixmap(self, size, mode, state):
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        pixmap = QPixmap.fromImage(image, Qt.NoFormatConversion)

        painter = QPainter(pixmap)
        rect = QRect(0, 0, size.width(), size.height())
        try:
            self.paint(painter, rect, mode, state)
        finally:
            painter.end()
        return pixmap


def getIconColor(theme=Theme.AUTO, reverse=False):
    """根据主题获取图标颜色

    Args:
        theme: 图标主题
        reverse: 是否反转颜色

    Returns:
        图标颜色字符串
    """
    if not reverse:
        lc, dc = "black", "white"
    else:
        lc, dc = "white", "black"

    if theme == Theme.AUTO:
        color = dc if isDarkTheme() else lc
    else:
        color = dc if theme == Theme.DARK else lc

    return color


def drawSvgIcon(icon, painter, rect):
    """绘制 SVG 图标

    Args:
        icon: SVG 图标路径或源码
        painter: 画笔对象
        rect: 图标绘制区域
    """
    renderer = QSvgRenderer(icon)
    renderer.render(painter, QRectF(rect))


def writeSvg(iconPath: str, indexes=None, **attributes):
    """使用指定属性重写 SVG

    Args:
        iconPath: SVG 图标路径
        indexes: 需要填充属性的路径索引
        **attributes: 要写入路径的属性

    Returns:
        SVG 代码
    """
    if not iconPath.lower().endswith('.svg'):
        return ""

    f = QFile(iconPath)
    f.open(QFile.ReadOnly)

    dom = QDomDocument()
    dom.setContent(f.readAll())

    f.close()

    # 修改每条路径的颜色.
    pathNodes = dom.elementsByTagName('path')
    indexes = range(pathNodes.length()) if not indexes else indexes
    for i in indexes:
        element = pathNodes.at(i).toElement()

        for k, v in attributes.items():
            element.setAttribute(k, v)

    return dom.toString()


def drawIcon(icon, painter, rect, state=QIcon.Off, **attributes):
    """绘制图标

    Args:
        icon: 要绘制的图标
        painter: 画笔对象
        rect: 图标绘制区域
        state: 图标状态
        **attributes: SVG 图标附加属性
    """
    if isinstance(icon, FluentIconBase):
        icon.render(painter, rect, **attributes)
    elif isinstance(icon, Icon):
        icon.fluentIcon.render(painter, rect, **attributes)
    else:
        icon = QIcon(icon)
        icon.paint(painter, QRectF(rect).toRect(), Qt.AlignCenter, state=state)


class FluentIconBase:
    """Fluent 图标基类
    定义 Fluent 图标的公共接口与主题切换行为，所有具体 Fluent 图标类均需继承此类并实现 path 属性，以便图标引擎正确加载资源
    """

    def path(self, theme=Theme.AUTO) -> str:
        """获取图标路径

        Args:
            theme: 图标所属主题
                * Theme.LIGHT: 黑色图标
                * Theme.DARK: 白色图标
                * Theme.AUTO: 图标颜色取决于 qconfig.theme

        Returns:
            图标路径
        """
        raise NotImplementedError

    def icon(self, theme=Theme.AUTO, color: QColor = None) -> QIcon:
        """创建 Fluent 图标

        Args:
            theme: 图标所属主题
                * Theme.LIGHT: 黑色图标
                * Theme.DARK: 白色图标
                * Theme.AUTO: 图标颜色取决于 qconfig.theme
            color: 图标颜色，仅适用于 SVG 图标

        Returns:
            QIcon 对象
        """
        path = self.path(theme)

        if not (path.endswith('.svg') and color):
            return QIcon(self.path(theme))

        color = QColor(color).name()
        return QIcon(SvgIconEngine(writeSvg(path, fill=color)))

    def colored(self, lightColor: QColor, darkColor: QColor) -> "ColoredFluentIcon":
        """创建带主题色的 Fluent 图标

        Args:
            lightColor: 亮色模式下的图标颜色
            darkColor: 暗色模式下的图标颜色

        Returns:
            ColoredFluentIcon 对象
        """
        return ColoredFluentIcon(self, lightColor, darkColor)

    def qicon(self, reverse=False) -> QIcon:
        """转换为 QIcon，并随应用主题同步更新图标

        Args:
            reverse: 是否反转图标主题

        Returns:
            QIcon 对象
        """
        return QIcon(FluentIconEngine(self, reverse))

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        """绘制 SVG 图标

        Args:
            painter: 画笔对象
            rect: 图标绘制区域
            theme: 图标所属主题
                * Theme.LIGHT: 黑色图标
                * Theme.DARK: 白色图标
                * Theme.AUTO: 图标颜色取决于 qconfig.theme
            indexes: 需要修改属性的 SVG 路径索引
            **attributes: 要更新到路径上的属性
        """
        icon = self.path(theme)

        if icon.endswith('.svg'):
            if attributes:
                icon = writeSvg(icon, indexes, **attributes).encode()

            drawSvgIcon(icon, painter, rect)
        else:
            icon = QIcon(icon)
            rect = QRectF(rect).toRect()
            painter.drawPixmap(rect, icon.pixmap(QRectF(rect).toRect().size()))


class FluentFontIconBase(FluentIconBase):
    """Fluent font 图标基类
    为基于字体的 Fluent 图标提供统一基类，管理字符编码与主题色映射，适合构建通过自定义字体承载的图标体系
    """

    _isFontLoaded = False
    fontId = None
    fontFamily = None
    _iconNames = {}

    def __init__(self, char: str):
        """初始化字体图标基类
        Args:
            char: 图标对应的字符或 Unicode 字符串，作为字体图标的显示内容
        """
        super().__init__()
        self.char = char
        self.lightColor = QColor(0, 0, 0)
        self.darkColor = QColor(255, 255, 255)
        self.isBold = False
        self.loadFont()

    @classmethod
    def fromName(cls, name: str):
        icon = cls("")
        icon.char = cls._iconNames.get(name, "")
        return icon

    def bold(self):
        self.isBold = True
        return self

    def icon(self, theme=Theme.AUTO, color: QColor = None) -> QIcon:
        if not color:
            color = self._getIconColor(theme)

        return QIcon(FontIconEngine(self.fontFamily, self.char, color, self.isBold))

    def colored(self, lightColor, darkColor):
        self.lightColor = QColor(lightColor)
        self.darkColor = QColor(darkColor)
        return self

    def render(self, painter: QPainter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        color = self._getIconColor(theme)

        if "fill" in attributes:
            color = QColor(attributes["fill"])

        font = QFont(self.fontFamily)
        font.setBold(self.isBold)
        font.setPixelSize(round(rect.height()))
        painter.setFont(font)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        path = QPainterPath()
        path.addText(rect.x(), rect.y() + rect.height(), font, self.char)
        painter.drawPath(path)

    def iconNameMapPath(self) -> str:
        return None

    def loadFont(self):
        """加载图标字体"""
        cls = self.__class__
        if cls._isFontLoaded or not QApplication.instance():
            return

        file = QFile(self.path())
        if not file.open(QFile.ReadOnly):
            raise FileNotFoundError(f"Cannot open font file: {self.path()}")

        data = file.readAll()
        file.close()

        cls.fontId = QFontDatabase.addApplicationFontFromData(data)
        cls.fontFamily = QFontDatabase.applicationFontFamilies(cls.fontId)[0]

        if self.iconNameMapPath():
            self.loadIconNames()

    def loadIconNames(self):
        """加载图标名称映射"""
        cls = self.__class__
        cls._iconNames.clear()

        file = QFile(self.iconNameMapPath())
        if not file.open(QFile.ReadOnly):
            raise FileNotFoundError(f"Cannot open font file: {self.iconNameMapPath()}")

        cls._iconNames = json.loads(str(file.readAll(), encoding='utf-8'))
        file.close()

    def _getIconColor(self, theme):
        if theme == Theme.AUTO:
            color = self.darkColor if isDarkTheme() else self.lightColor
        else:
            color = self.darkColor if theme == Theme.DARK else self.lightColor

        return color


class ColoredFluentIcon(FluentIconBase):
    """带主题色的 Fluent 图标
    在 FluentIcon 基础上支持自定义主题色覆盖，可根据应用主题自动调整图标色调，适用于需要强调视觉层次或品牌色的界面元素
    """

    def __init__(self, icon: FluentIconBase, lightColor, darkColor):
        """初始化带主题色的 Fluent 图标

        Args:
            icon: 要着色的图标
            lightColor: 亮色模式下的图标颜色
            darkColor: 暗色模式下的图标颜色
        """
        super().__init__()
        self.fluentIcon = icon
        self.lightColor = QColor(lightColor)
        self.darkColor = QColor(darkColor)

    def path(self, theme=Theme.AUTO) -> str:
        return self.fluentIcon.path(theme)

    def render(self, painter, rect, theme=Theme.AUTO, indexes=None, **attributes):
        icon = self.path(theme)

        if not icon.endswith('.svg'):
            return self.fluentIcon.render(painter, rect, theme, indexes, attributes)

        if theme == Theme.AUTO:
            color = self.darkColor if isDarkTheme() else self.lightColor
        else:
            color = self.darkColor if theme == Theme.DARK else self.lightColor

        attributes.update(fill=color.name())
        icon = writeSvg(icon, indexes, **attributes).encode()
        drawSvgIcon(icon, painter, rect)



class FluentIcon(FluentIconBase, Enum):
    """Fluent 图标
    内置丰富的标准化 Fluent Design 图标资源，支持自动适配应用明暗主题，常用于导航栏、按钮、菜单和设置面板等控件
    """

    UP = "Up"
    ADD = "Add"
    BUS = "Bus"
    CAR = "Car"
    CUT = "Cut"
    IOT = "IOT"
    PIN = "Pin"
    TAG = "Tag"
    VPN = "VPN"
    CAFE = "Cafe"
    CHAT = "Chat"
    COPY = "Copy"
    CODE = "Code"
    DOWN = "Down"
    EDIT = "Edit"
    FLAG = "Flag"
    FONT = "Font"
    GAME = "Game"
    HELP = "Help"
    HIDE = "Hide"
    HOME = "Home"
    INFO = "Info"
    LEAF = "Leaf"
    LINK = "Link"
    MAIL = "Mail"
    MENU = "Menu"
    MUTE = "Mute"
    MORE = "More"
    MOVE = "Move"
    PLAY = "Play"
    SAVE = "Save"
    SEND = "Send"
    SYNC = "Sync"
    UNIT = "Unit"
    VIEW = "View"
    WIFI = "Wifi"
    ZOOM = "Zoom"
    ALBUM = "Album"
    BRUSH = "Brush"
    BROOM = "Broom"
    CLOSE = "Close"
    CLOUD = "Cloud"
    EMBED = "Embed"
    GLOBE = "Globe"
    HEART = "Heart"
    LABEL = "Label"
    MEDIA = "Media"
    MOVIE = "Movie"
    MUSIC = "Music"
    ROBOT = "Robot"
    PAUSE = "Pause"
    PASTE = "Paste"
    PHOTO = "Photo"
    PHONE = "Phone"
    PRINT = "Print"
    SHARE = "Share"
    TILES = "Tiles"
    UNPIN = "Unpin"
    VIDEO = "Video"
    TRAIN = "Train"
    ADD_TO  ="AddTo"
    ACCEPT = "Accept"
    CAMERA = "Camera"
    CANCEL = "Cancel"
    DELETE = "Delete"
    FOLDER = "Folder"
    FILTER = "Filter"
    MARKET = "Market"
    SCROLL = "Scroll"
    LAYOUT = "Layout"
    GITHUB = "GitHub"
    UPDATE = "Update"
    REMOVE = "Remove"
    RETURN = "Return"
    PEOPLE = "People"
    QRCODE = "QRCode"
    RINGER = "Ringer"
    ROTATE = "Rotate"
    SEARCH = "Search"
    VOLUME = "Volume"
    FRIGID  = "Frigid"
    SAVE_AS = "SaveAs"
    ZOOM_IN = "ZoomIn"
    CONNECT  ="Connect"
    HISTORY = "History"
    SETTING = "Setting"
    PALETTE = "Palette"
    MESSAGE = "Message"
    FIT_PAGE = "FitPage"
    ZOOM_OUT = "ZoomOut"
    AIRPLANE = "Airplane"
    ASTERISK = "Asterisk"
    CALORIES = "Calories"
    CALENDAR = "Calendar"
    FEEDBACK = "Feedback"
    LIBRARY = "BookShelf"
    MINIMIZE = "Minimize"
    CHECKBOX = "CheckBox"
    DOCUMENT = "Document"
    LANGUAGE = "Language"
    DOWNLOAD = "Download"
    QUESTION = "Question"
    SPEAKERS = "Speakers"
    DATE_TIME = "DateTime"
    FONT_SIZE = "FontSize"
    HOME_FILL = "HomeFill"
    PAGE_LEFT = "PageLeft"
    SAVE_COPY = "SaveCopy"
    SEND_FILL = "SendFill"
    SKIP_BACK = "SkipBack"
    SPEED_OFF = "SpeedOff"
    ALIGNMENT = "Alignment"
    BLUETOOTH = "Bluetooth"
    COMPLETED = "Completed"
    CONSTRACT = "Constract"
    HEADPHONE = "Headphone"
    MEGAPHONE = "Megaphone"
    PROJECTOR = "Projector"
    EDUCATION = "Education"
    LEFT_ARROW = "LeftArrow"
    ERASE_TOOL = "EraseTool"
    PAGE_RIGHT = "PageRight"
    PLAY_SOLID = "PlaySolid"
    BOOK_SHELF = "BookShelf"
    HIGHTLIGHT = "Highlight"
    FOLDER_ADD = "FolderAdd"
    PAUSE_BOLD = "PauseBold"
    PENCIL_INK = "PencilInk"
    PIE_SINGLE = "PieSingle"
    QUICK_NOTE = "QuickNote"
    SPEED_HIGH = "SpeedHigh"
    STOP_WATCH = "StopWatch"
    ZIP_FOLDER = "ZipFolder"
    BASKETBALL = "Basketball"
    BRIGHTNESS = "Brightness"
    DICTIONARY = "Dictionary"
    MICROPHONE = "Microphone"
    ARROW_DOWN = "ChevronDown"
    FULL_SCREEN = "FullScreen"
    MIX_VOLUMES = "MixVolumes"
    REMOVE_FROM = "RemoveFrom"
    RIGHT_ARROW = "RightArrow"
    QUIET_HOURS  ="QuietHours"
    FINGERPRINT = "Fingerprint"
    APPLICATION = "Application"
    CERTIFICATE = "Certificate"
    TRANSPARENT = "Transparent"
    IMAGE_EXPORT = "ImageExport"
    SPEED_MEDIUM = "SpeedMedium"
    LIBRARY_FILL = "LibraryFill"
    MUSIC_FOLDER = "MusicFolder"
    POWER_BUTTON = "PowerButton"
    SKIP_FORWARD = "SkipForward"
    CARE_UP_SOLID = "CareUpSolid"
    ACCEPT_MEDIUM = "AcceptMedium"
    CANCEL_MEDIUM = "CancelMedium"
    CHEVRON_RIGHT = "ChevronRight"
    CLIPPING_TOOL = "ClippingTool"
    SEARCH_MIRROR = "SearchMirror"
    SHOPPING_CART = "ShoppingCart"
    FONT_INCREASE = "FontIncrease"
    BACK_TO_WINDOW = "BackToWindow"
    COMMAND_PROMPT = "CommandPrompt"
    CLOUD_DOWNLOAD = "CloudDownload"
    DICTIONARY_ADD = "DictionaryAdd"
    CARE_DOWN_SOLID = "CareDownSolid"
    CARE_LEFT_SOLID = "CareLeftSolid"
    CLEAR_SELECTION = "ClearSelection"
    DEVELOPER_TOOLS = "DeveloperTools"
    BACKGROUND_FILL = "BackgroundColor"
    CARE_RIGHT_SOLID = "CareRightSolid"
    CHEVRON_DOWN_MED = "ChevronDownMed"
    CHEVRON_RIGHT_MED = "ChevronRightMed"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"
    EXPRESSIVE_INPUT_ENTRY = "ExpressiveInputEntry"

    def path(self, theme=Theme.AUTO):
        return f':/qfluentwidgets/images/icons/{self.value}_{getIconColor(theme)}.svg'


class Icon(QIcon):
    """图标包装类
    对 FluentIconBase 或 QIcon 进行统一包装，提供与主题系统集成的图标对象，可在控件中直接使用并支持主题变更时自动刷新
    """

    def __init__(self, fluentIcon: FluentIcon):
        """初始化图标包装类
        Args:
            fluentIcon: 要包装的图标对象，可以是 FluentIconBase 枚举成员或 QIcon 实例
        """
        super().__init__(fluentIcon.path())
        self.fluentIcon = fluentIcon


def toQIcon(icon: Union[QIcon, FluentIconBase, str]) -> QIcon:
    """将图标转换为 QIcon

    Args:
        icon: 要转换的图标

    Returns:
        QIcon 对象
    """
    if isinstance(icon, str):
        return QIcon(icon)

    if isinstance(icon, FluentIconBase):
        return icon.icon()

    return icon


class Action(QAction):
    """Fluent Action
    继承自 QAction 并提供 Fluent 风格图标支持，可接受 FluentIcon 作为图标并自动跟随主题切换颜色，适用于菜单栏、工具栏和右键菜单等场景
    构造函数重载:
        * Action(parent: QObject = None, **kwargs)
        * Action(text: str, parent: QObject = None, **kwargs)
        * Action(icon: QIcon | FluentIconBase, text: str, parent: QObject = None, **kwargs)
    """

    @singledispatchmethod
    def __init__(self, parent: QObject = None, **kwargs):
        """初始化动作
        Args:
            parent: 父级 QObject
            **kwargs: 其他关键字参数，支持传入 text、icon、shortcut、triggered 等 QAction 属性进行快捷初始化
        """
        super().__init__(parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, text: str, parent: QObject = None, **kwargs):
        super().__init__(text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: QIcon, text: str, parent: QObject = None, **kwargs):
        super().__init__(icon, text, parent, **kwargs)
        self.fluentIcon = None

    @__init__.register
    def _(self, icon: FluentIconBase, text: str, parent: QObject = None, **kwargs):
        super().__init__(icon.icon(), text, parent, **kwargs)
        self.fluentIcon = icon

    def icon(self) -> QIcon:
        if self.fluentIcon:
            return Icon(self.fluentIcon)

        return super().icon()

    def setIcon(self, icon: Union[FluentIconBase, QIcon]):
        if isinstance(icon, FluentIconBase):
            self.fluentIcon = icon
            icon = icon.icon()

        super().setIcon(icon)