# coding: utf-8
"""配置管理模块
提供配置项定义、校验、序列化及主题管理等功能，通过 QConfig 及其子类可集中管理应用配置，支持范围约束、选项列表、文件夹路径等多种配置类型，并自动处理配置文件的读写与持久化
"""

import json
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal, qVersion
from PySide6.QtGui import QColor

from .exception_handler import exceptionHandler


_darkdetect = None


def _resolve_system_theme():
    global _darkdetect

    if _darkdetect is None:
        try:
            import darkdetect as _darkdetect_module
        except Exception:
            _darkdetect = False
        else:
            _darkdetect = _darkdetect_module

    if not _darkdetect:
        return Theme.LIGHT

    detected_theme = _darkdetect.theme()
    return Theme(detected_theme) if detected_theme else Theme.LIGHT

class Theme(Enum):
    """应用主题枚举类
    定义了浅色、深色及跟随系统三种主题模式，用于控制应用界面的整体配色风格，可通过 setTheme 方法全局切换
    """

    LIGHT = "Light"
    DARK = "Dark"
    AUTO = "Auto"


class ConfigValidator:
    """配置值校验器基类
    用于验证和修正配置项的输入值，子类需实现 validate 和 correct 方法，分别用于判断值是否合法以及将非法值修正为合法值，在配置项赋值和读取时自动调用
    """

    def validate(self, value):
        """校验值是否合法

        Args:
            value: 待校验的值

        Returns:
            如果值合法则为 True，否则为 False
        """
        return True

    def correct(self, value):
        """修正非法值

        Args:
            value: 待修正的值

        Returns:
            修正后的值
        """
        return value


class RangeValidator(ConfigValidator):
    """范围校验器

    构造函数重载:
        __init__(self, min, max)
    """

    def __init__(self, min, max):
        """初始化范围校验器
        
        Args:
            min: 允许的最小值
            max: 允许的最大值
        """
        self.min = min
        self.max = max
        self.range = (min, max)

    def validate(self, value):
        return self.min <= value <= self.max

    def correct(self, value):
        return min(max(self.min, value), self.max)


class OptionsValidator(ConfigValidator):
    """选项校验器

    构造函数重载:
        __init__(self, options)
    """

    def __init__(self, options):
        """初始化选项校验器
        
        Args:
            options: 允许的选项值列表，配置值必须是其中一项
        """
        if not options:
            raise ValueError("The `options` can't be empty.")

        if isinstance(options, Enum):
            options = options._member_map_.values()

        self.options = list(options)

    def validate(self, value):
        return value in self.options

    def correct(self, value):
        return value if self.validate(value) else self.options[0]


class BoolValidator(OptionsValidator):
    """布尔值校验器

    构造函数重载:
        __init__(self)
    """

    def __init__(self):
        """初始化文件夹校验器，在校验时会自动创建不存在的文件夹路径并将其修正为合法路径"""
        super().__init__([True, False])


class FolderValidator(ConfigValidator):
    """文件夹路径校验器
    确保配置值为有效的文件夹路径，若路径不存在会自动创建文件夹或将值修正为合法路径，适用于需要持久化存储文件目录的配置场景
    """

    def validate(self, value):
        return Path(value).exists()

    def correct(self, value):
        path = Path(value)
        path.mkdir(exist_ok=True, parents=True)
        return str(path.absolute()).replace("\\", "/")


class FolderListValidator(ConfigValidator):
    """文件夹路径列表校验器
    确保配置值为有效的文件夹路径列表，会自动过滤无效路径并创建不存在的文件夹，适用于管理多个存储目录或最近使用文件夹列表的配置场景
    """

    def validate(self, value):
        return all(Path(i).exists() for i in value)

    def correct(self, value: List[str]):
        folders = []
        for folder in value:
            path = Path(folder)
            if path.exists():
                folders.append(str(path.absolute()).replace("\\", "/"))

        return folders


class ColorValidator(ConfigValidator):
    """RGB 颜色校验器

    构造函数重载:
        __init__(self, default)
    """

    def __init__(self, default):
        """初始化文件夹列表校验器
        
        Args:
            default: 默认文件夹路径，当列表为空或校验失败时作为回退值
        """
        self.default = QColor(default)

    def validate(self, color):
        try:
            return QColor(color).isValid()
        except:
            return False

    def correct(self, value):
        return QColor(value) if self.validate(value) else self.default


