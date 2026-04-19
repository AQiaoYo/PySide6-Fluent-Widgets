# coding: utf-8
"""
TableWidget / TableView 演示

展示内容：
- TableWidget 表格控件
- 自定义 TableItemDelegate
- 边框与圆角设置
- 数据填充与选中信号
- 主题切换
"""
import sys

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QTableWidgetItem, QWidget, QVBoxLayout

from qfluentwidgets import (
    TableWidget, TableItemDelegate, BodyLabel, isDarkTheme, setTheme, Theme, PushButton,
)
from qfluentwidgets import FluentIcon as FIF


class CustomTableItemDelegate(TableItemDelegate):
    """自定义表格项委托 — 高亮艺术家列"""

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        super().initStyleOption(option, index)
        if index.column() != 1:
            return

        if isDarkTheme():
            option.palette.setColor(QPalette.Text, Qt.white)
            option.palette.setColor(QPalette.HighlightedText, Qt.white)
        else:
            option.palette.setColor(QPalette.Text, Qt.red)
            option.palette.setColor(QPalette.HighlightedText, Qt.red)


class Demo(QWidget):
    """TableWidget 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TableWidget - 演示')
        self.resize(800, 600)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化表格组件"""
        self.statusLabel = BodyLabel('请选择一个单元格', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.tableWidget = TableWidget(self)
        self.tableWidget.setBorderVisible(True)
        self.tableWidget.setBorderRadius(8)
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setRowCount(30)
        self.tableWidget.setColumnCount(5)

        songInfos = [
            ['かばん', 'aiko', 'かばん', '2004', '5:04'],
            ['爱你', '王心凌', '爱你', '2004', '3:39'],
            ['星のない世界', 'aiko', '星のない世界/横顔', '2007', '5:30'],
            ['横顔', 'aiko', '星のない世界/横顔', '2007', '5:06'],
            ['秘密', 'aiko', '秘密', '2008', '6:27'],
            ['シアワセ', 'aiko', '秘密', '2008', '5:25'],
            ['二人', 'aiko', '二人', '2008', '5:00'],
            ['スパークル', 'RADWIMPS', '君の名は。', '2016', '8:54'],
            ['なんでもないや', 'RADWIMPS', '君の名は。', '2016', '3:16'],
            ['前前前世', 'RADWIMPS', '人間開花', '2016', '4:35'],
            ['恋をしたのは', 'aiko', '恋をしたのは', '2016', '6:02'],
            ['夏バテ', 'aiko', '恋をしたのは', '2016', '4:41'],
            ['もっと', 'aiko', 'もっと', '2016', '4:50'],
            ['問題集', 'aiko', 'もっと', '2016', '4:18'],
            ['半袖', 'aiko', 'もっと', '2016', '5:50'],
        ]
        songInfos += songInfos  # 复制一份填满 30 行

        for i, songInfo in enumerate(songInfos):
            for j in range(5):
                self.tableWidget.setItem(i, j, QTableWidgetItem(songInfo[j]))

        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setHorizontalHeaderLabels(['标题', '艺术家', '专辑', '年份', '时长'])
        self.tableWidget.resizeColumnsToContents()

        # 信号连接
        self.tableWidget.cellClicked.connect(self.onCellClicked)
        self.tableWidget.currentItemChanged.connect(self.onItemChanged)

        # 主题切换
        self.themeBtn = PushButton(FIF.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 20, 30, 20)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.tableWidget, 1)
        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignCenter)

    def onCellClicked(self, row: int, column: int):
        """单元格点击"""
        item = self.tableWidget.item(row, column)
        if item:
            self.statusLabel.setText(f'点击: 第 {row + 1} 行, 第 {column + 1} 列 — {item.text()}')

    def onItemChanged(self, current: QTableWidgetItem, previous: QTableWidgetItem):
        """当前项变化"""
        if current:
            self.statusLabel.setText(
                f'选中: 第 {current.row() + 1} 行, 第 {current.column() + 1} 列 — {current.text()}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
