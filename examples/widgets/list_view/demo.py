# coding: utf-8
"""
ListWidget / ListView 演示

展示内容：
- ListWidget 列表控件
- ListView 列表视图
- 数据填充与选中信号
- 主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QListWidgetItem, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ListWidget, ListView, BodyLabel, setTheme, Theme, PushButton
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """ListWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ListWidget - 演示')
        self.resize(500, 500)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化列表组件"""
        self.statusLabel = BodyLabel('请选择一个项目', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        # ListWidget
        self.listWidget = ListWidget(self)
        items = [
            'Python', 'JavaScript', 'TypeScript', 'Go', 'Rust',
            'C++', 'Java', 'C#', 'Swift', 'Kotlin',
            'Ruby', 'PHP', 'Lua', 'Dart', 'Scala',
            'Haskell', 'Erlang', 'Clojure', 'F#', 'R',
        ]
        for item_text in items:
            item = QListWidgetItem(item_text)
            self.listWidget.addItem(item)

        self.listWidget.currentItemChanged.connect(self.onItemChanged)
        self.listWidget.itemClicked.connect(self.onItemClicked)

        # ListView（空数据展示结构）
        self.listView = ListView(self)
        for item_text in items[:10]:
            self.listView.addItem(item_text)

        # 主题切换
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.statusLabel)

        listLayout = QHBoxLayout()
        listLayout.setSpacing(16)
        listLayout.addWidget(self.listWidget, 1)
        listLayout.addWidget(self.listView, 1)
        mainLayout.addLayout(listLayout, 1)

        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onItemChanged(self, current: QListWidgetItem, previous: QListWidgetItem):
        """当前项变化"""
        if current:
            self.statusLabel.setText(f'当前选中: {current.text()}')

    def onItemClicked(self, item: QListWidgetItem):
        """项被点击"""
        self.statusLabel.setText(f'点击了: {item.text()}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
