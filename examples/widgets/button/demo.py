# coding:utf-8
"""
Button 演示

展示内容：
- ToolButton 工具按钮（标准/下拉/分割/主色/切换/透明/胶囊）
- PushButton 推送按钮（标准/主色/透明/切换/下拉/分割/超链接/胶囊）
- 按钮状态（禁用、选中）
- 自定义样式表
- 主题切换
"""
import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout

from qfluentwidgets import (
    Action, DropDownPushButton, DropDownToolButton, PushButton, PrimaryPushButton,
    HyperlinkButton, setTheme, Theme, ToolButton, ToggleButton, RoundMenu,
    SplitPushButton, SplitToolButton, PrimaryToolButton, PrimarySplitPushButton,
    PrimarySplitToolButton, PrimaryDropDownPushButton, PrimaryDropDownToolButton,
    TogglePushButton, ToggleToolButton, TransparentPushButton, TransparentToolButton,
    TransparentToggleToolButton, TransparentTogglePushButton, TransparentDropDownToolButton,
    TransparentDropDownPushButton, PillPushButton, PillToolButton, BodyLabel,
)
from qfluentwidgets import FluentIcon as FIF


class ButtonView(QWidget):
    """按钮视图基类"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("ButtonView{background: rgb(255,255,255)}")


class ToolButtonDemo(ButtonView):
    """工具按钮演示"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Button - 工具按钮')
        self.resize(400, 350)

        self.menu = RoundMenu(parent=self)
        self.menu.addAction(QAction(FIF.SEND_FILL.icon(), '发送'))
        self.menu.addAction(QAction(FIF.SAVE.icon(), '保存'))

        # 标准工具按钮
        self.toolButton = ToolButton(FIF.SETTING, self)

        # 下拉工具按钮
        self.dropDownToolButton = DropDownToolButton(FIF.MAIL, self)
        self.dropDownToolButton.setMenu(self.menu)

        # 分割工具按钮
        self.splitToolButton = SplitToolButton(FIF.GITHUB, self)
        self.splitToolButton.setFlyout(self.menu)

        # 主色工具按钮
        self.primaryToolButton = PrimaryToolButton(FIF.SETTING, self)

        # 主色下拉工具按钮
        self.primaryDropDownToolButton = PrimaryDropDownToolButton(FIF.MAIL, self)
        self.primaryDropDownToolButton.setMenu(self.menu)

        # 主色分割工具按钮
        self.primarySplitToolButton = PrimarySplitToolButton(FIF.GITHUB, self)
        self.primarySplitToolButton.setFlyout(self.menu)

        # 切换工具按钮
        self.toggleToolButton = ToggleToolButton(FIF.SETTING, self)
        self.toggleToolButton.toggled.connect(lambda: print('切换状态变化'))
        self.toggleToolButton.toggle()

        # 透明切换工具按钮
        self.transparentToggleToolButton = TransparentToggleToolButton(FIF.GITHUB, self)

        # 透明工具按钮
        self.tranparentToolButton = TransparentToolButton(FIF.MAIL, self)

        # 透明下拉工具按钮
        self.transparentDropDownToolButton = TransparentDropDownToolButton(FIF.MAIL, self)
        self.transparentDropDownToolButton.setMenu(self.menu)

        # 胶囊工具按钮
        self.pillToolButton1 = PillToolButton(FIF.CALENDAR, self)
        self.pillToolButton2 = PillToolButton(FIF.CALENDAR, self)
        self.pillToolButton3 = PillToolButton(FIF.CALENDAR, self)
        self.pillToolButton2.setDisabled(True)
        self.pillToolButton3.setChecked(True)
        self.pillToolButton3.setDisabled(True)

        # 布局
        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.toolButton, 0, 0)
        self.gridLayout.addWidget(self.dropDownToolButton, 0, 1)
        self.gridLayout.addWidget(self.splitToolButton, 0, 2)
        self.gridLayout.addWidget(self.primaryToolButton, 1, 0)
        self.gridLayout.addWidget(self.primaryDropDownToolButton, 1, 1)
        self.gridLayout.addWidget(self.primarySplitToolButton, 1, 2)
        self.gridLayout.addWidget(self.toggleToolButton, 2, 0)
        self.gridLayout.addWidget(self.transparentToggleToolButton, 2, 1)
        self.gridLayout.addWidget(self.tranparentToolButton, 3, 0)
        self.gridLayout.addWidget(self.transparentDropDownToolButton, 3, 1)
        self.gridLayout.addWidget(self.pillToolButton1, 4, 0)
        self.gridLayout.addWidget(self.pillToolButton2, 4, 1)
        self.gridLayout.addWidget(self.pillToolButton3, 4, 2)


