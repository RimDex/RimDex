from pathlib import Path
from typing import Any

import pytest

from app.core import update_check
from app.core.update_check import (
    asset_matches,
    find_appimage_asset,
    find_best_asset_match,
    parse_version,
    resolve_platform_download_url,
)
from packaging import version

# ─── parse_version ───────────────────────────────────────────────────────────


def test_parse_version_normal() -> None:
    assert parse_version("1.2.3") == version.parse("1.2.3")


def test_parse_version_unknown_sentinel_is_custom_build() -> None:
    # Unknown/custom builds are treated as updatable (0.0.0).
    assert parse_version("Unknown version") == version.parse("0.0.0")


def test_parse_version_invalid_falls_back_to_zero() -> None:
    assert parse_version("not-a-version") == version.parse("0.0.0")


# ─── asset_matches ───────────────────────────────────────────────────────────


def _asset(name: str, url: str = "https://example.com/x") -> dict[str, Any]:
    return {"name": name, "browser_download_url": url}


def test_asset_matches_extension_only() -> None:
    assert asset_matches(_asset("RimDex-Windows-x64.zip"), ["Windows"], ".zip")
    assert not asset_matches(_asset("RimDex-Windows-x64.msi"), ["Windows"], ".zip")


def test_asset_matches_requires_system_pattern() -> None:
    # Wrong system pattern -> no match even with correct extension.
    assert not asset_matches(_asset("RimDex-Linux-x64.zip"), ["Windows"], ".zip")


def test_asset_matches_list_name_normalized() -> None:
    assert asset_matches(
        {"name": ["RimDex", "Windows", "x64.zip"], "browser_download_url": "x"},
        ["Windows"],
        ".zip",
    )


def test_asset_matches_non_string_name_coerced() -> None:
    assert (
        asset_matches({"name": 123, "browser_download_url": "x"}, ["Windows"], ".zip")
        is False
    )


def test_asset_matches_arch_required() -> None:
    # arch pattern x86_64 present
    assert asset_matches(
        _asset("RimDex-Windows-x86_64.zip"),
        ["Windows"],
        ".zip",
        require_arch=True,
        arch_patterns=["x86_64"],
    )
    # arch pattern missing -> no match when required
    assert not asset_matches(
        _asset("RimDex-Windows-arm64.zip"),
        ["Windows"],
        ".zip",
        require_arch=True,
        arch_patterns=["x86_64"],
    )


# ─── find_best_asset_match ───────────────────────────────────────────────────


def test_find_best_asset_prefers_arch_specific() -> None:
    assets = [
        _asset("RimDex-Windows-x64.zip", "https://e/system.zip"),
        _asset("RimDex-Windows-x86_64.zip", "https://e/arch.zip"),
    ]
    info = find_best_asset_match(assets, ["Windows"], ["x86_64"], ".zip")
    assert info is not None
    assert info["url"] == "https://e/arch.zip"
    assert info["is_msi"] is False
    assert info["is_tar_gz"] is False


def test_find_best_asset_falls_back_to_system_only() -> None:
    assets = [
        _asset("RimDex-Windows-x64.zip", "https://e/system.zip"),
    ]
    info = find_best_asset_match(assets, ["Windows"], ["x86_64"], ".zip")
    assert info is not None
    assert info["url"] == "https://e/system.zip"


def test_find_best_asset_msi_flag() -> None:
    assets = [_asset("RimDex-Windows-x64.msi", "https://e/x.msi")]
    info = find_best_asset_match(assets, ["Windows"], ["x64"], ".msi")
    assert info is not None
    assert info["is_msi"] is True


def test_find_best_asset_none_when_no_match() -> None:
    assets = [_asset("RimDex-Linux-x64.zip", "https://e/x.zip")]
    assert find_best_asset_match(assets, ["Windows"], ["x64"], ".zip") is None


def test_find_best_asset_skips_assets_without_url() -> None:
    assets = [_asset("RimDex-Windows-x64.zip", "")]
    assert find_best_asset_match(assets, ["Windows"], ["x64"], ".zip") is None


# ─── find_appimage_asset ─────────────────────────────────────────────────────


def test_find_appimage_arch_specific() -> None:
    assets = [
        _asset("RimDex-1.0.0-x86_64.AppImage", "https://e/a.AppImage"),
        _asset("RimDex-1.0.0-arm64.AppImage", "https://e/b.AppImage"),
    ]
    info = find_appimage_asset(assets, ["x86_64"])
    assert info is not None
    assert info["url"] == "https://e/a.AppImage"
    assert info["is_appimage"] is True


def test_find_appimage_falls_back_to_any() -> None:
    assets = [_asset("RimDex-1.0.0-arm64.AppImage", "https://e/b.AppImage")]
    info = find_appimage_asset(assets, ["x86_64"])
    assert info is not None
    assert info["url"] == "https://e/b.AppImage"


def test_find_appimage_none_when_absent() -> None:
    assets = [_asset("RimDex-Linux-x64.zip", "https://e/x.zip")]
    assert find_appimage_asset(assets, ["x86_64"]) is None


# ─── resolve_platform_download_url ───────────────────────────────────────────


def test_resolve_returns_none_for_unknown_system() -> None:
    assert (
        resolve_platform_download_url([], "FreeBSD", "64bit", None, False, False)
        is None
    )


def test_resolve_windows_prefers_msi_in_protected_path() -> None:
    assets = [
        _asset("RimDex-Windows-x64.zip", "https://e/x.zip"),
        _asset("RimDex-Windows-x64.msi", "https://e/x.msi"),
    ]
    info = resolve_platform_download_url(
        assets,
        "Windows",
        "64bit",
        update_check.PLATFORM_PATTERNS["Windows"],
        is_appimage=False,
        is_in_protected_path=True,
    )
    assert info is not None
    assert info["url"] == "https://e/x.msi"


