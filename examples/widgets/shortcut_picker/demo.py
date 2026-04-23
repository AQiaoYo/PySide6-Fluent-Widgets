# coding: utf-8
"""ShortcutPicker 组件示例"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QFont
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel

# 添加库路径
sys.path.insert(0, r'D:\PySide6-Fluent-Widgets')

from qfluentwidgets import (FluentWindow, setTheme, Theme, FluentIcon,
                             ShortcutPicker, HeaderCardWidget, 
                             BodyLabel, setFont)


class DemoInterface(QWidget):
    """演示界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("DemoInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        
        # 标题
        self.titleLabel = QLabel(self.tr("快捷键选择器"), self)
        setFont(self.titleLabel, 24, QFont.Weight.DemiBold)
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # 示例1: 带默认快捷键
        self.card1 = HeaderCardWidget(self.tr("默认快捷键 (Ctrl+Shift+A)"), self)
        self.shortcutPicker1 = ShortcutPicker("Ctrl+Shift+A", self.card1)
        self.shortcutPicker1.shortcutChanged.connect(
            lambda s: print(f"快捷键1已更改: {s.toString()}")
        )
        self.card1.viewLayout.addWidget(self.shortcutPicker1)
        self.vBoxLayout.addWidget(self.card1)
        
        # 示例2: 无默认值
        self.card2 = HeaderCardWidget(self.tr("未设置快捷键"), self)
        self.shortcutPicker2 = ShortcutPicker(self.card2)
        self.shortcutPicker2.shortcutChanged.connect(
            lambda s: print(f"快捷键2已更改: {s.toString()}")
        )
        self.card2.viewLayout.addWidget(self.shortcutPicker2)
        self.vBoxLayout.addWidget(self.card2)
        
        # 示例3: 简单快捷键
        self.card3 = HeaderCardWidget(self.tr("简单快捷键 (Ctrl+C)"), self)
        self.shortcutPicker3 = ShortcutPicker("Ctrl+C", self.card3)
        self.shortcutPicker3.shortcutChanged.connect(
            lambda s: print(f"快捷键3已更改: {s.toString()}")
        )
        self.card3.viewLayout.addWidget(self.shortcutPicker3)
        self.vBoxLayout.addWidget(self.card3)
        
        # 说明文字
        self.hintLabel = BodyLabel(self.tr("点击卡片可以修改快捷键"), self)
        self.vBoxLayout.addWidget(self.hintLabel)
        
        self.vBoxLayout.addStretch(1)


class MainWindow(FluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("快捷键选择器示例"))
        self.resize(800, 600)
        
        # 添加演示界面
        self.demoInterface = DemoInterface(self)
        self.addSubInterface(self.demoInterface, FluentIcon.COMMAND_PROMPT, "Shortcut Picker")
        
        # 设置主题
        setTheme(Theme.AUTO)


def main():
    app = QApplication(sys.argv)
    
    # 启用高DPI支持
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
