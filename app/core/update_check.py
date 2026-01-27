"""Pure update-check layer for RimDex (no Qt, no views).

This module contains the version/asset-resolution logic used to decide whether a
RimDex update is available and which release asset to download. It deliberately
imports **no** PySide6 / Qt and **no** ``app.views`` code so it stays a leaf layer
that can be unit-tested and reused without the UI stack.

The apply / self-update side (download, extraction, backup, launch) lives in
:mod:`app.core.update_apply`, and :mod:`app.core.update_utils` re-exports both for
backwards compatibility.
"""

from __future__ import annotations

import platform
import re
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, TypedDict, cast

from loguru import logger

from app.core.app_info import AppInfo
from app.net import http
from packaging import version

# Pre-compiled regex patterns for performance
VERSION_PATTERN = re.compile(r"v?\d+[\.\-_]\d+")
TAG_PREFIX_PATTERN = re.compile(r"^v", re.IGNORECASE)

# API and network constants
GITHUB_API_URL = "https://api.github.com/repos/RimDex/RimDex/releases/latest"
API_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 30

# File and archive constants
ZIP_EXTENSION = ".zip"
TAR_GZ_EXTENSION = ".tar.gz"
MSI_EXTENSION = ".msi"
APPIMAGE_EXTENSION = ".AppImage"
DOWNLOAD_CHUNK_SIZE = 131072  # 128KB for better performance
MIN_UPDATE_SIZE = 1024  # Minimum reasonable size for an app update
UPDATER_LOG_FILENAME = "updater.log"

# Thread timeouts and waits
BACKUP_TIMEOUT_SECONDS = 600  # 10 minutes for backup
EXTRACTION_THREAD_TIMEOUT_MS = 5000  # 5 seconds for thread cleanup
THREAD_JOIN_TIMEOUT = 5  # 5 seconds for thread join
WINDOWS_PROTECTED_PATHS = [
    r"C:\PROGRAM FILES",
    r"C:\PROGRAM FILES (X86)",
    r"C:\WINDOWS",
]

# Tokens used for drive-agnostic protected path detection.
# e.g. D:\Program Files (x86)\... or E:\Program Files (x86)\... should be treated as protected.
WINDOWS_PROTECTED_TOKENS = [
    "WINDOWS",
    "PROGRAM FILES",
    "PROGRAM FILES (X86)",
]

if TYPE_CHECKING:
    from app.core.update_apply import UpdateManager


class UpdateError(Exception):
    """Base exception for update-related errors."""

    pass


class UpdateNetworkError(UpdateError):
    """Raised when network-related errors occur."""

    pass


class UpdateDownloadError(UpdateError):
    """Raised when download fails."""

    pass


class UpdateExtractionError(UpdateError):
    """Raised when extraction fails."""

    pass


class UpdateScriptLaunchError(UpdateError):
    """Raised when launching update script fails."""

    pass


class ReleaseInfo(TypedDict):
    """Type definition for release information dictionary."""

    version: version.Version
    tag_name: str
    download_url: str
    is_msi: bool
    is_appimage: bool
    is_tar_gz: bool


class DownloadInfo(TypedDict):
    """Type definition for download information dictionary."""

    url: str
    name: str
    is_msi: bool
    is_appimage: bool
    is_tar_gz: bool


class PlatformPatterns(TypedDict):
    """Type definition for platform pattern configuration."""

    patterns: list[str]
    arch_patterns: dict[str, list[str]]


