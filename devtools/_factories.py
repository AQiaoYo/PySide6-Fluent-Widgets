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
    from qfluentwidgets import ComboBox, EditableComboBox, ModelComboBox, EditableModelComboBox
    from PySide6.QtGui import QStandardItemModel, QStandardItem
    c = ComboBox(p); c.addItems(['Option 1', 'Option 2', 'Option 3']); c.setMinimumWidth(200)
    e = EditableComboBox(p); e.addItems(['Star Platinum', 'Crazy Diamond', 'Gold Experience'])
    e.setPlaceholderText('Choose...'); e.setMinimumWidth(200)

    # ModelComboBox
    mc = ModelComboBox(p); mc.setMinimumWidth(200)
    model1 = QStandardItemModel(mc)
    for text in ['Spring', 'Summer', 'Autumn', 'Winter']:
        model1.appendRow(QStandardItem(text))
    mc.setModel(model1); mc.setCurrentIndex(0)

    # EditableModelComboBox
    emc = EditableModelComboBox(p); emc.setMinimumWidth(200)
    model2 = QStandardItemModel(emc)
    for text in ['January', 'February', 'March', 'April']:
        model2.appendRow(QStandardItem(text))
    emc.setModel(model2); emc.setPlaceholderText('Type to search...')

    return [
        (c, 'ComboBox - 下拉框'), (e, 'EditableComboBox - 可编辑下拉框'),
        (mc, 'ModelComboBox - 模型下拉框'), (emc, 'EditableModelComboBox - 可编辑模型下拉框'),
    ]


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
    tb.setTabShadowEnabled(False)
    tb.addTab('t1', 'Tab 1', FIF.HOME); tb.addTab('t2', 'Tab 2', FIF.DOCUMENT)
    tb.addTab('t3', 'Tab 3', FIF.SETTING); tb.setMinimumWidth(400)
    # 彻底移除 TabItem 的 QGraphicsDropShadowEffect 并用 Python dummy 替换 shadowEffect 属性，
    # 既避免 paintEvent 冲突，又防止 setSelected/setShadowEnabled 访问已删除的 C++ 对象
    class _NoOpShadow:
        def setColor(self, *a, **k): pass
        def setBlurRadius(self, *a, **k): pass
        def setOffset(self, *a, **k): pass
    for item in tb.items:
        item.setGraphicsEffect(None)
        item.shadowEffect = _NoOpShadow()
    return [(tb, 'TabBar')]


def _cards(p):
    from qfluentwidgets import SimpleCardWidget, CardWidget, ElevatedCardWidget
    items = []
    for cls, name in [(SimpleCardWidget, 'SimpleCardWidget'),
                      (CardWidget, 'CardWidget'),
                      (ElevatedCardWidget, 'ElevatedCardWidget')]:
        c = cls(p); c.setFixedSize(200, 120)
        QVBoxLayout(c).addWidget(BodyLabel(name, c))
        # ElevatedCardWidget 的 DropShadowAnimation 在 hover 时设置 QGraphicsDropShadowEffect，
        # 与其自定义 paintEvent 冲突导致 QPainter 错误，禁用它
        if isinstance(c, ElevatedCardWidget):
            c.setGraphicsEffect(None)
            if hasattr(c, 'shadowAni') and c.shadowAni:
                c.shadowAni.setParent(None)
                c.shadowAni = None
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

    btn = CommandButton(FIF.SHARE, p)
    btn.setText('Share')
    btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    return [
        (bar, 'CommandBar - 命令栏'),
        (btn, 'CommandButton - 命令按钮'),
    ]


def _dropdown_tool_buttons(p):
    from qfluentwidgets import (DropDownToolButton, PrimaryDropDownToolButton,
                                TransparentDropDownToolButton,
                                SplitToolButton, PrimarySplitToolButton,
                                RoundMenu, Action)
    def m():
        menu = RoundMenu(parent=p)
        menu.addAction(Action(FIF.SEND, 'Send'))
        menu.addAction(Action(FIF.SAVE, 'Save'))
        return menu
    b1 = DropDownToolButton(FIF.MAIL, p); b1.setMenu(m())
    b2 = PrimaryDropDownToolButton(FIF.MAIL, p); b2.setMenu(m())
    b3 = TransparentDropDownToolButton(FIF.MAIL, p); b3.setMenu(m())
    b4 = SplitToolButton(FIF.BASKETBALL, p); b4.setFlyout(m())
    b5 = PrimarySplitToolButton(FIF.BASKETBALL, p); b5.setFlyout(m())
    return [
        (b1, 'DropDownToolButton'), (b2, 'PrimaryDropDownToolButton'),
        (b3, 'TransparentDropDownToolButton'),
        (b4, 'SplitToolButton'), (b5, 'PrimarySplitToolButton'),
    ]


