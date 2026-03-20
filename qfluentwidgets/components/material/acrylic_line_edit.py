# coding: utf-8
from .acrylic_menu import AcrylicCompleterMenu, AcrylicLineEditMenu
from ..widgets.line_edit import LineEdit, SearchLineEdit


class AcrylicLineEditBase:
    """ 亚克力 行编辑器 base """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def setCompleter(self, completer):
        super().setCompleter(completer)
        self.setCompleterMenu(AcrylicCompleterMenu(self))

    def contextMenuEvent(self, e):
        menu = AcrylicLineEditMenu(self)
        menu.exec(e.globalPos())



class AcrylicLineEdit(AcrylicLineEditBase, LineEdit):
    """ 亚克力 行编辑器 """


class AcrylicSearchLineEdit(AcrylicLineEditBase, SearchLineEdit):
    """ 亚克力 search 行编辑器 """