def test_resolve_windows_prefers_zip_outside_protected_path() -> None:
    assets = [
        _asset("RimDex-Windows-x64.zip", "https://e/x.zip"),
        _asset("RimDex-Windows-x64.msi", "https://e/x.msi"),
    ]
    info = resolve_platform_download_url(
        assets,
        "Windows",
        "64bit",
        update_check.PLATFORM_PATTERNS["Windows"],
        is_appimage=False,
        is_in_protected_path=False,
    )
    assert info is not None
    assert info["url"] == "https://e/x.zip"


def test_resolve_linux_prefers_appimage_when_appimage() -> None:
    assets = [
        _asset("RimDex-1.0.0-x86_64.AppImage", "https://e/x.AppImage"),
        _asset("RimDex-Linux-x64.tar.gz", "https://e/x.tar.gz"),
    ]
    info = resolve_platform_download_url(
        assets,
        "Linux",
        "64bit",
        update_check.PLATFORM_PATTERNS["Linux"],
        is_appimage=True,
        is_in_protected_path=False,
    )
    assert info is not None
    assert info["url"] == "https://e/x.AppImage"


def test_resolve_linux_falls_back_to_tar_gz() -> None:
    assets = [_asset("RimDex-Linux-x64.tar.gz", "https://e/x.tar.gz")]
    info = resolve_platform_download_url(
        assets,
        "Linux",
        "64bit",
        update_check.PLATFORM_PATTERNS["Linux"],
        is_appimage=False,
        is_in_protected_path=False,
    )
    assert info is not None
    assert info["is_tar_gz"] is True


def test_resolve_darwin_uses_tar_gz() -> None:
    assets = [_asset("RimDex-macOS-arm64.tar.gz", "https://e/x.tar.gz")]
    info = resolve_platform_download_url(
        assets,
        "Darwin",
        "arm64",
        update_check.PLATFORM_PATTERNS["Darwin"],
        is_appimage=False,
        is_in_protected_path=False,
    )
    assert info is not None
    assert info["is_tar_gz"] is True


def test_resolve_none_when_no_assets_match() -> None:
    assets = [_asset("RimDex-Linux-x64.zip", "https://e/x.zip")]
    assert (
        resolve_platform_download_url(
            assets,
            "Windows",
            "64bit",
            update_check.PLATFORM_PATTERNS["Windows"],
            is_appimage=False,
            is_in_protected_path=False,
        )
        is None
    )


# ─── ScriptConfig arg builders ───────────────────────────────────────────────


def test_script_config_windows_no_elevation_returns_list() -> None:
    cfg = update_check.ScriptConfig("update.bat", False, "Windows")
    args = cfg.get_args(Path("C:/app/update.bat"), Path("C:/tmp"), Path("C:/log"))
    assert isinstance(args, list)
    assert args[0] == "cmd"
    assert str(Path("C:/tmp")) in args


def test_script_config_linux_bash_command() -> None:
    cfg = update_check.ScriptConfig("update.sh", False, "Linux")
    args = cfg.get_args(Path("/app/update.sh"), Path("/tmp"), Path("/log"))
    assert isinstance(args, str)
    # Primary method is a direct (quoted) command string; temp path is present.
    assert str(Path("/tmp")) in args


def test_script_config_linux_elevation_uses_sudo() -> None:
    cfg = update_check.ScriptConfig("update.sh", False, "Linux")
    args = cfg.get_args(
        Path("/app/update.sh"), Path("/tmp"), Path("/log"), needs_elevation=True
    )
    assert isinstance(args, str)
    assert args.startswith("sudo ")


def test_script_config_macos_uses_osascript() -> None:
    cfg = update_check.ScriptConfig("update.sh", False, "Darwin")
    args = cfg.get_args(Path("/app/update.sh"), Path("/tmp"), Path("/log"))
    assert "osascript" in args


def test_script_config_windows_elevation_uses_powershell_runas() -> None:
    cfg = update_check.ScriptConfig("update.bat", False, "Windows")
    args = cfg.get_args(
        Path("C:/app/update.bat"),
        Path("C:/tmp"),
        Path("C:/log"),
        needs_elevation=True,
    )
    assert isinstance(args, str)
    assert "RunAs" in args
    assert "powershell.exe" in args


def test_build_terminal_command_unknown_raises() -> None:
    with pytest.raises(ValueError):
        update_check.ScriptConfig._build_terminal_command(
            "unknown-term", ["a", "b"], False
        )


def test_build_terminal_command_gnome_terminal() -> None:
    cmd = update_check.ScriptConfig._build_terminal_command(
        "gnome-terminal", ["/app/update.sh", "/tmp", "/log"], False
    )
    assert "gnome-terminal" in cmd
    assert "bash -c" in cmd


# ─── _is_in_protected_path ───────────────────────────────────────────────────


def test_is_in_protected_path_false_for_non_windows_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Patch the AppInfo singleton's application_folder to a non-protected path.
    from app.core.app_info import AppInfo

    app_info = AppInfo()
    monkeypatch.setattr(app_info, "_application_folder", Path("/home/user/rimdex"))
    assert update_check._is_in_protected_path() is False


def test_is_in_protected_path_true_for_program_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.app_info import AppInfo

    app_info = AppInfo()
    monkeypatch.setattr(
        app_info, "_application_folder", Path("C:/Program Files/RimDex")
    )
    assert update_check._is_in_protected_path() is True
