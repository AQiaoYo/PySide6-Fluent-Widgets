# coding: utf-8
"""
组件工厂函数和注册表

- FACTORIES: 需要特殊配置的组件才需要注册（可选增强，非必需）
- discover_categories(): 基于 __module__ 自动发现并分类所有组件，零维护
- try_instantiate(): 自动实例化兜底
"""
import inspect
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

import qfluentwidgets
from qfluentwidgets import FluentIcon as FIF, BodyLabel


# ===================================================================
# 组件预览工厂 (可选增强)
#
# 只有需要特殊配置的组件才要注册。不在这里的组件会自动实例化。
# 格式: '组件名': lambda parent: [(widget, '描述'), ...]
# ===================================================================

def _buttons(p):
    from qfluentwidgets import (PushButton, PrimaryPushButton, TransparentPushButton,
                                ToggleButton, HyperlinkButton, PillPushButton,
                                TransparentTogglePushButton)
    return [
        (PushButton('Standard', p), 'PushButton - 标准按钮'),
        (PrimaryPushButton('Primary', p), 'PrimaryPushButton - 主要按钮'),
        (TransparentPushButton('Transparent', p, FIF.BOOK_SHELF), 'TransparentPushButton - 透明按钮'),
        (ToggleButton('Toggle', p, FIF.BASKETBALL), 'ToggleButton - 切换按钮'),
        (PillPushButton('Tag', p, FIF.TAG), 'PillPushButton - 药丸按钮'),
        (HyperlinkButton('', 'Hyperlink', p, FIF.LINK), 'HyperlinkButton - 超链接按钮'),
        (TransparentTogglePushButton('Toggle', p, FIF.BASKETBALL), 'TransparentTogglePushButton'),
    ]


def _tool_buttons(p):
    from qfluentwidgets import (ToolButton, PrimaryToolButton, TransparentToolButton,
                                ToggleToolButton, TransparentToggleToolButton, PillToolButton)
    return [
        (ToolButton(FIF.SETTING, p), 'ToolButton'),
        (PrimaryToolButton(FIF.BASKETBALL, p), 'PrimaryToolButton'),
        (TransparentToolButton(FIF.BOOK_SHELF, p), 'TransparentToolButton'),
        (ToggleToolButton(FIF.BASKETBALL, p), 'ToggleToolButton'),
        (TransparentToggleToolButton(FIF.BASKETBALL, p), 'TransparentToggleToolButton'),
        (PillToolButton(FIF.BASKETBALL, p), 'PillToolButton'),
    ]


def _dropdown_buttons(p):
    from qfluentwidgets import (DropDownPushButton, PrimaryDropDownPushButton,
                                TransparentDropDownPushButton, SplitPushButton,
                                PrimarySplitPushButton, RoundMenu, Action)
    def m():
        menu = RoundMenu(parent=p)
        menu.addAction(Action(FIF.SEND, 'Send'))
        menu.addAction(Action(FIF.SAVE, 'Save'))
        return menu
    b1 = DropDownPushButton('DropDown', p, FIF.MAIL); b1.setMenu(m())
    b2 = PrimaryDropDownPushButton('Primary', p, FIF.MAIL); b2.setMenu(m())
    b3 = TransparentDropDownPushButton('Transparent', p, FIF.MAIL); b3.setMenu(m())
    b4 = SplitPushButton('Split', p, FIF.BASKETBALL); b4.setFlyout(m())
    b5 = PrimarySplitPushButton('Primary Split', p, FIF.BASKETBALL); b5.setFlyout(m())
    return [
        (b1, 'DropDownPushButton'), (b2, 'PrimaryDropDownPushButton'),
        (b3, 'TransparentDropDownPushButton'),
        (b4, 'SplitPushButton'), (b5, 'PrimarySplitPushButton'),
    ]


def _checkbox(p):
    from qfluentwidgets import CheckBox
    c1 = CheckBox('Two-state', p)
    c2 = CheckBox('Three-state', p); c2.setTristate(True)
    c3 = CheckBox('Checked', p); c3.setChecked(True)
    return [(c1, 'CheckBox - 两态'), (c2, 'CheckBox - 三态'), (c3, 'CheckBox - 已勾选')]


