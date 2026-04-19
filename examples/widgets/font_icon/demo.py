# coding:utf-8
"""
FluentFontIcon 演示

展示内容：
- FluentFontIconBase 自定义字体图标基类
- 自定义图标字体加载
- iconNameMapPath 名称映射
- 多种按钮类型使用自定义图标
- 主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import (
    FluentFontIconBase, Theme, PushButton, SwitchButton,
    TogglePushButton, toggleTheme, HyperlinkButton, BodyLabel,
)


class PhotoFontIcon(FluentFontIconBase):
    """照片应用图标字体"""

    def path(self, theme=Theme.AUTO):
        return "font/PhotosIcons.ttf"

    def iconNameMapPath(self):
        """名称映射路径，用于 fromName 方法"""
        return "font/PhotoIcons.json"


class MediaPlayerFontIcon(FluentFontIconBase):
    """媒体播放器图标字体"""

    def path(self, theme=Theme.AUTO):
        return "font/MediaPlayerIcons.ttf"


class Demo(QWidget):
    """FluentFontIcon 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FluentFontIcon - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.statusLabel = BodyLabel('切换主题查看图标变化', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.themeButton = SwitchButton(self)
        self.themeButton.setOnText("暗色")
        self.themeButton.setOffText("亮色")
        self.themeButton.checkedChanged.connect(self.toggleTheme)

        # 使用自定义图标字体
        self.button1 = PushButton(PhotoFontIcon("\ue77b"), "默认样式")
        self.button2 = PushButton(PhotoFontIcon.fromName("cloud").colored("#275EFF", Qt.GlobalColor.darkCyan), "自定义颜色")
        self.button3 = TogglePushButton(PhotoFontIcon.fromName("smile"), "切换按钮")
        self.button4 = HyperlinkButton(MediaPlayerFontIcon("\uf414"), "http://qfluentwidgets.com", "超链接")

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.button1)
        mainLayout.addWidget(self.button2)
        mainLayout.addWidget(self.button3)
        mainLayout.addWidget(self.button4)
        mainLayout.addWidget(self.themeButton)

    def toggleTheme(self, isChecked):
        """主题切换"""
        toggleTheme()
        if isChecked:
            self.setStyleSheet("Demo{background:rgb(32,32,32)}")
            self.statusLabel.setStyleSheet("color: white")
        else:
            self.setStyleSheet("Demo{background:rgb(242,242,242)}")
            self.statusLabel.setStyleSheet("color: black")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
