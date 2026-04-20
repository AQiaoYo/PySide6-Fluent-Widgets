# coding: utf-8
from PySide6.QtCore import Qt, QSize, QRectF, QModelIndex, QEvent
from PySide6.QtGui import QPainter, QColor, QPalette, QPainterPath, QPainterPath
from PySide6.QtWidgets import QTreeWidget, QStyledItemDelegate, QStyle, QTreeView, QApplication, QStyleOptionViewItem, QStyleFactory

from ...common.style_sheet import FluentStyleSheet, updateDynamicStyle, isDarkTheme, setCustomStyleSheet
from ...common.font import getFont
from ...common.color import autoFallbackThemeColor
from .check_box import CheckBoxIcon
from .scroll_area import SmoothScrollDelegate


class TreeItemDelegate(QStyledItemDelegate):
    """TreeItemDelegate 树形项委托
    
    用于自定义树形控件中项的绘制样式，负责背景色、圆角、选中高亮等视觉效果的渲染
    通常与 TreeViewBase 及其子类配合使用，以确保 Fluent Design 风格的一致性
    """

    def __init__(self, parent: QTreeView):
        """初始化树形项委托
        
        Args:
            parent: 父对象，默认为 None，指定父对象后委托将跟随父部件自动释放
        """
        super().__init__(parent)
        self.lightCheckedColor = QColor()
        self.darkCheckedColor = QColor()

    def setCheckedColor(self, light, dark):
        """设置指示器选中状态的颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的颜色
        """
        self.lightCheckedColor = QColor(light)
        self.darkCheckedColor = QColor(dark)
        self.parent().viewport().update()

    def paint(self, painter, option, index):
        painter.setRenderHints(
            QPainter.Antialiasing | QPainter.TextAntialiasing)
        super().paint(painter, option, index)

        if index.data(Qt.CheckStateRole) is not None:
            self._drawCheckBox(painter, option, index)

        if not (option.state & (QStyle.State_Selected | QStyle.State_MouseOver)):
            return

        painter.save()
        painter.setPen(Qt.NoPen)

        # 绘制背景
        self._drawBackground(painter, option, index)

        # 绘制指示器
        self._drawIndicator(painter, option, index)

        painter.restore()

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        c = 255 if isDarkTheme() else 0
        painter.setBrush(QColor(c, c, c, 9))

        column = index.column()
        lastColumn = self.parent().header().count() - 1

        radius = 4.0
        path = QPainterPath()

        rect = QRectF(option.rect)
        rect.setTop(option.rect.y() + 2)
        rect.setHeight(option.rect.height() - 4)

        if column == 0:
            rect.setX(4)

        if column == 0 and column == lastColumn:
            path.addRoundedRect(rect, radius, radius)
        elif column == 0:
            path.moveTo(rect.right(), rect.top())
            path.lineTo(rect.right(), rect.bottom())
            path.lineTo(rect.x() + radius, rect.bottom())
            path.arcTo(rect.x(), rect.bottom() - 2 * radius, 2 * radius, 2 * radius, 270, -90)
            path.lineTo(rect.x(), rect.top() + radius)
            path.arcTo(rect.x(), rect.top(), 2 * radius, 2 * radius, 180, -90)
            path.closeSubpath()
        elif column == lastColumn:
            path.moveTo(rect.x(), rect.top())
            path.lineTo(rect.right() - radius, rect.top())
            path.arcTo(rect.right() - 2 * radius, rect.top(), 2 * radius, 2 * radius, 90, -90)
            path.lineTo(rect.right(), rect.bottom() - radius)
            path.arcTo(rect.right() - 2 * radius, rect.bottom() - 2 * radius, 2 * radius, 2 * radius, 0, -90)
            path.lineTo(rect.x(), rect.bottom())
            path.closeSubpath()
        else:
            path.addRect(rect)

        painter.drawPath(path)

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        h = option.rect.height() - 4

        if option.state & QStyle.State_Selected and self.parent().horizontalScrollBar().value() == 0:
            painter.setBrush(autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor))
            painter.drawRoundedRect(4, 9+option.rect.y(), 3, h - 13, 1.5, 1.5)

    def _drawCheckBox(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        checkState = Qt.CheckState(index.data(Qt.ItemDataRole.CheckStateRole))

        isDark = isDarkTheme()

        r = 4.5
        x = option.rect.x() + 23
        y = option.rect.center().y() - 9
        rect = QRectF(x, y, 19, 19)

        if checkState == Qt.CheckState.Unchecked:
            painter.setBrush(QColor(0, 0, 0, 26)
                             if isDark else QColor(0, 0, 0, 6))
            painter.setPen(QColor(255, 255, 255, 142)
                           if isDark else QColor(0, 0, 0, 122))
            painter.drawRoundedRect(rect, r, r)
        else:
            color = autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor)
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, r, r)

            if checkState == Qt.CheckState.Checked:
                CheckBoxIcon.ACCEPT.render(painter, rect)
            else:
                CheckBoxIcon.PARTIAL_ACCEPT.render(painter, rect)

        painter.restore()


    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)

        # font
        option.font = index.data(Qt.FontRole) or getFont(13)

        # 文本颜色
        textColor = Qt.white if isDarkTheme() else Qt.black
        textBrush = index.data(Qt.ForegroundRole)
        if textBrush is not None:
            textColor = textBrush.color()

        option.palette.setColor(QPalette.Text, textColor)
        option.palette.setColor(QPalette.HighlightedText, textColor)


