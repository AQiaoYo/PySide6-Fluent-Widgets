# coding: utf-8
"""
组件快速预览工具

用法:
    uv run preview PushButton          # 预览 PushButton 及其所有变体
    uv run preview PushButton --dark   # 暗色主题预览
    uv run preview --list              # 列出所有可预览组件
    uv run preview push                # 模糊搜索包含 "push" 的组件
"""
import sys
import argparse
import inspect
from difflib import get_close_matches

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QScrollArea, QButtonGroup
)
from PySide6.QtGui import QAction

import qfluentwidgets
from qfluentwidgets import (
    setTheme, Theme, toggleTheme, isDarkTheme,
    FluentIcon, ToolButton, ToolTipFilter, CaptionLabel,
    TitleLabel, BodyLabel, StrongBodyLabel,
    ScrollArea, PrimaryPushButton, PushButton,
)


def _get_all_widget_classes():
    """收集 qfluentwidgets 中所有 QWidget 子类"""
    result = {}
    for name in dir(qfluentwidgets):
        obj = getattr(qfluentwidgets, name, None)
        if obj is None:
            continue
        if isinstance(obj, type) and issubclass(obj, QWidget) and obj is not QWidget:
            result[name] = obj
    return result


# ---------------------------------------------------------------------------
# 组件示例工厂
# 每个工厂函数返回一个 (widget, description) 或 [(widget, description), ...] 列表
# 这里注册的组件会有丰富的演示效果；未注册的组件使用通用实例化
# ---------------------------------------------------------------------------

