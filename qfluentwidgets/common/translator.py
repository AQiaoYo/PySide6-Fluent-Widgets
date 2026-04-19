# coding: utf-8
from PySide6.QtCore import QTranslator, QLocale


class FluentTranslator(QTranslator):
    """Fluent 部件翻译器"""

    def __init__(self, locale: QLocale = None, parent=None):
        super().__init__(parent=parent)
        self.load(locale or QLocale())

    def load(self, locale: QLocale):
        """加载翻译文件

        Args:
            locale: 区域设置
        """
        super().load(f":/qfluentwidgets/i18n/qfluentwidgets.{locale.name()}.qm")