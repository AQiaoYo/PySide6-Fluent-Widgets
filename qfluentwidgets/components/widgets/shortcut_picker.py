# coding: utf-8
"""快捷键选择器组件

提供可视化快捷键设置功能，支持键盘监听和防抖处理
适用于需要用户自定义快捷键的场景，如设置面板、热键配置等
"""

from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import (
    QKeyEvent,
    QKeySequence,
    QIcon,
    QPainter,
    QColor,
    QFontMetrics,
    QFont,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)

from ...common.icon import FluentIcon
from ...common.style_sheet import FluentStyleSheet, isDarkTheme
from ...common.font import setFont, getFont
from ...common.overload import singledispatchmethod
from .button import PrimaryPushButton, PushButton
from .card_widget import SimpleCardWidget
from ..dialog_box.mask_dialog_base import MaskDialogBase


class ShortcutKeyButton(QPushButton):
    """快捷键按键按钮

    用于显示单个按键的样式化按钮
    """

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setFixedHeight(36)
        self.setMinimumWidth(48)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        setFont(self, 13, QFont.Weight.DemiBold)
        # 宽度随内容自适应，不拉伸填满布局
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # 鼠标事件穿透到父级，让 ShortcutPicker 的点击事件正常触发
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        textWidth = fm.boundingRect(self.text()).width()
        width = max(48, textWidth + 24)
        return QSize(width, 36)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        # 绘制背景 - 使用主题色
        isDark = isDarkTheme()
        theme = (
            QColor(0, 178, 178) if isDark else QColor(0, 178, 178)
        )  # Cyan-Teal color from screenshot

        rect = self.rect().adjusted(2, 2, -2, -2)
        borderRadius = 5

        # 绘制按钮背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(theme)
        painter.drawRoundedRect(rect, borderRadius, borderRadius)

        # 绘制文字
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class ShortcutPickerDialog(MaskDialogBase):
    """快捷键选择对话框

    模态对话框，用于监听并设置新的快捷键组合
    支持防抖处理和按键过滤

    Signals:
        shortcutSaved(QKeySequence): 当用户保存快捷键时触发
    """

    shortcutSaved = Signal(QKeySequence)

    def __init__(self, parent=None, currentShortcut: QKeySequence = None):
        super().__init__(parent=parent)
        self._currentShortcut = currentShortcut or QKeySequence()
        self._tempShortcut = QKeySequence()
        self._keyBuffer = []  # 缓冲按键
        self._debounceTimer = QTimer(self)
        self._debounceTimer.setSingleShot(True)
        self._debounceTimer.timeout.connect(self._onDebounceTimeout)
        self._isListening = False

        self._setupUi()
        self._setStyle()

        # 设置对话框属性
        self.setMaskColor(QColor(0, 0, 0, 76))
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setClosableOnMaskClicked(True)
        self.widget.setMinimumSize(300, 250)

    def _setupUi(self):
        """初始化界面"""
        # 主布局
        self.vBoxLayout = QVBoxLayout(self.widget)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)

        # 标题
        self.titleLabel = QLabel(self.tr("激活快捷键"), self.widget)
        setFont(self.titleLabel, 16, QFont.Weight.DemiBold)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(4)

        # 说明文字
        self.hintLabel = QLabel(self.tr("按下组合键以更改此快捷键"), self.widget)
        setFont(self.hintLabel, 12)
        self.hintLabel.setTextColor = lambda c1, c2: self.hintLabel.setStyleSheet(
            f"color: {c1.name() if not isDarkTheme() else c2.name()};"
        )
        self.hintLabel.setTextColor(QColor(96, 96, 96), QColor(160, 160, 160))
        self.vBoxLayout.addWidget(self.hintLabel)

        # 快捷键显示区域
        self.keysLayout = QHBoxLayout()
        self.keysLayout.setSpacing(8)
        self.keysLayout.setAlignment(Qt.AlignCenter)

        # 初始化三个按键按钮（隐藏状态，等待输入）
        self.keyButtons = []
        for i in range(3):
            btn = ShortcutKeyButton("", self.widget)
            btn.hide()
            self.keyButtons.append(btn)
            self.keysLayout.addWidget(btn)

        self.vBoxLayout.addLayout(self.keysLayout, 1)

        # 按钮区域
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setAlignment(Qt.AlignCenter)

        self.saveButton = PrimaryPushButton(self.tr("保存"), self.widget)
        self.resetButton = PushButton(self.tr("重置"), self.widget)
        self.cancelButton = PushButton(self.tr("取消"), self.widget)

        self.saveButton.setFixedWidth(100)
        self.resetButton.setFixedWidth(100)
        self.cancelButton.setFixedWidth(100)

        self.buttonLayout.addWidget(self.saveButton)
        self.buttonLayout.addWidget(self.resetButton)
        self.buttonLayout.addWidget(self.cancelButton)

        self.vBoxLayout.addLayout(self.buttonLayout)

        # 信号连接
        self.saveButton.clicked.connect(self._onSave)
        self.resetButton.clicked.connect(self._onReset)
        self.cancelButton.clicked.connect(self.reject)

        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
        self.widget.setFocusPolicy(Qt.NoFocus)

        # 显示当前快捷键
        self._updateKeyButtons(self._currentShortcut)

    def _setStyle(self):
        """设置样式"""
        self.widget.setObjectName("centerWidget")
        self.titleLabel.setObjectName("titleLabel")
        self.hintLabel.setObjectName("contentLabel")
        FluentStyleSheet.DIALOG.apply(self)
        FluentStyleSheet.DIALOG.apply(self.widget)

        # 设置固定大小
        self.widget.setFixedSize(420, 280)
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignCenter)

    def showEvent(self, e):
        """显示事件"""
        super().showEvent(e)
        self._isListening = True
        self.setFocus()  # 获取焦点以接收键盘事件
        self.grabKeyboard()  # 捕获所有键盘输入

    def hideEvent(self, e):
        """隐藏事件"""
        self.releaseKeyboard()
        self._isListening = False
        super().hideEvent(e)

    def done(self, code):
        """关闭对话框"""
        self.releaseKeyboard()
        super().done(code)

    def keyPressEvent(self, e: QKeyEvent):
        """键盘按下事件 - 防抖处理"""
        if not self._isListening:
            return

        # 过滤无效按键
        key = e.key()
        if key in (Qt.Key_Escape,):
            self.reject()
            return
        if key in (Qt.Key_Enter, Qt.Key_Return):
            if self._tempShortcut:
                self._onSave()
            return

        # 获取修饰键状态
        modifiers = e.modifiers()

        # 过滤单独的修饰键（Ctrl, Shift, Alt, Meta）
        # 只有当有其他按键时才记录
        isModifierOnly = key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta)

        # 构建组合键
        if not isModifierOnly:
            # 重置防抖定时器
            self._debounceTimer.stop()

            # 构建快捷键字符串
            # 使用 QKeySequence 的字符串构造方式
            parts = []
            if modifiers & Qt.ControlModifier:
                parts.append("Ctrl")
            if modifiers & Qt.AltModifier:
                parts.append("Alt")
            if modifiers & Qt.ShiftModifier:
                parts.append("Shift")
            if modifiers & Qt.MetaModifier:
                parts.append("Meta")

            # 添加主键
            keyName = QKeySequence(key).toString()
            if keyName:
                parts.append(keyName)

            # 创建快捷键
            shortcutStr = "+".join(parts)
            self._tempShortcut = QKeySequence(shortcutStr)

            # 更新显示
            self._updateKeyButtons(self._tempShortcut)

            # 启动防抖定时器 (150ms)
            self._debounceTimer.start(150)
        else:
            # 只是修饰键按下，显示待命中状态
            self._showPendingState(modifiers)

    def keyReleaseEvent(self, e: QKeyEvent):
        """键盘释放事件"""
        if not self._isListening:
            return

        # 防抖处理：按键释放后短暂延迟再确认
        if self._debounceTimer.isActive():
            self._debounceTimer.stop()
            self._debounceTimer.start(100)

    def _onDebounceTimeout(self):
        """防抖超时处理 - 确认快捷键"""
        # 防抖结束，快捷键已确认
        pass

    def _showPendingState(self, modifiers: Qt.KeyboardModifiers):
        """显示待命中状态（只有修饰键按下）"""
        # 暂时清空显示或显示提示
        pass

    def _updateKeyButtons(self, shortcut: QKeySequence):
        """更新按键按钮显示"""
        text = shortcut.toString(QKeySequence.NativeText)

        if not text:
            # 无快捷键时显示 "None" 占位
            self.keyButtons[0].setText(self.tr("None"))
            self.keyButtons[0].show()
            for btn in self.keyButtons[1:]:
                btn.hide()
            return

        # 分割组合键，处理平台差异
        # Windows: Ctrl+Shift+A, macOS: ⌃⇧A
        if "+" in text:
            keys = text.split("+")
        else:
            keys = [text]

        # 过滤空字符串
        keys = [k.strip() for k in keys if k.strip()]

        # 更新按钮显示
        for i, btn in enumerate(self.keyButtons):
            if i < len(keys) and keys[i]:
                btn.setText(keys[i])
                btn.show()
                # 根据文字长度调整宽度
                fm = QFontMetrics(btn.font())
                width = max(48, fm.horizontalAdvance(keys[i]) + 24)
                btn.setFixedWidth(width)
            else:
                btn.hide()

    def _onSave(self):
        """保存快捷键"""
        # _tempShortcut 为空表示用户重置了，也需要保存（空快捷键）
        self._currentShortcut = self._tempShortcut
        self.shortcutSaved.emit(self._currentShortcut)
        self.accept()

    def _onReset(self):
        """重置为默认快捷键（清空快捷键，显示 None 占位）"""
        self._tempShortcut = QKeySequence()
        self._updateKeyButtons(self._tempShortcut)
        self.setFocus()

    def getShortcut(self) -> QKeySequence:
        """获取当前设置的快捷键"""
        return self._currentShortcut

    def setShortcut(self, shortcut: QKeySequence):
        """设置快捷键"""
        self._currentShortcut = shortcut
        self._updateKeyButtons(shortcut)


