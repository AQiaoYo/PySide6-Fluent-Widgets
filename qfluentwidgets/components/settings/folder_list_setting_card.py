# coding: utf-8
"""文件夹列表设置卡片"""

from typing import List
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QIcon
from PySide6.QtWidgets import (QPushButton, QFileDialog, QWidget, QLabel,
                               QHBoxLayout, QToolButton, QSizePolicy)

from ...components.widgets.button import ToolButton, PushButton
from ...common.config import ConfigItem, qconfig
from ...common.icon import drawIcon
from ...common.icon import FluentIcon as FIF
from ..dialog_box.dialog import Dialog
from .expand_setting_card import ExpandSettingCard



class FolderItem(QWidget):
    """文件夹项"""

    removed = Signal(QWidget)

    def __init__(self, folder: str, parent=None):
        super().__init__(parent=parent)
        self.folder = folder
        self.hBoxLayout = QHBoxLayout(self)
        self.folderLabel = QLabel(folder, self)
        self.removeButton = ToolButton(FIF.CLOSE, self)

        self.removeButton.setFixedSize(39, 29)
        self.removeButton.setIconSize(QSize(12, 12))

        self.setFixedHeight(53)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.hBoxLayout.setContentsMargins(48, 0, 60, 0)
        self.hBoxLayout.addWidget(self.folderLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.removeButton, 0, Qt.AlignRight)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        # 设置对象名称, 以应用主题感知颜色样式.
        self.folderLabel.setObjectName('titleLabel')

        self.removeButton.clicked.connect(
            lambda: self.removed.emit(self))


class FolderListSettingCard(ExpandSettingCard):
    """文件夹列表设置卡片

    构造函数重载:
        - __init__(configItem, title, content, directory, parent)
        - __init__(configItem, title, content, directory)
        - __init__(configItem, title, content)
        - __init__(configItem, title)
    """

    folderChanged = Signal(list)

    def __init__(self, configItem: ConfigItem, title: str, content: str = None, directory="./", parent=None):
        """
        初始化文件夹列表设置卡片

        Args:
            configItem (ConfigItem): 由卡片操作的配置项
            title (str): 卡片标题
            content (str): 卡片内容
            directory (str): 文件对话框的工作目录
            parent (QWidget): 父部件
        """
        super().__init__(FIF.FOLDER, title, content, parent)
        self.configItem = configItem
        self._dialogDirectory = directory
        self.addFolderButton = PushButton(self.tr('Add folder'), self, FIF.FOLDER_ADD)

        self.folders = qconfig.get(configItem).copy()   # type:List[str]
        self.__initWidget()

    def __initWidget(self):
        self.addWidget(self.addFolderButton)

        # 初始化布局
        self.viewLayout.setSpacing(0)
        self.viewLayout.setAlignment(Qt.AlignTop)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        for folder in self.folders:
            self.__addFolderItem(folder)

        self.addFolderButton.clicked.connect(self.__showFolderDialog)

    def __showFolderDialog(self):
        """显示文件夹对话框"""
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), self._dialogDirectory)

        if not folder or folder in self.folders:
            return

        self.__addFolderItem(folder)
        self.folders.append(folder)
        qconfig.set(self.configItem, self.folders)
        self.folderChanged.emit(self.folders)

    def __addFolderItem(self, folder: str):
        """添加文件夹项"""
        item = FolderItem(folder, self.view)
        item.removed.connect(self.__showConfirmDialog)
        self.viewLayout.addWidget(item)
        item.show()
        self._adjustViewSize()

    def __showConfirmDialog(self, item: FolderItem):
        """显示确认对话框"""
        name = Path(item.folder).name
        title = self.tr('Are you sure you want to delete the folder?')
        content = self.tr("If you delete the ") + f'"{name}"' + \
            self.tr(" folder and remove it from the list, the folder will no "
                    "longer appear in the list, but will not be deleted.")
        w = Dialog(title, content, self.window())
        w.yesSignal.connect(lambda: self.__removeFolder(item))
        w.exec_()

    def __removeFolder(self, item: FolderItem):
        """移除文件夹"""
        if item.folder not in self.folders:
            return

        self.folders.remove(item.folder)
        self.viewLayout.removeWidget(item)
        item.deleteLater()
        self._adjustViewSize()

        self.folderChanged.emit(self.folders)
        qconfig.set(self.configItem, self.folders)