# coding: utf-8
"""
ProgressInfoBar 演示

展示内容:
- 不确定模式 (旋转动画) 用于无法预估剩余时间的任务
- 确定模式 (按数值填充) 用于可量化的进度
- setComplete() 任务完成后切换状态图标并自动淡出
- finished 信号 / pauseAnimation / resumeAnimation
- 自定义进度环颜色与尺寸
"""
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget

from qfluentwidgets import (
    InfoBarPosition,
    ProgressInfoBar,
    PushButton,
)


class Demo(QWidget):
    """ProgressInfoBar 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('ProgressInfoBar - 演示')
        self.resize(720, 480)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化按钮"""
        self.button1 = PushButton('不确定进度', self)
        self.button2 = PushButton('确定进度', self)
        self.button3 = PushButton('任务完成', self)
        self.button4 = PushButton('任务失败', self)
        self.button5 = PushButton('自定义颜色', self)
        self.button6 = PushButton('暂停/恢复', self)

        self.button1.clicked.connect(self.createIndeterminateBar)
        self.button2.clicked.connect(self.createDeterminateBar)
        self.button3.clicked.connect(self.createCompleteSuccessBar)
        self.button4.clicked.connect(self.createCompleteErrorBar)
        self.button5.clicked.connect(self.createCustomColorBar)
        self.button6.clicked.connect(self.createPauseResumeBar)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(30, 30, 30, 30)
        for btn in [self.button1, self.button2, self.button3, self.button4,
                    self.button5, self.button6]:
            mainLayout.addWidget(btn)

    def createIndeterminateBar(self):
        """不确定模式: 旋转动画, 与截图一致"""
        ProgressInfoBar.indeterminate(
            title='请勿离开',
            content='正在发送邮件, 请耐心等待...',
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
        )

    def createDeterminateBar(self):
        """确定模式: 通过 QTimer 模拟进度推进"""
        bar = ProgressInfoBar.determinate(
            title='文件上传中',
            content='已上传 0 / 100 MB',
            maximum=100,
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
        )

        timer = QTimer(bar)
        timer.setInterval(60)

        def step():
            value = bar.value() + 2
            if value >= 100:
                value = 100
                bar.setValue(value)
                timer.stop()
                bar.setComplete(success=True, content='上传成功', autoCloseAfter=1500)
            else:
                bar.setContent(f'已上传 {value} / 100 MB')
                bar.setValue(value)

        timer.timeout.connect(step)
        timer.start()

    def createCompleteSuccessBar(self):
        """演示 setComplete(success=True): 不确定 -> 成功 -> 自动淡出"""
        bar = ProgressInfoBar.indeterminate(
            title='正在保存',
            content='正在保存文档到本地...',
            position=InfoBarPosition.TOP,
            parent=self,
        )
        bar.finished.connect(lambda ok: print(f'[finished] success={ok}'))
        QTimer.singleShot(1800, lambda: bar.setComplete(
            success=True, title='保存完成', content='文档已成功保存',
            autoCloseAfter=1500,
        ))

    def createCompleteErrorBar(self):
        """演示 setComplete(success=False): 失败状态 + 不自动关闭, 需手动关闭"""
        bar = ProgressInfoBar.indeterminate(
            title='正在连接',
            content='正在连接服务器...',
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self,
        )
        QTimer.singleShot(1500, lambda: bar.setComplete(
            success=False, title='连接失败', content='服务器无响应, 请检查网络后重试',
            autoCloseAfter=-1,
        ))

    def createCustomColorBar(self):
        """自定义进度环颜色与尺寸"""
        bar = ProgressInfoBar.indeterminate(
            title='正在同步',
            content='与云端同步配置中...',
            position=InfoBarPosition.BOTTOM,
            parent=self,
        )
        bar.setProgressColor('#13a10e', '#6ccb5f')
        bar.setRingSize(26, 3)

    def createPauseResumeBar(self):
        """演示 pauseAnimation / resumeAnimation"""
        bar = ProgressInfoBar.indeterminate(
            title='任务运行中',
            content='1 秒后暂停, 2 秒后恢复',
            position=InfoBarPosition.TOP_LEFT,
            parent=self,
        )
        QTimer.singleShot(1000, bar.pauseAnimation)
        QTimer.singleShot(3000, bar.resumeAnimation)
        QTimer.singleShot(5000, lambda: bar.setComplete(
            success=True, content='演示结束', autoCloseAfter=1000,
        ))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