class ScriptConfig:
    """Configuration for platform-specific update scripts."""

    def __init__(
        self,
        script_name: str,
        start_new_session: Optional[bool],
        platform: str,
    ) -> None:
        self.script_name = script_name
        self.start_new_session = start_new_session
        self.platform = platform

    def get_script_path(self) -> Path:
        """Get the script path for this platform."""
        if self.platform == "Darwin":
            return (
                Path(sys.argv[0]).parent.parent.parent
                / "Contents"
                / "MacOS"
                / self.script_name
            )
        else:
            return AppInfo().application_folder / self.script_name

    def get_args(
        self,
        script_path: Path,
        temp_path: Path,
        log_path: Path,
        needs_elevation: bool = False,
        install_dir: Optional[Path] = None,
        update_manager: Optional["UpdateManager"] = None,
    ) -> str | list[str]:
        """
        Get the appropriate arguments for launching the update script based on platform and elevation needs.

        Args:
            script_path: Path to the update script
            temp_path: Path to the temporary extraction directory
            log_path: Path to the update log file
            needs_elevation: Whether elevated privileges are required
            install_dir: Installation directory (required for Linux)
            update_manager: UpdateManager instance (for backwards compatibility, not used)

        Returns:
            Arguments string or list for subprocess
        """
        base_args = [str(script_path), str(temp_path), str(log_path)]
        if self.platform == "Windows":
            base_args.append(str(AppInfo().application_folder))
        elif install_dir and self.platform == "Linux":
            base_args.append(str(install_dir))

        return self._build_platform_args(
            base_args, script_path, needs_elevation, update_manager
        )

    @staticmethod
    def _build_bash_command(base_args: list[str], needs_elevation: bool) -> str:
        """
        Build a bash command string for launching update script directly.
        Used as primary method for modern terminal emulators and standalone execution.

        Args:
            base_args: Base arguments list [script_path, temp_path, log_path, install_dir?]
            needs_elevation: Whether to use sudo

        Returns:
            Command string for executing the update script
        """
        quoted_args = " ".join(shlex.quote(arg) for arg in base_args)
        if needs_elevation:
            return f"sudo {quoted_args}"
        else:
            return quoted_args

    @staticmethod
    def _build_terminal_command(
        terminal: str, base_args: list[str], needs_elevation: bool
    ) -> str:
        """
        Build terminal-specific command string for launching update script.
        Used as fallback if direct bash execution is not available.

        Args:
            terminal: Name of the terminal emulator (e.g., "gnome-terminal", "kitty")
            base_args: Base arguments list [script_path, temp_path, log_path, install_dir?]
            needs_elevation: Whether to use sudo

        Returns:
            Command string for the terminal emulator

        Raises:
            ValueError: If terminal emulator is unknown
        """
        quoted_args = " ".join(shlex.quote(arg) for arg in base_args)
        cmd_with_pause = f'{quoted_args}; read -p \\"Press enter to close\\"'

        # gnome-terminal uses -- instead of -e
        if terminal == "gnome-terminal":
            if needs_elevation:
                return f'gnome-terminal -- bash -c "sudo {quoted_args}"'
            else:
                return f'gnome-terminal -- bash -c "{cmd_with_pause}"'

        # konsole, xterm, x-terminal-emulator, and kitty use -e or equivalent
        elif terminal in ["konsole", "xterm", "x-terminal-emulator", "kitty"]:
            if needs_elevation:
                return f'{terminal} -e bash -c "sudo {quoted_args}"'
            else:
                return f'{terminal} -e bash -c "{cmd_with_pause}"'

        # xfce4-terminal and mate-terminal need nested quoting
        elif terminal in ["xfce4-terminal", "mate-terminal"]:
            if needs_elevation:
                return f"{terminal} -e \"bash -c 'sudo {quoted_args}'\""
            else:
                return f"{terminal} -e \"bash -c '{cmd_with_pause}'\""

        else:
            raise ValueError(f"Unknown terminal emulator: {terminal}")

    def _build_platform_args(
        self,
        base_args: list[str],
        script_path: Path,
        needs_elevation: bool,
        update_manager: Optional["UpdateManager"] = None,
    ) -> str | list[str]:
        """
        Build platform-specific arguments for launching the update script.

        For Linux: Uses a two-phase approach:
        1. Primary: Direct bash execution (works with all modern terminal emulators)
        2. Fallback: Terminal emulator detection if primary method fails

        Args:
            base_args: Base arguments list [script_path, temp_path, log_path, install_dir?]
            script_path: Path to the update script
            needs_elevation: Whether elevated privileges are required
            update_manager: UpdateManager instance (required for Linux fallback detection)

        Returns:
            Arguments string or list for subprocess

        Raises:
            ValueError: If platform is unsupported
        """
        if self.platform == "Darwin":
            quoted_args = " ".join(shlex.quote(arg) for arg in base_args)
            terminal_cmd = (
                f'/bin/bash {quoted_args}; read -p \\"Press enter to close\\"'
            )
            script_cmd = f"sudo {terminal_cmd}" if needs_elevation else terminal_cmd
            return f'osascript -e \'tell app "Terminal" to do script "{script_cmd}"\''
        elif self.platform == "Windows":
            if needs_elevation:
                # Properly escape paths for PowerShell with special characters and spaces
                # Paths need to be quoted for cmd.exe which is the actual executor
                script_dir = str(script_path.parent)
                script_file = str(script_path)
                temp_path = str(base_args[1])
                log_path = str(base_args[2])

                # Build the cmd command with properly quoted arguments
                # Using double quotes for cmd.exe path arguments
                cmd_command = f'cd /d "{script_dir}" && "{script_file}" "{temp_path}" "{log_path}"'

                # Escape single quotes in cmd_command for PowerShell (double them)
                cmd_command_escaped = cmd_command.replace("'", "''")

                return (
                    f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"Start-Process cmd -ArgumentList @('/k', "
                    f"'{cmd_command_escaped}') "
                    f'-Verb RunAs -WindowStyle Normal"'
                )
            else:
                # Return as list - subprocess will handle proper quoting
                return [
                    "cmd",
                    "/k",
                    str(script_path),
                    str(base_args[1]),
                    str(base_args[2]),
                ]
        elif self.platform == "Linux":
            # Linux: Try direct bash execution first (primary method)
            cmd = self._build_bash_command(base_args, needs_elevation)
            logger.debug("Linux: Using direct bash command (primary method)")
            return cmd
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")


