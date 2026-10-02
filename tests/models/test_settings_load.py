import builtins
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from app.core.constants import DEFAULT_INSTANCE_NAME
from app.models.settings import Settings


def _make_settings(settings_file: Path) -> Settings:
    with patch("app.models.settings.QApplication") as qapplication:
        qapplication.font.return_value.family.return_value = "test"
        settings = Settings()
    settings._settings_file = settings_file
    settings._debug_file = settings_file.parent / "DEBUG"
    return settings


def _settings_data(workshop_folder: str, steam_client_integration: bool) -> str:
    return json.dumps(
        {
            "current_instance": DEFAULT_INSTANCE_NAME,
            "current_instance_path": "C:/instances/Default",
            "instances": {
                DEFAULT_INSTANCE_NAME: {
                    "name": DEFAULT_INSTANCE_NAME,
                    "steam_client_integration": steam_client_integration,
                    "workshop_folder": workshop_folder,
                }
            },
        }
    )


def test_load_closes_settings_file_before_save(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    settings = _make_settings(settings_file)

    open_handles: list[Any] = []
    real_open = builtins.open

    def recording_open(*args: Any, **kwargs: Any) -> Any:
        handle = real_open(*args, **kwargs)
        if Path(args[0]) == settings_file:
            open_handles.append(handle)
        return handle

    save_saw_open_handle: list[bool] = []

    def fake_save(_settings: Settings) -> None:
        save_saw_open_handle.append(any(not handle.closed for handle in open_handles))

    monkeypatch.setattr(builtins, "open", recording_open)
    monkeypatch.setattr(Settings, "save", fake_save)

    settings.load()

    assert open_handles
    assert save_saw_open_handle == [False]


def test_load_continues_when_mitigation_save_fails(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    settings = _make_settings(settings_file)

    with (
        patch.object(Settings, "save", side_effect=OSError("mitigation failed")),
        patch("app.models.settings.logger") as mock_logger,
    ):
        settings.load()

    assert settings.instances[DEFAULT_INSTANCE_NAME].name == DEFAULT_INSTANCE_NAME
    mock_logger.error.assert_called_once_with(
        "Failed to save settings during load: mitigation failed"
    )


def test_load_continues_when_config_fix_save_fails(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        _settings_data("C:/Steam/steamapps/workshop/content/294100", False),
        encoding="utf-8",
    )
    settings = _make_settings(settings_file)

    with (
        patch.object(Settings, "save", side_effect=OSError("config fix failed")),
        patch("app.models.settings.logger") as mock_logger,
    ):
        settings.load()

    assert settings.instances[DEFAULT_INSTANCE_NAME].workshop_folder == ""
    mock_logger.error.assert_called_once_with(
        "Failed to save settings during load: config fix failed"
    )


def test_load_persists_steam_integration_fixes(tmp_path: Path) -> None:
    workshop_folder = tmp_path / "steamapps" / "workshop" / "content" / "294100"
    workshop_folder.mkdir(parents=True)
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        _settings_data(str(workshop_folder), True), encoding="utf-8"
    )
    settings = _make_settings(settings_file)

    settings.load()

    instance = settings.instances[DEFAULT_INSTANCE_NAME]
    assert instance.steam_client_integration is False
    assert instance.workshop_folder == ""
    saved = json.loads(settings_file.read_text(encoding="utf-8"))
    assert saved["instances"][DEFAULT_INSTANCE_NAME]["workshop_folder"] == ""


def test_load_creates_missing_settings_file(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings = _make_settings(settings_file)

    settings.load()

    assert json.loads(settings_file.read_text(encoding="utf-8"))["instances"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows file attributes only")
def test_load_tolerates_read_only_settings_file(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")
    os.chmod(settings_file, stat.S_IREAD)
    settings = _make_settings(settings_file)

    settings.load()

    assert json.loads(settings_file.read_text(encoding="utf-8"))["instances"]
