# coding:utf-8
"""
SwitchButton 演示

展示内容：
- 标准开关按钮（On/Off）
- 自定义文本开关按钮
- 禁用状态的开关按钮
- 信号槽连接响应状态切换
"""
import sys

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import SwitchButton, BodyLabel


class Demo(QWidget):
    """SwitchButton 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SwitchButton - 演示')
        self.resize(400, 250)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化开关按钮组件"""
        # 标准开关（默认 Off）
        self.switch1 = SwitchButton(self)
        self.switch1.setText('Off')
        self.switch1.checkedChanged.connect(self.onSwitchToggled)

        # 默认开启的开关
        self.switch2 = SwitchButton(self)
        self.switch2.setChecked(True)
        self.switch2.setText('On')
        self.switch2.checkedChanged.connect(self.onSwitchToggled)

        # 禁用状态
        self.switch3 = SwitchButton(self)
        self.switch3.setChecked(True)
        self.switch3.setEnabled(False)
        self.switch3.setText('On（禁用）')

        # 状态显示
        self.statusLabel = BodyLabel('点击开关查看状态变化', self)

    def initLayout(self):
        """初始化布局"""
        vLayout = QVBoxLayout(self)
        vLayout.setSpacing(20)
        vLayout.setContentsMargins(30, 30, 30, 30)

        vLayout.addWidget(self.switch1)
        vLayout.addWidget(self.switch2)
        vLayout.addWidget(self.switch3)
        vLayout.addStretch(1)
        vLayout.addWidget(self.statusLabel)

    def onSwitchToggled(self, isChecked: bool):
        """开关状态切换时更新文本和显示"""
        sender = self.sender()
        text = 'On' if isChecked else 'Off'
        sender.setText(text)
        self.statusLabel.setText(f'{sender.text()}: {"开启" if isChecked else "关闭"}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
