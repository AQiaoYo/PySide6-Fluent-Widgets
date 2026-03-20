#!/usr/bin/env python
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

TARGETS = (
    (
        ROOT / "pyproject.toml",
        re.compile(
            r'(?m)^(?P<prefix>version = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")$'
        ),
    ),
    (
        ROOT / "qfluentwidgets" / "_version.py",
        re.compile(
            r'(?m)^(?P<prefix>__version__ = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")$'
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync project version files. Defaults to bumping the patch number."
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Set an explicit version, for example: 2.1.0",
    )
    parser.add_argument(
        "--part",
        choices=("patch", "minor", "major"),
        default="patch",
        help="When no explicit version is provided, choose which segment to bump.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the target version without writing files.",
    )
    parser.add_argument(
        "--no-lock",
        action="store_true",
        help="Skip running `uv lock` after updating version files.",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create a git tag named `v<version>` after the version update.",
    )
    parser.add_argument(
        "--push-tag",
        action="store_true",
        help="Push the created tag to `origin` after tagging.",
    )
    return parser.parse_args()


def read_version(path: Path, pattern: re.Pattern[str]) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Could not find a version in {path}")
    return text, match.group("version")


def validate_version(raw: str) -> str:
    if not VERSION_RE.fullmatch(raw):
        raise ValueError(f"Invalid version: {raw}")
    return raw


def bump_version(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def replace_version(text: str, pattern: re.Pattern[str], new_version: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{new_version}{match.group('suffix')}"

    updated, count = pattern.subn(repl, text, count=1)
    if count != 1:
        raise ValueError("Expected to replace exactly one version string")
    return updated


def run_uv_lock() -> None:
    try:
        subprocess.run(["uv", "lock"], cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise ValueError("`uv` was not found, so `uv lock` could not be run") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"`uv lock` failed with exit code {exc.returncode}") from exc


def run_git_tag(tag_name: str) -> None:
    try:
        subprocess.run(["git", "tag", tag_name], cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise ValueError("`git` was not found, so the tag could not be created") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"`git tag` failed with exit code {exc.returncode}") from exc


def run_git_push_tag(tag_name: str) -> None:
    try:
        subprocess.run(["git", "push", "origin", tag_name], cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise ValueError("`git` was not found, so the tag could not be pushed") from exc
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"`git push origin {tag_name}` failed with exit code {exc.returncode}") from exc


def main() -> int:
    args = parse_args()
    if args.push_tag and not args.tag:
        args.tag = True

    loaded = []
    discovered_versions: dict[str, str] = {}
    for path, pattern in TARGETS:
        text, version = read_version(path, pattern)
        loaded.append((path, pattern, text))
        discovered_versions[path.relative_to(ROOT).as_posix()] = version

    current_version = discovered_versions["pyproject.toml"]
    target_version = (
        validate_version(args.version)
        if args.version
        else bump_version(current_version, args.part)
    )
    tag_name = f"v{target_version}"
    should_lock = (ROOT / "uv.lock").exists() and not args.no_lock

    print(f"Current version: {current_version}")
    print(f"Target version:  {target_version}")

    mismatched = {
        path: version
        for path, version in discovered_versions.items()
        if version != current_version
    }
    if mismatched:
        print("Detected mismatched version files; they will be synchronized:", file=sys.stderr)
        for path, version in mismatched.items():
            print(f"  {path}: {version}", file=sys.stderr)

    changed_files = []
    for path, pattern, text in loaded:
        updated = replace_version(text, pattern, target_version)
        relative_path = path.relative_to(ROOT).as_posix()
        if updated != text:
            changed_files.append(relative_path)
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    if args.dry_run:
        print("Dry run: no files were written.")
        if should_lock:
            print("Dry run: would run `uv lock`.")
        if args.tag:
            print(f"Dry run: would create git tag `{tag_name}`.")
        if args.push_tag:
            print(f"Dry run: would push git tag `{tag_name}` to `origin`.")
    else:
        if changed_files:
            print("Updated files:")
            for path in changed_files:
                print(f"  {path}")
        else:
            print("No file changes were needed.")

        if should_lock:
            print("Running `uv lock`...")
            run_uv_lock()
            print("Updated file:")
            print("  uv.lock")

        if args.tag:
            print(f"Creating git tag `{tag_name}`...")
            run_git_tag(tag_name)
            print(f"Created git tag: {tag_name}")

        if args.push_tag:
            print(f"Pushing git tag `{tag_name}` to `origin`...")
            run_git_push_tag(tag_name)

    print(f"Suggested tag: {tag_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