def _make_example_factories():
    """构建组件名 -> 示例工厂的映射"""
    factories = {}

    def register(*names):
        """装饰器: 将工厂函数注册到多个组件名"""
        def decorator(func):
            for n in names:
                factories[n] = func
            return func
        return decorator

    # ---- Buttons ----
    @register('PushButton', 'PrimaryPushButton', 'TransparentPushButton',
              'ToggleButton', 'TogglePushButton', 'HyperlinkButton',
              'PillPushButton', 'TransparentTogglePushButton')
    def _buttons(parent):
        from qfluentwidgets import (
            PushButton, PrimaryPushButton, TransparentPushButton,
            ToggleButton, HyperlinkButton, PillPushButton,
            TransparentTogglePushButton
        )
        return [
            (PushButton('Standard', parent), 'PushButton - 标准按钮'),
            (PrimaryPushButton('Primary', parent), 'PrimaryPushButton - 主要按钮'),
            (TransparentPushButton('Transparent', parent, FluentIcon.BOOK_SHELF),
             'TransparentPushButton - 透明按钮'),
            (ToggleButton('Toggle', parent, FluentIcon.BASKETBALL),
             'ToggleButton - 切换按钮'),
            (PillPushButton('Tag', parent, FluentIcon.TAG),
             'PillPushButton - 药丸按钮'),
            (HyperlinkButton('', 'HyperlinkButton', parent, FluentIcon.LINK),
             'HyperlinkButton - 超链接按钮'),
            (TransparentTogglePushButton('Toggle', parent, FluentIcon.BASKETBALL),
             'TransparentTogglePushButton - 透明切换按钮'),
        ]

    @register('ToolButton', 'PrimaryToolButton', 'TransparentToolButton',
              'ToggleToolButton', 'TransparentToggleToolButton', 'PillToolButton')
    def _tool_buttons(parent):
        from qfluentwidgets import (
            ToolButton, PrimaryToolButton, TransparentToolButton,
            ToggleToolButton, TransparentToggleToolButton, PillToolButton
        )
        return [
            (ToolButton(FluentIcon.SETTING, parent), 'ToolButton'),
            (PrimaryToolButton(FluentIcon.BASKETBALL, parent), 'PrimaryToolButton'),
            (TransparentToolButton(FluentIcon.BOOK_SHELF, parent), 'TransparentToolButton'),
            (ToggleToolButton(FluentIcon.BASKETBALL, parent), 'ToggleToolButton'),
            (TransparentToggleToolButton(FluentIcon.BASKETBALL, parent), 'TransparentToggleToolButton'),
            (PillToolButton(FluentIcon.BASKETBALL, parent), 'PillToolButton'),
        ]

    @register('DropDownPushButton', 'PrimaryDropDownPushButton',
              'TransparentDropDownPushButton', 'SplitPushButton',
              'PrimarySplitPushButton')
    def _dropdown_buttons(parent):
        from qfluentwidgets import (
            DropDownPushButton, PrimaryDropDownPushButton,
            TransparentDropDownPushButton, SplitPushButton,
            PrimarySplitPushButton, RoundMenu, Action
        )
        def make_menu():
            menu = RoundMenu(parent=parent)
            menu.addAction(Action(FluentIcon.SEND, 'Send'))
            menu.addAction(Action(FluentIcon.SAVE, 'Save'))
            return menu

        btn1 = DropDownPushButton('DropDown', parent, FluentIcon.MAIL)
        btn1.setMenu(make_menu())
        btn2 = PrimaryDropDownPushButton('Primary DropDown', parent, FluentIcon.MAIL)
        btn2.setMenu(make_menu())
        btn3 = TransparentDropDownPushButton('Transparent', parent, FluentIcon.MAIL)
        btn3.setMenu(make_menu())
        btn4 = SplitPushButton('Split', parent, FluentIcon.BASKETBALL)
        btn4.setFlyout(make_menu())
        btn5 = PrimarySplitPushButton('Primary Split', parent, FluentIcon.BASKETBALL)
        btn5.setFlyout(make_menu())

        return [
            (btn1, 'DropDownPushButton - 下拉按钮'),
            (btn2, 'PrimaryDropDownPushButton'),
            (btn3, 'TransparentDropDownPushButton'),
            (btn4, 'SplitPushButton - 拆分按钮'),
            (btn5, 'PrimarySplitPushButton'),
        ]

    # ---- CheckBox / RadioButton / SwitchButton ----
    @register('CheckBox')
    def _checkbox(parent):
        from qfluentwidgets import CheckBox
        cb1 = CheckBox('Two-state CheckBox', parent)
        cb2 = CheckBox('Three-state CheckBox', parent)
        cb2.setTristate(True)
        cb3 = CheckBox('Checked', parent)
        cb3.setChecked(True)
        return [
            (cb1, 'CheckBox - 两态'),
            (cb2, 'CheckBox - 三态'),
            (cb3, 'CheckBox - 已勾选'),
        ]

    @register('RadioButton')
    def _radio(parent):
        from qfluentwidgets import RadioButton
        w = QWidget(parent)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(2, 0, 0, 0)
        layout.setSpacing(12)
        group = QButtonGroup(w)
        for i, text in enumerate(['Option A', 'Option B', 'Option C']):
            rb = RadioButton(text, w)
            group.addButton(rb)
            layout.addWidget(rb)
            if i == 0:
                rb.setChecked(True)
        return [(w, 'RadioButton - 单选按钮组')]

    @register('SwitchButton')
    def _switch(parent):
        from qfluentwidgets import SwitchButton
        sw1 = SwitchButton(parent=parent)
        sw2 = SwitchButton(parent=parent)
        sw2.setChecked(True)
        return [
            (sw1, 'SwitchButton - Off'),
            (sw2, 'SwitchButton - On'),
        ]

    # ---- Input ----
    @register('ComboBox', 'EditableComboBox')
    def _combo(parent):
        from qfluentwidgets import ComboBox, EditableComboBox
        cb = ComboBox(parent)
        cb.addItems(['Option 1', 'Option 2', 'Option 3'])
        cb.setMinimumWidth(200)
        ecb = EditableComboBox(parent)
        ecb.addItems(['Star Platinum', 'Crazy Diamond', 'Gold Experience'])
        ecb.setPlaceholderText('Choose...')
        ecb.setMinimumWidth(200)
        return [
            (cb, 'ComboBox - 下拉框'),
            (ecb, 'EditableComboBox - 可编辑下拉框'),
        ]

    @register('LineEdit', 'SearchLineEdit', 'PasswordLineEdit', 'TextEdit')
    def _line_edit(parent):
        from qfluentwidgets import LineEdit, SearchLineEdit, PasswordLineEdit, TextEdit
        le = LineEdit(parent)
        le.setPlaceholderText('LineEdit placeholder')
        le.setMinimumWidth(250)
        sle = SearchLineEdit(parent)
        sle.setPlaceholderText('Search...')
        sle.setMinimumWidth(250)
        ple = PasswordLineEdit(parent)
        ple.setPlaceholderText('Password')
        ple.setMinimumWidth(250)
        te = TextEdit(parent)
        te.setPlaceholderText('TextEdit multi-line input...')
        te.setMinimumWidth(250)
        te.setMaximumHeight(100)
        return [
            (le, 'LineEdit - 单行输入'),
            (sle, 'SearchLineEdit - 搜索框'),
            (ple, 'PasswordLineEdit - 密码框'),
            (te, 'TextEdit - 多行输入'),
        ]

    @register('Slider')
    def _slider(parent):
        from qfluentwidgets import Slider
        s1 = Slider(Qt.Horizontal, parent)
        s1.setRange(0, 100)
        s1.setValue(40)
        s1.setMinimumWidth(250)
        s2 = Slider(Qt.Vertical, parent)
        s2.setRange(0, 100)
        s2.setValue(60)
        s2.setMinimumHeight(120)
        return [
            (s1, 'Slider - 水平滑块'),
            (s2, 'Slider - 垂直滑块'),
        ]

    @register('SpinBox', 'DoubleSpinBox', 'CompactSpinBox', 'CompactDoubleSpinBox')
    def _spin(parent):
        from qfluentwidgets import SpinBox, DoubleSpinBox, CompactSpinBox, CompactDoubleSpinBox
        sb = SpinBox(parent)
        sb.setRange(0, 100)
        sb.setValue(42)
        dsb = DoubleSpinBox(parent)
        dsb.setRange(0.0, 1.0)
        dsb.setSingleStep(0.1)
        dsb.setValue(0.5)
        csb = CompactSpinBox(parent)
        csb.setRange(0, 100)
        csb.setValue(42)
        cdsb = CompactDoubleSpinBox(parent)
        cdsb.setRange(0.0, 1.0)
        cdsb.setSingleStep(0.1)
        cdsb.setValue(0.5)
        return [
            (sb, 'SpinBox'),
            (dsb, 'DoubleSpinBox'),
            (csb, 'CompactSpinBox'),
            (cdsb, 'CompactDoubleSpinBox'),
        ]

    # ---- Progress ----
    @register('ProgressBar', 'IndeterminateProgressBar')
    def _progress_bar(parent):
        from qfluentwidgets import ProgressBar, IndeterminateProgressBar
        pb = ProgressBar(parent)
        pb.setRange(0, 100)
        pb.setValue(65)
        pb.setMinimumWidth(250)
        ipb = IndeterminateProgressBar(parent)
        ipb.setMinimumWidth(250)
        ipb.start()
        return [
            (pb, 'ProgressBar - 65%'),
            (ipb, 'IndeterminateProgressBar - 不确定进度'),
        ]

    @register('ProgressRing', 'IndeterminateProgressRing')
    def _progress_ring(parent):
        from qfluentwidgets import ProgressRing, IndeterminateProgressRing
        pr = ProgressRing(parent)
        pr.setRange(0, 100)
        pr.setValue(65)
        pr.setFixedSize(80, 80)
        ipr = IndeterminateProgressRing(parent)
        ipr.setFixedSize(80, 80)
        ipr.start()
        return [
            (pr, 'ProgressRing - 65%'),
            (ipr, 'IndeterminateProgressRing'),
        ]

    # ---- Info ----
    @register('InfoBadge')
    def _info_badge(parent):
        from qfluentwidgets import InfoBadge
        return [
            (InfoBadge.info(1, parent), 'InfoBadge - info'),
            (InfoBadge.success(10, parent), 'InfoBadge - success'),
            (InfoBadge.warning(100, parent), 'InfoBadge - warning'),
            (InfoBadge.error(99, parent), 'InfoBadge - error'),
        ]

    # ---- Date/Time ----
    @register('CalendarPicker', 'FastCalendarPicker')
    def _calendar(parent):
        from qfluentwidgets import CalendarPicker, FastCalendarPicker
        cp = CalendarPicker(parent)
        cp.setMinimumWidth(200)
        fcp = FastCalendarPicker(parent)
        fcp.setMinimumWidth(200)
        return [
            (cp, 'CalendarPicker - 日历选择器'),
            (fcp, 'FastCalendarPicker - 快速日历选择器'),
        ]

    @register('DatePicker', 'ZhDatePicker')
    def _date_picker(parent):
        from qfluentwidgets import DatePicker, ZhDatePicker
        dp = DatePicker(parent)
        zdp = ZhDatePicker(parent)
        return [
            (dp, 'DatePicker - 日期选择器'),
            (zdp, 'ZhDatePicker - 中文日期选择器'),
        ]

    @register('TimePicker', 'AMTimePicker')
    def _time_picker(parent):
        from qfluentwidgets import TimePicker, AMTimePicker
        tp = TimePicker(parent)
        atp = AMTimePicker(parent)
        return [
            (tp, 'TimePicker - 时间选择器'),
            (atp, 'AMTimePicker - AM/PM 时间选择器'),
        ]

    # ---- Navigation ----
    @register('Pivot')
    def _pivot(parent):
        from qfluentwidgets import Pivot
        pv = Pivot(parent)
        pv.addItem('tab1', 'Tab 1')
        pv.addItem('tab2', 'Tab 2')
        pv.addItem('tab3', 'Tab 3')
        pv.setCurrentItem('tab1')
        return [(pv, 'Pivot - 标签页导航')]

    @register('SegmentedWidget')
    def _segmented(parent):
        from qfluentwidgets import SegmentedWidget
        sw = SegmentedWidget(parent)
        sw.addItem('s1', 'Segment 1')
        sw.addItem('s2', 'Segment 2')
        sw.addItem('s3', 'Segment 3')
        sw.setCurrentItem('s1')
        return [(sw, 'SegmentedWidget - 分段控件')]

    @register('BreadcrumbBar')
    def _breadcrumb(parent):
        from qfluentwidgets import BreadcrumbBar
        bb = BreadcrumbBar(parent)
        bb.addItem('home', 'Home')
        bb.addItem('docs', 'Documents')
        bb.addItem('file', 'File.txt')
        bb.setMinimumWidth(300)
        return [(bb, 'BreadcrumbBar - 面包屑导航')]

    # ---- Label ----
    @register('CaptionLabel', 'BodyLabel', 'StrongBodyLabel', 'SubtitleLabel',
              'TitleLabel', 'LargeTitleLabel', 'DisplayLabel')
    def _labels(parent):
        from qfluentwidgets import (
            CaptionLabel, BodyLabel, StrongBodyLabel, SubtitleLabel,
            TitleLabel, LargeTitleLabel, DisplayLabel
        )
        return [
            (CaptionLabel('CaptionLabel', parent), 'CaptionLabel - 12px'),
            (BodyLabel('BodyLabel', parent), 'BodyLabel - 14px'),
            (StrongBodyLabel('StrongBodyLabel', parent), 'StrongBodyLabel - 14px bold'),
            (SubtitleLabel('SubtitleLabel', parent), 'SubtitleLabel - 20px'),
            (TitleLabel('TitleLabel', parent), 'TitleLabel - 28px'),
            (LargeTitleLabel('LargeTitleLabel', parent), 'LargeTitleLabel - 40px'),
            (DisplayLabel('DisplayLabel', parent), 'DisplayLabel - 68px'),
        ]

    # ---- Tab ----
    @register('TabBar')
    def _tab_bar(parent):
        from qfluentwidgets import TabBar
        tb = TabBar(parent)
        tb.addTab('tab1', 'Tab 1', FluentIcon.HOME)
        tb.addTab('tab2', 'Tab 2', FluentIcon.DOCUMENT)
        tb.addTab('tab3', 'Tab 3', FluentIcon.SETTING)
        tb.setMinimumWidth(400)
        return [(tb, 'TabBar - 标签栏')]

    # ---- Card ----
    @register('SimpleCardWidget', 'ElevatedCardWidget', 'CardWidget')
    def _card(parent):
        from qfluentwidgets import SimpleCardWidget, ElevatedCardWidget, CardWidget, BodyLabel
        items = []
        for cls, name in [
            (SimpleCardWidget, 'SimpleCardWidget'),
            (ElevatedCardWidget, 'ElevatedCardWidget'),
            (CardWidget, 'CardWidget'),
        ]:
            card = cls(parent)
            card.setFixedSize(200, 120)
            layout = QVBoxLayout(card)
            layout.addWidget(BodyLabel(name, card))
            items.append((card, name))
        return items

    # ---- Separator ----
    @register('HorizontalSeparator', 'VerticalSeparator')
    def _separator(parent):
        from qfluentwidgets import HorizontalSeparator, VerticalSeparator
        hs = HorizontalSeparator(parent)
        hs.setMinimumWidth(200)
        vs = VerticalSeparator(parent)
        vs.setMinimumHeight(60)
        return [
            (hs, 'HorizontalSeparator - 水平分隔线'),
            (vs, 'VerticalSeparator - 垂直分隔线'),
        ]

    @register('PipsScrollButtonDisplayMode', 'PipsPager')
    def _pips(parent):
        from qfluentwidgets import PipsPager
        pp = PipsPager(Qt.Horizontal, parent)
        pp.setPageNumber(5)
        pp.setVisibleNumber(5)
        return [(pp, 'PipsPager - 分页指示器')]

    return factories


