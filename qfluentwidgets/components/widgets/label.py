# coding: utf-8

"""标签组件模块，提供文本标签、图像标签、超链接标签和头像等常用显示控件
包含从 Caption 到 Display 多种层级的文本标签，以及支持高 DPI 显示的图像标签
适用于构建 Fluent Design 风格的界面信息展示层
"""

from typing import List, Union

from PySide6.QtCore import Qt, Property, QPoint, Signal, QSize, QRectF, QUrl
from PySide6.QtGui import (QPainter, QPixmap, QPalette, QColor, QFont, QImage, QPainterPath,
                         QImageReader, QBrush, QMovie, QDesktopServices)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QWidget, QPushButton, QApplication

from ...common.exception_handler import exceptionHandler
from ...common.overload import singledispatchmethod
from ...common.font import setFont, getFont, fontPixelSize
from ...common.style_sheet import FluentStyleSheet, setCustomStyleSheet, setCustomStyleSheet
from ...common.config import qconfig, isDarkTheme
from .menu import LabelContextMenu


class PixmapLabel(QLabel):
    """用于显示高 DPI 图像的标签
    通过自动识别设备像素比来缩放 QPixmap，确保在高分屏上图像依然清晰锐利
    适合用于展示图标、插图、照片等需要保持视觉质量的静态图像
    """

    def __init__(self, parent=None):
        """初始化标签
        Args:
            parent: 父级 QWidget，默认为 None。指定父窗口后标签会随父窗口生命周期自动管理并跟随布局
        """
        super().__init__(parent)
        self.__pixmap = QPixmap()

    def setPixmap(self, pixmap: QPixmap):
        self.__pixmap = pixmap
        self.setFixedSize(pixmap.size())
        self.update()

    def pixmap(self):
        return self.__pixmap

    def paintEvent(self, e):
        if self.__pixmap.isNull():
            return super().paintEvent(e)

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        painter.setPen(Qt.NoPen)
        painter.drawPixmap(self.rect(), self.__pixmap)


class FluentLabelBase(QLabel):
    """Fluent 标签基类
    定义了 Fluent Design 风格文本标签的基础样式与行为，提供统一的主题色切换和字体管理能力
    其子类涵盖 Caption、Body、Title 等多种文本层级，可直接用于界面文本展示
    通常不应直接实例化此类，而应使用具体层级的子类
    
    构造函数重载:
        * FluentLabelBase(parent: QWidget = None)
        * FluentLabelBase(text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化标签基类
        Args:
            parent: 父级 QWidget，默认为 None。提供父窗口时标签会被纳入父窗口的控件树和布局体系
        """
        super().__init__(parent)
        self._init()

    @__init__.register
    def _(self, text: str, parent: QWidget = None):
        self.__init__(parent)
        self.setText(text)

    def _init(self):
        FluentStyleSheet.LABEL.apply(self)
        self.setFont(self.getFont())
        self.setTextColor()
        qconfig.themeChanged.connect(lambda: self.setTextColor(self.lightColor, self.darkColor))

        self.customContextMenuRequested.connect(self._onContextMenuRequested)
        return self

    def getFont(self):
        raise NotImplementedError

    @exceptionHandler()
    def setTextColor(self, light=QColor(0, 0, 0), dark=QColor(255, 255, 255)):
        """ 设置标签的文本颜色

        Args:
            light: 浅色模式下的文本颜色，支持 QColor、Qt.GlobalColor 或 str
            dark: 深色模式下的文本颜色，支持 QColor、Qt.GlobalColor 或 str
        """
        self._lightColor = QColor(light)
        self._darkColor = QColor(dark)

        setCustomStyleSheet(
            self,
            f"FluentLabelBase{{color:{self.lightColor.name(QColor.NameFormat.HexArgb)}}}",
            f"FluentLabelBase{{color:{self.darkColor.name(QColor.NameFormat.HexArgb)}}}"
        )

    @Property(QColor)
    def lightColor(self):
        return self._lightColor

    @lightColor.setter
    def lightColor(self, color: QColor):
        self.setTextColor(color, self.darkColor)

    @Property(QColor)
    def darkColor(self):
        return self._darkColor

    @darkColor.setter
    def darkColor(self, color: QColor):
        self.setTextColor(self.lightColor, color)

    @Property(int)
    def pixelFontSize(self):
        return fontPixelSize(self.font())

    @pixelFontSize.setter
    def pixelFontSize(self, size: int):
        font = self.font()
        dpi = QGuiApplication.primaryScreen().logicalDotsPerInchY() if QGuiApplication.instance() else 96.0
        font.setPointSizeF(size * 72 / (dpi or 96.0))
        self.setFont(font)

    @Property(bool)
    def strikeOut(self):
        return self.font().strikeOut()

    @strikeOut.setter
    def strikeOut(self, isStrikeOut: bool):
        font = self.font()
        font.setStrikeOut(isStrikeOut)
        self.setFont(font)

    @Property(bool)
    def underline(self):
        return self.font().underline()

    @underline.setter
    def underline(self, isUnderline: bool):
        font = self.font()
        font.setStyle()
        font.setUnderline(isUnderline)
        self.setFont(font)

    def _onContextMenuRequested(self, pos):
        menu = LabelContextMenu(parent=self)
        menu.exec(self.mapToGlobal(pos))


