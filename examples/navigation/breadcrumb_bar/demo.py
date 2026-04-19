# coding:utf-8
"""
BreadcrumbBar 演示

展示内容：
- BreadcrumbBar 面包屑导航栏
- 与 QStackedWidget 联动切换页面
- 动态添加页面
- 字体与间距自定义
"""
import sys
from uuid import uuid1

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget

from qfluentwidgets import BreadcrumbBar, setFont, LineEdit, PrimaryToolButton, SubtitleLabel, FluentIcon


class Demo(QWidget):
    """BreadcrumbBar 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('BreadcrumbBar - 演示')
        self.resize(500, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.breadcrumbBar = BreadcrumbBar(self)
        self.stackedWidget = QStackedWidget(self)
        self.lineEdit = LineEdit(self)
        self.addButton = PrimaryToolButton(FluentIcon.SEND, self)

        self.lineEdit.setPlaceholderText('输入页面名称后按回车或点击按钮')
        self.addButton.clicked.connect(lambda: self.addInterface(self.lineEdit.text()))
        self.lineEdit.returnPressed.connect(lambda: self.addInterface(self.lineEdit.text()))

        # 设置面包屑样式
        setFont(self.breadcrumbBar, 20)
        self.breadcrumbBar.setSpacing(20)
        self.breadcrumbBar.currentItemChanged.connect(self.switchInterface)

        # 添加初始页面
        self.addInterface('主页')
        self.addInterface('文档')

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.breadcrumbBar)
        mainLayout.addWidget(self.stackedWidget, 1)

        inputLayout = QHBoxLayout()
        inputLayout.addWidget(self.lineEdit, 1)
        inputLayout.addWidget(self.addButton)
        mainLayout.addLayout(inputLayout)

    def addInterface(self, text: str):
        """添加新页面"""
        if not text:
            return

        widget = SubtitleLabel(text)
        widget.setObjectName(uuid1().hex)
        widget.setAlignment(Qt.AlignCenter)

        self.lineEdit.clear()
        self.stackedWidget.addWidget(widget)
        self.stackedWidget.setCurrentWidget(widget)
        self.breadcrumbBar.addItem(widget.objectName(), text)

    def switchInterface(self, objectName: str):
        """切换页面"""
        widget = self.findChild(SubtitleLabel, objectName)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