class PushButtonDemo(ButtonView):
    """推送按钮演示"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Button - 推送按钮')
        self.resize(500, 700)

        self.menu = RoundMenu(parent=self)
        self.menu.addAction(Action(FIF.BASKETBALL, '篮球'))
        self.menu.addAction(Action(FIF.ALBUM, '相册'))
        self.menu.addAction(Action(FIF.MUSIC, '音乐'))

        # 标准推送按钮
        self.pushButton1 = PushButton('标准按钮')
        self.pushButton2 = PushButton(FIF.FOLDER, '带图标按钮', self)

        # 主色按钮
        self.primaryButton1 = PrimaryPushButton('主色按钮', self)
        self.primaryButton2 = PrimaryPushButton(FIF.UPDATE, '带图标主色按钮', self)

        # 透明按钮
        self.transparentPushButton1 = TransparentPushButton('透明按钮', self)
        self.transparentPushButton2 = TransparentPushButton(FIF.BOOK_SHELF, '透明按钮', self)

        # 切换按钮
        self.toggleButton1 = TogglePushButton('切换按钮', self)
        self.toggleButton2 = TogglePushButton(FIF.SEND, '切换按钮', self)

        # 透明切换按钮
        self.transparentTogglePushButton1 = TransparentTogglePushButton('透明切换按钮', self)
        self.transparentTogglePushButton2 = TransparentTogglePushButton(FIF.BOOK_SHELF, '透明切换按钮', self)

        # 下拉按钮
        self.dropDownPushButton1 = DropDownPushButton('邮件', self)
        self.dropDownPushButton2 = DropDownPushButton(FIF.MAIL, '邮件', self)
        self.dropDownPushButton1.setMenu(self.menu)
        self.dropDownPushButton2.setMenu(self.menu)

        # 主色下拉按钮
        self.primaryDropDownPushButton1 = PrimaryDropDownPushButton('邮件', self)
        self.primaryDropDownPushButton2 = PrimaryDropDownPushButton(FIF.MAIL, '邮件', self)
        self.primaryDropDownPushButton1.setMenu(self.menu)
        self.primaryDropDownPushButton2.setMenu(self.menu)

        # 透明下拉按钮
        self.transparentDropDownPushButton1 = TransparentDropDownPushButton('邮件', self)
        self.transparentDropDownPushButton2 = TransparentDropDownPushButton(FIF.MAIL, '邮件', self)
        self.transparentDropDownPushButton1.setMenu(self.menu)
        self.transparentDropDownPushButton2.setMenu(self.menu)

        # 分割按钮
        self.splitPushButton1 = SplitPushButton('分割按钮', self)
        self.splitPushButton2 = SplitPushButton(FIF.GITHUB, '分割按钮', self)
        self.splitPushButton1.setFlyout(self.menu)
        self.splitPushButton2.setFlyout(self.menu)

        # 主色分割按钮
        self.primarySplitPushButton1 = PrimarySplitPushButton('分割按钮', self)
        self.primarySplitPushButton2 = PrimarySplitPushButton(FIF.GITHUB, '分割按钮', self)
        self.primarySplitPushButton1.setFlyout(self.menu)
        self.primarySplitPushButton2.setFlyout(self.menu)

        # 超链接按钮
        self.hyperlinkButton1 = HyperlinkButton(
            url='https://qfluentwidgets.com',
            text='超链接按钮',
            parent=self
        )
        self.hyperlinkButton2 = HyperlinkButton(
            url='https://qfluentwidgets.com',
            text='超链接按钮',
            parent=self,
            icon=FIF.LINK
        )

        # 胶囊按钮
        self.pillPushButton1 = PillPushButton('胶囊按钮', self)
        self.pillPushButton2 = PillPushButton(FIF.CALENDAR, '胶囊按钮', self)

        # 布局
        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.pushButton1, 0, 0)
        self.gridLayout.addWidget(self.pushButton2, 0, 1)
        self.gridLayout.addWidget(self.primaryButton1, 1, 0)
        self.gridLayout.addWidget(self.primaryButton2, 1, 1)
        self.gridLayout.addWidget(self.transparentPushButton1, 2, 0)
        self.gridLayout.addWidget(self.transparentPushButton2, 2, 1)

        self.gridLayout.addWidget(self.toggleButton1, 3, 0)
        self.gridLayout.addWidget(self.toggleButton2, 3, 1)
        self.gridLayout.addWidget(self.transparentTogglePushButton1, 4, 0)
        self.gridLayout.addWidget(self.transparentTogglePushButton2, 4, 1)

        self.gridLayout.addWidget(self.splitPushButton1, 5, 0)
        self.gridLayout.addWidget(self.splitPushButton2, 5, 1)
        self.gridLayout.addWidget(self.primarySplitPushButton1, 6, 0)
        self.gridLayout.addWidget(self.primarySplitPushButton2, 6, 1)

        self.gridLayout.addWidget(self.dropDownPushButton1, 7, 0, Qt.AlignLeft)
        self.gridLayout.addWidget(self.dropDownPushButton2, 7, 1, Qt.AlignLeft)
        self.gridLayout.addWidget(self.primaryDropDownPushButton1, 8, 0, Qt.AlignLeft)
        self.gridLayout.addWidget(self.primaryDropDownPushButton2, 8, 1, Qt.AlignLeft)
        self.gridLayout.addWidget(self.transparentDropDownPushButton1, 9, 0, Qt.AlignLeft)
        self.gridLayout.addWidget(self.transparentDropDownPushButton2, 9, 1, Qt.AlignLeft)

        self.gridLayout.addWidget(self.pillPushButton1, 10, 0, Qt.AlignLeft)
        self.gridLayout.addWidget(self.pillPushButton2, 10, 1, Qt.AlignLeft)

        self.gridLayout.addWidget(self.hyperlinkButton1, 11, 0, Qt.AlignLeft)
        self.gridLayout.addWidget(self.hyperlinkButton2, 11, 1, Qt.AlignLeft)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w1 = ToolButtonDemo()
    w1.show()

    w2 = PushButtonDemo()
    w2.show()
    app.exec()