def _radio(p):
    from qfluentwidgets import RadioButton
    w = QWidget(p); layout = QVBoxLayout(w); layout.setContentsMargins(2, 0, 0, 0); layout.setSpacing(12)
    group = QButtonGroup(w)
    for i, t in enumerate(['Option A', 'Option B', 'Option C']):
        rb = RadioButton(t, w); group.addButton(rb); layout.addWidget(rb)
        if i == 0: rb.setChecked(True)
    return [(w, 'RadioButton - 单选按钮组')]


def _switch(p):
    from qfluentwidgets import SwitchButton
    s1 = SwitchButton(parent=p)
    s2 = SwitchButton(parent=p); s2.setChecked(True)
    return [(s1, 'SwitchButton - Off'), (s2, 'SwitchButton - On')]


def _combo(p):
    from qfluentwidgets import ComboBox, EditableComboBox
    c = ComboBox(p); c.addItems(['Option 1', 'Option 2', 'Option 3']); c.setMinimumWidth(200)
    e = EditableComboBox(p); e.addItems(['Star Platinum', 'Crazy Diamond', 'Gold Experience'])
    e.setPlaceholderText('Choose...'); e.setMinimumWidth(200)
    return [(c, 'ComboBox - 下拉框'), (e, 'EditableComboBox - 可编辑下拉框')]


def _line_edit(p):
    from qfluentwidgets import LineEdit, SearchLineEdit, PasswordLineEdit, TextEdit
    le = LineEdit(p); le.setPlaceholderText('LineEdit'); le.setMinimumWidth(250)
    s = SearchLineEdit(p); s.setPlaceholderText('Search...'); s.setMinimumWidth(250)
    pw = PasswordLineEdit(p); pw.setPlaceholderText('Password'); pw.setMinimumWidth(250)
    te = TextEdit(p); te.setPlaceholderText('TextEdit...'); te.setMinimumWidth(250); te.setMaximumHeight(100)
    return [(le, 'LineEdit'), (s, 'SearchLineEdit'), (pw, 'PasswordLineEdit'), (te, 'TextEdit')]


def _slider(p):
    from qfluentwidgets import Slider
    h = Slider(Qt.Horizontal, p); h.setRange(0, 100); h.setValue(40); h.setMinimumWidth(250)
    v = Slider(Qt.Vertical, p); v.setRange(0, 100); v.setValue(60); v.setMinimumHeight(120)
    return [(h, 'Slider - 水平'), (v, 'Slider - 垂直')]


def _spin(p):
    from qfluentwidgets import SpinBox, DoubleSpinBox, CompactSpinBox, CompactDoubleSpinBox
    s = SpinBox(p); s.setRange(0, 100); s.setValue(42)
    d = DoubleSpinBox(p); d.setRange(0, 1); d.setSingleStep(0.1); d.setValue(0.5)
    cs = CompactSpinBox(p); cs.setRange(0, 100); cs.setValue(42)
    cd = CompactDoubleSpinBox(p); cd.setRange(0, 1); cd.setSingleStep(0.1); cd.setValue(0.5)
    return [(s, 'SpinBox'), (d, 'DoubleSpinBox'), (cs, 'CompactSpinBox'), (cd, 'CompactDoubleSpinBox')]


def _progress_bar(p):
    from qfluentwidgets import ProgressBar, IndeterminateProgressBar
    pb = ProgressBar(p); pb.setRange(0, 100); pb.setValue(65); pb.setMinimumWidth(250)
    ipb = IndeterminateProgressBar(p); ipb.setMinimumWidth(250); ipb.start()
    return [(pb, 'ProgressBar - 65%'), (ipb, 'IndeterminateProgressBar')]


def _progress_ring(p):
    from qfluentwidgets import ProgressRing, IndeterminateProgressRing
    pr = ProgressRing(p); pr.setRange(0, 100); pr.setValue(65); pr.setFixedSize(80, 80)
    ipr = IndeterminateProgressRing(p); ipr.setFixedSize(80, 80); ipr.start()
    return [(pr, 'ProgressRing - 65%'), (ipr, 'IndeterminateProgressRing')]


def _info_badge(p):
    from qfluentwidgets import InfoBadge
    return [(InfoBadge.info(1, p), 'info'), (InfoBadge.success(10, p), 'success'),
            (InfoBadge.warning(100, p), 'warning'), (InfoBadge.error(99, p), 'error')]


def _calendar(p):
    from qfluentwidgets import CalendarPicker, FastCalendarPicker
    c = CalendarPicker(p); c.setMinimumWidth(200)
    f = FastCalendarPicker(p); f.setMinimumWidth(200)
    return [(c, 'CalendarPicker'), (f, 'FastCalendarPicker')]


