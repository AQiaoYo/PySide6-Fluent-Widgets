# coding:utf-8
"""
WidgetMenu 演示

展示内容：
- RoundMenu 圆角菜单
- 自定义 ProfileCard 卡片组件
- 菜单中嵌入自定义控件
- 账户管理菜单示例
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    RoundMenu, FluentIcon, Action, AvatarWidget, BodyLabel,
    HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme,
)


class ProfileCard(QWidget):
    """个人信息卡片"""

    def __init__(self, avatarPath: str, name: str, email: str, parent=None):
        super().__init__(parent=parent)
        self.avatar = AvatarWidget(avatarPath, self)
        self.nameLabel = BodyLabel(name, self)
        self.emailLabel = CaptionLabel(email, self)
        self.logoutButton = HyperlinkButton('https://qfluentwidgets.com', '注销', self)

        color = QColor(206, 206, 206) if isDarkTheme() else QColor(96, 96, 96)
        self.emailLabel.setStyleSheet('QLabel{color: ' + color.name() + '}')

        color = QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0)
        self.nameLabel.setStyleSheet('QLabel{color: ' + color.name() + '}')
        setFont(self.logoutButton, 13)

        self.setFixedSize(307, 82)
        self.avatar.setRadius(24)
        self.avatar.move(2, 6)
        self.nameLabel.move(64, 13)
        self.emailLabel.move(64, 32)
        self.logoutButton.move(52, 48)


class Demo(QWidget):
    """WidgetMenu 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('WidgetMenu - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.label = BodyLabel('在此区域点击鼠标右键', self)
        self.label.setAlignment(Qt.AlignCenter)
        setFont(self.label, 18)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.label)
        self.setStyleSheet('Demo{background: white}')

    def contextMenuEvent(self, e) -> None:
        """右键显示菜单"""
        menu = RoundMenu(parent=self)

        # 自定义卡片
        card = ProfileCard('resource/shoko.png', '用户名称', 'user@example.com', menu)
        menu.addWidget(card, selectable=False)

        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.PEOPLE, '管理账户和设置'),
            Action(FluentIcon.SHOPPING_CART, '支付方式'),
            Action(FluentIcon.CODE, '兑换代码和礼品卡'),
        ])
        menu.addSeparator()
        menu.addAction(Action(FluentIcon.SETTING, '设置'))
        menu.exec(e.globalPos())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
