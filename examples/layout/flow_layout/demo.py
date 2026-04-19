# coding:utf-8
"""
FlowLayout 演示

展示内容：
- 流式布局基础用法
- 动画效果配置
- 动态添加/插入组件
- 间距与边距调整
"""
import sys

from PySide6.QtCore import QEasingCurve, Qt
from PySide6.QtWidgets import QApplication, QWidget

from qfluentwidgets import FlowLayout, PushButton, PrimaryPushButton, ToolButton
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """FlowLayout 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FlowLayout - 演示')
        self.resize(400, 300)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化流式布局组件"""
        # 创建流式布局（启用动画）
        self.flowLayout = FlowLayout(self, needAni=True)

        # 配置动画参数：250ms 时长，OutQuad 缓动曲线
        self.flowLayout.setAnimation(250, QEasingCurve.OutQuad)

        # 设置边距和间距
        self.flowLayout.setContentsMargins(20, 20, 20, 20)
        self.flowLayout.setVerticalSpacing(12)
        self.flowLayout.setHorizontalSpacing(10)

        # 添加不同类型的按钮
        self.flowLayout.addWidget(PushButton('流式'))
        self.flowLayout.addWidget(PushButton('布局'))
        self.flowLayout.addWidget(PushButton('自动换行'))
        self.flowLayout.addWidget(PrimaryPushButton('主题色'))
        self.flowLayout.addWidget(ToolButton(FIF.SETTING))
        self.flowLayout.addWidget(PushButton('按钮'))
        self.flowLayout.addWidget(PushButton('排列'))

        # 在指定位置插入按钮
        self.flowLayout.insertWidget(2, PrimaryPushButton('插入'))

        self.setStyleSheet(
            'Demo{background: white} '
            'QPushButton{padding: 5px 12px; font:14px "Microsoft YaHei"}'
        )

    def initLayout(self):
        """布局已在 initWidgets 中设置完成"""
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
