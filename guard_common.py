"""Shared scaffolding for the app/ lint guards.

Both ``check_deferred_imports.py`` and ``check_layer_violations.py`` walk the
source tree running a per-file checker and report collected violations the same
way. This module holds that common logic so the guards stay DRY.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent


def iter_py(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def iter_nodes(path: Path) -> Iterator[tuple[str, ast.AST]]:
    """Yield ``(relative_path, node)`` for every AST node in ``path``."""
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    tree = parse(path)
    if tree is None:
        return
    for node in ast.walk(tree):
        yield rel, node


def run_guard(
    *,
    checker: Callable[[Path], list[str]],
    subdir: str,
    error_label: str,
    ok_label: str,
    hint: str = "",
) -> int:
    """Walk ``app/<subdir>`` running ``checker`` on each file.

    Returns 0 when no violations are found, 1 otherwise.
    """
    target = PROJECT_ROOT / subdir
    if not target.is_dir():
        print(f"ERROR: {target} not found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in iter_py(target):
        try:
            errors.extend(checker(path))
        except Exception as exc:  # noqa: BLE001
            print(f"Error scanning {path}: {exc}", file=sys.stderr)
            return 1

    if errors:
        print(f"ERROR: {error_label}", file=sys.stderr)
        for err in sorted(errors):
            print(f"  {err}", file=sys.stderr)
        if hint:
            print(file=sys.stderr)
            print(hint, file=sys.stderr)
        return 1

    print(f"OK: {ok_label}")
    return 0
