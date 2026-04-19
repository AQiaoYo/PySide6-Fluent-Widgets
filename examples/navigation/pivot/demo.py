# coding:utf-8
"""
Pivot 演示

展示内容：
- Pivot 分段控制器
- 与 QStackedWidget 页面联动
- currentItemChanged 信号
- 主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QLabel

from qfluentwidgets import Pivot, BodyLabel, setTheme, Theme, PushButton
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """Pivot 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Pivot - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.statusLabel = BodyLabel('当前页面: Song', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # 创建页面
        self.songInterface = QLabel('歌曲页面', self)
        self.albumInterface = QLabel('专辑页面', self)
        self.artistInterface = QLabel('歌手页面', self)

        self.addSubInterface(self.songInterface, 'songInterface', '歌曲')
        self.addSubInterface(self.albumInterface, 'albumInterface', '专辑')
        self.addSubInterface(self.artistInterface, 'artistInterface', '歌手')

        # 信号连接
        self.pivot.currentItemChanged.connect(self.onCurrentItemChanged)
        self.stackedWidget.setCurrentWidget(self.songInterface)
        self.pivot.setCurrentItem(self.songInterface.objectName())

        # 主题切换
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 20, 30, 30)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        mainLayout.addWidget(self.stackedWidget, 1)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

        # 页面样式
        for widget in [self.songInterface, self.albumInterface, self.artistInterface]:
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet('QLabel{background:rgb(242,242,242);border-radius:8px;font:20px}')

    def addSubInterface(self, widget: QLabel, objectName: str, text: str):
        """添加子页面"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text)

    def onCurrentItemChanged(self, routeKey: str):
        """页面切换"""
        widget = self.findChild(QLabel, routeKey)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)
            self.statusLabel.setText(f'当前页面: {widget.text()}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