EXAMPLE_FACTORIES = _make_example_factories()


def _try_instantiate(cls, name: str, parent: QWidget):
    """尝试用最少参数自动实例化一个组件类

    策略按优先级:
    1. cls(parent=parent)
    2. 根据参数名猜测常见默认值 (text, icon, title 等)
    3. cls(name, parent) 作为最终兜底
    """
    # 策略 1: 仅 parent 参数
    try:
        return cls(parent=parent)
    except TypeError:
        pass

    # 策略 2: 分析签名，对常见参数名给默认值
    try:
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.values())
        required = [p for p in params[1:]
                    if p.default is inspect.Parameter.empty
                    and p.name not in ('parent', 'args', 'kwargs')]

        if required:
            kwargs = {'parent': parent}
            for p in required:
                pname = p.name.lower()
                if 'text' in pname or 'title' in pname or pname == 'content':
                    kwargs[p.name] = name
                elif 'icon' in pname:
                    kwargs[p.name] = FluentIcon.SETTING
                elif 'orientation' in pname:
                    kwargs[p.name] = Qt.Horizontal
                else:
                    raise TypeError(f'Cannot guess value for param: {p.name}')
            return cls(**kwargs)
    except (TypeError, ValueError):
        pass

    # 策略 3: 位置参数兜底
    try:
        return cls(name, parent)
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Preview 窗口
# ---------------------------------------------------------------------------