class ConfigSerializer:
    """配置序列化器基类
    负责配置值在 Python 对象与可存储格式之间的双向转换，子类需实现 serialize 和 deserialize 方法，用于配置文件的读写与持久化
    """

    def serialize(self, value):
        """序列化配置值

        Args:
            value: 待序列化的值

        Returns:
            序列化后的值
        """
        return value

    def deserialize(self, value):
        """反序列化配置值

        Args:
            value: 配置文件中的值

        Returns:
            反序列化后的值
        """
        return value


class EnumSerializer(ConfigSerializer):
    """枚举类序列化器

    构造函数重载:
        __init__(self, enumClass)
    """

    def __init__(self, enumClass):
        """初始化枚举序列化器
        
        Args:
            enumClass: 枚举类类型，用于将配置字符串反序列化为对应的枚举成员
        """
        self.enumClass = enumClass

    def serialize(self, value):
        return value.value

    def deserialize(self, value):
        return self.enumClass(value)


class ColorSerializer(ConfigSerializer):
    """QColor 序列化器
    负责 QColor 对象与十六进制字符串之间的相互转换，适用于需要持久化存储主题色、强调色等颜色配置项的场景
    """

    def serialize(self, value: QColor):
        return value.name(QColor.HexArgb)

    def deserialize(self, value):
        if isinstance(value, list):
            return QColor(*value)

        return QColor(value)


class ConfigItem(QObject):
    """配置项

    构造函数重载:
        __init__(self, group, name, default, validator=None, serializer=None, restart=False)
    """

    valueChanged = Signal(object)

    def __init__(self, group, name, default, validator=None, serializer=None, restart=False):
        """初始化配置项

        Args:
            group (str): 配置分组名称
            name (str): 配置项名称，可以为空
            default: 默认值
            validator (ConfigValidator, optional): 配置校验器，默认为 ConfigValidator
            serializer (ConfigSerializer, optional): 配置序列化器，默认为 ConfigSerializer
            restart (bool, optional): 更新值后是否需要重启应用
        """
        super().__init__()
        self.group = group
        self.name = name
        self.validator = validator or ConfigValidator()
        self.serializer = serializer or ConfigSerializer()
        self.__value = default
        self.value = default
        self.restart = restart
        self.defaultValue = self.validator.correct(default)

    @property
    def value(self):
        """获取配置项的值"""
        return self.__value

    @value.setter
    def value(self, v):
        v = self.validator.correct(v)
        ov = self.__value
        self.__value = v
        if ov != v:
            self.valueChanged.emit(v)

    @property
    def key(self):
        """获取以 `.` 分隔的配置键"""
        return self.group+"."+self.name if self.name else self.group

    def __str__(self):
        return f'{self.__class__.__name__}[value={self.value}]'

    def serialize(self):
        return self.serializer.serialize(self.value)

    def deserializeFrom(self, value):
        self.value = self.serializer.deserialize(value)


class RangeConfigItem(ConfigItem):
    """带数值范围约束的配置项
    配置值必须在指定的最小值和最大值之间，超出范围时会自动修正为边界值，适用于透明度、圆角半径、字体大小等需要限制取值范围的配置场景
    """

    @property
    def range(self):
        """获取配置项允许的取值范围"""
        return self.validator.range

    def __str__(self):
        return f'{self.__class__.__name__}[range={self.range}, value={self.value}]'


class OptionsConfigItem(ConfigItem):
    """带预设选项列表的配置项
    配置值必须是选项列表中的一项，适用于主题模式、语言设置、布局风格等具有固定可选项的配置场景
    """

    @property
    def options(self):
        return self.validator.options

    def __str__(self):
        return f'{self.__class__.__name__}[options={self.options}, value={self.value}]'


class ColorConfigItem(ConfigItem):
    """颜色配置项

    构造函数重载:
        __init__(self, group, name, default, restart=False)
    """

    def __init__(self, group, name, default, restart=False):
        """初始化配置项
        
        Args:
            group: 配置分组名称，用于在配置文件中组织归类
            name: 配置项名称，在同一分组下需唯一
            default: 默认值，当配置文件中不存在该配置时使用此值
            restart: 修改该配置后是否需要重启应用才能生效，默认为 False
        """
        super().__init__(group, name, QColor(default), ColorValidator(default),
                         ColorSerializer(), restart)

    def __str__(self):
        return f'{self.__class__.__name__}[value={self.value.name()}]'


