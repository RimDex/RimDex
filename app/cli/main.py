"""
Main CLI entry point for RimDex.

This module defines the Click command group and registers all subcommands.
"""

import click

from app.cli.translate import translate_group
from app.core.app_info import AppInfo

# build_db is NOT imported at module load. Its transitive import pulls in PySide6
# (app.mods.db_builder_core -> app.utils.steam.webapi.wrapper -> PySide6.QtWidgets),
# which requires Qt system libraries (e.g. libEGL.so.1) that are absent on headless
# runners. To keep headless commands like `translate run-all` working there, the
# heavy `build_db` command is loaded lazily only when it is actually invoked.


class _LazyCommandGroup(click.Group):
    """Command group that resolves `build-db` only when it is requested.

    The real command (app.cli.build_db.build_db) transitively imports PySide6
    (via app.mods.db_builder_core -> app.utils.steam.webapi.wrapper), which needs
    Qt system libraries (e.g. libEGL.so.1) absent on headless runners. By deferring
    the import to command-resolution time, loading `app.cli.main` (e.g. for
    `translate run-all`) never pulls in PySide6 there.
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> "click.Command | None":
        if cmd_name == "build-db":
            from app.cli.build_db import build_db

            return build_db
        return super().get_command(ctx, cmd_name)


@click.group(cls=_LazyCommandGroup)
@click.version_option(version=AppInfo().app_version, prog_name="RimDex")
def cli() -> None:
    """RimDex - RimWorld mod manager CLI

    Headless tools for managing RimWorld mods, building databases, and more.

    Global flags (processed before CLI):
      --disable-updater    Disable automatic update checks (same as RIMDEX_DISABLE_UPDATER env var)
    """
    pass


# Register subcommands. `build-db` is intentionally NOT registered here so its
# PySide6-dependent import chain is resolved lazily by `_LazyCommandGroup`.
cli.add_command(translate_group)


if __name__ == "__main__":
    cli()
