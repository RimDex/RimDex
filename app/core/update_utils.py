"""Backwards-compatible re-export shim for the RimDex update subsystem.

The self-update logic was split into two focused modules:

* :mod:`app.core.update_check` — pure version / asset-resolution layer (no Qt,
  no ``app.views`` imports). Safe to use from leaf code and unit tests.
* :mod:`app.core.update_apply` — the apply / self-update flow (download,
  extraction, backup, launch) which imports PySide6 and the progress UI.

This shim keeps the original public surface intact so existing imports such as
``from app.core.update_utils import UpdateManager`` continue to work.
"""

from __future__ import annotations

from app.core.update_apply import (
    PLATFORM_PATTERNS,
    DownloadInfo,
    PlatformPatterns,
    ReleaseInfo,
    ScriptConfig,
    TarExtractThread,
    UpdateDownloadError,
    UpdateError,
    UpdateExtractionError,
    UpdateManager,
    UpdateNetworkError,
    UpdateScriptLaunchError,
)

__all__ = [
    "UpdateError",
    "UpdateNetworkError",
    "UpdateDownloadError",
    "UpdateExtractionError",
    "UpdateScriptLaunchError",
    "ReleaseInfo",
    "DownloadInfo",
    "PlatformPatterns",
    "ScriptConfig",
    "PLATFORM_PATTERNS",
    "TarExtractThread",
    "UpdateManager",
]
