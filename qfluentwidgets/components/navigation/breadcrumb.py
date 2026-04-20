# coding: utf-8
"""面包屑导航组件

提供 BreadcrumbBar、BreadcrumbItem 和 ElideButton 等控件，用于构建层级路径导航界面
常在需要展示页面层级结构、文件路径或目录深度的场景中使用
"""

import math

from typing import Dict, List
from PySide6.QtCore import Qt, Signal, QRectF, Property, QPoint, QEvent
from PySide6.QtGui import QPainter, QFont, QHoverEvent, QAction
from PySide6.QtWidgets import QWidget, QApplication

from ...common.font import setFont, fontPixelSize
from ...common.icon import FluentIcon
from ...common.style_sheet import isDarkTheme
from ...components.widgets.menu import RoundMenu, MenuAnimationType


class BreadcrumbWidget(QWidget):
    """面包屑部件基类
    
    封装面包屑项的基础样式与交互行为，作为 BreadcrumbItem 和 ElideButton 的公共父类
    通常不直接实例化，而是由 BreadcrumbBar 在添加节点时自动创建和管理
    """

    clicked = Signal()

    def __init__(self, parent=None):
        """初始化面包屑部件
        
        Args:
            parent (QWidget): 父级窗口部件，传入后该对象将随父对象自动销毁并参与布局，传 None 时则作为独立顶层窗口
        """
        super().__init__(parent=parent)
        self.isHover = False
        self.isPressed = False

    def mousePressEvent(self, e):
        self.isPressed = True
        self.update()

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self.update()
        self.clicked.emit()

    def enterEvent(self, e):
        self.isHover = True
        self.update()

    def leaveEvent(self, e):
        self.isHover = False
        self.update()


class ElideButton(BreadcrumbWidget):
    """省略号按钮
    
    在面包屑路径过长或容器宽度不足时显示，用于折叠中间层级的节点以节省空间
    点击后通常会展开被省略的路径项或弹出菜单供用户选择
    """

    def __init__(self, parent=None):
        """初始化省略号按钮
        
        Args:
            parent (QWidget): 父级窗口部件，传入后该对象将随父对象自动销毁并参与布局，传 None 时则作为独立顶层窗口
        """
        super().__init__(parent)
        self.setFixedSize(16, 16)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.5)
        elif not self.isHover:
            painter.setOpacity(0.61)

        FluentIcon.MORE.render(painter, self.rect())

    def clearState(self):
        self.setAttribute(Qt.WA_UnderMouse, False)
        self.isHover = False
        e = QHoverEvent(QEvent.HoverLeave, QPoint(-1, -1), QPoint())
        QApplication.sendEvent(self, e)


class BreadcrumbItem(BreadcrumbWidget):
    """面包屑导航项
    
    表示层级路径中的一个节点，负责显示文本并响应点击事件以触发路由切换
    一般通过 BreadcrumbBar.addItem 添加到导航栏中，由导航栏统一控制其布局与激活状态
    """

    def __init__(self, routeKey: str, text: str, index: int, parent=None):
        """初始化面包屑项
        
        Args:
            routeKey (str): 路由键，用于唯一标识该节点并在点击时定位到对应页面或层级
            text (str): 节点显示的文本内容
            index (int): 节点在面包屑路径中的索引位置，决定其排列顺序
            parent (QWidget): 父级窗口部件，通常为所属的 BreadcrumbBar，传入后由导航栏统一管理布局与生命周期，传 None 时则作为独立顶层窗口
        """
        super().__init__(parent=parent)
        self.text = text
        self.routeKey = routeKey
        self.isHover = False
        self.isPressed = False
        self.isSelected = False
        self.index = index
        self.spacing = 5

    def setText(self, text: str):
        self.text = text

        rect = self.fontMetrics().boundingRect(text)
        w = rect.width() + math.ceil(fontPixelSize(self.font()) / 10)
        if not self.isRoot():
            w += self.spacing * 2

        self.setFixedWidth(w)
        self.setFixedHeight(rect.height())
        self.update()

    def isRoot(self):
        return self.index == 0

    def setSelected(self, isSelected: bool):
        self.isSelected = isSelected
        self.update()

    def setFont(self, font: QFont):
        super().setFont(font)
        self.setText(self.text)

    def setSpacing(self, spacing: int):
        self.spacing = spacing
        self.setText(self.text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.TextAntialiasing | QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # 绘制seperator
        sw = self.spacing * 2
        if not self.isRoot():
            iw = fontPixelSize(self.font()) / 14 * 8
            rect = QRectF((sw - iw) / 2, (self.height() - iw) / 2 + 1, iw, iw)

            painter.setOpacity(0.61)
            FluentIcon.CHEVRON_RIGHT_MED.render(painter, rect)

        # 绘制文本
        if self.isPressed:
            alpha = 0.54 if isDarkTheme() else 0.45
            painter.setOpacity(1 if self.isSelected else alpha)
        elif self.isSelected or self.isHover:
            painter.setOpacity(1)
        else:
            painter.setOpacity(0.79 if isDarkTheme() else 0.61)

        painter.setFont(self.font())
        painter.setPen(Qt.white if isDarkTheme() else Qt.black)

        if self.isRoot():
            rect = self.rect()
        else:
            rect = QRectF(sw, 0, self.width() - sw, self.height())

        painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, self.text)