def _display_widgets(p):
    from PySide6.QtGui import QPixmap, QColor as QC
    from qfluentwidgets import AvatarWidget, IconWidget, HyperlinkLabel, ImageLabel, PixmapLabel
    # AvatarWidget 无图像时展示文字头像
    av = AvatarWidget(p); av.setText('Q'); av.setRadius(32)
    # IconWidget
    iw = IconWidget(FIF.EMOJI_TAB_SYMBOLS, p); iw.setFixedSize(36, 36)
    # HyperlinkLabel
    hl = HyperlinkLabel('Fluent Widgets', p); hl.setUrl('')
    # ImageLabel - 渐变色 demo 图
    px1 = QPixmap(160, 100)
    px1.fill(QC('#0078d4'))
    il = ImageLabel(px1, p); il.setBorderRadius(8, 8, 8, 8)
    # PixmapLabel
    px2 = QPixmap(160, 100)
    px2.fill(QC('#48cae4'))
    pl = PixmapLabel(p); pl.setPixmap(px2)
    return [
        (av, 'AvatarWidget - 文字头像'),
        (iw, 'IconWidget - 图标'),
        (hl, 'HyperlinkLabel - 超链接标签'),
        (il, 'ImageLabel - 图像标签'),
        (pl, 'PixmapLabel - 高清位图标签'),
    ]


def _info_bar(p):
    from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition
    items = []
    for icon, title, style in [
        (InfoBarIcon.INFORMATION, 'Info', 'information'),
        (InfoBarIcon.SUCCESS, 'Success', 'success'),
        (InfoBarIcon.WARNING, 'Warning', 'warning'),
        (InfoBarIcon.ERROR, 'Error', 'error'),
    ]:
        bar = InfoBar(icon, title, f'This is a {style} message.',
                      orient=Qt.Horizontal, isClosable=True, duration=-1,
                      position=InfoBarPosition.NONE, parent=p)
        bar.setMinimumWidth(350)
        # 移除 opacityEffect 避免与父容器 paintEvent 冲突
        bar.setGraphicsEffect(None)
        items.append((bar, f'InfoBar - {title}'))
    return items


def _info_badge_extended(p):
    from PySide6.QtWidgets import QHBoxLayout
    from qfluentwidgets import InfoBadge, DotInfoBadge, IconInfoBadge
    # 横排容器，避免单个徽标太窄
    w = QWidget(p)
    lo = QHBoxLayout(w); lo.setContentsMargins(0, 0, 0, 0); lo.setSpacing(16)
    badges = [
        InfoBadge.info(1, w), InfoBadge.success(10, w),
        InfoBadge.warning(100, w), InfoBadge.error(99, w),
        DotInfoBadge(w), IconInfoBadge(FIF.ACCEPT, w),
    ]
    for b in badges:
        lo.addWidget(b)
    lo.addStretch()
    return [(w, 'InfoBadge / DotInfoBadge / IconInfoBadge - 徽标系列')]


def _state_tool_tip(p):
    from qfluentwidgets import StateToolTip
    st = StateToolTip('Loading', 'Please wait...', p)
    st.setFixedSize(280, 64)
    st.move(0, 0)
    # 移除 opacityEffect 避免 paintEvent 冲突（StateToolTip 有自定义 paintEvent）
    st.setGraphicsEffect(None)
    return [(st, 'StateToolTip - 状态工具提示')]


def _flyout_views(p):
    from qfluentwidgets import FlyoutView, TeachingTipView
    fv = FlyoutView('Flyout Title', 'This is flyout content.\nSupports multi-line.', FIF.INFO)
    tv = TeachingTipView('Teaching Tip', 'Helpful tip content goes here.', FIF.INFO, isClosable=True)
    return [
        (fv, 'FlyoutView - 浮出层视图'),
        (tv, 'TeachingTipView - 教学提示视图'),
    ]