class PreviewWindow(QWidget):
    """轻量预览窗口"""

    def __init__(self, component_name: str, dark: bool = False):
        super().__init__()
        self._component_name = component_name
        self._cards = []

        if dark:
            setTheme(Theme.DARK)

        self.setWindowTitle(f'Preview: {component_name}')
        self.setAttribute(Qt.WA_StyledBackground)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # --- 顶部工具栏 ---
        self._toolbar = QWidget(self)
        self._toolbar.setFixedHeight(56)
        toolbar_layout = QHBoxLayout(self._toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)

        title = TitleLabel(component_name, self._toolbar)
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        theme_btn = ToolButton(FluentIcon.CONSTRACT, self._toolbar)
        theme_btn.setToolTip('Toggle theme')
        theme_btn.installEventFilter(ToolTipFilter(theme_btn))
        theme_btn.clicked.connect(self._toggle_theme)
        toolbar_layout.addWidget(theme_btn)

        root.addWidget(self._toolbar)

        # --- 滚动内容区 ---
        self._scroll = ScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setObjectName('scrollContent')
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(24)
        self._content_layout.setContentsMargins(24, 24, 24, 24)
        self._content_layout.setAlignment(Qt.AlignTop)

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll)

        # --- 填充组件示例 ---
        self._populate(component_name)
        self._apply_theme()
        self.resize(520, 600)

    def _apply_theme(self):
        dark = isDarkTheme()
        bg = '#202020' if dark else '#f5f5f5'
        card_bg = '#2d2d2d' if dark else 'white'
        card_border = '#3d3d3d' if dark else '#e0e0e0'

        self.setStyleSheet(f'''
            PreviewWindow {{ background: {bg}; }}
            #scrollContent {{ background: transparent; }}
        ''')
        self._scroll.setStyleSheet(f'''
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
        ''')
        self._toolbar.setStyleSheet(f'''
            QWidget {{ background: {bg}; }}
        ''')

        for card in self._cards:
            card.setStyleSheet(
                f'#exampleCard {{ background: {card_bg}; border-radius: 8px; '
                f'border: 1px solid {card_border}; }}')

    def _toggle_theme(self):
        toggleTheme(True)
        self._apply_theme()

    def _populate(self, name: str):
        """根据组件名填充示例

        优先使用手动注册的工厂函数（有丰富的多变体演示），
        否则自动尝试实例化组件（只要组件被 qfluentwidgets 导出即可）。
        """
        factory = EXAMPLE_FACTORIES.get(name)
        if factory:
            result = factory(self)
            if not isinstance(result, list):
                result = [result]
            for widget, description in result:
                self._add_card(widget, description)
            return

        # 自动实例化: 只要组件在 qfluentwidgets 中导出，就能直接预览
        all_classes = _get_all_widget_classes()
        cls = all_classes.get(name)
        if cls is None:
            self._content_layout.addWidget(
                BodyLabel(f'"{name}" 不是可预览的组件', self))
            return

        widget = _try_instantiate(cls, name, self)
        if widget is not None:
            self._add_card(widget, f'{name}')
        else:
            self._content_layout.addWidget(
                BodyLabel(f'"{name}" 无法自动实例化，请通过工厂注册', self))

    def _add_card(self, widget: QWidget, description: str):
        """添加一个示例卡片"""
        card = QFrame(self)
        card.setObjectName('exampleCard')
        self._cards.append(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        label = CaptionLabel(description, card)
        label.setTextColor('#888888', '#999999')
        card_layout.addWidget(label)

        widget.setParent(card)
        card_layout.addWidget(widget)

        self._content_layout.addWidget(card)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def _fuzzy_search(query: str, candidates: list[str], n: int = 15) -> list[str]:
    """模糊搜索: 先尝试子串匹配，再用 difflib"""
    query_lower = query.lower()
    # 子串匹配
    substr_matches = [c for c in candidates if query_lower in c.lower()]
    if substr_matches:
        return sorted(substr_matches)[:n]
    # difflib 模糊匹配
    return get_close_matches(query, candidates, n=n, cutoff=0.3)


def main():
    parser = argparse.ArgumentParser(
        prog='preview',
        description='PySide6-Fluent-Widgets 组件快速预览工具',
    )
    parser.add_argument('component', nargs='?', help='组件类名 (如 PushButton)')
    parser.add_argument('--dark', action='store_true', help='使用暗色主题')
    parser.add_argument('--list', action='store_true', dest='list_all', help='列出所有可预览组件')
    args = parser.parse_args()

    all_classes = _get_all_widget_classes()
    all_names = sorted(all_classes.keys())

    # --list: 列出所有可预览组件
    if args.list_all:
        registered = sorted(EXAMPLE_FACTORIES.keys())
        print(f'\n  已注册示例的组件 ({len(registered)} 个):')
        print(f'  {"=" * 40}')
        for name in registered:
            print(f'    {name}')
        print(f'\n  所有可用组件 ({len(all_names)} 个):')
        print(f'  {"=" * 40}')
        for name in all_names:
            marker = ' *' if name in EXAMPLE_FACTORIES else ''
            print(f'    {name}{marker}')
        print(f'\n  (* = 有丰富示例)')
        return

    if not args.component:
        parser.print_help()
        return

    name = args.component

    # 精确匹配
    if name in all_classes or name in EXAMPLE_FACTORIES:
        pass
    else:
        # 模糊搜索
        candidates = list(set(list(all_classes.keys()) + list(EXAMPLE_FACTORIES.keys())))
        matches = _fuzzy_search(name, candidates)
        if not matches:
            print(f'\n  找不到组件 "{name}"')
            print(f'  使用 --list 查看所有可用组件')
            return
        elif len(matches) == 1:
            name = matches[0]
            print(f'  -> 自动匹配到: {name}')
        else:
            print(f'\n  "{name}" 匹配到多个组件:')
            for i, m in enumerate(matches, 1):
                marker = ' *' if m in EXAMPLE_FACTORIES else ''
                print(f'    {i}. {m}{marker}')
            print(f'\n  (* = 有丰富示例)')
            try:
                choice = input('  输入序号选择 (直接回车选第一个): ').strip()
                idx = int(choice) - 1 if choice else 0
                name = matches[idx]
            except (ValueError, IndexError):
                print('  已取消')
                return

    # 启动预览
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    window = PreviewWindow(name, dark=args.dark)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
