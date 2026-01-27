"""Lint guard: fail on new function-local imports from app/ outside an allowlist.

Scans every .py file under app/ for `from app.` / `import app.` statements
that appear inside function bodies (deferred imports).  Any import NOT in
ALLOWED is reported as an error, preventing regression of circular-import
cleanup (Phase 2).

Usage:
    uv run python check_deferred_imports.py
"""

import ast
import sys
from pathlib import Path

from guard_common import iter_nodes, run_guard

ALLOWED: set[str] = {
    # __main__ cli entry point — intentionally deferred
    "app/__main__.py: from app.cli.main import cli",
    # Window import is heavy; TYPE_CHECKING also covers the type
    "app/controllers/main_content_controller.py: from app.windows.github_mods_panel import GitHubModsPanel",
    # Genuine circular: settings_dialog ↔ language_controller
    # "app/views/settings_dialog.py: from app.controllers.language_controller import LanguageController",
    # Platform-guarded: find_steam_folder only defined on win32
    "app/utils/steam/availability.py: from app.core.win_find_steam import find_steam_folder",
    # Genuine circular via availability -> steamworks.wrapper -> steamworks.structs
    "app/utils/steam/webapi/wrapper.py: from app.utils.steam.availability import check_steam_available",
    "app/utils/steam/webapi/wrapper.py: from app.utils.steam.steamworks.wrapper import SteamworksAppDependenciesQuery",
    "app/utils/steam/webapi/wrapper.py: from app.utils.steam.steamworks.wrapper import _pool_init_worker",
    # Import chain: main_content_panel -> steamworks.wrapper -> steamworks.structs
    "app/views/main_content_panel.py: from app.utils.steam.availability import check_steam_available",
    "app/views/main_content_panel.py: from app.utils.steam.steamworks.wrapper import SteamworksGameLaunch, SteamworksSubscriptionHandler",
    # Heavy dialog import; avoids loading Qt widget at module level
    "app/controllers/translation_controller.py: from app.windows.translation_manager import TranslationManagerDialog",
    # Controller wired lazily alongside other controllers in MainWindow
    "app/views/main_window.py: from app.controllers.translation_controller import TranslationController",
}


def _normalise(line: str) -> str:
    return line.strip().rstrip(",").strip()


def _import_key(file_rel: str, node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        names = [a.name for a in node.names]
        app_names = [n for n in names if n.startswith("app") or n.startswith("app.")]
        if not app_names:
            return None
        return f"{file_rel}: import {', '.join(sorted(app_names))}"
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if not module.startswith("app"):
            return None
        names = sorted(a.name for a in node.names)
        return f"{file_rel}: from {module} import {', '.join(names)}"
    return None


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    for rel, node in iter_nodes(path):
        # Only look inside function / method bodies
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue  # skip nested functions (their own deferred imports are handled separately)
            key = _import_key(rel, child)
            if key and key not in ALLOWED:
                errors.append(key)

    return errors


def main() -> int:
    return run_guard(
        checker=check_file,
        subdir="app",
        error_label="Unauthorised deferred imports found (add to ALLOWED or hoist):",
        ok_label="no unauthorised deferred imports",
        hint=(
            "If this is a genuine circular dependency, add it to the ALLOWED set in\n"
            "  check_deferred_imports.py"
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
