# coding: utf-8
"""系统主题监听模块

提供检测操作系统深色/浅色模式的能力，并在系统主题切换时通知应用自动更新界面风格
适用于需要跟随系统主题自动换肤的场景，通常与 Theme 和 setTheme 配合使用
"""

from PySide6.QtCore import QThread, Signal

from .config import Theme, qconfig
import sys


class SystemThemeListener(QThread):
    """系统主题监听器

    监听操作系统主题变化，当检测到主题改变时发出 systemThemeChanged 信号
    """

    systemThemeChanged = Signal()

    def __init__(self, parent=None):
        """初始化监听器

        Args:
            parent: 父对象，默认为 None
        """
        super().__init__(parent=parent)
        self._darkdetect = None

    def _darkdetectModule(self):
        """导入并获取 darkdetect 模块

        Returns:
            成功时返回 darkdetect 模块，失败则返回 False
        """
        if self._darkdetect is None:
            try:
                import darkdetect
            except Exception:
                self._darkdetect = False
            else:
                self._darkdetect = darkdetect

        return self._darkdetect

    def run(self):
        """运行主题监听线程

        在 Windows 上使用 darkdetect 的监听器，其他平台通过轮询检测主题变化
        """
        darkdetect = self._darkdetectModule()
        if not darkdetect:
            return

        if sys.platform == "win32":
            darkdetect.listener(self._onThemeChanged)
            return

        while not self.isInterruptionRequested():
            t = darkdetect.theme().lower()
            theme = Theme.DARK if t == "dark" else Theme.LIGHT
            if theme != qconfig.theme:
                self._onThemeChanged(t)
                self.msleep(2000)   # anti shake
            else:
                self.msleep(1000)

    def _onThemeChanged(self, theme: str):
        """处理系统主题变化

        Args:
            theme: 系统主题字符串
        """
        theme = Theme.DARK if theme.lower() == "dark" else Theme.LIGHT

        if qconfig.themeMode.value != Theme.AUTO or theme == qconfig.theme:
            return

        qconfig.theme = Theme.AUTO
        qconfig._cfg.themeChanged.emit(Theme.AUTO)
        self.systemThemeChanged.emit()