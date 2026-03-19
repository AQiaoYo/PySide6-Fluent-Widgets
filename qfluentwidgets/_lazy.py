from __future__ import annotations

import ast
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any


class LazyExportNames:
    def __init__(self, loader):
        self._loader = loader

    def _names(self):
        return list(self._loader().keys())

    def __iter__(self):
        return iter(self._names())

    def __len__(self):
        return len(self._loader())

    def __contains__(self, item):
        return item in self._loader()

    def __getitem__(self, index):
        return self._names()[index]

    def __repr__(self):
        return repr(self._names())


def load_export(module_globals: dict[str, Any], name: str, exports: dict[str, str]) -> Any:
    """Import one exported symbol on first access and memoize it."""
    module_name = exports.get(name)
    if module_name is None:
        raise AttributeError(f"module {module_globals.get('__name__', '<unknown>')!r} has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name, module)
    module_globals[name] = value
    return value


def export_dir(module_globals: dict[str, Any], exports: dict[str, str]) -> list[str]:
    return sorted({*module_globals.keys(), *exports.keys()})


def load_child_module(module_globals: dict[str, Any], name: str) -> Any:
    package_dir = Path(module_globals["__file__"]).resolve().parent
    module_name = f"{module_globals['__name__']}.{name}"
    module_file = package_dir / f"{name}.py"
    package_file = package_dir / name / "__init__.py"
    if not module_file.exists() and not package_file.exists():
        raise AttributeError(f"module {module_globals.get('__name__', '<unknown>')!r} has no attribute {name!r}")

    module = import_module(module_name)
    module_globals[name] = module
    return module


@lru_cache(maxsize=None)
def build_package_exports(package_name: str, package_dir: str, source: str | None = None) -> dict[str, str]:
    return _build_package_exports(package_name, Path(package_dir), set(), source)


def _build_package_exports(
    package_name: str,
    package_dir: Path,
    visited: set[tuple[str, str, str | None]],
    source: str | None = None,
) -> dict[str, str]:
    cache_key = (package_name, str(package_dir), source)
    if cache_key in visited:
        return {}

    visited.add(cache_key)
    exports: dict[str, str] = {}
    init_path = package_dir / "__init__.py"
    if source is None:
        source = _extract_export_spec(init_path)

    source_text = source if source is not None else init_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text, filename=str(init_path))

    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 1 or not node.module:
            continue

        rel_module = node.module
        target_path = package_dir.joinpath(*rel_module.split("."))
        target_module_name = f"{package_name}.{rel_module}"
        module_file = target_path.with_suffix(".py")
        package_file = target_path / "__init__.py"

        # Importing a child module/package also exposes it as a package attribute.
        if module_file.exists() or package_file.exists():
            exports.setdefault(rel_module.split(".")[-1], target_module_name)

        if len(node.names) == 1 and node.names[0].name == "*":
            if package_file.exists():
                exports.update(_build_package_exports(target_module_name, target_path, visited))
            elif module_file.exists():
                for name in _public_names_from_module(module_file):
                    exports.setdefault(name, target_module_name)
            continue

        for alias in node.names:
            import_name = alias.asname or alias.name
            child_module_file = target_path / f"{alias.name}.py"
            child_package_file = target_path / alias.name / "__init__.py"
            if package_file.exists() and (child_module_file.exists() or child_package_file.exists()):
                exports[import_name] = f"{target_module_name}.{alias.name}"
            else:
                exports[import_name] = target_module_name

    return exports


@lru_cache(maxsize=None)
def _public_names_from_module(module_file: Path) -> tuple[str, ...]:
    tree = ast.parse(module_file.read_text(encoding="utf-8"), filename=str(module_file))
    explicit_all = _extract_explicit_all(tree)
    if explicit_all is not None:
        return tuple(name for name in explicit_all if not name.startswith("_"))

    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                import_name = alias.asname or alias.name.split(".")[0]
                if not import_name.startswith("_"):
                    names.append(import_name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                import_name = alias.asname or alias.name
                if not import_name.startswith("_"):
                    names.append(import_name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names.extend(_assignment_names(target))
        elif isinstance(node, ast.AnnAssign):
            names.extend(_assignment_names(node.target))

    return tuple(dict.fromkeys(name for name in names if not name.startswith("_")))


def _extract_explicit_all(tree: ast.Module) -> list[str] | None:
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            continue

        try:
            value = ast.literal_eval(node.value)
        except Exception:
            return None

        if isinstance(value, (list, tuple)):
            return [item for item in value if isinstance(item, str)]

    return None


@lru_cache(maxsize=None)
def _extract_export_spec(init_file: Path) -> str | None:
    tree = ast.parse(init_file.read_text(encoding="utf-8"), filename=str(init_file))
    return _extract_string_assignment(tree, "_EXPORT_SPEC")


def _extract_string_assignment(tree: ast.Module, name: str) -> str | None:
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue

        try:
            value = ast.literal_eval(node.value)
        except Exception:
            return None

        return value if isinstance(value, str) else None

    return None


def _assignment_names(target: ast.expr) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]

    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            names.extend(_assignment_names(element))
        return names

    return []