class CaptionLabel(FluentLabelBase):
    """Caption 文本标签
    用于展示说明性、辅助性的小字号文本，如图片注释、表单提示、次要信息
    字体尺寸较小，视觉权重低，适合在需要弱化信息层级的场景中使用
    
    构造函数重载:
        * CaptionLabel(parent: QWidget = None)
        * CaptionLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(12)


class BodyLabel(FluentLabelBase):
    """Body 文本标签
    用于展示正文或常规段落内容，是界面中最常用的标准文本层级
    适合用于说明文字、列表内容、对话消息等需要长时间阅读的场景
    
    构造函数重载:
        * BodyLabel(parent: QWidget = None)
        * BodyLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(14)


class StrongBodyLabel(FluentLabelBase):
    """Strong body 文本标签
    在 Body 文本基础上加粗显示，用于突出正文中的关键段落或强调性内容
    适合用作列表标题、摘要、选中项文本等需要吸引视觉注意的常规信息
    
    构造函数重载:
        * StrongBodyLabel(parent: QWidget = None)
        * StrongBodyLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(14, QFont.DemiBold)


class SubtitleLabel(FluentLabelBase):
    """Subtitle 文本标签
    用于展示区块副标题或卡片标题，字号介于 Body 与 Title 之间
    适合划分页面内的内容模块，帮助用户快速定位信息段落
    
    构造函数重载:
        * SubtitleLabel(parent: QWidget = None)
        * SubtitleLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(20, QFont.DemiBold)


class TitleLabel(FluentLabelBase):
    """标题文本标签
    用于展示页面标题或主要区域标题，具有较大的字号和视觉权重
    通常放在页面顶部或对话框头部，作为当前视图的核心信息标识
    
    构造函数重载:
        * TitleLabel(parent: QWidget = None)
        * TitleLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(28, QFont.DemiBold)


class LargeTitleLabel(FluentLabelBase):
    """Large 标题文本标签
    提供比 Title 更大的字号，用于首页大标题、欢迎页核心标语等强视觉场景
    由于字号极大，应避免在常规弹窗或紧凑布局中使用，防止占用过多空间
    
    构造函数重载:
        * LargeTitleLabel(parent: QWidget = None)
        * LargeTitleLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(40, QFont.DemiBold)


class DisplayLabel(FluentLabelBase):
    """Display 文本标签
    用于展示超大号强调文本，如数据仪表中的核心指标、计数、状态码等
    字号最大，视觉冲击力最强，适合在需要第一时间抓取用户注意力的场景使用
    
    构造函数重载:
        * DisplayLabel(parent: QWidget = None)
        * DisplayLabel(text: str, parent: QWidget = None)
    """

    def getFont(self):
        return getFont(68, QFont.DemiBold)


