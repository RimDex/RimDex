"""Lint guard: enforce the app/ layering rules.

Two rules are enforced:

1. ``app/models/`` (the lowest layer of the MVC stack) must not import the UI
   (``app/views``, ``app/windows``) or orchestration (``app/controllers``)
   layers.
2. ``app/services/`` and ``app/utils/`` are leaf layers that must not import the
   UI/orchestration layers either (``app/controllers``, ``app/views``,
   ``app/windows``). They may depend on other leaf modules only.

Known violations are listed in the ``*_ALLOWED`` sets so the check passes today.
As the refactor relocates that logic (e.g. routing UI through the EventBus or a
thin bridge instead of importing ``views/dialogue``), remove the corresponding
entry so the guard starts enforcing the corrected boundary.

Usage:
    uv run python check_layer_violations.py
"""

import ast
from collections.abc import Callable
from pathlib import Path

from guard_common import iter_nodes, run_guard

# Layer imports that currently violate the rule but are accepted until the
# refactor removes them. Format: "<file-rel>: <import statement as written>",
# where the statement is reconstructed as "from <module> import <sorted names>"
# (or "import <name>"). Keep these to an absolute minimum and remove entries
# as soon as the violating import is gone.
MODELS_ALLOWED: set[str] = set()
# Intentionally empty — app/models/ must not import app/controllers or app/views.

LEAF_ALLOWED: set[str] = set()

# Forbidden import targets per rule.
_MODELS_FORBIDDEN = (("app", "controllers"), ("app", "views"))
_LEAF_FORBIDDEN = (("app", "controllers"), ("app", "views"), ("app", "windows"))


def _import_keys(
    rel: str, node: ast.AST, forbidden: tuple[tuple[str, str], ...]
) -> list[str]:
    keys: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            if tuple(alias.name.split(".")[:2]) in forbidden:
                keys.append(f"{rel}: import {alias.name}")
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if tuple(module.split(".")[:2]) in forbidden:
            names = ", ".join(sorted(a.name for a in node.names))
            keys.append(f"{rel}: from {module} import {names}")
    return keys


def _make_checker(
    forbidden: tuple[tuple[str, str], ...], allowed: set[str]
) -> Callable[[Path], list[str]]:
    def check(path: Path) -> list[str]:
        errors: list[str] = []
        for rel, node in iter_nodes(path):
            for key in _import_keys(rel, node, forbidden):
                if key not in allowed:
                    errors.append(key)
        return errors

    return check


check_models_file = _make_checker(_MODELS_FORBIDDEN, MODELS_ALLOWED)
check_leaf_file = _make_checker(_LEAF_FORBIDDEN, LEAF_ALLOWED)


def main() -> int:
    rc = 0
    rc |= run_guard(
        checker=check_models_file,
        subdir="app/models",
        error_label="app/models/ must not import from app/controllers or app/views:",
        ok_label="no layer violations in app/models/",
        hint=(
            "If this is a genuine layering violation, fix it in the model layer and\n"
            "remove the entry from MODELS_ALLOWED in check_layer_violations.py."
        ),
    )
    rc |= run_guard(
        checker=check_leaf_file,
        subdir="app/services",
        error_label="app/services/ must not import from app/controllers, app/views, or app/windows:",
        ok_label="no layer violations in app/services/",
        hint=(
            "app/services is a leaf layer. Route UI through the EventBus or a thin\n"
            "bridge instead of importing views/controllers. Remove the entry from\n"
            "LEAF_ALLOWED in check_layer_violations.py once fixed."
        ),
    )
    rc |= run_guard(
        checker=check_leaf_file,
        subdir="app/utils",
        error_label="app/utils/ must not import from app/controllers, app/views, or app/windows:",
        ok_label="no layer violations in app/utils/",
        hint=(
            "app/utils/* adapters are leaf layers. Route UI through the EventBus or a\n"
            "thin bridge instead of importing views/controllers. Remove the entry from\n"
            "LEAF_ALLOWED in check_layer_violations.py once fixed."
        ),
    )
    return rc


if __name__ == "__main__":
    import sys

    sys.exit(main())