# Class-level cached platform patterns for performance
PLATFORM_PATTERNS: dict[str, PlatformPatterns] = {
    "Darwin": {
        "patterns": ["Darwin", "macOS", "Mac"],
        "arch_patterns": {
            "arm64": ["arm64", "arm", "apple"],
            "x86_64": ["x86_64", "i386", "intel"],
        },
    },
    "Linux": {
        "patterns": ["Linux", "Ubuntu"],
        "arch_patterns": {
            "64bit": ["x86_64", "amd64"],
            "32bit": ["i386", "x86"],
        },
    },
    "Windows": {
        "patterns": ["Windows", "Win"],
        "arch_patterns": {
            "64bit": ["x86_64", "x64", "amd64"],
            "32bit": ["x86", "i386"],
        },
    },
}


def parse_version(current_version: str) -> version.Version:
    """
    Parse the current version string, handling the "Unknown version" sentinel.

    Args:
        current_version: The current version string

    Returns:
        Parsed version object. ``0.0.0`` is returned for unknown/custom builds
        (treated as updatable); ``999.999.999`` for values that should never update.
    """
    try:
        if current_version == "Unknown version":
            logger.warning(
                f"Current version is: {current_version}, assuming custom build"
            )
            return version.parse("0.0.0")

        return version.parse(current_version)
    except Exception as e:
        logger.warning(f"Failed to parse version '{current_version}': {e}")
        return version.parse("0.0.0")


def asset_matches(
    asset: dict[str, Any],
    patterns: list[str],
    extension: str,
    require_arch: bool = False,
    arch_patterns: list[str] | None = None,
) -> bool:
    """
    Check if an asset matches the given patterns and extension.

    Args:
        asset: Asset dictionary from GitHub API
        patterns: List of patterns to match
        extension: File extension to check
        require_arch: Whether to require architecture match
        arch_patterns: Architecture patterns if require_arch is True

    Returns:
        True if asset matches, False otherwise
    """
    asset_name = asset.get("name", "")
    if isinstance(asset_name, list):
        asset_name = " ".join(asset_name)
    elif not isinstance(asset_name, str):
        asset_name = str(asset_name)
    asset_name_lower = asset_name.lower()

    # Early return if extension doesn't match
    if not asset_name_lower.endswith(extension):
        return False

    # Check system patterns
    if not any(pattern.lower() in asset_name_lower for pattern in patterns):
        return False

    # If architecture is required, check arch patterns
    if require_arch and arch_patterns:
        if not any(pattern.lower() in asset_name_lower for pattern in arch_patterns):
            return False

    return True


def find_best_asset_match(
    assets: list[dict[str, Any]],
    system_patterns: list[str],
    arch_patterns: list[str],
    preferred_extension: str,
) -> DownloadInfo | None:
    """
    Find the best matching asset from the list.

    Args:
        assets: List of asset dictionaries
        system_patterns: System name patterns to match
        arch_patterns: Architecture patterns to match
        preferred_extension: Preferred file extension (.zip or .msi)

    Returns:
        Dictionary with 'url', 'name', and 'is_msi' keys, or None if no match
    """
    candidate = None

    # Single pass: prefer arch-specific match, fallback to system-only
    for asset in assets:
        asset_name = str(asset.get("name", ""))
        download_url = asset.get("browser_download_url")

        if (
            download_url
            and arch_patterns
            and asset_matches(
                asset,
                system_patterns,
                preferred_extension,
                require_arch=True,
                arch_patterns=arch_patterns,
            )
        ):
            logger.debug(
                f"Found arch-specific matching asset: {asset_name} -> {download_url}"
            )
            return cast(
                DownloadInfo,
                {
                    "url": str(download_url),
                    "name": asset_name,
                    "is_msi": preferred_extension == MSI_EXTENSION,
                    "is_appimage": False,
                    "is_tar_gz": preferred_extension == TAR_GZ_EXTENSION,
                },
            )
        elif download_url and asset_matches(
            asset, system_patterns, preferred_extension, require_arch=False
        ):
            logger.debug(
                f"Found system-only matching asset: {asset_name} -> {download_url}"
            )
            if candidate is None:  # Only set if no arch-specific found
                candidate = cast(
                    DownloadInfo,
                    {
                        "url": str(download_url),
                        "name": asset_name,
                        "is_msi": preferred_extension == MSI_EXTENSION,
                        "is_appimage": False,
                        "is_tar_gz": preferred_extension == TAR_GZ_EXTENSION,
                    },
                )

    return candidate


