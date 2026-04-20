# coding: utf-8
"""媒体播放器模块

提供基于 Fluent Design 风格的媒体播放基础组件与实现类，支持在应用中集成音视频播放功能
包含播放器基类与标准播放器控件，可满足自定义扩展与直接使用两种需求
"""

from PySide6.QtCore import Qt, Signal, QObject, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class MediaPlayerBase(QObject):
    """媒体播放器基类
    
    定义了媒体播放器的通用接口与基础控制逻辑，适用于需要自定义播放行为或接入新播放后端的场景
    子类需重写相关方法以完成媒体加载、播放控制及状态反馈的具体实现
    """

    mediaStatusChanged = Signal(QMediaPlayer.MediaStatus)
    playbackRateChanged = Signal(float)
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    sourceChanged = Signal(QUrl)
    volumeChanged = Signal(int)
    mutedChanged = Signal(bool)

    def __init__(self, parent=None):
        """初始化播放器基类
        
        Args:
            parent: 父对象，类型为 QObject，用于指定该播放器的父级，传入 None 时表示无父对象，传入有效对象时将被纳入对应对象树中管理
        """
        super().__init__(parent=parent)

    def isPlaying(self):
        """媒体是否正在播放"""
        raise NotImplementedError

    def mediaStatus(self) -> QMediaPlayer.MediaStatus:
        """返回当前媒体流的状态"""
        raise NotImplementedError

    def playbackState(self) -> QMediaPlayer.PlaybackState:
        """返回当前媒体流的播放状态"""
        raise NotImplementedError

    def duration(self):
        """返回当前媒体的持续时间（ms）"""
        raise NotImplementedError

    def position(self):
        """返回当前媒体的播放位置（ms）"""
        raise NotImplementedError

    def volume(self):
        """返回播放器的音量"""
        raise NotImplementedError

    def source(self) -> QUrl:
        """返回正在使用的活动媒体源"""
        raise NotImplementedError

    def pause(self):
        """暂停播放当前源"""
        raise NotImplementedError

    def play(self):
        """开始或恢复播放当前源"""
        raise NotImplementedError

    def stop(self):
        """停止播放，并将播放位置重置到开头"""
        raise NotImplementedError

    def playbackRate(self) -> float:
        """返回当前媒体的播放速率"""
        raise NotImplementedError

    def setPosition(self, position: int):
        """设置媒体的播放位置

        Args:
            position: 播放位置（ms）
        """
        raise NotImplementedError

    def setSource(self, media: QUrl):
        """设置当前媒体源

        Args:
            media: 媒体源
        """
        raise NotImplementedError

    def setPlaybackRate(self, rate: float):
        """设置播放器的播放速率

        Args:
            rate: 播放速率
        """
        raise NotImplementedError

    def setVolume(self, volume: int):
        """设置播放器的音量

        Args:
            volume: 音量
        """
        raise NotImplementedError

    def setMuted(self, isMuted: bool):
        raise NotImplementedError

    def videoOutput(self) -> QObject:
        """返回媒体播放器使用的视频输出"""
        raise NotImplementedError

    def setVideoOutput(self, output: QObject) -> None:
        """设置媒体播放器使用的视频输出

        Args:
            output: 视频输出对象
        """
        raise NotImplementedError


class MediaPlayer(QMediaPlayer):
    """媒体播放器
    
    继承自 MediaPlayerBase 并提供完整的媒体播放能力，支持音视频播放、进度调节与状态显示
    适用于需要在界面中集成标准媒体播放器的业务场景
    """

    sourceChanged = Signal(QUrl)
    mutedChanged = Signal(bool)
    volumeChanged = Signal(int)

    def __init__(self, parent=None):
        """初始化媒体播放器
        
        Args:
            parent: 父控件，类型为 QWidget，用于指定该播放器控件的父级，传入 None 时作为独立窗口，传入有效控件时会被嵌入父控件的界面层级中
        """
        super().__init__(parent=parent)
        self._audioOutput = QAudioOutput(parent)
        self.setAudioOutput(self._audioOutput)

    def isPlaying(self):
        return self.playbackState() == QMediaPlayer.PlayingState

    def volume(self):
        """返回播放器的音量"""
        return int(self.audioOutput().volume() * 100)

    def setVolume(self, volume: int):
        """设置播放器的音量

        Args:
            volume: 音量
        """
        if volume == self.volume():
            return

        self.audioOutput().setVolume(volume / 100)
        self.volumeChanged.emit(volume)

    def setMuted(self, isMuted: bool):
        if isMuted == self.audioOutput().isMuted():
            return

        self.audioOutput().setMuted(isMuted)
        self.mutedChanged.emit(isMuted)