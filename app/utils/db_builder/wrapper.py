"""Thin RimDex-side wrapper around the standalone Database Builder.

Mirrors ``app/utils/todds/wrapper.py`` (prebuilt-binary locating + launch) and
``app/utils/steam/steamworks/wrapper.py`` (source/compiled fallback guard). RimDex
never imports the Database Builder's Python; it launches the bundled
``RimDexDatabaseBuilder[.exe]`` (or, when running from source, the
``submodules/DatabaseBuilder`` entry point) and talks over the process boundary.

Runtime contract (see ``RimDex-Database-Builder`` Agent.md §2 / db_builder_submodule_
migration.md §4):
  - ``build-db --output <path> [--include {all_mods,no_local}]
     [--dlc-data/--no-dlc-data] [--update/--overwrite] [--local-mods-path <path>]
     [--workshop-mods-path <path>] [--api-key <key>] [--storage-dir <path>]``
  - ``query-pfids --appid <id> --pfids-out <file> [--api-key <key>] [--storage-dir <path>]``
  - progress goes to stderr; exit code 0 = success.
"""

from __future__ import annotations

import os
import platform
import subprocess
from collections.abc import Sequence
from typing import Protocol

from loguru import logger
from PySide6.QtCore import QCoreApplication

from app.core.app_info import AppInfo


class DbBuilderRunner(Protocol):
    """Minimal interface for a process runner that the builder can use."""

    def execute(
        self, command: str, args: Sequence[str], progress_bar: int | None = None
    ) -> None: ...

    def message(self, line: str) -> None: ...


