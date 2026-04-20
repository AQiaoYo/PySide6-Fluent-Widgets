# coding:utf-8
"""Tag 和 Chip 组件演示

展示内容：
- Tag 基础用法和多种颜色变体
- Chip 基础用法、选中状态和关闭功能
- 图标组合展示
- 主题适配效果
"""
import sys
sys.path.insert(0, r'D:\PySide6-Fluent-Widgets')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy

from qfluentwidgets import (Tag, Chip, TagColor, BodyLabel, CaptionLabel,
                            setTheme, Theme, setFont)
from qfluentwidgets import FluentIcon as FIF


class Demo(QWidget):
    """演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tag & Chip - 演示')
        self.resize(600, 400)

        # Tag 演示区域
        self.tagLabel = BodyLabel('Tag 标签组件', self)
        setFont(self.tagLabel, 16)

        self.tagCaption = CaptionLabel('根据信息级别显示不同的背景色和前景色', self)

        self.tagRow1 = QHBoxLayout()
        self.tagRow1.setSpacing(8)
        self.tagRow1.setAlignment(Qt.AlignLeft)

        self.tagGray = Tag('默认', self)
        self.tagGray.setIcon(FIF.CAMERA)

        self.tagGreen = Tag('成功', self, FIF.PEOPLE)
        self.tagGreen.setColor(TagColor.GREEN)

        self.tagYellow = Tag('警告', self, FIF.PHONE)
        self.tagYellow.setColor(TagColor.YELLOW)

        self.tagRed = Tag('错误', self, FIF.SHARE)
        self.tagRed.setColor(TagColor.RED)

        self.tagBlue = Tag('信息', self, FIF.SYNC)
        self.tagBlue.setColor(TagColor.BLUE)

        self.tagRow1.addWidget(self.tagGray)
        self.tagRow1.addWidget(self.tagGreen)
        self.tagRow1.addWidget(self.tagYellow)
        self.tagRow1.addWidget(self.tagRed)
        self.tagRow1.addWidget(self.tagBlue)
        self.tagRow1.addStretch(1)

        # Tag 点击测试
        self.tagClickLabel = CaptionLabel('点击 Tag 测试：', self)
        self.tagClickResult = BodyLabel('未点击', self)
        self.tagGray.clicked.connect(lambda: self.tagClickResult.setText(f'已点击: {self.tagGray.text()}'))
        self.tagGreen.clicked.connect(lambda: self.tagClickResult.setText(f'已点击: {self.tagGreen.text()}'))

        # Chip 演示区域
        self.chipLabel = BodyLabel('Chip 芯片组件', self)
        setFont(self.chipLabel, 16)

        self.chipCaption = CaptionLabel('带有删除按钮，点击可切换选中状态', self)

        self.chipRow1 = QHBoxLayout()
        self.chipRow1.setSpacing(8)
        self.chipRow1.setAlignment(Qt.AlignLeft)

        self.chip1 = Chip('Attach camera', self, FIF.CAMERA)
        self.chip2 = Chip('Add friend', self, FIF.PEOPLE)
        self.chip2.setChecked(True)
        self.chip3 = Chip('Phone', self, FIF.PHONE)

        self.chipRow1.addWidget(self.chip1)
        self.chipRow1.addWidget(self.chip2)
        self.chipRow1.addWidget(self.chip3)
        self.chipRow1.addStretch(1)

        # 不可关闭的 Chip
        self.chipCaption2 = CaptionLabel('不可关闭的 Chip（setClosable(False)）', self)
        self.chipRow2 = QHBoxLayout()
        self.chipRow2.setSpacing(8)
        self.chipRow2.setAlignment(Qt.AlignLeft)

        self.chip4 = Chip('不可关闭', self)
        self.chip4.setClosable(False)
        self.chip5 = Chip('选中不可关闭', self, FIF.PEOPLE)
        self.chip5.setClosable(False)
        self.chip5.setChecked(True)

        self.chipRow2.addWidget(self.chip4)
        self.chipRow2.addWidget(self.chip5)
        self.chipRow2.addStretch(1)

        # Chip 事件监听
        self.chipEventLabel = CaptionLabel('Chip 事件：', self)
        self.chipEventResult = BodyLabel('等待事件...', self)

        self.chip1.clicked.connect(lambda: self._onChipEvent(self.chip1, 'clicked'))
        self.chip1.selectedChanged.connect(lambda c: self._onChipEvent(self.chip1, f'selected={c}'))
        self.chip1.closed.connect(lambda: self._onChipClosed(self.chip1))

        self.chip2.clicked.connect(lambda: self._onChipEvent(self.chip2, 'clicked'))
        self.chip2.selectedChanged.connect(lambda c: self._onChipEvent(self.chip2, f'selected={c}'))
        self.chip2.closed.connect(lambda: self._onChipClosed(self.chip2))

        self.chip3.clicked.connect(lambda: self._onChipEvent(self.chip3, 'clicked'))
        self.chip3.selectedChanged.connect(lambda c: self._onChipEvent(self.chip3, f'selected={c}'))
        self.chip3.closed.connect(lambda: self._onChipClosed(self.chip3))

        # 布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)

        self.vBoxLayout.addWidget(self.tagLabel)
        self.vBoxLayout.addWidget(self.tagCaption)
        self.vBoxLayout.addLayout(self.tagRow1)
        self.vBoxLayout.addWidget(self.tagClickLabel)
        self.vBoxLayout.addWidget(self.tagClickResult)
        self.vBoxLayout.addSpacing(20)

        self.vBoxLayout.addWidget(self.chipLabel)
        self.vBoxLayout.addWidget(self.chipCaption)
        self.vBoxLayout.addLayout(self.chipRow1)
        self.vBoxLayout.addWidget(self.chipCaption2)
        self.vBoxLayout.addLayout(self.chipRow2)
        self.vBoxLayout.addWidget(self.chipEventLabel)
        self.vBoxLayout.addWidget(self.chipEventResult)
        self.vBoxLayout.addStretch(1)

    def _onChipEvent(self, chip, event):
        self.chipEventResult.setText(f'{chip.text()}: {event}')

    def _onChipClosed(self, chip):
        chip.hide()
        self.chipEventResult.setText(f'{chip.text()}: closed (已隐藏)')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