def _date_picker(p):
    from qfluentwidgets import DatePicker, ZhDatePicker
    return [(DatePicker(p), 'DatePicker'), (ZhDatePicker(p), 'ZhDatePicker')]


def _time_picker(p):
    from qfluentwidgets import TimePicker, AMTimePicker
    return [(TimePicker(p), 'TimePicker'), (AMTimePicker(p), 'AMTimePicker')]


def _pivot(p):
    from qfluentwidgets import Pivot
    pv = Pivot(p)
    for k, t in [('t1', 'Tab 1'), ('t2', 'Tab 2'), ('t3', 'Tab 3')]: pv.addItem(k, t)
    pv.setCurrentItem('t1')
    return [(pv, 'Pivot - 标签页导航')]


def _segmented(p):
    from qfluentwidgets import SegmentedWidget
    sw = SegmentedWidget(p)
    for k, t in [('s1', 'Seg 1'), ('s2', 'Seg 2'), ('s3', 'Seg 3')]: sw.addItem(k, t)
    sw.setCurrentItem('s1')
    return [(sw, 'SegmentedWidget')]


def _breadcrumb(p):
    from qfluentwidgets import BreadcrumbBar
    bb = BreadcrumbBar(p)
    for k, t in [('home', 'Home'), ('docs', 'Documents'), ('f', 'File.txt')]: bb.addItem(k, t)
    bb.setMinimumWidth(300)
    return [(bb, 'BreadcrumbBar')]


def _labels(p):
    from qfluentwidgets import (CaptionLabel, BodyLabel, StrongBodyLabel, SubtitleLabel,
                                TitleLabel, LargeTitleLabel, DisplayLabel)
    return [
        (CaptionLabel('CaptionLabel', p), '12px'), (BodyLabel('BodyLabel', p), '14px'),
        (StrongBodyLabel('StrongBodyLabel', p), '14px bold'), (SubtitleLabel('SubtitleLabel', p), '20px'),
        (TitleLabel('TitleLabel', p), '28px'), (LargeTitleLabel('LargeTitleLabel', p), '40px'),
        (DisplayLabel('DisplayLabel', p), '68px'),
    ]


def _tab_bar(p):
    from qfluentwidgets import TabBar
    tb = TabBar(p)
    tb.addTab('t1', 'Tab 1', FIF.HOME); tb.addTab('t2', 'Tab 2', FIF.DOCUMENT)
    tb.addTab('t3', 'Tab 3', FIF.SETTING); tb.setMinimumWidth(400)
    return [(tb, 'TabBar')]


def _cards(p):
    from qfluentwidgets import SimpleCardWidget, ElevatedCardWidget, CardWidget
    items = []
    for cls, name in [(SimpleCardWidget, 'SimpleCardWidget'), (ElevatedCardWidget, 'ElevatedCardWidget'),
                      (CardWidget, 'CardWidget')]:
        c = cls(p); c.setFixedSize(200, 120)
        QVBoxLayout(c).addWidget(BodyLabel(name, c))
        items.append((c, name))
    return items


def _separator(p):
    from qfluentwidgets import HorizontalSeparator, VerticalSeparator
    h = HorizontalSeparator(p); h.setMinimumWidth(200)
    v = VerticalSeparator(p); v.setMinimumHeight(60)
    return [(h, 'HorizontalSeparator'), (v, 'VerticalSeparator')]


def _pips(p):
    from qfluentwidgets import PipsPager
    pp = PipsPager(Qt.Horizontal, p); pp.setPageNumber(5); pp.setVisibleNumber(5)
    return [(pp, 'PipsPager')]


def _command_bar(p):
    from qfluentwidgets import CommandBar, CommandButton, Action
    bar = CommandBar(p)
    bar.addActions([
        Action(FIF.ADD, 'Add'),
        Action(FIF.EDIT, 'Edit'),
        Action(FIF.COPY, 'Copy'),
        Action(FIF.DELETE, 'Delete'),
    ])
    bar.addSeparator()
    bar.addAction(Action(FIF.SETTING, 'Settings'))
    bar.setMinimumWidth(300)
    bar.setFixedHeight(45)

    btn = CommandButton(FIF.SHARE, 'Share', p)
    return [
        (bar, 'CommandBar - 命令栏'),
        (btn, 'CommandButton - 命令按钮'),
    ]