class DatabaseBuilderInterface:
    """Locates and launches the standalone RimDex Database Builder."""

    def __init__(self) -> None:
        logger.info("DatabaseBuilderInterface initializing...")

    # ------------------------------------------------------------------ locating
    def _resolve_binary(self) -> str | None:
        """Return the path to the prebuilt binary, or ``None`` if missing.

        Checks both the canonical ``RimDexDatabaseBuilder`` name and the
        Nuitka onefile default names the child's build may produce
        (``rimdex_db_builder[.exe/.bin]``), so the wrapper is robust to either
        packaging choice.
        """
        system = platform.system()
        db_builder_dir = AppInfo().application_folder / "db_builder"
        candidates = ["RimDexDatabaseBuilder"]
        if system == "Windows":
            candidates = [
                "RimDexDatabaseBuilder.exe",
                "rimdex_db_builder.exe",
                *candidates,
            ]
        elif system == "Darwin":
            candidates.append("rimdex_db_builder")
        else:
            candidates = [
                "RimDexDatabaseBuilder",
                "rimdex_db_builder.bin",
                "rimdex_db_builder",
            ]
        for name in candidates:
            exe_path = str(db_builder_dir / name)
            if os.path.exists(exe_path):
                return exe_path
        return None

    def _resolve_source_command(self) -> tuple[str, list[str], str] | None:
        """When running from source, fall back to the submodule entry point.

        Returns ``(command, args, cwd)`` so the child can be launched with its
        working directory set to the submodule root.
        """
        if "__compiled__" in globals():
            return None
        submodule_entry = (
            AppInfo().application_folder.parent / "submodules" / "DatabaseBuilder"
        )
        if not submodule_entry.exists():
            # Fall back to an application-folder-relative path as a last resort.
            submodule_entry = (
                AppInfo().application_folder / "submodules" / "DatabaseBuilder"
            )
        if submodule_entry.exists():
            return (
                "uv",
                ["run", "python", "-m", "rimdex_db_builder"],
                str(submodule_entry),
            )
        return None

    def _build_invocation(
        self, subcommand: str, *extra_args: str
    ) -> tuple[str, list[str], str | None]:
        """Return ``(command, args, cwd)`` for the requested subcommand."""
        subcommand_args = [subcommand, *extra_args] if subcommand else list(extra_args)
        binary = self._resolve_binary()
        if binary:
            return binary, subcommand_args, None
        source = self._resolve_source_command()
        if source:
            cmd, base_args, cwd = source
            return cmd, [*base_args, *subcommand_args], cwd
        raise FileNotFoundError(
            "RimDexDatabaseBuilder binary not found and no source fallback available."
        )

    # --------------------------------------------------------------------- launch
    def launch_gui(self) -> bool:
        """Launch the standalone Database Builder GUI (fire-and-forget).

        Returns ``True`` if the child was launched, ``False`` if it could not be
        located.
        """
        try:
            command, args, cwd = self._build_invocation("")
        except FileNotFoundError:
            self._show_missing_binary_message()
            return False
        # No subcommand → the child launches its own GUI.
        logger.info(f"Launching Database Builder GUI: {command} {args}")
        subprocess.Popen([command, *args], cwd=cwd)  # noqa: S603
        return True

    def build_database(
        self,
        output: str,
        include: str = "no_local",
        dlc_data: bool = False,
        update: bool = False,
        api_key: str = "",
        storage_dir: str = "",
        local_mods_path: str = "",
        workshop_mods_path: str = "",
        runner: DbBuilderRunner | None = None,
    ) -> int | None:
        """Build the Steam Workshop database via the standalone builder.

        Returns the child process exit code, or ``None`` if it could not launch.

        The standalone ``build-db`` CLI supports both ``no_local`` (WebAPI-only)
        and ``all_mods`` (with ``--local-mods-path`` and/or
        ``--workshop-mods-path`` pointing to local mod folders) modes.
        """
        args = ["--output", output]
        args += ["--include", include]
        args += ["--dlc-data" if dlc_data else "--no-dlc-data"]
        args += ["--update" if update else "--overwrite"]
        if local_mods_path:
            args += ["--local-mods-path", local_mods_path]
        if workshop_mods_path:
            args += ["--workshop-mods-path", workshop_mods_path]
        if api_key:
            args += ["--api-key", api_key]
        if storage_dir:
            args += ["--storage-dir", storage_dir]
        try:
            command, full_args, cwd = self._build_invocation("build-db", *args)
        except FileNotFoundError:
            self._show_missing_binary_message(runner)
            return None
        if runner is not None:
            runner.execute(command, full_args, -1)
        else:
            return self._run_blocking(command, full_args, cwd)
        return None

    def query_pfids(
        self,
        pfids_out: str,
        appid: int = 294100,
        api_key: str = "",
        storage_dir: str = "",
        runner: DbBuilderRunner | None = None,
    ) -> int | None:
        """Query all PublishedFileIDs for an AppID via the standalone builder.

        Returns the child process exit code, or ``None`` if it could not launch.
        """
        args = ["--appid", str(appid), "--pfids-out", pfids_out]
        if api_key:
            args += ["--api-key", api_key]
        if storage_dir:
            args += ["--storage-dir", storage_dir]
        try:
            command, full_args, cwd = self._build_invocation("query-pfids", *args)
        except FileNotFoundError:
            self._show_missing_binary_message(runner)
            return None
        if runner is not None:
            runner.execute(command, full_args, -1)
        else:
            return self._run_blocking(command, full_args, cwd)
        return None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _run_blocking(command: str, args: Sequence[str], cwd: str | None = None) -> int:
        logger.info(f"Running Database Builder (blocking): {command} {list(args)}")
        result = subprocess.run([command, *args], check=False, cwd=cwd)  # noqa: S603
        return result.returncode

    @staticmethod
    def _show_missing_binary_message(runner: DbBuilderRunner | None = None) -> None:
        development_guide_url = (
            "https://rimdex.github.io/RimDex/development-guide/development-setup"
        )
        support_url = "https://github.com/RimDex/RimDex/issues"
        message = QCoreApplication.translate(
            "DatabaseBuilderInterface",
            "ERROR: the RimDex Database Builder was not found. If you are running "
            "from source, please ensure you have followed the correct steps in the "
            "{development_guide_url} \n\n"
            "Please reach out to us for support at: {support_url}",
        ).format(
            development_guide_url=development_guide_url,
            support_url=support_url,
        )
        if runner is not None:
            runner.message(message)
        else:
            logger.error(message)
