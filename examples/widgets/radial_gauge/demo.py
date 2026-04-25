# coding:utf-8
"""RadialGauge 演示"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import RadialGauge, SpinBox, BodyLabel, PushButton, FluentIcon, setTheme


class Demo(QWidget):
    """RadialGauge 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('RadialGauge - 演示')
        self.resize(420, 420)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化仪表盘组件"""
        self.statusLabel = BodyLabel('进度: 40%', self)
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.gauge = RadialGauge(self)
        self.gauge.setValue(40)

        self.speedGauge = RadialGauge(self)
        self.speedGauge.setRange(0, 240)
        self.speedGauge.setValue(80)
        self.speedGauge.setFormat('%v km/h')
        self.speedGauge.setGaugeSize(130, 14)
        self.speedGauge.setTextSizeRange(8, 22)

        self.flatGauge = RadialGauge(self)
        self.flatGauge.setValue(66)
        self.flatGauge.setFormat('%p%')
        self.flatGauge.setGaugeSize(100)
        self.flatGauge.setGaugeStyle(thicknessRatio=0.08)

        self.thickGauge = RadialGauge(self)
        self.thickGauge.setValue(72)
        self.thickGauge.setGaugeSize(100)
        self.thickGauge.setGaugeStyle(thicknessRatio=0.18, startAngle=210, spanAngle=-240)
        self.thickGauge.setGaugeColor('#ff8c00', '#ffb45c', '#dedede', '#555555')

        self.spinBox = SpinBox(self)
        self.spinBox.setRange(0, 100)
        self.spinBox.setValue(40)
        self.spinBox.valueChanged.connect(self.onSpinBoxValueChanged)

        self.themeBtn = PushButton(FluentIcon.CONSTRACT, '切换主题', self)
        self.themeBtn.clicked.connect(setTheme)

    def initLayout(self):
        """初始化布局"""
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(18)
        mainLayout.setContentsMargins(30, 30, 30, 30)

        mainLayout.addWidget(self.statusLabel)
        mainLayout.addWidget(self.gauge, 0, Qt.AlignHCenter)

        gaugeLayout = QHBoxLayout()
        gaugeLayout.addWidget(self.spinBox, 0, Qt.AlignHCenter)
        gaugeLayout.addWidget(self.speedGauge, 0, Qt.AlignHCenter)
        mainLayout.addLayout(gaugeLayout)

        styleLayout = QHBoxLayout()
        styleLayout.addWidget(self.flatGauge, 0, Qt.AlignHCenter)
        styleLayout.addWidget(self.thickGauge, 0, Qt.AlignHCenter)
        mainLayout.addLayout(styleLayout)

        mainLayout.addWidget(self.themeBtn, 0, Qt.AlignHCenter)
        mainLayout.addStretch(1)

    def onSpinBoxValueChanged(self, value: int):
        """SpinBox 数值变化"""
        self.gauge.setValue(value)
        self.statusLabel.setText(f'进度: {value}%')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
