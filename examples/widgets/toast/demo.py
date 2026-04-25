# coding:utf-8
"""Toast / ProgressToast 组件演示

展示内容:
1. Toast（静态顶部色条，手动关闭）：成功/错误/警告/信息
2. ProgressToast（底部进度条，自动关闭）：确定进度（3秒倒计时）、不确定进度（循环动画）
3. 亮色/暗色主题切换
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel

sys.path.insert(0, '../../../')

from qfluentwidgets import (
    PushButton, TogglePushButton, setTheme, Theme,
    InfoBarPosition
)
from qfluentwidgets import Toast, ProgressToast, ToastType


class DemoWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Toast / ProgressToast Demo')
        self.resize(760, 560)
        self._initLayout()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        # 主题切换
        self.themeBtn = TogglePushButton('切换暗色主题', self)
        self.themeBtn.toggled.connect(self._onThemeToggled)
        layout.addWidget(self.themeBtn)

        # ── Toast 区域（静态色条，手动关闭）──────────────────────────────
        toastLabel = QLabel('Toast（静态顶部色条，手动关闭）', self)
        layout.addWidget(toastLabel)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        successBtn = PushButton('成功 Toast', self)
        errorBtn = PushButton('错误 Toast', self)
        warningBtn = PushButton('警告 Toast', self)
        infoBtn = PushButton('信息 Toast', self)

        successBtn.clicked.connect(self._showToastSuccess)
        errorBtn.clicked.connect(self._showToastError)
        warningBtn.clicked.connect(self._showToastWarning)
        infoBtn.clicked.connect(self._showToastInfo)

        for btn in [successBtn, errorBtn, warningBtn, infoBtn]:
            row1.addWidget(btn)
        layout.addLayout(row1)

        # ── ProgressToast 区域（底部进度条，自动关闭）────────────────────
        progressLabel = QLabel('ProgressToast（底部进度条）', self)
        layout.addWidget(progressLabel)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        determinateBtn = PushButton('确定进度（3秒）', self)
        indeterminateBtn = PushButton('不确定进度（循环）', self)
        stackBtn = PushButton('堆叠 3 个', self)
        customBtn = PushButton('自定义主题色', self)

        determinateBtn.clicked.connect(self._showProgressDeterminate)
        indeterminateBtn.clicked.connect(self._showProgressIndeterminate)
        stackBtn.clicked.connect(self._showProgressStacked)
        customBtn.clicked.connect(self._showProgressCustom)

        for btn in [determinateBtn, indeterminateBtn, stackBtn, customBtn]:
            row2.addWidget(btn)
        layout.addLayout(row2)

        # ── 不同位置 ──────────────────────────────────────────────────────
        posLabel = QLabel('不同位置（ProgressToast）', self)
        layout.addWidget(posLabel)

        row3 = QHBoxLayout()
        row3.setSpacing(10)

        topBtn = PushButton('顶部居中', self)
        topRightBtn = PushButton('右上角', self)
        topLeftBtn = PushButton('左上角', self)
        bottomBtn = PushButton('底部居中', self)

        topBtn.clicked.connect(lambda: ProgressToast.info(
            '顶部通知', '显示在窗口顶部居中位置', duration=3000,
            position=InfoBarPosition.TOP, parent=self))
        topRightBtn.clicked.connect(lambda: ProgressToast.info(
            '右上角通知', '显示在窗口右上角', duration=3000,
            position=InfoBarPosition.TOP_RIGHT, parent=self))
        topLeftBtn.clicked.connect(lambda: ProgressToast.info(
            '左上角通知', '显示在窗口左上角', duration=3000,
            position=InfoBarPosition.TOP_LEFT, parent=self))
        bottomBtn.clicked.connect(lambda: ProgressToast.info(
            '底部通知', '显示在窗口底部居中位置', duration=3000,
            position=InfoBarPosition.BOTTOM, parent=self))

        for btn in [topBtn, topRightBtn, topLeftBtn, bottomBtn]:
            row3.addWidget(btn)
        layout.addLayout(row3)

    def _onThemeToggled(self, checked: bool):
        setTheme(Theme.DARK if checked else Theme.LIGHT)

    # ── Toast 工厂 ────────────────────────────────────────────────────────

    def _showToastSuccess(self):
        Toast.success('操作成功', '文件已成功保存到本地磁盘',
                      position=InfoBarPosition.BOTTOM_RIGHT, parent=self)

    def _showToastError(self):
        Toast.error('操作失败', '网络连接超时，请检查网络设置后重试',
                    position=InfoBarPosition.BOTTOM_RIGHT, parent=self)

    def _showToastWarning(self):
        Toast.warning('注意', '磁盘空间不足，剩余空间低于 1 GB',
                      position=InfoBarPosition.BOTTOM_RIGHT, parent=self)

    def _showToastInfo(self):
        Toast.info('提示', '新版本 v2.0 已发布，点击查看更新内容',
                   position=InfoBarPosition.BOTTOM_RIGHT, parent=self)

    # ── ProgressToast 工厂 ────────────────────────────────────────────────

    def _showProgressDeterminate(self):
        ProgressToast.success(
            '正在保存',
            '文件保存中，3 秒后自动关闭',
            duration=3000,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self
        )

    def _showProgressIndeterminate(self):
        ProgressToast.new(
            ToastType.INFO,
            '正在处理',
            '请稍候，任务正在后台运行...',
            duration=-1,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self
        )

    def _showProgressStacked(self):
        ProgressToast.success('第一条', '成功完成任务 A', duration=5000, parent=self)
        ProgressToast.warning('第二条', '任务 B 需要注意', duration=5000, parent=self)
        ProgressToast.error('第三条', '任务 C 执行失败', duration=5000, parent=self)

    def _showProgressCustom(self):
        ProgressToast.new(
            ToastType.CUSTOM,
            '自定义主题色',
            '进度条颜色跟随当前主题色变化',
            duration=4000,
            position=InfoBarPosition.BOTTOM_RIGHT,
            parent=self
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = DemoWindow()
    w.show()
    sys.exit(app.exec())
