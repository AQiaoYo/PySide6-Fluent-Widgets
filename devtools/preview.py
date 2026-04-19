# coding: utf-8
"""
组件快速预览工具

用法:
    uv run preview                     # 打开全组件浏览器
    uv run preview PushButton          # 预览 PushButton 及其所有变体
    uv run preview PushButton --dark   # 暗色主题预览
    uv run preview --list              # 列出所有可预览组件
    uv run preview push                # 模糊搜索包含 "push" 的组件

写了新组件？只要 qfluentwidgets 导出了就能直接预览。
想要更丰富的演示？在 _factories.py 的 FACTORIES 中加几行即可。
"""
import sys
import argparse
from difflib import get_close_matches

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ._factories import FACTORIES, all_widget_classes


def _fuzzy(query, candidates, n=15):
    q = query.lower()
    hits = [c for c in candidates if q in c.lower()]
    return sorted(hits)[:n] if hits else get_close_matches(query, candidates, n=n, cutoff=0.3)


def main():
    parser = argparse.ArgumentParser(prog='preview',
                                     description='PySide6-Fluent-Widgets 组件快速预览工具')
    parser.add_argument('component', nargs='?', help='组件类名 (如 PushButton)')
    parser.add_argument('--dark', action='store_true', help='暗色主题')
    parser.add_argument('--list', action='store_true', dest='list_all', help='列出所有组件')
    args = parser.parse_args()

    all_names = sorted(all_widget_classes().keys())
    reg = set(FACTORIES.keys())

    # --list: 列出所有组件
    if args.list_all:
        print(f'\n  已注册示例 ({len(reg)} 个):')
        print(f'  {"=" * 40}')
        for n in sorted(reg): print(f'    {n}')
        print(f'\n  所有组件 ({len(all_names)} 个):')
        print(f'  {"=" * 40}')
        for n in all_names: print(f'    {n}{" *" if n in reg else ""}')
        print(f'\n  (* = 有丰富示例)\n')
        return

    # 无参数: 打开全组件浏览器
    if not args.component:
        from qfluentwidgets import setTheme, Theme
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
        if args.dark:
            setTheme(Theme.DARK)

        from ._gallery import GalleryWindow
        w = GalleryWindow(dark=args.dark)
        w.show()
        sys.exit(app.exec())

    # 有参数: 单组件快速预览
    name = args.component
    if name not in all_widget_classes() and name not in reg:
        matches = _fuzzy(name, list(set(all_names) | reg))
        if not matches:
            print(f'\n  找不到 "{name}"，用 --list 查看'); return
        if len(matches) == 1:
            name = matches[0]; print(f'  -> {name}')
        else:
            print(f'\n  "{name}" 匹配到:')
            for i, m in enumerate(matches, 1): print(f'    {i}. {m}{" *" if m in reg else ""}')
            try:
                ch = input('  选择 (回车=1): ').strip()
                name = matches[int(ch) - 1 if ch else 0]
            except (ValueError, IndexError):
                print('  已取消'); return

    from ._single import PreviewWindow
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    w = PreviewWindow(name, dark=args.dark)
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