def _setting_cards(p):
    from qfluentwidgets import (SettingCard, SwitchSettingCard, PushSettingCard,
                                PrimaryPushSettingCard, HyperlinkCard)
    sc = SettingCard(FIF.SETTING, 'General Settings', 'Configure your preferences', p)
    sw = SwitchSettingCard(FIF.UPDATE, 'Auto Update', 'Check for updates automatically', parent=p)
    ps = PushSettingCard('Choose', FIF.FOLDER, 'Download Directory', 'D:/Downloads', p)
    pp = PrimaryPushSettingCard('Action', FIF.DEVELOPER_TOOLS, 'Developer Options', 'Advanced settings', p)
    hc = HyperlinkCard('', 'Open', FIF.LINK, 'Project Homepage', 'Visit the project website', p)
    return [
        (sc, 'SettingCard - 基础设置卡片'),
        (sw, 'SwitchSettingCard - 开关设置卡片'),
        (ps, 'PushSettingCard - 按钮设置卡片'),
        (pp, 'PrimaryPushSettingCard - 主题色按钮设置卡片'),
        (hc, 'HyperlinkCard - 超链接设置卡片'),
    ]


def _setting_cards_config(p):
    from qfluentwidgets import (ColorSettingCard, ComboBoxSettingCard, RangeSettingCard,
                                OptionsSettingCard, FolderListSettingCard, CustomColorSettingCard)
    from qfluentwidgets.common.config import (RangeConfigItem, ColorConfigItem,
                                               OptionsConfigItem, ConfigItem,
                                               RangeValidator, OptionsValidator,
                                               FolderListValidator)
    # RangeSettingCard
    range_cfg = RangeConfigItem('demo', 'range', 50, RangeValidator(0, 100))
    rc = RangeSettingCard(range_cfg, FIF.VOLUME, 'Volume', 'Adjust system volume', p)
    rc.setMinimumWidth(400)

    # ColorSettingCard
    color_cfg = ColorConfigItem('demo', 'themeColor', '#0078d4')
    cc = ColorSettingCard(color_cfg, FIF.PALETTE, 'Theme Color', 'Choose application theme color', p)
    cc.setMinimumWidth(400)

    # ComboBoxSettingCard
    combo_cfg = OptionsConfigItem('demo', 'resolution', '1080p',
                                  OptionsValidator(['720p', '1080p', '1440p', '4K']))
    cbc = ComboBoxSettingCard(combo_cfg, FIF.FULL_SCREEN, 'Resolution',
                              'Set display resolution', texts=['720p', '1080p', '1440p', '4K'], parent=p)
    cbc.setMinimumWidth(400)

    # OptionsSettingCard
    opt_cfg = OptionsConfigItem('demo', 'language', 'English',
                                OptionsValidator(['English', 'Chinese', 'Japanese']))
    oc = OptionsSettingCard(opt_cfg, FIF.LANGUAGE, 'Language',
                            'Select interface language',
                            texts=['English', 'Chinese', 'Japanese'], parent=p)
    oc.setMinimumWidth(400)

    # FolderListSettingCard
    folder_cfg = ConfigItem('demo', 'folders', [], FolderListValidator())
    flc = FolderListSettingCard(folder_cfg, 'Download Folders', 'Manage download directories', parent=p)
    flc.setMinimumWidth(400)

    # CustomColorSettingCard
    custom_color_cfg = ColorConfigItem('demo', 'accentColor', '#ff4444')
    ccc = CustomColorSettingCard(custom_color_cfg, FIF.PALETTE, 'Accent Color',
                                 'Pick a custom accent color', p)
    ccc.setMinimumWidth(400)

    return [
        (rc, 'RangeSettingCard - 范围设置卡片'),
        (cc, 'ColorSettingCard - 颜色设置卡片'),
        (cbc, 'ComboBoxSettingCard - 组合框设置卡片'),
        (oc, 'OptionsSettingCard - 选项设置卡片'),
        (flc, 'FolderListSettingCard - 文件夹列表设置卡片'),
        (ccc, 'CustomColorSettingCard - 自定义颜色设置卡片'),
    ]