def find_appimage_asset(
    assets: list[dict[str, Any]],
    arch_patterns: list[str],
) -> DownloadInfo | None:
    """
    Find an AppImage asset from the release.

    AppImage filenames use the format ``RimDex-{version}-{arch}.AppImage``
    and don't contain "Linux"/"Ubuntu", so we match only on extension and
    optionally on architecture.
    """
    for asset in assets:
        asset_name = str(asset.get("name", ""))
        download_url = asset.get("browser_download_url")
        if not download_url or not asset_name.lower().endswith(
            APPIMAGE_EXTENSION.lower()
        ):
            continue

        asset_name_lower = asset_name.lower()
        if arch_patterns and any(p.lower() in asset_name_lower for p in arch_patterns):
            logger.debug(f"Found arch-specific AppImage asset: {asset_name}")
            return cast(
                DownloadInfo,
                {
                    "url": str(download_url),
                    "name": asset_name,
                    "is_msi": False,
                    "is_appimage": True,
                    "is_tar_gz": False,
                },
            )

    # Fallback: return any AppImage regardless of arch
    for asset in assets:
        asset_name = str(asset.get("name", ""))
        download_url = asset.get("browser_download_url")
        if download_url and asset_name.lower().endswith(APPIMAGE_EXTENSION.lower()):
            logger.debug(f"Found AppImage asset (no arch match): {asset_name}")
            return cast(
                DownloadInfo,
                {
                    "url": str(download_url),
                    "name": asset_name,
                    "is_msi": False,
                    "is_appimage": True,
                    "is_tar_gz": False,
                },
            )

    return None


def resolve_platform_download_url(
    assets: list[dict[str, Any]],
    system: str,
    arch: str,
    cached_patterns: PlatformPatterns | None,
    is_appimage: bool,
    is_in_protected_path: bool,
) -> DownloadInfo | None:
    """
    Get the appropriate download URL for the current platform.

    Args:
        assets: List of asset dictionaries from GitHub API
        system: ``platform.system()`` result (Darwin/Linux/Windows)
        arch: Architecture string (e.g. ``64bit`` / ``arm64``)
        cached_patterns: Platform pattern config from :data:`PLATFORM_PATTERNS`
        is_appimage: Whether the running executable is an AppImage
        is_in_protected_path: Whether the install dir is Windows-protected

    Returns:
        Dictionary with 'url', 'name', 'is_msi', 'is_appimage', 'is_tar_gz' keys,
        or None if not found
    """
    if cached_patterns is None:
        logger.warning(f"Unsupported system: {system}")
        return None

    system_patterns = cached_patterns["patterns"]
    arch_patterns = cached_patterns["arch_patterns"].get(arch, [])

    # AppImage mode: prefer .AppImage asset, fall back to ZIP
    if system == "Linux" and is_appimage:
        logger.info("AppImage mode: looking for .AppImage asset first")
        candidate = find_appimage_asset(assets, arch_patterns)
        if candidate:
            return candidate
        logger.warning("No .AppImage asset found in release, falling back to ZIP")

    # Determine preferred extension order
    if system == "Windows" and is_in_protected_path:
        preferred_order = [MSI_EXTENSION, ZIP_EXTENSION]
    elif system == "Windows":
        preferred_order = [ZIP_EXTENSION, MSI_EXTENSION]
    else:
        preferred_order = [TAR_GZ_EXTENSION, ZIP_EXTENSION]

    logger.debug(
        f"Looking for asset matching system={system}, arch={arch}, patterns={system_patterns + arch_patterns}, order={preferred_order}"
    )

    for ext in preferred_order:
        candidate = find_best_asset_match(assets, system_patterns, arch_patterns, ext)
        if candidate:
            return candidate

    logger.warning(
        f"No matching asset found for {system} {arch} with extensions order {preferred_order}"
    )
    return None