class QConfig(QObject):
    """应用级配置对象

    构造函数重载:
        __init__(self)
    """

    appRestartSig = Signal()
    themeChanged = Signal(Theme)
    themeChangedFinished = Signal()
    themeColorChanged = Signal(QColor)

    themeMode = OptionsConfigItem(
        "QFluentWidgets", "ThemeMode", Theme.LIGHT, OptionsValidator(Theme), EnumSerializer(Theme))
    themeColor = ColorConfigItem("QFluentWidgets", "ThemeColor", '#009faa')
    fontFamilies = ConfigItem("QFluentWidgets", "FontFamilies", ['Segoe UI', 'Microsoft YaHei', 'PingFang SC'])

    def __init__(self):
        """初始化配置管理器，自动加载配置文件并初始化所有已定义的配置项，若配置文件不存在则使用默认值创建"""
        super().__init__()
        self.file = Path("config/config.json")
        self._theme = Theme.LIGHT
        self._cfg = self

    def get(self, item):
        """获取配置项的值

        Args:
            item (ConfigItem): 配置项

        Returns:
            配置项的当前值
        """
        return item.value

    def set(self, item, value, save=True, copy=True):
        """设置配置项的值

        Args:
            item (ConfigItem): 配置项
            value: 要写入的新值
            save (bool, optional): 是否立即保存到配置文件，默认为 True
            copy (bool, optional): 是否对新值执行深拷贝，默认为 True
        """
        if item.value == value:
            return

        try:
            item.value = deepcopy(value) if copy else value
        except:
            item.value = value

        if save:
            self.save()

        if item.restart:
            self._cfg.appRestartSig.emit()

        if item is self._cfg.themeMode:
            self.theme = value
            self._cfg.themeChanged.emit(value)

        if item is self._cfg.themeColor:
            self._cfg.themeColorChanged.emit(value)

    def toDict(self, serialize=True):
        """将配置项转换为 dict

        Args:
            serialize (bool, optional): 是否对值进行序列化，默认为 True

        Returns:
            包含所有配置项的字典
        """
        items = {}
        for name in dir(self._cfg.__class__):
            item = getattr(self._cfg.__class__, name)
            if not isinstance(item, ConfigItem):
                continue

            value = item.serialize() if serialize else item.value
            if not items.get(item.group):
                if not item.name:
                    items[item.group] = value
                else:
                    items[item.group] = {}

            if item.name:
                items[item.group][item.name] = value

        return items

    def save(self):
        """保存配置"""
        self._cfg.file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cfg.file, "w", encoding="utf-8") as f:
            json.dump(self._cfg.toDict(), f, ensure_ascii=False, indent=4)

    @exceptionHandler()
    def load(self, file=None, config=None):
        """加载配置

        Args:
            file (str or Path, optional): JSON 配置文件路径
            config (QConfig, optional): 要初始化的配置对象
        """
        if isinstance(config, QConfig):
            self._cfg = config
            self._cfg.themeChanged.connect(self.themeChanged)

        if isinstance(file, (str, Path)):
            self._cfg.file = Path(file)

        try:
            with open(self._cfg.file, encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            cfg = {}

        items = {}
        for name in dir(self._cfg.__class__):
            item = getattr(self._cfg.__class__, name)
            if isinstance(item, ConfigItem):
                items[item.key] = item

        for k, v in cfg.items():
            if not isinstance(v, dict) and items.get(k) is not None:
                items[k].deserializeFrom(v)
            elif isinstance(v, dict):
                for key, value in v.items():
                    key = k + "." + key
                    if items.get(key) is not None:
                        items[key].deserializeFrom(value)

        self.theme = self.get(self._cfg.themeMode)

    @property
    def theme(self):
        """获取当前主题模式"""
        return self._cfg._theme

    @theme.setter
    def theme(self, t):
        """切换主题，但不修改配置文件"""
        if t == Theme.AUTO:
            t = _resolve_system_theme()

        self._cfg._theme = t


QT_VERSION = tuple([int(v) for v in qVersion().split('.')])
qconfig = QConfig()


def isDarkTheme():
    """返回当前主题是否为暗色模式"""
    return qconfig.theme == Theme.DARK

def theme():
    """获取当前主题"""
    return qconfig.theme

def isDarkThemeMode(theme=Theme.AUTO):
    """判断给定主题模式是否为暗色模式

    Args:
        theme (Theme, optional): 要判断的主题模式，默认为 Theme.AUTO

    Returns:
        如果主题为暗色模式则返回 True，否则返回 False
    """
    return theme == Theme.DARK if theme != Theme.AUTO else isDarkTheme()