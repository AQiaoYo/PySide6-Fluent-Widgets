# coding:utf-8
"""
LineEdit 演示

展示内容：
- LineEdit 单行输入框
- SearchLineEdit 搜索输入框
- QCompleter 自动补全
- 清除按钮与占位符文本
- 主题切换
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QCompleter

from qfluentwidgets import LineEdit, PushButton, SearchLineEdit, BodyLabel, setTheme, Theme


class Demo(QWidget):
    """LineEdit 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('LineEdit - 演示')
        self.resize(400, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化输入框"""
        self.statusLabel = BodyLabel('请输入内容进行搜索', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.lineEdit = SearchLineEdit(self)
        self.button = PushButton('搜索', self)

        # 自动补全数据
        searchTerms = [
            'Python', 'JavaScript', 'TypeScript', 'Go', 'Rust',
            'C++', 'Java', 'C#', 'Swift', 'Kotlin',
            'Ruby', 'PHP', 'Lua', 'Dart', 'Scala',
        ]
        self.completer = QCompleter(searchTerms, self.lineEdit)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(10)
        self.lineEdit.setCompleter(self.completer)

        self.lineEdit.setFixedSize(200, 33)
        self.lineEdit.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText('搜索编程语言')
        self.lineEdit.returnPressed.connect(self.onSearch)
        self.button.clicked.connect(self.onSearch)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.lineEdit, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.button, 0, Qt.AlignCenter)

    def onSearch(self):
        """搜索按钮点击"""
        text = self.lineEdit.text()
        if text:
            self.statusLabel.setText(f'搜索: {text}')
        else:
            self.statusLabel.setText('请输入内容进行搜索')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
