from pathlib import Path

import msgspec

from app.core.app_info import AppInfo
from app.core.constants import DEFAULT_INSTANCE_NAME, INSTANCE_FOLDER_NAME


class InvalidArchivePathError(ValueError):
    """Raised when provided archive path is invalid or not a valid ZIP file."""

    def __init__(self, archive_path: str) -> None:
        super().__init__(f"Invalid archive path: {archive_path}")


class Instance(msgspec.Struct):
    """
    Data model for a RimWorld game instance.

    Pure data class with no side effects on attribute mutation.
    Validation and signal emission handled by controllers and settings management.
    """

    name: str = DEFAULT_INSTANCE_NAME
    game_folder: str = ""
    config_folder: str = ""
    local_folder: str = ""
    workshop_folder: str = ""
    run_args: str = ""
    steamcmd_auto_clear_depot_cache: bool = True
    steamcmd_install_path: str = str(
        Path(
            AppInfo().app_storage_folder / INSTANCE_FOLDER_NAME / DEFAULT_INSTANCE_NAME
        )
    )
    steamcmd_ignore: bool = False
    steam_client_integration: bool = False
    # Launch game via Steam protocol to enable Steam overlay
    launch_via_steam_protocol: bool = False
    instance_folder_override: str = (
        ""  # Custom instance folder path, empty = use default
    )
    initial_setup: bool = True

    @staticmethod
    def get_instance_folder_path(instance_name: str, override_path: str = "") -> Path:
        """Get instance folder path, using override if provided."""
        # Default instance never uses override
        if override_path and instance_name != DEFAULT_INSTANCE_NAME:
            return Path(override_path) / instance_name
        return AppInfo().app_storage_folder / INSTANCE_FOLDER_NAME / instance_name
