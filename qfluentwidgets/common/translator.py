# coding: utf-8
from PySide6.QtCore import QTranslator, QLocale


class FluentTranslator(QTranslator):
    """Fluent Widgets 翻译器，用于加载和安装对应语言的翻译文件
    
     适用于需要为 Fluent Widgets 界面提供多语言支持的场景
     实例化后需通过 QApplication.installTranslator() 安装方可生效
     切换语言时通常需要先移除旧翻译器再重新安装新的实例
    """

    def __init__(self, locale: QLocale = None, parent=None):
        """初始化翻译器并加载指定 locale 的翻译资源
        
         Args:
          locale (str): 语言地区代码，例如 ``zh_CN``、``en_US`` 或 ``zh_HK`` 等
           用于匹配和加载对应的内置 qm 翻译文件
          parent (QObject): 父对象，控制该翻译器的生命周期，通常传入 QApplication 实例或保持为 None
        """
        super().__init__(parent=parent)
        self.load(locale or QLocale())

    def load(self, locale: QLocale):
        """加载翻译文件

        Args:
            locale: 区域设置
        """
        super().load(f":/qfluentwidgets/i18n/qfluentwidgets.{locale.name()}.qm")