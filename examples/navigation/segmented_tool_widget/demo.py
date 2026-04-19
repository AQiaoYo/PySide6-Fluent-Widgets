# coding:utf-8
"""
SegmentedToolWidget 演示

展示内容：
- SegmentedToolWidget 图标分段控件
- SegmentedToggleToolWidget 切换式图标分段控件
- 与 QStackedWidget 页面联动
- currentItemChanged 信号
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout

from qfluentwidgets import SegmentedToggleToolWidget, BodyLabel, FluentIcon


class Demo(QWidget):
    """SegmentedToolWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SegmentedToolWidget - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.pivot = SegmentedToggleToolWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.statusLabel = BodyLabel('当前页面: 音乐', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # 创建页面
        self.songInterface = QLabel('音乐页面', self)
        self.albumInterface = QLabel('专辑页面', self)
        self.artistInterface = QLabel('歌手页面', self)

        self.addSubInterface(self.songInterface, 'songInterface', FluentIcon.MUSIC)
        self.addSubInterface(self.albumInterface, 'albumInterface', FluentIcon.ALBUM)
        self.addSubInterface(self.artistInterface, 'artistInterface', FluentIcon.PEOPLE)

        # 信号连接
        self.pivot.currentItemChanged.connect(self.onCurrentItemChanged)
        self.stackedWidget.setCurrentWidget(self.songInterface)
        self.pivot.setCurrentItem(self.songInterface.objectName())

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 20, 30, 30)

        mainLayout.addWidget(self.statusLabel)

        pivotLayout = QHBoxLayout()
        pivotLayout.addWidget(self.pivot, 0, Qt.AlignCenter)
        mainLayout.addLayout(pivotLayout)
        mainLayout.addWidget(self.stackedWidget, 1)

        # 页面样式
        for widget in [self.songInterface, self.albumInterface, self.artistInterface]:
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet('QLabel{background:rgb(242,242,242);border-radius:8px;font:20px}')

    def addSubInterface(self, widget: QLabel, objectName: str, icon):
        """添加子页面"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, icon=icon)

    def onCurrentItemChanged(self, routeKey: str):
        """页面切换"""
        widget = self.findChild(QLabel, routeKey)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)
            self.statusLabel.setText(f'当前页面: {widget.text().replace("页面", "")}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