# ===================================================================
# 注册表: 组件名 -> 工厂函数
#
# 只有需要特殊参数 / 多变体展示的组件才需要注册。
# 新增的组件如果 try_instantiate 能搞定，就不用加。
# ===================================================================

FACTORIES = {}
for _names, _fn in [
    ('PushButton PrimaryPushButton TransparentPushButton ToggleButton '
     'TogglePushButton HyperlinkButton PillPushButton TransparentTogglePushButton', _buttons),
    ('ToolButton PrimaryToolButton TransparentToolButton '
     'ToggleToolButton TransparentToggleToolButton PillToolButton', _tool_buttons),
    ('DropDownPushButton PrimaryDropDownPushButton TransparentDropDownPushButton '
     'SplitPushButton PrimarySplitPushButton', _dropdown_buttons),
    ('CheckBox', _checkbox),
    ('RadioButton', _radio),
    ('SwitchButton', _switch),
    ('ComboBox EditableComboBox', _combo),
    ('LineEdit SearchLineEdit PasswordLineEdit TextEdit', _line_edit),
    ('Slider', _slider),
    ('SpinBox DoubleSpinBox CompactSpinBox CompactDoubleSpinBox', _spin),
    ('ProgressBar IndeterminateProgressBar', _progress_bar),
    ('ProgressRing IndeterminateProgressRing', _progress_ring),
    ('InfoBadge', _info_badge),
    ('CalendarPicker FastCalendarPicker', _calendar),
    ('DatePicker ZhDatePicker', _date_picker),
    ('TimePicker AMTimePicker', _time_picker),
    ('Pivot', _pivot),
    ('SegmentedWidget', _segmented),
    ('BreadcrumbBar', _breadcrumb),
    ('CaptionLabel BodyLabel StrongBodyLabel SubtitleLabel TitleLabel LargeTitleLabel DisplayLabel', _labels),
    ('TabBar', _tab_bar),
    ('SimpleCardWidget ElevatedCardWidget CardWidget', _cards),
    ('HorizontalSeparator VerticalSeparator', _separator),
    ('PipsPager', _pips),
    ('CommandBar CommandButton', _command_bar),
]:
    for _n in _names.split():
        FACTORIES[_n] = _fn


# ===================================================================
# 自动发现: 基于 __module__ 父模块自动分类，零手动维护
#
# 分类粒度 = components 下的第一级子包:
#   widgets / date_time / dialog_box / navigation / settings / material / layout
# 新增的组件只要放在对应子包下，就会自动出现在对应分类里。
# ===================================================================

# 父模块名 -> (显示名, 图标, 排序权重)
_CATEGORY_DISPLAY = {
    'widgets':    ('Widgets',    FIF.CHECKBOX,  10),
    'date_time':  ('Date Time',  FIF.DATE_TIME, 20),
    'navigation': ('Navigation', FIF.MENU,      30),
    'dialog_box': ('Dialogs',    FIF.MESSAGE,   40),
    'material':   ('Material',   FIF.PALETTE,   50),
    'layout':     ('Layout',     FIF.LAYOUT,    60),
    'settings':   ('Settings',   FIF.SETTING,   70),
}

