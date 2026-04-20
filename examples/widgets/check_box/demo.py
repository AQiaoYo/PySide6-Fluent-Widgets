# coding:utf-8
"""
CheckBox 演示

展示内容：
- 两态复选框（勾选/未勾选）
- 三态复选框（勾选/部分勾选/未勾选）
- 禁用状态的复选框
- SubtitleCheckBox（带子标题的复选框）
- 信号槽连接获取状态变化
"""
import sys

sys.path.insert(0, r"D:\PySide6-Fluent-Widgets")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import CheckBox, SubtitleCheckBox, BodyLabel, CaptionLabel, setFont


class Demo(QWidget):
    """CheckBox 演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CheckBox - 演示")
        self.resize(500, 620)
        self.initWidgets()
        self.initLayout()

    def initWidgets(self):
        """初始化复选框组件"""
        # 两态复选框
        self.checkBox1 = CheckBox("两态复选框", self)
        self.checkBox1.stateChanged.connect(self.onStateChanged)

        # 三态复选框
        self.checkBox2 = CheckBox("三态复选框", self)
        self.checkBox2.setTristate(True)
        self.checkBox2.stateChanged.connect(self.onStateChanged)

        # 禁用状态
        self.checkBox3 = CheckBox("禁用 - 已勾选", self)
        self.checkBox3.setChecked(True)
        self.checkBox3.setEnabled(False)

        self.checkBox4 = CheckBox("禁用 - 未勾选", self)
        self.checkBox4.setEnabled(False)

        # SubtitleCheckBox
        self.subCb1 = SubtitleCheckBox("扬声器", self)
        self.subCb1.setSubtitle("Realtek(R) Audio")
        self.subCb1.setChecked(True)

        self.subCb2 = SubtitleCheckBox("麦克风", self)
        self.subCb2.setSubtitle("High Definition Audio Device")

        self.subCb3 = SubtitleCheckBox("蓝牙耳机", self)
        self.subCb3.setSubtitle("Connected")
        self.subCb3.setChecked(True)

        self.subCb4 = SubtitleCheckBox("禁用设备", self)
        self.subCb4.setSubtitle("此设备不可用")
        self.subCb4.setEnabled(False)

        # 状态显示标签
        self.statusLabel = BodyLabel("等待操作...", self)

    def initLayout(self):
        """初始化布局"""
        vLayout = QVBoxLayout(self)
        vLayout.setSpacing(12)
        vLayout.setContentsMargins(30, 30, 30, 30)

        # CheckBox 区域
        vLayout.addWidget(BodyLabel("CheckBox", self))

        vLayout.addWidget(self.checkBox1)
        vLayout.addWidget(self.checkBox2)
        vLayout.addWidget(self.checkBox3)
        vLayout.addWidget(self.checkBox4)
        vLayout.addSpacing(20)

        # SubtitleCheckBox 区域
        vLayout.addWidget(BodyLabel("SubtitleCheckBox", self))

        vLayout.addWidget(
            CaptionLabel("带子标题的复选框，使用方式与 QCheckBox 相同", self)
        )
        vLayout.addWidget(self.subCb1)
        vLayout.addWidget(self.subCb2)
        vLayout.addWidget(self.subCb3)
        vLayout.addWidget(self.subCb4)
        vLayout.addStretch(1)
        vLayout.addWidget(self.statusLabel)

    def onStateChanged(self, state):
        """状态变化时更新显示"""
        sender = self.sender()
        names = {0: "未勾选", 1: "部分勾选", 2: "已勾选"}
        self.statusLabel.setText(f'{sender.text()}: {names.get(state, "未知")}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