def _expand_setting_cards(p):
    from qfluentwidgets import (ExpandSettingCard, ExpandGroupSettingCard,
                                SimpleExpandGroupSettingCard, SettingCard)
    ec = ExpandSettingCard(FIF.SCROLL, 'Expand Card', 'Click to expand for more options', p)
    inner1 = SettingCard(FIF.WIFI, 'WiFi', 'Connected', ec)
    inner2 = SettingCard(FIF.BLUETOOTH, 'Bluetooth', 'On', ec)
    ec.addWidget(inner1)
    ec.addWidget(inner2)

    eg = ExpandGroupSettingCard(FIF.SCROLL, 'Group Card', 'Grouped options', p)
    gi1 = SettingCard(FIF.FONT, 'Font', 'Segoe UI', eg)
    gi2 = SettingCard(FIF.FONT_SIZE, 'Font Size', '14px', eg)
    eg.addGroupWidget(gi1)
    eg.addGroupWidget(gi2)

    seg = SimpleExpandGroupSettingCard(FIF.SCROLL, 'Simple Group', 'Simple grouped options', p)
    sgi1 = SettingCard(FIF.LANGUAGE, 'Language', 'English', seg)
    sgi2 = SettingCard(FIF.UPDATE, 'Updates', 'Auto', seg)
    seg.addGroupWidget(sgi1)
    seg.addGroupWidget(sgi2)

    return [
        (ec, 'ExpandSettingCard - 可展开设置卡片'),
        (eg, 'ExpandGroupSettingCard - 可展开分组设置卡片'),
        (seg, 'SimpleExpandGroupSettingCard - 简易可展开分组设置卡片'),
    ]


def _color_picker(p):
    from PySide6.QtGui import QColor as QC
    from qfluentwidgets import ColorPickerButton
    cp1 = ColorPickerButton(QC('#0078d4'), 'Theme Color', p)
    cp2 = ColorPickerButton(QC('#ff4444'), 'Accent Color', p)
    return [
        (cp1, 'ColorPickerButton - 主题色'),
        (cp2, 'ColorPickerButton - 强调色'),
    ]


def _data_views(p):
    from PySide6.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QHeaderView
    from PySide6.QtGui import QStandardItemModel, QStandardItem
    from qfluentwidgets import (ListWidget, TableWidget, TreeWidget,
                                ListView, TableView, TreeView)

    # ListWidget
    lw = ListWidget(p)
    for text in ['Apple', 'Banana', 'Cherry', 'Durian', 'Elderberry']:
        lw.addItem(text)
    lw.setFixedHeight(180)
    lw.setMinimumWidth(250)

    # ListView (Model-based)
    lv = ListView(p)
    lv_model = QStandardItemModel(lv)
    for text in ['January', 'February', 'March', 'April', 'May']:
        lv_model.appendRow(QStandardItem(text))
    lv.setModel(lv_model)
    lv.setFixedHeight(180)
    lv.setMinimumWidth(250)

    # TableWidget
    tw = TableWidget(p)
    tw.setColumnCount(3)
    tw.setRowCount(4)
    tw.setHorizontalHeaderLabels(['Name', 'Age', 'City'])
    data = [('Alice', '25', 'Beijing'), ('Bob', '30', 'Shanghai'),
            ('Carol', '28', 'Shenzhen'), ('Dave', '35', 'Hangzhou')]
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            tw.setItem(r, c, QTableWidgetItem(val))
    tw.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tw.setFixedHeight(200)
    tw.setMinimumWidth(350)

    # TableView (Model-based)
    tv = TableView(p)
    tv_model = QStandardItemModel(4, 3, tv)
    tv_model.setHorizontalHeaderLabels(['Product', 'Price', 'Stock'])
    tv_data = [('Widget A', '$10', '50'), ('Widget B', '$25', '30'),
               ('Widget C', '$15', '80'), ('Widget D', '$40', '12')]
    for r, row in enumerate(tv_data):
        for c, val in enumerate(row):
            tv_model.setItem(r, c, QStandardItem(val))
    tv.setModel(tv_model)
    tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tv.setFixedHeight(200)
    tv.setMinimumWidth(350)

    # TreeWidget
    trw = TreeWidget(p)
    trw.setColumnCount(1)
    trw.setHeaderLabels(['File Browser'])
    root1 = QTreeWidgetItem(trw, ['Documents'])
    QTreeWidgetItem(root1, ['report.pdf'])
    QTreeWidgetItem(root1, ['notes.txt'])
    root2 = QTreeWidgetItem(trw, ['Pictures'])
    QTreeWidgetItem(root2, ['photo.jpg'])
    root1.setExpanded(True)
    trw.setFixedHeight(200)
    trw.setMinimumWidth(250)

    # TreeView (Model-based)
    from PySide6.QtWidgets import QFileSystemModel
    trv = TreeView(p)
    fs_model = QStandardItemModel(trv)
    fs_model.setHorizontalHeaderLabels(['Folder Structure'])
    root_item = fs_model.invisibleRootItem()
    src = QStandardItem('src'); src.setEditable(False)
    src.appendRow(QStandardItem('main.py'))
    src.appendRow(QStandardItem('utils.py'))
    tests = QStandardItem('tests'); tests.setEditable(False)
    tests.appendRow(QStandardItem('test_main.py'))
    root_item.appendRows([src, tests, QStandardItem('README.md')])
    trv.setModel(fs_model)
    trv.expandAll()
    trv.setFixedHeight(200)
    trv.setMinimumWidth(250)

    return [
        (lw, 'ListWidget - 列表 (Item-based)'),
        (lv, 'ListView - 列表 (Model-based)'),
        (tw, 'TableWidget - 表格 (Item-based)'),
        (tv, 'TableView - 表格 (Model-based)'),
        (trw, 'TreeWidget - 树形 (Item-based)'),
        (trv, 'TreeView - 树形 (Model-based)'),
    ]