class ImageLabel(QLabel):
    """图像标签
    支持从文件路径、QImage 或 QPixmap 加载并展示图像，可自动适应高 DPI 显示
    常用于用户头像、商品图片、预览缩略图等需要直接展示图像内容的场景
    
    构造函数重载:
        * ImageLabel(parent: QWidget = None)
        * ImageLabel(image: str | QImage | QPixmap, parent: QWidget = None)
    """

    clicked = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
        """初始化图像标签
        Args:
            parent: 父级 QWidget，默认为 None。设置父窗口后图像标签将跟随父窗口进行内存管理和界面布局
        """
        super().__init__(parent)
        self.image = QImage()
        self.setBorderRadius(0, 0, 0, 0)
        self._postInit()

    @__init__.register
    def _(self, image: str, parent=None):
        self.__init__(parent)
        self.setImage(image)

    @__init__.register
    def _(self, image: QImage, parent=None):
        self.__init__(parent)
        self.setImage(image)

    @__init__.register
    def _(self, image: QPixmap, parent=None):
        self.__init__(parent)
        self.setImage(image)

    def _postInit(self):
        pass

    def _onFrameChanged(self, index: int):
        self.image = self.movie().currentImage()
        self.update()

    def setBorderRadius(self, topLeft: int, topRight: int, bottomLeft: int, bottomRight: int):
        """ 设置图像的圆角半径

        Args:
            topLeft: 左上角圆角半径
            topRight: 右上角圆角半径
            bottomLeft: 左下角圆角半径
            bottomRight: 右下角圆角半径
        """
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomLeftRadius = bottomLeft
        self._bottomRightRadius = bottomRight
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        """ 设置标签的图像

        Args:
            image: 图像路径、QPixmap 或 QImage
        """
        self.image = image or QImage()

        if isinstance(image, str):
            reader = QImageReader(image)
            if reader.supportsAnimation():
                self.setMovie(QMovie(image))
            else:
                self.image = reader.read()
        elif isinstance(image, QPixmap):
            self.image = image.toImage()

        self.setFixedSize(self.image.size())
        self.update()

    def scaledToWidth(self, width: int):
        if self.isNull():
            return

        h = int(width / self.image.width() * self.image.height())
        self.setFixedSize(width, h)

        if self.movie():
            self.movie().setScaledSize(QSize(width, h))

    def scaledToHeight(self, height: int):
        if self.isNull():
            return

        w = int(height / self.image.height() * self.image.width())
        self.setFixedSize(w, height)

        if self.movie():
            self.movie().setScaledSize(QSize(w, height))

    def setScaledSize(self, size: QSize):
        if self.isNull():
            return

        self.setFixedSize(size)

        if self.movie():
            self.movie().setScaledSize(size)

    def isNull(self):
        return self.image.isNull()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

    def setPixmap(self, pixmap: QPixmap):
        self.setImage(pixmap)

    def pixmap(self) -> QPixmap:
        return QPixmap.fromImage(self.image)

    def setMovie(self, movie: QMovie):
        super().setMovie(movie)
        self.movie().start()
        self.image = self.movie().currentImage()
        self.movie().frameChanged.connect(self._onFrameChanged)

    def paintEvent(self, e):
        if self.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        path = QPainterPath()
        w, h = self.width(), self.height()

        # top line
        path.moveTo(self.topLeftRadius, 0)
        path.lineTo(w - self.topRightRadius, 0)

        # top right arc
        d = self.topRightRadius * 2
        path.arcTo(w - d, 0, d, d, 90, -90)

        # right line
        path.lineTo(w, h - self.bottomRightRadius)

        # bottom right arc
        d = self.bottomRightRadius * 2
        path.arcTo(w - d, h - d, d, d, 0, -90)

        # bottom line
        path.lineTo(self.bottomLeftRadius, h)

        # bottom left arc
        d = self.bottomLeftRadius * 2
        path.arcTo(0, h - d, d, d, -90, -90)

        # left line
        path.lineTo(0, self.topLeftRadius)

        # top left arc
        d = self.topLeftRadius * 2
        path.arcTo(0, 0, d, d, -180, -90)

        # 绘制图像
        image = self.image.scaled(
            self.size()*self.devicePixelRatioF(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.drawImage(self.rect(), image)

    @Property(int)
    def topLeftRadius(self):
        return self._topLeftRadius

    @topLeftRadius.setter
    def topLeftRadius(self, radius: int):
        self.setBorderRadius(radius, self.topRightRadius, self.bottomLeftRadius, self.bottomRightRadius)

    @Property(int)
    def topRightRadius(self):
        return self._topRightRadius

    @topRightRadius.setter
    def topRightRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, radius, self.bottomLeftRadius, self.bottomRightRadius)

    @Property(int)
    def bottomLeftRadius(self):
        return self._bottomLeftRadius

    @bottomLeftRadius.setter
    def bottomLeftRadius(self, radius: int):
        self.setBorderRadius(self.topLeftRadius, self.topRightRadius, radius, self.bottomRightRadius)

    @Property(int)
    def bottomRightRadius(self):
        return self._bottomRightRadius

    @bottomRightRadius.setter
    def bottomRightRadius(self, radius: int):
        self.setBorderRadius(
            self.topLeftRadius, self.topRightRadius, self.bottomLeftRadius, radius)


class AvatarWidget(ImageLabel):
    """头像部件
    专门用于展示用户头像的圆形裁剪图像控件，支持从文件路径、QImage 或 QPixmap 加载
    广泛应用于用户信息卡片、评论区、聊天列表、设置页等需要标识用户身份的位置
    
    构造函数重载:
        * AvatarWidget(parent: QWidget = None)
        * AvatarWidget(image: str | QImage | QPixmap, parent: QWidget = None)
    """

    def _postInit(self):
        self.setRadius(48)
        self.lightBackgroundColor = QColor(0, 0, 0, 50)
        self.darkBackgroundColor = QColor(255, 255, 255, 50)

    def getRadius(self):
        return self._radius

    def setRadius(self, radius: int):
        self._radius = radius
        setFont(self, radius)
        self.setFixedSize(2*radius, 2*radius)
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        super().setImage(image)
        self.setRadius(self.radius)

    def setBackgroundColor(self, light: QColor, dark: QColor):
        self.lightBackgroundColor = QColor(light)
        self.darkBackgroundColor = QColor(light)
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if not self.isNull():
            self._drawImageAvatar(painter)
        else:
            self._drawTextAvatar(painter)

    def _drawImageAvatar(self, painter: QPainter):
        # center crop 图像
        image = self.image.scaled(
            self.size()*self.devicePixelRatioF(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)  # type: QImage

        iw, ih = image.width(), image.height()
        d = self.getRadius() * 2 * self.devicePixelRatioF()
        x, y = (iw - d) / 2, (ih - d) / 2
        image = image.copy(int(x), int(y), int(d), int(d))

        # 绘制图像
        path = QPainterPath()
        path.addEllipse(QRectF(self.rect()))

        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.drawImage(self.rect(), image)

    def _drawTextAvatar(self, painter: QPainter):
        if not self.text():
            return

        painter.setBrush(self.darkBackgroundColor if isDarkTheme() else self.lightBackgroundColor)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(self.rect()))

        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text()[0].upper())

    radius = Property(int, getRadius, setRadius)


