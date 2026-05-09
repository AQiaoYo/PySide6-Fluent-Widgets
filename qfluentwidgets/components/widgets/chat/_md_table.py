# coding: utf-8
"""Markdown 表格自定义渲染 mixin.

把 ``markdown_view._TextBlock`` 中"识别 GFM 表格 + 调整 cell padding /
border / spacing + paint 表头浅灰背景 + paint 外圆角描边"这一组 ~260 行
逻辑抽到独立的 mixin, 让 ``_TextBlock`` 主类不再混杂表格视觉细节.

依赖 (consumer 类必须提供):
    self.document() -> QTextDocument
    self.viewport() -> QWidget
    self.horizontalScrollBar() / self.verticalScrollBar()

子类的 ``_BLOCK_TOP_MARGIN`` 控制表格上下间距 (与外层 block spacing 节奏
保持一致); 不存在时回退到本 mixin 的默认值.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath,
    QTextFrameFormat, QTextLength, QTextTable, QTextTableCellFormat,
    QTextTableFormat,
)

from ....common.style_sheet import isDarkTheme


__all__ = ['TableRenderMixin']


class TableRenderMixin:
    """混入 ``QTextBrowser`` 子类的 GFM 表格视觉处理.

    使用方法::

        class _TextBlock(InlineCodeRenderMixin, TableRenderMixin, QTextBrowser):
            def setMarkdown(self, text):
                self.document().setMarkdown(...)
                ...
                self._styleTables()    # 调整 border / padding / spacing
                ...

            def paintEvent(self, e):
                self._paintTableHeaderBackgrounds()  # super 之前
                super().paintEvent(e)
                self._paintTableBorders()            # super 之后
    """

    # 视觉参数 (子类可覆盖)
    _TABLE_CELL_PAD_X = 16
    _TABLE_CELL_PAD_Y = 8
    _TABLE_ROW_BORDER = 1
    _TABLE_HEADER_BORDER = 1
    _TABLE_BORDER_RADIUS = 8
    _TABLE_OUTER_BORDER = 1
    # 表格整体的 top/bottom margin. 与外层 block spacing 节奏对齐.
    # 子类 _TextBlock 已定义 _BLOCK_TOP_MARGIN; 走 ``getattr`` 兜底.
    _BLOCK_TOP_MARGIN = 8

    # ------------------------------------------------------------------
    # _styleTables: 设置 cell border / padding / spacing
    # ------------------------------------------------------------------

    def _styleTables(self) -> None:
        """重排 markdown 表格的默认样式.

        Qt ``QTextDocument.setMarkdown`` 对 GFM 表格的默认渲染是 "separate
        border" 模式 — 每个 cell 有独立边框 + cellSpacing>0 间隙, 视觉上
        每格都是独立圆角矩形. 这里改成 GitHub / Fluent TableView 的 "无列
        分隔线 + 行间水平细线 + 表头浅背景" 风格.
        """
        if isDarkTheme():
            sep_color = QColor(255, 255, 255, 30)
        else:
            sep_color = QColor(0, 0, 0, 25)
        solid = QTextFrameFormat.BorderStyle.BorderStyle_Solid
        none_ = QTextFrameFormat.BorderStyle.BorderStyle_None

        block_top_margin = getattr(self, "_BLOCK_TOP_MARGIN", 8)
        doc = self.document()
        for frame in doc.rootFrame().childFrames():
            if not isinstance(frame, QTextTable):
                continue

            # 表格级: 关掉外边框, 邻接边共享, cell 之间无间隙
            tfmt: QTextTableFormat = frame.format().toTableFormat()
            tfmt.setBorder(0)
            tfmt.setBorderCollapse(True)
            tfmt.setBorderStyle(none_)
            tfmt.setCellSpacing(0)
            tfmt.setCellPadding(0)
            tfmt.setLeftMargin(0)
            tfmt.setRightMargin(0)
            tfmt.setTopMargin(block_top_margin)
            tfmt.setBottomMargin(block_top_margin)
            # 表格宽度 = 100% 容器
            tfmt.clearColumnWidthConstraints()
            tfmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))
            frame.setFormat(tfmt)

            rows = frame.rows()
            cols = frame.columns()
            pad_x = self._TABLE_CELL_PAD_X
            pad_y = self._TABLE_CELL_PAD_Y
            for r in range(rows):
                is_last = (r == rows - 1)
                bottom_w = 0 if is_last else self._TABLE_ROW_BORDER
                for c in range(cols):
                    cell = frame.cellAt(r, c)
                    cfmt: QTextTableCellFormat = (
                        cell.format().toTableCellFormat()
                    )
                    # 列方向: 不画任何 border
                    cfmt.setLeftBorder(0)
                    cfmt.setLeftBorderStyle(none_)
                    cfmt.setRightBorder(0)
                    cfmt.setRightBorderStyle(none_)
                    cfmt.setTopBorder(0)
                    cfmt.setTopBorderStyle(none_)
                    # 行方向: 只画 bottom 分隔线 (除最后一行)
                    cfmt.setBottomBorder(bottom_w)
                    cfmt.setBottomBorderStyle(solid if bottom_w else none_)
                    cfmt.setBottomBorderBrush(sep_color)
                    # cell 内边距 (Fluent table 风格大水平 + 适中竖向)
                    cfmt.setLeftPadding(pad_x)
                    cfmt.setRightPadding(pad_x)
                    cfmt.setTopPadding(pad_y)
                    cfmt.setBottomPadding(pad_y)
                    cell.setFormat(cfmt)

    # ------------------------------------------------------------------
    # paint: 表头浅灰背景 + 外圆角描边
    # ------------------------------------------------------------------

    def _tableRectInViewport(self, tbl: QTextTable) -> QRectF:
        """计算 ``tbl`` 在 viewport 坐标系下的真实外接矩形.

        不要信 ``QAbstractTextDocumentLayout.frameBoundingRect`` 在 markdown
        表格上的返回值 — 实测它给的是错的 (left=16 偏移, width=root frame
        宽), 与 Qt 实际渲染的 cell 不对齐. 这里改用 cell 内 block 的
        ``blockBoundingRect`` 反推 cell 边沿.
        """
        rows = tbl.rows()
        cols = tbl.columns()
        if rows < 1 or cols < 1:
            return QRectF()

        layout = self.document().documentLayout()
        pad_x = self._TABLE_CELL_PAD_X
        pad_y = self._TABLE_CELL_PAD_Y

        tl_block = tbl.cellAt(0, 0).firstCursorPosition().block()
        br_block = tbl.cellAt(rows - 1, cols - 1).lastCursorPosition().block()
        tl_br = layout.blockBoundingRect(tl_block)
        br_br = layout.blockBoundingRect(br_block)
        if not (tl_br.isValid() and br_br.isValid()):
            return QRectF()

        left = tl_br.left() - pad_x
        top = tl_br.top() - pad_y
        right = br_br.right() + pad_x
        bottom = br_br.bottom() + pad_y

        scroll_x = self.horizontalScrollBar().value()
        scroll_y = self.verticalScrollBar().value()
        return QRectF(
            left - scroll_x,
            top - scroll_y,
            right - left,
            bottom - top,
        )

    def _paintTableHeaderBackgrounds(self) -> None:
        """画 markdown 表格表头 row 0 的浅灰背景, clip 到外圆角内.

        必须在 ``super().paintEvent`` **之前**调 — 这样 Qt 默认渲染文字
        时画在我们的浅灰背景上面.
        """
        doc = self.document()
        tables = [
            f for f in doc.rootFrame().childFrames()
            if isinstance(f, QTextTable)
        ]
        if not tables:
            return

        if isDarkTheme():
            header_bg = QColor(255, 255, 255, 16)
        else:
            header_bg = QColor(0, 0, 0, 10)
        radius = self._TABLE_BORDER_RADIUS
        pad_y = self._TABLE_CELL_PAD_Y

        layout = doc.documentLayout()

        painter = QPainter(self.viewport())
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)

            for tbl in tables:
                if tbl.rows() < 1:
                    continue
                table_rect = self._tableRectInViewport(tbl)
                if table_rect.isEmpty():
                    continue

                header_cell = tbl.cellAt(0, 0)
                first_block = header_cell.firstCursorPosition().block()
                last_block = header_cell.lastCursorPosition().block()
                top_br = layout.blockBoundingRect(first_block)
                bot_br = layout.blockBoundingRect(last_block)
                header_h = (bot_br.bottom() - top_br.top()) + 2 * pad_y
                if header_h <= 0:
                    continue

                header_rect = QRectF(
                    table_rect.left(),
                    table_rect.top(),
                    table_rect.width(),
                    header_h,
                )

                # 表头浅灰区域 = 外圆角矩形 ∩ 表头矩形
                round_path = QPainterPath()
                round_path.addRoundedRect(table_rect, radius, radius)
                head_path = QPainterPath()
                head_path.addRect(header_rect)
                clipped = round_path.intersected(head_path)
                painter.fillPath(clipped, header_bg)
        finally:
            painter.end()

    def _paintTableBorders(self) -> None:
        """画 markdown 表格的外圆角边框.

        Qt ``QTextTableFormat`` 不支持 border-radius, 这里在 paintEvent 阶段
        拿到 viewport 坐标里的外接矩形画 1px 圆角描边, 视觉上把直角 cell
        装进圆角容器.
        """
        doc = self.document()
        tables = [
            f for f in doc.rootFrame().childFrames()
            if isinstance(f, QTextTable)
        ]
        if not tables:
            return

        if isDarkTheme():
            border = QColor(255, 255, 255, 35)
        else:
            border = QColor(0, 0, 0, 35)
        radius = self._TABLE_BORDER_RADIUS
        bw = self._TABLE_OUTER_BORDER

        painter = QPainter(self.viewport())
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = painter.pen()
            pen.setColor(border)
            pen.setWidthF(bw)
            painter.setPen(pen)

            for tbl in tables:
                rect = self._tableRectInViewport(tbl)
                if rect.isEmpty():
                    continue
                # 描边内缩 0.5 让 1px 线整张 pixel 落在矩形边内
                rect = rect.adjusted(0.5, 0.5, -0.5, -0.5)
                painter.drawRoundedRect(rect, radius, radius)
        finally:
            painter.end()
