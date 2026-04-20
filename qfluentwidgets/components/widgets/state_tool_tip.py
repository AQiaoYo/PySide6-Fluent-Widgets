# coding: utf-8
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal, QSize, QPoint, QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QWidget, QToolButton, QGraphicsOpacityEffect
from PySide6.QtSvgWidgets import QSvgWidget

from ...common import FluentStyleSheet, isDarkTheme, Theme
from ...common.icon import FluentIcon as FIF


class StateCloseButton(QToolButton):
    """状态工具提示的关闭按钮
    
    用于 StateToolTip 右上角，提供用户手动关闭提示的途径
    通常在提示需要持久显示或操作出错时呈现
    """

    def __init__(self, parent=None):
        """初始化关闭按钮
        
        Args:
            parent: 父窗口或父部件，指定后按钮会随父部件一起销毁并自动定位在父部件内部
        """
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.isPressed = False
        self.isEnter = False

    def enterEvent(self, e):
        self.isEnter = True
        self.update()

    def leaveEvent(self, e):
        self.isEnter = False
        self.isPressed = False
        self.update()

    def mousePressEvent(self, e):
        self.isPressed = True
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isPressed:
            painter.setOpacity(0.6)
        elif self.isEnter:
            painter.setOpacity(0.8)

        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
        FIF.CLOSE.render(painter, self.rect(), theme)


class StateToolTip(QWidget):
    """显示操作状态的工具提示组件
    
    适用于向用户反馈长时间操作进度或操作结果的场景，如文件保存、网络请求等
    支持自动关闭和手动关闭两种模式，可通过 setContent 动态更新提示文本
    """

    closedSignal = Signal()

    def __init__(self, title, content, parent=None):
        """初始化状态工具提示
        
        Args:
            title: 工具提示标题
            content: 工具提示内容
            parent: 父窗口
        """
        super().__init__(parent)
        self.title = title
        self.content = content

        self.titleLabel = QLabel(self.title, self)
        self.contentLabel = QLabel(self.content, self)
        self.rotateTimer = QTimer(self)

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.animation = QPropertyAnimation(self.opacityEffect, b"opacity")
        self.closeButton = StateCloseButton(self)

        self.isDone = False
        self.rotateAngle = 0
        self.deltaAngle = 20

        self.__initWidget()

    def __initWidget(self):
        """初始化部件"""
        self.setAttribute(Qt.WA_StyledBackground)
        self.setGraphicsEffect(self.opacityEffect)
        self.opacityEffect.setOpacity(1)
        self.rotateTimer.setInterval(50)
        self.contentLabel.setMinimumWidth(200)

        # 连接信号与槽函数
        self.closeButton.clicked.connect(self.__onCloseButtonClicked)
        self.rotateTimer.timeout.connect(self.__rotateTimerFlowSlot)

        self.__setQss()
        self.__initLayout()

        self.rotateTimer.start()

    def __initLayout(self):
        """初始化布局"""
        self.setFixedSize(max(self.titleLabel.width(),
                          self.contentLabel.width()) + 56, 51)
        self.titleLabel.move(32, 9)
        self.contentLabel.move(12, 27)
        self.closeButton.move(self.width() - 24, 19)

    def __setQss(self):
        """设置样式表"""
        self.titleLabel.setObjectName("titleLabel")
        self.contentLabel.setObjectName("contentLabel")

        FluentStyleSheet.STATE_TOOL_TIP.apply(self)

        self.titleLabel.adjustSize()
        self.contentLabel.adjustSize()

    def setTitle(self, title: str):
        """设置工具提示标题"""
        self.title = title
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setContent(self, content: str):
        """设置工具提示内容"""
        self.content = content
        self.contentLabel.setText(content)

        # adjustSize() will 遮罩 spinner 获取 stuck
        self.contentLabel.adjustSize()

    def setState(self, isDone=False):
        """设置工具提示状态"""
        self.isDone = isDone
        self.update()
        if isDone:
            QTimer.singleShot(1000, self.__fadeOut)

    def __onCloseButtonClicked(self):
        """关闭按钮 clicked 槽函数"""
        self.closedSignal.emit()
        self.hide()

    def __fadeOut(self):
        """淡出"""
        self.rotateTimer.stop()
        self.animation.setDuration(200)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()

    def __rotateTimerFlowSlot(self):
        """旋转定时器超时槽函数"""
        self.rotateAngle = (self.rotateAngle + self.deltaAngle) % 360
        self.update()

    def getSuitablePos(self):
        """获取主窗口中的合适位置"""
        for i in range(10):
            dy = i*(self.height() + 16)
            pos = QPoint(self.parent().width() - self.width() - 24, 50+dy)
            widget = self.parent().childAt(pos + QPoint(2, 2))
            if isinstance(widget, StateToolTip):
                pos += QPoint(0, self.height() + 16)
            else:
                break

        return pos

    def paintEvent(self, e):
        """绘制状态工具提示"""
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT

        if not self.isDone:
            painter.translate(19, 18)
            painter.rotate(self.rotateAngle)
            FIF.SYNC.render(painter, QRectF(-8, -8, 16, 16), theme)
        else:
            FIF.COMPLETED.render(painter, QRectF(11, 10, 16, 16), theme)
