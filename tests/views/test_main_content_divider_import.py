# tests/views/test_main_content_divider_import.py
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from PySide6.QtWidgets import QApplication

from app.ui import dialogue
from app.views.main_content_panel import MainContent


@pytest.fixture
def main_content(
    monkeypatch: pytest.MonkeyPatch,
    qapp: QApplication,
    mock_settings_controller: MagicMock,
    mock_metadata_controller: MagicMock,
    mock_steamcmd_interface: MagicMock,
) -> MainContent:
    mc = MainContent(
        mock_settings_controller.settings,
        metadata_controller=mock_metadata_controller,
    )
    # Replace list widgets with simple namespaces so paths can be assigned
    # and read like plain lists in a headless test.
    mc.mods_panel.active_mods_list = SimpleNamespace(paths=[])  # type: ignore[assignment]
    mc.mods_panel.inactive_mods_list = SimpleNamespace(paths=[])  # type: ignore[assignment]
    monkeypatch.setattr(mc.mods_panel, "reset_all_filters_and_search", Mock())
    monkeypatch.setattr(mc, "_insert_data_into_lists", Mock())
    monkeypatch.setattr(mc, "_duplicate_mods_prompt", Mock())
    monkeypatch.setattr(mc, "_missing_mods_prompt", Mock())
    return mc


def test_appending_xml_mod_list_appends_only_new_mods(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    main_content: MainContent,
    mock_metadata_controller: MagicMock,
) -> None:
    """Test that appending an XML mod list only adds new active mods and removes them from inactive."""
    imported_list = tmp_path / "append-list.xml"
    imported_list.write_text("<ModsConfigData></ModsConfigData>")
    monkeypatch.setattr(
        dialogue, "show_dialogue_file", Mock(return_value=str(imported_list))
    )

    # Set initial lists
    main_content.mods_panel.active_mods_list.paths = [
        "existing.mod.a",
        "existing.mod.b",
    ]
    main_content.mods_panel.inactive_mods_list.paths = [
        "appended.mod.c",
        "inactive.mod.d",
    ]

    # Mock get_mods_from_list output: active has a duplicate (a), a moved mod (c), and a new mod (e)
    mock_metadata_controller.get_mods_from_list.return_value = (
        ["existing.mod.a", "appended.mod.c", "new.mod.e"],
        ["inactive.mod.d"],
        {},
        {},
    )

    main_content._do_append_list_file_xml()

    from typing import cast

    insert_mock = cast(Mock, main_content._insert_data_into_lists)
    insert_mock.assert_called_once_with(
        ["existing.mod.a", "existing.mod.b", "appended.mod.c", "new.mod.e"],
        ["inactive.mod.d"],
    )
