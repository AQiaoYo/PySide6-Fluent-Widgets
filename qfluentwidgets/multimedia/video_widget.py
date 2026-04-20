# coding: utf-8
"""提供视频播放相关的界面组件，支持在 PyQt/PySide 应用中嵌入视频渲染功能
 包含适用于 QGraphicsScene 的图形项与常规 QWidget 控件，适用于需要集成多媒体播放的 Fluent Design 桌面应用
"""

from PySide6.QtCore import Qt, Signal, QUrl, QSizeF, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QWidget, QGraphicsView, QVBoxLayout, QGraphicsScene

from ..common.style_sheet import FluentStyleSheet
from .media_play_bar import StandardMediaPlayBar


class GraphicsVideoItem(QGraphicsVideoItem):
    """用于在 QGraphicsScene 中渲染视频画面的图形项
     适合需要与其他图形元素叠加、进行几何变换或精细化布局控制的场景，可作为复杂可视化界面的一部分嵌入使用
    """

    def paint(self, painter: QPainter, option, widget):
        painter.setCompositionMode(QPainter.CompositionMode_Difference)
        super().paint(painter, option, widget)


class VideoWidget(QGraphicsView):
    """基于 QWidget 的视频播放控件，提供完整的视频渲染与交互界面
     可直接嵌入到应用窗口的布局中使用，支持播放状态展示和鼠标事件响应，满足常规桌面视频播放需求
    """

    def __init__(self, parent=None):
        """初始化视频播放控件
         Args:
             parent: 父控件，用于指定该控件的父级窗口或布局容器，传入 None 时表示该控件为独立顶层窗口
        """
        super().__init__(parent)
        self.isHover = False
        self.timer = QTimer(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.videoItem = QGraphicsVideoItem()
        self.graphicsScene = QGraphicsScene(self)
        self.playBar = StandardMediaPlayBar(self)

        self.setMouseTracking(True)
        self.setScene(self.graphicsScene)
        self.graphicsScene.addItem(self.videoItem)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.player.setVideoOutput(self.videoItem)
        FluentStyleSheet.MEDIA_PLAYER.apply(self)

        self.timer.timeout.connect(self._onHideTimeOut)

    def setVideo(self, url: QUrl):
        """设置视频源

        Args:
            url: 视频文件的 QUrl 地址
        """
        self.player.setSource(url)
        self.fitInView(self.videoItem, Qt.KeepAspectRatio)

    def hideEvent(self, e):
        self.pause()
        e.accept()

    def wheelEvent(self, e):
        return

    def enterEvent(self, e):
        self.isHover = True
        self.playBar.fadeIn()

    def leaveEvent(self, e):
        self.isHover = False
        self.timer.start(3000)

    def _onHideTimeOut(self):
        if not self.isHover:
            self.playBar.fadeOut()

    def play(self):
        self.playBar.play()

    def pause(self):
        self.playBar.pause()

    def stop(self):
        self.playBar.stop()

    def togglePlayState(self):
        """切换播放状态"""
        if self.player.isPlaying():
            self.pause()
        else:
            self.play()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.videoItem.setSize(QSizeF(self.size()))
        self.fitInView(self.videoItem, Qt.KeepAspectRatio)
        self.playBar.move(11, self.height() - self.playBar.height() - 11)
        self.playBar.setFixedSize(self.width() - 22, self.playBar.height())

    @property
    def player(self):
        return self.playBar.player