class ShortcutPicker(SimpleCardWidget):
    """快捷键选择器卡片

    用于显示和修改快捷键的卡片组件
    点击后弹出快捷键设置对话框

    Signals:
        shortcutChanged(QKeySequence): 当快捷键被修改时触发
    """

    shortcutChanged = Signal(QKeySequence)

    @singledispatchmethod
    def __init__(self, parent=None):
        """初始化快捷键选择器

        Args:
            parent: 父部件
        """
        super().__init__(parent=parent)
        self._shortcut = QKeySequence()
        self._defaultShortcut = QKeySequence()

        self._setupUi()
        self._updateDisplay()
        self.setClickEnabled(True)
        self.clicked.connect(self._onClicked)

    @__init__.register
    def _(self, shortcut: QKeySequence, parent=None):
        """初始化并设置默认快捷键

        Args:
            shortcut: 默认快捷键
            parent: 父部件
        """
        self.__init__(parent=parent)
        self.setShortcut(shortcut)
        self._defaultShortcut = shortcut

    @__init__.register
    def _(self, shortcut: str, parent=None):
        """初始化并设置默认快捷键（字符串格式）

        Args:
            shortcut: 快捷键字符串，如 "Ctrl+Shift+A"
            parent: 父部件
        """
        self.__init__(QKeySequence(shortcut), parent)

    def _setupUi(self):
        """初始化界面"""
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setSpacing(8)
        self.hBoxLayout.setContentsMargins(16, 12, 16, 12)
        self.hBoxLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 创建按键显示按钮（不可点击的展示用）
        self.keyButtons = []
        for i in range(3):
            btn = ShortcutKeyButton("", self)
            btn.hide()
            self.keyButtons.append(btn)
            self.hBoxLayout.addWidget(btn)

        self.hBoxLayout.addSpacing(8)

        # 编辑图标
        self.editIcon = QLabel(self)
        editIcon = QIcon(FluentIcon.EDIT.path())
        self.editIcon.setPixmap(editIcon.pixmap(16, 16))
        self.hBoxLayout.addWidget(self.editIcon)

        self.setFixedHeight(56)
        # 宽度随内容自适应，不拉伸填满父布局
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def setShortcut(self, shortcut: QKeySequence):
        """设置显示的快捷键"""
        self._shortcut = shortcut
        self._updateDisplay()

    def shortcut(self) -> QKeySequence:
        """获取当前快捷键"""
        return self._shortcut

    def sizeHint(self):
        """根据内容计算宽度"""
        # 左右 padding
        margins = self.hBoxLayout.contentsMargins()
        w = margins.left() + margins.right()
        # 可见按键按钮宽度之和
        spacing = self.hBoxLayout.spacing()
        visibleBtns = [btn for btn in self.keyButtons if btn.isVisible()]
        for btn in visibleBtns:
            w += btn.sizeHint().width() + spacing
        # 编辑图标 + 右侧间距
        w += 8 + 16  # addSpacing(8) + icon width
        return QSize(max(80, w), 56)

    def _updateDisplay(self):
        """更新显示"""
        text = self._shortcut.toString(QKeySequence.NativeText)

        if not text:
            # 无快捷键时显示 "None" 占位
            self.keyButtons[0].setText(self.tr("None"))
            self.keyButtons[0].show()
            for btn in self.keyButtons[1:]:
                btn.hide()
            self.updateGeometry()
            return

        # 分割组合键，处理平台差异
        if "+" in text:
            keys = text.split("+")
        else:
            keys = [text]

        # 过滤空字符串
        keys = [k.strip() for k in keys if k.strip()]

        for i, btn in enumerate(self.keyButtons):
            if i < len(keys) and keys[i]:
                btn.setText(keys[i])
                btn.show()
                btn.updateGeometry()
            else:
                btn.hide()

        # 通知父布局重新计算本组件宽度
        self.updateGeometry()

    def _onClicked(self):
        """点击卡片时弹出对话框"""
        dialog = ShortcutPickerDialog(self.window(), self._shortcut)
        dialog.shortcutSaved.connect(self._onShortcutSaved)
        dialog.exec()

    def _onShortcutSaved(self, shortcut: QKeySequence):
        """快捷键保存回调"""
        if shortcut != self._shortcut:
            self._shortcut = shortcut
            self._updateDisplay()
            self.shortcutChanged.emit(shortcut)

    def getDefaultShortcut(self) -> QKeySequence:
        """获取默认快捷键"""
        return self._defaultShortcut

    def resetToDefault(self):
        """重置为默认快捷键"""
        self.setShortcut(self._defaultShortcut)
        self.shortcutChanged.emit(self._defaultShortcut)
