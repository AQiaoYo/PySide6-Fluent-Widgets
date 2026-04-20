# coding: utf-8
"""翻页视图组件

用于创建支持水平或垂直方向的图像翻页浏览界面，适用于图片预览、轮播展示、相册浏览等场景
提供 FlipView 及其便捷子类 HorizontalFlipView、VerticalFlipView，以及配套的滚动按钮 ScrollButton 和图像委托 FlipImageDelegate
"""

from typing import List, Union

from PySide6.QtCore import Qt, Signal, QModelIndex, QSize, Property, QRectF, QPropertyAnimation, QSizeF
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage, QWheelEvent, QPainterPath, QImageReader
from PySide6.QtWidgets import QStyleOptionViewItem, QListWidget, QStyledItemDelegate, QListWidgetItem

from ...common.overload import singledispatchmethod
from ...common.style_sheet import isDarkTheme, FluentStyleSheet
from ...common.icon import drawIcon, FluentIcon
from .scroll_bar import SmoothScrollBar
from .button import ToolButton


class ScrollButton(ToolButton):
    """滚动按钮
    
    用于 FlipView 翻页视图中控制图像前后翻页的导航按钮，支持水平或垂直布局下的自动适配与方向感知
    通常在视图边缘根据当前图像位置自动显示或隐藏，点击后触发视图滚动到上一张或下一张图像
    """

    def _postInit(self):
        self._opacity = 0
        self.opacityAni = QPropertyAnimation(self, b'opacity', self)
        self.opacityAni.setDuration(150)

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, o: float):
        self._opacity = o
        self.update()

    def isTransparent(self):
        return self.opacity == 0

    def fadeIn(self):
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(1)
        self.opacityAni.start()

    def fadeOut(self):
        self.opacityAni.setStartValue(self.opacity)
        self.opacityAni.setEndValue(0)
        self.opacityAni.start()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setOpacity(self.opacity)

        # 绘制背景
        if not isDarkTheme():
            painter.setBrush(QColor(252, 252, 252, 217))
        else:
            painter.setBrush(QColor(44, 44, 44, 245))

        painter.drawRoundedRect(self.rect(), 4, 4)

        # 绘制图标
        if isDarkTheme():
            color = QColor(255, 255, 255)
            opacity = 0.773 if self.isHover or self.isPressed else 0.541
        else:
            color = QColor(0, 0, 0)
            opacity = 0.616 if self.isHover or self.isPressed else 0.45

        painter.setOpacity(self.opacity * opacity)

        s = 6 if self.isPressed else 8
        w, h = self.width(), self.height()
        x, y = (w - s) / 2, (h - s) / 2
        drawIcon(self._icon, painter, QRectF(x, y, s, s), fill=color.name())

    opacity = Property(float, getOpacity, setOpacity)


class FlipImageDelegate(QStyledItemDelegate):
    """翻页视图图像委托
    
    负责 FlipView 中图像项的绘制、尺寸计算和样式渲染，将模型中的图像数据转换为可视化的列表项
    可通过继承此类自定义图像在翻页视图中的显示效果，例如添加圆角、阴影、选中边框或占位图样式
    """

    def __init__(self, parent=None):
        """初始化滚动按钮
        
        Args:
            parent (QWidget, optional): 父控件，默认为 None
        """
        super().__init__(parent)
        self.borderRadius = 0

    def itemSize(self, index: int):
        p = self.parent() # type: FlipView
        return p.item(index).sizeHint()

    def setBorderRadius(self, radius: int):
        self.borderRadius = radius
        self.parent().viewport().update()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        size = self.itemSize(index.row())  # type: QSize
        p = self.parent()  # type: FlipView

        # 绘制图像
        r = p.devicePixelRatioF()
        image = index.data(Qt.UserRole)  # type: QImage
        if image is None:
            return painter.restore()

        # lazy load 图像
        if image.isNull() and index.data(Qt.ItemDataRole.DisplayRole):
            image.load(index.data(Qt.ItemDataRole.DisplayRole))
            index.model().setData(index, image, Qt.ItemDataRole.UserRole)

        x = option.rect.x() + int((option.rect.width() - size.width()) / 2)
        y = option.rect.y() + int((option.rect.height() - size.height()) / 2)
        rect = QRectF(x, y, size.width(), size.height())

        # clipped path
        path = QPainterPath()
        path.addRoundedRect(rect, self.borderRadius, self.borderRadius)
        subPath = QPainterPath()
        subPath.addRoundedRect(QRectF(p.rect()), self.borderRadius, self.borderRadius)
        path = path.intersected(subPath)

        image = image.scaled(size * r, p.aspectRatioMode, Qt.SmoothTransformation)
        painter.setClipPath(path)

        # center crop 图像
        if p.aspectRatioMode == Qt.AspectRatioMode.KeepAspectRatioByExpanding:
            iw, ih = image.width(), image.height()
            size = QSizeF(size) * r
            x, y = (iw - size.width()) / 2, (ih - size.height()) / 2
            image = image.copy(int(x), int(y), int(size.width()), int(size.height()))

        painter.drawImage(rect, image)
        painter.restore()


