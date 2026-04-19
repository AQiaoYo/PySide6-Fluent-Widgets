# coding:utf-8
"""
CustomMessageBox 演示

展示内容：
- MessageBoxBase 自定义消息框基类
- 自定义输入验证 (validate)
- 错误提示与输入框高亮
- 按钮文本自定义
"""
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout

from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit, PushButton, CaptionLabel, setTheme, Theme


class CustomMessageBox(MessageBoxBase):
    """自定义 URL 打开对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('打开 URL', self)
        self.urlLineEdit = LineEdit(self)

        self.urlLineEdit.setPlaceholderText('输入文件、流或者播放列表的 URL')
        self.urlLineEdit.setClearButtonEnabled(True)

        self.warningLabel = CaptionLabel("URL 格式无效")
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))

        # 添加控件到视图布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.urlLineEdit)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        # 修改按钮文本
        self.yesButton.setText('打开')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)

    def validate(self):
        """重写验证方法"""
        isValid = self.urlLineEdit.text().lower().startswith("http://")
        self.warningLabel.setHidden(isValid)
        self.urlLineEdit.setError(not isValid)
        return isValid


class Demo(QWidget):
    """CustomMessageBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CustomMessageBox - 演示')
        self.resize(600, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化组件"""
        self.button = PushButton('打开 URL', self)
        self.button.clicked.connect(self.showDialog)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(self.button, 0, Qt.AlignCenter)

    def showDialog(self):
        """显示自定义对话框"""
        w = CustomMessageBox(self)
        if w.exec():
            print(w.urlLineEdit.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
