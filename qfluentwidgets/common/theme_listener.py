# coding:utf-8
from PySide6.QtCore import QThread, Signal

from .config import Theme, qconfig
import sys


class SystemThemeListener(QThread):
    """ System theme listener """

    systemThemeChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._darkdetect = None

    def _darkdetectModule(self):
        if self._darkdetect is None:
            try:
                import darkdetect
            except Exception:
                self._darkdetect = False
            else:
                self._darkdetect = darkdetect

        return self._darkdetect

    def run(self):
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
        theme = Theme.DARK if theme.lower() == "dark" else Theme.LIGHT

        if qconfig.themeMode.value != Theme.AUTO or theme == qconfig.theme:
            return

        qconfig.theme = Theme.AUTO
        qconfig._cfg.themeChanged.emit(Theme.AUTO)
        self.systemThemeChanged.emit()
