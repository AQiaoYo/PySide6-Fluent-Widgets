# coding:utf-8
"""
StateToolTip 演示

展示内容：
- 状态提示的显示与关闭
- 成功/失败状态的切换
- 位置调整
- 按钮触发交互
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import StateToolTip, PushButton, PrimaryPushButton, BodyLabel


class Demo(QWidget):
    """StateToolTip 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('StateToolTip - 演示')
        self.resize(500, 300)
        self.initWidgets()
        self.initLayout()
        self.stateTooltip = None

    def initWidgets(self):
        """初始化状态提示组件"""
        # 触发按钮
        self.btnStart = PrimaryPushButton('开始任务', self)
        self.btnStart.clicked.connect(self.onStartTask)

        self.btnSuccess = PushButton('标记成功', self)
        self.btnSuccess.clicked.connect(self.onMarkSuccess)
        self.btnSuccess.setEnabled(False)

        self.btnFail = PushButton('标记失败', self)
        self.btnFail.clicked.connect(self.onMarkFail)
        self.btnFail.setEnabled(False)

        # 状态显示
        self.statusLabel = BodyLabel('点击「开始任务」启动状态提示', self)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(16)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.btnStart)
        btnLayout.addWidget(self.btnSuccess)
        btnLayout.addWidget(self.btnFail)
        btnLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        mainLayout.addStretch(1)
        mainLayout.addWidget(self.statusLabel, 0, Qt.AlignCenter)

    def onStartTask(self):
        """开始任务，显示状态提示"""
        if self.stateTooltip:
            self.stateTooltip.close()

        self.stateTooltip = StateToolTip('正在处理', '请稍候...', self)
        self.stateTooltip.move(120, 30)
        self.stateTooltip.show()

        self.btnStart.setEnabled(False)
        self.btnSuccess.setEnabled(True)
        self.btnFail.setEnabled(True)
        self.statusLabel.setText('任务进行中...')

    def onMarkSuccess(self):
        """标记任务成功"""
        if self.stateTooltip:
            self.stateTooltip.setContent('任务完成')
            self.stateTooltip.setState(True)
            self.stateTooltip = None

        self.resetButtons()
        self.statusLabel.setText('任务已完成')

    def onMarkFail(self):
        """标记任务失败"""
        if self.stateTooltip:
            self.stateTooltip.setContent('任务失败')
            self.stateTooltip.setState(False)
            self.stateTooltip = None

        self.resetButtons()
        self.statusLabel.setText('任务已失败')

    def resetButtons(self):
        """重置按钮状态"""
        self.btnStart.setEnabled(True)
        self.btnSuccess.setEnabled(False)
        self.btnFail.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
