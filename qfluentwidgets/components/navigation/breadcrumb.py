# coding: utf-8
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
    """ Bread crumb 部件 """

    clicked = Signal()

    def __init__(self, parent=None):
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
    """ Elide 按钮 """

    def __init__(self, parent=None):
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
    """ Breadcrumb 项 """

    def __init__(self, routeKey: str, text: str, index: int, parent=None):
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
    """ Breadcrumb 栏 """

    currentItemChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None):
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
        """ 添加 项

        参数
        ----------
        routeKey: str
            unique key 的 项

        text: str
            文本 的 项
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
        """ 清空all 项 """
        while self.items:
            item = self.items.pop()
            self.itemMap.pop(item.routeKey)
            item.deleteLater()

        self.elideButton.hide()
        self._currentIndex = -1

    def popItem(self):
        """ pop trailing 项 """
        if not self.items:
            return

        if self.count() >= 2:
            self.setCurrentIndex(self.currentIndex() - 1)
        else:
            self.clear()

    def count(self):
        """ 返回 number 的 项 """
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