# 跳过的内部 / 基类组件 (不适合独立预览)
_SKIP_NAMES = {
    'QAbstractItemView', 'QAbstractScrollArea', 'QCheckBox', 'QDateEdit',
    'QDateTimeEdit', 'QDoubleSpinBox', 'QFrame', 'QLabel', 'QLineEdit',
    'QListView', 'QListWidget', 'QMenu', 'QPlainTextEdit', 'QProgressBar',
    'QPushButton', 'QRadioButton', 'QScrollArea', 'QScrollBar', 'QSlider',
    'QSpinBox', 'QStackedWidget', 'QSvgWidget', 'QTableView', 'QTableWidget',
    'QTextBrowser', 'QTextEdit', 'QTimeEdit', 'QToolButton', 'QTreeView',
    'QTreeWidget',
    # 内部辅助组件
    'ArrowButton', 'CompactSpinButton', 'EditLayer', 'Indicator',
    'LineEditButton', 'MenuActionListWidget', 'MoreActionsButton',
    'ScrollBarGroove', 'ScrollBarHandle', 'ScrollButton', 'SliderHandle',
    'SpinButton', 'SplitDropButton', 'PrimarySplitDropButton',
    'StateCloseButton', 'SubMenuItemWidget', 'TabToolButton',
    'FluentLabelBase', 'SplitWidgetBase', 'FluentTitleBarButton',
    'InfoIconWidget', 'DesktopInfoBarView',
    'ComboBoxMenu', 'CompleterMenu', 'EditMenu', 'LabelContextMenu',
    'LineEditMenu', 'TextEditMenu', 'SpinFlyoutView',
    # 弹出式菜单组件 (不适合嵌入布局, 会引发 QPainter 错误)
    'RoundMenu', 'CheckableMenu', 'CheckableSystemTrayMenu',
    'SystemTrayMenu', 'DWMMenu',
    'CommandMenu', 'CommandViewMenu', 'CommandSeparator',
    'CommandBarView', 'CommandViewBar',
    # 窗口级组件 (不适合嵌入预览)
    'FluentWindow', 'MSFluentWindow', 'SplitFluentWindow',
    'FluentWidget', 'FluentWidgetTitleBar', 'FluentTitleBar',
    'MSFluentTitleBar', 'SplitTitleBar', 'SplashScreen',
    # 导航内部组件 (在 FluentWindow 内实例化会与宿主导航冲突导致 segfault)
    'NavigationInterface', 'NavigationPanel', 'NavigationBar',
    'NavigationBarPushButton', 'NavigationPushButton',
    'NavigationToolButton', 'NavigationSeparator',
    'NavigationAvatarWidget', 'NavigationTreeWidget', 'NavigationWidget',
    # 基类
    'MaskDialogBase', 'MessageBoxBase', 'FlyoutViewBase',
    'DatePickerBase', 'PickerBase', 'PickerPanel',
    'NavigationTreeWidgetBase', 'TransitionStackedWidget',
}


@lru_cache(maxsize=1)
def all_widget_classes():
    """收集 qfluentwidgets 中所有 QWidget 子类"""
    result = {}
    for name in dir(qfluentwidgets):
        obj = getattr(qfluentwidgets, name, None)
        if isinstance(obj, type) and issubclass(obj, QWidget) and obj is not QWidget:
            result[name] = obj
    return result


@lru_cache(maxsize=1)
def discover_categories():
    """基于 __module__ 父模块自动发现并分类所有可预览组件

    分组粒度 = qfluentwidgets.components 下的第一级子包。
    新增组件只要放在对应子包下就会自动出现，零手动维护。

    返回: [(display_name, icon, [widget_name, ...]), ...]
    """
    groups = {}  # parent_module -> [widget_name, ...]

    for name, cls in all_widget_classes().items():
        if name in _SKIP_NAMES:
            continue

        mod = cls.__module__
        parts = mod.split('.')

        # 提取 components 下的第一级子包名
        if 'components' in parts:
            idx = parts.index('components')
            parent = parts[idx + 1] if idx + 1 < len(parts) else 'other'
        else:
            continue  # 跳过 window 等非 components 包

        groups.setdefault(parent, []).append(name)

    result = []
    for parent, names in sorted(
        groups.items(),
        key=lambda x: _CATEGORY_DISPLAY.get(x[0], ('', FIF.APPLICATION, 999))[2]
    ):
        display, icon, _ = _CATEGORY_DISPLAY.get(
            parent, (parent.replace('_', ' ').title(), FIF.APPLICATION, 999))
        result.append((display, icon, sorted(names)))

    return result


# 子模块名 -> (显示名, 图标)，用于子分类导航（合并后的键名）
_SUBMODULE_DISPLAY = {
    'button':           ('Basic Input',   FIF.CHECKBOX),
    'combo_box':        ('ComboBox',      FIF.CHECKBOX),
    'slider':           ('Slider',        FIF.CHECKBOX),
    'label':            ('Labels',        FIF.FONT),
    'line_edit':        ('Text Input',    FIF.EDIT),
    'spin_box':         ('SpinBox',       FIF.EDIT),
    'progress_bar':     ('Progress',      FIF.DOWNLOAD),
    'info_badge':       ('Status & Info', FIF.CHAT),
    'teaching_tip':     ('Tips & Flyout', FIF.CHAT),
    'calendar_picker':  ('Date & Time',   FIF.DATE_TIME),
    'menu':             ('Menu',          FIF.MENU),
    'segmented_widget': ('Navigation',    FIF.MENU),
    'card_widget':      ('Layout',        FIF.LAYOUT),
    'list_view':        ('Data View',     FIF.LAYOUT),
    'dialog':           ('Dialogs',       FIF.MESSAGE),
    'setting_card':     ('Settings',      FIF.SETTING),
    'navigation_bar':   ('Nav Components', FIF.MENU),
}