class BreadcrumbBar(QWidget):
    """面包屑导航栏
    
    在内容区域顶部横向展示当前页面的层级路径，支持动态添加、移除节点以及自动省略溢出部分
    适用于多级页面导航、文件路径展示或需要快速返回上级目录的场景
    """

    currentItemChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None):
        """初始化面包屑导航栏
        
        Args:
            parent (QWidget): 父级窗口部件，传入后该对象将随父对象自动销毁并参与布局，传 None 时则作为独立顶层窗口
        """
        super().__init__(parent=parent)
        self.itemMap = {}       # type: Dict[BreadcrumbItem]
        self.items = []         # type: 列表[BreadcrumbItem]
        self.hiddenItems = []   # type: 列表[BreadcrumbItem]

        self._spacing = 10
        self._currentIndex = -1

        self.elideButton = ElideButton(self)

        setFont(self, 14)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.elideButton.hide()
        self.elideButton.clicked.connect(self._showHiddenItemsMenu)

    def addItem(self, routeKey: str, text: str):
        """添加项

        Args:
            routeKey (str): 项的唯一标识
            text (str): 项的显示文本
        """
        if routeKey in self.itemMap:
            return

        item = BreadcrumbItem(routeKey, text, len(self.items), self)
        item.setFont(self.font())
        item.setSpacing(self.spacing)
        item.clicked.connect(lambda: self.setCurrentItem(routeKey))

        self.itemMap[routeKey] = item
        self.items.append(item)
        self.setFixedHeight(max(i.height() for i in self.items))
        self.setCurrentItem(routeKey)

        self.updateGeometry()

    def setCurrentIndex(self, index: int):
        if not 0 <= index < len(self.items) or index == self.currentIndex():
            return

        if 0<= self.currentIndex() < len(self.items):
            self.currentItem().setSelected(False)

        self._currentIndex = index
        self.currentItem().setSelected(True)

        # 移除 trailing 项
        for item in self.items[-1:index:-1]:
            item = self.items.pop()
            self.itemMap.pop(item.routeKey)
            item.deleteLater()

        self.updateGeometry()

        self.currentIndexChanged.emit(index)
        self.currentItemChanged.emit(self.currentItem().routeKey)

    def setCurrentItem(self, routeKey: str):
        if routeKey not in self.itemMap:
            return

        self.setCurrentIndex(self.items.index(self.itemMap[routeKey]))

    def setItemText(self, routeKey: str, text: str):
        item = self.item(routeKey)
        if item:
            item.setText(text)

    def item(self, routeKey: str) -> BreadcrumbItem:
        return self.itemMap.get(routeKey, None)

    def itemAt(self, index: int):
        if 0 <= index < len(self.items):
            return self.items[index]

        return None

    def currentIndex(self):
        return self._currentIndex

    def currentItem(self) -> BreadcrumbItem:
        if self.currentIndex() >= 0:
            return self.items[self.currentIndex()]

        return None

    def resizeEvent(self, e):
        self.updateGeometry()

    def clear(self):
        """清空所有项"""
        while self.items:
            item = self.items.pop()
            self.itemMap.pop(item.routeKey)
            item.deleteLater()

        self.elideButton.hide()
        self._currentIndex = -1

    def popItem(self):
        """弹出尾部项"""
        if not self.items:
            return

        if self.count() >= 2:
            self.setCurrentIndex(self.currentIndex() - 1)
        else:
            self.clear()

    def count(self):
        """返回项的数量"""
        return len(self.items)

    def updateGeometry(self):
        if not self.items:
            return

        x = 0
        self.elideButton.hide()
        self.hiddenItems = self.items[:-1].copy()

        if not self.isElideVisible():
            visibleItems = self.items
            self.hiddenItems.clear()
        else:
            visibleItems = [self.elideButton, self.items[-1]]
            w = sum(i.width() for i in visibleItems)

            for item in self.items[-2::-1]:
                w += item.width()
                if w > self.width():
                    break

                visibleItems.insert(1, item)
                self.hiddenItems.remove(item)

        for item in self.hiddenItems:
            item.hide()

        for item in visibleItems:
            item.move(x, (self.height() - item.height()) // 2)
            item.show()
            x += item.width()

    def isElideVisible(self):
        w = sum(i.width() for i in self.items)
        return w > self.width()

    def setFont(self, font: QFont):
        super().setFont(font)

        s = int(fontPixelSize(font) / 14 * 16)
        self.elideButton.setFixedSize(s, s)

        for item in self.items:
            item.setFont(font)

    def _showHiddenItemsMenu(self):
        self.elideButton.clearState()

        menu = RoundMenu(parent=self)
        menu.setItemHeight(32)

        for item in self.hiddenItems:
            menu.addAction(
                QAction(item.text, menu, triggered=lambda checked=True, i=item: self.setCurrentItem(i.routeKey)))

        # 判断the 动画 type by choosing maximum 高度 的 视图
        x = -menu.layout().contentsMargins().left()
        pd = self.mapToGlobal(QPoint(x, self.height()))
        hd = menu.view.heightForAnimation(pd, MenuAnimationType.DROP_DOWN)

        pu = self.mapToGlobal(QPoint(x, 0))
        hu = menu.view.heightForAnimation(pu, MenuAnimationType.PULL_UP)

        if hd >= hu:
            menu.view.adjustSize(pd, MenuAnimationType.DROP_DOWN)
            menu.exec(pd, aniType=MenuAnimationType.DROP_DOWN)
        else:
            menu.view.adjustSize(pu, MenuAnimationType.PULL_UP)
            menu.exec(pu, aniType=MenuAnimationType.PULL_UP)

    def getSpacing(self):
        return self._spacing

    def setSpacing(self, spacing: int):
        if spacing == self._spacing:
            return

        self._spacing = spacing
        for item in self.items:
            item.setSpacing(spacing)

    spacing = Property(int, getSpacing, setSpacing)