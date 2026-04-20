# coding: utf-8
"""信息徽标组件库

  提供数字徽标、文本徽标、圆点徽标和图标徽标等多种形态，以及用于自动挂载和定位的管理器类

  适用于未读消息计数、状态标记、新功能提示等场景，支持通过 InfoLevel 调整视觉层级，通过 InfoBadgePosition 控制挂载方位
"""

from enum import Enum
from typing import Union

from PySide6.QtCore import Qt, QEvent, QRectF, QPoint, QObject, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtWidgets import QLabel, QWidget, QSizePolicy

from ...common.font import setFont
from ...common.icon import drawIcon, FluentIconBase, toQIcon
from ...common.overload import singledispatchmethod
from ...common.style_sheet import themeColor, FluentStyleSheet, isDarkTheme, Theme


class InfoLevel(Enum):
    """信息层级枚举
    
      定义徽标的视觉优先级和配色方案，用于区分普通提示、成功状态、警告信息及严重错误等不同语义级别
    """
    INFOAMTION = 'Info'
    SUCCESS = 'Success'
    ATTENTION = 'Attension'
    WARNING = "Warning"
    ERROR = "Error"


class InfoBadgePosition(Enum):
    """徽标挂载位置枚举
    
      定义徽标相对于目标控件的方位，配合 InfoBadgeManager 使用以自动计算并同步徽标的几何位置
    """
    TOP_RIGHT = 0
    BOTTOM_RIGHT = 1
    RIGHT = 2
    TOP_LEFT = 3
    BOTTOM_LEFT = 4
    LEFT = 5
    NAVIGATION_ITEM = 6