def _flip_view(p):
    from PySide6.QtGui import QColor as QC, QPixmap
    from qfluentwidgets import FlipView, HorizontalFlipView, VerticalFlipView
    fv = FlipView(Qt.Horizontal, p)
    colors = ['#0078d4', '#00b4d8', '#48cae4', '#90e0ef']
    for c in colors:
        px = QPixmap(160, 120)
        px.fill(QC(c))
        fv.addImage(px)
    fv.setFixedSize(200, 140)

    hfv = HorizontalFlipView(p)
    for c in colors:
        px = QPixmap(160, 120)
        px.fill(QC(c))
        hfv.addImage(px)
    hfv.setFixedSize(200, 140)

    vfv = VerticalFlipView(p)
    for c in ['#ff6b6b', '#ffa07a', '#ffd93d', '#6bcb77']:
        px = QPixmap(160, 100)
        px.fill(QC(c))
        vfv.addImage(px)
    vfv.setFixedSize(180, 130)

    return [
        (fv, 'FlipView - 翻转视图'),
        (hfv, 'HorizontalFlipView - 水平翻转视图'),
        (vfv, 'VerticalFlipView - 垂直翻转视图'),
    ]


def _advanced_cards(p):
    from qfluentwidgets import (HeaderCardWidget, GroupHeaderCardWidget,
                                CardGroupWidget, CardSeparator)
    # HeaderCardWidget
    hc = HeaderCardWidget(p)
    hc.setTitle('Header Card')
    hc.headerLayout.addWidget(BodyLabel('Header content goes here', hc))
    hc.viewLayout.addWidget(BodyLabel('Body content area', hc))
    hc.setMinimumWidth(300)
    hc.setFixedHeight(160)

    # GroupHeaderCardWidget
    ghc = GroupHeaderCardWidget(p)
    ghc.setTitle('Group Header Card')
    ghc.headerLayout.addWidget(BodyLabel('Group header content', ghc))
    inner_w = BodyLabel('Group body widget', ghc)
    ghc.addGroup(FIF.FOLDER, 'Documents', 'Manage your files', inner_w)
    ghc.setMinimumWidth(300)
    ghc.setFixedHeight(200)

    # CardGroupWidget
    cg = CardGroupWidget(FIF.PEOPLE, 'Team', 'Group of settings', p)
    cg.setMinimumWidth(300)
    cg.setFixedHeight(80)

    # CardSeparator
    cs = CardSeparator(p)
    cs.setMinimumWidth(200)

    return [
        (hc, 'HeaderCardWidget - 头部卡片'),
        (ghc, 'GroupHeaderCardWidget - 分组头部卡片'),
        (cg, 'CardGroupWidget - 卡片分组'),
        (cs, 'CardSeparator - 卡片分隔线'),
    ]


def _segmented_tool(p):
    from qfluentwidgets import SegmentedToolWidget, SegmentedToggleToolWidget
    stw = SegmentedToolWidget(p)
    for k, ico in [('s1', FIF.HOME), ('s2', FIF.DOCUMENT), ('s3', FIF.SETTING)]:
        stw.addItem(k, ico)
    stw.setCurrentItem('s1')

    sttw = SegmentedToggleToolWidget(p)
    for k, ico in [('t1', FIF.CALENDAR), ('t2', FIF.BOOK_SHELF), ('t3', FIF.PEOPLE)]:
        sttw.addItem(k, ico)
    sttw.setCurrentItem('t1')

    return [
        (stw, 'SegmentedToolWidget - 分段工具'),
        (sttw, 'SegmentedToggleToolWidget - 分段切换工具'),
    ]


