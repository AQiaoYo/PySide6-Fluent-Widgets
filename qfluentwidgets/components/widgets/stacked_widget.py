# coding: utf-8
from typing import List

from PySide6.QtCore import (QAbstractAnimation, QEasingCurve, QPoint, QPropertyAnimation,
                          Signal, QParallelAnimationGroup, Qt, QSequentialAnimationGroup, QRect)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget, QLabel

from ...common.animation import FluentAnimation


class OpacityAniStackedWidget(QStackedWidget):
    """使用淡入淡出动画的 StackedWidget"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__nextIndex = 0
        self.__effects = []  # type:List[QPropertyAnimation]
        self.__anis = []     # type:List[QPropertyAnimation]

    def addWidget(self, w: QWidget):
        super().addWidget(w)

        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(1)
        ani = QPropertyAnimation(effect, b'opacity', self)
        ani.setDuration(220)
        ani.finished.connect(self.__onAniFinished)
        self.__anis.append(ani)
        self.__effects.append(effect)
        w.setGraphicsEffect(effect)

    def setCurrentIndex(self, index: int):
        index_ = self.currentIndex()
        if index == index_:
            return

        if index > index_:
            ani = self.__anis[index]
            ani.setStartValue(0)
            ani.setEndValue(1)
            super().setCurrentIndex(index)
        else:
            ani = self.__anis[index_]
            ani.setStartValue(1)
            ani.setEndValue(0)

        self.widget(index_).show()
        self.__nextIndex = index
        ani.start()

    def setCurrentWidget(self, w: QWidget):
        self.setCurrentIndex(self.indexOf(w))

    def __onAniFinished(self):
        super().setCurrentIndex(self.__nextIndex)


class PopUpAniInfo:
    """弹出动画信息类"""

    def __init__(self, widget: QWidget, deltaX: int, deltaY: int, effect: QGraphicsOpacityEffect):
        self.widget = widget
        self.deltaX = deltaX
        self.deltaY = deltaY
        self.effect = effect


class PopUpAniStackedWidget(QStackedWidget):
    """使用弹出动画的 StackedWidget"""

    aniFinished = Signal()
    aniStart = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aniInfos = []  # type: 列表[PopUpAniInfo]
        self.isAnimationEnabled = True
        self._currentIndex = None
        self._nextIndex = None
        self._ani = None

    def addWidget(self, widget, deltaX=0, deltaY=76):
        """将部件添加到窗口
        
        Args:
            widget: 要添加的部件
            deltaX: x轴方向动画偏移量
            deltaY: y轴方向动画偏移量
        """
        super().addWidget(widget)

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(1)
        widget.setGraphicsEffect(effect)

        self.aniInfos.append(PopUpAniInfo(
            widget=widget,
            deltaX=deltaX,
            deltaY=deltaY,
            effect=effect,
        ))

    def removeWidget(self, widget: QWidget):
        index = self.indexOf(widget)
        if index == -1:
            return

        self.aniInfos.pop(index)
        super().removeWidget(widget)

    def setAnimationEnabled(self, isEnabled: bool):
        """设置动画是否启用
        
        Args:
            isEnabled (bool): 是否启用弹出动画
        """
        self.isAnimationEnabled = isEnabled

    def setCurrentIndex(self, index: int, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                        duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """设置当前显示的窗口索引
        
        Args:
            index (int): 要显示的部件索引
            needPopOut (bool): 是否需要弹出动画
            showNextWidgetDirectly (bool): 动画开始时是否直接显示下一个部件
            duration (int): 动画持续时间
            easingCurve: 动画的缓动曲线
        """
        if index < 0 or index >= self.count():
            raise Exception(f'The index `{index}` is illegal')

        if index == self.currentIndex():
            return

        if not self.isAnimationEnabled:
            return super().setCurrentIndex(index)

        if self._ani and self._ani.state() == QAbstractAnimation.Running:
            self._ani.stop()
            self.__onAniFinished()

        self._currentIndex = self.currentIndex()
        self._nextIndex = index

        nextAniInfo = self.aniInfos[index]
        currentAniInfo = self.aniInfos[self._currentIndex]

        self.__resetWidgetState(currentAniInfo)
        self.__resetWidgetState(nextAniInfo)

        exitDuration = max(100, duration // 2)
        enterDuration = max(160, duration)

        ani = QSequentialAnimationGroup(self)
        exitAni = self.__createExitAnimationGroup(
            currentAniInfo, needPopOut, exitDuration, easingCurve)
        enterAni = self.__createEnterAnimationGroup(
            nextAniInfo, enterDuration, easingCurve)

        if exitAni.animationCount() > 0:
            exitAni.finished.connect(
                lambda: self.__switchToNextWidget(nextAniInfo, showNextWidgetDirectly))
            ani.addAnimation(exitAni)
        else:
            self.__switchToNextWidget(nextAniInfo, showNextWidgetDirectly)

        ani.addAnimation(enterAni)
        ani.finished.connect(self.__onAniFinished)
        self._ani = ani
        ani.start()
        self.aniStart.emit()

    def setCurrentWidget(self, widget, needPopOut: bool = False, showNextWidgetDirectly: bool = True,
                         duration: int = 250, easingCurve=QEasingCurve.OutQuad):
        """设置当前显示的部件
        
        Args:
            widget: 要显示的部件
            needPopOut (bool): 是否需要弹出动画
            showNextWidgetDirectly (bool): 动画开始时是否直接显示下一个部件
            duration (int): 动画持续时间
            easingCurve: 动画的缓动曲线
        """
        self.setCurrentIndex(
            self.indexOf(widget), needPopOut, showNextWidgetDirectly, duration, easingCurve)

    def __createPositionAnimation(self, widget: QWidget, startValue: QPoint, endValue: QPoint,
                                  duration: int, easingCurve=QEasingCurve.Linear):
        ani = QPropertyAnimation(widget, b'pos', self)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)
        ani.setEasingCurve(easingCurve)
        return ani

    def __createOpacityAnimation(self, effect: QGraphicsOpacityEffect, startValue: float,
                                 endValue: float, duration: int,
                                 easingCurve=QEasingCurve.Linear):
        ani = QPropertyAnimation(effect, b'opacity', self)
        ani.setStartValue(startValue)
        ani.setEndValue(endValue)
        ani.setDuration(duration)
        ani.setEasingCurve(easingCurve)
        return ani

    def __createExitAnimationGroup(self, aniInfo: PopUpAniInfo, needPopOut: bool,
                                   duration: int, easingCurve):
        aniGroup = QParallelAnimationGroup(self)
        aniGroup.addAnimation(self.__createOpacityAnimation(
            aniInfo.effect, 1.0, 0.0, duration))

        if needPopOut:
            startPos = aniInfo.widget.pos()
            endPos = startPos + QPoint(aniInfo.deltaX, aniInfo.deltaY)
            aniGroup.addAnimation(self.__createPositionAnimation(
                aniInfo.widget, startPos, endPos, duration, easingCurve))

        return aniGroup

    def __createEnterAnimationGroup(self, aniInfo: PopUpAniInfo, duration: int, easingCurve):
        aniGroup = QParallelAnimationGroup(self)
        startPos = QPoint(aniInfo.widget.x(), aniInfo.widget.y()) + QPoint(aniInfo.deltaX, aniInfo.deltaY)
        endPos = QPoint(aniInfo.widget.x(), aniInfo.widget.y())

        aniGroup.addAnimation(self.__createPositionAnimation(
            aniInfo.widget, startPos, endPos, duration, easingCurve))
        aniGroup.addAnimation(self.__createOpacityAnimation(
            aniInfo.effect, 0.0, 1.0, max(100, duration // 2)))
        return aniGroup

    def __switchToNextWidget(self, aniInfo: PopUpAniInfo, showNextWidgetDirectly: bool):
        super().setCurrentIndex(self._nextIndex)
        if showNextWidgetDirectly:
            aniInfo.widget.show()
        aniInfo.widget.raise_()

    def __resetWidgetState(self, aniInfo: PopUpAniInfo):
        aniInfo.effect.setOpacity(1.0)
        aniInfo.widget.move(0, 0)
        aniInfo.widget.resize(self.size())

    def __onAniFinished(self):
        """动画结束槽函数"""
        if self._ani:
            try:
                self._ani.finished.disconnect(self.__onAniFinished)
            except (RuntimeError, TypeError):
                pass

        super().setCurrentIndex(self._nextIndex)
        self.__resetWidgetState(self.aniInfos[self._nextIndex])
        if self._currentIndex is not None and self._currentIndex < len(self.aniInfos):
            self.__resetWidgetState(self.aniInfos[self._currentIndex])

        self._ani = None
        self.aniFinished.emit()


class TransitionStackedWidget(QStackedWidget):

    aniFinished = Signal()
    aniStart = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aniGroup = QParallelAnimationGroup(self)
        self._currentSnapshot = self._createSnapshotLabel()
        self._nextSnapshot = self._createSnapshotLabel()
        self._nextIndex = None
        self._isAnimationEnabled = True

        self._aniGroup.finished.connect(self._onAniFinished)

    def setAnimationEnabled(self, isEnabled: bool):
        """设置转场动画是否启用
        
        Args:
            isEnabled (bool): 是否启用转场动画
        """
        self._isAnimationEnabled = isEnabled

    def isAnimationEnabled(self) -> bool:
        """返回转场动画是否启用
        
        Returns:
            转场动画是否启用
        """
        return self._isAnimationEnabled

    def addWidget(self, w):
        w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        return super().addWidget(w)

    def insertWidget(self, index, w):
        w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        return super().insertWidget(index, w)

    def setCurrentWidget(self, widget: QWidget, duration: int = None, isBack: bool = False):
        """使用转场动画设置当前页面部件
        
        Args:
            widget (QWidget): 目标部件
            duration (int): 动画持续时间（毫秒），None 表示使用默认值
            isBack (bool): 是否为返回导航
        """
        self.setCurrentIndex(self.indexOf(widget), duration, isBack)

    def setCurrentIndex(self, index: int, duration: int = None, isBack: bool = False):
        """使用转场动画设置当前页面索引
        
        Args:
            index (int): 页面索引
            duration (int): 动画持续时间（毫秒），None 表示使用默认值
            isBack (bool): 是否为返回导航
        """
        if index < 0 or index >= self.count():
            return

        if index == self.currentIndex():
            return

        if not self.isAnimationEnabled():
            return super().setCurrentIndex(index)

        self._stopAnimation()

        self._nextIndex = index

        # 设置 up 动画 properties
        self._setUpTransitionAnimation(index, duration, isBack)

        # 开始transition 动画
        self._aniGroup.start()
        self.aniStart.emit()

    def _setUpTransitionAnimation(self, nextIndex: int, duration: int, isBack: bool):
        """设置转场动画
        
        Args:
            nextIndex (int): 下一个窗口索引
            duration (int): 动画持续时间
            isBack (bool): 是否为返回导航
        """
        raise NotImplementedError

    def _stopAnimation(self):
        """停止正在运行的动画"""
        if self._aniGroup.state() != QAbstractAnimation.State.Running:
            return

        self._aniGroup.stop()
        self._onAniFinished()

    def _hideSnapshots(self):
        self._currentSnapshot.hide()
        self._nextSnapshot.hide()

    def _onAniFinished(self):
        self._hideSnapshots()
        super().setCurrentIndex(self._nextIndex)
        self.aniFinished.emit()

    def _createSnapshotLabel(self):
        label = QLabel(self)
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        effect = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(effect)
        label.hide()

        return label

    def _renderSnapshot(self, widget: QWidget, label: QLabel):
        # ensure 部件 has correct 大小
        widget.resize(self.size())

        # use grab() which 适用 even 当 部件 is hidden
        pixmap = widget.grab()

        # if grab failed, fallback 到 render 使用 透明 fill
        if pixmap.isNull() or pixmap.size().isEmpty():
            pixmap = QPixmap(widget.size())
            pixmap.fill(Qt.GlobalColor.transparent)
            widget.render(pixmap)

        label.setPixmap(pixmap)
        label.setGeometry(self.rect())
        label.show()
        label.raise_()


class EntranceTransitionStackedWidget(TransitionStackedWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.outDuration = 150
        self.offset = 140

        self.currentFadeOutAni = QPropertyAnimation(self._currentSnapshot.graphicsEffect(), b'opacity', self)
        self.currentSlideOutAni = QPropertyAnimation(self._currentSnapshot, b'pos', self)
        self.nextSlideInAni = QPropertyAnimation(self, b'pos', self)

        self.nextWidgetAniGroup = QSequentialAnimationGroup(self)

        self._aniGroup.addAnimation(self.nextWidgetAniGroup)

    def _setUpTransitionAnimation(self, nextIndex, duration, isBack):
        inDuration = duration or 300
        inCurve = FluentAnimation.createBezierCurve(0.1, 0.9, 0.2, 1.0)
        outCurve = FluentAnimation.createBezierCurve(0.7, 0.0, 1.0, 0.5)

        currentWidget = self.currentWidget()
        nextWidget = self.widget(nextIndex)

        if currentWidget:
            self._renderSnapshot(currentWidget, self._currentSnapshot)
            currentWidget.hide()

            # 淡出当前部件.
            self.currentFadeOutAni.setDuration(self.outDuration)
            self.currentFadeOutAni.setStartValue(1.0)
            self.currentFadeOutAni.setEndValue(0.0)
            self.currentFadeOutAni.setEasingCurve(outCurve)
            self._aniGroup.addAnimation(self.currentFadeOutAni)

            # 滑出当前部件.
            if isBack:
                self.currentSlideOutAni.setDuration(self.outDuration)
                self.currentSlideOutAni.setStartValue(QPoint(0, 0))
                self.currentSlideOutAni.setEndValue(QPoint(0, self.offset))
                self.currentSlideOutAni.setEasingCurve(outCurve)
                self._aniGroup.addAnimation(self.currentSlideOutAni)

        nextWidget.hide()

        # 显示next 部件 after outDuration
        if self.nextWidgetAniGroup.animationCount() > 0:
            self.nextWidgetAniGroup.takeAnimation(0)

        if self.nextWidgetAniGroup.indexOfAnimation(self.nextSlideInAni) >= 0:
            self.nextWidgetAniGroup.removeAnimation(self.nextSlideInAni)

        pauseAni = self.nextWidgetAniGroup.addPause(self.outDuration)
        pauseAni.finished.connect(lambda: nextWidget.show())

        if not isBack:
            # slide 中的 next 部件
            self.nextSlideInAni.setTargetObject(nextWidget)
            nextWidget.setGeometry(0, self.offset, self.width(), self.height())
            self.nextSlideInAni.setDuration(inDuration)
            self.nextSlideInAni.setStartValue(QPoint(0, self.offset))
            self.nextSlideInAni.setEndValue(QPoint(0, 0))
            self.nextSlideInAni.setEasingCurve(inCurve)
            self.nextWidgetAniGroup.addAnimation(self.nextSlideInAni)
        else:
            # directly 显示 next 部件
            nextWidget.setGeometry(self.rect())


class DrillInTransitionStackedWidget(TransitionStackedWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentScaleOutAni = QPropertyAnimation(self._currentSnapshot, b'geometry', self)
        self.currentFadeOutAni = QPropertyAnimation(self._currentSnapshot.graphicsEffect(), b'opacity', self)
        self.nextScaleInAni = QPropertyAnimation(self._nextSnapshot, b'geometry', self)
        self.nextFadeInAni = QPropertyAnimation(self._nextSnapshot.graphicsEffect(), b'opacity', self)

    def _setUpTransitionAnimation(self, nextIndex, duration, isBack):
        scaleCurve = FluentAnimation.createBezierCurve(0.1, 0.9, 0.2, 1.0)
        opacityCurve = FluentAnimation.createBezierCurve(0.17, 0.17, 0.0, 1.0)
        backScaleCurve = FluentAnimation.createBezierCurve(0.12, 0.0, 0.0, 1.0)

        if isBack:
            inScale = 1.06
            outScale = 0.96
            inDuration = duration or 333
            outDuration = 100
            inScaleCurve = backScaleCurve
        else:
            inScale = 0.94
            outScale = 1.04
            # shortened 从 783ms 到 333ms 用于 better responsiveness
            inDuration = duration or 333
            outDuration = 100
            inScaleCurve = scaleCurve

        currentWidget = self.currentWidget()
        nextWidget = self.widget(nextIndex)
        rect = self.rect()

        if currentWidget:
            self._renderSnapshot(currentWidget, self._currentSnapshot)
            self._currentSnapshot.setScaledContents(True)
            currentWidget.hide()

            # 缩放退出当前部件.
            outW = int(rect.width() * outScale)
            outH = int(rect.height() * outScale)
            outX = (rect.width() - outW) // 2
            outY = (rect.height() - outH) // 2
            outRect = QRect(outX, outY, outW, outH)

            self.currentScaleOutAni.setDuration(outDuration)
            self.currentScaleOutAni.setStartValue(rect)
            self.currentScaleOutAni.setEndValue(outRect)
            self.currentScaleOutAni.setEasingCurve(scaleCurve)
            self._aniGroup.addAnimation(self.currentScaleOutAni)

            # 淡出当前部件.
            self.currentFadeOutAni.setDuration(outDuration)
            self.currentFadeOutAni.setStartValue(1.0)
            self.currentFadeOutAni.setEndValue(0.0)
            self.currentFadeOutAni.setEasingCurve(opacityCurve)
            self._aniGroup.addAnimation(self.currentFadeOutAni)

        # scale 中的 next 部件
        self._renderSnapshot(nextWidget, self._nextSnapshot)
        self._nextSnapshot.setScaledContents(True)
        nextWidget.hide()

        inW = int(rect.width() * inScale)
        inH = int(rect.height() * inScale)
        inX = (rect.width() - inW) // 2
        inY = (rect.height() - inH) // 2
        inRect = QRect(inX, inY, inW, inH)

        self._nextSnapshot.setGeometry(inRect)

        self.nextScaleInAni.setDuration(inDuration)
        self.nextScaleInAni.setStartValue(inRect)
        self.nextScaleInAni.setEndValue(rect)
        self.nextScaleInAni.setEasingCurve(inScaleCurve)
        self._aniGroup.addAnimation(self.nextScaleInAni)

        self.nextFadeInAni.setDuration(inDuration)
        self.nextFadeInAni.setStartValue(0.0)
        self.nextFadeInAni.setEndValue(1.0)
        self.nextFadeInAni.setEasingCurve(opacityCurve)
        self._aniGroup.addAnimation(self.nextFadeInAni)
