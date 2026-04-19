# coding:utf-8
"""
AcrylicLineEdit 演示

展示内容：
- AcrylicSearchLineEdit 亚克力搜索输入框
- QCompleter 自动补全
- 清除按钮
- 占位符文本
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QCompleter

from qfluentwidgets import PushButton
from qfluentwidgets.components.material import AcrylicSearchLineEdit


class Demo(QWidget):
    """AcrylicLineEdit 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AcrylicLineEdit - 演示')
        self.resize(400, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化输入框"""
        self.lineEdit = AcrylicSearchLineEdit(self)
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

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(self.lineEdit, 0, Qt.AlignCenter)
        mainLayout.addWidget(self.button, 0, Qt.AlignCenter)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