def _tab_widget(p):
    from qfluentwidgets import TabWidget
    tw = TabWidget(p)
    tw.tabBar.setTabShadowEnabled(False)
    for text, icon in [('Home', FIF.HOME), ('Files', FIF.DOCUMENT), ('Settings', FIF.SETTING)]:
        page = QWidget()
        QVBoxLayout(page).addWidget(BodyLabel(f'{text} Page Content', page))
        tw.addTab(page, text, icon)
    # 彻底移除 TabItem 的 QGraphicsDropShadowEffect 并用 Python dummy 替换 shadowEffect 属性
    class _NoOpShadow:
        def setColor(self, *a, **k): pass
        def setBlurRadius(self, *a, **k): pass
        def setOffset(self, *a, **k): pass
    for item in tw.tabBar.items:
        item.setGraphicsEffect(None)
        item.shadowEffect = _NoOpShadow()
    tw.setMinimumWidth(400)
    tw.setFixedHeight(200)
    return [(tw, 'TabWidget - 标签页组件')]


def _text_edit_extended(p):
    from qfluentwidgets import (LineEdit, SearchLineEdit, PasswordLineEdit,
                                TextEdit, PlainTextEdit, TextBrowser)
    le = LineEdit(p); le.setPlaceholderText('LineEdit'); le.setMinimumWidth(250)
    s = SearchLineEdit(p); s.setPlaceholderText('Search...'); s.setMinimumWidth(250)
    pw = PasswordLineEdit(p); pw.setPlaceholderText('Password'); pw.setMinimumWidth(250)
    te = TextEdit(p); te.setPlaceholderText('TextEdit...'); te.setMinimumWidth(250); te.setMaximumHeight(100)
    pte = PlainTextEdit(p); pte.setPlaceholderText('PlainTextEdit...'); pte.setMinimumWidth(250); pte.setMaximumHeight(100)
    tb = TextBrowser(p); tb.setText('Rich text <b>browser</b> content.\n<i>Supports HTML.</i>'); tb.setMinimumWidth(250); tb.setMaximumHeight(100)
    return [
        (le, 'LineEdit'), (s, 'SearchLineEdit'), (pw, 'PasswordLineEdit'),
        (te, 'TextEdit'), (pte, 'PlainTextEdit - 纯文本编辑'),
        (tb, 'TextBrowser - 富文本浏览器'),
    ]


def _date_time_edit(p):
    from qfluentwidgets import (DateEdit, TimeEdit, DateTimeEdit,
                                CompactDateEdit, CompactTimeEdit, CompactDateTimeEdit)
    return [
        (DateEdit(p), 'DateEdit'),
        (TimeEdit(p), 'TimeEdit'),
        (DateTimeEdit(p), 'DateTimeEdit'),
        (CompactDateEdit(p), 'CompactDateEdit'),
        (CompactTimeEdit(p), 'CompactTimeEdit'),
        (CompactDateTimeEdit(p), 'CompactDateTimeEdit'),
    ]


def _pips_extended(p):
    from qfluentwidgets import PipsPager, HorizontalPipsPager, VerticalPipsPager
    pp = PipsPager(Qt.Horizontal, p); pp.setPageNumber(5); pp.setVisibleNumber(5)
    hp = HorizontalPipsPager(p); hp.setPageNumber(5); hp.setVisibleNumber(5)
    vp = VerticalPipsPager(p); vp.setPageNumber(5); vp.setVisibleNumber(5)
    return [
        (pp, 'PipsPager'),
        (hp, 'HorizontalPipsPager'),
        (vp, 'VerticalPipsPager'),
    ]