# 子模块排序权重（合并后的键名）
_SUBMODULE_ORDER = [
    'button', 'combo_box', 'slider',
    'label', 'line_edit', 'spin_box',
    'progress_bar', 'info_badge', 'teaching_tip',
    'calendar_picker',
    'menu', 'segmented_widget', 'navigation_bar',
    'card_widget', 'list_view',
    'dialog', 'setting_card',
]
_SUBMODULE_WEIGHT = {name: i for i, name in enumerate(_SUBMODULE_ORDER)}


@lru_cache(maxsize=1)
def discover_subcategories():
    """基于 __module__ 子模块自动分类，合并相关小分组

    返回: [(display_name, icon, [widget_name, ...]), ...]
    """
    groups = {}

    for name, cls in all_widget_classes().items():
        if name in _SKIP_NAMES:
            continue

        mod = cls.__module__
        parts = mod.split('.')
        if 'components' not in parts and 'window' not in parts:
            continue

        submod = parts[-1]
        # 将相关子模块合并
        merged = _MERGE_MAP.get(submod, submod)
        groups.setdefault(merged, []).append(name)

    result = []
    for submod, names in sorted(
        groups.items(),
        key=lambda x: _SUBMODULE_WEIGHT.get(x[0], 999)
    ):
        display, icon = _SUBMODULE_DISPLAY.get(
            submod, (submod.replace('_', ' ').title(), FIF.APPLICATION))
        result.append((display, icon, sorted(names)))

    return result


# 子模块合并映射: 将过小的子模块合并到相关模块
_MERGE_MAP = {
    # 输入控件合并
    'check_box': 'button',
    'switch_button': 'button',
    'model_combo_box': 'combo_box',
    # 进度 & 状态合并
    'progress_ring': 'progress_bar',
    'info_bar': 'info_badge',
    'state_tool_tip': 'info_badge',
    # 提示类合并
    'tool_tip': 'teaching_tip',
    'flyout': 'teaching_tip',
    # 日期时间合并
    'date_picker': 'calendar_picker',
    'time_picker': 'calendar_picker',
    # 导航合并
    'pivot': 'segmented_widget',
    'breadcrumb': 'segmented_widget',
    'tab_view': 'segmented_widget',
    'pips_pager': 'segmented_widget',
    # 命令栏 -> 菜单
    'command_bar': 'menu',
    # 视图合并
    'flip_view': 'list_view',
    'table_view': 'list_view',
    'tree_view': 'list_view',
    # 布局辅助合并
    'separator': 'card_widget',
    'scroll_area': 'card_widget',
    'scroll_bar': 'card_widget',
    'stacked_widget': 'card_widget',
    'cycle_list_widget': 'card_widget',
    # 对话框合并
    'color_dialog': 'dialog',
    'folder_list_dialog': 'dialog',
    'message_dialog': 'dialog',
    'mask_dialog_base': 'dialog',
    'message_box_base': 'dialog',
    # 设置卡片合并
    'expand_setting_card': 'setting_card',
    'custom_color_setting_card': 'setting_card',
    'folder_list_setting_card': 'setting_card',
    'options_setting_card': 'setting_card',
    'setting_card_group': 'setting_card',
    # 导航组件合并
    'navigation_widget': 'navigation_bar',
    'navigation_interface': 'navigation_bar',
    'navigation_panel': 'navigation_bar',
}


def try_instantiate(cls, name, parent):
    """尝试自动实例化组件"""
    for attempt in [
        lambda: cls(parent=parent),
        lambda: cls(name, parent),
    ]:
        try:
            return attempt()
        except Exception:
            pass

    try:
        sig = inspect.signature(cls.__init__)
        params = [p for p in list(sig.parameters.values())[1:]
                  if p.default is inspect.Parameter.empty and p.name not in ('parent', 'args', 'kwargs')]
        kwargs = {'parent': parent}
        for p in params:
            pn = p.name.lower()
            if 'text' in pn or 'title' in pn: kwargs[p.name] = name
            elif 'icon' in pn: kwargs[p.name] = FIF.SETTING
            elif 'orientation' in pn: kwargs[p.name] = Qt.Horizontal
            else: return None
        return cls(**kwargs)
    except Exception:
        return None
