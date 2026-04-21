# coding:utf-8
"""
MultiSelectionComboBox Demo

展示内容:
- 多选下拉菜单基础用法
- 占位文本和预选项
- token 删除与状态同步
- 主题适配
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    MultiSelectionComboBox,
    setTheme,
    Theme,
    setFont,
)


class Demo(QWidget):
    """演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MultiSelectionComboBox - Demo")
        self.resize(760, 360)

        self.titleLabel = BodyLabel("MultiSelectionComboBox", self)
        setFont(self.titleLabel, 18)
        self.captionLabel = CaptionLabel(
            "用于同时选择多个选项，并以标签形式展示已选内容", self
        )

        self.comboBox = MultiSelectionComboBox(self)
        self.comboBox.setFixedWidth(520)
        self.comboBox.setPlaceholderText("请选择成员")
        self.comboBox.setMaxVisibleItems(6)
        self.comboBox.addItems(
            [
                "西宫硝子",
                "中野六花",
                "宝多六花",
                "雪之下雪乃",
                "千反田爱瑠",
                "一之濑花名",
                "加藤惠",
                "牧濑红莉栖",
                "三日月夜空",
            ]
        )
        self.comboBox.setCheckedIndexes([1, 3])

        self.resultLabel = BodyLabel("已选: 中野六花, 雪之下雪乃", self)
        self.comboBox.checkedTextsChanged.connect(
            lambda texts: self.resultLabel.setText(
                "已选: " + (" , ".join(texts) if texts else "无")
            )
        )

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(14)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.captionLabel)
        self.vBoxLayout.addWidget(self.comboBox, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.resultLabel)
        self.vBoxLayout.addStretch(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setTheme(Theme.LIGHT)
    w = Demo()
    w.show()
    app.exec()