def get_latest_release_info(
    needs_elevation: bool = False,
) -> ReleaseInfo | None:
    """
    Fetch the latest release information from the GitHub API.

    Args:
        needs_elevation: Whether elevation is needed (affects Windows asset selection)

    Returns:
        Dictionary containing version, tag_name, download_url, and is_* flags, or
        None if the request fails. Network/parse failures are raised as
        :class:`UpdateNetworkError` / :class:`UpdateError` so the caller can
        surface them.
    """
    # Use releases API for better asset information
    response = http.get(GITHUB_API_URL, timeout=API_TIMEOUT)
    response.raise_for_status()
    release_data = response.json()

    tag_name = release_data.get("tag_name", "")
    # Normalize tag name by removing prefix 'v' if present
    normalized_tag = TAG_PREFIX_PATTERN.sub("", str(tag_name))

    # Parse version
    try:
        latest_version = version.parse(normalized_tag)
    except Exception as e:
        logger.warning(f"Failed to parse version from tag {tag_name}: {e}")
        raise UpdateError(f"Failed to parse version from tag {tag_name}: {e}") from e

    # Get platform-specific download URL
    download_info = resolve_platform_download_url(
        release_data.get("assets", []),
        platform.system(),
        _current_arch(),
        PLATFORM_PATTERNS.get(platform.system()),
        AppInfo().is_appimage,
        _is_in_protected_path(),
    )
    if not download_info:
        system_info = (
            f"{platform.system()} {platform.architecture()[0]} {platform.machine()}"
        )
        raise UpdateError(ERR_NO_VALID_RELEASE_TEXT.format(system_info=system_info))

    return {
        "version": latest_version,
        "tag_name": tag_name,
        "download_url": download_info["url"],
        "is_msi": download_info.get("is_msi", False),
        "is_appimage": download_info.get("is_appimage", False),
        "is_tar_gz": download_info.get("is_tar_gz", False),
    }


def _current_arch() -> str:
    """Return the architecture string used by the platform pattern tables."""
    if platform.system() == "Darwin":
        return platform.machine()
    return platform.architecture()[0]


def _is_in_protected_path() -> bool:
    """Check whether the application lives in a Windows protected path."""
    app_folder = AppInfo().application_folder
    app_path_str = str(app_folder).replace("/", "\\").upper()

    for protected in WINDOWS_PROTECTED_PATHS:
        if protected in app_path_str:
            return True

    for token in WINDOWS_PROTECTED_TOKENS:
        if f"\\{token}\\" in app_path_str:
            return True

    return False


# Standardized error messages
ERR_UPDATE_SKIPPED_TITLE = "Update skipped"
ERR_UPDATE_SKIPPED_TEXT = "You are running from Python interpreter."
ERR_UPDATE_SKIPPED_INFO = "Skipping update check..."
ERR_UPDATE_ERROR_TITLE = "RimDex Update Error"
ERR_NO_VALID_RELEASE_TITLE = "RimDex Update Error"
ERR_NO_VALID_RELEASE_TEXT = "Failed to find valid RimDex release for {system_info}"
ERR_API_CONNECTION_TITLE = "RimDex Update Error"
ERR_API_CONNECTION_TEXT = "Failed to connect to GitHub API: {error}"
ERR_DOWNLOAD_FAILED_TITLE = "Download failed"
ERR_DOWNLOAD_FAILED_TEXT = "Failed to download the update."
ERR_EXTRACTION_FAILED_TITLE = "Extraction failed"
ERR_EXTRACTION_FAILED_TEXT = "Failed to extract the downloaded update."
ERR_BACKUP_FAILED_TITLE = "Backup failed"
ERR_BACKUP_FAILED_TEXT = "Failed to create a backup before updating."
ERR_LAUNCH_FAILED_TITLE = "Launch failed"
ERR_LAUNCH_FAILED_TEXT = "Failed to launch the update script."
ERR_UPDATE_FAILED_TITLE = "Update failed"
ERR_UPDATE_FAILED_TEXT = "An unexpected error occurred during the update process."
ERR_RETRIEVE_RELEASE_TITLE = "Unable to retrieve latest release information"
ERR_RETRIEVE_RELEASE_TEXT = "Please check your internet connection and try again, You can also check 'https://github.com/RimDex/RimDex/releases' directly."