class TreeViewBase:
    """TreeViewBase 树视图基类
    
    提供树形控件的基础功能与通用样式设置，支持平滑滚动、自定义选中效果等
    作为 TreeWidget 与 TreeView 的公共基类，用于统一树形控件的行为与视觉表现
    """

    def _initView(self):
        self.scrollDelagate = SmoothScrollDelegate(self)

        self.header().setHighlightSections(False)
        self.header().setDefaultAlignment(Qt.AlignCenter)

        self.setItemDelegate(TreeItemDelegate(self))
        self.setIconSize(QSize(16, 16))
        self.setMouseTracking(True)

        FluentStyleSheet.TREE_VIEW.apply(self)
        updateDynamicStyle(self)

    def setCheckedColor(self, light, dark):
        """设置选中状态的颜色
        
        Args:
            light (str | QColor | Qt.GlobalColor): 亮色主题下的颜色
            dark (str | QColor | Qt.GlobalColor): 暗色主题下的颜色
        """
        self.itemDelegate().setCheckedColor(light, dark)

    def drawBranches(self, painter, rect, index):
        rect.moveLeft(15)
        return QTreeView.drawBranches(self, painter, rect, index)

    def setBorderVisible(self, isVisible: bool):
        """设置边框的可见性
        
        Args:
            isVisible: 边框是否可见
        """
        self.setProperty("isBorderVisible", isVisible)
        updateDynamicStyle(self)

    def setBorderRadius(self, radius: int):
        """设置边框的半径
        
        Args:
            radius: 边框圆角半径
        """
        qss = f"QTreeView{{border-radius: {radius}px}}"
        setCustomStyleSheet(self, qss, qss)


class TreeWidget(TreeViewBase, QTreeWidget):
    """TreeWidget 树形部件
    
    基于 QTreeWidget 的便捷树形控件，支持直接添加、删除和管理树形项
    适用于数据量较小、无需复杂 Model/View 分离的简单层级数据展示场景
    """

    def __init__(self, parent=None):
        """初始化树形部件
        
        Args:
            parent: 父级窗口部件，默认为 None，传入父对象可将该控件嵌入到对应布局中
        """
        super().__init__(parent=parent)
        self._initView()

    def viewportEvent(self, event):
        """捕获点击事件以重写项的展开/折叠功能
        
        Args:
            event: 视图事件
        """
        if event.type() != QEvent.Type.MouseButtonPress:
            return super().viewportEvent(event)

        index = self.indexAt(event.pos())
        item = self.itemFromIndex(index)

        if item is None:
            return super().viewportEvent(event)

        level = 0
        while item.parent() is not None:
            item = item.parent()
            level += 1

        indent = level * self.indentation() + 20
        if event.pos().x() > indent and event.pos().x() < indent + 10:
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)

        return super().viewportEvent(event)


class TreeView(TreeViewBase, QTreeView):
    """TreeView 树视图
    
    基于 QTreeView 的 Model/View 架构树形控件，适合与自定义数据模型配合使用
    适用于数据量较大或需要与底层数据动态同步的复杂层级结构展示场景
    """

    def __init__(self, parent=None):
        """初始化树视图
        
        Args:
            parent: 父级窗口部件，默认为 None，传入父对象可将该控件嵌入到对应布局中
        """
        super().__init__(parent=parent)
        self._initView()

    def viewportEvent(self, event):
        """捕获点击事件以重写项的展开/折叠功能
        
        Args:
            event: 视图事件
        """
        if event.type() != QEvent.Type.MouseButtonPress:
            return super().viewportEvent(event)

        index = self.indexAt(event.pos())
        if not index.isValid():
            return super().viewportEvent(event)

        level = 0
        currentIndex = index
        while currentIndex.parent().isValid():
            currentIndex = currentIndex.parent()
            level += 1

        indent = level * self.indentation() + 20
        if event.pos().x() > indent and event.pos().x() < indent + 10:
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)

        return super().viewportEvent(event)
