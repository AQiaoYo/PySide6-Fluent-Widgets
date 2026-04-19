# coding:utf-8
"""
TextBrowser 演示

展示内容：
- Markdown 文本渲染
- HTML 内容支持
- 占位文本
- 内容切换交互
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import TextBrowser, PushButton, BodyLabel


class Demo(QWidget):
    """TextBrowser 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TextBrowser - 演示')
        self.resize(500, 400)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化文本浏览器组件"""
        self.textBrowser = TextBrowser(self)
        self.textBrowser.setPlaceholderText('在此搜索...')

        # Markdown 内容
        self.markdownContent = """## Steel Ball Run

* **Johnny Joestar** - 替身: 牙 (Tusk)
* **Gyro Zeppeli** - 铁球回旋

> "这是一场关于回旋的竞赛。"
"""

        # HTML 内容
        self.htmlContent = """
        <h2>PySide6-Fluent-Widgets</h2>
        <p>基于 PySide6 的 Fluent Design 风格组件库。</p>
        <ul>
            <li>丰富的组件</li>
            <li>流畅的动画</li>
            <li>完善的主题系统</li>
        </ul>
        """

        self.textBrowser.setMarkdown(self.markdownContent)

        # 切换按钮
        self.btnMarkdown = PushButton('Markdown', self)
        self.btnMarkdown.clicked.connect(self.onShowMarkdown)

        self.btnHtml = PushButton('HTML', self)
        self.btnHtml.clicked.connect(self.onShowHtml)

        self.btnClear = PushButton('清空', self)
        self.btnClear.clicked.connect(self.onClear)

        self.statusLabel = BodyLabel('当前: Markdown 模式', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(20, 20, 20, 20)

        mainLayout.addWidget(self.textBrowser, 1)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(10)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnMarkdown)
        btnLayout.addWidget(self.btnHtml)
        btnLayout.addWidget(self.btnClear)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onShowMarkdown(self):
        """显示 Markdown 内容"""
        self.textBrowser.setMarkdown(self.markdownContent)
        self.statusLabel.setText('当前: Markdown 模式')

    def onShowHtml(self):
        """显示 HTML 内容"""
        self.textBrowser.setHtml(self.htmlContent)
        self.statusLabel.setText('当前: HTML 模式')

    def onClear(self):
        """清空内容"""
        self.textBrowser.clear()
        self.statusLabel.setText('内容已清空')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