class InfoBadge(QLabel):
    """信息徽标控件
    
      以小型标签形式展示文本、整数、浮点数或百分比等内容，常用于消息计数、状态标记和数据提示
    
      构造函数重载:
          * InfoBadge(parent: QWidget = None, level=InfoLevel.ATTENTION)
          * InfoBadge(text: str, parent: QWidget = None, level=InfoLevel.ATTENTION)
          * InfoBadge(num: int, parent: QWidget = None, level=InfoLevel.ATTENTION)
          * InfoBadge(num: float, parent: QWidget = None, level=InfoLevel.ATTENTION)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None, level=InfoLevel.ATTENTION):
        """初始化信息徽标
        
          Args:
              parent: 父控件，为 None 时徽标作为独立浮窗
              level: 信息层级，决定徽标的主题色，默认值为 InfoLevel.ATTENTION，影响背景与文字配色
        """
        super().__init__(parent=parent)
        self.level = InfoLevel.INFOAMTION
        self.lightBackgroundColor = None
        self.darkBackgroundColor = None
        self.manager = None  # type: InfoBadgeManager
        self.setLevel(level)

        setFont(self, 11)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        FluentStyleSheet.INFO_BADGE.apply(self)

    @__init__.register
    def _(self, text: str, parent: QWidget = None, level=InfoLevel.ATTENTION):
        self.__init__(parent, level)
        self.setText(text)

    @__init__.register
    def _(self, num: int, parent: QWidget = None, level=InfoLevel.ATTENTION):
        self.__init__(parent, level)
        self.setNum(num)

    @__init__.register
    def _(self, num: float, parent: QWidget = None, level=InfoLevel.ATTENTION):
        self.__init__(parent, level)
        self.setNum(num)

    def setLevel(self, level: InfoLevel):
        """设置信息层级

        Args:
            level: 信息层级
        """
        if level == self.level:
            return

        self.level = level
        self.setProperty('level', level.value)
        self.update()

    def setProperty(self, name: str, value):
        super().setProperty(name, value)
        if name != "level":
            return

        values = [i.value for i in InfoLevel._member_map_.values()]
        if value in values:
            self.level = InfoLevel(value)

    def setCustomBackgroundColor(self, light, dark):
        """设置自定义背景色

        Args:
            light: 亮色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
        """
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(dark)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._backgroundColor())

        r = self.height() / 2
        painter.drawRoundedRect(self.rect(), r, r)

        super().paintEvent(e)

    def _backgroundColor(self):
        isDark = isDarkTheme()

        if self.lightBackgroundColor:
            color = self.darkBackgroundColor if isDark else self.lightBackgroundColor
        elif self.level == InfoLevel.INFOAMTION:
            color = QColor(157, 157, 157) if isDark else QColor(138, 138, 138)
        elif self.level == InfoLevel.SUCCESS:
            color = QColor(108, 203, 95) if isDark else QColor(15, 123, 15)
        elif self.level == InfoLevel.ATTENTION:
            color = themeColor()
        elif self.level == InfoLevel.WARNING:
            color = QColor(255, 244, 206) if isDark else QColor(157, 93, 0)
        else:
            color = QColor(255, 153, 164) if isDark else QColor(196, 43, 28)

        return color

    @classmethod
    def make(cls, text: Union[str, float], parent=None, level=InfoLevel.INFOAMTION, target: QWidget = None,
             position=InfoBadgePosition.TOP_RIGHT):
        w = InfoBadge(text, parent, level)
        w.adjustSize()

        if target:
            w.manager = InfoBadgeManager.make(position, target, w)
            w.move(w.manager.position())

        return w

    @classmethod
    def info(cls, text: Union[str, float], parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(text, parent, InfoLevel.INFOAMTION, target, position)

    @classmethod
    def success(cls, text: Union[str, float], parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(text, parent, InfoLevel.SUCCESS, target, position)

    @classmethod
    def attension(cls, text: Union[str, float], parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(text, parent, InfoLevel.ATTENTION, target, position)

    @classmethod
    def warning(cls, text: Union[str, float], parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(text, parent, InfoLevel.WARNING, target, position)

    @classmethod
    def error(cls, text: Union[str, float], parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(text, parent, InfoLevel.ERROR, target, position)

    @classmethod
    def custom(cls, text: Union[str, float], light: QColor, dark: QColor, parent=None, target: QWidget = None,
               position=InfoBadgePosition.TOP_RIGHT):
        """创建使用自定义背景色的徽标

        Args:
            text: 徽标文本，支持 str 或 float
            light: 亮色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            parent: 父部件
            target: 要显示徽标的目标部件
            position: 相对于目标部件的位置
        """
        w = cls.make(text, parent, target=target, position=position)
        w.setCustomBackgroundColor(light, dark)
        return w


class DotInfoBadge(InfoBadge):
    """点状信息徽标
    
      仅显示纯色圆点而不展示任何文本或数字，适用于需要低干扰度状态提示的场景，如未读标记、在线状态指示或操作进度标识
    """

    def __init__(self, parent=None, level=InfoLevel.ATTENTION):
        """初始化点状徽标
        
          Args:
              parent: 父控件
              level: 信息层级，决定圆点的主题色，默认值为 InfoLevel.ATTENTION，影响填充配色
        """
        super().__init__(parent, level)
        self.setFixedSize(4, 4)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._backgroundColor())
        painter.drawEllipse(self.rect())

    @classmethod
    def make(cls, parent=None, level=InfoLevel.INFOAMTION, target: QWidget = None,
             position=InfoBadgePosition.TOP_RIGHT):
        w = DotInfoBadge(parent, level)

        if target:
            w.manager = InfoBadgeManager.make(position, target, w)
            w.move(w.manager.position())

        return w

    @classmethod
    def info(cls, parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(parent, InfoLevel.INFOAMTION, target, position)

    @classmethod
    def success(cls, parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(parent, InfoLevel.SUCCESS, target, position)

    @classmethod
    def attension(cls, parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(parent, InfoLevel.ATTENTION, target, position)

    @classmethod
    def warning(cls, parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(parent, InfoLevel.WARNING, target, position)

    @classmethod
    def error(cls, parent=None, target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(parent, InfoLevel.ERROR, target, position)

    @classmethod
    def custom(cls, light: QColor, dark: QColor, parent=None, target: QWidget = None,
               position=InfoBadgePosition.TOP_RIGHT):
        """创建使用自定义背景色的点状徽标

        Args:
            light: 亮色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            parent: 父部件
            target: 要显示徽标的目标部件
            position: 相对于目标部件的位置
        """
        w = cls.make(parent, target=target, position=position)
        w.setCustomBackgroundColor(light, dark)
        return w


class IconInfoBadge(InfoBadge):
    """图标徽标控件
    
      以图标形式直观表达状态或类别，相比文本徽标更具辨识度，适合空间受限或需要统一图标的场景
    
      构造函数重载:
          * IconInfoBadge(parent: QWidget = None, level=InfoLevel.ATTENTION)
          * IconInfoBadge(icon: QIcon | str | FluentIconBase, parent: QWidget = None, level=InfoLevel.ATTENTION)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None, level=InfoLevel.ATTENTION):
        """初始化图标徽标
        
          Args:
              parent: 父控件
              level: 信息层级，决定图标与背景的主题色，默认值为 InfoLevel.ATTENTION，影响整体配色方案
        """
        super().__init__(parent=parent, level=level)
        self._icon = QIcon()
        self._iconSize = QSize(8, 8)
        self.setFixedSize(16, 16)

    @__init__.register
    def _(self, icon: FluentIconBase, parent: QWidget = None, level=InfoLevel.ATTENTION):
        self.__init__(parent, level)
        self.setIcon(icon)

    @__init__.register
    def _(self, icon: QIcon, parent: QWidget = None, level=InfoLevel.ATTENTION):
        self.__init__(parent, level)
        self.setIcon(icon)

    def setIcon(self, icon: Union[QIcon, FluentIconBase, str]):
        """设置信息徽标图标"""
        self._icon = icon
        self.update()

    def icon(self):
        return toQIcon(self._icon)

    def iconSize(self):
        return self._iconSize

    def setIconSize(self, size: QSize):
        self._iconSize = size
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._backgroundColor())
        painter.drawEllipse(self.rect())

        iw, ih = self.iconSize().width(), self.iconSize().height()
        x, y = (self.width() - iw) / 2, (self.width() - ih) / 2
        rect = QRectF(x, y, iw, ih)

        if isinstance(self._icon, FluentIconBase):
            theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
            self._icon.render(painter, rect, theme)
        else:
            drawIcon(self._icon, painter, rect)

    @classmethod
    def make(cls, icon: Union[QIcon, FluentIconBase], parent=None, level=InfoLevel.INFOAMTION, target: QWidget = None,
             position=InfoBadgePosition.TOP_RIGHT):
        w = IconInfoBadge(icon, parent, level)

        if target:
            w.manager = InfoBadgeManager.make(position, target, w)
            w.move(w.manager.position())

        return w

    @classmethod
    def info(cls, icon: Union[QIcon, FluentIconBase], parent=None, target: QWidget = None,
             position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(icon, parent, InfoLevel.INFOAMTION, target, position)

    @classmethod
    def success(cls, icon: Union[QIcon, FluentIconBase], parent=None, target: QWidget = None,
                position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(icon, parent, InfoLevel.SUCCESS, target, position)

    @classmethod
    def attension(cls, icon: Union[QIcon, FluentIconBase], parent=None, target: QWidget = None,
                  position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(icon, parent, InfoLevel.ATTENTION, target, position)

    @classmethod
    def warning(cls, icon: Union[QIcon, FluentIconBase], parent=None, target: QWidget = None,
                position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(icon, parent, InfoLevel.WARNING, target, position)

    @classmethod
    def error(cls, icon: Union[QIcon, FluentIconBase], parent=None, target: QWidget = None,
              position=InfoBadgePosition.TOP_RIGHT):
        return cls.make(icon, parent, InfoLevel.ERROR, target, position)

    @classmethod
    def custom(cls, icon: Union[QIcon, FluentIconBase], light: QColor, dark: QColor, parent=None,
               target: QWidget = None, position=InfoBadgePosition.TOP_RIGHT):
        """创建使用自定义背景色的图标徽标

        Args:
            icon: 徽标图标
            light: 亮色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            dark: 暗色主题下的背景色，支持 str、Qt.GlobalColor 或 QColor
            parent: 父部件
            target: 要显示徽标的目标部件
            position: 相对于目标部件的位置
        """
        w = cls.make(icon, parent, target=target, position=position)
        w.setCustomBackgroundColor(light, dark)
        return w


class InfoBadgeManager(QObject):
    """信息徽标管理器基类
    
      负责将徽标实例附加到目标控件并监听其几何变化，自动维护徽标的显示位置
    
      通常情况下不应直接实例化此类，而应使用 TopRightInfoBadgeManager 等子类来指定具体的挂载方位
    """

    managers = {}

    def __init__(self, target: QWidget, badge: InfoBadge):
        """初始化徽标管理器
        
          Args:
              target: 目标控件，徽标将围绕该控件进行定位并同步其几何变化
              badge: 要挂载的徽标实例，应为 InfoBadge、DotInfoBadge 或 IconInfoBadge 的对象
        """
        super().__init__()
        self.target = target
        self.badge = badge

        self.target.installEventFilter(self)

    def eventFilter(self, obj, e: QEvent):
        if obj is self.target:
            if e.type() in [QEvent.Resize, QEvent.Move]:
                self.badge.move(self.position())

        return super().eventFilter(obj, e)

    @classmethod
    def register(cls, name):
        """注册信息徽标位置管理器

        Args:
            name: 管理器名称，必须唯一
        """
        def wrapper(Manager):
            if name not in cls.managers:
                cls.managers[name] = Manager

            return Manager

        return wrapper

    @classmethod
    def make(cls, position: InfoBadgePosition, target: QWidget, badge: InfoBadge):
        """创建信息徽标位置管理器

        Args:
            position: 徽标位置
            target: 目标部件
            badge: 信息徽标实例

        Raises:
            ValueError: 如果 position 不是有效的位置类型
        """
        if position not in cls.managers:
            raise ValueError(f'`{position}` is an invalid animation type.')

        return cls.managers[position](target, badge)

    def position(self):
        """返回信息徽标的位置"""
        return QPoint()


@InfoBadgeManager.register(InfoBadgePosition.TOP_RIGHT)
class TopRightInfoBadgeManager(InfoBadgeManager):
    """右上角信息徽标管理器
    
      将徽标固定于目标控件的右上角，是最常见的消息未读标记和新内容提示位置，徽标会随目标控件的移动和大小变化自动同步更新
    """

    def position(self):
        pos = self.target.geometry().topRight()
        x = pos.x() - self.badge.width() // 2
        y = pos.y() - self.badge.height() // 2
        return QPoint(x, y)


@InfoBadgeManager.register(InfoBadgePosition.RIGHT)
class RightInfoBadgeManager(InfoBadgeManager):
    """右侧信息徽标管理器
    
      将徽标固定于目标控件右侧居中位置，适合在横向布局中作为辅助说明或侧边状态标记
    """

    def position(self):
        x = self.target.geometry().right() - self.badge.width() // 2
        y = self.target.geometry().center().y() - self.badge.height() // 2
        return QPoint(x, y)


@InfoBadgeManager.register(InfoBadgePosition.BOTTOM_RIGHT)
class BottomRightInfoBadgeManager(InfoBadgeManager):
    """右下角信息徽标管理器
    
      将徽标固定于目标控件的右下角，适用于对话框、卡片或特定容器组件中的状态展示
    """

    def position(self):
        pos = self.target.geometry().bottomRight()
        x = pos.x() - self.badge.width() // 2
        y = pos.y() - self.badge.height() // 2
        return QPoint(x, y)


@InfoBadgeManager.register(InfoBadgePosition.TOP_LEFT)
class TopLeftInfoBadgeManager(InfoBadgeManager):
    """左上角信息徽标管理器
    
      将徽标固定于目标控件的左上角，适用于从左侧开始阅读的场景或特殊布局需求
    """

    def position(self):
        x = self.target.x() - self.badge.width() // 2
        y = self.target.y() - self.badge.height() // 2
        return QPoint(x, y)


@InfoBadgeManager.register(InfoBadgePosition.LEFT)
class LeftInfoBadgeManager(InfoBadgeManager):
    """左侧信息徽标管理器
    
      将徽标固定于目标控件左侧居中位置，适合在纵向列表或左侧导航项旁显示状态标记
    """

    def position(self):
        x = self.target.x() - self.badge.width() // 2
        y = self.target.geometry().center().y() - self.badge.height() // 2
        return QPoint(x, y)


@InfoBadgeManager.register(InfoBadgePosition.BOTTOM_LEFT)
class BottomLeftInfoBadgeManager(InfoBadgeManager):
    """左下角信息徽标管理器
    
      将徽标固定于目标控件的左下角，可用于左下角优先级提示或特殊方位标记
    """

    def position(self):
        pos = self.target.geometry().bottomLeft()
        x = pos.x() - self.badge.width() // 2
        y = pos.y() - self.badge.height() // 2
        return QPoint(x, y)