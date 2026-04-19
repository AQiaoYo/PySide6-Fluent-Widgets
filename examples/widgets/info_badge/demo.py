# coding:utf-8
"""
InfoBadge 演示

展示内容：
- InfoBadge 信息徽章（数字类型）
- DotInfoBadge 圆点徽章
- IconInfoBadge 图标徽章
- InfoBadgeManager 自定义位置管理器
- 与按钮控件结合使用
"""
import sys

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    InfoBadge, DotInfoBadge, IconInfoBadge, ToolButton, BodyLabel,
    InfoBadgePosition, InfoBadgeManager, setTheme, Theme, PushButton,
)
from qfluentwidgets import FluentIcon as FIF


@InfoBadgeManager.register('Custom')
class CustomInfoBadgeManager(InfoBadgeManager):
    """自定义徽章位置管理器 — 居中顶部"""

    def position(self):
        pos = self.target.geometry().center()
        x = pos.x() - self.badge.width() // 2
        y = self.target.y() - self.badge.height() // 2
        return QPoint(x, y)


class Demo(QWidget):
    """InfoBadge 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('InfoBadge - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化徽章组件"""
        self.statusLabel = BodyLabel('点击按钮查看徽章变化', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # 数字信息徽章
        self.infoBadges = [
            InfoBadge.info(1),
            InfoBadge.success(10),
            InfoBadge.attension(100),
            InfoBadge.warning(1000),
            InfoBadge.error(10000),
            InfoBadge.custom('1w+', '#005fb8', '#60cdff'),
        ]

        # 圆点徽章
        self.dotBadges = [
            DotInfoBadge.info(),
            DotInfoBadge.success(),
            DotInfoBadge.attension(),
            DotInfoBadge.warning(),
            DotInfoBadge.error(),
            DotInfoBadge.custom('#005fb8', '#60cdff'),
        ]

        # 图标徽章
        self.iconBadges = [
            IconInfoBadge.info(FIF.ACCEPT_MEDIUM),
            IconInfoBadge.success(FIF.ACCEPT_MEDIUM),
            IconInfoBadge.attension(FIF.ACCEPT_MEDIUM),
            IconInfoBadge.warning(FIF.CANCEL_MEDIUM),
            IconInfoBadge.error(FIF.CANCEL_MEDIUM),
        ]
        customIconBadge = IconInfoBadge.custom(FIF.RINGER, '#005fb8', '#60cdff')
        customIconBadge.setFixedSize(32, 32)
        customIconBadge.setIconSize(QSize(16, 16))
        self.iconBadges.append(customIconBadge)

        # 与按钮结合的徽章
        self.button = ToolButton(FIF.BASKETBALL, self)
        self.button.clicked.connect(self.onButtonClicked)
        self.buttonBadge = InfoBadge.success(
            3, self, target=self.button, position=InfoBadgePosition.TOP_RIGHT
        )

        # 主题切换按钮
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(24)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)

        # 数字徽章行
        mainLayout.addWidget(BodyLabel('InfoBadge (数字)', self))
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        for badge in self.infoBadges:
            row1.addWidget(badge)
        mainLayout.addLayout(row1)

        # 圆点徽章行
        mainLayout.addWidget(BodyLabel('DotInfoBadge (圆点)', self))
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        for badge in self.dotBadges:
            row2.addWidget(badge)
        mainLayout.addLayout(row2)

        # 图标徽章行
        mainLayout.addWidget(BodyLabel('IconInfoBadge (图标)', self))
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        for badge in self.iconBadges:
            row3.addWidget(badge)
        mainLayout.addLayout(row3)

        # 按钮 + 徽章
        mainLayout.addWidget(BodyLabel('与按钮结合 (点击按钮递减)', self))
        mainLayout.addWidget(self.button, 0, Qt.AlignHCenter)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onButtonClicked(self):
        """按钮点击 — 递减徽章数字"""
        current = int(self.buttonBadge.text())
        if current > 0:
            current -= 1
            self.buttonBadge.setText(str(current))
            self.statusLabel.setText(f'徽章数值递减为: {current}')
        else:
            self.statusLabel.setText('徽章数值已为 0')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