class FlipView(QListWidget):
    """翻页视图
    
    用于展示一系列图像并支持水平或垂直方向翻页浏览的控件，适用于相册预览、商品图轮播、广告横幅、图片选择器等场景
    支持通过索引切换、导航按钮点击或拖拽手势来浏览图像，可配合 FlipImageDelegate 自定义图像渲染与交互反馈
    
    构造函数重载:
        * FlipView(parent: QWidget = None)
        * FlipView(orientation: Qt.Orientation, parent: QWidget = None)
    """

    currentIndexChanged = Signal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化翻页视图
        
        Args:
            orientation (Qt.Orientation, optional): 布局方向，决定图像是水平排列还是垂直排列，默认为 Qt.Horizontal
            parent (QWidget, optional): 父控件，默认为 None
        """
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        self.isHover = False
        self._currentIndex = -1
        self._aspectRatioMode = Qt.AspectRatioMode.IgnoreAspectRatio
        self._itemSize = QSize(480, 270)  # 16:9

        self.delegate = FlipImageDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(500)
        self.scrollBar.setForceHidden(True)

        # self.setUniformItemSizes(True)
        self.setMinimumSize(self.itemSize)
        self.setItemDelegate(self.delegate)
        self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        FluentStyleSheet.FLIP_VIEW.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.preButton = ScrollButton(FluentIcon.CARE_LEFT_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_RIGHT_SOLID, self)
            self.preButton.setFixedSize(16, 38)
            self.nextButton.setFixedSize(16, 38)
        else:
            self.preButton = ScrollButton(FluentIcon.CARE_UP_SOLID, self)
            self.nextButton = ScrollButton(FluentIcon.CARE_DOWN_SOLID, self)
            self.preButton.setFixedSize(38, 16)
            self.nextButton.setFixedSize(38, 16)

        # 连接信号与槽函数
        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)

    def isHorizontal(self):
        return self.orientation == Qt.Horizontal

    def setItemSize(self, size: QSize):
        """设置项的大小"""
        if size == self.itemSize:
            return

        self._itemSize = size

        for i in range(self.count()):
            self._adjustItemSize(self.item(i))

        self.viewport().update()

    def getItemSize(self):
        """获取项的大小"""
        return self._itemSize

    def setBorderRadius(self, radius: int):
        """设置项的边框半径"""
        self.delegate.setBorderRadius(radius)

    def getBorderRadius(self):
        return self.delegate.borderRadius

    def scrollPrevious(self):
        """滚动到上一项"""
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollNext(self):
        """滚动到下一项"""
        self.setCurrentIndex(self.currentIndex() + 1)

    def setCurrentIndex(self, index: int):
        """设置当前索引"""
        if not 0 <= index < self.count() or index == self.currentIndex():
            return

        self.scrollToIndex(index)

        # 更新滚动按钮的可见性.
        if index == 0:
            self.preButton.fadeOut()
        elif self.preButton.isTransparent() and self.isHover:
            self.preButton.fadeIn()

        if index == self.count() - 1:
            self.nextButton.fadeOut()
        elif self.nextButton.isTransparent() and self.isHover:
            self.nextButton.fadeIn()

        # fire 信号
        self.currentIndexChanged.emit(index)

    def scrollToIndex(self, index):
        if not 0 <= index < self.count():
            return

        self._currentIndex = index

        if self.isHorizontal():
            value = sum(self.item(i).sizeHint().width() for i in range(index))
        else:
            value = sum(self.item(i).sizeHint().height() for i in range(index))

        value += (2 * index + 1) * self.spacing()
        self.scrollBar.scrollTo(value)

    def currentIndex(self):
        return self._currentIndex

    def image(self, index: int):
        if not 0 <= index < self.count():
            return QImage()

        return self.item(index).data(Qt.UserRole)

    def addImage(self, image: Union[QImage, QPixmap, str]):
        """添加图像"""
        self.addImages([image])

    def addImages(self, images: List[Union[QImage, QPixmap, str]], targetSize: QSize = None):
        """批量添加图像"""
        if not images:
            return

        N = self.count()
        self.addItems([''] * len(images))

        for i in range(N, self.count()):
            self.setItemImage(i, images[i - N], targetSize=targetSize)

        if self.currentIndex() < 0:
            self._currentIndex = 0

    def setItemImage(self, index: int, image: Union[QImage, QPixmap, str], targetSize: QSize = None):
        """设置指定项的图像"""
        if not 0 <= index < self.count():
            return

        item = self.item(index)

        # 将图像转换为QImage
        if isinstance(image, QPixmap):
            image = image.toImage()

        # lazy load
        if isinstance(image, QImage):
            item.setData(Qt.ItemDataRole.UserRole, image)
        else:
            item.setData(Qt.ItemDataRole.UserRole, QImage())
            item.setData(Qt.ItemDataRole.DisplayRole, image)

        self._adjustItemSize(item)

    def _adjustItemSize(self, item: QListWidgetItem):
        image = self.itemImage(self.row(item), load=False)

        if not image.isNull():
            size = image.size()
        else:
            imagePath = item.data(Qt.ItemDataRole.DisplayRole) or ""
            size = QImageReader(imagePath).size().expandedTo(QSize(1, 1))

        if self.aspectRatioMode == Qt.AspectRatioMode.KeepAspectRatio:
            if self.isHorizontal():
                h = self.itemSize.height()
                w = int(size.width() * h / size.height())
            else:
                w = self.itemSize.width()
                h = int(size.height() * w / size.width())
        else:
            w, h = self.itemSize.width(), self.itemSize.height()

        item.setSizeHint(QSize(w, h))

    def itemImage(self, index: int, load=True) -> QImage:
        """获取指定项的图像

        Args:
            index: 图像索引
            load: 是否加载图像数据
        """
        if not 0 <= index < self.count():
            return

        item = self.item(index)
        image = item.data(Qt.ItemDataRole.UserRole)  # type: QImage

        if image is None:
            return QImage()

        imagePath = item.data(Qt.ItemDataRole.DisplayRole)
        if image.isNull() and imagePath and load:
            image.load(imagePath)

        return image

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        bw, bh = self.preButton.width(), self.preButton.height()

        if self.isHorizontal():
            self.preButton.move(2, int(h / 2 - bh / 2))
            self.nextButton.move(w - bw - 2, int(h / 2 - bh / 2))
        else:
            self.preButton.move(int(w / 2 - bw / 2), 2)
            self.nextButton.move(int(w / 2 - bw / 2), h - bh - 2)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True

        if self.currentIndex() > 0:
            self.preButton.fadeIn()

        if self.currentIndex() < self.count() - 1:
            self.nextButton.fadeIn()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        self.preButton.fadeOut()
        self.nextButton.fadeOut()

    def showEvent(self, e):
        self.scrollBar.duration = 0
        self.scrollToIndex(self.currentIndex())
        self.scrollBar.duration = 500

    def wheelEvent(self, e: QWheelEvent):
        e.setAccepted(True)
        if self.scrollBar.ani.state() == QPropertyAnimation.Running:
            return

        if e.angleDelta().y() < 0:
            self.scrollNext()
        else:
            self.scrollPrevious()

    def getAspectRatioMode(self):
        return self._aspectRatioMode

    def setAspectRatioMode(self, mode: Qt.AspectRatioMode):
        if mode == self.aspectRatioMode:
            return

        self._aspectRatioMode = mode

        for i in range(self.count()):
            self._adjustItemSize(self.item(i))

        self.viewport().update()

    itemSize = Property(QSize, getItemSize, setItemSize)
    borderRadius = Property(int, getBorderRadius, setBorderRadius)
    aspectRatioMode = Property(Qt.AspectRatioMode, getAspectRatioMode, setAspectRatioMode)


class HorizontalFlipView(FlipView):
    """水平翻页视图
    
    用于水平方向展示图像并支持左右翻页浏览的便捷控件，适用于横向相册、Banner 轮播、商品横图预览等场景
    继承自 FlipView，默认使用 Qt.Horizontal 方向，无需手动设置 orientation 即可直接创建水平翻页效果
    """

    def __init__(self, parent=None):
        """初始化水平翻页视图
        
        Args:
            parent (QWidget, optional): 父控件，默认为 None
        """
        super().__init__(Qt.Horizontal, parent)


class VerticalFlipView(FlipView):
    """垂直翻页视图
    
    用于垂直方向展示图像并支持上下翻页浏览的便捷控件，适用于纵向相册、竖图瀑布流、长图预览等场景
    继承自 FlipView，默认使用 Qt.Vertical 方向，无需手动设置 orientation 即可直接创建垂直翻页效果
    """

    def __init__(self, parent=None):
        """初始化垂直翻页视图
        
        Args:
            parent (QWidget, optional): 父控件，默认为 None
        """
        super().__init__(Qt.Vertical, parent)