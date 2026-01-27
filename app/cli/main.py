"""
Main CLI entry point for RimDex.

This module defines the Click command group and registers all subcommands.
"""

import click

from app.cli.build_db import build_db
from app.core.app_info import AppInfo


@click.group()
@click.version_option(version=AppInfo().app_version, prog_name="RimDex")
def cli() -> None:
    """RimDex - RimWorld mod manager CLI

    Headless tools for managing RimWorld mods, building databases, and more.

    Global flags (processed before CLI):
      --disable-updater    Disable automatic update checks (same as RIMDEX_DISABLE_UPDATER env var)
    """
    pass


# Register subcommands
cli.add_command(build_db)


if __name__ == "__main__":
    cli()
