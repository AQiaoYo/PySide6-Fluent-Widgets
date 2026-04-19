# coding: utf-8
"""
MediaPlayer 演示

展示内容：
- SimpleMediaPlayBar 简洁播放条
- StandardMediaPlayBar 标准播放条
- VideoWidget 视频播放
- 在线/本地媒体源切换
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import setTheme, Theme, BodyLabel
from qfluentwidgets.multimedia import SimpleMediaPlayBar, StandardMediaPlayBar, VideoWidget


class Demo1(QWidget):
    """音频播放演示"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MediaPlayer - 音频')
        self.resize(500, 200)
        self.initLayout()

        # 简洁播放条
        self.simplePlayBar = SimpleMediaPlayBar(self)

        # 标准播放条
        self.standardPlayBar = StandardMediaPlayBar(self)

        self.layout.addWidget(self.simplePlayBar)
        self.layout.addWidget(self.standardPlayBar)

        # 设置媒体源
        try:
            url = QUrl.fromLocalFile(str(Path('resource/aiko - シアワセ.mp3').absolute()))
            self.standardPlayBar.player.setSource(url)
        except Exception:
            pass

    def initLayout(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)


class Demo2(QWidget):
    """视频播放演示"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('MediaPlayer - 视频')
        self.resize(800, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.videoWidget = VideoWidget(self)
        self.videoWidget.setVideo(QUrl('https://media.w3.org/2010/05/sintel/trailer.mp4'))
        self.videoWidget.play()

        layout.addWidget(self.videoWidget)


if __name__ == '__main__':
    setTheme(Theme.DARK)
    app = QApplication(sys.argv)

    demo1 = Demo1()
    demo1.show()

    demo2 = Demo2()
    demo2.show()

    sys.exit(app.exec())
