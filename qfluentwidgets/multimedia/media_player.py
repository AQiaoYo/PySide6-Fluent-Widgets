# coding: utf-8
from PySide6.QtCore import Qt, Signal, QObject, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class MediaPlayerBase(QObject):
    """ 媒体播放器基类 """

    mediaStatusChanged = Signal(QMediaPlayer.MediaStatus)
    playbackRateChanged = Signal(float)
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    sourceChanged = Signal(QUrl)
    volumeChanged = Signal(int)
    mutedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def isPlaying(self):
        """ 是否 media is playing """
        raise NotImplementedError

    def mediaStatus(self) -> QMediaPlayer.MediaStatus:
        """ 返回 状态 的 当前媒体流 """
        raise NotImplementedError

    def playbackState(self) -> QMediaPlayer.PlaybackState:
        """ 返回 播放状态 的 当前媒体流 """
        raise NotImplementedError

    def duration(self):
        """ 返回 持续时间 的 当前 media 中的 ms """
        raise NotImplementedError

    def position(self):
        """ 返回 当前 位置 inside media being played back 中的 ms """
        raise NotImplementedError

    def volume(self):
        """ 返回 音量 的 播放器 """
        raise NotImplementedError

    def source(self) -> QUrl:
        """ 返回 active media 源 being used """
        raise NotImplementedError

    def pause(self):
        """ Pause playing 当前 源 """
        raise NotImplementedError

    def play(self):
        """ 开始or resume playing 当前 源 """
        raise NotImplementedError

    def stop(self):
        """ 停止playing, 和 reset play 位置 到 beginning """
        raise NotImplementedError

    def playbackRate(self) -> float:
        """ 返回 播放速率 的 当前 media """
        raise NotImplementedError

    def setPosition(self, position: int):
        """ 设置 位置 的 media 中的 ms """
        raise NotImplementedError

    def setSource(self, media: QUrl):
        """ 设置 当前 源 """
        raise NotImplementedError

    def setPlaybackRate(self, rate: float):
        """ 设置 播放速率 的 播放器 """
        raise NotImplementedError

    def setVolume(self, volume: int):
        """ 设置 音量 的 播放器 """
        raise NotImplementedError

    def setMuted(self, isMuted: bool):
        raise NotImplementedError

    def videoOutput(self) -> QObject:
        """ 返回 视频 output 到 be used by 媒体播放器 """
        raise NotImplementedError

    def setVideoOutput(self, output: QObject) -> None:
        """ 设置 视频 output 到 be used by 媒体播放器 """
        raise NotImplementedError


class MediaPlayer(QMediaPlayer):
    """ 媒体播放器 """

    sourceChanged = Signal(QUrl)
    mutedChanged = Signal(bool)
    volumeChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._audioOutput = QAudioOutput(parent)
        self.setAudioOutput(self._audioOutput)

    def isPlaying(self):
        return self.playbackState() == QMediaPlayer.PlayingState

    def volume(self):
        """ 返回 音量 的 播放器 """
        return int(self.audioOutput().volume() * 100)

    def setVolume(self, volume: int):
        """ 设置 音量 的 播放器 """
        if volume == self.volume():
            return

        self.audioOutput().setVolume(volume / 100)
        self.volumeChanged.emit(volume)

    def setMuted(self, isMuted: bool):
        if isMuted == self.audioOutput().isMuted():
            return

        self.audioOutput().setMuted(isMuted)
        self.mutedChanged.emit(isMuted)