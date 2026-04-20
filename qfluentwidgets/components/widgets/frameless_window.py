"""无边框窗口组件

提供跨平台的无边框窗口基类与相关实现，用于构建具有自定义标题栏的现代化桌面应用
支持 Windows 与 macOS 平台，在保留原生窗口阴影、动画与系统菜单的同时移除默认标题栏
"""

import sys

if sys.platform != "win32" or sys.getwindowsversion().build < 22000:
    from qframelesswindow import FramelessWindow
else:
    from ctypes.wintypes import MSG

    import win32con
    from PySide6.QtCore import QPoint, QEvent, Qt
    from PySide6.QtGui import QCursor, QMouseEvent
    from PySide6.QtWidgets import QApplication

    from qframelesswindow import AcrylicWindow as Window
    from qframelesswindow.titlebar.title_bar_buttons import TitleBarButtonState


    class FramelessWindow(Window):
        """无边框窗口
        
        移除系统原生标题栏并保留完整窗口交互能力，适用于需要完全自定义标题栏和控制按钮的应用场景
        支持边缘拖拽调整大小、双击最大化与系统菜单触发，Windows 平台可自动继承 DWM 阴影和最大化动画
        """

        def __init__(self, parent=None):
            """初始化窗口

            Args:
                parent: 父窗口，默认为 None
            """
            super().__init__(parent)
            self.windowEffect.setMicaEffect(self.winId())

        def nativeEvent(self, eventType, message):
            """处理原生 Windows 消息

            Args:
                eventType: 事件类型
                message: Windows 消息对象

            Returns:
                消息处理结果
            """
            msg = MSG.from_address(message.__int__())
            if not msg.hWnd:
                return super().nativeEvent(eventType, message)

            if msg.message == win32con.WM_NCHITTEST and self._isResizeEnabled:
                if self._isHoverMaxBtn():
                    self.titleBar.maxBtn.setState(TitleBarButtonState.HOVER)
                    return True, win32con.HTMAXBUTTON

            elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE]:
                self.titleBar.maxBtn.setState(TitleBarButtonState.NORMAL)
            elif msg.message in [win32con.WM_NCLBUTTONDOWN, win32con.WM_NCLBUTTONDBLCLK] and self._isHoverMaxBtn():
                e = QMouseEvent(QEvent.MouseButtonPress, QPoint(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(self.titleBar.maxBtn, e)
                return True, 0
            elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP] and self._isHoverMaxBtn():
                e = QMouseEvent(QEvent.MouseButtonRelease, QPoint(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(self.titleBar.maxBtn, e)

            return super().nativeEvent(eventType, message)

        def _isHoverMaxBtn(self):
            """判断鼠标是否悬停在最大化按钮上

            Returns:
                悬停返回 True，否则返回 False
            """
            pos = QCursor.pos() - self.geometry().topLeft() - self.titleBar.pos()
            return self.titleBar.childAt(pos) is self.titleBar.maxBtn