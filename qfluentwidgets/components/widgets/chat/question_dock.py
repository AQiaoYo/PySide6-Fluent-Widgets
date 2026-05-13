# coding: utf-8
"""问答 Dock (QuestionDock)

当 Agent 需要用户做出选择 (单选/多选) 时, 在输入框上方弹出一张
结构化问答面板. 用户勾选选项后点提交.

视觉参考 opencode 的 ``SessionQuestionDock``:
- header: 问题文本
- content: 选项列表 (radio / checkbox)
- footer: [提交] 按钮

使用方式:
    dock = QuestionDock(parent)
    dock.setQuestion(
        question="选择要使用的测试框架:",
        options=["pytest", "unittest", "nose2"],
        multi=False,
    )
    dock.submitted.connect(lambda answers: print(answers))
    dock.show()
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QHBoxLayout, QRadioButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ....common.icon import FluentIcon
from ..button import PrimaryPushButton
from ..label import BodyLabel, StrongBodyLabel
from .dock_surface import DockSurface


__all__ = ['QuestionDock']


class QuestionDock(DockSurface):
    """问答 Dock.

    Signals:
        submitted(list): 用户点击提交后发出, 参数为选中的选项文本列表

    构造函数:
        QuestionDock(parent: QWidget = None)
    """

    submitted = Signal(list)

    def __init__(self, parent: Optional[QWidget] = None):
        self._question = ""
        self._options: List[str] = []
        self._multi = False
        self._optionWidgets: List[QWidget] = []
        super().__init__(parent, collapsible=False)
        self.setObjectName("questionDock")
        self.hide()

    # ------------------------------------------------------------------
    # 子类覆盖
    # ------------------------------------------------------------------

    def _headerHeight(self) -> int:
        return 40

    def _buildHeader(self, layout: QHBoxLayout) -> None:
        self._questionLabel = StrongBodyLabel("", self._header)
        self._questionLabel.setObjectName("questionTitle")
        self._questionLabel.setWordWrap(True)
        self._questionLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self._questionLabel, 1, Qt.AlignmentFlag.AlignVCenter)

    def _buildContent(self, layout: QVBoxLayout) -> None:
        # 选项容器
        self._optionsContainer = QWidget(self._content)
        self._optionsLayout = QVBoxLayout(self._optionsContainer)
        self._optionsLayout.setContentsMargins(0, 0, 0, 0)
        self._optionsLayout.setSpacing(4)
        layout.addWidget(self._optionsContainer)

        # 按钮行
        btnRow = QWidget(self._content)
        btnLayout = QHBoxLayout(btnRow)
        btnLayout.setContentsMargins(0, 8, 0, 0)
        btnLayout.setSpacing(8)

        self._submitBtn = PrimaryPushButton(
            FluentIcon.ACCEPT, self.tr("提交"), btnRow,
        )
        self._submitBtn.setFixedHeight(28)
        self._submitBtn.clicked.connect(self._onSubmit)

        btnLayout.addStretch(1)
        btnLayout.addWidget(self._submitBtn)

        layout.addWidget(btnRow)

        # 单选按钮组
        self._radioGroup = QButtonGroup(self)
        self._radioGroup.setExclusive(True)

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def setQuestion(self, question: str, options: List[str],
                    multi: bool = False) -> None:
        """设置问题和选项.

        Args:
            question: 问题文本
            options:  选项列表
            multi:    是否多选 (默认单选)
        """
        self._question = question
        self._options = list(options)
        self._multi = multi

        self._questionLabel.setText(question)
        self._rebuildOptions()
        self._submitBtn.setEnabled(True)
        self.show()

    def question(self) -> str:
        return self._question

    def options(self) -> List[str]:
        return list(self._options)

    def isMulti(self) -> bool:
        return self._multi

    def selectedOptions(self) -> List[str]:
        """返回当前选中的选项文本列表."""
        result = []
        for w in self._optionWidgets:
            if isinstance(w, (QRadioButton, QCheckBox)) and w.isChecked():
                result.append(w.text())
        return result

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _rebuildOptions(self) -> None:
        # 清空旧选项
        for w in self._optionWidgets:
            self._optionsLayout.removeWidget(w)
            if isinstance(w, QRadioButton):
                self._radioGroup.removeButton(w)
            w.setParent(None)
            w.deleteLater()
        self._optionWidgets.clear()

        # 创建新选项
        for text in self._options:
            if self._multi:
                w = QCheckBox(text, self._optionsContainer)
            else:
                w = QRadioButton(text, self._optionsContainer)
                self._radioGroup.addButton(w)
            w.setObjectName("questionOption")
            self._optionsLayout.addWidget(w)
            self._optionWidgets.append(w)

        # 默认选中第一个 (单选模式)
        if not self._multi and self._optionWidgets:
            self._optionWidgets[0].setChecked(True)

    def _onSubmit(self) -> None:
        selected = self.selectedOptions()
        self._submitBtn.setEnabled(False)
        self.submitted.emit(selected)
        self.hide()
