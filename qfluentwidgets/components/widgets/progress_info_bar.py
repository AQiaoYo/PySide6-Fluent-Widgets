# coding: utf-8
"""进度信息栏组件

在 InfoBar 标准布局基础上, 将左侧图标替换为进度环, 用于在通知中同时展示任务名称, 描述与执行进度
适用于发送邮件, 文件上传, 同步等长时间运行任务的非阻塞反馈场景
"""

from typing import Optional, Union

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from .info_bar import InfoBar, InfoBarIcon, InfoBarManager, InfoBarPosition, InfoIconWidget
from .progress_ring import IndeterminateProgressRing, ProgressRing


class ProgressIconWidget(QWidget):
    """进度信息栏左侧的图标占位

    与 InfoIconWidget 保持一致的 36x36 固定尺寸, 内部承载进度环并将其居中放置
    用于在替换 InfoBar 默认图标时, 保证 ProgressInfoBar 与 InfoBar 视觉对齐
    """

    def __init__(self, ring: QWidget, parent=None):
        """初始化图标占位

        Args:
            ring: 进度环控件, 由外部创建并由该占位负责定位
            parent: 父级控件, 一般为 ProgressInfoBar 实例
        """
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self._ring = ring
        ring.setParent(self)
        self.centerRing()

    def ring(self) -> QWidget:
        """获取当前进度环"""
        return self._ring

    def setRing(self, ring: QWidget):
        """替换内部进度环

        Args:
            ring: 新的进度环控件, 替换后会自动销毁原有控件并重新居中
        """
        if self._ring is ring:
            return

        if self._ring is not None:
            self._ring.setParent(None)
            self._ring.deleteLater()

        self._ring = ring
        ring.setParent(self)
        ring.show()
        self.centerRing()

    def centerRing(self):
        """将进度环居中放置在占位中央, 在调整进度环尺寸后需手动调用以重新居中"""
        if self._ring is None:
            return

        size = self._ring.size()
        x = (self.width() - size.width()) // 2
        y = (self.height() - size.height()) // 2
        self._ring.move(x, y)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.centerRing()