def _scroll_bar(p):
    from qfluentwidgets import ScrollBar, SmoothScrollBar, ScrollArea
    # ScrollBar 需要 QAbstractScrollArea 作为 parent
    sa1 = ScrollArea(p)
    sa1.setFixedSize(250, 150)
    inner1 = QWidget()
    inner1.setFixedHeight(500)
    sa1.setWidget(inner1)
    sa1.setWidgetResizable(False)
    sb = ScrollBar(Qt.Vertical, sa1)

    sa2 = ScrollArea(p)
    sa2.setFixedSize(250, 150)
    inner2 = QWidget()
    inner2.setFixedHeight(500)
    sa2.setWidget(inner2)
    sa2.setWidgetResizable(False)
    ssb = SmoothScrollBar(Qt.Vertical, sa2)

    return [
        (sa1, 'ScrollBar - 滚动条 (in ScrollArea)'),
        (sa2, 'SmoothScrollBar - 平滑滚动条 (in ScrollArea)'),
    ]


def _scroll_areas(p):
    from qfluentwidgets import ScrollArea, SmoothScrollArea, SingleDirectionScrollArea
    items = []
    for cls, name in [(ScrollArea, 'ScrollArea'),
                      (SmoothScrollArea, 'SmoothScrollArea'),
                      (SingleDirectionScrollArea, 'SingleDirectionScrollArea')]:
        try:
            sa = cls(p)
        except TypeError:
            sa = cls(p, orient=Qt.Vertical)
        sa.setFixedSize(280, 150)
        sa.setWidgetResizable(True)
        content = QWidget()
        lo = QVBoxLayout(content)
        lo.setSpacing(8)
        for i in range(12):
            lo.addWidget(BodyLabel(f'  Item {i+1} in {name}', content))
        sa.setWidget(content)
        items.append((sa, f'{name} - 滚动区域'))
    return items


def _slider_extended(p):
    from qfluentwidgets import Slider, ClickableSlider
    h = Slider(Qt.Horizontal, p); h.setRange(0, 100); h.setValue(40); h.setMinimumWidth(250)
    v = Slider(Qt.Vertical, p); v.setRange(0, 100); v.setValue(60); v.setMinimumHeight(120)
    ch = ClickableSlider(Qt.Horizontal, p); ch.setRange(0, 100); ch.setValue(70); ch.setMinimumWidth(250)
    return [
        (h, 'Slider - 水平'), (v, 'Slider - 垂直'),
        (ch, 'ClickableSlider - 可点击滑块'),
    ]


def _setting_card_group(p):
    from qfluentwidgets import SettingCardGroup, SettingCard
    sg = SettingCardGroup('General', p)
    sg.addSettingCard(SettingCard(FIF.LANGUAGE, 'Language', 'English', sg))
    sg.addSettingCard(SettingCard(FIF.FONT, 'Font', 'Segoe UI', sg))
    sg.addSettingCard(SettingCard(FIF.UPDATE, 'Update', 'Auto-check enabled', sg))
    sg.setMinimumWidth(400)
    return [(sg, 'SettingCardGroup - 设置卡片组')]


# ===================================================================
# 注册表: 组件名 -> 工厂函数
#
# 只有需要特殊参数 / 多变体展示的组件才需要注册。
# 新增的组件如果 try_instantiate 能搞定，就不用加。
# ===================================================================

