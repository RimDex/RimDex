from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from app.core import app_info
from app.core.app_info import AppInfo


def _make_app_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppInfo:
    """Construct a real AppInfo rooted at ``<tmp>/app``, avoiding real user data.

    Resets the AppInfo singleton and installs a fake ``__main__`` module whose
    ``__file__`` points two levels below the desired application folder
    (``<tmp>/app/app/__main__.py`` -> application_folder ``<tmp>/app``), so init
    derives all folders from the temp tree (no writes to the real user data dir,
    no Qt/network). Returns the application folder path too via the instance.
    """
    import sys

    AppInfo._instance = None
    if hasattr(app_info, "__compiled__"):
        monkeypatch.delattr(app_info, "__compiled__", raising=False)

    app_dir = tmp_path / "app"
    (app_dir / "app").mkdir(parents=True, exist_ok=True)
    fake_main = ModuleType("__main__")
    fake_main.__file__ = str(app_dir / "app" / "__main__.py")
    monkeypatch.setitem(sys.modules, "__main__", fake_main)

    with patch.object(app_info.AppInfo, "_cleanup_appimage_backup", lambda self: None):
        info = AppInfo()
    return info


@pytest.fixture
def _fresh_app_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppInfo:
    """Fresh AppInfo rooted at a temp dir (see ``_make_app_info``)."""
    return _make_app_info(tmp_path, monkeypatch)


def test_app_name_and_version_defaults(
    _fresh_app_info: AppInfo,
) -> None:
    assert _fresh_app_info.app_name == "RimDex"
    # No version.xml in temp -> "Unknown version".
    assert _fresh_app_info.app_version == "Unknown version"
    assert _fresh_app_info.app_copyright == ""


def test_application_folder_derived_from_main(_fresh_app_info: AppInfo) -> None:
    # __main__.__file__ = <tmp>/app/app/__main__.py -> application_folder = <tmp>/app
    assert _fresh_app_info.application_folder.name == "app"


def test_libs_folder_source_vs_compiled(
    _fresh_app_info: AppInfo, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Source mode: libs live in <application_folder>/libs
    assert _fresh_app_info.libs_folder == _fresh_app_info.application_folder / "libs"
    # Compiled mode: libs live at application_folder root
    monkeypatch.setattr(app_info, "__compiled__", True, raising=False)
    AppInfo._instance = None
    info = AppInfo()
    assert info.libs_folder == info.application_folder


def test_derived_folder_properties(_fresh_app_info: AppInfo) -> None:
    app = _fresh_app_info.application_folder
    assert _fresh_app_info.language_data_folder == app / "locales"
    assert _fresh_app_info.theme_data_folder == app / "themes"
    assert (
        _fresh_app_info.setup_web_channel_script_file
        == app / "setup_web_channel_script.js"
    )


def test_storage_subfolders(_fresh_app_info: AppInfo) -> None:
    storage = _fresh_app_info.app_storage_folder
    assert _fresh_app_info.databases_folder == storage / "dbs"
    assert _fresh_app_info.saved_modlists_folder == storage / "modlists"
    assert _fresh_app_info.theme_storage_folder == storage / "themes"
    assert _fresh_app_info.backups_folder == storage / "backups"


def test_backup_subfolders(_fresh_app_info: AppInfo) -> None:
    backups = _fresh_app_info.backups_folder
    assert _fresh_app_info.game_saves_backups_folder == backups / "saves"
    assert _fresh_app_info.settings_backups_folder == backups / "settings"
    assert _fresh_app_info.application_backups_folder == backups / "rimdex_installation"


def test_settings_and_rules_files(_fresh_app_info: AppInfo) -> None:
    assert _fresh_app_info.app_settings_file.name == "settings.json"
    assert _fresh_app_info.user_rules_file.name == "userRules.json"
    assert _fresh_app_info.ignore_mods_file.name == "ignore.json"
    # userRules.json is created on init with the default payload.
    assert _fresh_app_info.user_rules_file.exists()


def test_is_appimage_from_env(
    _fresh_app_info: AppInfo, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("APPIMAGE", raising=False)
    assert _fresh_app_info.is_appimage is False
    assert _fresh_app_info.appimage_path is None

    monkeypatch.setenv("APPIMAGE", "/opt/RimDex-1.0.0-x86_64.AppImage")
    # Re-read env live (properties read os.environ each call).
    assert _fresh_app_info.is_appimage is True
    assert _fresh_app_info.appimage_path == Path("/opt/RimDex-1.0.0-x86_64.AppImage")


def test_version_parsed_from_version_xml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    info = _make_app_info(tmp_path, monkeypatch)
    (info.application_folder / "version.xml").write_text(
        "<root><version>1.2.3</version></root>", encoding="utf-8"
    )
    # Re-read after writing version.xml.
    AppInfo._instance = None
    info = _make_app_info(tmp_path, monkeypatch)
    assert info.app_version == "1.2.3"
