# coding: utf-8

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
    """ 标签 用于 high dpi pixmap """

    def __init__(self, parent=None):
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
    """ Fluent 标签 基类

    构造函数
    ------------
    * FluentLabelBase(`父部件`: QWidget = None)
    * FluentLabelBase(`文本`: str, `父部件`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
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
        """ 设置标签的文本 颜色

        参数
        ----------
        亮色, dark: QColor | Qt.GlobalColor | str
            文本颜色 中的 light/dark 模式
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
    """ Caption 文本 标签

    构造函数
    ------------
    * CaptionLabel(`父部件`: QWidget = None)
    * CaptionLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(12)


class BodyLabel(FluentLabelBase):
    """ Body 文本 标签

    构造函数
    ------------
    * BodyLabel(`父部件`: QWidget = None)
    * BodyLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(14)


class StrongBodyLabel(FluentLabelBase):
    """ Strong body 文本 标签

    构造函数
    ------------
    * StrongBodyLabel(`父部件`: QWidget = None)
    * StrongBodyLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(14, QFont.DemiBold)


class SubtitleLabel(FluentLabelBase):
    """ Subtitle 文本 标签

    构造函数
    ------------
    * SubtitleLabel(`父部件`: QWidget = None)
    * SubtitleLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(20, QFont.DemiBold)


class TitleLabel(FluentLabelBase):
    """ Sub 标题 文本 标签

    构造函数
    ------------
    * TitleLabel(`父部件`: QWidget = None)
    * TitleLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(28, QFont.DemiBold)


class LargeTitleLabel(FluentLabelBase):
    """ Large 标题 文本 标签

    构造函数
    ------------
    * LargeTitleLabel(`父部件`: QWidget = None)
    * LargeTitleLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(40, QFont.DemiBold)


class DisplayLabel(FluentLabelBase):
    """ Display 文本 标签

    构造函数
    ------------
    * DisplayLabel(`父部件`: QWidget = None)
    * DisplayLabel(`文本`: str, `父部件`: QWidget = None)
    """

    def getFont(self):
        return getFont(68, QFont.DemiBold)


class ImageLabel(QLabel):
    """ 图像 标签

    构造函数
    ------------
    * ImageLabel(`父部件`: QWidget = None)
    * ImageLabel(`图像`: str | QImage | QPixmap, `父部件`: QWidget = None)
    """

    clicked = Signal()

    @singledispatchmethod
    def __init__(self, parent: QWidget = None):
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
        """ 设置图像的边框 半径 """
        self._topLeftRadius = topLeft
        self._topRightRadius = topRight
        self._bottomLeftRadius = bottomLeft
        self._bottomRightRadius = bottomRight
        self.update()

    def setImage(self, image: Union[str, QPixmap, QImage] = None):
        """ 设置标签的图像 """
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
    """ Avatar 部件

    构造函数
    ------------
    * AvatarWidget(`父部件`: QWidget = None)
    * AvatarWidget(`图像`: str | QImage | QPixmap, `父部件`: QWidget = None)
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
    """ Hyperlink 标签

    构造函数
    ------------
    * HyperlinkLabel(`父部件`: QWidget = None)
    * HyperlinkLabel(`文本`: str, `父部件`: QWidget = None)
    * HyperlinkLabel(`url`: QUrl, `父部件`: QWidget = None)
    """

    @singledispatchmethod
    def __init__(self, parent=None):
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