class HyperlinkLabel(QPushButton):
    """超链接标签
    展示可点击的外部链接文本，点击后会调用系统默认浏览器打开目标网址
    适合用于关于页面、授权信息、帮助文档等需要引导用户访问外部网页的场景
    
    构造函数重载:
        * HyperlinkLabel(parent: QWidget = None)
        * HyperlinkLabel(text: str, parent: QWidget = None)
        * HyperlinkLabel(url: QUrl, text: str, parent: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化超链接标签
        Args:
            parent: 父级 QWidget，默认为 None。指定父窗口后超链接标签会被纳入父控件的布局与事件分发体系
        """
        super().__init__(parent=parent)
        self._url = QUrl()

        setFont(self, 14)
        self.setUnderlineVisible(False)
        FluentStyleSheet.LABEL.apply(self)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, text: str, parent=None):
        self.__init__(parent)
        self.setText(text)

    @__init__.register
    def _(self, url: QUrl, text: str, parent=None):
        self.__init__(parent)
        self.setText(text)
        self._url = url

    def getUrl(self) -> QUrl:
        return self._url

    def setUrl(self, url: Union[QUrl, str]):
        self._url = QUrl(url)

    def isUnderlineVisible(self):
        return self._isUnderlineVisible

    def setUnderlineVisible(self, isVisible: bool):
        self._isUnderlineVisible = isVisible
        self.setProperty('underline', isVisible)
        self.setStyle(QApplication.style())

    def _onClicked(self):
        if self.getUrl().isValid():
            QDesktopServices.openUrl(self.getUrl())

    url = Property(QUrl, getUrl, setUrl)
    underlineVisible = Property(bool, isUnderlineVisible, setUnderlineVisible)