class ProgressInfoBar(InfoBar):
    """带进度环的信息栏

    在 InfoBar 基础上将左侧图标替换为进度环, 用于展示长时间任务的执行状态
    支持不确定模式 (旋转动画) 与确定模式 (按数值填充弧度), 复用 InfoBarManager 的位置, 动画与堆叠
    调用 setComplete() 会将进度环替换为成功/失败图标, 并可选择在指定时间后自动淡出

    构造函数重载:
        * ProgressInfoBar(title: str, content: str, parent: QWidget = None, indeterminate: bool = True, ...)
    """

    DEFAULT_RING_SIZE = 22
    DEFAULT_RING_STROKE = 3

    finished = Signal(bool)

    def __init__(self, title: str, content: str, orient=Qt.Horizontal, isClosable=True,
                 duration=-1, position=InfoBarPosition.TOP_RIGHT, parent=None,
                 indeterminate: bool = True):
        """构造函数

        Args:
            title: 任务标题, 显示在进度环右侧
            content: 任务描述, 剩余时间等附加信息
            orient: 布局方向, 短描述建议 Qt.Horizontal
            isClosable: 是否显示关闭按钮
            duration: 显示时长, 单位毫秒, 小于 0 表示不会自动消失, 适合长时间任务
            position: 信息栏显示位置, 复用 InfoBarPosition
            parent: 父部件
            indeterminate: 是否使用不确定进度环, 默认 True
        """
        super().__init__(InfoBarIcon.INFORMATION, title, content, orient,
                         isClosable, duration, position, parent)

        self._indeterminate = bool(indeterminate)
        self._isFinished = False

        # 用进度环替换 InfoBar 默认的图标控件
        ring = self._createRing(self._indeterminate)
        oldIcon = self.iconWidget
        index = self.hBoxLayout.indexOf(oldIcon)
        align = Qt.AlignTop | Qt.AlignLeft

        self.hBoxLayout.removeWidget(oldIcon)
        oldIcon.setParent(None)
        oldIcon.deleteLater()

        self.iconWidget = ProgressIconWidget(ring, self)
        self.hBoxLayout.insertWidget(max(0, index), self.iconWidget, 0, align)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # 任何导致自身尺寸变化的操作 (setTitle/setContent/setComplete) 都会走到这里
        # 主动请求 InfoBarManager 重新布局同位置的所有兄弟节点, 以保证右对齐/底部对齐与堆叠 y 坐标始终同步
        self._refreshLayout()

    def _refreshLayout(self):
        """重新计算自身及同位置兄弟节点的坐标

        概念与 InfoBarManager.eventFilter 处理父窗口 Resize 的逻辑一致, 但触发点从
        “父窗口尺寸变化” 拓展为 “本身尺寸变化”, 避免在 setTitle/setContent/setComplete 后出现
        x 偏移 (宽度变化) 或堆叠兄弟重叠 (高度变化) 的问题
        """
        if self.position == InfoBarPosition.NONE:
            return

        parent = self.parent()
        if parent is None:
            return

        try:
            manager = InfoBarManager.make(self.position)
        except ValueError:
            return

        bars = manager.infoBars.get(parent)
        # 构造期尚未被 manager 接管, 此时不需要重新定位
        if not bars or self not in bars:
            return

        for bar in bars:
            try:
                bar.move(manager._pos(bar))
            except RuntimeError:
                # 部分兄弟节点可能已被 Qt 销毁, 直接跳过
                continue

    def _createRing(self, indeterminate: bool) -> QWidget:
        """根据模式创建进度环

        Args:
            indeterminate: 是否使用不确定进度环
        """
        if indeterminate:
            ring = IndeterminateProgressRing(start=True)
        else:
            ring = ProgressRing()
            ring.setTextVisible(False)

        ring.setFixedSize(self.DEFAULT_RING_SIZE, self.DEFAULT_RING_SIZE)
        ring.setStrokeWidth(self.DEFAULT_RING_STROKE)
        return ring

    def progressRing(self) -> Optional[QWidget]:
        """获取内部进度环, 任务标记完成后返回 None"""
        if self.hasProgressRing():
            return self.iconWidget.ring()
        return None

    def hasProgressRing(self) -> bool:
        """当前左侧图标是否仍为进度环

        调用 setComplete() 后会被替换为状态图标, 返回 False
        """
        return isinstance(self.iconWidget, ProgressIconWidget)

    def isIndeterminate(self) -> bool:
        """是否处于不确定模式"""
        return self._indeterminate

    def isFinished(self) -> bool:
        """是否已被标记为完成 (调用过 setComplete)"""
        return self._isFinished

    def setIndeterminate(self, indeterminate: bool):
        """切换不确定/确定模式

        Args:
            indeterminate: 是否使用不确定模式, 切换会重新创建内部进度环
        """
        if bool(indeterminate) == self._indeterminate:
            return

        if not self.hasProgressRing():
            return

        # 切换前停止旧动画, 避免 deleteLater 前动画组还在跳动导致封装在 try/except 中的可能泄漏
        oldRing = self.progressRing()
        if isinstance(oldRing, IndeterminateProgressRing):
            oldRing.stop()

        self._indeterminate = bool(indeterminate)
        ring = self._createRing(self._indeterminate)
        self.iconWidget.setRing(ring)

    def setValue(self, value: int):
        """设置进度值, 若当前为不确定模式会自动切换到确定模式

        Args:
            value: 当前进度数值
        """
        if not self.hasProgressRing():
            return

        if self._indeterminate:
            self.setIndeterminate(False)

        ring = self.progressRing()
        if hasattr(ring, 'setValue'):
            ring.setValue(int(value))

    def value(self) -> int:
        """获取当前进度值"""
        ring = self.progressRing()
        return ring.value() if ring is not None and hasattr(ring, 'value') else 0

    def setRange(self, minimum: int, maximum: int):
        """设置进度范围, 若当前为不确定模式会自动切换到确定模式

        Args:
            minimum: 最小值
            maximum: 最大值
        """
        if not self.hasProgressRing():
            return

        if self._indeterminate:
            self.setIndeterminate(False)

        ring = self.progressRing()
        if hasattr(ring, 'setRange'):
            ring.setRange(int(minimum), int(maximum))

    def setMaximum(self, maximum: int):
        """设置进度最大值"""
        if not self.hasProgressRing():
            return

        if self._indeterminate:
            self.setIndeterminate(False)

        ring = self.progressRing()
        if hasattr(ring, 'setMaximum'):
            ring.setMaximum(int(maximum))

    def setMinimum(self, minimum: int):
        """设置进度最小值"""
        if not self.hasProgressRing():
            return

        if self._indeterminate:
            self.setIndeterminate(False)

        ring = self.progressRing()
        if hasattr(ring, 'setMinimum'):
            ring.setMinimum(int(minimum))

    def maximum(self) -> int:
        """获取进度最大值"""
        ring = self.progressRing()
        return ring.maximum() if ring is not None and hasattr(ring, 'maximum') else 0

    def minimum(self) -> int:
        """获取进度最小值"""
        ring = self.progressRing()
        return ring.minimum() if ring is not None and hasattr(ring, 'minimum') else 0

    def pauseAnimation(self):
        """暂停不确定模式的旋转动画, 仅在不确定模式下生效"""
        ring = self.progressRing()
        if isinstance(ring, IndeterminateProgressRing):
            ring.stop()

    def resumeAnimation(self):
        """恢复不确定模式的旋转动画, 仅在不确定模式下生效"""
        ring = self.progressRing()
        if isinstance(ring, IndeterminateProgressRing):
            ring.start()

    def setTitle(self, title: str):
        """更新标题文本

        Args:
            title: 新的标题文本
        """
        self.title = title
        self.titleLabel.setVisible(bool(title))
        self._adjustText()

    def setContent(self, content: str):
        """更新内容描述

        Args:
            content: 新的内容文本
        """
        self.content = content
        self.contentLabel.setVisible(bool(content))
        self._adjustText()

    def setRingSize(self, size: int, strokeWidth: int = None):
        """调整内部进度环的尺寸与描边宽度

        Args:
            size: 进度环边长 (像素)
            strokeWidth: 进度环描边宽度, 留空则保持当前值
        """
        if not self.hasProgressRing():
            return

        size = max(1, int(size))
        ring = self.progressRing()
        ring.setFixedSize(size, size)
        if strokeWidth is not None:
            ring.setStrokeWidth(max(1, int(strokeWidth)))
        self.iconWidget.centerRing()

    def setProgressColor(self, light, dark):
        """自定义进度环前景颜色

        Args:
            light: 亮色主题颜色, 支持 str, Qt.GlobalColor, QColor
            dark: 暗色主题颜色, 支持 str, Qt.GlobalColor, QColor
        """
        ring = self.progressRing()
        if hasattr(ring, 'setCustomBarColor'):
            ring.setCustomBarColor(QColor(light), QColor(dark))

    def setComplete(self, success: bool = True, content: str = None,
                    title: str = None, autoCloseAfter: int = 1500):
        """将信息栏标记为完成状态

        会停止不确定动画, 将进度环替换为成功/失败图标, 同时更新背景色调为 Success/Error 主题
        多次调用仅首次生效, 以避免重复发出 finished 信号

        Args:
            success: True 表示成功 (Success 主题), False 表示失败 (Error 主题)
            content: 完成后的描述文本, 为 None 时保持现有内容
            title: 完成后的标题文本, 为 None 时保持现有标题
            autoCloseAfter: 自动淡出的延迟, 单位毫秒, 小于 0 表示不自动关闭
        """
        if self._isFinished:
            return

        # 停止还在运行的不确定动画
        oldRing = self.progressRing()
        if isinstance(oldRing, IndeterminateProgressRing):
            oldRing.stop()

        # 用 InfoIconWidget 完整替换进度环占位
        icon = InfoBarIcon.SUCCESS if success else InfoBarIcon.ERROR
        newIcon = InfoIconWidget(icon, self)

        index = self.hBoxLayout.indexOf(self.iconWidget)
        align = Qt.AlignTop | Qt.AlignLeft
        self.hBoxLayout.removeWidget(self.iconWidget)
        self.iconWidget.setParent(None)
        self.iconWidget.deleteLater()
        self.iconWidget = newIcon
        self.hBoxLayout.insertWidget(max(0, index), self.iconWidget, 0, align)

        if title is not None:
            self.setTitle(title)
        if content is not None:
            self.setContent(content)

        # 刷新 type 属性以应用 Success/Error 背景色
        self.icon = icon
        self.setProperty('type', icon.value)
        self.style().unpolish(self)
        self.style().polish(self)

        self._isFinished = True
        self.finished.emit(bool(success))

        if autoCloseAfter >= 0:
            QTimer.singleShot(int(autoCloseAfter), self.close)

    @classmethod
    def new(cls, title: str, content: str, orient=Qt.Horizontal, isClosable=True,
            duration=-1, position=InfoBarPosition.TOP_RIGHT, parent=None,
            indeterminate: bool = True) -> 'ProgressInfoBar':
        """快捷工厂方法, 创建实例并立即显示

        Args:
            title: 任务标题
            content: 任务描述
            orient: 布局方向
            isClosable: 是否显示关闭按钮
            duration: 显示时长, 单位毫秒
            position: 信息栏显示位置
            parent: 父部件
            indeterminate: 是否使用不确定进度环

        Returns:
            ProgressInfoBar 实例
        """
        bar = cls(title, content, orient, isClosable, duration, position, parent, indeterminate)
        bar.show()
        return bar

    @classmethod
    def indeterminate(cls, title: str, content: str, orient=Qt.Horizontal, isClosable=True,
                      duration=-1, position=InfoBarPosition.TOP_RIGHT,
                      parent=None) -> 'ProgressInfoBar':
        """创建不确定模式的 ProgressInfoBar 并立即显示, 适用于无法预估剩余时间的任务。"""
        return cls.new(title, content, orient, isClosable, duration, position, parent,
                       indeterminate=True)

    @classmethod
    def determinate(cls, title: str, content: str, maximum: int = 100,
                    orient=Qt.Horizontal, isClosable=True, duration=-1,
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=None) -> 'ProgressInfoBar':
        """创建确定模式的 ProgressInfoBar 并立即显示, 适用于可量化进度的任务。

        Args:
            title: 任务标题
            content: 任务描述
            maximum: 进度最大值, 默认 100
            orient: 布局方向
            isClosable: 是否显示关闭按钮
            duration: 显示时长
            position: 信息栏显示位置
            parent: 父部件

        Returns:
            ProgressInfoBar 实例, 进度范围已设为 [0, maximum]
        """
        bar = cls.new(title, content, orient, isClosable, duration, position, parent,
                      indeterminate=False)
        bar.setRange(0, int(maximum))
        return bar