FACTORIES = {}
for _names, _fn in [
    # 按钮系列
    ('PushButton PrimaryPushButton TransparentPushButton ToggleButton '
     'TogglePushButton HyperlinkButton PillPushButton TransparentTogglePushButton', _buttons),
    ('ToolButton PrimaryToolButton TransparentToolButton '
     'ToggleToolButton TransparentToggleToolButton PillToolButton', _tool_buttons),
    ('DropDownPushButton PrimaryDropDownPushButton TransparentDropDownPushButton '
     'SplitPushButton PrimarySplitPushButton', _dropdown_buttons),
    ('DropDownToolButton PrimaryDropDownToolButton TransparentDropDownToolButton '
     'SplitToolButton PrimarySplitToolButton', _dropdown_tool_buttons),
    ('CheckBox', _checkbox),
    ('RadioButton', _radio),
    ('SwitchButton', _switch),
    # 输入控件
    ('ComboBox EditableComboBox ModelComboBox EditableModelComboBox', _combo),
    ('LineEdit SearchLineEdit PasswordLineEdit TextEdit PlainTextEdit TextBrowser', _text_edit_extended),
    ('Slider ClickableSlider', _slider_extended),
    ('SpinBox DoubleSpinBox CompactSpinBox CompactDoubleSpinBox', _spin),
    # 进度 & 状态
    ('ProgressBar IndeterminateProgressBar', _progress_bar),
    ('ProgressRing IndeterminateProgressRing', _progress_ring),
    ('InfoBadge DotInfoBadge IconInfoBadge', _info_badge_extended),
    ('InfoBar', _info_bar),
    ('StateToolTip', _state_tool_tip),
    # 浮出层 & 提示
    ('FlyoutView TeachingTipView', _flyout_views),
    # 日期时间
    ('CalendarPicker FastCalendarPicker', _calendar),
    ('DatePicker ZhDatePicker', _date_picker),
    ('TimePicker AMTimePicker', _time_picker),
    ('DateEdit TimeEdit DateTimeEdit CompactDateEdit CompactTimeEdit CompactDateTimeEdit', _date_time_edit),
    # 导航
    ('Pivot', _pivot),
    ('SegmentedWidget', _segmented),
    ('SegmentedToolWidget SegmentedToggleToolWidget', _segmented_tool),
    ('BreadcrumbBar', _breadcrumb),
    ('PipsPager HorizontalPipsPager VerticalPipsPager', _pips_extended),
    ('TabBar', _tab_bar),
    ('TabWidget', _tab_widget),
    # 标签 & 显示
    ('CaptionLabel BodyLabel StrongBodyLabel SubtitleLabel TitleLabel LargeTitleLabel DisplayLabel', _labels),
    ('AvatarWidget IconWidget HyperlinkLabel ImageLabel PixmapLabel', _display_widgets),
    # 卡片 & 布局
    ('SimpleCardWidget CardWidget ElevatedCardWidget', _cards),
    ('HeaderCardWidget GroupHeaderCardWidget CardGroupWidget CardSeparator', _advanced_cards),
    ('HorizontalSeparator VerticalSeparator', _separator),
    ('CommandBar CommandButton', _command_bar),
    # 设置卡片
    ('SettingCard SwitchSettingCard PushSettingCard PrimaryPushSettingCard HyperlinkCard', _setting_cards),
    ('ColorSettingCard ComboBoxSettingCard RangeSettingCard OptionsSettingCard FolderListSettingCard CustomColorSettingCard', _setting_cards_config),
    ('ExpandSettingCard ExpandGroupSettingCard SimpleExpandGroupSettingCard', _expand_setting_cards),
    ('ColorPickerButton', _color_picker),
    ('SettingCardGroup', _setting_card_group),
    # 数据视图
    ('ListWidget ListView TableWidget TableView TreeWidget TreeView', _data_views),
    ('FlipView HorizontalFlipView VerticalFlipView', _flip_view),
    # 滚动条
    ('ScrollBar SmoothScrollBar', _scroll_bar),
    # 滚动区域
    ('ScrollArea SmoothScrollArea SingleDirectionScrollArea', _scroll_areas),
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
    # (原 ElevatedCardWidget 已恢复 — QFrame 容器无 QPainter 冲突)
    # 导航内部组件 (在 FluentWindow 内实例化会与宿主导航冲突导致 segfault)
    'NavigationInterface', 'NavigationPanel', 'NavigationBar',
    'NavigationBarPushButton', 'NavigationPushButton',
    'NavigationToolButton', 'NavigationSeparator',
    'NavigationAvatarWidget', 'NavigationTreeWidget', 'NavigationWidget',
    # 基类
    'MaskDialogBase', 'MessageBoxBase', 'FlyoutViewBase',
    'DatePickerBase', 'PickerBase', 'PickerPanel',
    'NavigationTreeWidgetBase', 'TransitionStackedWidget',
    # 弹出式对话框 (需要模态显示, 不适合嵌入预览)
    'Dialog', 'MessageBox', 'MessageDialog', 'FolderListDialog', 'ColorDialog',
    # 过渡动画堆叠组件 (空壳, 嵌入预览无意义)
    'DrillInTransitionStackedWidget', 'EntranceTransitionStackedWidget',
    'OpacityAniStackedWidget', 'PopUpAniStackedWidget',
    # 内部子项组件 (不适合独立预览)
    'PivotItem', 'SegmentedItem', 'SegmentedToolItem',
    'SegmentedToggleToolItem', 'TabItem', 'BreadcrumbItem',
    'ItemViewToolTip', 'TeachTipBubble',
    # 弹出式浮动组件 (需锚定到目标, 不适合嵌入布局)
    'ToolTip', 'Flyout', 'TeachingTip', 'PopupTeachingTip',
    # 通过容器组件预览的滚动区域
    'CycleListWidget',
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
